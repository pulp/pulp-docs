---
date: 2025-03-11T08:30:00+00:00
title: Checkpoint Support - A Journey Towards Predictable and Consistent Deployments
author: Moustafa Moustafa
tags:
  - announcement
---

In the ever-evolving landscape of software development, ensuring predictability and consistency in
deployments has always been a challenge.
Our team faced similar hurdles, especially when managing historical versions of repositories.
We needed a solution that could help us recreate environments from specific points in time, ensure
reproducible deployments, and track changes in package behavior over time.

Inspired by the success stories of [Ubuntu Snapshots on Azure](https://ubuntu.com/blog/ubuntu-snapshots-on-azure-ensuring-predictability-and-consistency-in-cloud-deployments) and the
[increased security and resiliency of Canonical workloads on Azure](https://techcommunity.microsoft.com/blog/linuxandopensourceblog/increased-security-and-resiliency-of-canonical-workloads-on-azure---now-in-previ/3970623), we
embarked on a journey to develop a feature that could address these challenges.

<!-- more -->

## The Problem

Imagine working on a project where you need to ensure that your deployment environment is consistent
with a specific point in time.
This is crucial for debugging, testing, and even for compliance purposes. However, without a robust
system in place, managing and accessing historical versions of repositories can be a daunting task.

## The Solution: Checkpoint

After weeks of brainstorming, development, and testing, we are thrilled to announce the release of
the Checkpoint feature in Pulp!
Think of it as similar to [snapshot.debian.org](https://snapshot.debian.org/) or [snapshot.ubuntu.com](https://snapshot.ubuntu.com/).
This new addition allows you to manage and access historical versions of repositories, enhancing
your content management capabilities.
**This feature is available as a tech-preview starting from Pulp version 3.74.0.**

## Key Benefits

* **Historical Version Management:** Easily recreate environments from specific points in time.
This is particularly useful for debugging and compliance purposes.
* **Reproducible Deployments:** Ensure consistent replication of validated environments.
This means that you can deploy the same environment multiple times with the same results.
* **Structured Update Workflow:** Track changes in package behavior over time.
This helps in understanding how updates affect your environment and in planning future updates.

## How It Works

The Checkpoint feature integrates seamlessly with Pulp, allowing you to create and manage
checkpoints for your repositories.
These checkpoints act as snapshots, capturing the state of your repository at a specific point in time.
You can then use these checkpoints to recreate environments, ensuring that they are consistent with
the state of the repository at the time the checkpoint was created.

For more details on how plugins can enable the checkpoint feature, check out [this guide](https://pulpproject.org/pulpcore/docs/dev/learn/subclassing/checkpoint/).

For repo admins looking to manage checkpoints for their repos, [this guide](https://pulpproject.org/pulpcore/docs/user/guides/checkpoint/) provides all the necessary steps.

## Example Usage with Pulp CLI

Here's a step-by-step example of how to use the checkpoint feature with the pulp CLI.

### Setting Up the Repository, Remote, and Distributions

First, set up the repository, remote, and distributions:

```shell
pulp file remote create --url https://fixtures.pulpproject.org/file/PULP_MANIFEST --name myfile
pulp file repository create --name myfile --remote myfile
pulp file distribution create --name myfile --repository myfile --base-path myfile  # regular distro
pulp file distribution create --checkpoint --name myfile-snapshot --repository myfile --base-path checkpoints/myfile  # checkpoint distro
```

### Creating an Empty Publication for Testing

Next, create an empty publication for testing purposes:

```shell
pulp file publication create --checkpoint --repository myfile  # use "--checkpoint" to create the publication
http ${CONTENT_ADDR}/pulp/content/checkpoints/myfile/  # one checkpoint

HTTP/1.1 200 OK
Content-Length: 296
Content-Type: text/html
Date: Tue, 18 Mar 2025 14:04:11 GMT
Server: Python/3.10 aiohttp/3.8.1
X-PULP-CACHE: MISS
<html>
<head><title>Index of </title></head>
<body bgcolor="white">
<h1>Index of </h1>
<hr><pre><a href="../">../</a>
<a href="20250318T140338Z/">20250318T140338Z/</a>                                                                                   18-Mar-2025 14:03
</pre><hr></body>
</html>
```

### Syncing the Repository and Creating Another Checkpoint Publication

Sync the repository and create another checkpoint publication:

```shell
pulp file repository sync --name myfile
pulp file publication create --checkpoint --repository myfile
http ${CONTENT_ADDR}/pulp/content/checkpoints/myfile/

HTTP/1.1 200 OK
Content-Length: 448
Content-Type: text/html
Date: Tue, 18 Mar 2025 14:05:04 GMT
Server: Python/3.10 aiohttp/3.8.1
X-PULP-CACHE: MISS
<html>
<head><title>Index of </title></head>
<body bgcolor="white">
<h1>Index of </h1>
<hr><pre><a href="../">../</a>
<a href="20250318T140338Z/">20250318T140338Z/</a>                                                                                   18-Mar-2025 14:03
<a href="20250318T140442Z/">20250318T140442Z/</a>                                                                                   18-Mar-2025 14:04
</pre><hr></body>
</html>


http ${CONTENT_ADDR}/pulp/content/checkpoints/myfile/20250318T140442Z/

HTTP/1.1 200 OK
Content-Length: 835
Content-Type: text/html
Date: Tue, 18 Mar 2025 14:06:31 GMT
Server: Python/3.10 aiohttp/3.8.1
X-PULP-CACHE: MISS
<html>
<head><title>Index of /pulp/content/checkpoints/myfile/20250318T140442Z/</title></head>
<body bgcolor="white">
<h1>Index of /pulp/content/checkpoints/myfile/20250318T140442Z/</h1>
<hr><pre><a href="../">../</a>
<a href="1.iso">1.iso</a>                                                                                               18-Mar-2025 14:04  1.0 kB
<a href="2.iso">2.iso</a>                                                                                               18-Mar-2025 14:04  1.0 kB
<a href="3.iso">3.iso</a>                                                                                               18-Mar-2025 14:04  1.0 kB
<a href="PULP_MANIFEST">PULP_MANIFEST</a>                                                                                       18-Mar-2025 14:04  228 Bytes
</pre><hr></body>
</html>
```

### Testing the Redirect

Finally, test the redirect by attempting to access a timestamp for which no checkpoint exists. The system will automatically redirect you to the nearest checkpoint created at or before the specified timestamp in the URL.

```shell
$ http ${CONTENT_ADDR}/pulp/content/checkpoints/myfile/20250318T140340Z/

HTTP/1.1 301 Moved Permanently
Content-Length: 22
Content-Type: text/plain; charset=utf-8
Date: Tue, 18 Mar 2025 14:09:19 GMT
Location: /pulp/content/checkpoints/myfile/20250318T140338Z/
Server: Python/3.10 aiohttp/3.8.1
301: Moved Permanently
```

## Moving Towards SDP

The introduction of the Checkpoint feature is a significant step towards achieving Safe Deployment
Practices (SDP).
By ensuring that deployments are predictable and consistent, we can reduce the risk of errors and
improve the overall quality of our software.

We are excited about the possibilities that the Checkpoint feature brings and look forward to seeing
how it helps you in your projects.

Happy coding!
