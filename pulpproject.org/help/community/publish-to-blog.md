# Publish to our blog

This guide will walk you through the process of contributing a blog post to the Pulp Project blog.

## Prerequisites

- A GitHub account
- Basic knowledge of Markdown
- Something you wanna share with the Pulp Project community!

## Overview

Blog posts for the Pulp Project are published through pull requests to the [pulp-docs repository](https://github.com/pulp/pulp-docs). All blog posts are written in Markdown and include metadata that helps organize and display the content properly.

## Step-by-step process

### 1. Create a branch on your fork

1. Fork the [pulp-docs repository](https://github.com/pulp/pulp-docs) on GitHub
2. Clone your fork to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pulp-docs.git
   cd pulp-docs
   ```
3. Create a branch to work on your post

### 2. Create your blog post file

Blog posts are organized by year.
Create your Markdown file in the appropriate year directory.
If your post requires images put them side-by-side with the post file:

```
pulpproject.org/blog/posts/YYYY/your-post-title.md
pulpproject.org/blog/posts/YYYY/my-image.png
pulpproject.org/blog/posts/YYYY/my-graph.svg
```

### 3. Add metadata

Every blog post must start with YAML front matter that includes the following required and optional fields:

```yaml
---
# requires
date: YYYY-MM-DD
title: Your Blog Post Title
authors:
  - author-name

# optional
tags:
  - tag1
  - tag2
links:
  - "[discourse] LTS strategy": "https://discourse.pulpproject.org/t/need-to-reduce-the-number-of-release-branches-aka-we-need-an-lts-strategy/449"
  - "[discourse] CalVer": "https://discourse.pulpproject.org/t/switching-pulpcore-to-calendar-versioning-scheme/771"
---
```

About the metadata:

- **date**: The publication date and time
- **title**: The title of your blog post as it will appear on the blog
- **author**: Your author name as it shows in the *authors file* (see below)
- **tags**: A list of relevant tags to help categorize your post
- **links**: These are references you wanna share. These receive a special rendering.

!!! tip "Add yourself as an author"

      Add an author entry to `pulpproject.org/blog/.authors.yml` by using others entries as a template.

      Use that in the `authors` fields.

### 4. Write your content

After the front matter, add your blog post content using standard Markdown.

**Important**: Include the `<!-- more -->` comment after your opening paragraph or introduction. This creates a "read more" break on the blog index page:

```markdown
---
date: 2025-12-05
title: Getting Started with Pulp Container Registry
authors:
  - jane-developer
tags:
  - tutorial
  - container
---

Learn how to set up and use Pulp as a container registry for your organization's Docker images.

<!-- more -->

## Introduction

In this tutorial, we'll walk through...
```

### 5. Preview and submit

Before submitting it's recommended that you preview your blog post locally.
A quick way to do it is run `pulp-docs` in the pulp-docs repository:

```bash
uv run pulp-docs serve --draft
```

When everything looks good, submit your PR and we'll review it!

!!! note "Issues with preview"

      If you have problems with the preview, submit an issue [here](https://github.com/pulp/pulp-docs/issues/).

## Content guidelines

### Writing tips

- You may use AI, but use it wisely. See our [AI Policy](site:help/more/governance/ai_policy/)
- Link to relevant documentation and resources
- Run an appropriate tool to check for typos

