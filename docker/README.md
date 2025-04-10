# Antalya Docker Example

This directory contains samples for construction of an Iceberg-based data 
lake using Docker Compose and Altinity Antalya. 

The docker compose structure and the Python scripts take inspiration from 
[ClickHouse integration tests for Iceberg](https://github.com/ClickHouse/ClickHouse/tree/master/tests/integration/test_database_iceberg) but deviate substantially. 

## Quickstart

Examples are for Ubuntu. Adjust commands for other distros.

### Install Docker

Install [Docker Desktop](https://docs.docker.com/engine/install/) and 
[Docker Compose](https://docs.docker.com/compose/install/). 

### Bring up the data lake

```
./x-up.sh
```

### Enable Python and create data

Install Python virtual environment module for your python version. Example shown
below. 
```
sudo apt install python3.12-venv
```

Create and invoke the venv, then install required modules. 
```
python3.12 -m venv venv
. ./venv/bin/activate
pip install --upgrade pip
pip install pyarrow pyiceberg pandas
```

Start Docker + Add data. 
```
docker compose up -d
python iceberg_setup.py
```

### Demonstrate Antalya queries against a swarm cluster

Connect to the Antalya server container and start clickhouse-client.
```
docker exec -it antalya clickhouse-client
```

Confirm you are connected to Antalya. 
```
SELECT version()

   ┌─version()─────────────────────┐
1. │ 24.12.2.20101.altinityantalya │
   └───────────────────────────────┘
```

Select directly from S3 data using the swarm cluster. 
```
SELECT hostName() AS host, count()
FROM s3('http://minio:9000/warehouse/data/data/**/**.parquet')
GROUP BY host
SETTINGS use_hive_partitioning=1, object_storage_cluster='swarm'
```

Select Iceberg table data. 
```
SELECT hostName() AS host, count()
FROM icebergS3Cluster('swarm', 'http://minio:9000/warehouse/data')
GROUP BY host
SETTINGS object_storage_cluster = 'swarm'
```

You will be able to see swarm host names in the results for both queries.

## Reference

This section shows operations in complete detail. 

### Scripts

#### Bring up the data lake.
```
./x-up.sh
```

#### Bring down the data lake.

Minio loses its data when you do this. It's best to remove all containers
to ensure the data is consistent. 
```
./x-down.sh
```

#### Cleaning up

This deletes *all* containers and volumes for a fresh start. Do not use it
if you have other Docker applications running. 
```
./x-clean.sh -f
```

#### Handy Docker commands

Connect to Antalya, Spark, and Iceberg REST containers. 
```
docker exec -it antalya /bin/bash
docker exec -it spark-iceberg /bin/bash
docker exec -it iceberg-rest /bin/bash
```

### Python commands to create and read Iceberg data

Use Python scripts to create and prove you can read data stored in Iceberg. 
They use pyiceberg. 
```
python iceberg_setup.py
python iceberg_read.py
```
These commands create a table in Iceberg named iceberg.bids with 4 rows. 

WARNING: You may need to run these in the lib/python3.x/site-packages 
directory of your virtual environment. There is a bug in some 
environments that prevents pyiceberg libraries from loading properly. 
Copy the scripts into the directory and run them there. 

### Using Antalya to query Iceberg data

Connect to ClickHouse and use the following commands to run queries. 
You can access data in 3 different ways. 

#### Direct query on Parquet files. 

You can connect to the Parquet files directly without reading Iceberg 
metadata as follows. You just have to know where the files are located
on S3. 
```
SELECT hostName(), count() 
FROM s3('http://minio:9000/warehouse/data/data/**/**.parquet')

SELECT hostName(), * 
FROM s3('http://minio:9000/warehouse/data/data/**/**.parquet')
```
Both of them read all files from all Iceberg snapshots. If you remove 
or change data they won't give the right answer. 

#### Direct query on Parquet files using Antalya swarm cluster. 

First, make sure you are talking to an Antalya build. 
```
SELECT version()

   ┌─version()─────────────────────┐
1. │ 24.12.2.20101.altinityantalya │
   └───────────────────────────────┘
```

You can dispatch queries to the Antalya swarm cluster using s3() 
function with the object_storage_cluster setting. Or you can use 
s3Cluster() with the swarm cluster name. 

```
SELECT hostName() AS host, count() 
FROM s3('http://minio:9000/warehouse/data/data/**/**.parquet')
GROUP BY host
SETTINGS use_hive_partitioning=1, object_storage_cluster='swarm'

SELECT hostName() AS host, * 
FROM s3Cluster('swarm', 'http://minio:9000/warehouse/data/data/**/**.parquet')
SETTINGS use_hive_partitioning=1
```

If you are curious to find out where your query was actually processed,
you can find out easily. Take the query_id that clickhouse-client prints
and run a query like the following. You'll see all query log records.

```
SELECT hostName() AS host, type, initial_query_id, is_initial_query, query
FROM clusterAllReplicas('all', system.query_log)
WHERE (type = 'QueryStart') 
AND (initial_query_id = '8051eef1-e68b-491a-b63d-fac0c8d6ef27')\G
```

#### Query using Iceberg metadata without a catalog

Use the icebergS3 table function if you want to avoid specifying the
exact location of files. 

```
SELECT count()
FROM iceberg('http://minio:9000/warehouse/data')

SELECT *
FROM iceberg('http://minio:9000/warehouse/data')
```

Notice that the path is to your data directory, which has metadata and data
under it. There will be trouble if it contains more than one table. 

#### Query on Iceberg tables using Antalya swarm cluster

(Partially works in Antalya build 24.12.2.20101. )

You can use the swarm cluster also with the iceberg table function. Here 
is an example. To get this to work you must use the icebergS3Cluster()
function. 
```
SELECT hostName() AS host, count()
FROM icebergS3Cluster('swarm', 'http://minio:9000/warehouse/data')
GROUP BY host
SETTINGS object_storage_cluster = 'swarm'
```

This will work with regular iceberg() table functions in the next build. 

#### Query using the Iceberg REST catalog

Create an Iceberg database. This is the easiest way to locate data. 

```
DROP DATABASE IF EXISTS datalake
;
SET allow_experimental_database_iceberg=true
;
CREATE DATABASE datalake
ENGINE = Iceberg('http://rest:8181/v1', 'minio', 'minio123')
SETTINGS catalog_type = 'rest', storage_endpoint = 'http://minio:9000/warehouse', warehouse = 'iceberg' 
;
SHOW TABLES from datalake
;
SELECT count() FROM datalake.`iceberg.bids`
;
SELECT * FROM datalake.`iceberg.bids`
```

#### Query Iceberg and local data together

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

#### Query on Iceberg database using Antalya swarm cluster

(Does not work in Antalya build 24.12.2.20101. Will be implemented in
the next build.)

### Using Spark

Connect to the spark-iceberg container command line. 
```
docker exec -it spark-iceberg /bin/bash
```

Start the Spark scala shell. Do not be alarmed by its slowness. 
```
spark-shell \
--conf spark.sql.catalog.rest_prod=org.apache.iceberg.spark.SparkCatalog \
--conf spark.sql.catalog.rest_prod.type=rest \
--conf spark.sql.catalog.rest_prod.uri=http://rest:8080
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

Try selecting data each of the three ways in ClickHouse to see which of them 
still give the right answers. 

### Fetching values from Iceberg catalog using curl

The Iceberg REST API is simple to query using curl. The documentation is 
effectively [the full REST spec in the Iceberg GitHub Repo](https://github.com/apache/iceberg/blob/main/open-api/rest-catalog-open-api.yaml). Meanwhile here 
are a few examples that you can try on this project. 

Find namespaces. 
```
curl http://localhost:8182/v1/namespaces | jq -s
```

Find tables in namespace. 
```
curl http://localhost:8182/v1/namespaces/iceberg/tables | jq -s
```

Find table spec in Iceberg. 
```
curl http://localhost:8182/v1/namespaces/iceberg/tables/bids | jq -s
```

Find table spec in Iceberg. 
```
curl http://localhost:8182/v1/namespaces/iceberg/tables/bids/snapshots | jq -s
```
