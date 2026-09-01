# Security policy

Never commit Wi-Fi credentials, SSH keys, Firebase service-account credentials, or device secrets. Store device-only configuration outside the repository under /etc/ai-trash-sorter/ and use redacted examples only.

Do not expose SSH or Firebase service-account credentials. Report suspected credential exposure by rotating the affected secret before sharing diagnostic output.
