---
date: 2025-06-04T00:00:00Z
title: "Using Pulp at Microsoft: Coming Full Circle"
author: David Davis
tags:
  - community
---

Hi, I’m David. If you've been using Pulp for long enough, there's a good chance you may have
encountered a bug I contributed. I worked on Pulp for many years while at Red Hat, from the
beginning of the Pulp 3 back when it was just a proof of concept. Those early days were full of
whiteboarding and discussions around which technologies to use (e.g. futures or asyncio?), whether
to create a CLI or Web UI, and how to integrate Pulp 3 with products like Satellite and Ansible
Galaxy.

Fast-forward to today, I now work at Microsoft on the Azure Core Linux team. And in a really
interesting bit of serendipity, we've spent the past few years using Pulp to overhaul
[packages.microsoft.com](https://packages.microsoft.com), Microsoft's service for Linux package
repositories. I've gone from developing Pulp full-time to running it as a user.

<!-- more -->

It's been a wild and rewarding ride. Our project — a critical part of Microsoft's support for Linux
— distributes packages for Microsoft's Linux distro (Azure Linux), VS Code, Edge, and more.
When we started overhauling the old infrastructure, we knew we wanted something flexible,
extensible, and built with modern architecture in mind, and Pulp fit the bill perfectly.

Using Pulp we were able to leverage several cloud-based Azure services such as Azure Kubernetes
Service (AKS) for orchestrating containers, Azure Blob Storage to store artifacts, and Azure Front
Door to handle global content delivery. This gave us a highly scalable and reliable platform to
serve Linux packages to Microsoft customers around the globe.

We even got to contribute back to Pulp along the way — adding features like checkpoint support and
[apt-by-hash](https://wiki.ubuntu.com/AptByHash) in pulp_deb. If you're interested to learn more
about how we use Pulp at Microsoft, today we've published a blog post detailing our use of Pulp:

["How Pulp powers Microsoft's Linux Software
Repositories"](https://techcommunity.microsoft.com/blog/linuxandopensourceblog/how-pulp-powers-microsofts-linux-software-repositories/4420257)
by Colin Mixon.

Huge thanks to the Pulp project for making this possible. I believe Pulp’s greatest strength is its
passionate, dedicated community, and it’s been a real pleasure to collaborate with everyone.
Watching the project grow and thrive has been incredible — and using it in a whole new context has
been even more rewarding.
