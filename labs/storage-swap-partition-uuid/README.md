# Lab: Create a Swap Partition by UUID

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Create a small swap partition, capture its UUID, add a persistent `/etc/fstab` entry that references it by UUID (not device path), activate the swap, and verify it survives a reboot.

### Steps to be covered

1. Use `lsblk` and `fdisk -l` to identify an available block device or partition slot.
2. Create a new partition (or use a free loop device for safe practice) and run `mkswap /dev/<part>`.
3. Capture the swap UUID with `blkid /dev/<part>` — copy the `UUID=...` value exactly.
4. Append a single line to `/etc/fstab`:
   ```
   UUID=<value>   swap   swap   defaults   0 0
   ```
5. Run `systemctl daemon-reload`, then `swapon -a` to activate without rebooting.
6. Verify with `swapon --show` and `free -h` — the new swap should appear under `/dev/<part>`.
7. Reboot once to prove persistence; re-verify with `swapon --show`.

### Career-arc connection

- **RHCSA** — UUID-based fstab entries are the canonical safe way to mount any block device. Memorize the four-field swap line shape.
- **SRE / Platform** — swap sizing decisions matter on memory-constrained hosts and Kubernetes nodes (where swap is often deliberately disabled).

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
