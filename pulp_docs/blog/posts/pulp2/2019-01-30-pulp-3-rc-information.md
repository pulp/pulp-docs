---
date: 2019-01-30T20:55:50+00:00
title: Pulp 3.0 RC Information
author: David Davis
tags:
  - "3.0"
---
<!-- more -->
Pulp 3.0 is currently in beta and will soon become a release candidate (RC) when the remaining must-have items are completed. We wanted to give an update on the RC and what it'll mean for users, plugin writers, and other stakeholders.

The list of open items for the RC can be viewed with [the RC blocker query](https://pulp.plan.io/issues?query_id=121). People interested in the status of the RC can check this query to get an idea of how the RC's progress.


### How long will Pulp be in an RC period before going GA?

The RC period will likely last for several months, but not longer than 1 year, while users and plugin writers identify any major problems.


### Why is the RC period so long?

Once the GA occurs, the REST API is semantically versioned. We need to be confident that the REST API design is serving the right use cases and creating the right value for Pulp users.

We also want to discover any issues with the plugin API. This is likely where most of the issues will be discovered since plugins identify new needs regularly, but this is also at version, so we can still make backwards incompatible changes post GA for this software component. A longer "baking" period should reduce the amount of backwards incompatible changes made post GA.


### When will the GA be released?

The GA release depends on us receiving community feedback from Katello, Ansible Galaxy,  and Pulp plugin writers. We hope enough plugins written by the community will provide us with valuable feedback during our RC period.


### What if major/breaking changes are made to pulpcore or the plugin API during the RC?

New changes that are breaking/backwards incompatible would be released as an RC with changes documented in release notes.


### How many RC releases will there be?

Hopefully only a few. We plan to release no more often than once a month


### Will new features be added to pulp/pulp and pulpcore-plugin during this time?

No. We want the release candidate asset to be very unsurprising from the start of the RC to the GA. Generally a new feature should only be added if releasing without it would be "very bad". One example would be a feature required by a plugin to perform basic sync or publish. Another example would be a change that is required by Katello, Ansible Galaxy, or Pulp plugin writers.


### Will bugfixes be added to pulp/pulp and pulpcore-plugin during this time?

Yes. Including bugfixes during the RC will benefit GA users.


### Will refactors be added to pulp/pulp and pulpcore-plugin during this time?

Stability is the goal of the RC and so we are trying to avoid refactoring  except in cases we deem essential.


### Will new features for 3.1 be started?

No. There are a lot of additional things that are being launched "around" Pulp3 like the installer, upgrade and migration tooling, container build+delivery, etc that 3.1 features should not be the focus.

A lot of the focus during the RC period will be on plugin development and ensuring that core is stable and meets the needs of the Pulp 3 plugin ecosystem.
