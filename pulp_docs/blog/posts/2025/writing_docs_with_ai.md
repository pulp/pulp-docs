---
date: 2025-05-22T00:00:00Z
title: Writing Docs with AI - An Experiment in Workflow
authors: 
  - bmbouter
tags:
  - documentation
  - AI
  - workflow
  - NotebookLM
---

Writing documentation can often be a significant effort. Recently, I needed to document a new feature, the "Alternate Content Source". But where to start? The core information existed in a user conversation on Matrix. How could I turn that scattered information into structured, usable documentation efficiently? I decided to experiment with an AI tool, specifically NotebookLM, to see if it could streamline the process.

The starting point was straightforward. I took the raw Matrix conversation and uploaded it as a source into NotebookLM. I also added the existing pulpproject.org website as another source, hoping it would provide context and stylistic examples (Note: this specific detail about adding the pulpproject.org site comes from my process description, not the provided source text). My initial prompt was simple: "write me markdown docs from this user conversation". It produced the content for [this pull requested](https://github.com/pulp/pulpcore/pull/6610).

<!-- more -->

### Experimenting with Conversation Styles

NotebookLM offers different "conversation styles" which seem to influence the tone and structure of the output. I tried two main styles for this task to see which was best suited for generating technical documentation:

*   **Default Style:** This was my first attempt. The output was mostly usable markdown documentation. It extracted the key points from the conversation and presented them in a relatively coherent structure, suitable for integration into our existing documentation.

*   **Guide Style:** Hoping for a more pedagogical approach, I switched to the "Guide" style. However, this proved less suitable for generating technical documentation. The output adopted a first-person narrative, often reading like an author explaining the topic directly to the reader. It also included numerous links, often to general concepts or external resources, which were unnecessary and cluttered the output for the specific task of writing concise project documentation. It became clear that the "Guide" style is **not ideal for generating straightforward reference or how-to documentation**.

### The Iterative Rewriting Challenge and Solution

My initial thought for refinement was to use NotebookLM's conversational interface for iterative feedback. The first draft wasn't perfect, so I tried telling NotebookLM what needed changing and asking it to rewrite parts while retaining the markdown formatting.

This approach **did not work well**. Any subsequent generations after the first often failed to retain the markdown formatting, even when explicitly requested to do so in my feedback. The output would revert to plain text or inconsistent formatting, making it unusable without significant manual cleanup.

A much more effective method emerged: **Clear the chat history**. Instead of having a back-and-forth conversation, I found it worked best to clear the existing chat with NotebookLM, keep the uploaded sources, and then refine my *original* prompt by appending my feedback to it. For instance, I might change the prompt from "write me markdown docs..." to "write me markdown docs... focusing on X and excluding Y, ensure Z is covered...". Keeping the revised prompt as a single, comprehensive instruction and re-prompting from a clean slate consistently produced markdown-formatted output based on the updated requirements.

### Results and Necessary Refinements

Using the "clear history and re-prompt" strategy with the "Default" conversation style, I was able to generate very usable documentation drafts quickly. The output required some hand-editing, primarily to remove links that seemed specific to the NotebookLM environment and didn't make sense in the final documentation, and a few minor content rewrites for clarity or flow. Any content issues were entirely due to a lack of content from the original user discussion on Matrix.

It generated the content for [this pull request](https://github.com/pulp/pulpcore/pull/6610).

Overall, the process was **significantly quicker and yielded higher quality initial drafts** compared to starting from scratch with direct authorship. It allowed me to rapidly structure the information from the Matrix conversation and get a solid base document ready for final polish and integration.

### Acknowledging the AI Assistant

In the spirit of exploring AI-assisted workflows, it feels appropriate to reveal something about *this* blog post itself.

This blog post you've just read was also drafted with the help of NotebookLM. I provided it with my notes on the documentation writing process and used an existing blog post from the Pulp project, like the one detailing the "Whenever, Whatever-based Release Cycle", as a formatting example source. The aim was to see if it could follow a specific markdown structure and incorporate the described content points accurately.

The process mirrored the successful method used for the documentation: clear history, provide the notes and the formatting example source, and use a single, clear prompt. The result is what you see before you, demonstrating another application of AI in streamlining content creation, from technical docs to blog posts explaining the process.
