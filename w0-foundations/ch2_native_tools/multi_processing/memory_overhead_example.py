"""
Ch2.2b - Multiprocessing Limitation: Memory Overhead (Final, Refactored)

This version programmatically measures the total memory usage of the
main process and all its child worker processes. The logic has been
refactored for clarity and reliability.

操作說明：
uv run python ch2_native_tools/multi_processing/memory_overhead_advanced_example.py
"""
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil
import os

# --- Demo Configuration ---
N_WORKERS = 2
DATA_SIZE_GB = 1.0
WORKER_HOLD_TIME = 5      # How long each worker holds memory (seconds)
MONITOR_WARM_UP_TIME = 2  # How long main waits before starting to monitor (seconds)
MONITOR_DURATION = 3      # How long the monitoring lasts (seconds)

def print_total_memory(main_process, stage=""):
    """
    Helper function to calculate and print the total memory usage of the 
    main process and all its children.
    """
    total_rss = main_process.memory_info().rss
    children = main_process.children(recursive=True)
    for child in children:
        try:
            total_rss += child.memory_info().rss
        except psutil.NoSuchProcess:
            continue
            
    total_rss_gb = total_rss / (1024 ** 3)
    # Changed "workers" to "child processes" for accuracy, as it includes the manager process.
    print(f"[{stage}] Total Memory (Main + {len(children)} child processes): {total_rss_gb:.2f} GB")
    return total_rss_gb

def process_data_in_memory(data_size_gb, sleep_duration):
    """
    Worker function that allocates memory and holds it for a specified time.
    """
    worker_pid = os.getpid()
    print(f"  Worker (PID: {worker_pid}) starting, will allocate {data_size_gb:.2f} GB...")
    # This allocation itself takes time
    worker_data = np.random.rand(int(data_size_gb * 125_000_000))
    print(f"  Worker (PID: {worker_pid}) memory allocated, now holding for {sleep_duration}s...")
    time.sleep(sleep_duration) 
    print(f"  Worker (PID: {worker_pid}) finished.")
    return True

def time_it(title, func_to_run, *args):
    """Helper function to time and print the execution of a function."""
    print(f"--- {title} ---")
    start = time.time()
    result = func_to_run(*args)
    elapsed = time.time() - start
    print(f"\nFinished in {elapsed:.2f} seconds.")
    return result

def run_and_monitor_multiprocessing(main_process, data_size_gb):
    """
    Handles the logic of running multiprocessing tasks while monitoring memory.
    Returns the peak memory measured.
    """
    peak_memory = 0
    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        futures = [executor.submit(process_data_in_memory, data_size_gb, WORKER_HOLD_TIME) for _ in range(N_WORKERS)]
        
        print(f"\n--- Main process waiting {MONITOR_WARM_UP_TIME}s for workers to start and allocate memory... ---")
        time.sleep(MONITOR_WARM_UP_TIME)

        print(f"\n--- Starting memory monitor for {MONITOR_DURATION}s... ---")
        for i in range(MONITOR_DURATION):
            current_memory = print_total_memory(main_process, f"Monitoring {i+1}/{MONITOR_DURATION}")
            if current_memory > peak_memory:
                peak_memory = current_memory
            time.sleep(1)
        
        print("\n--- Monitoring finished, waiting for all tasks to complete... ---")
        for future in as_completed(futures):
            future.result()
    
    return peak_memory

def main():
    print("=" * 60)
    print("Demo: Memory Overhead (Advanced Measurement)")
    print("=" * 60)
    
    main_process = psutil.Process(os.getpid())

    print_total_memory(main_process, "Initial Baseline")
    print(f"\nWill start {N_WORKERS} worker processes, each allocating {DATA_SIZE_GB:.2f} GB.")
    print(f"Expected peak memory: ~{DATA_SIZE_GB * N_WORKERS:.2f} GB (from workers) + baseline.")
    input("Press Enter to run the Multiprocessing demo and monitor memory...")

    peak_memory = time_it(
        "Running Multiprocessing and Monitoring Memory",
        run_and_monitor_multiprocessing,
        main_process,
        DATA_SIZE_GB
    )
    
    print("\n--- Summary ---")
    print("Result: The total memory usage of all processes was measured programmatically.")
    print(f"Measured Peak Memory: {peak_memory:.2f} GB")
    print("Reason: The main process started 2 worker processes. Each worker created its own")
    print(f"      independent {DATA_SIZE_GB:.2f} GB copy of the data in its own memory space,")
    print("      causing the total memory usage to spike significantly.")
    print("      This directly demonstrates the high memory overhead of multiprocessing.")

if __name__ == '__main__':
    main()

