"""
Ch3.4a - Dask Delayed: Quick Parallelization of Custom Functions

Demonstrates how to use the @delayed decorator to convert existing
Python functions into delayed tasks and automatically build task graphs.

Usage:
uv run python w0-foundations/ch3_dask_intro/delayed_example.py
"""
import time
from dask import delayed
import dask

# Use threads scheduler (suitable for I/O bound tasks)
dask.config.set(scheduler='threads')


# ============================================================
# Core Logic: Business Functions
# ============================================================

@delayed
def load_file(filename):
    """Simulate file reading (I/O-bound)"""
    time.sleep(1)  # Simulate I/O wait 
    return f"data_from_{filename}"


@delayed
def process_data(data):
    """Simulate data processing (CPU-bound)"""
    time.sleep(0.5)  # Simulate computation
    return data.upper()


@delayed
def aggregate(results):
    """Aggregate results"""
    return ", ".join(results)


# ============================================================
# Helper Functions: Task Graph Analysis
# ============================================================

def analyze_task_graph(delayed_obj):
    """
    Analyze Dask task graph structure
    
    Returns:
        dict: Task statistics information
    """
    graph = delayed_obj.__dask_graph__()
    
    # Count each task type
    task_types = {}
    for key in graph.keys():
        task_name = str(key).split('-')[0]
        task_types[task_name] = task_types.get(task_name, 0) + 1
    
    return {
        'task_types': task_types,
        'total_tasks': len(graph),
        'graph': graph
    }


def build_data_pipeline(files):
    """
    Build data processing pipeline
    
    Args:
        files: List of file names
        
    Returns:
        Delayed object: Final aggregated result
    """
    # Step 1: Load files in parallel
    loaded = [load_file(f) for f in files]
    
    # Step 2: Process each file's data in parallel
    processed = [process_data(data) for data in loaded]
    
    # Step 3: Aggregate all results
    final = aggregate(processed)
    
    return final


# ============================================================
# Display Functions
# ============================================================

def print_header():
    """Print header"""
    print("=" * 60)
    print("Demo: Dask Delayed - Automatic Parallelization")
    print("=" * 60)


def print_task_graph_info(analysis):
    """
    Print task graph analysis results
    
    Args:
        analysis: Return value from analyze_task_graph()
    """
    print("\nTask Graph Structure:")
    print("=" * 60)
    
    print("\nTask Summary:")
    for task_name, count in sorted(analysis['task_types'].items()):
        print(f"   - {task_name}: {count} task(s)")
    
    print(f"\nTotal tasks: {analysis['total_tasks']}")
    
    print("\nExecution Flow:")
    print("   Step 1: load_file tasks (4) -> Can execute in parallel")
    print("   Step 2: process_data tasks (4) -> Can execute in parallel") 
    print("   Step 3: aggregate task (1) -> Waits for Step 2 to complete")
    print("=" * 60)


def print_execution_result(result, elapsed):
    """
    Print execution results
    
    Args:
        result: Computation result
        elapsed: Execution time in seconds
    """
    print(f"\nResult: {result}")
    print(f"Total time: {elapsed:.2f}s")


def print_explanation():
    """Print explanation of parallel execution"""
    print("\n" + "=" * 60)
    print("Why is file reading parallel?")
    print("=" * 60)
    print("""
1. Dask analyzes task graph and finds 4 load_file tasks have no dependencies
2. Creates ThreadPool with 4 threads
3. 4 threads start executing load_file simultaneously
4. time.sleep(1) is I/O wait, which releases GIL
5. All threads can wait simultaneously

Time Comparison:
  Sequential: 4 × 1s + 4 × 0.5s = 6s
  Parallel:   max(1s, 1s, 1s, 1s) + max(0.5s, ...) ≈ 1.5s
  
Speedup: ~4x faster!
    """)


# ============================================================
# Main Program
# ============================================================

def main():
    # 1. Print header
    print_header()
    
    # 2. Build task graph
    print("\nBuilding task graph...")
    files = [f"file_{i}.csv" for i in range(4)]
    final = build_data_pipeline(files)
    print("Task graph built (no computation yet!)")
    
    # 3. Analyze and display task graph
    analysis = analyze_task_graph(final)
    print_task_graph_info(analysis)
    
    # 4. Display scheduler being used
    print(f"\nUsing scheduler: {dask.config.get('scheduler')}")
    
    # 5. Execute computation
    print("\nStarting computation with .compute()...\n")
    start = time.time()
    result = final.compute()
    elapsed = time.time() - start
    
    # 6. Display results
    print_execution_result(result, elapsed)
    
    # 7. Display explanation
    print_explanation()


if __name__ == '__main__':
    main()