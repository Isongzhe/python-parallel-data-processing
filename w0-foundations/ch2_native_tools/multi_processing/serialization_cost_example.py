"""
Ch2.2a - Multiprocessing Limitation: Serialization Cost

Demonstrates how the cost of serializing and transferring large
data between processes can make multiprocessing slower than
sequential execution.

操作說明：
uv run python ch2_native_tools/multi_processing/serialization_cost_example.py
"""
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor

def simple_sum(data):
    """A very fast computation on a potentially large dataset."""
    return np.sum(data)

def time_it(title, func_to_run, *args):
    """Helper function to time and print the execution of a function."""
    print(f"--- {title} ---")
    start = time.time()
    result = func_to_run(*args)
    elapsed = time.time() - start
    print(f"Time: {elapsed:.4f} seconds\n")
    return elapsed

def run_multiprocessing_sum(data):
    """Wrapper to run simple_sum in a ProcessPoolExecutor."""
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(simple_sum, [data])  
        return list(results)[0]

def main():
    print("=" * 60)
    print("Demo: Serialization Cost > Computation Cost")
    print("=" * 60)
    
    # 1. Create a large (1GB) NumPy array
    print("Creating a large 1GB NumPy array...")
    large_array = np.random.rand(125_000_000)
    print("Array created.\n")

    # 2. Time the sequential execution
    elapsed_seq = time_it(
        "Running Sequentially (pure computation)",
        simple_sum,
        large_array
    )

    # 3. Time the multiprocessing execution
    elapsed_multi = time_it(
        "Running with Multiprocessing (serialization + transfer + computation)",
        run_multiprocessing_sum,
        large_array
    )
    
    # --- Summary ---
    print("--- Summary ---")
    if elapsed_multi > elapsed_seq:
        slowdown = elapsed_multi / elapsed_seq
        print(f"Result: Multiprocessing was {slowdown:.2f}x SLOWER than sequential!")
        print("Reason: The time to serialize and transfer 1GB of data to another process")
        print("        was far greater than the actual computation time.")
    else:
        print("Result: Multiprocessing was faster (this is unexpected for this demo).")

if __name__ == '__main__':
    main()

