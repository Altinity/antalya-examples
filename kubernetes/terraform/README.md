# Installing AWS EKS using terraform

This directory shows how to use the Altinity 
[terraform-aws-eks-clickhouse](https://github.com/Altinity/terraform-aws-eks-clickhouse)
module to stand up an EKS cluster. 

## Description

The main.tf sets up an EKS cluster in a single AZ. The cluster has 
3 node groups. 

* clickhouse - VMs for ClickHouse permanent nodes
* clickhouse-swarm - VMs for ClickHouse swarm nodes
* system - VMs for system nodes including ClickHouse Keeper

You can extend the example to multiple AZs by uncommenting code lines
appropriately. 

## Installation

1. Edit the main.tf file. 
2. Update the cluster name, region, and any other parameters you wish to change. 
3. Follow the installation instructions. Typical commands are shown below. 

```
terraform init
terraform apply
aws eks update-kubeconfig --name my-eks-cluster 
```

## Trouble-shooting

Use aws eks commands to check configuration of the deployed cluster. 
Here's how to see available EKS clusters in the region. 

```
aws eks list-clusters
```

Show the node groups in a single cluster. 

```
aws eks list-nodegroups --cluster=my-eks-cluster
```

Show the details of a node group. Helpful to ensure you have auto-scaling 
limits set correctly. 
```
aws eks describe-nodegroup --cluster=my-eks-cluster \
 --nodegroup=clickhouse-20250224214119166800000016
```
