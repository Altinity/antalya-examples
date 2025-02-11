#!/usr/bin/env python3
# Python script showing how to create and populate a table in Iceberg. 

# Uncomment to see the module search path. 
#import sys
#print(sys.path)

import pyarrow
import pyiceberg
# Allows us to connect to the catalog. 
from pyiceberg.catalog import load_catalog

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

print("Get table data as a Pandas dataframe and print it")
table = catalog.load_table("iceberg.bids")
df = table.scan().to_pandas()
print(df)
