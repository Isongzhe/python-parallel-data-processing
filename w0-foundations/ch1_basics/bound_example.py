"""
Ch1.1 - 效能瓶頸：CPU-bound vs I/O-bound

操作說明：
    1. 用 cProfile 分析 CPU:
        uv run python -m cProfile ch1_basics/bound_example.py cpu

    2. 用 cProfile 分析 I/O:
        uv run python -m cProfile ch1_basics/bound_example.py io
"""
import time
import sys 

# =============================================================================
# example functions
# =============================================================================
N = 1_000_000  # find primes up to N

# CPU-bound: cal prime numbers
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(max_number):
    return [n for n in range(max_number) if is_prime(n)]


# I/O-bound: time sleep -> simulate network request 
def simulate_io_operation(duration=0.5):
    time.sleep(duration)
    return "Operation completed"

# =============================================================================
# Demo 1: CPU-bound Task
# =============================================================================
def demo_cpu_bound():
    print("=" * 60)
    print("Demo 1: CPU-bound - 尋找質數")
    print("=" * 60)
    print("Running computation...\n")
    start = time.time()
    # 使用 1,000,000 讓 cProfile 有足夠時間分析
    primes = find_primes(N) 
    elapsed = time.time() - start
    print(f"Found {len(primes):,} primes")
    print(f"Time: {elapsed:.2f} seconds\n")

# =============================================================================
# Demo 2: I/O-bound Task
# =============================================================================
def demo_io_bound():
    print("=" * 60)
    print("Demo 2: I/O-bound - 模擬網路請求")
    print("=" * 60)
    print("Running I/O operations...\n")
    start = time.time()
    n_requests = 5
    for i in range(n_requests):
        simulate_io_operation(0.5)
        print(f"  Request {i+1}/{n_requests} done")
    elapsed = time.time() - start
    print(f"\nCompleted {n_requests} requests")
    print(f"Time: {elapsed:.2f} seconds\n")

# =============================================================================
# Main 
# =============================================================================
def main():
    if len(sys.argv) < 2:
        print("錯誤：請提供一個參數 'cpu' 或 'io'")
        print("範例: python bound_example.py cpu")
        sys.exit(1) 

    task_type = sys.argv[1]

    if task_type == 'cpu':
        demo_cpu_bound()
    elif task_type == 'io':
        demo_io_bound()
    else:
        print(f"錯誤：未知的參數 '{task_type}'。請使用 'cpu' 或 'io'")
        sys.exit(1)

if __name__ == '__main__':
    main()