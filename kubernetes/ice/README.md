# Configuring an Ice REST catalog in Kubernetes

Iceberg REST catalogs enable ClickHouse to access Iceberg catalogs as if
they were databases.  This directory show how to leverage the Altinity 
[Ice Toolset](https://github.com/Altinity/ice) to add an Iceberg REST
catalog to an existing EKS cluster.

## Prerequisites

You should have an EKS cluster already setup using the Terraform 
[main.tf](../kubernetes/main.tf) script. This procedure will also 
work for EKS clusters that you create by other means.  

You will also need eksctl. Install it following the 
[eksctl installation instructions](https://eksctl.io/installation/). 

Finally, these examples assume you have an antalya namespace that is
also the default. 

## IAM Configuration

Start by ensuring that OIDC is correctly configured in your cluster.
Run the following command. You should see a hex string like
CA23823F2D578D6A905B5718679C69D2 as output. If you don't see it refer
to [AWS EKS OIDC docs](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) 
for help. 

```
aws eks describe-cluster --name my-eks-cluster \
  --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5
```

Next, use eksctl to create a Kubernetes ServiceAccount that has
privileges to read and write to S3 buckets. The attached policy is
suitable for testing only--it gives read/write access to all buckets.
In a production environment you would attach a more restrictive policy
that gives privileges on certain buckets.

```
eksctl create iamserviceaccount --name ice-rest-catalog \
 --namespace antalya \
 --cluster my-eks-cluster --role-name eksctl-cluster-autoscaler-role \
 --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
 --approve
```

If you get something wrong and it fails, you need to clean up. Use the
following commands. It's important to clean up *everything* to avoid
weird failures when you try again.

```
eksctl delete iamserviceaccount --name ice-rest-catalog \
 --namespace antalya --cluster my-eks-cluster
aws iam detach-role-policy --role-name=eksctl-cluster-autoscaler-role \
 --policy-arn=arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam delete-role --role-name=eksctl-cluster-autoscaler-role
```

If it still does not work, try going into CloudFormation and deleting
the stack that created the ServiceAccount. (We figured this out so you
don't have to. ;)

## REST Catalog Start and Data Loading

For the remainder of the setup use the 
[Altinity ice project eks sample](https://github.com/Altinity/ice/tree/master/examples/eks).

Clone the ice project to get started. 
```
git clone https://github.com/Altinity/ice
cd ice/examples/eks
```

Follow an adapted procedure from the local README.md. Skip the `eksctl
create cluster` command as you already have a cluster set up. You'll
need to [install devbox](https://github.com/jetify-com/devbox) if you
don't already have it. This example uses us-west-2 as the AWS region.

```
devbox shell

export CATALOG_BUCKET="$USER-ice-rest-catalog-demo"
export AWS_REGION=us-west-2

# create bucket if you don't have it already. 
aws s3api create-bucket --bucket "$CATALOG_BUCKET" \
    --create-bucket-configuration "LocationConstraint=$AWS_REGION"

# deploy etcd
kubectl -n antalya apply -f etcd.eks.yaml

# deploy ice-rest-catalog. The debug-with-ice image has the ice
# utility bundled in the catalog container. 
cat ice-rest-catalog.eks.envsubst.yaml |\
 envsubst -no-unset -no-empty |\
 sed -e 's/debug-0.0.0-SNAPSHOT/debug-with-ice/' > ice-rest-catalog.eks.yaml
kubectl -n antalya apply -f ice-rest-catalog.eks.yaml

# add data to the catalog to make things interesting. 
kubectl -n antalya exec -it ice-rest-catalog-0 -- ice insert nyc.taxis -p \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet

# add a larger dataset from AWS public BTC transaction data.
kubectl -n antalya exec -it ice-rest-catalog-0 -- ice insert btc.transactions \
 -p --s3-no-sign-request --s3-region=us-east-2 \
 's3://aws-public-blockchain/v1.0/btc/transactions/date=2025-0*-*/*.parquet'
```

## Connecting ClickHouse to the ice catalog. 

Issue SQL commands to connect to the Ice catalog. You should see the 
tables you just added. 

```
kubectl -n antalya exec -it chi-vector-example-0-0-0 -- clickhouse-client 
...
SET allow_experimental_database_iceberg = 1;

-- (re)create iceberg db
DROP DATABASE IF EXISTS ice;

CREATE DATABASE ice
  ENGINE = DataLakeCatalog('http://ice-rest-catalog:5000')
  SETTINGS catalog_type = 'rest',
    auth_header = 'Authorization: Bearer foo',
    warehouse = 's3://${CATALOG_BUCKET}';

SHOW TABLES FROM ice;
```

# Troubleshooting

The ice toolset is pretty easy to set up. If you run into trouble it's likely something
to do with AWS IAM. For more hints check out the ice 
[examples/eks/README.md](https://github.com/Altinity/ice/tree/master/examples/eks#readme). 
