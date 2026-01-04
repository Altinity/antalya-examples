# Antalya Python Examples

This directory contains Python samples as well as a basic test for both docker and kubernetes samples. 

## Prerequisites

Bring up the data lake using the docker example. 

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
