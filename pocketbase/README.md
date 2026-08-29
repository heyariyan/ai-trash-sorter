# PocketBase schema

The live PocketBase data directory must never be committed. This folder only
stores schema definitions and notes used to provision a local Pi instance.

The fast local runner writes to local JSONL first, then optionally posts to:

- `sorting_events`
- `feedback`
- `settings`

If PocketBase is down or rejects a write, sorting continues and the failed
remote record is buffered under `/var/lib/ai-trash-sorter/runtime/`.
