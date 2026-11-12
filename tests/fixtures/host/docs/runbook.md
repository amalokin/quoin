# Runbook

How to operate svc in production. To work on the code, start from the [README](../README.md).

svc runs as the `svc` systemd unit on the application hosts. The maintainers named in `CODEOWNERS` are on call for it.

## Start

```
sudo systemctl start svc
```

Then run the health check.

## Stop

```
sudo systemctl stop svc
```

## Health check

```
curl -fsS https://svc.example.org/health
```

A healthy svc answers `200` with `{"ok": true}`. Any other answer, or none, is a failed check: read the unit's recent
log with `sudo journalctl -u svc -n 100`, restart the unit (stop, then start) and check again. If it still fails, roll
back.

## Rollback

1. Find the previous release tag with `git tag --sort=-creatordate`: the newest is the failed release, and the one
   below it is the release to restore.
2. Deploy that tag with the platform team's deploy job.
3. Run the health check again.
4. Open a ticket, `SVC-<n>`, describing the failed release.
