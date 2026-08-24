# Security policy

Never commit Wi-Fi credentials, SSH keys, Cloudflare tokens, PocketBase superuser credentials, or device secrets. Store device-only configuration outside the repository under `/etc/ai-trash-sorter/` and use `.env.example` files only for redacted variable names.

Do not expose SSH or PocketBase's superuser surface through the Cloudflare Tunnel. Report suspected credential exposure by rotating the affected secret before sharing diagnostic output.
