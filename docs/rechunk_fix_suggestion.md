# ERA5 Rechunking 問題與修正建議

## 問題診斷

你的 `era5_rechunk.py` 有一個關鍵問題：

```python
# 目前的做法（錯誤）
ds_final = ds_subset.chunk(SUBSET_CHUNKS)  # 只在 Dask 層面 rechunk
ds_final.to_zarr(output_path, mode='w', consolidated=True)  # 儲存時沒有指定 encoding
```

**結果**：
- Zarr 檔案保留原始全球資料的 chunks: `[1, 721, 1440]`
- subset 後變成: `[1, 121, 161]`（8760 個微小 chunks！）
- 這導致大量 "get-items" overhead 和黃色塊在 Dashboard

## 修正方案

### 方案 1：使用 encoding 參數（簡單）

```python
def rechunk_year(year: int, era5_dir: str, output_dir: str) -> bool:
    # ... 前面的程式碼相同 ...

    # Step 3: Rechunk
    ds_final = ds_subset.chunk(SUBSET_CHUNKS)

    # Step 4: Save with explicit encoding
    logger.info(f"\nStep 4: Saving to zarr with explicit chunking")

    # 準備 encoding（明確指定每個變數的 chunks）
    encoding = {}
    for var in ds_final.data_vars:
        var_dims = ds_final[var].dims
        var_chunks = []
        for dim in var_dims:
            if dim == 'time':
                var_chunks.append(SUBSET_CHUNKS['time'])
            elif dim == 'level':
                var_chunks.append(SUBSET_CHUNKS.get('level', ds_final.sizes['level']))
            elif dim == 'latitude':
                var_chunks.append(SUBSET_CHUNKS['latitude'])
            elif dim == 'longitude':
                var_chunks.append(SUBSET_CHUNKS['longitude'])
            else:
                var_chunks.append(ds_final.sizes[dim])

        encoding[var] = {
            'chunks': tuple(var_chunks),
            'compressor': numcodecs.Blosc(cname='zstd', clevel=3, shuffle=2)
        }

    t0 = time.time()
    with ProgressBar(dt=10):
        ds_final.to_zarr(
            output_path,
            mode='w',
            consolidated=True,
            encoding=encoding  # 關鍵：明確指定 chunks
        )

    # ... 後面的程式碼相同 ...
```

需要 import:
```python
import numcodecs
```

### 方案 2：使用 rechunker library（推薦，更高效）

```python
from rechunker import rechunk
import tempfile

def rechunk_year_with_rechunker(year: int, era5_dir: str, output_dir: str) -> bool:
    # ... 前面的程式碼到 ds_subset ...

    # Step 3: 使用 rechunker
    logger.info("\nStep 3: Rechunking with rechunker library (efficient)")

    target_chunks = {
        'time': 360,  # 15 天
        'latitude': 121,  # 完整空間
        'longitude': 161,
        'level': 4  # 如果有的話
    }

    # 移除不存在的維度
    actual_chunks = {k: v for k, v in target_chunks.items() if k in ds_subset.dims}

    # 使用 temporary storage for intermediate chunks
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_store = os.path.join(tmpdir, 'temp.zarr')

        rechunked = rechunk(
            ds_subset,
            target_chunks=actual_chunks,
            max_mem='4GB',  # 控制記憶體使用
            target_store=output_path,
            temp_store=temp_store
        )

        # 執行 rechunking（會顯示進度）
        t0 = time.time()
        rechunked.execute()
        elapsed = (time.time() - t0) / 60
        logger.info(f"Rechunking completed in {elapsed:.1f} minutes")

    # Consolidate metadata
    import zarr
    zarr.consolidate_metadata(output_path)

    return True
```

需要安裝：
```bash
pip install rechunker
```

## 驗證 Chunking

重新處理後，用這個 script 驗證：

```python
import xarray as xr
import json

# 檢查 zarr metadata
with open('/home/sungche/NAS/dataset/era5/era5_2019_10N40N_100E140E.zarr/convective_available_potential_energy/.zarray') as f:
    zarray = json.load(f)
    print(f"Stored chunks: {zarray['chunks']}")

# 檢查 xarray 讀取的 chunks
ds = xr.open_zarr('/home/sungche/NAS/dataset/era5/era5_2019_10N40N_100E140E.zarr', consolidated=True)
print(f"Loaded chunks: {ds['convective_available_potential_energy'].chunks}")

# 應該看到 (360, 121, 161) 而不是 (1, 121, 161)
```

## 重新處理建議

1. **選擇方案 2（rechunker）** - 更高效、更可靠
2. **先測試單一年份** (2023) 確認正確
3. **批次處理** 2019-2023
4. **驗證** chunk 大小和結構
5. **更新 workshop notebooks** 移除 catalog.yaml 的 chunks 參數（不再需要）

## Chunk Size 考量

目前設定 360 time steps (15天)：
- 單一 chunk: 360 × 121 × 161 × 4 bytes ≈ **28 MB** ✓（理想範圍 10-100 MB）
- 一年總共: 24 chunks（很好管理）

如果覺得太小，可以改為 720 (30天)：
- 單一 chunk: **56 MB**
- 一年總共: 12 chunks

## 暫時方案（目前使用）

在 `catalog.yaml` 中用 `chunks` 參數補救：
```yaml
era5_2019:
  driver: zarr
  args:
    chunks: {'time': 744, 'latitude': 121, 'longitude': 161}  # 讀取時 rechunk
```

**缺點**：
- 每次讀取都要 rechunk（overhead）
- 不如直接儲存正確的 chunks

**優點**：
- 不用重新處理所有資料
- 可以立即使用

## 結論

**短期**：使用 catalog.yaml 的 chunks 參數（已完成）
**長期**：使用 rechunker 重新處理所有年份資料
