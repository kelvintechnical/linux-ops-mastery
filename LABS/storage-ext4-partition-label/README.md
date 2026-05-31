# Lab: Create an Ext4 Partition Mounted by LABEL

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Status:** 📅 Planned — full walkthrough coming soon. The task definition below is exam-accurate; lab content (concept sections, task breakdowns, expected output, troubleshoot tables) has not yet been written.

---

## Task

Format a new partition as ext4 with an explicit filesystem label, add a persistent `/etc/fstab` entry that references the partition by `LABEL=` (not UUID, not device path), and mount it at `/mnt/stdfs1`.

### Steps to be covered

1. Identify a free partition with `lsblk` / `fdisk -l`, or carve one out with `fdisk` / `parted`.
2. Format with an explicit label using `mkfs.ext4 -L stdlabel /dev/<part>`.
3. Verify the label with `blkid /dev/<part>` — look for `LABEL="stdlabel"`.
4. Create the mount point: `mkdir -p /mnt/stdfs1`.
5. Append an `/etc/fstab` line using the `LABEL=` form:
   ```
   LABEL=stdlabel   /mnt/stdfs1   ext4   defaults   0 2
   ```
6. Run `systemctl daemon-reload`, then `mount -a` to mount everything in fstab.
7. Verify with `findmnt /mnt/stdfs1` and `df -hT /mnt/stdfs1`.
8. Reboot once to prove persistence.

### When to choose LABEL vs UUID

| Reference | When to use |
|---|---|
| `UUID=` | Default — globally unique, survives reformatting only if you preserve the UUID |
| `LABEL=` | Human-readable, easier to recognize; **fails if two filesystems share the same label** on the same host |
| `/dev/sdX1` | Avoid — device names can change across reboots |

### Career-arc connection

- **RHCSA** — both LABEL and UUID forms appear in exam variants; knowing the trade-off between them is the point of this lab.
- **SRE** — labels are useful when cloning disk images, because the UUID changes per clone but the label can be kept stable.

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
