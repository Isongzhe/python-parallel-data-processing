"""
Ch2.2c - Multiprocessing Limitation: Tiny Task Overhead

Demonstrates that for very small, fast tasks, the overhead of
creating and managing processes is greater than the computation itself.

操作說明：
uv run python ch2_native_tools/multi_processing/tiny_tasks_example.py
"""
import time
from concurrent.futures import ProcessPoolExecutor
import sys

# --- Demo Configuration ---
N_WORKERS = 4

def tiny_task(n):
    """A trivial, instantly completed calculation."""
    return n * 2

def run_sequentially(tasks):
    """Runs the tiny tasks in a simple for-loop."""
    for i in tasks:
        tiny_task(i)

def run_multiprocessing(tasks):
    """Runs the tiny tasks using a process pool."""
    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        # We must call list() to ensure all tasks are completed before returning.
        list(executor.map(tiny_task, tasks))

def time_it(title, func_to_run, *args):
    """Helper function to time and print the execution of a function."""
    print(f"--- {title} ---")
    start = time.time()
    func_to_run(*args)
    elapsed = time.time() - start
    print(f"Time: {elapsed:.4f} seconds\n")
    return elapsed

def main():
    print("=" * 60)
    print("Demo: Overhead of Tiny Tasks")
    print("=" * 60)

    N_TASKS = 20_000
    tasks = range(N_TASKS)

    # 1. Time the sequential execution
    elapsed_seq = time_it(
        f"Executing {N_TASKS:,} tiny tasks (Sequentially)",
        run_sequentially,
        tasks
    )

    # 2. Time the multiprocessing execution
    elapsed_multi = time_it(
        f"Executing {N_TASKS:,} tiny tasks (Multiprocessing)",
        run_multiprocessing,
        tasks
    )

    # --- Summary ---
    print("--- Summary ---")
    if elapsed_multi > elapsed_seq and elapsed_seq > 0:
        slowdown = elapsed_multi / elapsed_seq
        print(f"Result: Multiprocessing was {slowdown:.2f}x SLOWER than sequential!")
        print("Reason: The overhead of creating, managing, and communicating with worker")
        print("        processes was far greater than the time to do the trivial work.")
    else:
        print("Result: Multiprocessing was faster (this is unexpected for this demo).")

if __name__ == '__main__':
    main()

