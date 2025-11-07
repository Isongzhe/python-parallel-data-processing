#!/usr/bin/env python3
"""
03-ml-pipeline.py - ML Pipeline with xbatcher
Fixed version: variable dimension preserved in input_dims
"""

# ===== Cell 2 =====
import dask
from dask.distributed import Client
import xarray as xr
import xbatcher
from xbatcher.loaders.torch import MapDataset
import intake
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# 啟動 Dask Client
client = Client(n_workers=2, threads_per_worker=2, memory_limit='2GB')
print(f"Dask Dashboard: {client.dashboard_link}")

# 載入 catalog
catalog = intake.open_catalog('catalog.yaml')

# ===== Cell 5 =====
ds = catalog.era5_2019_chunked.to_dask()
ds

# ===== Cell 6 =====
# Resample 到 daily 以減少資料量
ds_daily = ds.resample(time='1D').mean()

print("Dataset:")
print(ds_daily)
print()
print(f"Shape: {ds_daily['convective_available_potential_energy'].shape}")
print(f"Total size: {ds_daily.nbytes / 1e9:.2f} GB")

# ===== Cell 8 =====
# 建立 binary label
convection_flag = (
    (ds_daily['convective_available_potential_energy'] > 1000) & 
    (ds_daily['convective_inhibition'] > -50)
).astype(np.float32)  # 轉為 float32 以便與 features 相容

# 加入 Dataset
ds_daily['convection_flag'] = convection_flag

print("Convection flag:")
print(ds_daily['convection_flag'])
print()

# 檢查 class balance
flag_mean = convection_flag.mean().compute()
print(f"Convection occurrence rate: {flag_mean.values * 100:.2f}%")
print(f"  Class 0 (no convection): {(1 - flag_mean.values) * 100:.2f}%")
print(f"  Class 1 (convection): {flag_mean.values * 100:.2f}%")

# ===== Cell 11 =====
# 計算分割點
n_total = len(ds_daily.time)
n_train = int(n_total * 0.7)
n_val = int(n_total * 0.15)

# 時間序列分割
train_ds = ds_daily.isel(time=slice(0, n_train))
val_ds = ds_daily.isel(time=slice(n_train, n_train + n_val))
test_ds = ds_daily.isel(time=slice(n_train + n_val, None))

print("Data split:")
print(f"  Training: {len(train_ds.time)} days ({train_ds.time.values[0]} to {train_ds.time.values[-1]})")
print(f"  Validation: {len(val_ds.time)} days ({val_ds.time.values[0]} to {val_ds.time.values[-1]})")
print(f"  Test: {len(test_ds.time)} days ({test_ds.time.values[0]} to {test_ds.time.values[-1]})")

# ===== Cell 14 =====
# 定義 feature 變數
feature_vars = ['convective_available_potential_energy', 'convective_inhibition', 'k_index', 'boundary_layer_height']

# Stage 1a: 為 features 創建 BatchGenerator
X_bgen = xbatcher.BatchGenerator(
    train_ds[feature_vars],
    input_dims={'latitude': 12, 'longitude': 12},
    batch_dims={'time': 16},                      # 16 time steps per batch
    preload_batch=False  # 保持 lazy evaluation
)

# Stage 1b: 為 labels 創建 BatchGenerator
y_bgen = xbatcher.BatchGenerator(
    train_ds['convection_flag'],
    input_dims={'latitude': 12, 'longitude': 12},  
    batch_dims={'time': 16},
    preload_batch=False
)

print("BatchGenerators created:")
print(f"  X_bgen: {len(list(X_bgen))} batches")
print(f"  y_bgen: {len(list(y_bgen))} batches")
print()
print("Note: 上面的 list() 會實際迭代，只是為了計數。")
print("      實際使用時不需要這樣做。")

# ===== Cell 16 =====
# 重新創建（因為 generator 已經被消耗了）
X_bgen = xbatcher.BatchGenerator(
    train_ds[feature_vars],
    input_dims={'latitude': 12, 'longitude': 12},
    batch_dims={'time': 16},
    preload_batch=False
)

# 取得第一個 batch
first_batch = next(iter(X_bgen))

print("First batch (still lazy):")
print(first_batch)
print()
print(f"Dimensions: {first_batch.dims}")
print(f"Shape: {first_batch.dims}")
print(f"Variables: {list(first_batch.data_vars)}")
print()
print(f"CAPE shape in this batch: {first_batch['convective_available_potential_energy'].shape}")
print(f"Type: {type(first_batch['convective_available_potential_energy'].data)}")

# ===== Cell 19 =====
# Configuration
SPATIAL_PATCH_SIZE = {'latitude': 12, 'longitude': 12}  # Small spatial patches
TIME_BATCH_SIZE = 16  # Number of time steps per batch

lat_size = train_ds.sizes['latitude']
lon_size = train_ds.sizes['longitude']

print(f"Data dimensions: latitude={lat_size}, longitude={lon_size}")
print(f"Spatial patch size: {SPATIAL_PATCH_SIZE}")
print(f"Time batch size: {TIME_BATCH_SIZE}")
print()

# ============================================================================
# 方法選擇：處理多變數 Dataset
# ============================================================================
# 
# 有兩種方法可以處理多變數 Dataset（CAPE, CIN, K-index, BLH）：
# 
# 方法 1：提前轉換 (更直觀) ✅ 推薦
#   - 在創建 BatchGenerator 之前，先用 .to_array() 把 Dataset 轉成 DataArray
#   - variable 維度會自動變成第一個維度
#   - 使用 xbatcher 預設的 to_tensor() 即可
# 
# 方法 2：使用自定義 transform (更靈活)
#   - 直接傳入 Dataset 給 BatchGenerator
#   - 在 MapDataset 中提供自定義的 transform 函數
#   - transform 會在每個 batch 載入時自動處理轉換
# 
# 兩種方法都是 lazy 的，記憶體使用相同。選你喜歡的！
# ============================================================================

print("使用方法 1：提前轉換 Dataset → DataArray")
print("-" * 60)

# 提前把多變數 Dataset 轉成 DataArray
train_features = train_ds[feature_vars].to_array(dim='variable')
train_labels = train_ds['convection_flag']

print(f"Features shape: {train_features.shape}")  # (variable=4, time=255, lat=121, lon=161)
print(f"Labels shape: {train_labels.shape}")      # (time=255, lat=121, lon=161)
print(f"Features type: {type(train_features.data)}")  # Still dask array!
print()

# 創建 BatchGenerator
# input_dims: 每個 patch 要保留的維度大小（會沿著這些維度切分成多個 patches）
# batch_dims: 會沿著這個維度切分成多個 batches
X_bgen = xbatcher.BatchGenerator(
    train_features,  # DataArray: (variable=4, time=255, lat=121, lon=161)
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},  # 空間 patch 大小: 12x12
    batch_dims={'time': TIME_BATCH_SIZE},  # 時間 batch: 16 time steps
    preload_batch=False
)

y_bgen = xbatcher.BatchGenerator(
    train_labels,  # DataArray: (time=255, lat=121, lon=161)
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},  # 空間 patch 大小: 12x12
    batch_dims={'time': TIME_BATCH_SIZE},  # 時間 batch: 16 time steps
    preload_batch=False
)

# 創建 MapDataset (使用預設的 to_tensor)
train_dataset = MapDataset(
    X_bgen,
    y_bgen
    # 不需要 transform 參數！
)

print("✓ 使用 xbatcher 預設的 to_tensor()")


print()
print(f"PyTorch Dataset created: {len(train_dataset)} batches")
print(f"Type: {type(train_dataset)}")
print()
print(f"Expected output shape:")
print(f"  X: (variable=4, time={TIME_BATCH_SIZE}, lat={SPATIAL_PATCH_SIZE['latitude']}, lon={SPATIAL_PATCH_SIZE['longitude']})")
print(f"  y: (time={TIME_BATCH_SIZE}, lat={SPATIAL_PATCH_SIZE['latitude']}, lon={SPATIAL_PATCH_SIZE['longitude']})")

# ===== Cell 21 =====
# 取得一個樣本
X_sample, y_sample = train_dataset[0]

print("Sample from Dataset:")
print(f"  X type: {type(X_sample)}")
print(f"  X shape: {X_sample.shape}")
print(f"  X dtype: {X_sample.dtype}")
print()
print(f"  y type: {type(y_sample)}")
print(f"  y shape: {y_sample.shape}")
print(f"  y dtype: {y_sample.dtype}")
print()

# Shape interpretation (handle both methods)
if len(X_sample.shape) == 4:
    print("Shape interpretation:")
    print(f"  X: (variable={X_sample.shape[0]}, time={X_sample.shape[1]}, lat={X_sample.shape[2]}, lon={X_sample.shape[3]})")
    print(f"  y: (time={y_sample.shape[0]}, lat={y_sample.shape[1]}, lon={y_sample.shape[2]})")
    print()
    print("✓ Shape is correct! The 'variable' dimension (4 weather variables) serves as the channel dimension for CNN.")
else:
    print(f"⚠️ Unexpected shape! Expected 4D tensor but got {len(X_sample.shape)}D")
    print(f"  Actual X shape: {X_sample.shape}")
    print(f"  Actual y shape: {y_sample.shape}")
    
print()
print("Note: The 'variable' dimension represents the 4 feature variables:")
print("  - variable[0]: CAPE (Convective Available Potential Energy)")
print("  - variable[1]: CIN (Convective Inhibition)")
print("  - variable[2]: K-index")
print("  - variable[3]: BLH (Boundary Layer Height)")

# ===== Cell 23 =====
# 創建 Training DataLoader
train_loader = DataLoader(
    train_dataset,
    batch_size=None,  # 不要再增加 batch 維度！
    shuffle=True,     # 打亂 batches 順序（不是打亂 batch 內的順序）
    num_workers=0,    # 不使用 multiprocessing（避免序列化問題）
)

print(f"Training DataLoader created: {len(train_loader)} batches")
print()
print("Parameters:")
print(f"  batch_size: None (xbatcher already defines batch)")
print(f"  shuffle: True")
print(f"  num_workers: 0 (no multiprocessing)")


# ===== Cell 25 =====
# 為 Validation 和 Test sets 創建 datasets 和 DataLoaders

# 方法 1：提前轉換
# Validation set
val_features = val_ds[feature_vars].to_array(dim='variable')
val_labels = val_ds['convection_flag']

X_val_bgen = xbatcher.BatchGenerator(
    val_features,
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},
    batch_dims={'time': TIME_BATCH_SIZE},
    preload_batch=False
)

y_val_bgen = xbatcher.BatchGenerator(
    val_labels,
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},
    batch_dims={'time': TIME_BATCH_SIZE},
    preload_batch=False
)

val_dataset = MapDataset(X_val_bgen, y_val_bgen)

# Test set
test_features = test_ds[feature_vars].to_array(dim='variable')
test_labels = test_ds['convection_flag']

X_test_bgen = xbatcher.BatchGenerator(
    test_features,
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},
    batch_dims={'time': TIME_BATCH_SIZE},
    preload_batch=False
)

y_test_bgen = xbatcher.BatchGenerator(
    test_labels,
    input_dims={'variable': 4, **SPATIAL_PATCH_SIZE},
    batch_dims={'time': TIME_BATCH_SIZE},
    preload_batch=False
)

test_dataset = MapDataset(X_test_bgen, y_test_bgen)

# 創建 DataLoaders
val_loader = DataLoader(
    val_dataset,
    batch_size=None,
    shuffle=False,  # Validation 不 shuffle
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=None,
    shuffle=False,  # Test 不 shuffle
    num_workers=0
)

print(f"✓ Validation DataLoader created: {len(val_loader)} batches")
print(f"✓ Test DataLoader created: {len(test_loader)} batches")
print()
print("All DataLoaders ready for training and evaluation!")

# ===== Cell 27 =====
# 迭代取得一個 batch
for X_batch, y_batch in train_loader:
    print("Batch from DataLoader:")
    print(f"  X: {X_batch.shape}, dtype: {X_batch.dtype}")
    print(f"  y: {y_batch.shape}, dtype: {y_batch.dtype}")
    print()
    print(f"  X min/max: {X_batch.min():.2f} / {X_batch.max():.2f}")
    print(f"  y unique values: {torch.unique(y_batch)}")
    break  # 只看第一個 batch

# ===== Cell 29 =====
class SimpleConvectionCNN(nn.Module):
    def __init__(self, in_channels=4):
        super().__init__()
        
        # 3D Convolutions (time + space)
        self.conv1 = nn.Conv3d(in_channels, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv3d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv3d(32, 1, kernel_size=3, padding=1)  # output: 1 channel
        
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()  # for binary classification
        
    def forward(self, x):
        # Input from xbatcher: (variable, time, lat, lon) = (4, 16, 121, 161)
        # Need: (batch, channels, time, height, width)
        
        # Add batch dimension if not present
        if x.dim() == 4:
            x = x.unsqueeze(0)  # (1, variable, time, lat, lon)
        
        # x is now: (batch, variable, time, lat, lon)
        # Conv3d expects: (batch, channels, depth, height, width)
        # Map: variable->channels, time->depth, lat/lon->height/width
        # So shape is already correct!
        
        # Convolution layers
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.sigmoid(self.conv3(x))
        
        # Output: (batch, 1, time, lat, lon)
        # Squeeze channel dim
        x = x.squeeze(1)  # (batch, time, lat, lon)
        
        # Remove batch dim if it was added
        if x.size(0) == 1:
            x = x.squeeze(0)  # (time, lat, lon)
        
        return x

# 創建模型
model = SimpleConvectionCNN(in_channels=4)
print(model)
print()

# 計算參數數量
n_params = sum(p.numel() for p in model.parameters())
print(f"Total parameters: {n_params:,}")

# ===== Cell 31 =====
# 創建 dummy input matching xbatcher output shape
dummy_input = torch.randn(4, 16, 121, 161)  # (variable, time, lat, lon)

# Forward pass
with torch.no_grad():
    output = model(dummy_input)

print(f"Input shape: {dummy_input.shape}")
print(f"Output shape: {output.shape}")
print(f"Output range: [{output.min():.3f}, {output.max():.3f}]")
print()
print("✓ Model forward pass successful!")

# ===== Cell 33 =====
# 設定 device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

model = model.to(device)

# Loss function
criterion = nn.BCELoss()  # Binary Cross Entropy

# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training config
n_epochs = 2  # Demo: 快速展示流程

print(f"Training configuration:")
print(f"  Epochs: {n_epochs}")
print(f"  Optimizer: Adam (lr=0.001)")
print(f"  Loss: Binary Cross Entropy")

# ===== Cell 35 =====
# Training loop
history = {'loss': []}

for epoch in range(n_epochs):
    model.train()
    epoch_loss = 0.0
    n_batches = 0
    
    for X_batch, y_batch in train_loader:
        # Move to device
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        # Forward pass
        outputs = model(X_batch)
        
        # Calculate loss
        loss = criterion(outputs, y_batch)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Record
        epoch_loss += loss.item()
        n_batches += 1
    
    # Epoch summary
    avg_loss = epoch_loss / n_batches
    history['loss'].append(avg_loss)
    
    print(f"Epoch {epoch+1}/{n_epochs} - Loss: {avg_loss:.4f}")

print("\n✓ Training complete!")

# ===== Cell 37 =====
plt.figure(figsize=(8, 5))
plt.plot(range(1, n_epochs+1), history['loss'], marker='o', linewidth=2, markersize=8)
plt.xlabel('Epoch', fontsize=12)
plt.ylabel('Loss', fontsize=12)
plt.title('Training Loss', fontsize=13)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ===== Cell 39 =====
# 為 test set 創建 DataLoader
# 使用與 training set 相同的方法

if USE_METHOD == 1:
    # 方法 1：提前轉換
    test_features = test_ds[feature_vars].to_array(dim='variable')
    test_labels = test_ds['convection_flag']
    
    X_test_bgen = xbatcher.BatchGenerator(
        test_features,
        input_dims={'latitude': 16, 'longitude': 16},
        batch_dims={'time': 32},
        preload_batch=False
    )
    
    y_test_bgen = xbatcher.BatchGenerator(
        test_labels,
        input_dims={'latitude': 16, 'longitude': 16},
        batch_dims={'time': 32},
        preload_batch=False
    )
    
    test_dataset = MapDataset(X_test_bgen, y_test_bgen)

elif USE_METHOD == 2:
    # 方法 2：使用 transform
    # 需要重新定義 transform（如果這個 cell 單獨執行）
    def dataset_to_tensor(xr_obj):
        if isinstance(xr_obj, xr.Dataset):
            xr_obj = xr_obj.to_array(dim='variable')
        if isinstance(xr_obj, xr.DataArray):
            xr_obj = xr_obj.values
        return torch.from_numpy(xr_obj)
    
    X_test_bgen = xbatcher.BatchGenerator(
        test_ds[feature_vars],
        input_dims={'latitude': 16, 'longitude': 16},
        batch_dims={'time': 32},
        preload_batch=False
    )
    
    y_test_bgen = xbatcher.BatchGenerator(
        test_ds['convection_flag'],
        input_dims={'latitude': 16, 'longitude': 16},
        batch_dims={'time': 32},
        preload_batch=False
    )
    
    test_dataset = MapDataset(
        X_test_bgen, 
        y_test_bgen,
        transform=dataset_to_tensor,
        target_transform=dataset_to_tensor
    )

test_loader = DataLoader(
    test_dataset,
    batch_size=None,
    shuffle=False,  # test set 不 shuffle
    num_workers=2,
    multiprocessing_context='forkserver'
)

print(f"Test set: {len(test_loader)} batches")

# ===== Cell 40 =====
# Evaluation
model.eval()
test_loss = 0.0
predictions = []
targets = []

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        
        test_loss += loss.item()
        predictions.append(outputs.cpu())
        targets.append(y_batch.cpu())

avg_test_loss = test_loss / len(test_loader)
print(f"Test Loss: {avg_test_loss:.4f}")

# Concatenate all predictions
predictions = torch.cat(predictions, dim=0)
targets = torch.cat(targets, dim=0)

print(f"\nPredictions shape: {predictions.shape}")
print(f"Targets shape: {targets.shape}")

# ===== Cell 42 =====
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# 轉為 binary predictions (threshold = 0.5)
pred_binary = (predictions > 0.5).float()

# Flatten for sklearn
pred_flat = pred_binary.flatten().numpy()
target_flat = targets.flatten().numpy()

# Calculate metrics
accuracy = accuracy_score(target_flat, pred_flat)
precision = precision_score(target_flat, pred_flat, zero_division=0)
recall = recall_score(target_flat, pred_flat, zero_division=0)
f1 = f1_score(target_flat, pred_flat, zero_division=0)

print("Classification Metrics:")
print(f"  Accuracy:  {accuracy:.4f}")
print(f"  Precision: {precision:.4f}")
print(f"  Recall:    {recall:.4f}")
print(f"  F1 Score:  {f1:.4f}")

# ===== Cell 44 =====
# 選取一個時間步驟和空間 patch 來視覺化
t_idx = 10  # 第 10 個時間步

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# True labels
im1 = axes[0].imshow(targets[t_idx], cmap='RdYlBu_r', vmin=0, vmax=1)
axes[0].set_title('Ground Truth', fontsize=12)
axes[0].set_xlabel('Longitude')
axes[0].set_ylabel('Latitude')
plt.colorbar(im1, ax=axes[0])

# Predictions (probability)
im2 = axes[1].imshow(predictions[t_idx], cmap='RdYlBu_r', vmin=0, vmax=1)
axes[1].set_title('Predicted Probability', fontsize=12)
axes[1].set_xlabel('Longitude')
plt.colorbar(im2, ax=axes[1])

# Binary predictions
im3 = axes[2].imshow(pred_binary[t_idx], cmap='RdYlBu_r', vmin=0, vmax=1)
axes[2].set_title('Binary Prediction (>0.5)', fontsize=12)
axes[2].set_xlabel('Longitude')
plt.colorbar(im3, ax=axes[2])

plt.tight_layout()
plt.show()

# ===== Cell 47 =====
# 注意：這裡是簡化版，實務上需要正確對應每個 patch 的座標
# 為了示範，我們假設 predictions 和 test_ds 的空間範圍相同

# 取得一個 batch 的座標
sample_batch = next(iter(X_test_bgen))
time_coords = sample_batch['time'].values
lat_coords = sample_batch['latitude'].values
lon_coords = sample_batch['longitude'].values

# 創建 Xarray DataArray
pred_da = xr.DataArray(
    predictions[:len(time_coords)].numpy(),  # 限制到實際的時間長度
    dims=['time', 'latitude', 'longitude'],
    coords={
        'time': time_coords,
        'latitude': lat_coords,
        'longitude': lon_coords
    },
    name='convection_probability'
)

target_da = xr.DataArray(
    targets[:len(time_coords)].numpy(),
    dims=['time', 'latitude', 'longitude'],
    coords={
        'time': time_coords,
        'latitude': lat_coords,
        'longitude': lon_coords
    },
    name='convection_truth'
)

print("Predictions as Xarray:")
print(pred_da)
print()
print("Targets as Xarray:")
print(target_da)

# ===== Cell 49 =====
import xskillscore as xs

# 計算每個時間步的空間相關
spatial_corr = xs.pearson_r(pred_da, target_da, dim=['latitude', 'longitude'])

print("Spatial correlation (per time step):")
print(spatial_corr.values)
print()
print(f"Mean spatial correlation: {spatial_corr.mean().values:.4f}")
print(f"Std: {spatial_corr.std().values:.4f}")

# 繪圖
plt.figure(figsize=(10, 4))
spatial_corr.plot(marker='o')
plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
plt.title('Spatial Correlation over Time', fontsize=13)
plt.ylabel('Pearson r', fontsize=12)
plt.xlabel('Time', fontsize=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ===== Cell 51 =====
# 計算 RMSE
rmse = xs.rmse(pred_da, target_da, dim=['time', 'latitude', 'longitude'])

print(f"Overall RMSE: {rmse.values:.4f}")

# 也可以計算每個格點的時間 RMSE
rmse_spatial = xs.rmse(pred_da, target_da, dim='time')

plt.figure(figsize=(10, 6))
rmse_spatial.plot(cmap='YlOrRd', vmin=0)
plt.title('RMSE by Location (averaged over time)', fontsize=13)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.show()

print("\nInterpretation:")
print("紅色區域：模型預測誤差較大")
print("黃色/綠色：預測較準確")
print("可以幫助識別模型在哪些地理位置表現較差")

# ===== Cell 56 =====
# 關閉 Dask Client
# client.close()

print("Workshop completed! 🎉")
