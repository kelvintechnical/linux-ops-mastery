# Lab: Online Extend an LV and Its Filesystem Without Unmounting

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Grow an existing logical volume by 64 MiB and grow its XFS filesystem to fill the new space — all while the filesystem remains mounted and in active use.

### Steps to be covered

1. Start from a mounted XFS-formatted LV (e.g. the one built in [`lvm-create-lv1-xfs`](../lvm-create-lv1-xfs/)).
2. Run `lvs` and `df -h` to capture the **before** state — both the LV size and the mounted-filesystem size.
3. Extend the LV with `lvextend -L +64M /dev/<vg>/<lv>` (no `--resizefs`, so the FS does not auto-grow yet).
4. Grow the XFS filesystem online with `xfs_growfs /mount/point`. Note: XFS only grows, never shrinks.
5. Re-run `lvs` and `df -h` to capture the **after** state and confirm the new size is visible to userland.
6. Verify the filesystem stayed mounted the entire time and no I/O errors appear in `dmesg` or `journalctl -k`.

### Career-arc connection

- **RHCSA** — "extend an existing LV and its filesystem" is a recurring storage objective.
- **SRE / Platform** — growing `/var/log` or `/var/lib/docker` under load without downtime is the daily-driver use case.
- **DevOps** — same pattern applied to container storage drivers and CI cache volumes.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
