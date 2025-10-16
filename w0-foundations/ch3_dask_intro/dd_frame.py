import dask.datasets as dd

# 小型 NYC Taxi 資料
df = dd.timeseries(
    start='2024-01-01',
    end='2024-01-10',
    freq='1h',
    partition_freq='1D'
)

print(df)
print(type(df))