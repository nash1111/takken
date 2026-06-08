# Cloudflare Pages deploy via GitHub Actions

This static site deploys to the existing Cloudflare Pages project `takken-sokuto-lab`.

## Required repository secrets

Add these secrets in GitHub repository settings:

- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account id for the Pages project.
- `CLOUDFLARE_API_TOKEN`: Cloudflare API token with permission to deploy Pages.

Recommended token permissions:

- Account → Cloudflare Pages → Edit
- Account → Account Settings → Read

The workflow validates all checked-in HTML files and `sitemap.xml` on pull requests. Production deploy runs only after a push to `main`.
