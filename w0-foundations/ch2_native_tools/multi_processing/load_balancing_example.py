"""
Ch2.2d - Multiprocessing Limitation: Poor Load Balancing (Final Version)

This version demonstrates the load balancing problem by splitting a single,
large prime number search into evenly-sized ranges. The worker with the
highest range will take the longest, causing other workers to sit idle.

操作說明：
uv run python ch2_native_tools/multi_processing/load_balancing_example.py
"""
import time
from concurrent.futures import ProcessPoolExecutor
import sys
import os

# --- Demo Configuration ---
N_WORKERS = 4
MAX_NUMBER = 1_400_000 # The total range to search for primes

# --- CPU-bound Task ---
def find_primes_in_range(args):
    """
    Finds all primes within a given (start, end) range.
    """
    start_range, end_range, start_time = args
    pid = os.getpid()
    
    print(f"  [PID: {pid}] Worker starting task: find_primes(from {start_range:,} to {end_range:,})...")
    
    primes_count = 0
    for n in range(start_range, end_range):
        if n < 2:
            continue
        is_prime = True
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                is_prime = False
                break
        if is_prime:
            primes_count += 1
            
    elapsed_total = time.time() - start_time
    # Added separator line to make this print statement stand out
    print(f"  --- [PID: {pid}] Worker finished task ({start_range:,} to {end_range:,}) at {elapsed_total:.2f}s. Found {primes_count:,} primes. ---")
    return primes_count

# --- Execution Runner ---
def run_multiprocessing(tasks):
    """Runs the prime search tasks using a process pool."""
    start_time = time.time()
    # Package the start time with each task for timestamping
    tasks_with_time = [(start, end, start_time) for start, end in tasks]
    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        return list(executor.map(find_primes_in_range, tasks_with_time))

# --- Main Demo ---
def main():
    print("=" * 60)
    print("Demo: Poor Load Balancing by Splitting a Single Problem")
    print("=" * 60)

    # Split the total range into N_WORKERS chunks
    chunk_size = MAX_NUMBER // N_WORKERS
    workloads = []
    for i in range(N_WORKERS):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        workloads.append((start, end))

    print(f"Total range to search: 0 to {MAX_NUMBER:,}")
    print(f"Splitting into {N_WORKERS} chunks of size {chunk_size:,}...")
    for i, (start, end) in enumerate(workloads):
        print(f"  Chunk {i+1}: {start:,} to {end:,}")
    print("")

    # --- Run the demo ---
    print(f"--- Running {len(workloads)} chunks (Multiprocessing with {N_WORKERS} workers) ---")
    start = time.time()
    run_multiprocessing(workloads)
    elapsed_multi = time.time() - start
    print(f"\nTotal Time: {elapsed_multi:.2f} seconds\n")
    
    # --- Summary ---
    print("--- Summary ---")
    print("Observe the timestamps in the output above.")
    print("The workers searching lower number ranges finish much earlier than the")
    print("worker searching the highest number range.")
    print("\nThis creates a 'straggler' problem: 3 out of 4 workers are SITTING IDLE,")
    print("waiting for the single slowest worker to finish.")
    print("\nThis demonstrates the poor resource utilization of `Pool.map`'s default task allocation.")

if __name__ == '__main__':
    main()