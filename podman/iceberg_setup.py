#!/usr/bin/env python3
# Python script showing how to create and populate a table in Iceberg. 

# Uncomment to see the module search path.
# import sys
# print(sys.path)

from datetime import datetime 

import pyarrow
import pyiceberg
# Allows us to connect to the catalog. 
from pyiceberg.catalog import load_catalog
# These are used to create the table structure. 
from pyiceberg.schema import Schema
from pyiceberg.types import (
    TimestampType,
    FloatType,
    DoubleType,
    StringType,
    NestedField,
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform
from pyiceberg.table.sorting import SortOrder, SortField
from pyiceberg.transforms import IdentityTransform

print("Connect to the catalog") 
catalog = load_catalog(
    "rest", 
    **{
        "uri": "http://localhost:8182/",  # REST server URL. 
        "type": "rest",
        "s3.endpoint": f"http://localhost:9002",  # Minio URI and credentials
        "s3.access-key-id": "minio",
        "s3.secret-access-key": "minio123",
    }  
)

# Set up a namespace if it does not exist. 
print("Create namespace iceberg")
try:
    catalog.create_namespace("iceberg")
    print("--Created")
except pyiceberg.exceptions.NamespaceAlreadyExistsError:
    print("--Already exists")

print("List namespaces")
ns_list = catalog.list_namespaces()
for ns in ns_list:
    print(ns)

# List tables and delete the bids table if it exists. 
print("List tables")
tab_list = catalog.list_tables("iceberg")
for tab in tab_list:
    print(tab, type(tab))
    if tab[0] == "iceberg" and tab[1] == "bids":
        print("Dropping bids table")
        catalog.drop_table("iceberg.bids")

# Now create the test table. It's partitioned by datetime and 
# sorted by symbol. 
schema = Schema(
    NestedField(field_id=1, name="datetime", field_type=TimestampType(), required=False),
    NestedField(field_id=2, name="symbol", field_type=StringType(), required=False),
    NestedField(field_id=3, name="bid", field_type=DoubleType(), required=False),
    NestedField(field_id=4, name="ask", field_type=DoubleType(), required=False),
)
partition_spec = PartitionSpec(
    PartitionField(
        source_id=1, field_id=1000, transform=DayTransform(), name="datetime_day"
    )
)
sort_order = SortOrder(SortField(source_id=2, transform=IdentityTransform()))
table = catalog.create_table(
    identifier="iceberg.bids",
    schema=schema,
    location="s3://warehouse/data", 
    partition_spec=partition_spec,
    sort_order=sort_order,
)

# Define a helper function to create datetime values. 
def to_dt(string):
    format = "%Y-%m-%d %H:%M:%S"
    dt = datetime.strptime(string, format)
    return dt

# Generate some trading data. Of course we use AAPL as an example.
print("Add some data")
import pyarrow as pa
tt = pa.timestamp('us')
df = pa.Table.from_pylist(
    [
        {"datetime": pa.scalar(to_dt("2019-08-07 08:35:00"), tt), "symbol": "AAPL", "bid": 195.23, "ask": 195.28},
        {"datetime": pa.scalar(to_dt("2019-08-07 08:35:00"), tt), "symbol": "AAPL", "bid": 195.22, "ask": 195.28},
    ],
)
table.append(df)

# Add more trading data on another day. This will be in another partiion. 
print("Add some more data")
df2 = pa.Table.from_pylist(
    [
        {"datetime": pa.scalar(to_dt("2019-08-09 08:35:00"), tt), "symbol": "AAPL", "bid": 198.23, "ask": 195.45},
        {"datetime": pa.scalar(to_dt("2019-08-09 08:35:00"), tt), "symbol": "AAPL", "bid": 198.25, "ask": 198.50},
    ],
)
table.append(df2)
