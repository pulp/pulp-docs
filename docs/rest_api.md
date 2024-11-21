---
render_macros: true
---

# Rest API

The REST API reference for Pulp Plugins is generated using [ReDoc](https://redocly.com/redoc/) and are published in standalone pages:

<div class="grid cards" markdown>

{% for repo in get_repos() %}
- <a href="https://docs.pulpproject.org/{{ repo.name }}/restapi.html" target="_blank">{{ repo.title }}</a>
{% endfor %}

</div>
