"""
Ch3.4b - Dask Dashboard: Real-time Monitoring

展示如何啟動和使用 Dask Dashboard 來監控任務執行狀況。
使用真實的資料處理場景：讀取多個 CSV 檔案並進行分析。

操作說明：
uv run python w0-foundations/ch3_dask_intro/dashboard_demo.py
"""
import time
import numpy as np
import pandas as pd
from pathlib import Path
from dask import delayed, compute, persist
from dask.distributed import Client, LocalCluster


# ============================================================
# Configuration
# ============================================================

# Use absolute path from script location
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "temp_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Core Logic: Realistic Data Processing Tasks
# ============================================================

def generate_sample_csv(filename, rows=10000):
    """
    Generate a sample CSV file with time-series sensor data
    
    Args:
        filename: Output filename
        rows: Number of rows to generate
    """
    # Generate time series with trend and noise
    timestamps = pd.date_range('2024-01-01', periods=rows, freq='1min')
    
    # Add daily pattern (temperature higher during day)
    hour_of_day = timestamps.hour
    daily_pattern = 5 * np.sin(2 * np.pi * hour_of_day / 24)
    
    data = {
        'timestamp': timestamps,
        'sensor_id': np.random.choice(['A', 'B', 'C', 'D'], rows),
        'temperature': 25 + daily_pattern + np.random.normal(0, 2, rows),
        'humidity': 60 + np.random.normal(0, 5, rows),
        'pressure': 1013 + np.random.normal(0, 10, rows)
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)


@delayed
def load_and_validate(filename):
    """
    I/O-bound: Load CSV and validate data
    
    Simulates real file I/O operations
    
    Args:
        filename: CSV file to load
        
    Returns:
        DataFrame: Loaded data
    """
    print(f"[I/O] Loading {Path(filename).name}...")
    time.sleep(2)  # 增加到 2 秒，讓你有時間觀察
    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Validate data
    assert not df.isnull().any().any(), "Found null values"
    assert len(df) > 0, "Empty dataframe"
    
    print(f"[I/O] {Path(filename).name} loaded: {len(df)} rows")
    
    return df


@delayed
def compute_statistics(df, file_id):
    """
    CPU-bound: Compute time-series statistics
    
    Realistic analysis:
    - Basic statistics (mean, std)
    - Moving averages
    - Correlation analysis
    - Trend detection
    
    Args:
        df: Input DataFrame
        file_id: File identifier
        
    Returns:
        dict: Computed statistics
    """
    print(f"[CPU] Computing statistics for file {file_id}...")
    
    # 增加到 3 秒，讓你有時間觀察
    time.sleep(3)
    
    # Calculate moving averages (simulate trend analysis)
    df_sorted = df.sort_values('timestamp')
    ma_24h = df_sorted['temperature'].rolling(window=60*24, min_periods=1).mean()
    
    stats = {
        'file_id': file_id,
        'row_count': len(df),
        
        # Basic statistics
        'mean_temp': df['temperature'].mean(),
        'std_temp': df['temperature'].std(),
        'min_temp': df['temperature'].min(),
        'max_temp': df['temperature'].max(),
        
        'mean_humidity': df['humidity'].mean(),
        'std_humidity': df['humidity'].std(),
        
        'mean_pressure': df['pressure'].mean(),
        'std_pressure': df['pressure'].std(),
        
        # Trend analysis
        'temp_range': df['temperature'].max() - df['temperature'].min(),
        'temp_trend': ma_24h.iloc[-1] - ma_24h.iloc[0] if len(ma_24h) > 1 else 0,
        
        # Correlation
        'temp_humidity_corr': df['temperature'].corr(df['humidity']),
        'temp_pressure_corr': df['temperature'].corr(df['pressure']),
        
        # Sensor distribution
        'sensor_a_pct': (df['sensor_id'] == 'A').sum() / len(df) * 100,
        'sensor_b_pct': (df['sensor_id'] == 'B').sum() / len(df) * 100,
    }
    
    print(f"[CPU] Statistics computed for file {file_id}")
    return stats


@delayed
def analyze_hourly_patterns(df, file_id):
    """
    CPU-bound: Analyze hourly patterns in sensor data
    
    Realistic analysis:
    - Group by hour of day
    - Calculate hourly averages
    - Identify peak hours
    
    Args:
        df: Input DataFrame
        file_id: File identifier
        
    Returns:
        dict: Hourly pattern analysis
    """
    print(f"[CPU] Analyzing hourly patterns for file {file_id}...")
    
    time.sleep(2)  # 增加到 2 秒
    
    # Extract hour from timestamp
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Calculate hourly statistics
    hourly_temp = df.groupby('hour')['temperature'].agg(['mean', 'std', 'count'])
    
    # Find peak hours
    peak_hour = hourly_temp['mean'].idxmax()
    lowest_hour = hourly_temp['mean'].idxmin()
    
    result = {
        'file_id': file_id,
        'peak_temp_hour': int(peak_hour),
        'peak_temp_value': float(hourly_temp.loc[peak_hour, 'mean']),
        'lowest_temp_hour': int(lowest_hour),
        'lowest_temp_value': float(hourly_temp.loc[lowest_hour, 'mean']),
        'daily_temp_variation': float(hourly_temp['mean'].max() - hourly_temp['mean'].min()),
        'avg_hourly_std': float(hourly_temp['std'].mean()),
    }
    
    print(f"[CPU] Hourly analysis complete for file {file_id}")
    return result


@delayed
def aggregate_results(stats_list):
    """
    Lightweight: Aggregate results from all files
    
    Args:
        stats_list: List of statistics dictionaries
        
    Returns:
        DataFrame: Aggregated results
    """
    print(f"[Aggregate] Combining results from {len(stats_list)} files...")
    time.sleep(0.2)
    
    results_df = pd.DataFrame(stats_list)
    
    print("[Aggregate] Aggregation complete")
    return results_df


@delayed
def combine_hourly_patterns(pattern_list):
    """
    Lightweight: Combine hourly pattern analysis
    
    Args:
        pattern_list: List of hourly pattern dictionaries
        
    Returns:
        DataFrame: Combined hourly patterns
    """
    print(f"[Aggregate] Combining hourly patterns from {len(pattern_list)} files...")
    time.sleep(0.1)
    
    combined = pd.DataFrame(pattern_list)
    
    print(f"[Aggregate] Combined patterns from {len(combined)} files")
    return combined


# ============================================================
# Display Functions
# ============================================================

def print_header():
    """Print header"""
    print("=" * 70)
    print("Demo: Dask Dashboard - Real-time Task Monitoring")
    print("Scenario: Multi-file Sensor Data Analysis")
    print("=" * 70)


def print_dashboard_info(client):
    """
    Print dashboard access information
    
    Args:
        client: Dask Client instance
    """
    dashboard_url = client.dashboard_link
    
    print("\nDashboard Information:")
    print("-" * 70)
    print(f"Dashboard URL: {dashboard_url}")
    print("\nPlease open this URL in your browser:")
    print("  - Chrome, Firefox, or Safari recommended")
    print("  - NOT VSCode Simple Browser (it may not work)")
    print("-" * 70)


def print_cluster_info(client):
    """
    Print cluster configuration
    
    Args:
        client: Dask Client instance
    """
    scheduler_info = client.scheduler_info()
    
    print("\nCluster Configuration:")
    print("-" * 70)
    print(f"Workers: {len(scheduler_info['workers'])}")
    
    for worker_id, worker_info in scheduler_info['workers'].items():
        nthreads = worker_info['nthreads']
        print(f"  - {worker_id}: {nthreads} threads")
    
    print("-" * 70)


def print_instructions():
    """Print step-by-step instructions"""
    print("\nHow to Use Dashboard:")
    print("=" * 70)
    print("""
1. Open the Dashboard URL in your browser

2. IMPORTANT: Click on 'Task Stream' in the left sidebar
   - The default page will show 'Scheduler is empty' (this is normal)
   - You MUST switch to 'Task Stream' to see tasks executing

3. After switching to Task Stream, come back here and press Enter

4. Watch the Task Stream page - you will see:
   - Green bars = actual computation time
   - Orange/Red bars = data transfer/waiting time
   - Different rows = different workers executing in parallel
   - Tasks will run for ~15-20 seconds (enough time to observe)

5. Other useful tabs:
   - Progress: Overall completion percentage
   - Workers: CPU and memory usage per worker
    """)
    print("=" * 70)


def print_task_graph_info(final_stats, final_patterns):
    """
    Print task graph information
    
    Args:
        final_stats: Delayed stats result
        final_patterns: Delayed patterns result
    """
    # Get graph information
    stats_graph = final_stats.__dask_graph__()
    
    print("\nTask Graph Information:")
    print("=" * 70)
    
    # Count task types
    task_types = {}
    for key in stats_graph.keys():
        task_name = str(key).split('-')[0]
        task_types[task_name] = task_types.get(task_name, 0) + 1
    
    print("\nTask Summary:")
    total_tasks = 0
    for task_name, count in sorted(task_types.items()):
        print(f"  - {task_name}: {count} task(s)")
        total_tasks += count
    
    print(f"\nTotal tasks in graph: {total_tasks}")
    
    print("\nExecution Flow:")
    print("  Stage 1: Load Files (I/O)")
    print("    - 12 load_and_validate tasks")
    print("    - Run in parallel")
    print("    - ~2s per task")
    print()
    print("  Stage 2: Process Data (CPU)")
    print("    - 12 compute_statistics tasks (~3s each)")
    print("    - 12 analyze_hourly_patterns tasks (~2s each)")
    print("    - Run in parallel (24 tasks total)")
    print()
    print("  Stage 3: Aggregate (Lightweight)")
    print("    - 2 aggregation tasks")
    print("    - Wait for all Stage 2 tasks")
    print("    - ~0.2s per task")
    
    print("\nExpected total time: ~15-20 seconds")
    print("(vs ~80+ seconds if sequential)")
    
    print("=" * 70)


# ============================================================
# Demo Scenarios
# ============================================================

def demo_realistic_pipeline(client, n_files=12):
    """
    Demo: Realistic data processing pipeline
    
    Pipeline:
    1. Load multiple CSV files (I/O-bound)
    2. For each file:
       - Compute statistics (CPU-bound)
       - Analyze hourly patterns (CPU-bound)
    3. Aggregate all results (lightweight)
    
    Watch the Dashboard to see:
    - I/O and CPU tasks interleaved
    - Parallel execution across workers
    - Task dependencies
    - Load balancing
    
    Args:
        client: Dask client
        n_files: Number of files to process
        
    Returns:
        list: List of generated filenames (for cleanup later)
    """
    print(f"\n[Pipeline] Processing {n_files} sensor data files...")
    print(f"Data directory: {DATA_DIR}")
    print()
    
    # Generate test files
    print("Generating sample data files...")
    filenames = []
    for i in range(n_files):
        filename = DATA_DIR / f'sensor_data_{i}.csv'
        generate_sample_csv(filename, rows=5000)
        filenames.append(filename)
    print(f"Generated {n_files} files in {DATA_DIR}\n")
    
    print("Building task graph...")
    
    # Step 1: Load all files (I/O-bound, parallel)
    loaded_dfs = [load_and_validate(str(f)) for f in filenames]
    
    # Step 2a: Compute statistics (CPU-bound, parallel)
    stats_tasks = [compute_statistics(df, i) for i, df in enumerate(loaded_dfs)]
    
    # Step 2b: Analyze hourly patterns (CPU-bound, parallel)
    pattern_tasks = [analyze_hourly_patterns(df, i) for i, df in enumerate(loaded_dfs)]
    
    # Step 3: Aggregate results (depends on all previous tasks)
    final_stats = aggregate_results(stats_tasks)
    final_patterns = combine_hourly_patterns(pattern_tasks)
    
    print("Task graph built!")
    print_task_graph_info(final_stats, final_patterns)
    
    # === 關鍵修改：分兩階段執行 ===
    
    # 階段 1: 提交任務到 scheduler（但不執行）
    print("\n" + "=" * 70)
    print("Stage 1: Submitting tasks to scheduler...")
    print("=" * 70)
    input("\nPress Enter to submit tasks to scheduler (they won't run yet)...")
    
    # 使用 persist() 提交任務，但不立即執行
    final_stats_persisted, final_patterns_persisted = persist(final_stats, final_patterns)
    
    print("\nTasks submitted to scheduler!")
    print("Now you can see the Graph in Dashboard!")
    print()
    print("What to do:")
    print("  1. Switch to Dashboard")
    print("  2. Click 'Graph' tab in the top menu")
    print("  3. You should see the task dependency graph")
    print("  4. Come back here when ready")
    
    # 階段 2: 真正開始執行
    print("\n" + "=" * 70)
    print("Stage 2: Starting execution...")
    print("=" * 70)
    input("\nPress Enter to START EXECUTION (watch Task Stream now)...")
    
    # Countdown
    print("\nStarting in:")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("  GO! Switch to Task Stream NOW!\n")
    
    print("Executing pipeline...")
    
    start = time.time()
    
    # 真正執行（compute）
    stats_result, patterns_result = compute(final_stats_persisted, final_patterns_persisted)
    
    elapsed = time.time() - start
    
    # Display results
    print("\n" + "=" * 70)
    print("Pipeline Completed!")
    print("=" * 70)
    print(f"Total time: {elapsed:.2f}s")
    print(f"\nProcessed {n_files} files")
    
    print("\nStatistics Summary:")
    print(stats_result[['file_id', 'mean_temp', 'temp_range', 'temp_humidity_corr']].head())
    
    print("\nHourly Pattern Summary:")
    print(patterns_result[['file_id', 'peak_temp_hour', 'peak_temp_value', 'daily_temp_variation']].head())
    
    print(f"\nData files are in: {DATA_DIR}")
    print("Files will be cleaned up after cluster closes")
    
    return filenames


# ============================================================
# Cleanup Functions
# ============================================================

def cleanup_data_files(filenames):
    """
    Clean up generated data files
    
    Args:
        filenames: List of file paths to remove
    """
    print("\nCleaning up data files...")
    
    removed_count = 0
    for f in filenames:
        try:
            if f.exists():
                f.unlink()
                removed_count += 1
        except Exception as e:
            print(f"Warning: Could not remove {f}: {e}")
    
    print(f"Removed {removed_count} data files")
    
    # Try to remove the temp_data directory if empty
    try:
        if DATA_DIR.exists() and not any(DATA_DIR.iterdir()):
            DATA_DIR.rmdir()
            print(f"Removed empty directory: {DATA_DIR}")
    except Exception:
        pass  # Directory not empty or other issue


# ============================================================
# Main Program
# ============================================================

def main():
    cluster = None
    client = None
    filenames = []  # Track generated files
    
    try:
        # 1. Print header
        print_header()
        print(f"\nData directory: {DATA_DIR}")
        
        # 2. Start LocalCluster
        print("\nStarting Dask LocalCluster...")
        cluster = LocalCluster(
            n_workers=4,
            threads_per_worker=2,
            dashboard_address=':0'
        )
        
        client = Client(cluster)
        print("Cluster started!")
        
        # 3. Display cluster and dashboard info
        print_cluster_info(client)
        print_dashboard_info(client)
        print_instructions()
        
        # 4. Wait for user to open dashboard
        input("\nPress Enter after opening Dashboard and switching to Task Stream...")
        
        # 5. Run realistic pipeline (returns filenames for cleanup)
        filenames = demo_realistic_pipeline(client, n_files=12)
        
        # 6. Wait before closing
        input("\nPress Enter to close the cluster and exit...")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Cleaning up...")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 7. Close cluster first
        print("\nClosing cluster...")
        if client:
            client.close()
        if cluster:
            cluster.close()
        print("Cluster closed.")
        
        # 8. Clean up data files after cluster is closed
        if filenames:
            cleanup_data_files(filenames)
        
        print("\nGoodbye!")


if __name__ == '__main__':
    main()