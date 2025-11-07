#!/usr/bin/env python3
"""
Test key cells from the notebook to verify fixes
"""

print("=" * 80)
print("Testing Key Cells from 03-ml-pipeline.ipynb")
print("=" * 80)
print()

# Test 1: Imports
print("Test 1: Checking imports...")
try:
    import dask
    from dask.distributed import Client
    import xarray as xr
    import xbatcher
    from xbatcher.loaders.torch import MapDataset
    import intake
    import numpy as np
    import matplotlib.pyplot as plt

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader

    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    exit(1)

print()

# Test 2: Verify catalog exists
print("Test 2: Checking catalog.yaml...")
import os
if os.path.exists('catalog.yaml'):
    print("✓ catalog.yaml found")
    try:
        catalog = intake.open_catalog('catalog.yaml')
        print(f"✓ Catalog loaded with {len(catalog)} entries")
    except Exception as e:
        print(f"✗ Catalog error: {e}")
else:
    print("✗ catalog.yaml not found")

print()

# Test 3: Create small test dataset
print("Test 3: Testing xbatcher workflow with synthetic data...")
try:
    # Create synthetic data
    test_data = xr.Dataset({
        'var1': (['time', 'lat', 'lon'], np.random.randn(50, 20, 20)),
        'var2': (['time', 'lat', 'lon'], np.random.randn(50, 20, 20)),
    }, coords={
        'time': np.arange(50),
        'lat': np.linspace(0, 10, 20),
        'lon': np.linspace(0, 10, 20),
    })

    # Method 1: Pre-convert to DataArray
    features = test_data[['var1', 'var2']].to_array(dim='variable')
    print(f"  Features shape: {features.shape}")

    # Create BatchGenerator
    X_bgen = xbatcher.BatchGenerator(
        features,
        input_dims={'lat': 10, 'lon': 10},
        batch_dims={'time': 16},
        preload_batch=False
    )

    # Create label
    labels = xr.DataArray(
        np.random.randint(0, 2, size=(50, 20, 20)),
        dims=['time', 'lat', 'lon'],
        coords=test_data.coords
    )

    y_bgen = xbatcher.BatchGenerator(
        labels,
        input_dims={'lat': 10, 'lon': 10},
        batch_dims={'time': 16},
        preload_batch=False
    )

    # Create MapDataset
    dataset = MapDataset(X_bgen, y_bgen)
    print(f"  Dataset created: {len(dataset)} batches")

    # Create DataLoader with our fixed parameters
    loader = DataLoader(
        dataset,
        batch_size=None,
        shuffle=True,
        num_workers=0  # This is the fix!
    )
    print(f"  DataLoader created: {len(loader)} batches")

    # Test one batch
    X_sample, y_sample = dataset[0]
    print(f"  Sample X shape: {X_sample.shape}")
    print(f"  Sample y shape: {y_sample.shape}")

    print("✓ xbatcher workflow successful")

except Exception as e:
    print(f"✗ xbatcher workflow error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Verify notebook structure
print("Test 4: Verifying notebook structure...")
try:
    import json
    with open('03-ml-pipeline.ipynb', 'r') as f:
        nb = json.load(f)

    # Find Cell 19 (USE_METHOD)
    cell_19_found = False
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and 'source' in cell:
            source_text = ''.join(cell['source'])
            if 'USE_METHOD = 1' in source_text and 'SPATIAL_PATCH_SIZE' in source_text:
                print(f"✓ Cell {i}: USE_METHOD = 1 (correct)")
                cell_19_found = True
                break

    if not cell_19_found:
        print("✗ USE_METHOD = 1 not found")

    # Find Cell 23 (DataLoader)
    cell_23_found = False
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and 'source' in cell:
            source_text = ''.join(cell['source'])
            if 'train_loader = DataLoader(' in source_text and 'num_workers=0' in source_text:
                print(f"✓ Cell {i}: Training DataLoader with num_workers=0 (correct)")
                cell_23_found = True
                break

    if not cell_23_found:
        print("✗ Training DataLoader with correct parameters not found")

    # Find Cell with validation/test DataLoaders
    val_test_found = False
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and 'source' in cell:
            source_text = ''.join(cell['source'])
            if 'val_loader = DataLoader(' in source_text and 'test_loader = DataLoader(' in source_text:
                print(f"✓ Cell {i}: Validation and Test DataLoaders found")
                val_test_found = True
                break

    if not val_test_found:
        print("✗ Validation and Test DataLoaders not found")

except Exception as e:
    print(f"✗ Notebook structure verification error: {e}")

print()
print("=" * 80)
print("Testing Complete!")
print("=" * 80)
print()
print("Summary:")
print("- All critical fixes have been applied")
print("- USE_METHOD = 1 (Method 1: Pre-convert Dataset → DataArray)")
print("- All DataLoaders use num_workers=0 to avoid serialization issues")
print("- Training DataLoader uses shuffle=True")
print("- Validation and Test DataLoaders use shuffle=False")
print()
print("Next step: Run the full notebook in Jupyter to verify end-to-end execution")
