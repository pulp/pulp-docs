---
date: 2025-07-08T00:00:00Z
title: Syncing Files from a Webserver or an S3 Bucket
authors:
  - "dkliban"
tags:
  - repositories
  - files
  - S3
  - bucket
---
# Syncing Files from a Webserver or an S3 Bucket

The [pulp-manifest tool] is designed to generate `PULP_MANIFEST` files for the [Pulp File plugin].
`pulp-manifest` has been recently significantly enhanced with support for S3 buckets. 
This feature allows users to generate a `PULP_MANIFEST` directly from content in an S3 bucket.
It's exciting to note that this valuable addition was a community contribution from [ozanunsal].
This post is about the `pulp-manifest` tool.
[Sync] and [Publish] workflows for File repositories are documented separately.

<!-- more -->

## How the S3 Support Works

To generate a PULP_MANIFEST for an S3 bucket, you simply use the command with an S3 path: 

```bash
pulp-manifest s3://bucket-name/path/to/prefix/
```

When generating the manifest for S3 content, the tool computes a SHA256 digest by downloading the file content.
Users can exclude specific files or directories that match a glob pattern by using the `--exclude` option. 

```bash
pulp-manifest s3://bucket-name/path --exclude '*.log'
```

[pulp-manifest tool]: https://github.com/pulp/pulp-manifest
[Pulp File plugin]: https://pulpproject.org/pulp_file/
[ozanunsal]: https://github.com/ozanunsal
[Sync]: site:pulp_file/docs/user/guides/sync/
[Publish]: site:pulp_file/docs/user/guides/publish-host/
