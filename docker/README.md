# Antalya Docker Example

This directory contains samples for construction of an Iceberg-based data 
lake using Docker Compose and Altinity Antalya. 

The docker compose structure and the Python scripts took early inspiration from 
[ClickHouse integration tests for Iceberg](https://github.com/ClickHouse/ClickHouse/tree/master/tests/integration/test_database_iceberg) but have deviated substantially since then. 

## Quickstart

Examples are for Ubuntu. Adjust commands for other distros.

### Install prerequisite software

Install [Docker Desktop](https://docs.docker.com/engine/install/) and 
[Docker Compose](https://docs.docker.com/compose/install/). 

Install the Altinity ice catalog client. (Requires a JDK.)

```
sudo apt install openjdk-21-jdk
curl -sSL https://github.com/altinity/ice/releases/download/v0.8.1/ice-0.8.1 \
  -o ice && chmod a+x ice && sudo mv ice /usr/local/bin/
```

### Bring up the data lake

```
docker compose up -d
```

### Load data

Create a table by loading using the ice catalog client. This creates the 
table automatically from the schema in the parquet file. 

```
ice insert nyc.taxis -p \
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
```

### Compute aggregates on Parquet data

Connect to the Antalya server container and start clickhouse-client.
```
docker exec -it vector clickhouse-client
```

Set up database pointing to Ice[berg] REST catalog. 
```
SET allow_experimental_database_iceberg = 1;

DROP DATABASE IF EXISTS ice;

CREATE DATABASE ice ENGINE = DataLakeCatalog('http://ice-rest-catalog:5000')
SETTINGS catalog_type = 'rest',
  auth_header = 'Authorization: Bearer foo',
  storage_endpoint = 'http://minio:9000',
  warehouse = 's3://warehouse';
```

Query data on vector only, followed by vector plus swarm servers.
```
-- Run query only on initiator. 
SELECT
    toDate(tpep_pickup_datetime) AS date,
    avg(passenger_count) AS passengers,
    avg(fare_amount) AS fare
FROM ice.`nyc.taxis` GROUP BY date ORDER BY date

-- Delegate to swarm servers. 
SELECT
    toDate(tpep_pickup_datetime) AS date,
    avg(passenger_count) AS passengers,
    avg(fare_amount) AS fare
FROM ice.`nyc.taxis` GROUP BY date ORDER BY date
SETTINGS object_storage_cluster='swarm'
```

### Bring down cluster and delete data

```
docker compose down
sudo rm -rf data
```

## Load data with Python and view with ClickHouse

### Enable Python

Install Python virtual environment module for your python version. Example shown
below for Python 3.12. 

```
sudo apt install python3.12-venv
```

Create and invoke the venv, then install required modules. 
```
python3.12 -m venv venv
. ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Load and read data with pyiceberg library
```
python iceberg_setup.py
python iceberg_read.py
```

### Demonstrate Antalya queries against data from Python

Connect to the Antalya server container and start clickhouse-client.
```
docker exec -it vector clickhouse-client
```

Query data on vector only, followed by vector plus swarm servers.
```
-- Run query only on initiator. 
SELECT * FROM ice.`iceberg.bids`

-- Delegate to swarm servers. 
SELECT symbol, avg(bid)
FROM ice.`iceberg.bids` GROUP BY symbol
SETTINGS object_storage_cluster = 'swarm'
```

## Using Spark with ClickHouse and Ice

Connect to the spark-iceberg container command line. 
```
docker exec -it spark-iceberg /bin/bash
```

Start the Spark scala shell. 
```
spark-shell 
```

Read data and prove you can change it as well by running the commands below. 
```
spark.sql("SHOW NAMESPACES").show()
spark.sql("SHOW TABLES FROM iceberg").show()
spark.sql("SHOW CREATE TABLE iceberg.bids").show(truncate=false)
spark.sql("SELECT * FROM iceberg.bids").show()
spark.sql("DELETE FROM iceberg.bids WHERE bid < 198.23").show()
spark.sql("SELECT * FROM iceberg.bids").show()
```

Try reading the table from ClickHouse. The deleted rows should be gone. 

## Additional help and troubleshooting

### Logs

Logs are in the data directory along with service data. 

### Cleaning up

This deletes *all* containers and volumes for a fresh start. Do not use it
if you have other Docker applications running. 
```
./clean-all.sh -f
```

### Find out where your query ran

If you are curious to find out where your query was actually processed,
you can find out easily. Take the query_id that clickhouse-client prints
and run a query like the following. You'll see all query log records.

```
SELECT hostName() AS host, type, initial_query_id, is_initial_query, query
FROM clusterAllReplicas('all', system.query_log)
WHERE (type = 'QueryFinish') 
AND (initial_query_id = '8051eef1-e68b-491a-b63d-fac0c8d6ef27')\G
```

### Setting up Iceberg databases

These commands when the vector server comes up for the first time. 

```
SET allow_experimental_database_iceberg = 1;

DROP DATABASE IF EXISTS ice;

CREATE DATABASE ice
  ENGINE = DataLakeCatalog('http://ice-rest-catalog:5000')
  SETTINGS catalog_type = 'rest',
    auth_header = 'Authorization: Bearer foo',
    storage_endpoint = 'http://minio:9000',
    warehouse = 's3://warehouse';
```

### Query Iceberg and local data together

Create a local table and populate it with data from Iceberg, altering
data to make it different. 

```
CREATE DATABASE IF NOT EXISTS local
;
CREATE TABLE local.bids AS datalake.`iceberg.bids`
ENGINE = MergeTree
PARTITION BY toDate(datetime)
ORDER BY (symbol, datetime)
SETTINGS allow_nullable_key = 1
;
-- Pull some data into the local table, making it look different. 
INSERT INTO local.bids 
SELECT datetime + toIntervalDay(4), symbol, bid, ask
FROM datalake.`iceberg.bids`
;
SELECT *
FROM local.bids
UNION ALL
SELECT *
FROM datalake.`iceberg.bids`
;
-- Create a merge table.
CREATE TABLE all_bids AS local.bids
ENGINE = Merge(REGEXP('local|datalake'), '.*bids')
;
SELECT * FROM all_bids
;
```

### Fetching values from Iceberg catalog using curl

The Iceberg REST API is simple to query using curl. The documentation is 
effectively [the full REST spec in the Iceberg GitHub Repo](https://github.com/apache/iceberg/blob/main/open-api/rest-catalog-open-api.yaml). Meanwhile here 
are a few examples that you can try on this project. 

Find namespaces. 
```
curl -H "Authorization: bearer foo" http://localhost:5000/v1/namespaces | jq -s
```

Find tables in namespace. 
```
curl -H "Authorization: bearer foo" http://localhost:5000/v1/namespaces/iceberg/tables | jq -s
```

Find table spec in Iceberg. 
```
curl -H "Authorization: bearer foo" http://localhost:5000/v1/namespaces/iceberg/tables/bids | jq -s
```
