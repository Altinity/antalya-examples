# Command and Configuration Reference

## SQL Syntax Guide

This section shows how to use the Iceberg database engine, table engine, and 
table function. 

### Iceberg Database Engine

The Iceberg database engine connects ClickHouse to an Iceberg REST catalog. The
tables listed in the REST catalog show up as database. The Iceberg REST catalog
must already exist. Here is an example of the syntax. 

```
CREATE DATABASE datalake
ENGINE = Iceberg('http://rest:8181/v1', 'minio', 'minio123')
SETTINGS catalog_type = 'rest', 
storage_endpoint = 'http://minio:9000/warehouse', 
warehouse = 'iceberg'
```

The Iceberg database engine takes three arguments:

* url - Path to Iceberg READ catalog endpoint
* user - Object storage user
* password - Object storage password

The following settings are supported. 

* auth_head - Authorization header of format 'Authorization: <scheme> <auth_info>'
* auth_scope - Authorization scope for client credentials or token exchange
* oauth_server_uri - OAuth server URI
* vended_credentials - Use vended credentials (storage credentials) from catalog
* warehouse - Warehouse name inside the catalog
* storage_endpoint - Object storage endpoint

### Iceberg Table Engine

Will be documented later. 

### Iceberg Table Function

The [Iceberg table function](https://clickhouse.com/docs/en/sql-reference/table-functions/iceberg)
selects from an Iceberg table. It uses the path of the table in object
storage to locate table metadata. Here is an example of the syntax.

```
SELECT count()
FROM iceberg('http://minio:9000/warehouse/data')
```

The iceberg() function is an alias for icebergS3(). See the upstream docs for more information. 

It's important to note that the iceberg() table function expects to see data
and metadata directores after the URL provided as an argument. In other words, 
the Iceberg table must be arranged in object storage as follows:

* http://minio:9000/warehouse/data/metadata - Contains Iceberg metadata files for the table
* http://minio:9000/warehouse/data/data - Contains Iceberg data files for the table

If the files are not laid out as shown above the iceberg() table function
may not be able to read data.

## Swarm Clusters

Swarm clusters are clusters of stateless ClickHouse servers that may be used for parallel
query on S3 files as well as Iceberg tables (which are just collections of S3 files). 

### Using Swarm Clusters to speed up query

To delegate subqueries to a swarm cluster, add the object_storage_cluster setting 
as shown below with the swarm cluster name. 

```
SELECT hostName() AS host, count()
FROM s3('http://minio:9000/warehouse/data/data/**/**.parquet')
GROUP BY host
SETTINGS use_hive_partitioning=1, object_storage_cluster='swarm'
```

Swarm clusters can be used in SELECT queries on the following:

* s3() function
* s3Cluster() function -- Specify as function argument
* iceberg() -- SUPPORTED IN NEXT ANTALYA BUILD
* icebergS3Cluster() -- Specify as function argument
* iceberg table engine -- SUPPORTED IN NEXT ANTALYA BUILD

Here's an example of using the swarm cluster with the icebergS3Cluster()
function.

```
SELECT hostName() AS host, count()
FROM icebergS3Cluster('swarm', 'http://minio:9000/warehouse/data')
GROUP BY host
```

### Configuring swarm cluster autodiscovery

Cluster-autodiscovery uses [Zoo]Keeper as a registry for swarm cluster 
members. Swarm cluster servers register themselves on a specific path
at start-up time to join the cluster. Other servers can read the path 
find members of the swarm cluster. 

To use auto-discovery, you must enable Keeper by adding a `<zookeeper>` 
tag similar to the following example. This must be done for all servers
including swarm servers as well as ClickHouse servers that invoke them. 

```
<clickhouse>
    <zookeeper>
        <node>
            <host>keeper</host>
            <port>9181</port>
        </node>
    </zookeeper>
</clickhouse>
```

You must also enable automatic cluster discovery. 
```
    <allow_experimental_cluster_discovery>1</allow_experimental_cluster_discovery>
```

#### Using a single Keeper ensemble

When using a single Keeper for all servers, add the following remote server 
definition to each swarm server configuration. This provides a path on which
the server will register. 

```
    <remote_servers>
        <!-- Swarm cluster built using remote discovery -->
        <swarm>
            <discovery>
                <path>/clickhouse/discovery/swarm</path>
                <secret>secret_key</secret>
            </discovery>
        </swarm>
    </remote_servers>
```

Add the following remote server definition to each server that _reads_ the 
swarm server list using remote discovery. Note the `<observer>` tag, which 
must be set to prevent non-swarm servers from joining th cluster. 

```
    <remote_servers>
        <!-- Swarm cluster built using remote discovery. -->
        <swarm>
            <discovery>
                <path>/clickhouse/discovery/swarm</path>
                <secret>secret_key</secret>
                <!-- Use but do not join cluster. -->
                <observer>true</observer>
            </discovery>
        </swarm>
    </remote_servers>
```

#### Using multiple keeper ensembles

It's common to use separate keeper ensembles to manage intra-cluster 
replication and swarm cluster discovery. In this case you can enable
an auxiliary keeper that handles only auto-discovery. Here is the 
configuration for such a Keeper ensemble. ClickHouse will 
use this Keeper ensemble for auto-discovery. 

```
<clickhouse>
    <!-- Zookeeper for registering swarm members. -->
    <auxiliary_zookeepers>
        <registry>
            <node>
                <host>keeper</host>
                <port>9181</port>
            </node>
        </registry>
    </auxiliary_zookeepers>
<clickhouse>
```

This is in addition to the settings described in previous sections, 
which remain the same. 

## Configuring Caches

Caches make a major difference in the performance of ClickHouse queries. This 
section describes how to configure them in a swarm cluster. 

### S3 Filesystem Cache

This cache stores blocks read from object storage on local disk. It offers 
a considerable speed advantage, especially when blocks are in storage. The 
S3 filesystem cache requires special configuration each swarm host. 

#### Define the cache

Add a definition like the following to /etc/clickhouse/filesystem_cache.xml 
to set up a filesystem cache. 

```
spec:                                                                          
  configuration:
    files:
      config.d/filesystem_cache.xml: |
        <clickhouse>
          <filesystem_caches>
            <s3_parquet_cache>
              <path>/var/lib/clickhouse/s3_parquet_cache</path>
              <max_size>50Gi</max_size>
            </s3_parquet_cache>
          </filesystem_caches>
        </clickhouse>
```

#### Enable cache use in queries

The following settings control use of the cache. 

* enable_filesystem_cache - Enable filesystem cache (1=enabled)
* enable_filesystem_cache_log - Enable logging of cache operations (1=enabled)
* filesystem_cache_name - Name of the cache to use (must be specified)

You can enable the settings on a query as follows:

```
SELECT date, sum(output_count)
FROM s3('s3://aws-public-blockchain/v1.0/btc/transactions/**.parquet', NOSIGN)
WHERE date >= '2025-01-01' GROUP BY date ORDER BY date ASC
SETTINGS use_hive_partitioning = 1, object_storage_cluster = 'swarm',
enable_filesystem_cache = 1, filesystem_cache_name = 's3_parquet_cache'
```

You can also set cache values in user profiles as shown by the following 
settings in Altinity operator format:

```
spec:
  configuration:
    profiles:
      use_cache/enable_filesystem_cache: 1
      use_cache/enable_filesystem_cache_log: 1
      use_cache/filesystem_cache_name: "s3_parquet_cache"
```

#### Clear cache

Issue the following command on any swarm server. (It does not work from 
other clusters.)

```
SYSTEM DROP FILESYSTEM CACHE ON CLUSTER 'swarm'
```

#### Find out how the cache is doing. 

Get statistics on file system caches across the swarm. 

```
SELECT hostName() host, cache_name, count() AS segments, sum(size) AS size,
    min(cache_hits) AS min_hits, avg(cache_hits) AS avg_hits,
    max(cache_hits) AS max_hits
FROM clusterAllReplicas('swarm', system.filesystem_cache)
GROUP BY host, cache_name
ORDER BY host, cache_name ASC
FORMAT Vertical
```
