# Antalya Kubernetes Example

This directory contains samples for querying a Parquet-based data lake
lake using AWS EKS, AWS S3, and Project Antalya. 

## Quickstart

### Prerequisites

Install: 
* [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
* [terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

### Start Kubernetes

Cd to the terraform directory and follow the installation directions in the 
README.md file to set up a Kubernetes cluster on EKS. Here's the short form. 

```
cd terraform
terraform init
terraform apply
aws eks update-kubeconfig --name my-eks-cluster  # Default cluster name
```

Create a namespace named antalya and make it the default. (You don't
have to do this but the examples assume it.)

```
kubectl create ns antalya
kubectl config set-context --current --namespace=antalya
```

### Install the Altinity Operator for Kubernetes

Install the latest production version of the [Altinity Kubernetes Operator
for ClickHouse](https://github.com/Altinity/clickhouse-operator). 

```
kubectl apply -f https://raw.githubusercontent.com/Altinity/clickhouse-operator/master/deploy/operator/clickhouse-operator-install-bundle.yaml
```

### Install an Iceberg REST catalog

This step installs an Iceberg REST catalog using the 
Altinity [Ice Toolset](https://github.com/Altinity/ice). 

Follow instructions in the [ice directory README.md](ice/README.md). 

### Install ClickHouse server with Antalya swarm cluster

This step installs a ClickHouse "vector" server that applications can connect 
to, an Antalya swarm cluster, and a Keeper ensemble to allow the swarm servers
to register themselves dynamically. 

#### Using plain manifest files

Cd to the manifests directory and install the manifests in the default 
namespace. 

```
cd manifest
kubectl apply -f gp3-encrypted-fast-storage-class.yaml
kubectl apply -f keeper.yaml
kubectl apply -f swarm.yaml
kubectl apply -f vector.yaml
```

#### Using helm

The helm script is in the helm directory. 

## Running

### Querying Parquet files on AWS S3 and Apache Iceberg

AWS kindly provides 
[AWS Public Block Data](https://registry.opendata.aws/aws-public-blockchain/), 
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
WHERE date >= '2025-02-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm';
```

The next query shows results when caches are turned on. 
```
SELECT date, sum(output_count)
FROM s3('s3://aws-public-blockchain/v1.0/btc/transactions/**.parquet', NOSIGN)
WHERE date >= '2025-02-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm',
input_format_parquet_use_metadata_cache = 1, enable_filesystem_cache = 1;
```

Successive queries will complete faster as caches load. 

### Improving performance by scaling up the swarm

You can at any time increase the size of the swarm server by directly
editing the swarm CHI resource, changing the number of shards to 8,
and submitting the changes. (Example using manifest files.)

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

To scale down the swarm, just edit the shardsCount again and set it to 
a smaller number. 

Important note: You may see failed queries as the swarm scales down. This
is [a known issue](https://github.com/Altinity/ClickHouse/issues/759)
and will be corrected soon.

### Querying Parquet files in Iceberg

You can load the public data set into Iceberg, which makes the queries
much easier to construct. Here are examples of the same queries when 
the public data are available in Iceberg once you do the ice REST 
catalog installation. 

```
SET allow_experimental_database_iceberg=true;

-- Use this for Antalya 25.3 or above. 
CREATE DATABASE ice
  ENGINE = DataLakeCatalog('http://ice-rest-catalog:5000')
  SETTINGS catalog_type = 'rest',
    auth_header = 'Authorization: Bearer foo',
    warehouse = 's3://rhodges-ice-rest-catalog-demo}';

-- Use this for Antalya 25.2 or below. 
CREATE DATABASE ice
  ENGINE = Iceberg('https://rest-catalog.dev.altinity.cloud')
  SETTINGS catalog_type = 'rest',
    auth_header = 'Authorization: Bearer jj...2j',
    warehouse = 's3://aws...iceberg';
```

Show the tables available in the database. 

```
SHOW TABLES FROM ice

   ┌─name─────────────┐
1. │ btc.transactions │
2. │ nyc.taxis        │
   └──────────────────┘
```

Try counting rows. This goes faster if you enable caching of Iceberg metadata. 

```
SELECT count()
FROM ice.`btc.transactions`
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm',
input_format_parquet_use_metadata_cache = 1, enable_filesystem_cache = 1,
use_iceberg_metadata_files_cache=1;
```

Now try the same query that we ran earlier directly against the public S3 
dataset files. Caches are not enabled. 

```
SELECT date, sum(output_count)
FROM ice.`btc.transactions`
WHERE date >= '2025-02-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm';
```

Try the same query with all caches enabled. It should be faster. 

```
SELECT date, sum(output_count)
FROM ice.`btc.transactions`
WHERE date = '2025-02-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm',
input_format_parquet_use_metadata_cache = 1, enable_filesystem_cache = 1,
use_iceberg_metadata_files_cache = 1;
```
