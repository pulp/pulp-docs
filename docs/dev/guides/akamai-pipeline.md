# Akamai CDN Pipeline

The packages.redhat.com CDN configuration is managed through an Akamai property pipeline.
The pipeline repo contains templates, environment configs, and deployment tooling.

## Repository

- **GitLab:** [hosted-pulp/akamai-packages.redhat.com](https://gitlab.cee.redhat.com/hosted-pulp/akamai-packages.redhat.com)

See the repository's README for complete setup instructions (CLI install, credentials) and the
deployment workflow (save, promote, test).

## Quick reference

| Environment | Akamai property | URL |
|-------------|-----------------|-----|
| Stage       | `stage.packages.redhat.com` | <https://packages.stage.redhat.com> |
| Prod        | `prod.packages.redhat.com` | <https://packages.redhat.com> |

## Related resources

- [IT Akamai Pipeline docs](https://it-akamai.pages.redhat.com/docs/user/delivery/pipeline) — upstream pipeline documentation
- [Console Promotion document](https://docs.google.com/document/d/1NDG8MH4PNGF8h87FjTItkndLLpODNUWQxpLpTjlAVD4/edit) — promotion runbook (originally for console.redhat.com, applicable to packages.redhat.com)
