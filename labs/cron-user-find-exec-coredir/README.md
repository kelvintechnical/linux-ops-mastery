# Lab: User-Level Cron Job with `find -exec`

**Series:** linux-ops-mastery — RHCSA Scheduled Tasks
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

As a non-root user (`user70`), schedule a personal cron job that runs every Monday at 01:20 to find every file named `core` under `/var` and copy it into `/var/tmp/coredir1`. The job must be installed via `crontab -e` (not via `/etc/cron.d/`), and survive logout/reboot.

### Steps to be covered

1. Create `user70` if it does not exist; ensure they have a usable shell.
2. As root, ensure `/var/tmp/coredir1` exists with permissions that let `user70` write to it (e.g. `chmod 1777` or `chown user70:user70`).
3. Switch to `user70` (`su - user70`) and run `crontab -e`.
4. Add a single line:
   ```
   20 1 * * 1 find /var -name core -exec cp {} /var/tmp/coredir1 \;
   ```
   - Fields: `minute=20`, `hour=1`, `day-of-month=*`, `month=*`, `day-of-week=1` (Monday)
5. Verify the entry with `crontab -l` (still as `user70`).
6. Confirm the per-user crontab file lives at `/var/spool/cron/user70` (only root can read it, but its existence is the proof).
7. Test the command body interactively first: `find /var -name core -exec cp {} /var/tmp/coredir1 \;` — never trust a cron job you haven't smoke-tested.

### Cron-field cheat sheet

```
*    *    *    *    *
│    │    │    │    │
│    │    │    │    └─ day of week (0-6, 0=Sun, or Mon/Tue/...)
│    │    │    └────── month (1-12)
│    │    └─────────── day of month (1-31)
│    └──────────────── hour (0-23)
└───────────────────── minute (0-59)
```

### Career-arc connection

- **RHCSA** — user-level cron + `find -exec` together is a recurring two-objective combo.
- **SRE / Platform** — every retention/cleanup script in production is a `find -mtime ... -exec` cron job at heart.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
