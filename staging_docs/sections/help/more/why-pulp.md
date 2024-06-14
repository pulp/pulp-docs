# Why Pulp?

<figure markdown="span">
  <iframe width="560" height="315" src="https://www.youtube.com/embed/grDXPtnJu4U?si=TPCsysh3GmGAKByY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
  <figcaption>If you have to manage hundreds or thousands of packages, Pulp can help!</figcaption>
</figure>


## Selling Points

### Ensure stability and continuity

External content sources can go offline unexpectedly.
If you want to ensure that you always have what you need, Pulp can help.

### Stop using rsync

Pulp is designed with complex content management workflows and disk optimization in mind.
If your sync script is letting you down, Pulp can help.

### Reduce rate limiting

From one day to the next, third-party platforms can introduce rate limiting and change the conditions of service.
If you want to reduce operation costs by having your team consume content from Pulp rather than third parties, Pulp can help.

### Distribute content privately

Sometimes you need a way to distribute private content you have developed in house.
If you want to keep your private packages off third-party platforms and distribute them internally with ease, Pulp can help.

### Experiment without risk

Every change to content hosted in Pulp creates a new repository version.
You can rollback to earlier versions whenever you need to.
If you need to pin packages to certain versions to ensure stability and repeatability, Pulp can help.

### High Availability

Pulp's architecture is designed for both scalability and high availability, offering you the flexibility to scale according to your needs.
You can boost the capabilities of API request handling, binary/package data serving and tasks processing (e.g, syncing and publishing).

### One tool for different content types

With Pulp, you can fetch, upload, and distribute content from a wide variety of content types.
Add the plugins for the different content you want to work with and use Pulp to manage them all.

### Safely roll back with repository versioning

Every time you add or remove content, Pulp creates an immutable repository version so that you can roll back to earlier versions and thereby guarantee the safety and stability of your operation.

### Optimizing disk storage and speed during remote synchronization

Download and store only what you need from remote repositories.
You can select from three modes to optimize disk speed and storage when synchronizing.
While the default download option downloads all content, you can enable either the on_demand or streamed option.
The on_demand option saves disk space by downloading and saving only the content that clients request.
With the streamed option, you download also on client request without saving the content in Pulp.
This is ideal for synchronizing content, for example, from a nightly repository and saves having to perform a disk clean up at a later stage.

### Multiple storage options

As well as local file storage, Pulp supports a range of cloud storage options, such as Amazon S3 and Azure, to ensure that you can scale to meet the demands of your deployment.

