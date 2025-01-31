---
date: 2024-11-11T08:55:50+00:00
title: Pulp UI Beta out now in Pulp images
author: Gerrod Ubben
tags:
  - announcement
---

Pulp-UI (beta) is now available in the latest `pulp/pulp` image. This was a huge effort over the 
last two months to get the beta into the hands of our users. Big thanks to Martin Hradil, Zita 
Nemeckova and everyone who helped us get here. Check out the demo below:
<!-- more -->
### Demo

<iframe width="560" height="315" src="https://www.youtube.com/embed/RwNA4EiR-rs?si=-hTHys2RCuEjuuEY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

### Test it out

[Follow the quickstart guide](site:pulp-oci-images/docs/admin/tutorials/quickstart/) with the 
`latest` tag and visit the `/ui/` endpoint in a browser to check it out. If you wish to disable 
the UI then set the env `PULP_UI=false` when starting the container.

### Want to help out?

Come join us in developing the new UI at [https://github.com/pulp/pulp-ui/](https://github.com/pulp/pulp-ui/).
We appreciate any feedback and help.
