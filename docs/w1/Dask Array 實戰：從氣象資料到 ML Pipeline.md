# Dask Array 實戰：從氣象資料到 ML Pipeline

# Dask Array 實戰：從氣象資料到 ML Pipeline

---

## 課程簡介

<aside>
📢

### 本工作坊是「Python 大數據處理三部曲」的第二部：N-D Array 處理篇

當你的氣象資料從 GB 成長到 TB 級別，傳統的 NetCDF + Xarray 單機處理方式將會遭遇瓶頸。本課程將帶你使用 Zarr + Dask + Xarray 的現代化工作流程，實現真正的 out-of-core 分析，並將資料無縫接入 PyTorch 進行機器學習。

</aside>

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
- ✅ 理解 GIL, Processes vs. Threads（已完成 Part 1 課程）

---

## 課程架構

```
Part 0: 環境設定
├── uv 專案管理
├── Jupyter Kernel 設定
└── Dask Dashboard 啟動

Part 1: Zarr 與 Xarray 基礎
├── 為什麼需要 Zarr？
├── Zarr vs NetCDF 對照
└── 實作：讀取與探索
		└── 時空切片

Part 2: 時空資料處理
├── 多檔案讀取
├── 重採樣&重投影
├── 計算與儲存優化 
└── rechunker 存成 zarr

Part 3: ML Pipeline 
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

> 💡 為什麼用 uv？
> 
> 
> `uv` 是新一代的 Python 套件管理工具，比傳統的 pip + virtualenv 快 10-100 倍，且能自動處理相依性衝突。
> 

### 安裝 uv

```bash
# 如果還沒安裝 
uvcurl -LsSf https://astral.sh/uv/install.sh | sh # 驗證安裝uv --version
```

### 初始化專案

```bash
git clone https://github.com/Isongzhe/python-parallel-data-processing.git
cd python-parallel-data-processing
```

### 安裝相依套件 & 檢查環

```bash
uv sync 
uv run python -c "import xarray, dask, zarr; print('Environment OK!')"
```

## 0.2 VSCode Jupyter Kernel 設定

### 步驟 1: 建立 Jupyter Kernel

```bash
# 使用 uv 建立 kernel
uv add --dev ipykernel
uv run python -m ipykernel install --user --name dask-workshop --display-name "python-parallel-data-processing"
```

### 步驟 2: 在 VSCode 選擇 Kernel

1. 打開 VSCode
2. 建立新的 `.ipynb` 檔案
3. 點擊右上角「選擇核心」
4. 選擇 `python-parallel-data-processing`

### 步驟 3: 測試連線

在 Notebook 中執行：

```python
# 測試 Cellimport xarray as xr
import dask
import zarr
print(f"Xarray version: {xr.__version__}")
print(f"Dask version: {dask.__version__}")
print(f"Zarr version: {zarr.__version__}")
# 確認 Zarr < 3.0assert int(zarr.__version__.split('.')[0]) < 3, "請確認 Zarr 版本 < 3.0"print("✅ 環境設定完成！")
```

## 0.3 啟動 Dask Dashboard

> 💡 Dask Dashboard 是什麼？
> 
> 
> Dashboard 是一個網頁介面，可以即時觀察：
> - Task Graph（任務依賴關係）
> - Task Stream（任務執行時間線）
> - Memory Usage（記憶體使用情況）
> - Workers Status（工作程序狀態）
> 

### 啟動 Client

在 Jupyter Notebook 中執行：

```python
from dask.distributed import Client
# 啟動本地 Clusterclient = Client()
# 顯示 Dashboard 連結print(client)
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
    # 在本機執行ssh -L 8787:localhost:8787 user@remote-server
    # 然後在本機瀏覽器訪問# http://localhost:8787/status
    ```
    
3. **VSCode Remote SSH**：VSCode 會自動轉發 port，直接點擊連結即可

### Dashboard 重要頁面

- **Status**: 總覽
- **Task Stream**: 即時任務執行（最常用）
- **Progress**: 進度條
- **Graph**: 任務相依圖
- **System**: CPU/Memory 使用率

# Part 1: Zarr 與 Xarray 基礎

<aside>
📖

**對照**: /w1/notebooks/01-data-loading-basics.ipynb 

</aside>

## 1.1 為什麼需要 Zarr？

### 傳統 NetCDF 的痛點

[Cloud-Optimized HDF/NetCDF – Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/cloud-optimized-netcdf4-hdf5/)

<aside>
📖

NetCDF-4 是一種檔案格式，它**使用 HDF5 作為底層的儲存格式**。

</aside>

❌ 多檔案**讀取速度慢**

- **元資料散佈**：元資料可能散布在檔案的各個區塊，需要進行多次 I/O 讀取才能拼湊出完整的檔案結構圖。當你嘗試用 `xarray.open_mfdataset()` 一次開啟數千個 NetCDF 檔案時，程式會逐一讀取每個檔案，尋找並解析這些散布的元資料，導致極大的延遲。
- **元資料鎖**：HDF5 為了確保檔案的一致性，在進行修改時會啟動鎖定機制。這種鎖定對於並行寫入非常不利。在 `open_mfdataset` 這種多檔串接情境中，即使是讀取，後續的計算也可能因底層的 HDF5 檔案存取而相互等待。

```python
# 處理多檔案超級久
ds = xr.open_mfdataset('*.nc')  # 掃描所有 metadata

# NetCDF 有 metadata lock，無法真正平行
# 多個 process 同時讀取 → 互相等待
```

❌ **雲端不友善 (ex. Himawri** https://noaa-himawari9.s3.amazonaws.com/index.html#AHI-L2-FLDK-Clouds/2025/10/10/0000/)

- 性**非雲端原生**：這種設計對於傳統的檔案系統（本地硬碟）很有效，但在雲端儲存（如 S3）中卻效率低下。在雲端，每次讀取都需要發出 HTTP Range Request。如果元資料散布在檔案中，讀取元資料就必須發出多次請求，而不是一次下載。

```python
# 如果資料在 S3/GCS 上...

# NetCDF 需要下載整個檔案才能讀取
# Zarr 
xr.open_zarr('gs://weatherbench2/datasets/era5/1959-2023_01_10-wb13-6h-1440x721_with_derived_variables.zarr')
```

---

### Zarr 的解決方案

**目錄結構，每個 chunk 是獨立檔案**

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

**真正的平行讀寫**

- 沒有 metadata lock
- 每個 worker 讀取不同的 chunk 檔案
- 可以同時寫入不同的 chunk

**雲端原生設計**

- 只下載需要的 chunk
- 支援 S3, GCS, Azure Blob
- HTTP Range Request 友善

<aside>
📖

現在多個機構會把 TB 級的資料放到 GCP / AWS s3 再提供出去，例如：[WeatherBench ERA5](https://weatherbench2.readthedocs.io/en/latest/data-guide.html#era5) 

</aside>

## 1.2 Zarr vs NetCDF 完整對照

| 特性 | NetCDF (HDF5) | Zarr | 說明 |
| --- | --- | --- | --- |
| **檔案結構** | 單一檔案 | 目錄 + 多個檔案 | Zarr 每個 chunk 獨立 |
| **Metadata** | 集中式（有 lock） | 分散式（無 lock） | Zarr 可平行讀寫 |
| **平行讀取** | 受限 | 完全支援 | NetCDF 有競爭問題 |
| **平行寫入** | 不支援 | 完全支援 | Zarr 可同時寫不同 chunk |
| **雲端儲存** | 需完整下載 | 只下載需要的 chunk | Zarr 節省頻寬 |
| **壓縮選項** | 有限（zlib, gzip） | 豐富（Blosc, Zstd, LZ4…） | Zarr 壓縮更快更好 |
| **追加資料** | 困難 | 容易 | Zarr 直接新增 chunk |
| **生態系支援** | 成熟（幾十年） | 新興（快速成長） | NetCDF 仍是主流格式 |

[A Comparison of HDF5, Zarr, and netCDF4 in Performing Common I/O Operations](https://arxiv.org/abs/2207.09503)

<aside>
⚠️

### 為什麼必須用 Zarr < 3.0？

**Zarr 2.x（推薦用於生產環境）**

```
era5.zarr/
├── .zattrs          # JSON 格式
├── .zgroup
├── temperature/
│   ├── .zarray      # 陣列 metadata
│   └── 0.0.0        # chunk 命名：維度索引
```

**Zarr 3.x（2024，仍在穩定中)** 

```
era5.zarr/
├── zarr.json        # 新的 metadata 格式
├── temperature/
│   ├── zarr.json    # 統一格式
│   └── c/0/0/0      # 新的 chunk 命名：c/ 前綴
```

**主要變更**

| 項目 | Zarr 2.x | Zarr 3.x |
| --- | --- | --- |
| Metadata 格式 | `.zarray`, `.zattrs` | 統一的 `zarr.json` |
| Chunk 命名 | `0.1.2` | `c/0/1/2` |
| Storage API | `store[key]` | 新的 abstract API |
| 壓縮器 | `numcodecs` | 可插拔的 codec pipeline |
</aside>

---

## 1.3 Part1 - 實作：讀取與探索 ERA5 資料

<aside>

**來源**：ERA5 Reanalysis
**空間範圍**：10°N-40°N, 100°E-140°E（東亞-西太平洋）
**時間範圍**：2019-2023（5 年）
**變數**：溫度、濕度、風場、對流參數、降水等

</aside>

### 重點 1: 讀取資料

[Reading and writing files](https://docs.xarray.dev/en/stable/user-guide/io.html)

<aside>
👉

先載 Engine 來解析你的資料格式，不然開不起來 (ex. **zarr / h5netcdf )**

[xarray.open_dataset](https://docs.xarray.dev/en/stable/generated/xarray.open_dataset.html)

</aside>

```python
import xarray as xr
import dask

# open h5 / netcdf 
ds = xr.open_dataset(..., engine = 'h5netcdf', chunk='auto')

# open zarr with dask 
ds_dask_lazy = xr.open_zarr(...)
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
    temperature  (time, level, latitude, longitude) float32 dask.array<...>
    specific_humidity  (time, level, latitude, longitude) float32 dask.array<...>
    total_precipitation  (time, latitude, longitude) float32 dask.array<...>
    ...
```

**重點觀察**

1. **`dask.array<...>`**：這表示資料還沒有真正讀入記憶體（lazy）
2. **Dimensions**：4 個維度（時間、緯度、經度、氣壓層）
3. **Coordinates**：每個維度都有座標值

<aside>
👉

我都會盡可能使用 `intake-xarray` 來讀取檔案: 

- 集中管理：所有資料來源定義在 `catalog.yaml`
- 描述性：每個資料集有 description，方便團隊協作
- 可攜性：換環境只需修改 catalog，code 不用動

```markdown
# 路徑寫死
ds_2019 = xr.open_zarr('.../era5_2019_10N40N_100E140E.zarr')

# intake 
catalog = intake.open_catalog('catalog.yaml')
ds = catalog.era5_2019_raw.to_dask() # catalog.dataset_name 
```

</aside>

---

### 重點 2: Chunking 的重要性 !!!

<aside>

良好的 chunking：
✅ 每個 chunk 大小適中（10-100 MB）
✅ 符合你的讀取模式（時間序列？空間切片？）
✅ 平衡任務數量與傳輸開銷

不良的 chunking：
❌ 太小：產生過多任務，調度開銷大
❌ 太大：記憶體壓力大，平行度低
❌ 不符合讀取模式：需要讀取大量無用資料

</aside>

```python
# 查看 chunks
print(ds.chunks)
# 查看單一變數的 chunks
print(ds['temperature'].chunks)

**輸出範例**：
Frozen({'time': (24, 24, 24, ...),
        'latitude': (50, 50, 21),
        'longitude': (50, 50, 50, 11),
        'level': (13,)})
        
這表示：
- 時間維度：每 24 小時一個 chunk（一天）
- 緯度：每 50 個格點一個 chunk
- 經度：每 50 個格點一個 chunk
- 氣壓層：全部在一起（13 層）
```

<aside>
📖

該如何選擇 good chunk sizes 可以參考這兩篇文章：

https://blog.dask.org/2021/11/02/choosing-dask-chunk-sizes

https://docs.dask.org/en/latest/array-chunks.html

</aside>

### 重點 3: Xarray Data Structures

[Xarray in 45 minutes](https://tutorial.xarray.dev/overview/xarray-in-45-min.html)

<aside>
📖

Xarray provides two main data structures:

1. [**`DataArrays`**](https://docs.xarray.dev/en/stable/user-guide/data-structures.html#dataarray) that wrap underlying data containers (e.g. numpy arrays) and contain associated metadata
2. [**`Datasets`**](https://docs.xarray.dev/en/stable/user-guide/data-structures.html#dataset) that are dictionary-like containers of DataArrays

DataArrays contain underlying arrays and associated metadata:

1. Name
2. Dimension names
3. Coordinate variables
4. and arbitrary attributes.
</aside>

---

# Part2 - 實作: 時空資料處理

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

### `parallel=True`

```python
# parallel=True：平行讀取各檔案的 metadata # 速度快，但要確保檔案結構一致
# parallel=False：序列讀取（預設）# 較慢，但更安全
```

### `chunks` 參數

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

### 儲存成 Zarr

### 基本儲存

```python
# 儲存距平資料
output_path = './taiwan_summer_anomaly.zarr'
anomaly.to_zarr(
    output_path,
    mode='w',              # 'w' = 覆寫, 'a' = 追加    consolidated=True      # 合併 metadata（重要！加速讀取）)
print(f"✅ 已儲存到：{output_path}")
```

### 進階：壓縮設定

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
# 比較大小import os
import subprocess
# 原始大小（未壓縮）raw_size = anomaly.nbytes / 1e9print(f"原始大小：{raw_size:.2f} GB")
# 壓縮後大小compressed_size = float(subprocess.check_output(['du', '-sb', output_path]).split()[0]) / 1e9print(f"壓縮後大小：{compressed_size:.2f} GB")
print(f"壓縮率：{raw_size / compressed_size:.2f}x")
```

### 壓縮演算法選擇

| 壓縮器 | 速度 | 壓縮率 | 適用情境 |
| --- | --- | --- | --- |
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
# 準備測試資料（選一個子集）ds_test = ds_multi.sel(time=slice('2019-01', '2019-12'))
# 測試不同的 chunk 大小chunk_configs = [
    {'time': 10, 'latitude': 20, 'longitude': 20},   # 小 chunk    {'time': 24, 'latitude': 50, 'longitude': 50},   # 中等 chunk    {'time': 100, 'latitude': 100, 'longitude': 100} # 大 chunk]
results = []
for config in chunk_configs:
    # Rechunk    ds_rechunked = ds_test.chunk(config)
    # 執行相同計算：全域平均    start = time.time()
    result = ds_rechunked['temperature'].mean().compute()
    elapsed = time.time() - start
    results.append({
        'config': config,
        'time': elapsed,
        'n_tasks': len(ds_rechunked['temperature'].__dask_graph__())
    })
    print(f"Chunk size {config}: {elapsed:.2f}s, {results[-1]['n_tasks']} tasks")
# 視覺化import pandas as pd
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
# 測試會不會 OOM 的操作# 情況 1: Lazy 操作（不會 OOM）large_result = ds_multi['temperature'].mean(dim='time')
print(f"Lazy result created. Memory usage: {large_result.nbytes / 1e9:.2f} GB (虛擬)")
# 情況 2: Eager 操作（可能 OOM）try:
    large_result_eager = large_result.compute()
    print(f"Computed! Memory usage: {large_result_eager.nbytes / 1e9:.2f} GB")
except MemoryError:
    print("❌ Out of Memory!")
# 情況 3: Persist（載入到分散式記憶體）large_result_persist = large_result.persist()
# 這會將結果分散儲存在 Dask workers 的記憶體中print("✅ Persisted to distributed memory")
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

### 對流指標

我們使用以下參數來預測對流：

| 參數 | 縮寫 | 意義 | 典型對流值 |
| --- | --- | --- | --- |
| **Convective Available Potential Energy** | CAPE | 對流可用位能（能量） | > 1000 J/kg |
| **Convective Inhibition** | CIN | 對流抑制（阻礙） | < -50 J/kg |
| **K-Index** | KI | 綜合不穩定指數 | > 30 |
| **Boundary Layer Height** | BLH | 邊界層高度 | > 1500 m |

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

### 實作：準備資料

```python
import xarray as xr
import numpy as np
# 讀取訓練資料（2019-2020）train_files = [
    '/home/sungche/NAS/dataset/era5/era5_2019_10N40N_100E140E.zarr',
    '/home/sungche/NAS/dataset/era5/era5_2020_10N40N_100E140E.zarr']
ds_train = xr.open_mfdataset(
    train_files,
    engine='zarr',
    parallel=True,
    chunks={'time': 24, 'latitude': 50, 'longitude': 50}
)
# 選取特徵變數feature_vars = [
    'convective_available_potential_energy',
    'convective_inhibition',
    'k_index',
    'boundary_layer_height']
features = ds_train[feature_vars]
# 建立標籤（降雨 > 5mm/hr 定義為對流）# ERA5 降雨單位通常是累積量，需要轉換成 mm/hrprecip_threshold = 5  # mm/hrlabel = (ds_train['total_precipitation'] > precip_threshold).astype(int)
label.name = 'convection_flag'# 合併成訓練資料集train_ds = xr.merge([features, label])
print("Training dataset:")
print(train_ds)
print(f"\n對流事件比例：{label.mean().compute().values * 100:.2f}%")
```

### 準備驗證資料

```python
# 讀取驗證資料（2021）ds_valid = xr.open_zarr('/home/sungche/NAS/dataset/era5/era5_2021_10N40N_100E140E.zarr')
valid_ds = xr.merge([
    ds_valid[feature_vars],
    (ds_valid['total_precipitation'] > precip_threshold).astype(int).rename('convection_flag')
])
print("Validation dataset:")
print(valid_ds)
```

## 3.2 xbatcher：批次切割

> 💡 核心問題：如何把 TB 級的 Xarray 資料餵給 PyTorch？
> 
> 
> **答案**：使用 `xbatcher` 切成小批次，lazy 讀取
> 

### xbatcher 簡介

**xbatcher** 是專為 Xarray 設計的批次產生器：
- 自動切割空間/時間維度
- 支援 overlap（避免邊界效應）
- 完全 lazy（不會一次載入所有資料）
- 與 Dask 完美整合

### 基本使用

```python
import xbatcher
# 建立 BatchGeneratorbgen = xbatcher.BatchGenerator(
    train_ds,
    input_dims={'latitude': 16, 'longitude': 16},     # 空間 patch size    input_overlap={'latitude': 4, 'longitude': 4},    # 50% overlap    batch_dims={'time': 32}                            # 時間批次大小)
print(f"Total batches: {len(bgen)}")
# 查看第一個 batchfor i, batch in enumerate(bgen):
    print(f"\n--- Batch {i} ---")
    print(batch)
    print(f"CAPE shape: {batch['convective_available_potential_energy'].shape}")
    print(f"Label shape: {batch['convection_flag'].shape}")
    if i == 0:  # 只看第一個        break
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

### 參數詳解

### `input_dims`

```python
# 空間 patch 的大小input_dims={'latitude': 16, 'longitude': 16}
# 如何選擇？# - 太小（如 4×4）：context 不足，模型難學習# - 太大（如 128×128）：記憶體需求高，batch size 受限# - 推薦：16×16 到 64×64
```

### `input_overlap`

```python
# Patch 之間的重疊input_overlap={'latitude': 4, 'longitude': 4}  # 25% overlap# 為什麼需要 overlap？# - 避免邊界效應（CNN 在邊界的預測較差）# - 增加訓練資料量（data augmentation）# - 讓相鄰 patch 之間有連續性
```

### `batch_dims`

```python
# 在時間維度上批次化batch_dims={'time': 32}
# 注意：# - 這會產生 32 個時間點的序列# - 如果你的模型不處理時序，可以之後再平均或選取# - 也可以設定其他維度，如 {'latitude': 4}（但較少見）
```

### 轉換成 NumPy

```python
# 取得一個 batchbatch = next(iter(bgen))
# 方法 1: to_array（推薦）# 將多個變數合併成一個新維度 'variable'X = batch[feature_vars].to_array(dim='variable').values
y = batch['convection_flag'].values
print(f"X shape: {X.shape}")  # (4, 32, 16, 16) = (variables, time, lat, lon)print(f"y shape: {y.shape}")  # (32, 16, 16) = (time, lat, lon)# 方法 2: 手動 stackX_manual = np.stack([batch[var].values for var in feature_vars], axis=0)
```

### 進階：動態批次（Iterable）

```python
# 如果資料太大，不想預先生成所有 batch 索引# 可以直接迭代（更省記憶體）for i, batch in enumerate(bgen):
    # 處理 batch    X = batch[feature_vars].to_array(dim='variable').values
    y = batch['convection_flag'].values
    print(f"Batch {i}: X={X.shape}, y={y.shape}")
    if i >= 5:  # 只看前 5 個        break# 這樣做的好處：# - 不會一次生成所有 batch 的索引# - 記憶體使用更少# - 適合超大資料集
```

## 3.3 PyTorch DataLoader 橋接

### 目標

建立一個「橋接層」，讓 PyTorch 的 `DataLoader` 能夠讀取 `xbatcher` 產生的資料。

### 實作：XarrayDataset

```python
from torch.utils.data import Dataset, DataLoader
import torch
import numpy as np
class XarrayDataset(Dataset):
    """    將 xbatcher 包裝成 PyTorch Dataset    這是一個可重複使用的橋接層！    """    def __init__(self, ds, feature_vars, label_var, batch_config):
        """        Args:            ds: xarray.Dataset（輸入資料）            feature_vars: list of str（特徵變數名稱）            label_var: str（標籤變數名稱）            batch_config: dict（xbatcher 設定）        """        self.ds = ds
        self.feature_vars = feature_vars
        self.label_var = label_var
        # 建立 BatchGenerator        self.bgen = xbatcher.BatchGenerator(ds, **batch_config)
        # 預先生成所有 batch（只是索引，不是資料）        self.batches = list(self.bgen)
        print(f"✅ XarrayDataset initialized with {len(self.batches)} batches")
    def __len__(self):
        return len(self.batches)
    def __getitem__(self, idx):
        """        取得第 idx 個 batch（這時才真正讀取資料）        """        # 取得 batch        batch = self.batches[idx]
        # 轉成 NumPy（這時會 compute）        X = batch[self.feature_vars].to_array(dim='variable').values
        y = batch[self.label_var].values
        # 處理 NaN（如果有）        X = np.nan_to_num(X, nan=0.0)
        y = np.nan_to_num(y, nan=0)
        # 轉成 Torch Tensor        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y)
        return X_tensor, y_tensor
```

### 建立 DataLoader

```python
# 定義 batch 設定batch_config = {
    'input_dims': {'latitude': 16, 'longitude': 16},
    'input_overlap': {'latitude': 4, 'longitude': 4},
    'batch_dims': {'time': 32}
}
# 建立訓練 Datasettrain_dataset = XarrayDataset(
    train_ds,
    feature_vars=feature_vars,
    label_var='convection_flag',
    batch_config=batch_config
)
# 建立 DataLoadertrain_loader = DataLoader(
    train_dataset,
    batch_size=4,        # 一次讀 4 個 xarray batch    shuffle=True,        # 訓練時打亂    num_workers=2,       # 平行讀取（重要！）    pin_memory=True,     # GPU 優化    persistent_workers=True  # 保持 workers 存活（加速）)
print(f"✅ DataLoader created with {len(train_loader)} batches")
# 測試一下for X, y in train_loader:
    print(f"X: {X.shape}, dtype: {X.dtype}, device: {X.device}")
    print(f"y: {y.shape}, dtype: {y.dtype}, device: {y.device}")
    break
```

**輸出範例**：

```
✅ XarrayDataset initialized with 1250 batches
✅ DataLoader created with 313 batches
X: torch.Size([4, 4, 32, 16, 16]), dtype: torch.float32, device: cpu
y: torch.Size([4, 32, 16, 16]), dtype: torch.int64, device: cpu
```

### 重要參數說明

### `num_workers`

```python
# num_workers=0：主程序讀取（慢）# num_workers=2：開 2 個子程序平行讀取（快）# num_workers=4：開 4 個子程序（更快，但記憶體需求高）# 推薦設定：# - CPU 充足：num_workers = CPU cores / 2# - 記憶體有限：num_workers = 2# - Debug 時：num_workers = 0（避免多程序錯誤難追蹤）
```

### `pin_memory`

```python
# pin_memory=True（推薦，如果有 GPU）# - 將資料固定在 CPU 記憶體中# - 加速 CPU → GPU 資料傳輸# pin_memory=False# - 不使用 GPU 時，或記憶體不足時
```

### `persistent_workers`

```python
# persistent_workers=True（推薦）# - 保持 workers 存活，不用每個 epoch 重啟# - 加速訓練，特別是多 epoch 時# persistent_workers=False# - 每個 epoch 結束後關閉 workers# - 節省記憶體，但每次重啟有開銷
```

### Dashboard 觀察

執行以下程式碼，觀察 Dashboard：

```python
# 迭代幾個 batch，觀察 Dashboardfor i, (X, y) in enumerate(train_loader):
    print(f"Batch {i}: X={X.shape}")
    if i >= 5:
        break
```

**觀察重點**：
- **Task Stream**：看到資料讀取任務（藍色）
- **Workers**：`num_workers=2` 時，會看到多個 workers 同時工作
- **Memory**：記憶體使用會波動（讀取 → 處理 → 釋放）

## 3.4 模型訓練（簡化示範）

> ⚠️ 重點提醒：
> 
> 
> 這部分只是示範「資料 pipeline 通了」，不深入講解模型訓練技巧。
> 模型架構、訓練調參是另一堂課的內容。
> 

### 簡單的 CNN 模型

```python
import torch.nn as nn
import torch.nn.functional as F
class SimpleConvNet(nn.Module):
    """    超級簡單的 CNN（僅用於示範）    Input: (batch, 4, 32, 16, 16)  # (batch, vars, time, lat, lon)    Output: (batch, 2)              # (batch, num_classes)    """    def __init__(self, in_channels=4, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),  # 16×16 → 8×8            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))  # 全局平均池化 → 1×1        )
        self.classifier = nn.Linear(64, num_classes)
    def forward(self, x):
        # x: (batch, vars, time, lat, lon)        # 簡化：對時間維度取平均        x = x.mean(dim=2)  # → (batch, vars, lat, lon)        # CNN        x = self.features(x)  # → (batch, 64, 1, 1)        x = x.view(x.size(0), -1)  # → (batch, 64)        # 分類        x = self.classifier(x)  # → (batch, 2)        return x
```

### 訓練一個 Batch（示範）

```python
import torch.optim as optim
# 建立模型model = SimpleConvNet(in_channels=len(feature_vars), num_classes=2)
model = model.cuda()  # 移到 GPU# 定義損失函數和優化器criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
# 訓練一個 batch（只是示範！）model.train()
for X, y in train_loader:
    # 移到 GPU    X = X.cuda()
    y = y.cuda()
    # 簡化標籤（取空間平均後二值化）    # y shape: (batch, time, lat, lon) → (batch,)    y_simple = (y.float().mean(dim=[1, 2, 3]) > 0.5).long()
    # 前向傳播    outputs = model(X)
    loss = criterion(outputs, y_simple)
    # 反向傳播    optimizer.zero_grad()
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

## 3.5 預測結果 → Xarray

> 💡 核心問題：模型輸出是 Tensor/NumPy，如何轉回帶座標的 Xarray？
> 
> 
> **答案**：手動建立 `xr.DataArray`，保留原始座標資訊
> 

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

### 實作：空間預測

```python
# 建立驗證 Dataset（不 shuffle）valid_dataset = XarrayDataset(
    valid_ds,
    feature_vars=feature_vars,
    label_var='convection_flag',
    batch_config=batch_config
)
valid_loader = DataLoader(
    valid_dataset,
    batch_size=1,
    shuffle=False,  # 重要！保持順序    num_workers=2)
# 預測model.eval()
predictions = []
with torch.no_grad():
    for idx, (X, y) in enumerate(valid_loader):
        X = X.cuda()
        # 預測        outputs = model(X)
        pred = outputs.argmax(dim=1).cpu().numpy()  # (batch,)        # 這裡只有一個預測值（因為我們簡化了標籤）        # 在實際應用中，你可能想保留空間維度        predictions.append(pred)
        if idx >= 100:  # 只預測前 100 個 batch（示範）            break# 合併預測pred_array = np.concatenate(predictions, axis=0)
print(f"Predictions shape: {pred_array.shape}")  # (101,)
```

### 實作：保留空間資訊的預測

如果你想要空間分佈的預測（而不是單一值），需要修改模型：

```python
class SpatialConvNet(nn.Module):
    """    輸出空間預測的 CNN    Input: (batch, 4, 32, 16, 16)    Output: (batch, 2, 16, 16)  # 保留空間維度    """    def __init__(self, in_channels=4, num_classes=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, num_classes, 1)  # 1×1 conv，保留空間        )
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

## 3.6 xskillscore 空間驗證

> 💡 xskillscore 的核心優勢：
> 
> 
> 可以計算「保留座標資訊」的驗證指標，知道「哪裡預測得好/差」
> 

### 安裝與導入

```python
import xskillscore as xs
import numpy as np
import matplotlib.pyplot as plt
```

### 範例：計算 RMSE

```python
# 為了示範，我們先建立一些假資料# 實際應用時，這會是你的模型預測# 觀測值obs = valid_ds['convection_flag'].isel(time=slice(0, 100))
# 假設的預測值（實際上應該來自模型）# 這裡用觀測值加上一些雜訊pred = obs + np.random.randn(*obs.shape) * 0.2pred = pred.clip(0, 1)  # 限制在 [0, 1]print(f"Observation shape: {obs.shape}")  # (100, 121, 161)print(f"Prediction shape: {pred.shape}")
# 計算空間分佈的 RMSE（對時間維度）rmse_spatial = xs.rmse(pred, obs, dim='time')
print("Spatial RMSE:")
print(rmse_spatial)  # (121, 161) - 每個格點的 RMSE
```

### 範例：計算多種指標

```python
# 1. Mean Absolute Errormae = xs.mae(pred, obs, dim='time')
# 2. Mean Squared Errormse = xs.mse(pred, obs, dim='time')
# 3. Pearson Correlationcorr = xs.pearson_r(pred, obs, dim='time')
# 4. R-squaredr2 = xs.r2(pred, obs, dim='time')
print(f"MAE (spatial mean): {mae.mean().values:.4f}")
print(f"MSE (spatial mean): {mse.mean().values:.4f}")
print(f"Correlation (spatial mean): {corr.mean().values:.4f}")
print(f"R² (spatial mean): {r2.mean().values:.4f}")
```

### 視覺化驗證結果

```python
import cartopy.crs as ccrs
import cartopy.feature as cfeature
# 建立圖表fig, axes = plt.subplots(2, 3, figsize=(18, 10),
                          subplot_kw={'projection': ccrs.PlateCarree()})
# 第一列：觀測、預測、差異t_idx = 0  # 第一個時間點obs.isel(time=t_idx).plot(
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
# 第二列：驗證指標rmse_spatial.plot(
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

### xskillscore 進階功能

### 分類問題的混淆矩陣相關指標

```python
# 將預測和觀測轉成二元pred_binary = (pred > 0.5).astype(int)
obs_binary = obs.astype(int)
# 可以使用 sklearn 計算混淆矩陣，然後可視化from sklearn.metrics import confusion_matrix, classification_report
# 展平成 1Dpred_flat = pred_binary.values.ravel()
obs_flat = obs_binary.values.ravel()
# 計算cm = confusion_matrix(obs_flat, pred_flat)
print("Confusion Matrix:")
print(cm)
report = classification_report(obs_flat, pred_flat, target_names=['No Convection', 'Convection'])
print("\nClassification Report:")
print(report)
```

### 時間序列驗證

```python
# 計算時間序列的相關係數（對空間維度）corr_temporal = xs.pearson_r(pred, obs, dim=['latitude', 'longitude'])
# 繪製時間序列fig, ax = plt.subplots(figsize=(12, 4))
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
# xskillscore 方法（空間分佈）print("\n=== xskillscore 方法（空間分佈）===")
print(f"RMSE (mean): {rmse_spatial.mean().values:.4f}")
print(f"RMSE (std):  {rmse_spatial.std().values:.4f}")
print(f"RMSE (min):  {rmse_spatial.min().values:.4f}")
print(f"RMSE (max):  {rmse_spatial.max().values:.4f}")
print("\n✅ xskillscore 可以告訴你「哪裡」預測得好/差！")
```

# 總結與下一步

## 本課程學到的核心技能

### 1. Zarr 儲存優化

- 理解 Zarr vs NetCDF 的差異
- 知道為何要用 Zarr < 3.0
- 能夠讀取並優化 Zarr 檔案

### 2. Xarray + Dask 資料處理

- 使用 lazy evaluation 處理超過記憶體的資料
- 時空切片與重採樣
- 理解 chunking 對效能的影響
- 使用 Dashboard 監控效能

### 3. ML Pipeline 建構

- 使用 xbatcher 切批次
- 建立 Xarray → PyTorch 橋接層
- 將預測結果轉回 Xarray
- 使用 xskillscore 進行空間驗證

---

## 重要觀念回顧

### Lazy Evaluation

```python
# Lazy（不計算）result_lazy = ds['temperature'].mean(dim='time')
# Eager（計算）result_eager = result_lazy.compute()
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
| --- | --- | --- | --- |
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
# 資料流向Zarr files
  ↓ xr.open_zarr() [Xarray Dataset]
  ↓ xbatcher.BatchGenerator() [Lazy Batches]
  ↓ torch.utils.data.Dataset [PyTorch DataLoader]
  ↓ model.forward() [Predictions (Tensor)]
  ↓ xr.DataArray() [Xarray DataArray with coords]
  ↓ xskillscore [Spatial validation metrics]
```

## 延伸學習資源

## 官方文件

- **Xarray**: https://docs.xarray.dev/
- **Dask**: https://docs.dask.org/
- **Zarr**: https://zarr.readthedocs.io/
- **xbatcher**: [https://xbatcher.readthedocs.io/](https://xbatcher.readthedocs.io/)
- **xskillscore**: [https://xskillscore.readthedocs.io/](https://xskillscore.readthedocs.io/)
- 

### 進階主題

### 1. 分散式運算（Dask Cluster）

```python
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
# 在 HPC 上建立 cluster
cluster = SLURMCluster(cores=4, memory='16GB')
cluster.scale(jobs=10)  # 啟動 10 個 workersclient = Client(cluster)
```

### 2. 雲端儲存（S3, GCS）

```python
import fsspec
# 從 S3 讀取 Zarr
ds = xr.open_zarr(
    's3://bucket-name/data.zarr',
    storage_options={'anon': True}
)
```

### 3. GPU 加速（cupy, cuDF）

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

### 如果你想深入氣象應用：

- 探索 MetPy（氣象計算）
- 學習 Satpy（衛星資料處理）
- 研究 Climate Data Operators (CDO)

---

## 參考資料

### netCDF vs Zarr

[netCDF vs Zarr, an Incomplete Comparison | NSF Unidata](https://www.unidata.ucar.edu/blogs/news/entry/netcdf-vs-zarr-an-incomplete)

### **Pangeo**: 大氣與海洋科學的開源社群

[Pangeo: A community for open, reproducible, scalable geoscience](https://pangeo.io/)

[SBOTOP:Link Alternatif SBOTOP, Agen SBOTOP Login, Daftar Akun SBOTOP Mobile Terbaru](https://xarray-spatial.org/)

- **Intake**: 資料目錄系統
    - https://intake.readthedocs.io/
- **Xarray-spatial**: 地理空間分析
    - https://xarray-spatial.org/