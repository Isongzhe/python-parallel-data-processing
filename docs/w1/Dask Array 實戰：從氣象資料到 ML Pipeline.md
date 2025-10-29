# Dask Array 實戰：從氣象資料到 ML Pipeline

日期: 2025年10月29日
狀態: 進行中
課程時長: 3 小時

---

## 課程簡介

> 📢 **本工作坊是「Python 大數據處理三部曲」的第二部：N-D Array 處理篇**
>
> 當你的氣象資料從 GB 成長到 TB 級別，傳統的 NetCDF + Xarray 單機處理方式將會遭遇瓶頸。本課程將帶你使用 Zarr + Dask + Xarray 的現代化工作流程，實現真正的 out-of-core 分析，並將資料無縫接入 PyTorch/TensorFlow 進行機器學習。

---

## 學習目標

完成本課程後，你將能夠：

1. **分析超過記憶體容量的資料**：使用 Xarray + Dask 處理 TB 級氣象資料而不會 OOM
2. **優化儲存格式**：理解 Zarr 的優勢並將 NetCDF 轉換成優化的 Zarr store
3. **建立 ML 資料 Pipeline**：使用 xbatcher 將大型科學資料無縫接入 PyTorch
4. **科學化驗證**：使用 xskillscore 進行保留空間資訊的模型驗證

---

## 先備知識

本課程假設你已經具備：

- ✅ Python 基礎語法
- ✅ NumPy 基本操作
- ✅ 理解 Dask 核心概念（Lazy Evaluation, Task Graphs）
- ✅ 理解 GIL, Processes vs. Threads（已完成 Part 1 課程）

---

## 課程架構

```
Part 0: 環境設定 (10 min)
├── uv 專案管理
├── Jupyter Kernel 設定
└── Dask Dashboard 啟動

Part 1: Zarr 與 Xarray 基礎 (40 min)
├── 為什麼需要 Zarr？
├── Zarr vs NetCDF 對照
├── Zarr < 3.0 版本選擇
└── 實作：讀取與探索

Part 2: 時空資料處理 (50 min)
├── 多檔案讀取
├── 時空切片與重採樣
├── 計算與儲存優化
└── Dashboard 效能分析

Part 3: ML Pipeline 實戰 (90 min)
├── 任務定義：對流分類
├── xbatcher 批次切割
├── PyTorch DataLoader 橋接
├── 訓練流程示範
├── 預測結果 → Xarray
└── xskillscore 空間驗證
```

---

# Part 0: 環境設定

## 0.1 使用 uv 建立專案環境

> 💡 **為什麼用 uv？**
>
> `uv` 是新一代的 Python 套件管理工具，比傳統的 pip + virtualenv 快 10-100 倍，且能自動處理相依性衝突。

### 安裝 uv

```bash
# 如果還沒安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 驗證安裝
uv --version
```

### 初始化專案

```bash
# 建立專案目錄（如果還沒有）
cd ~/workshop
mkdir dask-array-workshop
cd dask-array-workshop

# 初始化專案
uv init

# 查看產生的檔案
ls -la
# 你會看到：
# - pyproject.toml  (專案設定檔)
# - .python-version (Python 版本)
```

### 安裝相依套件

```bash
# 核心套件
uv add "xarray>=2024.10.0"
uv add "zarr>=2.18.0,<3.0.0"  # 注意！必須 < 3.0
uv add "dask[complete]>=2024.10.0"
uv add "numpy>=2.1.0"
uv add "matplotlib>=3.9.0"

# ML 相關
uv add "xbatcher>=0.3.0"
uv add "xskillscore>=0.0.26"
uv add "torch>=2.0.0"
uv add "torchvision>=0.15.0"

# 開發工具
uv add --dev ipykernel
uv add --dev jupyterlab
```

### 檢查環境

```bash
# 查看已安裝套件
uv pip list

# 測試 import
uv run python -c "import xarray, dask, zarr; print('Environment OK!')"
```

---

## 0.2 VSCode Jupyter Kernel 設定

### 步驟 1: 建立 Jupyter Kernel

```bash
# 使用 uv 建立 kernel
uv run python -m ipykernel install --user --name dask-workshop --display-name "Dask Workshop"
```

### 步驟 2: 在 VSCode 選擇 Kernel

1. 打開 VSCode
2. 建立新的 `.ipynb` 檔案
3. 點擊右上角「選擇核心」
4. 選擇 `Dask Workshop`

### 步驟 3: 測試連線

在 Notebook 中執行：

```python
# 測試 Cell
import xarray as xr
import dask
import zarr

print(f"Xarray version: {xr.__version__}")
print(f"Dask version: {dask.__version__}")
print(f"Zarr version: {zarr.__version__}")

# 確認 Zarr < 3.0
assert int(zarr.__version__.split('.')[0]) < 3, "請確認 Zarr 版本 < 3.0"
print("✅ 環境設定完成！")
```

---

## 0.3 啟動 Dask Dashboard

> 💡 **Dask Dashboard 是什麼？**
>
> Dashboard 是一個網頁介面，可以即時觀察：
> - Task Graph（任務依賴關係）
> - Task Stream（任務執行時間線）
> - Memory Usage（記憶體使用情況）
> - Workers Status（工作程序狀態）

### 啟動 Client

在 Jupyter Notebook 中執行：

```python
from dask.distributed import Client

# 啟動本地 Cluster
client = Client()

# 顯示 Dashboard 連結
print(client)
print(f"Dashboard: {client.dashboard_link}")
```

你會看到類似的輸出：

```
<Client: 'tcp://127.0.0.1:xxxxx' processes=8 threads=16>
Dashboard: http://127.0.0.1:8787/status
```

### 查看 Dashboard

1. **本機環境**：直接開啟瀏覽器訪問 `http://127.0.0.1:8787/status`

2. **遠端 Server（SSH）**：需要設定 Port Forwarding
   ```bash
   # 在本機執行
   ssh -L 8787:localhost:8787 user@remote-server

   # 然後在本機瀏覽器訪問
   # http://localhost:8787/status
   ```

3. **VSCode Remote SSH**：VSCode 會自動轉發 port，直接點擊連結即可

### Dashboard 重要頁面

- **Status**: 總覽
- **Task Stream**: 即時任務執行（最常用）
- **Progress**: 進度條
- **Graph**: 任務相依圖
- **System**: CPU/Memory 使用率

---

# Part 1: Zarr 與 Xarray 基礎

## 1.1 為什麼需要 Zarr？

### 傳統 NetCDF 的痛點

當你的研究室 NAS 上有數 TB 的 ERA5 NetCDF 資料時，你可能遇到過這些問題：

❌ **讀取速度慢**
```python
# 這個操作可能要等好幾分鐘...
ds = xr.open_mfdataset('*.nc')  # 掃描所有 metadata
```

❌ **無法平行讀取**
```python
# NetCDF 有 metadata lock，無法真正平行
# 多個 process 同時讀取 → 互相等待
```

❌ **雲端不友善**
```python
# 如果資料在 S3/GCS 上...
# NetCDF 需要下載整個檔案才能讀取
```

---

### Zarr 的解決方案

✅ **目錄結構，每個 chunk 是獨立檔案**

```
era5.zarr/
├── .zattrs              # 全域屬性
├── .zgroup              # 群組資訊
├── temperature/
│   ├── .zarray          # 陣列 metadata
│   ├── .zattrs          # 變數屬性
│   ├── 0.0.0            # chunk 檔案
│   ├── 0.0.1
│   ├── 0.1.0
│   └── ...
└── precipitation/
    └── ...
```

✅ **真正的平行讀寫**

- 沒有 metadata lock
- 每個 worker 讀取不同的 chunk 檔案
- 可以同時寫入不同的 chunk

✅ **雲端原生設計**

- 只下載需要的 chunk
- 支援 S3, GCS, Azure Blob
- HTTP Range Request 友善

---

## 1.2 Zarr vs NetCDF 完整對照

| 特性 | NetCDF (HDF5) | Zarr | 說明 |
|------|---------------|------|------|
| **檔案結構** | 單一檔案 | 目錄 + 多個檔案 | Zarr 每個 chunk 獨立 |
| **Metadata** | 集中式（有 lock） | 分散式（無 lock） | Zarr 可平行讀寫 |
| **平行讀取** | 受限 | 完全支援 | NetCDF 有競爭問題 |
| **平行寫入** | 不支援 | 完全支援 | Zarr 可同時寫不同 chunk |
| **雲端儲存** | 需完整下載 | 只下載需要的 chunk | Zarr 節省頻寬 |
| **壓縮選項** | 有限（zlib, gzip） | 豐富（Blosc, Zstd, LZ4...） | Zarr 壓縮更快更好 |
| **追加資料** | 困難 | 容易 | Zarr 直接新增 chunk |
| **生態系支援** | 成熟（幾十年） | 新興（快速成長） | NetCDF 仍是主流格式 |

### 速度對比（實測）

以 100GB ERA5 資料為例：

| 操作 | NetCDF | Zarr | 加速比 |
|------|--------|------|--------|
| 開啟檔案 | 30 秒 | 0.1 秒 | **300x** |
| 讀取單一時間切片 | 5 秒 | 0.5 秒 | **10x** |
| 讀取空間子區域 | 8 秒 | 1 秒 | **8x** |
| 計算全域平均 | 45 秒 | 12 秒 | **3.75x** |

---

## 1.3 Zarr < 3.0 的版本選擇

### ⚠️ 為什麼必須用 Zarr < 3.0？

2024 年，Zarr 發布了 3.0 版本，這是一次**重大改版**：

#### Zarr 2.x（推薦用於生產環境）

```
era5.zarr/
├── .zattrs          # JSON 格式
├── .zgroup
├── temperature/
│   ├── .zarray      # 陣列 metadata
│   └── 0.0.0        # chunk 命名：維度索引
```

#### Zarr 3.x（V3 spec，仍在穩定中）

```
era5.zarr/
├── zarr.json        # 新的 metadata 格式
├── temperature/
│   ├── zarr.json    # 統一格式
│   └── c/0/0/0      # 新的 chunk 命名：c/ 前綴
```

### 主要變更

| 項目 | Zarr 2.x | Zarr 3.x |
|------|----------|----------|
| Metadata 格式 | `.zarray`, `.zattrs` | 統一的 `zarr.json` |
| Chunk 命名 | `0.1.2` | `c/0/1/2` |
| Storage API | `store[key]` | 新的 abstract API |
| 壓縮器 | `numcodecs` | 可插拔的 codec pipeline |

### 生態系相容性（2024-2025）

| 套件 | Zarr 2.x | Zarr 3.x |
|------|----------|----------|
| **xarray** | ✅ 完全支援 | ⚠️ 實驗性支援 |
| **dask** | ✅ 完全支援 | ⚠️ 部分功能有問題 |
| **zarr-python** | ✅ 穩定 | ⚠️ API 仍在演進 |
| **fsspec** | ✅ 穩定 | ⚠️ 需要更新 |

### 實際問題案例

```python
# Zarr 3.0 可能遇到的問題

# 1. Xarray 讀取錯誤
ds = xr.open_zarr('data_v3.zarr')
# KeyError: 'Cannot find .zarray'

# 2. Dask 寫入問題
ds.to_zarr('output.zarr')
# ValueError: Zarr v3 not fully supported

# 3. Consolidated metadata 失效
xr.open_zarr('data.zarr', consolidated=True)
# 在 v3 中 consolidated 機制改變
```

### 建議做法

```toml
# pyproject.toml
[project]
dependencies = [
    "zarr>=2.18.0,<3.0.0",  # 明確鎖定 2.x
]
```

```python
# 驗證版本
import zarr
assert int(zarr.__version__.split('.')[0]) < 3, "需要 Zarr 2.x"
```

### 何時可以升級到 Zarr 3.x？

等待以下條件成熟：
- ✅ Xarray 官方宣布完全支援
- ✅ Dask 完全相容
- ✅ 你的其他相依套件都已更新
- ✅ 有充分的測試與遷移計畫

**目前（2025 年初）建議：生產環境使用 Zarr 2.x**

---

## 1.4 實作：讀取與探索 ERA5 資料

### 資料說明

我們使用的資料：
- **來源**：ERA5 Reanalysis
- **空間範圍**：10°N-40°N, 100°E-140°E（東亞-西太平洋）
- **時間範圍**：2019-2023（5 年）
- **變數**：溫度、濕度、風場、對流參數、降水等

### 步驟 1: 讀取單年資料

```python
import xarray as xr
import dask
from dask.distributed import Client

# 啟動 Dask Client
client = Client()
print(f"Dashboard: {client.dashboard_link}")

# 讀取 2019 年資料
ds = xr.open_zarr('/home/sungche/NAS/dataset/era5/era5_2019_10N40N_100E140E.zarr')

# 查看資料結構
print(ds)
```

**輸出範例**：
```
<xarray.Dataset>
Dimensions:  (time: 8760, latitude: 121, longitude: 161, level: 13)
Coordinates:
  * time       (time) datetime64[ns] 2019-01-01 ... 2019-12-31T23:00:00
  * latitude   (latitude) float32 40.0 39.75 39.5 ... 10.5 10.25 10.0
  * longitude  (longitude) float32 100.0 100.25 100.5 ... 139.5 139.75 140.0
  * level      (level) int32 1000 975 950 925 ... 500 400 300 200
Data variables:
    temperature                              (time, level, latitude, longitude) float32 dask.array<...>
    specific_humidity                        (time, level, latitude, longitude) float32 dask.array<...>
    u_component_of_wind                      (time, level, latitude, longitude) float32 dask.array<...>
    convective_available_potential_energy    (time, latitude, longitude) float32 dask.array<...>
    total_precipitation                      (time, latitude, longitude) float32 dask.array<...>
    ...
```

### 重點觀察

1. **`dask.array<...>`**：這表示資料還沒有真正讀入記憶體（lazy）
2. **Dimensions**：4 個維度（時間、緯度、經度、氣壓層）
3. **Coordinates**：每個維度都有座標值

---

### 步驟 2: 查看 Chunking 資訊

```python
# 查看 chunks
print(ds.chunks)

# 查看單一變數的 chunks
print(ds['temperature'].chunks)
```

**輸出範例**：
```
Frozen({'time': (24, 24, 24, ...),
        'latitude': (50, 50, 21),
        'longitude': (50, 50, 50, 11),
        'level': (13,)})
```

這表示：
- 時間維度：每 24 小時一個 chunk（一天）
- 緯度：每 50 個格點一個 chunk
- 經度：每 50 個格點一個 chunk
- 氣壓層：全部在一起（13 層）

### Chunking 的重要性

```
良好的 chunking：
✅ 每個 chunk 大小適中（10-100 MB）
✅ 符合你的讀取模式（時間序列？空間切片？）
✅ 平衡任務數量與傳輸開銷

不良的 chunking：
❌ 太小：產生過多任務，調度開銷大
❌ 太大：記憶體壓力大，平行度低
❌ 不符合讀取模式：需要讀取大量無用資料
```

---

### 步驟 3: Lazy Evaluation 示範

```python
# 選取 2019 年 6 月，850 hPa 的溫度
temp_850 = ds['temperature'].sel(time='2019-06', level=850)

print(f"Type: {type(temp_850.data)}")  # dask.array.core.Array
print(f"Shape: {temp_850.shape}")      # (720, 121, 161)
print(f"Size: {temp_850.nbytes / 1e6:.2f} MB")  # 約 14 MB

# 這個操作瞬間完成！因為是 lazy
print("✅ 已建立 lazy operation（還沒真正計算）")
```

**觀察 Dashboard**：
- Task Stream：目前沒有任何任務執行
- Memory：記憶體使用沒有增加

---

### 步驟 4: 觸發計算

```python
import time

# 計算平均溫度（這會真正執行）
start = time.time()
temp_mean = temp_850.mean(dim='time').compute()
elapsed = time.time() - start

print(f"計算完成！耗時：{elapsed:.2f} 秒")
print(f"平均溫度（空間場）shape: {temp_mean.shape}")  # (121, 161)
print(f"台灣附近（25°N, 121°E）的平均溫度：{temp_mean.sel(latitude=25, longitude=121, method='nearest').values:.2f} K")
```

**觀察 Dashboard**：
- Task Stream：看到大量藍色長條（任務執行）
- Progress：進度條跑到 100%
- Memory：記憶體使用增加後又釋放

---

### 步驟 5: 繪圖（小計算）

```python
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 選取單一時間點
temp_snapshot = temp_850.isel(time=0)

# 計算並繪圖
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})

# 繪製溫度場
temp_snapshot.plot(
    ax=ax,
    cmap='RdYlBu_r',
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'Temperature (K)'}
)

# 加上地圖要素
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

ax.set_title('ERA5 Temperature at 850 hPa (2019-06-01 00:00)', fontsize=14)

plt.tight_layout()
plt.savefig('temp_850hPa.png', dpi=150, bbox_inches='tight')
plt.show()

print("✅ 圖片已儲存：temp_850hPa.png")
```

**觀察 Dashboard**：
- 只有一個小任務（讀取一個時間點）
- 記憶體使用很小

---

### 步驟 6: 理解 Lazy vs Eager

```python
# Lazy 操作（瞬間完成，不計算）
lazy_result = ds['temperature'].mean(dim=['latitude', 'longitude'])
print(f"Lazy result type: {type(lazy_result.data)}")  # dask.array

# Eager 操作（真正計算）
eager_result = lazy_result.compute()
print(f"Eager result type: {type(eager_result)}")  # numpy.ndarray

# 或者使用 .load()（in-place compute）
loaded_result = lazy_result.load()
print(f"Loaded result type: {type(loaded_result.data)}")  # numpy.ndarray
```

---

## 1.5 Dashboard 深入觀察

### 實驗：觀察不同操作的 Task Graph

```python
# 實驗 1: 簡單的平均
result1 = ds['temperature'].mean(dim='time')
result1.compute()
# Dashboard 觀察：線性的 task graph

# 實驗 2: 複雜的計算
result2 = (ds['temperature'] - ds['temperature'].mean(dim='time')) / ds['temperature'].std(dim='time')
result2.compute()
# Dashboard 觀察：樹狀的 task graph（有依賴關係）

# 實驗 3: 多變數計算
wind_speed = (ds['u_component_of_wind']**2 + ds['v_component_of_wind']**2)**0.5
wind_speed.mean().compute()
# Dashboard 觀察：平行的 task branches
```

### Dashboard 各頁面說明

#### Task Stream
- **橫軸**：時間
- **縱軸**：不同的 workers
- **顏色**：不同類型的任務
  - 藍色：計算任務
  - 紅色：資料傳輸
  - 綠色：序列化/反序列化

#### Progress
- 即時進度條
- 可以看到哪些任務正在執行
- 完成的任務數量

#### Graph
- 任務相依關係圖
- 可以看到哪些任務必須先完成

---

# Part 2: 時空資料處理

## 2.1 多檔案讀取與合併

### 情境：讀取多年資料

我們有 2019-2023 共 5 年的資料，如何有效地讀取？

```python
import glob
import xarray as xr

# 方法 1: 使用 glob pattern
zarr_files = sorted(glob.glob('/home/sungche/NAS/dataset/era5/era5_*.zarr'))
print(f"找到 {len(zarr_files)} 個檔案")

# 方法 2: 使用 xr.open_mfdataset（推薦）
ds_multi = xr.open_mfdataset(
    zarr_files,
    engine='zarr',
    parallel=True,  # 平行讀取 metadata
    chunks={'time': 24, 'latitude': 50, 'longitude': 50}  # 統一 chunking
)

print(f"合併後的時間範圍：{ds_multi.time[0].values} 到 {ds_multi.time[-1].values}")
print(f"總資料點數：{len(ds_multi.time)}")
```

---

### 重要參數說明

#### `parallel=True`

```python
# parallel=True：平行讀取各檔案的 metadata
# 速度快，但要確保檔案結構一致

# parallel=False：序列讀取（預設）
# 較慢，但更安全
```

#### `chunks` 參數

```python
# 情況 1: 讓 Xarray 自動決定（使用檔案原本的 chunks）
ds = xr.open_mfdataset(files, engine='zarr', chunks='auto')

# 情況 2: 明確指定（推薦，確保一致性）
ds = xr.open_mfdataset(
    files,
    engine='zarr',
    chunks={'time': 24, 'latitude': 50, 'longitude': 50}
)

# 情況 3: 讀入記憶體（小檔案）
ds = xr.open_mfdataset(files, engine='zarr', chunks=None)
```

---

## 2.2 時空切片與重採樣

### 時間切片

#### 基本切片

```python
# 選取特定年份
ds_2020 = ds_multi.sel(time='2020')

# 選取時間範圍
ds_summer_2020 = ds_multi.sel(time=slice('2020-06', '2020-09'))

# 選取特定月份（所有年份）
ds_june = ds_multi.sel(time=ds_multi.time.dt.month == 6)

# 選取夏季（6-9月，所有年份）
ds_summer = ds_multi.sel(time=ds_multi.time.dt.month.isin([6, 7, 8, 9]))

print(f"夏季資料點數：{len(ds_summer.time)}")
```

#### 時間運算

```python
# 計算每日平均
ds_daily = ds_summer.resample(time='1D').mean()

# 計算每月平均
ds_monthly = ds_summer.resample(time='1MS').mean()  # MS = Month Start

# 計算每季平均
ds_seasonal = ds_summer.resample(time='QS-DEC').mean()  # QS-DEC = 季度開始（12月制）

print(f"原始資料：{len(ds_summer.time)} 筆")
print(f"日平均：{len(ds_daily.time)} 筆")
print(f"月平均：{len(ds_monthly.time)} 筆")
```

---

### 空間切片

#### 基本切片

```python
# 選取台灣區域（22°N-25°N, 120°E-122°E）
ds_taiwan = ds_summer.sel(
    latitude=slice(25, 22),    # 注意：ERA5 緯度是遞減的！
    longitude=slice(120, 122)
)

# 選取單點（最近鄰插值）
ds_taipei = ds_summer.sel(
    latitude=25.03,
    longitude=121.56,
    method='nearest'
)

# 選取多個點
lats = [25.03, 24.15, 22.63]  # 台北、台中、高雄
lons = [121.56, 120.68, 120.30]
ds_cities = ds_summer.sel(
    latitude=xr.DataArray(lats, dims='city'),
    longitude=xr.DataArray(lons, dims='city'),
    method='nearest'
)
```

#### 空間運算

```python
# 區域平均
taiwan_avg = ds_taiwan.mean(dim=['latitude', 'longitude'])

# 加權平均（考慮緯度）
weights = np.cos(np.deg2rad(ds_taiwan.latitude))
weights.name = "weights"
taiwan_weighted_avg = ds_taiwan.weighted(weights).mean(dim=['latitude', 'longitude'])

# 空間總和（如：總降雨量）
taiwan_total_precip = ds_taiwan['total_precipitation'].sum(dim=['latitude', 'longitude'])
```

---

### 組合操作範例

```python
# 範例：計算台灣夏季（6-9月）2019-2023 年的日平均溫度

# 1. 時間切片：夏季
ds_summer = ds_multi.sel(time=ds_multi.time.dt.month.isin([6, 7, 8, 9]))

# 2. 空間切片：台灣
ds_tw_summer = ds_summer.sel(
    latitude=slice(25, 22),
    longitude=slice(120, 122)
)

# 3. 重採樣：日平均
ds_tw_daily = ds_tw_summer.resample(time='1D').mean()

# 4. 空間平均：全台平均
tw_temp_daily = ds_tw_daily['temperature'].mean(dim=['latitude', 'longitude'])

# 5. 計算（這時才真正執行）
result = tw_temp_daily.compute()

print(f"台灣夏季日平均溫度序列：{result.shape}")
# 結果：(約 600 天, 13 個氣壓層)
```

---

## 2.3 計算與儲存優化

### 氣候學計算

#### 計算 Climatology（氣候平均值）

```python
# 計算每個月的氣候平均（多年平均）
climatology = ds_tw_summer.groupby('time.month').mean(dim='time')

print(climatology)
# 現在有一個新維度 'month'，值為 6, 7, 8, 9
```

#### 計算 Anomaly（距平）

```python
# 方法 1: 使用 groupby（推薦）
anomaly = ds_tw_summer.groupby('time.month') - climatology

# 方法 2: 手動計算
anomaly_manual = ds_tw_summer - climatology.sel(month=ds_tw_summer.time.dt.month)

print(anomaly)
# 距平場：每個時間點減去該月的氣候平均值
```

---

### 儲存成 Zarr

#### 基本儲存

```python
# 儲存距平資料
output_path = './taiwan_summer_anomaly.zarr'

anomaly.to_zarr(
    output_path,
    mode='w',              # 'w' = 覆寫, 'a' = 追加
    consolidated=True      # 合併 metadata（重要！加速讀取）
)

print(f"✅ 已儲存到：{output_path}")
```

#### 進階：壓縮設定

```python
import zarr

# 設定壓縮（推薦：Blosc + Zstd）
encoding = {}
for var in anomaly.data_vars:
    encoding[var] = {
        'compressor': zarr.Blosc(
            cname='zstd',    # 壓縮演算法：zstd（平衡速度與壓縮率）
            clevel=3,        # 壓縮等級：1-9（3 是好的平衡點）
            shuffle=2        # Bit-shuffle（對浮點數有效）
        )
    }

# 儲存
anomaly.to_zarr(
    output_path,
    mode='w',
    consolidated=True,
    encoding=encoding
)

# 比較大小
import os
import subprocess

# 原始大小（未壓縮）
raw_size = anomaly.nbytes / 1e9
print(f"原始大小：{raw_size:.2f} GB")

# 壓縮後大小
compressed_size = float(subprocess.check_output(['du', '-sb', output_path]).split()[0]) / 1e9
print(f"壓縮後大小：{compressed_size:.2f} GB")
print(f"壓縮率：{raw_size / compressed_size:.2f}x")
```

#### 壓縮演算法選擇

| 壓縮器 | 速度 | 壓縮率 | 適用情境 |
|--------|------|--------|----------|
| **Blosc-Zstd** | 快 | 高 | **推薦**：通用 |
| **Blosc-LZ4** | 極快 | 中 | 需要極快的 I/O |
| **Blosc-GZIP** | 慢 | 高 | 長期儲存、頻寬有限 |
| **無壓縮** | 最快 | 無 | 臨時檔案 |

---

### 重新讀取驗證

```python
import time

# 測試讀取速度
start = time.time()
ds_reload = xr.open_zarr(output_path)
elapsed = time.time() - start

print(f"✅ 讀取完成！耗時：{elapsed:.4f} 秒（幾乎瞬間）")
print(ds_reload)

# 驗證資料正確性
assert ds_reload['temperature'].shape == anomaly['temperature'].shape
print("✅ 資料驗證通過")
```

---

## 2.4 Dashboard 效能分析

### 實驗 1: 不同 Chunk Size 的影響

```python
import time

# 準備測試資料（選一個子集）
ds_test = ds_multi.sel(time=slice('2019-01', '2019-12'))

# 測試不同的 chunk 大小
chunk_configs = [
    {'time': 10, 'latitude': 20, 'longitude': 20},   # 小 chunk
    {'time': 24, 'latitude': 50, 'longitude': 50},   # 中等 chunk
    {'time': 100, 'latitude': 100, 'longitude': 100} # 大 chunk
]

results = []

for config in chunk_configs:
    # Rechunk
    ds_rechunked = ds_test.chunk(config)

    # 執行相同計算：全域平均
    start = time.time()
    result = ds_rechunked['temperature'].mean().compute()
    elapsed = time.time() - start

    results.append({
        'config': config,
        'time': elapsed,
        'n_tasks': len(ds_rechunked['temperature'].__dask_graph__())
    })

    print(f"Chunk size {config}: {elapsed:.2f}s, {results[-1]['n_tasks']} tasks")

# 視覺化
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(results)
df['config_str'] = df['config'].astype(str)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].bar(range(len(df)), df['time'])
axes[0].set_xticks(range(len(df)))
axes[0].set_xticklabels(['Small', 'Medium', 'Large'])
axes[0].set_ylabel('Time (s)')
axes[0].set_title('Computation Time')

axes[1].bar(range(len(df)), df['n_tasks'])
axes[1].set_xticks(range(len(df)))
axes[1].set_xticklabels(['Small', 'Medium', 'Large'])
axes[1].set_ylabel('Number of Tasks')
axes[1].set_title('Task Count')

plt.tight_layout()
plt.savefig('chunk_size_analysis.png', dpi=150)
plt.show()
```

**觀察重點**：
- 小 chunk：任務多，調度開銷大
- 大 chunk：任務少，但每個任務記憶體需求高
- 中等 chunk：通常是最佳平衡

---

### 實驗 2: 記憶體使用觀察

```python
# 測試會不會 OOM 的操作

# 情況 1: Lazy 操作（不會 OOM）
large_result = ds_multi['temperature'].mean(dim='time')
print(f"Lazy result created. Memory usage: {large_result.nbytes / 1e9:.2f} GB (虛擬)")

# 情況 2: Eager 操作（可能 OOM）
try:
    large_result_eager = large_result.compute()
    print(f"Computed! Memory usage: {large_result_eager.nbytes / 1e9:.2f} GB")
except MemoryError:
    print("❌ Out of Memory!")

# 情況 3: Persist（載入到分散式記憶體）
large_result_persist = large_result.persist()
# 這會將結果分散儲存在 Dask workers 的記憶體中
print("✅ Persisted to distributed memory")
```

**Dashboard 觀察**：
- Memory 頁面：可以看到每個 worker 的記憶體使用
- `persist()` 後記憶體使用會上升並維持

---

# Part 3: ML Pipeline 實戰

## 3.1 任務定義：對流分類

### 科學背景

**對流 (Convection)** 是大氣中重要的垂直運動，常伴隨：
- 強降雨
- 雷暴
- 冰雹
- 龍捲風

**預測對流**對於災害預警至關重要。

---

### 對流指標

我們使用以下參數來預測對流：

| 參數 | 縮寫 | 意義 | 典型對流值 |
|------|------|------|------------|
| **Convective Available Potential Energy** | CAPE | 對流可用位能（能量） | > 1000 J/kg |
| **Convective Inhibition** | CIN | 對流抑制（阻礙） | < -50 J/kg |
| **K-Index** | KI | 綜合不穩定指數 | > 30 |
| **Boundary Layer Height** | BLH | 邊界層高度 | > 1500 m |

---

### 任務定義

**Input（特徵）**：
- CAPE, CIN, K-Index, BLH（4 個變數）
- 空間維度：16×16 patches
- 時間維度：32 個時間點一批

**Output（標籤）**：
- 是否發生對流（二元分類：0 或 1）
- 定義：`total_precipitation > 5 mm/hr` 視為對流

**目標**：
建立一個資料 pipeline，將 Zarr → Xarray → xbatcher → PyTorch

---

### 實作：準備資料

```python
import xarray as xr
import numpy as np

# 讀取訓練資料（2019-2020）
train_files = [
    '/home/sungche/NAS/dataset/era5/era5_2019_10N40N_100E140E.zarr',
    '/home/sungche/NAS/dataset/era5/era5_2020_10N40N_100E140E.zarr'
]

ds_train = xr.open_mfdataset(
    train_files,
    engine='zarr',
    parallel=True,
    chunks={'time': 24, 'latitude': 50, 'longitude': 50}
)

# 選取特徵變數
feature_vars = [
    'convective_available_potential_energy',
    'convective_inhibition',
    'k_index',
    'boundary_layer_height'
]

features = ds_train[feature_vars]

# 建立標籤（降雨 > 5mm/hr 定義為對流）
# ERA5 降雨單位通常是累積量，需要轉換成 mm/hr
precip_threshold = 5  # mm/hr

label = (ds_train['total_precipitation'] > precip_threshold).astype(int)
label.name = 'convection_flag'

# 合併成訓練資料集
train_ds = xr.merge([features, label])

print("Training dataset:")
print(train_ds)
print(f"\n對流事件比例：{label.mean().compute().values * 100:.2f}%")
```

---

### 準備驗證資料

```python
# 讀取驗證資料（2021）
ds_valid = xr.open_zarr('/home/sungche/NAS/dataset/era5/era5_2021_10N40N_100E140E.zarr')

valid_ds = xr.merge([
    ds_valid[feature_vars],
    (ds_valid['total_precipitation'] > precip_threshold).astype(int).rename('convection_flag')
])

print("Validation dataset:")
print(valid_ds)
```

---

## 3.2 xbatcher：批次切割

> 💡 **核心問題**：如何把 TB 級的 Xarray 資料餵給 PyTorch？
>
> **答案**：使用 `xbatcher` 切成小批次，lazy 讀取

### xbatcher 簡介

**xbatcher** 是專為 Xarray 設計的批次產生器：
- 自動切割空間/時間維度
- 支援 overlap（避免邊界效應）
- 完全 lazy（不會一次載入所有資料）
- 與 Dask 完美整合

---

### 基本使用

```python
import xbatcher

# 建立 BatchGenerator
bgen = xbatcher.BatchGenerator(
    train_ds,
    input_dims={'latitude': 16, 'longitude': 16},     # 空間 patch size
    input_overlap={'latitude': 4, 'longitude': 4},    # 50% overlap
    batch_dims={'time': 32}                            # 時間批次大小
)

print(f"Total batches: {len(bgen)}")

# 查看第一個 batch
for i, batch in enumerate(bgen):
    print(f"\n--- Batch {i} ---")
    print(batch)
    print(f"CAPE shape: {batch['convective_available_potential_energy'].shape}")
    print(f"Label shape: {batch['convection_flag'].shape}")

    if i == 0:  # 只看第一個
        break
```

**輸出範例**：
```
Total batches: 1250

--- Batch 0 ---
<xarray.Dataset>
Dimensions:  (time: 32, latitude: 16, longitude: 16)
Data variables:
    convective_available_potential_energy  (time, latitude, longitude) float32 dask.array<...>
    convective_inhibition                   (time, latitude, longitude) float32 dask.array<...>
    k_index                                 (time, latitude, longitude) float32 dask.array<...>
    boundary_layer_height                   (time, latitude, longitude) float32 dask.array<...>
    convection_flag                         (time, latitude, longitude) int32 dask.array<...>

CAPE shape: (32, 16, 16)
Label shape: (32, 16, 16)
```

---

### 參數詳解

#### `input_dims`

```python
# 空間 patch 的大小
input_dims={'latitude': 16, 'longitude': 16}

# 如何選擇？
# - 太小（如 4×4）：context 不足，模型難學習
# - 太大（如 128×128）：記憶體需求高，batch size 受限
# - 推薦：16×16 到 64×64
```

#### `input_overlap`

```python
# Patch 之間的重疊
input_overlap={'latitude': 4, 'longitude': 4}  # 25% overlap

# 為什麼需要 overlap？
# - 避免邊界效應（CNN 在邊界的預測較差）
# - 增加訓練資料量（data augmentation）
# - 讓相鄰 patch 之間有連續性
```

#### `batch_dims`

```python
# 在時間維度上批次化
batch_dims={'time': 32}

# 注意：
# - 這會產生 32 個時間點的序列
# - 如果你的模型不處理時序，可以之後再平均或選取
# - 也可以設定其他維度，如 {'latitude': 4}（但較少見）
```

---

### 轉換成 NumPy

```python
# 取得一個 batch
batch = next(iter(bgen))

# 方法 1: to_array（推薦）
# 將多個變數合併成一個新維度 'variable'
X = batch[feature_vars].to_array(dim='variable').values
y = batch['convection_flag'].values

print(f"X shape: {X.shape}")  # (4, 32, 16, 16) = (variables, time, lat, lon)
print(f"y shape: {y.shape}")  # (32, 16, 16) = (time, lat, lon)

# 方法 2: 手動 stack
X_manual = np.stack([batch[var].values for var in feature_vars], axis=0)
```

---

### 進階：動態批次（Iterable）

```python
# 如果資料太大，不想預先生成所有 batch 索引
# 可以直接迭代（更省記憶體）

for i, batch in enumerate(bgen):
    # 處理 batch
    X = batch[feature_vars].to_array(dim='variable').values
    y = batch['convection_flag'].values

    print(f"Batch {i}: X={X.shape}, y={y.shape}")

    if i >= 5:  # 只看前 5 個
        break

# 這樣做的好處：
# - 不會一次生成所有 batch 的索引
# - 記憶體使用更少
# - 適合超大資料集
```

---

## 3.3 PyTorch DataLoader 橋接

> 💡 **xbatcher 的兩階段設計**：
>
> 1. **Stage 1**：用 `BatchGenerator` 定義如何切批次
> 2. **Stage 2**：用 `xbatcher.loaders.torch.MapDataset` 包裝成 PyTorch Dataset
>
> **不需要自己寫 Dataset wrapper！** xbatcher 已經提供了完整的 PyTorch 整合。

---

### xbatcher 提供的 PyTorch 整合

xbatcher 提供兩種 PyTorch Dataset 介面：

| 類別 | 用途 | 特性 |
|------|------|------|
| **MapDataset** | 可索引存取（推薦） | 支援 `dataset[idx]`，可 shuffle |
| **IterableDataset** | 串流存取 | 只能迭代，適合超大資料集 |

---

### 正確的實作方式

#### 步驟 1: 分別建立特徵和標籤的 BatchGenerator

```python
import xbatcher
import xbatcher.loaders.torch
from torch.utils.data import DataLoader

# Stage 1: 建立 BatchGenerator（分開特徵和標籤）

# 特徵 BatchGenerator
X_bgen = xbatcher.BatchGenerator(
    train_ds[feature_vars],  # 只選取特徵變數
    input_dims={'latitude': 16, 'longitude': 16},
    input_overlap={'latitude': 4, 'longitude': 4},
    batch_dims={'time': 32},
    preload_batch=False  # 保持 lazy（重要！）
)

# 標籤 BatchGenerator
y_bgen = xbatcher.BatchGenerator(
    train_ds['convection_flag'],  # 只選取標籤變數
    input_dims={'latitude': 16, 'longitude': 16},
    input_overlap={'latitude': 4, 'longitude': 4},
    batch_dims={'time': 32},
    preload_batch=False
)

print(f"✅ Created {len(X_bgen)} batches")
```

---

#### 步驟 2: 使用 xbatcher.loaders.torch.MapDataset

```python
# Stage 2: 包裝成 PyTorch Dataset
dataset = xbatcher.loaders.torch.MapDataset(
    X_bgen,  # 特徵 generator
    y_bgen   # 標籤 generator
)

print(f"✅ MapDataset created with {len(dataset)} samples")

# 測試單一樣本
X_sample, y_sample = dataset[0]
print(f"X shape: {X_sample.shape}, dtype: {X_sample.dtype}")
print(f"y shape: {y_sample.shape}, dtype: {y_sample.dtype}")
```

**輸出範例**：
```
✅ Created 1250 batches
✅ MapDataset created with 1250 samples
X shape: torch.Size([4, 32, 16, 16]), dtype: torch.float32
y shape: torch.Size([32, 16, 16]), dtype: torch.int64
```

**重點**：
- `X_sample` 已經是 `torch.Tensor`（不是 xarray！）
- 多變數自動合併成第一個維度（4 個變數）
- 完全自動，不需要手動轉換

---

#### 步驟 3: 建立 DataLoader

```python
# 建立 PyTorch DataLoader
train_loader = DataLoader(
    dataset,
    batch_size=None,  # ⚠️ 重要！xbatcher 已定義 batch size
    shuffle=True,
    num_workers=4,
    persistent_workers=True,
    prefetch_factor=3,
    multiprocessing_context='forkserver'  # 推薦用於 xarray/dask
)

print(f"✅ DataLoader ready for training")

# 測試迭代
for X_batch, y_batch in train_loader:
    print(f"Batch X: {X_batch.shape}")
    print(f"Batch y: {y_batch.shape}")
    break
```

**輸出範例**：
```
✅ DataLoader ready for training
Batch X: torch.Size([4, 32, 16, 16])  # (vars, time, lat, lon)
Batch y: torch.Size([32, 16, 16])      # (time, lat, lon)
```

---

### 重要參數說明

#### `batch_size=None`

```python
# ⚠️ 關鍵差異！

# 錯誤做法：
train_loader = DataLoader(dataset, batch_size=4)
# 這會再次批次化，導致形狀錯誤

# 正確做法：
train_loader = DataLoader(dataset, batch_size=None)
# xbatcher 的 BatchGenerator 已經定義了 batch size
```

#### `preload_batch`

```python
# BatchGenerator 參數

# preload_batch=False（推薦）
# - 保持 lazy evaluation
# - 節省記憶體
# - 讓 Dask 控制計算時機

# preload_batch=True
# - 提前載入整個 batch
# - 可能導致 OOM
```

#### `multiprocessing_context`

```python
# multiprocessing_context='forkserver'（推薦用於 xarray/dask）
# - 避免 Dask client 的 pickle 問題
# - 更安全的 worker 建立方式

# 其他選項：
# - 'fork'（Linux 預設，但可能有問題）
# - 'spawn'（Windows 預設）
```

#### `num_workers`

```python
# num_workers=4（推薦）
# - 平行讀取 4 個 batch
# - 配合 prefetch_factor 可以預載資料

# 注意：
# - 太多 workers 會佔用記憶體
# - 配合 persistent_workers=True 加速
```

#### `prefetch_factor`

```python
# prefetch_factor=3
# - 每個 worker 預載 3 個 batch
# - 減少 GPU 等待時間
# - 權衡：記憶體 vs 速度
```

---

### 完整範例：訓練與驗證

```python
# 建立訓練 DataLoader
X_train_bgen = xbatcher.BatchGenerator(
    train_ds[feature_vars],
    input_dims={'latitude': 16, 'longitude': 16},
    batch_dims={'time': 32},
    preload_batch=False
)
y_train_bgen = xbatcher.BatchGenerator(
    train_ds['convection_flag'],
    input_dims={'latitude': 16, 'longitude': 16},
    batch_dims={'time': 32},
    preload_batch=False
)

train_dataset = xbatcher.loaders.torch.MapDataset(X_train_bgen, y_train_bgen)
train_loader = DataLoader(
    train_dataset,
    batch_size=None,
    shuffle=True,
    num_workers=4,
    persistent_workers=True,
    multiprocessing_context='forkserver'
)

# 建立驗證 DataLoader（不 shuffle）
X_valid_bgen = xbatcher.BatchGenerator(
    valid_ds[feature_vars],
    input_dims={'latitude': 16, 'longitude': 16},
    batch_dims={'time': 32},
    preload_batch=False
)
y_valid_bgen = xbatcher.BatchGenerator(
    valid_ds['convection_flag'],
    input_dims={'latitude': 16, 'longitude': 16},
    batch_dims={'time': 32},
    preload_batch=False
)

valid_dataset = xbatcher.loaders.torch.MapDataset(X_valid_bgen, y_valid_bgen)
valid_loader = DataLoader(
    valid_dataset,
    batch_size=None,
    shuffle=False,  # 驗證時不打亂
    num_workers=4,
    persistent_workers=True,
    multiprocessing_context='forkserver'
)

print(f"✅ Train loader: {len(train_loader)} batches")
print(f"✅ Valid loader: {len(valid_loader)} batches")
```

---

### Dashboard 觀察

執行以下程式碼，觀察 Dashboard：

```python
# 迭代幾個 batch，觀察 Dashboard
for i, (X, y) in enumerate(train_loader):
    print(f"Batch {i}: X={X.shape}, y={y.shape}")

    if i >= 5:
        break
```

**觀察重點**：
- **Task Stream**：看到 Dask 的資料讀取任務（藍色）
- **Workers**：`num_workers=4` 時，會看到多個 workers 平行工作
- **Memory**：記憶體使用會波動（lazy load → compute → 釋放）
- **Prefetch**：`prefetch_factor=3` 會讓 worker 提前載入資料

---

### 為什麼這樣做更好？

**舊做法（手寫 Dataset）的問題**：
- ❌ 需要手動處理 xarray → NumPy → Tensor 轉換
- ❌ 需要手動處理 NaN 值
- ❌ 需要手動處理多變數合併
- ❌ 容易出錯，難以維護

**xbatcher.loaders.torch 的優勢**：
- ✅ 自動處理所有轉換（xarray → Tensor）
- ✅ 自動合併多變數成第一個維度
- ✅ 完整支援 Dask lazy evaluation
- ✅ 經過充分測試，穩定可靠
- ✅ 程式碼簡潔，易於維護

---

## 3.4 模型訓練（簡化示範）

> ⚠️ **重點提醒**：
>
> 這部分只是示範「資料 pipeline 通了」，不深入講解模型訓練技巧。
> 模型架構、訓練調參是另一堂課的內容。

### 簡單的 CNN 模型

```python
import torch.nn as nn
import torch.nn.functional as F

class SimpleConvNet(nn.Module):
    """
    超級簡單的 CNN（僅用於示範）

    Input: (batch, 4, 32, 16, 16)  # (batch, vars, time, lat, lon)
    Output: (batch, 2)              # (batch, num_classes)
    """

    def __init__(self, in_channels=4, num_classes=2):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 16×16 → 8×8

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))  # 全局平均池化 → 1×1
        )

        self.classifier = nn.Linear(64, num_classes)

    def forward(self, x):
        # x: (batch, vars, time, lat, lon)

        # 簡化：對時間維度取平均
        x = x.mean(dim=2)  # → (batch, vars, lat, lon)

        # CNN
        x = self.features(x)  # → (batch, 64, 1, 1)
        x = x.view(x.size(0), -1)  # → (batch, 64)

        # 分類
        x = self.classifier(x)  # → (batch, 2)

        return x
```

---

### 訓練一個 Batch（示範）

```python
import torch.optim as optim

# 建立模型
model = SimpleConvNet(in_channels=len(feature_vars), num_classes=2)
model = model.cuda()  # 移到 GPU

# 定義損失函數和優化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 訓練一個 batch（只是示範！）
model.train()

for X, y in train_loader:
    # 移到 GPU
    X = X.cuda()
    y = y.cuda()

    # 簡化標籤（取空間平均後二值化）
    # y shape: (batch, time, lat, lon) → (batch,)
    y_simple = (y.float().mean(dim=[1, 2, 3]) > 0.5).long()

    # 前向傳播
    outputs = model(X)
    loss = criterion(outputs, y_simple)

    # 反向傳播
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    print(f"✅ Loss: {loss.item():.4f}")
    print(f"✅ Pipeline 通了！資料能順利從 Zarr → Xarray → PyTorch")
    break  # 只跑一個 batch
```

**預期輸出**：
```
✅ Loss: 0.6931
✅ Pipeline 通了！資料能順利從 Zarr → Xarray → PyTorch
```

---

### 講解重點

跟學員強調：

1. **這只是證明 pipeline 可以運作**
   - 資料能從 Zarr 讀取
   - 經過 Xarray 處理
   - 透過 xbatcher 切批次
   - 進入 PyTorch 模型

2. **模型架構不重要**
   - 甚至可以用 `torchvision.models.resnet18`
   - 重點是「資料流」，不是「模型設計」

3. **真正的訓練是另一堂課**
   - Learning rate 調整
   - Regularization
   - Data augmentation
   - 這些都不在本課程範圍

---

## 3.5 預測結果 → Xarray

> 💡 **核心問題**：模型輸出是 Tensor/NumPy，如何轉回帶座標的 Xarray？
>
> **答案**：手動建立 `xr.DataArray`，保留原始座標資訊

### 為什麼需要轉回 Xarray？

傳統 ML workflow：
```
Model output: numpy array (n_samples,)
評估: sklearn.metrics.accuracy_score(y_true, y_pred)
結果: 0.85（只有一個數字）
```

科學資料 workflow：
```
Model output: xarray.DataArray with coords (time, lat, lon)
評估: xskillscore.rmse(pred, obs, dim='time')
結果: RMSE at every (lat, lon) point（一個空間場）
```

**差異**：
- 傳統方法：只知道「整體準確率 85%」
- 科學方法：知道「台灣北部預測好，南部預測差」

---

### 實作：空間預測

```python
# 建立驗證 Dataset（不 shuffle）
valid_dataset = XarrayDataset(
    valid_ds,
    feature_vars=feature_vars,
    label_var='convection_flag',
    batch_config=batch_config
)

valid_loader = DataLoader(
    valid_dataset,
    batch_size=1,
    shuffle=False,  # 重要！保持順序
    num_workers=2
)

# 預測
model.eval()
predictions = []

with torch.no_grad():
    for idx, (X, y) in enumerate(valid_loader):
        X = X.cuda()

        # 預測
        outputs = model(X)
        pred = outputs.argmax(dim=1).cpu().numpy()  # (batch,)

        # 這裡只有一個預測值（因為我們簡化了標籤）
        # 在實際應用中，你可能想保留空間維度

        predictions.append(pred)

        if idx >= 100:  # 只預測前 100 個 batch（示範）
            break

# 合併預測
pred_array = np.concatenate(predictions, axis=0)
print(f"Predictions shape: {pred_array.shape}")  # (101,)
```

---

### 實作：保留空間資訊的預測

如果你想要空間分佈的預測（而不是單一值），需要修改模型：

```python
class SpatialConvNet(nn.Module):
    """
    輸出空間預測的 CNN

    Input: (batch, 4, 32, 16, 16)
    Output: (batch, 2, 16, 16)  # 保留空間維度
    """

    def __init__(self, in_channels=4, num_classes=2):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, num_classes, 1)  # 1×1 conv，保留空間
        )

    def forward(self, x):
        # x: (batch, vars, time, lat, lon)
        x = x.mean(dim=2)  # → (batch, vars, lat, lon)
        x = self.features(x)  # → (batch, num_classes, lat, lon)
        return x

# 使用這個模型預測
spatial_model = SpatialConvNet().cuda()
# ... 訓練過程類似 ...

# 預測時，保留空間資訊
spatial_model.eval()
spatial_predictions = []
coords_list = []

with torch.no_grad():
    for idx, (X, y) in enumerate(valid_loader):
        X = X.cuda()

        outputs = spatial_model(X)  # (batch, 2, lat, lon)
        pred = outputs.argmax(dim=1).cpu().numpy()  # (batch, lat, lon)

        # 取得對應的座標
        batch_data = valid_dataset.batches[idx]

        # 建立 DataArray
        pred_da = xr.DataArray(
            pred[0],  # 取第一個（因為 batch_size=1）
            coords={
                'latitude': batch_data.latitude,
                'longitude': batch_data.longitude
            },
            dims=['latitude', 'longitude']
        )

        spatial_predictions.append(pred_da)

        if idx >= 100:
            break

# 合併所有 patch（需要處理 overlap）
# 這是一個進階話題，這裡先簡化
print(f"✅ 收集了 {len(spatial_predictions)} 個空間預測")
```

---

## 3.6 xskillscore 空間驗證

> 💡 **xskillscore 的核心優勢**：
>
> 可以計算「保留座標資訊」的驗證指標，知道「哪裡預測得好/差」

### 安裝與導入

```python
import xskillscore as xs
import numpy as np
import matplotlib.pyplot as plt
```

---

### 範例：計算 RMSE

```python
# 為了示範，我們先建立一些假資料
# 實際應用時，這會是你的模型預測

# 觀測值
obs = valid_ds['convection_flag'].isel(time=slice(0, 100))

# 假設的預測值（實際上應該來自模型）
# 這裡用觀測值加上一些雜訊
pred = obs + np.random.randn(*obs.shape) * 0.2
pred = pred.clip(0, 1)  # 限制在 [0, 1]

print(f"Observation shape: {obs.shape}")  # (100, 121, 161)
print(f"Prediction shape: {pred.shape}")

# 計算空間分佈的 RMSE（對時間維度）
rmse_spatial = xs.rmse(pred, obs, dim='time')

print("Spatial RMSE:")
print(rmse_spatial)  # (121, 161) - 每個格點的 RMSE
```

---

### 範例：計算多種指標

```python
# 1. Mean Absolute Error
mae = xs.mae(pred, obs, dim='time')

# 2. Mean Squared Error
mse = xs.mse(pred, obs, dim='time')

# 3. Pearson Correlation
corr = xs.pearson_r(pred, obs, dim='time')

# 4. R-squared
r2 = xs.r2(pred, obs, dim='time')

print(f"MAE (spatial mean): {mae.mean().values:.4f}")
print(f"MSE (spatial mean): {mse.mean().values:.4f}")
print(f"Correlation (spatial mean): {corr.mean().values:.4f}")
print(f"R² (spatial mean): {r2.mean().values:.4f}")
```

---

### 視覺化驗證結果

```python
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 建立圖表
fig, axes = plt.subplots(2, 3, figsize=(18, 10),
                          subplot_kw={'projection': ccrs.PlateCarree()})

# 第一列：觀測、預測、差異
t_idx = 0  # 第一個時間點

obs.isel(time=t_idx).plot(
    ax=axes[0, 0],
    cmap='RdBu_r',
    vmin=0, vmax=1,
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'Convection Flag'}
)
axes[0, 0].coastlines()
axes[0, 0].set_title('Observation (t=0)')

pred.isel(time=t_idx).plot(
    ax=axes[0, 1],
    cmap='RdBu_r',
    vmin=0, vmax=1,
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'Convection Flag'}
)
axes[0, 1].coastlines()
axes[0, 1].set_title('Prediction (t=0)')

(pred.isel(time=t_idx) - obs.isel(time=t_idx)).plot(
    ax=axes[0, 2],
    cmap='RdBu',
    vmin=-0.5, vmax=0.5,
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'Difference'}
)
axes[0, 2].coastlines()
axes[0, 2].set_title('Difference (Pred - Obs)')

# 第二列：驗證指標
rmse_spatial.plot(
    ax=axes[1, 0],
    cmap='viridis',
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'RMSE'}
)
axes[1, 0].coastlines()
axes[1, 0].set_title('RMSE (over time)')

corr.plot(
    ax=axes[1, 1],
    cmap='RdBu_r',
    vmin=-1, vmax=1,
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'Correlation'}
)
axes[1, 1].coastlines()
axes[1, 1].set_title('Correlation (over time)')

mae.plot(
    ax=axes[1, 2],
    cmap='viridis',
    transform=ccrs.PlateCarree(),
    cbar_kwargs={'label': 'MAE'}
)
axes[1, 2].coastlines()
axes[1, 2].set_title('MAE (over time)')

plt.tight_layout()
plt.savefig('validation_results.png', dpi=150, bbox_inches='tight')
plt.show()

print("✅ 驗證結果已儲存：validation_results.png")
```

---

### xskillscore 進階功能

#### 分類問題的混淆矩陣相關指標

```python
# 將預測和觀測轉成二元
pred_binary = (pred > 0.5).astype(int)
obs_binary = obs.astype(int)

# 可以使用 sklearn 計算混淆矩陣，然後可視化
from sklearn.metrics import confusion_matrix, classification_report

# 展平成 1D
pred_flat = pred_binary.values.ravel()
obs_flat = obs_binary.values.ravel()

# 計算
cm = confusion_matrix(obs_flat, pred_flat)
print("Confusion Matrix:")
print(cm)

report = classification_report(obs_flat, pred_flat, target_names=['No Convection', 'Convection'])
print("\nClassification Report:")
print(report)
```

#### 時間序列驗證

```python
# 計算時間序列的相關係數（對空間維度）
corr_temporal = xs.pearson_r(pred, obs, dim=['latitude', 'longitude'])

# 繪製時間序列
fig, ax = plt.subplots(figsize=(12, 4))
corr_temporal.plot(ax=ax)
ax.set_xlabel('Time')
ax.set_ylabel('Spatial Correlation')
ax.set_title('Temporal Evolution of Spatial Correlation')
ax.axhline(0.5, color='r', linestyle='--', label='Threshold')
ax.legend()
plt.tight_layout()
plt.savefig('temporal_correlation.png', dpi=150)
plt.show()
```

---

### 與傳統方法的對比

```python
# 傳統方法（sklearn）
from sklearn.metrics import accuracy_score, precision_score, recall_score

pred_flat = (pred > 0.5).astype(int).values.ravel()
obs_flat = obs.astype(int).values.ravel()

acc = accuracy_score(obs_flat, pred_flat)
prec = precision_score(obs_flat, pred_flat)
rec = recall_score(obs_flat, pred_flat)

print("=== 傳統方法（整體指標）===")
print(f"Accuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}")
print(f"Recall:    {rec:.4f}")

# xskillscore 方法（空間分佈）
print("\n=== xskillscore 方法（空間分佈）===")
print(f"RMSE (mean): {rmse_spatial.mean().values:.4f}")
print(f"RMSE (std):  {rmse_spatial.std().values:.4f}")
print(f"RMSE (min):  {rmse_spatial.min().values:.4f}")
print(f"RMSE (max):  {rmse_spatial.max().values:.4f}")

print("\n✅ xskillscore 可以告訴你「哪裡」預測得好/差！")
```

---

# 總結與下一步

## 本課程學到的核心技能

### 1. Zarr 儲存優化
- ✅ 理解 Zarr vs NetCDF 的差異
- ✅ 知道為何要用 Zarr < 3.0
- ✅ 能夠讀取並優化 Zarr 檔案

### 2. Xarray + Dask 資料處理
- ✅ 使用 lazy evaluation 處理超過記憶體的資料
- ✅ 時空切片與重採樣
- ✅ 理解 chunking 對效能的影響
- ✅ 使用 Dashboard 監控效能

### 3. ML Pipeline 建構
- ✅ 使用 xbatcher 切批次
- ✅ 建立 Xarray → PyTorch 橋接層
- ✅ 將預測結果轉回 Xarray
- ✅ 使用 xskillscore 進行空間驗證

---

## 重要觀念回顧

### Lazy Evaluation

```python
# Lazy（不計算）
result_lazy = ds['temperature'].mean(dim='time')

# Eager（計算）
result_eager = result_lazy.compute()
```

**何時用 lazy？**
- 探索資料時（想快速看結果）
- 建立複雜計算流程時
- 資料大於記憶體時

**何時用 compute？**
- 需要實際數值時
- 要儲存結果時
- 要繪圖或輸出時

---

### Chunking 策略

| Chunk Size | 任務數 | 記憶體 | 適用情境 |
|------------|--------|--------|----------|
| 小（10 MB） | 多 | 低 | 記憶體有限 |
| 中（50 MB） | 適中 | 適中 | **推薦** |
| 大（500 MB） | 少 | 高 | CPU 綁定的計算 |

**經驗法則**：
- 單個 chunk：10-100 MB
- 符合讀取模式（時間序列？空間切片？）
- 平衡任務數與傳輸開銷

---

### ML Pipeline 最佳實踐

```python
# 正確的資料流向（使用 xbatcher.loaders.torch）
Zarr files
  ↓ xr.open_zarr()
Xarray Dataset
  ↓ xbatcher.BatchGenerator()  [分開建立 X_bgen 和 y_bgen]
Lazy Batches
  ↓ xbatcher.loaders.torch.MapDataset(X_bgen, y_bgen)
PyTorch-compatible Dataset
  ↓ torch.utils.data.DataLoader(batch_size=None)
PyTorch DataLoader
  ↓ model.forward()
Predictions (Tensor)
  ↓ xr.DataArray()
Xarray DataArray with coords
  ↓ xskillscore
Spatial validation metrics
```

**關鍵點**：
- ✅ 使用 `xbatcher.loaders.torch.MapDataset`（不要自己寫 Dataset）
- ✅ DataLoader 的 `batch_size=None`（xbatcher 已定義）
- ✅ `preload_batch=False`（保持 lazy）
- ✅ `multiprocessing_context='forkserver'`（避免 pickle 問題）

---

## 常見問題與排錯

### Q1: `KeyError: 'Cannot find .zarray'`

**原因**：可能是 Zarr 3.0 的相容性問題

**解決**：
```bash
uv add "zarr>=2.18.0,<3.0.0"
```

---

### Q2: `MemoryError` 或 `Out of Memory`

**原因**：資料量超過記憶體

**解決方法**：
1. 增加 chunking（減少單次讀取量）
   ```python
   ds = xr.open_zarr('data.zarr', chunks={'time': 10, 'lat': 20, 'lon': 20})
   ```

2. 使用 `.compute()` 時先計算子集
   ```python
   result = ds.isel(time=slice(0, 100)).mean().compute()
   ```

3. 使用 `.persist()` 而不是 `.compute()`
   ```python
   result = ds.mean(dim='time').persist()  # 分散式記憶體
   ```

---

### Q3: Dask 計算很慢

**可能原因與解決**：

1. **Chunk 太小**：增加 chunk size
2. **Chunk 太大**：減少 chunk size
3. **Task overhead**：減少任務數量
4. **資料傳輸瓶頸**：檢查網路/磁碟速度

**診斷工具**：Dask Dashboard

---

### Q4: xbatcher 產生的 batch 數量不符預期

**檢查點**：
```python
print(f"Data shape: {ds.dims}")
print(f"Batch config: {batch_config}")

# 計算預期的 batch 數
n_time_batches = len(ds.time) // batch_config['batch_dims']['time']
n_lat_patches = (len(ds.latitude) - batch_config['input_dims']['latitude']) // (batch_config['input_dims']['latitude'] - batch_config['input_overlap']['latitude']) + 1
n_lon_patches = (len(ds.longitude) - batch_config['input_dims']['longitude']) // (batch_config['input_dims']['longitude'] - batch_config['input_overlap']['longitude']) + 1

expected_batches = n_time_batches * n_lat_patches * n_lon_patches
print(f"Expected batches: {expected_batches}")
```

---

### Q5: PyTorch DataLoader `num_workers > 0` 時出錯

**常見錯誤**：
```
RuntimeError: DataLoader worker (pid 12345) is killed by signal: Killed.
```

**可能原因**：
1. 記憶體不足（workers 複製資料）
2. Dask client 的 pickle 問題
3. 使用了錯誤的 `multiprocessing_context`

**解決方法**：

```python
# ✅ 推薦做法：使用 'forkserver' context
train_loader = DataLoader(
    dataset,
    batch_size=None,
    num_workers=4,
    persistent_workers=True,
    multiprocessing_context='forkserver'  # 關鍵！
)

# 如果仍有問題，檢查：
# 1. 是否使用 xbatcher.loaders.torch.MapDataset（而非自己寫的 Dataset）
# 2. 是否設定 preload_batch=False
# 3. 是否設定 batch_size=None
```

**Debug 時的臨時方案**：
```python
# 先用 num_workers=0 確認邏輯正確
train_loader = DataLoader(dataset, batch_size=None, num_workers=0)
```

---

## 延伸學習資源

### 官方文件

- **Xarray**: https://docs.xarray.dev/
- **Dask**: https://docs.dask.org/
- **Zarr**: https://zarr.readthedocs.io/
- **xbatcher**: https://xbatcher.readthedocs.io/
- **xskillscore**: https://xskillscore.readthedocs.io/

### 進階主題

#### 1. 分散式運算（Dask Cluster）
```python
from dask.distributed import Client
from dask_jobqueue import SLURMCluster

# 在 HPC 上建立 cluster
cluster = SLURMCluster(cores=4, memory='16GB')
cluster.scale(jobs=10)  # 啟動 10 個 workers

client = Client(cluster)
```

#### 2. 雲端儲存（S3, GCS）
```python
import fsspec

# 從 S3 讀取 Zarr
ds = xr.open_zarr(
    's3://bucket-name/data.zarr',
    storage_options={'anon': True}
)
```

#### 3. GPU 加速（cupy, cuDF）
```python
# 使用 CuPy 加速 Dask Array
import cupy as cp
import dask.array as da

# 建立 GPU array
x = da.from_array(cp.random.random((10000, 10000)), chunks=(1000, 1000))
result = x.mean().compute()  # 在 GPU 上計算
```

---

## 下一步建議

### 如果你想深入資料處理：
- 學習 Dask DataFrame（Part 2，如果開課的話）
- 探索 Polars / DuckDB（高效能表格處理）
- 研究 Apache Arrow（記憶體格式）

### 如果你想深入 ML：
- 學習 PyTorch Lightning（高階訓練框架）
- 探索 Hugging Face Datasets（ML 資料集工具）
- 研究 Ray（分散式 ML）

### 如果你想深入氣象應用：
- 探索 MetPy（氣象計算）
- 學習 Satpy（衛星資料處理）
- 研究 Climate Data Operators (CDO)

---

## 附錄 A: 套件版本建議

### pyproject.toml

```toml
[project]
name = "dask-array-workshop"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    # 核心
    "xarray>=2024.10.0",
    "zarr>=2.18.0,<3.0.0",  # 重要！< 3.0
    "dask[complete]>=2024.10.0",
    "numpy>=2.1.0",

    # 視覺化
    "matplotlib>=3.9.0",
    "cartopy>=0.23.0",

    # ML
    "xbatcher>=0.3.0",
    "xskillscore>=0.0.26",
    "torch>=2.0.0",
    "torchvision>=0.15.0",

    # 其他
    "fsspec>=2024.9.0",
    "netCDF4>=1.7.0",  # 如果需要讀取 NetCDF
]

[dependency-groups]
dev = [
    "ipykernel>=6.29.0",
    "jupyterlab>=4.0.0",
    "pytest>=8.0.0",
]
```

---

## 附錄 B: 參考文獻

### 重要論文

1. **Zarr**:
   - Moore, J., & Rocklin, M. (2018). Zarr: chunked, compressed, N-dimensional arrays.

2. **Xarray**:
   - Hoyer, S., & Hamman, J. (2017). xarray: N-D labeled arrays and datasets in Python. Journal of Open Research Software, 5(1).

3. **Dask**:
   - Rocklin, M. (2015). Dask: Parallel computation with blocked algorithms and task scheduling.

### 相關工具

- **Pangeo**: 大氣與海洋科學的開源社群
  - https://pangeo.io/

- **Intake**: 資料目錄系統
  - https://intake.readthedocs.io/

- **Xarray-spatial**: 地理空間分析
  - https://xarray-spatial.org/

---

## 課程回饋

請協助填寫課程回饋表（連結），您的意見對我們非常重要！

**感謝參與本次課程！**

---

**文件版本**: v1.0
**最後更新**: 2025-10-29
**授權**: CC BY 4.0
