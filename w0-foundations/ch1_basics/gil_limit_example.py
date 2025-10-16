"""
Ch1.2 - The Effect of the GIL (Global Interpreter Lock)

操作說明：
1. 執行 CPU demo: uv run python ch1_basics/gil_limit_example.py cpu
2. 執行 I/O demo: uv run python ch1_basics/gil_limit_example.py io
"""
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# =============================================================================
# example functions
# =============================================================================

# 1. A CPU-bound task (adding numbers +1 COUNT times)
COUNT = 100_000_000

def cpu_bound_task():
    print(f"  Running CPU-bound task...")
    start_t = time.time()
    n = 0
    for i in range(COUNT):
        n += 1
    elapsed = time.time() - start_t
    print(f"  CPU-bound task done in {elapsed:.2f}s")
    return elapsed

# 2. An I/O-bound task (waiting/sleeping for duration seconds)
def io_bound_task(duration=0.5):
    print(f"  Running I/O-bound task (waiting {duration}s)...")
    start_t = time.time()
    time.sleep(duration)
    elapsed = time.time() - start_t
    print(f"  I/O-bound task done in {elapsed:.2f}s")
    return elapsed

# =============================================================================
# Helper function for map()
# =============================================================================
def run_task_helper(task_function):
    """
    A top-level helper function that calls the function it's given.
    This is pickle-able for multiprocessing.
    """
    return task_function()

# =============================================================================
# Demo Runners
# =============================================================================

def run_sequentially(tasks):
    """Runs a list of functions one by one."""
    # This can stay as a list comprehension, it's not parallel
    return [task() for task in tasks]

def run_with_threads(tasks):
    """Runs a list of functions in a thread pool."""
    # Use the helper function instead of lambda
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        return list(executor.map(run_task_helper, tasks))

def run_with_processes(tasks):
    """Runs a list of functions in a process pool."""
    # Use the helper function instead of lambda
    with ProcessPoolExecutor(max_workers=len(tasks)) as executor:
        return list(executor.map(run_task_helper, tasks))

# =============================================================================
# Demo 1: CPU-bound Comparison
# =============================================================================
def demo_cpu_gil():
    print("\nCh1.2 - Demonstrating the GIL's effect on CPU-bound tasks")
    
    # We will run 2 tasks, each takes ~1 sec.
    # Parallel target time is ~1 sec.
    tasks_cpu = [cpu_bound_task, cpu_bound_task]
    
    # 1. Baseline: Sequential
    print("=" * 60)
    print("Demo 1: Sequential CPU-bound")
    print("=" * 60)
    start = time.time()
    run_sequentially(tasks_cpu)
    t_seq_cpu = time.time() - start
    print(f"\nTotal time: {t_seq_cpu:.2f} seconds\n")
    
    # 2. Problem: Threading
    print("=" * 60)
    print("Demo 2: ThreadPoolExecutor (CPU-bound)")
    print("=" * 60)
    start = time.time()
    run_with_threads(tasks_cpu)
    t_thread_cpu = time.time() - start
    print(f"\nTotal time: {t_thread_cpu:.2f} seconds\n")
    
    # 3. Solution: Multiprocessing
    print("=" * 60)
    print("Demo 3: ProcessPoolExecutor (CPU-bound)")
    print("=" * 60)
    start = time.time()
    run_with_processes(tasks_cpu)
    t_proc_cpu = time.time() - start
    print(f"\nTotal time: {t_proc_cpu:.2f} seconds\n")

    # --- Summary ---
    print("=" * 60)
    print("CPU-bound Summary (Parallel Target: ~1.0s)")
    print("=" * 60)
    print(f"  Sequential:       {t_seq_cpu:.2f}s")
    print(f"  Multi-Threading:  {t_thread_cpu:.2f}s  <-- NO SPEEDUP (GIL blocks)")
    print(f"  Multi-Processing: {t_proc_cpu:.2f}s  <-- TRUE SPEEDUP")

# =============================================================================
# Demo 2: I/O-bound Comparison
# =============================================================================
def demo_io_gil():
    print("\nCh1.2 - Demonstrating Threading's effectiveness for I/O-bound tasks")
    
    # We will run 4 tasks, each takes 0.5 sec.
    # Parallel target time is ~0.5 sec.
    tasks_io = [io_bound_task] * 4
    
    # 1. Baseline: Sequential
    print("=" * 60)
    print("Demo 4: Sequential I/O-bound")
    print("=" * 60)
    start = time.time()
    run_sequentially(tasks_io)
    t_seq_io = time.time() - start
    print(f"\nTotal time: {t_seq_io:.2f} seconds\n")
    
    # 2. Solution: Threading
    print("=" * 60)
    print("Demo 5: ThreadPoolExecutor (I/O-bound)")
    print("=" * 60)
    start = time.time()
    run_with_threads(tasks_io)
    t_thread_io = time.time() - start
    print(f"\nTotal time: {t_thread_io:.2f} seconds\n")
    
    # --- Summary ---
    print("=" * 60)
    print("I/O-bound Summary (Parallel Target: ~0.5s)")
    print("=" * 60)
    print(f"  Sequential:       {t_seq_io:.2f}s")
    print(f"  Multi-Threading:  {t_thread_io:.2f}s  <-- SPEEDUP (GIL released)")

# =============================================================================
# Main 
# =============================================================================
def main():
    if len(sys.argv) < 2:
        print("錯誤：請提供一個參數 'cpu' 或 'io'")
        print("範例: python gil_limit_example.py cpu")
        sys.exit(1) 

    task_type = sys.argv[1]

    if task_type == 'cpu':
        demo_cpu_gil()
    elif task_type == 'io':
        demo_io_gil()
    else:
        print(f"錯誤：未知的參數 '{task_type}'。請使用 'cpu' 或 'io'")
        sys.exit(1)

if __name__ == '__main__':
    main()