<div align=center>

<a href="https://altinity.com/slack">
  <img src="https://img.shields.io/static/v1?logo=slack&logoColor=959DA5&label=Slack&labelColor=333a41&message=join%20conversation&color=3AC358" alt="AltinityDB Slack" />
</a>

<picture align=center>
    <source media="(prefers-color-scheme: dark)" srcset="/docs/images/logo_horizontal_blue_white.png">
    <source media="(prefers-color-scheme: light)" srcset="/docs/images/logo_horizontal_blue_black.png">
    <img alt="Altinity company logo" src="/docs/images/logo_horizontal_blue_black.png">
</picture>

</div>

# Altinity Project Antalya Examples

Project Antalya is a new branch of ClickHouse® code designed to
integrate real-time analytic query with data lakes.  This project
provides documentation as well as working code examples to help you use
and contribute to Antalya.

*Important Note!* Altinity maintains and supports Project Antalya. Altinity 
is not affiliated or associated with ClickHouse Inc any way. ClickHouse® is 
a registered trademark of ClickHouse, Inc. 

See the 
[Community Support Section](#community-support) if you want to ask 
questions or log ideas and issues.

## Project Antalya Goals

Analytic data size has increased to a point where traditional designs
based on shared-nothing architectures and block storage are prohibitively
expensive to operate. Project Antalya introduces a fully open source
architecture for cost-efficient, real-time systems using cheap object
storage and scalable compute, specifically:

* Enable real-time analytics to work off a single copy of
  data that is shared with AI and data science applications.
* Provide a single SQL endpoint for native ClickHouse® and data lake data.
* Use open table formats to enable easy access from any application type.
* Separate compute and storage; moreover, allow users to scale compute 
  for ingest, merge, transformation, and query independently. 

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
5. Simplify backup and DR by leveraging Iceberg features like snapshots.
6. Maintain full compability with upstream ClickHouse® features and
   bug fixes.

## Roadmap

[Project Antalya Roadmap 2025 - Real-Time Data Lakes](https://github.com/Altinity/ClickHouse/issues/804)

## Licensing

Project Antalya code is licensed under Apache 2.0 license. There are no feature
hold-backs.

## Quick Start

See the [Docker Quick Start](./docker/README.md) to try out Antalya in
a few minutes using Docker Compose on a laptop.

## Scalable Swarm Example

For a fully functional swarm cluster implemention, look at the
[kubernetes](kubernetes/README.md) example. It demonstrates use of swarm
clusters on a large blockchain dataset stored in Parquet.

## Project Antalya Binaries

### Packages

Project Antalya ClickHouse® server and keeper packages are available on the 
[builds.altinity.cloud](https://builds.altinity.cloud/) page. Scan to the last 
section to find them. 

### Containers

Project Antalya ClickHouse® server and ClickHouse® keeper containers
are available on Docker Hub.

Check for the latest build on 
[Docker Hub](https://hub.docker.com/r/altinity/clickhouse-server/tags). 

## Documentation

Look in the docs directory for current documentation. More is on the way. 

* [Project Antalya Concepts Guide](docs/concepts.md) 
* [Command and Configuration Reference](docs/reference.md)

See also the [Project Antalya Launch Video](https://altinity.com/events/scale-clickhouse-queries-infinitely-with-10x-cheaper-storage-introducing-project-antalya) 
for an introduction to Project Antalya and a demo of performance.

The [Altinity Blog](https://altinity.com/blog/) has regular articles 
on Project Antalya features and performance. 

## Code

To access Project Antalya code run the following commands. 

```
git clone git@github.com:Altinity/ClickHouse.git Altinity-ClickHouse
cd Altinity-ClickHouse
git branch
```

You will be in the antalya branch by default. 

## Building

Build instructions are located [here](https://github.com/Altinity/ClickHouse/blob/antalya/docs/en/development/developer-instruction.md) 
in the Altinity ClickHouse code tree. Project Antalya code does not
introduce new libaries or build procedures.

## Contributing

We welcome contributions. We're setting up procedures for community
contribution. For now, please contact us in Slack to find out how to
join the project.

## Community Support

* Join the [AltinityDB Slack Workspace](https://altinity.com/slack) to ask questions. 
* [Log an issue on this documentation](https://github.com/Altinity/antalya-examples/issues).
* [Log an issue on Antalya code](https://github.com/Altinity/ClickHouse/issues).

## Commercial Support

Altinity is the primary maintainer of Project Antalya. It is the
basis of our data lake-enabled Altinity.Cloud and is also used in
self-managed installations.  Altinity offers a range of services related
to ClickHouse® and data lakes.

- [Official website](https://altinity.com/) - Get a high level overview of Altinity and our offerings.
- [Altinity.Cloud](https://altinity.com/cloud-database/) - Run Antalya in your cloud or ours. 
- [Altinity Support](https://altinity.com/support/) - Get Enterprise-class support for ClickHouse®.
- [Slack](https://altinity.com/slack) - Talk directly with ClickHouse® users and Altinity devs.
- [Contact us](https://hubs.la/Q020sH3Z0) - Contact Altinity with your questions or issues.
- [Free consultation](https://hubs.la/Q020sHkv0) - Get a free consultation with a ClickHouse® expert today.
