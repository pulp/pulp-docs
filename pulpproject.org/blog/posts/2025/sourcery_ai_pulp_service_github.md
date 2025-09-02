---
date: 2025-06-18T00:00:00Z
title: My Experience with `sourcery-ai` in Pulp-Service Development
authors:
  - "dkliban"
tags:
  - development
  - AI
---
# My Experience with [`sourcery-ai`](https://sourcery.ai/) in Pulp-Service Development

As a developer contributing to the `pulp-service` GitHub repository, I can confidently say that integrating the `sourcery-ai` bot has significantly reshaped my workflow and, by extension, our team's productivity. The bot has become an integral part of our pull request process, offering automated, structured, and actionable feedback that helps us deliver higher quality code more efficiently.

Here's how `sourcery-ai` has impacted my productivity:

<!-- more -->

### Automated Code Reviews and Structured Feedback

`sourcery-ai` provides an initial layer of code review for every pull request I open, offering a concise "Summary by Sourcery" and a detailed "Reviewer's Guide". This has been a game-changer, as it significantly reduces the initial workload for human reviewers, allowing us to focus on more complex logic and architectural decisions rather than basic code quality checks. The bot categorizes its findings into "General issues," "Security," "Testing," and "Documentation". Often, it reports that security, testing, and documentation aspects "all looks good," which provides quick assurance in these areas.

### Early Identification of Bugs and Code Quality Improvements

`sourcery-ai` actively identifies potential bugs and offers suggestions for improving code quality and adhering to best practices. For instance, it pinpointed a "bug risk" where `settings.TEST_TASK_INGESTION` was not defined and recommended using timezone-aware timestamps with `django.utils.timezone.now()` instead of `datetime.now()` in [Pull Request #523](https://github.com/pulp/pulp-service/pull/523). It also detected an issue where a task was "not registered or implemented" in the same [Pull Request #523](https://github.com/pulp/pulp-service/pull/523). Beyond bugs, the bot suggests improvements such as removing unused parameters from method signatures (also in [Pull Request #523](https://github.com/pulp/pulp-service/pull/523)), including exception details in logs for better debugging in [Pull Request #527](https://github.com/pulp/pulp-service/pull/527), and simplifying redundant `save()` calls after ManyToManyField additions in [Pull Request #530](https://github.com/pulp/pulp-service/pull/530). By catching these issues early in my development cycle, the bot helps prevent time-consuming debugging sessions later and encourages a higher standard of code quality.

### Enhanced Understanding with Visual Aids

A unique feature of `sourcery-ai` is its ability to generate visual diagrams, including Sequence Diagrams, Class Diagrams, Entity-Relationship (ER) Diagrams, and Flow Diagrams. These diagrams provide a clear, high-level overview of my proposed changes, their impact on the system's architecture, and the flow of logic. This visual representation can significantly reduce the time I spend trying to understand complex code modifications, thereby accelerating the review and integration process.

### Streamlining Workflow and Developer Adoption

The bot offers a suite of commands that enable me to interact with it directly and automate various review-related tasks. I can trigger new reviews, continue discussions, generate GitHub issues from review comments, create pull request titles or summaries, and generate reviewer guides. This automation contributes to a more efficient and less manual pull request workflow.

My frequent interactions and reactions to `sourcery-ai`'s comments, such as giving "thumbs up" or providing clarifications, demonstrate its successful integration and my perceived value from its feedback. For instance, when it pointed out a potentially missing data migration for the `DomainOrg` model in [Pull Request #540](https://github.com/pulp/pulp-service/pull/540), I was able to clarify that this was already handled by a previous migration in [Pull Request #530](https://github.com/pulp/pulp-service/pull/530). Similarly, when it highlighted a potential bug risk regarding `TEST_TASK_INGESTION` not being defined in [Pull Request #523](https://github.com/pulp/pulp-service/pull/523), `decko` and I reacted with a thumbs-down, indicating we had context or a different approach.

### Limitations of `sourcery-ai` Bot

While `sourcery-ai` offers significant benefits, I've also observed some limitations, particularly concerning its awareness of our project's custom implementations:

*   **Lack of Awareness of Custom File Handling (`PulpTemporaryUploadedFile`)**
    During a pull request where I added a synchronous RPM create API in [Pull Request #550](https://github.com/pulp/pulp-service/pull/550), `sourcery-ai` suggested that reading RPM metadata from `uploaded_file.file.name` might not work for `InMemoryUploadedFile`. It recommended writing to a temporary file or using a file-like object API instead. However, I clarified in [Pull Request #550](https://github.com/pulp/pulp-service/pull/550) that our project uses `PulpTemporaryUploadedFile` instead of `InMemoryUploadedFile`, and that even small files are available on disk due to this custom implementation. This interaction highlighted a limitation where the bot's analysis, while generally helpful, might not be fully aware of bespoke architectural choices or custom classes within our specific codebase. This means its suggestions, while technically sound in a generic context, sometimes aren't applicable to our unique setup, still requiring me to apply my contextual knowledge to its feedback.

In conclusion, the `sourcery-ai` bot has become an invaluable tool for the `pulp-service` repository. By automating aspects of code review, providing intelligent and actionable feedback, visually explaining changes, and streamlining review workflows, it has undoubtedly enhanced my productivity and that of my colleagues, allowing us to deliver higher quality code more efficiently. However, its effectiveness can sometimes be tempered by a lack of awareness of highly specific or custom implementations within our project, reminding me that human oversight and domain-specific knowledge remain crucial.
