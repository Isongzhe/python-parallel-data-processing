"""
Ch2.1 - Threading Limitation: Race Conditions

This version adds a `time.sleep(0)` to the "danger zone"
to encourage the OS to switch threads, guaranteeing that
the race condition is visible.

操作說明：
uv run python ch2_native_tools/race_condition_example.py
"""
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# A shared variable
counter = 0
N_TASKS = 2
# We can use a much smaller number now because the sleep
# makes the race condition easy to trigger.
N_INCREMENTS = 100_000 

# =============================================================================
# Demo 1: The Race Condition (Guaranteed Fail)
# =============================================================================
def unsafe_increment():
    """
    Manually simulates the non-atomic steps of `counter += 1`
    and adds a sleep to encourage a context switch.
    """
    global counter
    for _ in range(N_INCREMENTS):
        local_copy = counter
        
        # This sleep gives another thread a chance to run
        time.sleep(0)  # Encourage context switch (GIL release)
        
        local_copy += 1
        counter = local_copy

def demo_race_condition():
    print("=" * 60)
    print("Demo 1: Race Condition with Threading (Guaranteed Fail)")
    print("=" * 60)
    global counter
    counter = 0 # Reset counter
    
    tasks = [unsafe_increment] * N_TASKS
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=N_TASKS) as executor:
        executor.map(lambda f: f(), tasks)
    elapsed = time.time() - start
    
    expected = N_TASKS * N_INCREMENTS
    print(f"Expected result: {expected:,}")
    print(f"Actual result:   {counter:,}") # This will be wrong
    print(f"Time: {elapsed:.2f} seconds")
    
    if counter == expected:
        print("\nResult: Race condition did not occur (extremely rare!).")
    else:
        print(f"\nResult: The final count is WRONG! ({expected - counter:,} increments lost)")

# =============================================================================
# Demo 2: The Solution (using a Lock)
# =============================================================================
counter_safe = 0
lock = threading.Lock()

def safe_increment():
    """
    Uses a lock to protect the entire "read-calculate-write" operation = (+=1),
    operation, making it atomic.
    """
    global counter_safe
    for _ in range(N_INCREMENTS):
        with lock:
            local_copy = counter_safe
            # Even with a sleep here, the lock prevents other
            # threads from entering this block.
            time.sleep(0) 
            local_copy += 1
            counter_safe = local_copy

def demo_lock_solution():
    print("=" * 60)
    print("Demo 2: Race Condition Solved with a Lock")
    print("=" * 60)
    global counter_safe
    counter_safe = 0 # Reset counter
    
    tasks = [safe_increment] * N_TASKS
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=N_TASKS) as executor:
        executor.map(lambda f: f(), tasks)
    elapsed = time.time() - start
    
    expected = N_TASKS * N_INCREMENTS
    print(f"Expected result: {expected:,}")
    print(f"Actual result:   {counter_safe:,}") # This will be correct
    print(f"Time: {elapsed:.2f} seconds")
    print("\nResult: The final count is correct.")

# =============================================================================
# Main
# =============================================================================
def main():
    demo_race_condition()
    print("\n")
    demo_lock_solution()

if __name__ == '__main__':
    main()