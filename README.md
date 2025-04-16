<a href="https://altinity.com/slack">
  <img src="https://img.shields.io/static/v1?logo=slack&logoColor=959DA5&label=Slack&labelColor=333a41&message=join%20conversation&color=3AC358" alt="AltinityDB Slack" />
</a>

# Altinity Antalya Examples Project

Altinity Antalya is a new branch of ClickHouse® code designed to
integrate real-time analytic query with data lakes.  This project
provides documentation as well as working code examples to help you use
and contribute to Antalya.

## Antalya Goals and Roadmap

The main goals of Antalya are as follows. 

* Enable real-time analytics to work off a single copy of
  data that is shared with AI and data science applications.
* Provide a single SQL endpoint for native ClickHouse® and data lake data.
* Use open table formats to enable easy access from any application type.
* Separate compute and storage; moreover, allow usres to scale compute 
  for ingest, merge, transformatino, and query independently. 

Antalya will implement these goals through the following concrete features:

1. Optimize query performance of ClickHouse® on Parquet files stored 
   S3-compatible object storage. 
2. Enable ClickHouse® clusters to add pools of stateless servers aka swarm
   clusters that handle query and insert operations on shared object storage 
   files with linear scaling.
3. Adapt ClickHouse® to use Iceberg tables as shared storage.
4. Enable ClickHouse® clusters to extend existing tables onto unlimited
   Iceberg storage with transparent query across both native MergeTree and
   Parquet data. 
5. Simplify backup and DR by leveraging Iceberg snapshots.
6. Maintain full compability with upstream ClickHouse® features and
   bug fixes.

At this time Antalya builds demonstrate features 1, 2, 3 (partially), and 6. 

## Licensing

Antalya is licensed under Apache 2.0 license. There are no feature
hold-backs.

## Quick Start

See the [Docker Quick Start](./docker/README.md) to try out Antalya in
a few minutes using Docker Compose on a laptop.

## Scalable Swarm Example

For a fully functional swarm cluster implemention, look at the
[kubernetes](kubernetes/README.md) example. It demonstrates use of swarm
clusters on a large blockchain dataset stored in Parquet.

## Antalya Binaries

### Packages

Antalya ClickHouse® server and keeper packages are available on the 
[builds.altinity.cloud](https://builds.altinity.cloud/) page. Scan to the last 
section to find them. 

### Containers

Antalya ClickHouse® server and ClickHouse® keeper containers are available
on Docker Hub. To start Antalya run the following Docker commands:

```
docker run altinity/ClickHouse®-server:24.12.2.20101.altinityantalya
docker run altinity/ClickHouse®-keeper:24.12.2.20101.altinityantalya
```

## Documentation

Look in the docs directory for current documentation. 

* [Antalya Concepts Guide](docs/concepts.md) 
* [Antalya Feature Status](docs/feature-status.md) 
* [Command and Configuration Reference](docs/reference.md)

## Code

To access Antalya code run the following commands. 

```
git clone git@github.com:Altinity/ClickHouse®.git Antalya-ClickHouse®
cd Antalya-ClickHouse®
git checkout project-antalya-24.12.2
```

We will be changing the active Antalya branch name to be more 
memory-friendly shortly. 

## Building

Follow ClickHouse® build instructions. 

## Contributing

We welcome contributions. We're setting up procedures for community
contribution now. Please contact us to find out how to join the project.

## Community Support

Join the [AltinityDB Slack Workspace](https://altinity.com/slack) or 
[log an issue](https://github.com/Altinity-Research/antalya-examples/issues) to get help. 

## Commercial Support

Altinity is the primary maintainer of Antalya. It is the basis of our data 
lake-enabled Altinity.Cloud and is also used in self-managed installations. 
Altinity offers a range of services related to ClickHouse® and data lakes. 

- [Official website](https://altinity.com/) - Get a high level overview of Altinity and our offerings.
- [Altinity.Cloud](https://altinity.com/cloud-database/) - Run ClickHouse® in our cloud or yours.
- [Altinity Support](https://altinity.com/support/) - Get Enterprise-class support for ClickHouse®.
- [Slack](https://altinity.com/slack) - Talk directly with ClickHouse® users and Altinity devs.
- [Contact us](https://hubs.la/Q020sH3Z0) - Contact Altinity with your questions or issues.
- [Free consultation](https://hubs.la/Q020sHkv0) - Get a free consultation with a ClickHouse® expert today.
