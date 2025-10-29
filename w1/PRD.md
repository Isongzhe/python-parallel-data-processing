PRD: Scalable N-D Array Analysis Workshop (Part 3)

Document Owner: (Your Name)
Last Updated: 2025-10-29
Status: Draft

1. Overview

1.1. Product

A 2-3 hour hands-on programming workshop (Part 3 of a series) focused on scalable N-D array processing for scientific data.

1.2. Target Audience

Internal lab members (Masters students, PhD students, and Professors) who have already completed "Part 1: Python Parallel Processing Basics."

Assumed Knowledge:

Basic Python and NumPy.

Core concepts of Dask (Lazy Evaluation, Task Graphs).

Understanding of GIL, Processes vs. Threads.

Knowledge Gap: No practical experience using Dask, Xarray, or Zarr on real, large-scale scientific datasets.

1.3. Problem Statement

Our lab's NAS is full of large ERA5 datasets (in NetCDF format) which are critical for our research. Our current analysis scripts (using basic Python/Numpy/Xarray) are slow, often crash due to "Out of Memory" errors, and are not easily adapted for machine learning workflows.

1.4. Goal (The "Job to be Done")

After this workshop, a lab member will be able to confidently perform out-of-core analysis on the entire NAS ERA5 dataset and build a scalable, ML-ready data pipeline using the modern Python scientific stack.

2. Core Learning Objectives

This workshop will be a single, hands-on "Golden Path" exercise. By the end, a user must be able to:

Analyze > RAM Data: Load, slice, and perform a computation (e.g., .mean()) on a dataset larger than local RAM using xarray and dask without crashing.

Optimize Storage: Explain why Zarr is superior to NetCDF for parallel I/O and successfully convert a large NetCDF dataset to an optimized Zarr store.

Build an ML Pipeline: Create a data pipeline that lazily feeds large-scale scientific data into a PyTorch model using xbatcher and verify the model's output using xskillscore.

3. Feature Breakdown (The "Golden Path" Workflow)

This maps directly to the required topics. The workshop will be a single script that walks through these 6 points in order, using the lab's NAS ERA5 data.

3.1. Module 1: The Xarray + Dask "Aha!" Moment

Goal: Show the problem (slow NetCDF) and the instant solution (lazy Dask).

Topics Covered:

[Xarray Foundations] Show the "Pain": xarray.open_mfdataset("*.nc") is slow to parse.

[Dask Array] Show the "Solution": xarray's dask backend allows lazy, out-of-core access.

[Chunking] Explain how chunks are the key to parallelism. Visualize ds.chunks.

[Slicing] Demonstrate that .sel() or .isel() are instantaneous (lazy).

[Plotting] Show .plot() on a slice as a way to trigger a small, concrete computation.

Practical Win: Run .mean(dim="time").compute() on the full dataset and watch the Dask Dashboard light up.

3.2. Module 2: The Storage Revolution (Zarr)

Goal: Make the analysis permanently fast by fixing the storage format.

Topics Covered:

[Why Zarr?] Explain the concept: NetCDF/HDF5 = single-file, metadata lock (bad for parallel). Zarr = directory of chunk-files (good for parallel).

[Save to Zarr] Practical Exercise: Take the Dask-backed dataset and run ds.to_zarr("era5.zarr", consolidated=True). Explain this is a "one-time cost."

The Payoff: Restart the kernel and open the Zarr store: xarray.open_zarr("era5.zarr"). It will be instantaneous.

3.3. Module 3: The ML Application Workflow

Goal: Apply this new power to a real research problem (ML).

Topics Covered:

[Xbatcher to Torch DataLoader] Show the "Pain": How to feed 1TB of data to PyTorch? dataset.load().to_numpy() will crash.

Solution: Use xbatcher.BatchGenerator to create lazy, Dask-backed batches. Show the for batch in generator: loop that yields small, concrete NumPy arrays ready for torch.

[Xskillscore for Evaluation] Show the "Pain": Evaluating a model's xarray output with sklearn.metrics.rmse loses all the scientific context (lat, lon, time).

Solution: Use xskillscore.rmse(predictions, observations, dim='time') to get an xarray.DataArray of the RMSE at every grid point.

4. Scope & Constraints

4.1. In-Scope

Data: Must use the lab's internal ERA5 dataset (NetCDF format) from the NAS.

Tools: xarray, dask, zarr, xbatcher, xskillscore, torch (for DataLoader only), dask.distributed.Client (for the Dashboard).

Environment: All code must run on a single machine (laptop or server) using Dask's local scheduler. The goal is to maximize single-machine performance.

4.2. Out-of-Scope (Critical)

No DataFrame: This workshop is only for N-D Arrays. dask.dataframe, polars, etc., are not included.

No Cluster Setup: We will not cover setting up a Dask cluster (e.g., Kubernetes, SLURM, dask-ssh).

No Low-Level Dask: We will not use dask.delayed. We will only use Dask via the high-level xarray integration.

No Part 1 Review: This workshop assumes knowledge of GIL, Dask basics, etc. No time will be spent re-teaching these concepts.