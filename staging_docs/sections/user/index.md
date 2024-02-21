---
hide:
  - toc
---
<div class="hero-header" markdown>
# Overview

## This section is for users who need to need create sync, publish and interact with repositories.



<div class="grid cards" markdown>

-   **Get Started**

    ---
    
    Complete the started tutorial [here](#).

    
-   **Understand the docs**
    
    ---

    Get familiar withhow to use this documentation works. [here](#)

- **Explore**

    ---

    Some content

- **Engage**

    ---

    Some content

</div>
</div>

---

## Quick Links


{% for repo_type in ("core", "content") %}
Repo | Version | Rest API | Github Page | Changelog
--- | --- | --- | --- | --- 
{% for repo in get_repos(repo_type) -%}
{{ repo.title }} | `{{ repo.version }}` | <a href="{{ repo.rest_api_url}}" target="_blank">:link:</a> | [:link:]({{ repo.codebase_url }}) | [:link:]({{ repo.changelog_url }})
{% endfor %}
{% endfor %}

Repo | Version | Code (Github) | Changelog
--- | --- | --- | --- 
{% for repo in get_repos("other") -%}
{{ repo.title }} | `{{ repo.version }}` | [:link:]({{ repo.codebase_url }}) | [:link:]({{ repo.changelog_url }})
{% endfor %}

