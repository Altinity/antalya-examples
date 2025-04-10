# Installing Vector and Swarm clusters using manifest files

This directory shows how to set up an Antalya swarm cluster using 
Kubernetes manifest files. The following manifests are provided. 

* keeper.yaml - Sets up a 3-node keeper ensemble. 
* swarm.yaml - Sets up a 4-node swarm cluster.
* vector.yaml - Sets up a 1-node "vector" cluster. This is where to issue queries. 

IMPORTANT NOTE: The node selectors and tolerations match node pool
default settings from [main.tf](../terraform/main.tf). If you change
those settings you will need to update the manifests according so that
pods can be scheduled.

## Prerequisites

Install [Altinity Kubernetes Operator for ClickHouse](https://github.com/Altinity/clickhouse-operator). 
(Must be 0.24.4 or above to support CHK resource to manage ClickHouse Keeper.)

## Installation

Use Kubectl to install manifests in your default namespace. 
```
kubectl apply -f keeper.yaml
kubectl apply -f vector.yaml
kubectl apply -f gp3-encrypted-fast-storage-class.yaml
kubectl apply -f swarm.yaml
```

The swarm servers use EBS volumes which integrate well with cluster autoscaling
but are suboptimal for caches. 

## NVMe SSD swarm support (experimental)

The [nvme](./nvme) directory contains work in progress. See the
[README.md](nvme/README.md) for more information.

## Verify installation

Connect to the vector server and confirm that all swarm cluster hosts are visible. 

```
kubectl exec -it chi-vector-example-0-0-0 -- clickhouse-client
...
SELECT cluster, groupArray(host_name)
FROM system.clusters
GROUP BY cluster ORDER BY cluster ASC FORMAT Vertical
```

You should see the swarm cluster in the last line with 4 hosts listed. Confirm that 
all hosts are responsive with the following query. 

```
SELECT hostName()
FROM clusterAllReplicas('swarm', system.one)
ORDER BY 1 ASC
```

Your setup is now ready for use. 
