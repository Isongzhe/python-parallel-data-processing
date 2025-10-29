# Python 平行資料處理基礎

日期: 2025年10月17日
狀態: 進行中

[GitHub - Isongzhe/python-parallel-data-processing](https://github.com/Isongzhe/python-parallel-data-processing.git)

<aside>
📢

### 本工作坊是「Python 大數據處理三部曲」的第一部：**平行處理基礎篇**

當你的資料從 MB 成長到 GB，再到 TB 級別時，傳統的 Pandas + 單執行緒處理方式將會遭遇瓶頸。本課程將帶你理解 Python 平行處理的核心概念，並為後續的進階資料處理技巧打好基礎。

</aside>

### **理解 Python 在大數據處理上的限制**

- 為什麼處理 GB ~ TB 級資料時會遇到記憶體不足？
- GIL (Global Interpreter Lock) 如何限制 Python 的多核心運算能力？
- 單機處理的極限在哪裡？

### 掌握 Process vs. Thread 的核心差異

- 執行緒 (Threads) vs. 行程 (Processes) 的本質區別
- CPU-bound vs. I/O-bound 任務的最佳策略
- 如何根據任務特性選擇正確的平行化方式

### 認識Python 原生平行處理工具: Dask 背後原理

- 使用 `threading` 加速 I/O 密集型任務
- 使用 `multiprocessing` 突破 GIL 限制
- 理解 serialization overhead 與效能陷阱
- ThreadPoolExecutor 與 ProcessPoolExecutor 功能與限制

### 認識 Dask：企業級大數據處理框架

- 原生工具的限制：為什麼需要 Dask？
- Dask 如何簡化複雜的資料流程編排
- Task Graph 與 Lazy Evaluation 的威力

### 銜接後續實作進階課程

**Part 2: DataFrame 處理 - 表格資料的極致優化：**

<aside>

- 深入**Dask DataFrame**：突破記憶體限制的分散式表格處理
- 現代高效能引擎對決：**Polars** vs **DuckDB** vs **Dask**
- Out-of-Core 運算：處理大於記憶體 N 倍的資料集
- 實戰案例：TB 級 ETL pipeline 設計
</aside>

**Part 3: N-D Array 處理 - 科學運算與影像數據：**

<aside>

- **Dask Array**：分散式多維陣列運算
- **Xarray**：帶標籤的 N 維資料結構
- **Zarr**：雲端原生的陣列儲存格式
- **Xbatcher / Xskillscores**
- 應用場景：衛星影像、氣象資料、醫學影像分析
</aside>

# Ch1. Python 平行處理基礎

### **學習目標:**

- 識別兩種主要的效能瓶頸：CPU 密集型 (CPU-bound) vs. I/O 密集型 (I/O-bound)。
- 理解 Process vs. Thread 差別，以及扮演的角色。
- 理解 GIL (Global Interpreter Lock) 及其對 Python 效能的致命影響。

## **1.1 -**  效能瓶頸 **CPU-bound vs. I/O-bound**

### CPU-bound：

<aside>

- **特徵：** CPU 使用率接近 100%，程式花大量時間在「計算」，還是跑很久。
- **常見情境：**
    - 數學計算（統計分析、矩陣運算）
    - 資料轉換（格式轉換、編碼解碼）
    - 影像處理（濾波、特徵提取）
    - 機器學習訓練
</aside>

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image.png)

### I/O-bound：

<aside>

- **特徵：** CPU 使用率很低，程式花大量時間在「等待」
- **常見情境：**
    - 網路請求（API 呼叫、網頁爬蟲）
    - 檔案讀寫（大量小檔案、資料庫查詢）
    - 磁碟操作（備份、複製）
    - Muti-process 傳輸 !!!
</aside>

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%201.png)

## 1.2 - 認識 Process vs. Thread

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%202.png)

<aside>
🗣

一個系統中可以運行多個獨立的行程 (Process)，而每個行程內部則由一或多個執行緒 (Thread) 來執行任務。

</aside>

<aside>
📌

**CPU 核心 (CPU Cores) = 總廚師數量(硬體資源)**

- 這是實際可以同時工作的廚師總數
- 例如:8核CPU = 8位廚師可以真正同時做菜
</aside>

### Process (行程)：

<aside>
📖

Process 是作業系統分配資源的最小單位。你可以把它想像成一個**完全獨立的廚房**。

</aside>

- **擁有獨立資源:** 每個廚房都有自己**專屬**的全套廚具、食材庫和冰箱（也就是獨立的記憶體空間）。
- **提供隔離環境:** 每個廚房的牆壁都非常厚實。一個廚房裡發生的事（例如程式崩潰），完全不會影響到隔壁的廚房。這就是**隔離性 (Isolation)**。

### Thread (執行緒)：

<aside>
📖

Thread 是 CPU 實際排程執行的最小單位。可以想像成廚房裡規劃的「廚師配置人數」。

</aside>

- **在 Process 內工作**: 廚師配置 (`thread`) 屬於某個廚房 (`process`)。
- **共享資源**: 同一個廚房裡配置的所有廚師，共用這個廚房的所有資源——共用同一套廚具和食材（共享記憶體空間）。
- **執行程式碼**: 實際的廚師(CPU core)會被排程器派去執行任務，按照食譜(程式碼)來烹飪。

### 懶人包：

- **比喻**: `CPU cores` = 總廚師數量(硬體)。`process` = 獨立的廚房(軟體隔離單位)。`thread` = 廚房內的配置人數(軟體排程單位)。
- **資源**: `process`各自擁有完整資源；`thread`在同一`process`內共享資源。
- **隔離**: 不同`process`彼此完全隔離；同一`process`內的`thread`不隔離、可能互相影響。
- **開銷**: 建立`process`成本較高；建立`thread`成本較低。
- **最佳配置**: `Process數 × Thread數 ≈ CPU Cores數`。

## 1.3 - Python limit - GIL (Global **Interpreter Lock)**

### What is the GIL?

<aside>
📖

在 CPython 中，一個行程 (`process`) 內一次只有一個執行緒 (`thread`) 能執行 Python 位元組碼 (bytecode)。

</aside>

<aside>

- **設計緣由:** 在 Python 誕生的年代 (90年代初)，多核心 CPU 尚不普及。主要目的是：
    - **簡化記憶體管理:** 保護所有 Python 物件不被多個 `thread` 同時修改，避免競爭條件 (Race Conditions)，讓 C 語言擴充套件的開發變得更容易。
    - **提升單執行緒效能:** 在單核心時代，GIL 避免了重複獲取和釋放鎖的開銷。
</aside>

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%203.png)

<aside>
➡️

**類比:** 一個廚房 (`process`) 裡，不管有多少位廚師 (`threads`)，都只有**一個爐灶 (GIL)** 能用來做菜 (CPU 運算)，其他人只能等在旁邊。

</aside>

### The Effects of the Python Global Interpreter Lock (GIL)：

1. **它嚴重限制了 CPU 密集型任務：** 
    
    對於純計算的任務，GIL 強制同一`process`內的所有`threads`必須順序執行，而不是平行執行。
    
    <aside>
    ⚠️
    
    使用 `multiple threads` 來處理 CPU-bound 工作，將**完全無法獲得加速效果**，甚至可能因為`threads`切換的額外開銷而變得更慢。
    
    </aside>
    
2. **它對 I/O 密集型任務不成問題：** 
    
    當一個`threads`在等待外部資源時（例如等待網路回應或讀取檔案），GIL 會被智慧地釋放。這就允許其他`threads`在這段等待時間內使用 CPU 進行運算。
    

# Ch2. Python 原生加速工具

## 2.0 三種執行方式

<aside>
🗣

在學習 threading 和 multiprocessing 之前，先理解三種執行模式的本質差異：

</aside>

### **Sequential 序列 (ex. Single Process and Single Thread)**

![](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/a5b3c97f-d561-415c-8f1f-adbb4306d802.png)

### **Concurrency 並行 (ex. Multi-Threading)**

![](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/c56ee43d-660e-4ac3-9180-ad49a92a694b.png)

### **Parallelism 平行  (ex. Multi-Processing)**

![](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/24a0dc86-bd0f-4b0d-bdae-8416c08f72cb.png)

## **2.1 threading**

### **核心概念**

管理多個任務，讓它們的執行時間重疊。**適合 I/O-bound 任務。實現 Concurrency**

<aside>
➡️

同一個廚房裡有多位廚師（threads）。當一位廚師在等蛋糕烤好時（I/O 等待），另一位廚師可以去準備其他食材。

</aside>

### 基本架構

```python
import threading

# Step 1: Define the task*
def worker(name):
    """Task to be executed by the thread"""
    *# Execute task...*
    pass

# Step 2: Create a thread*
thread = threading.Thread(target=worker, args=("Thread-1",))

# Step 3: Start the thread*
thread.start()

# Step 4: Wait for the thread to complete*
thread.join()
```

<aside>

**說明：**

- `threading.Thread(target=函式, args=(參數,))` - 建立執行緒
- `.start()` - 啟動執行緒
- `.join()` - 等待執行緒完成
</aside>

```python
import threading
import time

def worker(task_id):
    """Task to be executed by the thread"""
    time.sleep(1)  # Simulate I/O operation
    return f"Task {task_id} completed"

# Create multiple threads (手動管理)
threads = []
for i in range(4):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()
```

### 實務應用：[ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html)

<aside>

在實務中，我們通常使用 `ThreadPoolExecutor` 來自動管理 thread pool：

</aside>

```python
from concurrent.futures import ThreadPoolExecutor
import time

def worker(task_id):
    time.sleep(1)
    return f"Task {task_id} completed"

with ThreadPoolExecutor(max_workers=4) as executor:
    results = [executor.map](http://executor.map)(worker, range(8))
    
    # Get all results
    for result in results:
        print(result)
```

<aside>
⚠️

**即便有 GIL 存在，還是要小心 Race Conditions !!！**

避免多個執行緒同時修改共享資料/ 變數，必要時使用 `Lock` 或 `Queue`。

</aside>

## **2.2 multiprocessing**

### **核心概念**

**同時**執行多個任務，平行處理。這才是我們解決 CPU-bound 問題所需要的

<aside>
➡️

既然『一個爐灶』的規則是**每個廚房**的限制 (GIL)，那麼解決方案就是蓋**多個獨立的廚房 (`processes`)**。每個廚房都有自己的廚師、自己的全套廚具和食材 (記憶體)，以及自己的爐灶。他們可以完全同時做菜。

</aside>

### 基本架構

```python
from multiprocessing import Process

# Step 1: Define the task
def worker(name):
    """Task to be executed by the process"""
    # Execute task...
    pass

# Step 2: Create a process (Must be inside if __name__ == '__main__')
if __name__ == '__main__':
    process = Process(target=worker, args=("Process-1",))
    
    # Step 3: Start the process
    process.start()
    
    # Step 4: Wait for process to complete
    process.join()
```

<aside>

**說明：**

- `multiprocessing.Process(target=函式, args=(參數,))` - 建立行程
- `.start()` - 啟動行程
- `.join()` - 等待行程完成

<aside>
⚠️

**為什麼必須包在 `if __name__ == '__main__':` 裡面？**

當啟動新的 Process 時，Python 會重新執行整個腳本。如果沒有這個保護，
每個新的 Process 又會建立更多 Process，導致無限遞迴。

</aside>

</aside>

### 實務應用：ProcessPoolExecutor

```python
from concurrent.futures import ProcessPoolExecutor
import time

def compute(n):
    """CPU-bound task"""
    time.sleep(1)  # Simulate heavy computation
    return n ** 2

if __name__ == '__main__':
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # Create a process pool with 4 workers
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(compute, data)
        
        print(list(results))  # [1, 4, 9, 16, 25, 36, 49, 64]
```

### **Trade-offs:**

<aside>
👉

使用 `multiprocessing` 雖然能獲得真正的平行加速，但也帶來額外的成本

</aside>

1. **記憶體開銷:** 每個**`processes`**都有獨立的記憶體空間，這可能導致記憶體消耗倍增。
2. **通訊成本:**  **`processes`** 之間無法直接共享記憶體，傳遞資料需要序列化（Serialization)，解析資料需要反序列化。

***什麼情況下，使用multiprocessing 需要特別小心 :*** 

1. **通訊成本過高 (Serialization Cost)**
    
    <aside>
    🚫
    
    當傳送資料給 worker 的時間，比計算本身還長時，平行化反而會讓程式變慢。
    
    </aside>
    
    ```python
    # The computation is extremely fast (~0.1 seconds)
    def simple_sum(large_array):
        return large_array.sum()
    
    # But sending a 1GB array to a new process can take seconds
    # due to serialization (pickling) and data transfer.
    with Pool(processes=4) as pool:
      pool.map(simple_sum, [large_1GB_array])
    
    # 1. Serialization (序列化): 將 1GB array 轉換成可傳輸的格式 (pickle)
    # 2. IPC (Inter-Process Communication): 透過 pipe/queue 傳輸資料到子進程
    # 3. Deserialization (反序列化): 子進程接收後還原成 numpy array
    # 4. 實際計算: simple_sum(data)
    # 5. 結果回傳: 再經歷一次序列化 -> 傳輸 -> 反序列化
    #
    # 對於這個案例：
    # - 計算時間: ~0.1 秒 (單純 np.sum)
    # - 序列化+傳輸: 數秒 (1GB 資料的 pickle + IPC)
    # - 總時間: 遠大於直接計算！
    ```
    
2. **記憶體開銷倍增 (Memory Overhead)**
    
    <aside>
    ⚠️
    
    每一個 worker process 都會建立一份獨立的資料副本，導致總記憶體需求倍增。
    
    </aside>
    
    ```python
    # The main process loads a 10GB DataFrame into its memory.
    df = pd.read_csv('large_data.csv')  # 10GB in main process
    
    # When sent to 10 workers, 10 new 10GB copies are created.
    with Pool(processes=10) as pool:
        pool.map(process_data, [df] * 10)
    
    # Total RAM needed: ~100GB+
    # Result: Out of Memory (OOM) error!
    ```
    
3. **任務太細碎 (Tiny Task Overhead)**
    
    <aside>
    ⚠️
    
    對於執行速度極快的任務，建立和管理新行程的額外開銷，遠大於實際工作本身
    
    </aside>
    
    ```python
    # A task that takes only 0.0001 seconds
    def tiny_task(n):
        return n * 2
    
    # The overhead of starting the Pool and sending 20,000 tiny tasks...
    tasks = range(20000)
    with Pool(processes=4) as pool:
        pool.map(tiny_task, tasks)
    
    # ...is much slower than just running a simple for-loop.
    # Result: Slower than sequential!
    ```
    
4. **工作分配不均 (Poor Load Balancing)**
    
    <aside>
    ⚠️
    
    對於執行速度極快的任務，建立和管理新行程的額外開銷，遠大於實際工作本身
    
    </aside>
    
    ```python
    # Split a prime search into 4 equal-sized ranges.
    # The higher ranges are much harder to compute.
    workloads = [
        (0, 350_000),         # Easy
        (350_000, 700_000),   # Medium
        (700_000, 1_050_000), # Hard
        (1_050_000, 1_400_000) # Very Hard (the "straggler")
    ]
    
    # Worker 1 finishes at 0.5s.
    # Worker 2 finishes at 0.8s.
    # Worker 3 finishes at 1.2s.
    # --> Workers 1, 2, and 3 are now IDLE.
    # Worker 4 finally finishes at 3.5s.
    
    # Result: Total time is 3.5s, but 3 of 4 CPUs were unused for most of it.
    ```
    

## 2.3 總結

[Speed Up Your Python Program With Concurrency – Real Python](https://realpython.com/python-concurrency/)

| 模式 | 架構 | 執行方式 | 適用場景 | Python 工具 |
| --- | --- | --- | --- | --- |
| **Sequential** | 1 Process + 1 Thread | 一個接一個 | 簡單任務 | 一般寫法 |
| **Concurrency** | 1 Process + N Threads | 交錯執行（GIL 限制） | I/O-bound | `threading` |
| **Parallelism** | N Processes | 真正同時 | CPU-bound | `multiprocessing` |

| 特性 | threading | multiprocessing |
| --- | --- | --- |
| 適用場景 | I/O-bound（網路、硬碟讀寫） | CPU-bound（大量計算） |
| 機制 | Concurrency（並行） | Parallelism（平行） |
| 記憶體 (Memory) | Shared（共享） | Independent（獨立） |
| GIL 限制 | 有，一次只有 1 個 thread 能跑 CPU | 無，每個 process 有自己的 GIL |

| 功能 | `threading`: ThreadPoolExecutor | `multiprocessing`: ProcessPoolExecutor |
| --- | --- | --- |
| 自動分配任務 | ✅ | ✅ |
| 管理 workers | ✅ | ✅ |
| 收集結果 | ✅ | ✅ |
| 分割資料 | ❌ | ❌ |
| 負載平衡 | ❌ | ❌ |
| 任務依賴 | ❌ | ❌ |
| Out-of-Core | ❌ | ❌ |

# Ch3. Dask 入門

## 3.1 原生工具的限制：

### **問題一：手動編排平行工作流的複雜性**

<aside>
⚠️

對於資料科學家而言，使用原生工具（如 `multiprocessing`）意味著必須手動解決所有複雜的調度問題，這不僅容易出錯，且難以維護。

</aside>

- **手動分割資料：**
    - 為了在 32GB 記憶體的機器上處理 100GB 的檔案，你必須手動編寫邏輯（例如，將一個大型 Pandas DataFrame 手動切割成數個小區塊），處理每個區塊，最後再手動（例如 `pd.concat`）合併結果。
- **手動管理任務依賴：**
    - 你必須手動編寫程式碼，以確保某個步驟必須在所有前置任務（例如：讀取 100 個檔案）完成後才能開始。( Task A → Task B → Task C)
- **缺乏負載平衡：**
    - `Pool.map` 會將**任務**（來自 iterable 的項目）分配給 workers。如果某個**任務**（例如處理一個特別大的檔案）的執行時間是其他任務的 10 倍，所有其他 workers 在完成自己的任務後都會閒置，空等那個緩慢的任務完成。
- **沒有核外運算 (Out-of-Core) 能力：**
    - 原生工具假設所有資料都能放入記憶體。如果不行，程式就會崩潰。

### **問題二：真實世界的資料處理是混合型任務（I/O + CPU）**

<aside>
❓

一個典型的資料流程通常是**混合**的：

- 讀取 100 個檔案（I/O-bound）
- 解壓縮並解析它們（CPU-bound）
- 執行一個大型計算（CPU-bound）
- 將結果寫入 NAS（I/O-bound）

如果你用 `multiprocessing.Pool` 來做，你的行程 (processes) 在 I/O 步驟中會閒置，浪費資源。如果你用 `ThreadPoolExecutor`，你的執行緒 (threads) 會在 CPU 步驟中被 GIL 卡住。

</aside>

## 3.2 Dask 的解決方案

[Dask | Scale the Python tools you love](https://www.dask.org/)

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%204.png)

### **延遲評估 (Lazy Evaluation) & 任務圖 (Task Graph)** ：

<aside>
📖 **Lazy Evaluation:**  
Dask 操作（例如 `dd.read_csv`）不會立即執行，而是建立一個「任務計畫圖」（Task Graph）。

</aside>

<aside>
🛠 **如何解決【問題一】（手動編排）：**

- **Collections**（如 Dask DataFrame）自動處理資料分割 (chunks)。
- **Task Graph** 自動管理所有任務依賴。
- 任務圖是「Lazy」的，直到被呼叫 `.compute()`  才會開始執行。
</aside>

### **調度器 (Schedulers):**

<aside>
📖 **Schedulers:** 
調度器是執行任務圖的「引擎」。當你呼叫 `.compute()` ，任務圖就會被送給它。

</aside>

<aside>
🛠 **如何解決【問題一】的缺失功能：**

- **負載平衡：** 自動將任務分配給空閒的 worker。
- **核外運算：** 以串流 (streaming) 方式處理區塊 (chunks)，避免 OOM。
- **可擴展性：** 程式碼可無痛從單機（Single-machine）擴展到叢集（Distributed）。

**如何解決【問題二】（混合任務）：**

- **智慧型調度：** 分析任務圖，自動將 I/O 任務分配給執行緒（threads），將 CPU 任務分配給行程（processes）。
</aside>

## 3.3 Dask 與 Python 生態系統整合

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%205.png)

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%206.png)

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%207.png)

## 3.4 How to use Dask

### **Dask Delayed**

<aside>
📖

將 Python function 包裝成「延遲任務」，呼叫時不會立即執行，而是記錄在任務圖中。

→ 適合將現有的自訂函式快速平行化 !!

</aside>

```python
from dask import delayed
import time

@delayed # 只加這一行! 
def process_file(filename):
		# 讀取 + 計算
		df = pd.read_csv(filename)
		    result = df['amount'].sum()
		    heavy_calc = sum(i**2 for i in range(1000000))
		    return result
	
# 建立延遲任務（task graph)
tasks = [process_file(f'data_{i}.csv') for i in range(10)]
total = delayed(sum)(tasks)

# 執行
final_result = total.compute()  # .compute() 觸發 task graph 得到結果
```

### Dashboard 即時監控

[Dashboard Diagnostics — Dask  documentation](https://docs.dask.org/en/latest/dashboard.html)

```python
from dask.distributed import Client
client = Client()
```

![image.png](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/image%208.png)

# Ch4. 總結以及補充資訊

## Recap

### Python 限制以及挑戰：

<aside>

**GIL 的影響：**

- 因為 GIL (Global Interpreter Lock)，Python 在 CPU 密集型任務上是單執行緒的
- 這意味著多個 threads 無法同時執行 Python code
- 這是 Python 在處理 CPU-bound 任務時的限制

**兩種效能瓶頸：**

- **CPU-bound**：程式花大量時間在「計算」
- **I/O-bound**：程式花大量時間在「等待」
</aside>

### 並行 vs 平行：兩種不同加速策略

<aside>

**Concurrency 並行 (**`threading`)

![](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/c56ee43d-660e-4ac3-9180-ad49a92a694b.png)

</aside>

<aside>

**Parallelism 平行 (**`multiprocessing`**)**

![](Python%20%E5%B9%B3%E8%A1%8C%E8%B3%87%E6%96%99%E8%99%95%E7%90%86%E5%9F%BA%E7%A4%8E/24a0dc86-bd0f-4b0d-bdae-8416c08f72cb.png)

</aside>

### 原生工具的限制：

<aside>
⚠️

雖然 `threading` 和 `multiprocessing` 能解決部分問題，但它們都有明顯的限制：

- **手動編排複雜：**
    - 需要手動分割資料
    - 需要手動管理任務依賴
    - 需要手動合併結果
- **缺乏負載平衡：**
    - 某個任務特別慢時，其他 workers 會閒置
- **沒有 Out-of-Core 能力：**
    - 資料必須全部放入記憶體
    - 無法處理超大型資料集
- **混合型任務難以處理：**
    - I/O + CPU 混合的真實場景很難優化
</aside>

## 參考目錄

### Python GIL

[What Is the Python Global Interpreter Lock (GIL)? – Real Python](https://realpython.com/python-gil/)

### Python Process / Threads

[Probably the Easiest Tutorial for Python Threads, Processes and GIL | Towards Data Science](https://towardsdatascience.com/dont-know-what-is-python-gil-this-may-be-the-easiest-tutorial-3b99805d2225/)

[Speed Up Your Python Program With Concurrency – Real Python](https://realpython.com/python-concurrency/)

### Python 3.14 - Free Thread Version

[Python 3.14](https://astral.sh/blog/python-3.14)

### Threading

[threading --- 基於執行緒的平行性](https://docs.python.org/zh-tw/3.13/library/threading.html)

[concurrent.futures — Launching parallel tasks](https://docs.python.org/3/library/concurrent.futures.html)

[](https://ithelp.ithome.com.tw/articles/10344891)

### Thread Safety

[Python Thread Safety: Using a Lock and Other Techniques – Real Python](https://realpython.com/python-thread-lock/)

[System Design Patterns: Producer Consumer Pattern](https://dsysd-dev.medium.com/system-design-patterns-producer-consumer-pattern-1572f813329b)

### Multi-processing

[multiprocessing — Process-based parallelism](https://docs.python.org/3/library/multiprocessing.html)

### Python 碼農高天

[【python】天使还是魔鬼？GIL的前世今生。一期视频全面了解GIL！](https://www.youtube.com/watch?v=XjBsk8JGHhQ&t=2s)

[【python】queue是个啥？能干啥？啥是任务分配？](https://www.youtube.com/watch?v=Qsa3xZgDUh4&t=134s)

[【python】听说因为有GIL，多线程连锁都不需要了？](https://www.youtube.com/watch?v=qQt7G5qhRS8)

[【python】我用了多进程怎么程序反而变慢了？](https://youtu.be/xFtEg_e54as?si=Y6vg9HOVyCiafWXa)

<aside>
📖

線程 = 執行緒 = `thread` ;  進程 = 行程  = `process` 

</aside>

### Dask Introduction

[Why Dask? — Dask  documentation](https://docs.dask.org/en/stable/why.html)

[What is Dask?](https://www.nvidia.com/en-us/glossary/dask/)

[利用 Dask 讓 Python 資料科學進入企業就緒狀態 - NVIDIA 台灣官方部落格](https://blogs.nvidia.com.tw/blog/making-python-data-science-enterprise-ready-with-dask/)

[What is Dask and How Does it Work? | Saturn Cloud Blog](https://saturncloud.io/blog/what-is-dask/)

### Dask Tutorial

[Dask Tutorial — Dask Tutorial  documentation](https://tutorial.dask.org/)

[10 Minutes to Dask — Dask  documentation](https://docs.dask.org/en/stable/10-minutes-to-dask.html)

[Dashboard Diagnostics — Dask  documentation](https://docs.dask.org/en/latest/dashboard.html)