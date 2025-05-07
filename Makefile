docs:
	pulp-docs fetch --dest /tmp/pulpdocs-tmp
	pulp-docs build --path pulp-docs@..:/tmp/pulpdocs-tmp

.PHONY: docs
