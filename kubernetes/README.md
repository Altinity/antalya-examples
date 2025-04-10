# Antalya Kubernetes Example

This directory contains samples for querying a Parquet-based data lake
lake using AWS EKS, AWS S3, and Altinity Antalya. 

Note: Iceberg will be covered in the next Antalya build. 

## Quickstart

### Prerequisites

Install: 
* [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
* [terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

### Start Kubernetes

Cd to the terraform directory and follow the installation directions in the 
README.md file to set up a Kubernetes cluster on EKS. 

### Install the Altinity Operator for Kubernetes

Install the latest production version of the [Altinity Kubernetes Operator
for ClickHouse](https://github.com/Altinity/clickhouse-operator). 

```
kubectl apply -f https://raw.githubusercontent.com/Altinity/clickhouse-operator/master/deploy/operator/clickhouse-operator-install-bundle.yaml
```

### Install ClickHouse cluster with Antalya swarm cluster

This step installs a ClickHouse "vector" server that applications can connect 
to, an Antalya swarm cluster, and a Keeper ensemble to allow the swarm servers
to register themselves dynamically. 

#### Using plain manifest files

Cd to the manifests directory and follow the README.md directions. Confirm 
the setup as described in the README.md.

#### Using helm

Coming soon. This will work for any Kubernetes distribution. 

## Running

### Querying Parquet files on AWS S3

AWS kindly provides [AWS Public Block Data](https://registry.opendata.aws/aws-public-blockchain/), 
which we will use as example data for Parquet on S3. 

Start by logging into the vector server. 
```
kubectl exec -it chi-vector-example-0-0-0 -- clickhouse-client
```

Try running a query using only the vector server. 
```
SELECT date, sum(output_count)
FROM s3('s3://aws-public-blockchain/v1.0/btc/transactions/**.parquet', NOSIGN)
WHERE date >= '2025-01-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1
```

This query sets the baseline for execution without assistance from the swarm. 
Depending on the date range you use it is likely to be slow. You can cancel
using ^C. 

Next, let's try a query using the swarm. The object_storage_cluster
setting points to the swarm cluster name.

```
SELECT date, sum(output_count)
FROM s3('s3://aws-public-blockchain/v1.0/btc/transactions/**.parquet', NOSIGN)
WHERE date >= '2025-01-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm';
```

The next query shows results when caches are turned on. 
```
SELECT date, sum(output_count)
FROM s3('s3://aws-public-blockchain/v1.0/btc/transactions/**.parquet', NOSIGN)
WHERE date >= '2025-01-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm',
input_format_parquet_use_metadata_cache = 1, enable_filesystem_cache = 1;
```

Successive queries will complete somewhat faster due to caching.

Next, increase the size of the swarm server by directly editing the
swarm CHI resource, changing the number of shards to 8, and submitting
the changes. (Example using manifest files.)

```
kubectl edit chi swarm
...
              podTemplate: replica
              volumeClaimTemplate: storage
          shardsCount: 4 <-- Change to 8 and save. 
        templates:
...
```

Run the query again after scale-up completes. You should see the response
time drop by roughly 50%. Try running it again. You should see a further drop 
as swarm caches pick up additional files. You can scale up further to see 
additional drops. This setup has been tested to 16 nodes. 
