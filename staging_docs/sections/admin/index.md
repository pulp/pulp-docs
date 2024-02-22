---
hide:
  - toc
---
<div class="hero-header" markdown>
<h1 class="landing-page-h1"></h1>

## This section is for **admins**

Common needs are to *configure, deploy and maintain Pulp instances*.



<div class="grid cards" markdown>

- **Build and deploy**

    ---

    Start developing your service or application by levaraging our powerfull deployment setups.
    
- **Engage**

    ---

    Get and provide feedback from the peers to help our Project and your Product to grow.

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

