# Lab: Format a Partition with XFS — `mkfs.xfs`, `mount`, `UUID`, `/etc/fstab`, `xfs_info`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** XFS as RHEL 9's default filesystem, `mkfs.xfs` (formatting, default options, `-f` force, `-L LABEL`, `-b size=`, `-s size=`, `-i size=`, `-d agcount=`, `-m crc=1` CRC, `-m reflink=1`, `-m bigtime=1`), `blkid` for UUID/LABEL, `mkdir /mnt/...` mount point conventions, `mount -t xfs UUID=... /mnt/data`, `mount -o defaults,noatime`, `xfs_info /MNT` post-format inspection, `/etc/fstab` line construction (UUID vs LABEL vs device path), `mount -a` validation, `findmnt /mnt/data` and `df -hT` verification, `xfs_admin -L` to relabel, `xfs_admin -U` to change UUID, `xfs_repair` placeholder (covered in Lab 118)
- **Career arcs covered:** RHCSA (EX200 — "create an XFS filesystem on /dev/vdb1 and mount persistently"), RHCE (Ansible `community.general.filesystem` + `ansible.posix.mount`), SRE (database volume formatting), DevOps (cloud-init disk_setup → fs_setup), AI / MLOps (NVMe scratch XFS)
- **Prerequisite:** Labs 110–115 (inspect + partitioning)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 sandbox + partition · Task 3 `mkfs.xfs` default · Task 4 `-L LABEL` · Task 5 `blkid` UUID · Task 6 mount by UUID · Task 7 `xfs_info` · Task 8 fstab + `mount -a` · Task 9 verify with `findmnt` and `df -hT` · Task 10 capstone fstab entry + cleanup

---

## Objective

Format a partition with XFS, give it a label, mount it by UUID, and make the mount persistent across reboots via `/etc/fstab` — the exact workflow RHCSA examines.

The capstone is: *"Format `/dev/loop9p1` as XFS labeled `RHCSA_XFS`, add a persistent fstab entry mounted by UUID at `/mnt/rhcsa-xfs` with `defaults,noatime`, then `mount -a` and verify with `findmnt`."*

> **Lab safety note:** Uses loopback files in `/var/tmp/` — safe on any RHEL 9 VM. Never run `mkfs.xfs` against a partition that already has data unless you intend to destroy it.

---

## Concept: XFS Is RHEL's Default

XFS has been RHEL's default since RHEL 7 (2014). It's chosen for:
- Excellent performance under parallel I/O (allocation groups = lockless parallelism)
- Online filesystem growth (`xfs_growfs`)
- Native CRC metadata since v5 superblock
- No fsck required in normal operation (XFS replays its log on mount)

```
   ┌─────────────────────────────────────────────────────────────┐
   │ mkfs.xfs DEV                                                 │
   │   ├── superblock × N (one per allocation group)              │
   │   ├── allocation groups (default = 4 for small disks)        │
   │   ├── log (internal by default, sized automatically)         │
   │   ├── v5 features: crc=1 finobt=1 reflink=1 bigtime=1        │
   │   └── UUID generated automatically                            │
   │                                                              │
   │ blkid DEV  →  UUID="..."  LABEL="..."  TYPE="xfs"            │
   │                                                              │
   │ mount UUID=... /mnt/X    or    mount LABEL=... /mnt/X        │
   │                                                              │
   │ /etc/fstab line:                                              │
   │   UUID=...  /mnt/X  xfs  defaults,noatime  0 0               │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** RHCSA tasks almost always say "mount persistently" — that is fstab. And fstab entries should always use UUID or LABEL, never the device path (which can change across reboots).

---

## 📜 Why XFS — The Story

XFS was created by **SGI in 1993** for IRIX, optimized for very large files and parallel I/O on multi-CPU SGI workstations. Open-sourced in 2000, merged into Linux 2.4.25 in 2002. **Red Hat made XFS the default for RHEL 7 in 2014** because the consensus around ext4 began to hit ceilings at petabyte-scale and high-IOPS NVMe workloads.

The big modern XFS features:
- **CRC (v5 superblock)** — every metadata block is checksummed
- **reflink** — `cp --reflink` does copy-on-write clones (RHEL 9 default)
- **bigtime** — timestamps survive past 2038 (RHEL 9 default)
- **Online resize** — `xfs_growfs` extends an XFS without unmounting

You cannot shrink XFS. If you need shrink, choose ext4. Everything else, XFS.

> **The point of the story:** XFS is the RHEL default for very good reasons. RHCSA expects you to use `mkfs.xfs` as your reflex.

---

## 👪 The XFS Family

```
Creation
├── mkfs.xfs DEV               ← format
├── mkfs.xfs -f DEV            ← force overwrite
├── mkfs.xfs -L LABEL DEV
└── mkfs.xfs -m crc=1,reflink=1,bigtime=1 DEV

Inspection
├── blkid DEV                  ← UUID, LABEL, TYPE
├── xfs_info /MNT              ← post-format details
├── xfs_db -r DEV              ← read-only superblock
└── lsblk -f DEV

Mounting
├── mount -t xfs DEV /MNT
├── mount -t xfs UUID=... /MNT
├── mount -t xfs LABEL=... /MNT
├── mount -o defaults,noatime  ← common mount options
└── /etc/fstab                 ← persistence

Administration
├── xfs_admin -L NEWLABEL DEV  ← relabel (unmounted)
├── xfs_admin -U NEWUUID DEV   ← change UUID
├── xfs_growfs /MNT            ← extend (Lab 129)
└── xfs_repair DEV             ← repair (Lab 118)
```

---

## 📚 XFS Reference Table

| Goal | Command | Notes |
|---|---|---|
| Default format | `mkfs.xfs /dev/X` | RHEL 9 defaults are good |
| Force (existing FS) | `mkfs.xfs -f /dev/X` | Overwrite signature |
| Label at format | `mkfs.xfs -L MYLABEL /dev/X` | Max 12 chars |
| Show UUID/label/type | `blkid /dev/X` | |
| Mount by UUID | `mount UUID=XXX /mnt/Y` | |
| Mount by LABEL | `mount LABEL=MYLABEL /mnt/Y` | |
| Mount options | `mount -o defaults,noatime` | `noatime` = perf |
| Post-format info | `xfs_info /MNT` | After mount |
| Relabel (offline) | `xfs_admin -L NEW /dev/X` | Unmount first |
| Change UUID | `xfs_admin -U NEW /dev/X` | Or `generate` |
| Add to fstab | `UUID=XXX /mnt/Y xfs defaults,noatime 0 0` | |
| Validate fstab | `mount -a && findmnt /mnt/Y` | |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | Mandatory exam task. UUID in fstab — not device path. |
| **RHCE candidate** | Ansible `community.general.filesystem: fstype=xfs` + `ansible.posix.mount: state=mounted`. |
| **SRE / Platform** | Database scratch, log volumes — XFS is the default. |
| **DevOps** | cloud-init `fs_setup: filesystem: xfs`. |
| **AI / MLOps** | NVMe training scratch usually formats XFS with `noatime`. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up sandbox & loop device

```bash
sudo -i
mkdir -p /root/xfs-lab && cd /root/xfs-lab

LOOP_IMG=/var/tmp/xfs-lab.img
truncate -s 1G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "$LOOP_DEV" | tee 01-loop.txt
```

---

### Task 2 — Create a single partition with `parted`

```bash
cd /root/xfs-lab

sudo parted -s "$LOOP_DEV" mklabel gpt
sudo parted -s "$LOOP_DEV" mkpart primary xfs 1MiB 100%
sudo partprobe "$LOOP_DEV"; sudo udevadm settle

PART="${LOOP_DEV}p1"
echo "$PART" | tee 02-partition.txt
lsblk "$LOOP_DEV" | tee 02-lsblk.txt
```

**Reading it left to right:** `parted -s` creates GPT + single full-disk partition. `${LOOP_DEV}p1` is the partition node (e.g. `/dev/loop9p1`).

---

### Task 3 — Format with defaults using `mkfs.xfs`

```bash
cd /root/xfs-lab

sudo mkfs.xfs "$PART" | tee 03-mkfs-default.txt
```

**Human-Readable Breakdown:** Format the partition with XFS using all defaults. `mkfs.xfs` prints the geometry it chose — capture for the report.

**Reading it left to right:** No options means `mkfs.xfs` uses RHEL 9 defaults: 4096-byte blocks, 512-byte sectors, CRC on, reflink on, bigtime on, internal log auto-sized, 4 allocation groups.

**The story:** RHEL 9 defaults are well-tuned. Touch them only if you have measured a reason.

**Expected output:**

```text
meta-data=/dev/loop9p1           isize=512    agcount=4, agsize=65472 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=1, sparse=1, rmapbt=0
         =                       reflink=1    bigtime=1 inobtcount=1 nrext64=0
data     =                       bsize=4096   blocks=261888, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
log      =internal log           bsize=4096   blocks=16384, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```

**Switches**

| Token | Meaning |
|---|---|
| `mkfs.xfs DEV` | Format DEV with XFS, defaults |
| `-f` | Force — overwrite an existing FS signature |
| `-L LABEL` | Set filesystem label |
| `-m crc=1` | CRC metadata (default in RHEL 9) |
| `-m reflink=1` | Copy-on-write clones |
| `-m bigtime=1` | Post-2038 timestamps |
| `-b size=4096` | Block size |
| `-d agcount=8` | Allocation group count |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `existing filesystem detected` | Add `-f` if you really want to overwrite |
| `Device busy` | `umount` first |
| `agcount=1 agsize=...` warning | Disk is small — fine for the lab |

---

### Task 4 — Reformat with a label `RHCSA_XFS`

```bash
cd /root/xfs-lab

sudo mkfs.xfs -f -L RHCSA_XFS "$PART" | tee 04-mkfs-label.txt
sudo blkid "$PART" | tee 04-blkid.txt
```

**Human-Readable Breakdown:** `-f` is required because Task 3 already wrote XFS to this partition. `-L RHCSA_XFS` sets the label. `blkid` reads back UUID + LABEL.

**Expected output:**

```text
/dev/loop9p1: LABEL="RHCSA_XFS" UUID="d8c0fe...-..." BLOCK_SIZE="4096" TYPE="xfs" PARTUUID="..."
```

---

### Task 5 — Capture UUID for fstab

```bash
cd /root/xfs-lab

UUID=$(sudo blkid -s UUID -o value "$PART")
echo "$UUID" | tee 05-uuid.txt
```

**Reading it left to right:** `blkid -s UUID -o value` prints just the UUID — perfect for shell substitution.

---

### Task 6 — Mount manually by UUID

```bash
cd /root/xfs-lab

sudo mkdir -p /mnt/rhcsa-xfs
sudo mount -t xfs -o defaults,noatime "UUID=$UUID" /mnt/rhcsa-xfs
findmnt /mnt/rhcsa-xfs | tee 06-findmnt.txt
df -hT /mnt/rhcsa-xfs | tee 06-df.txt
```

**The story:** Always make the mount point first (`mkdir -p`). Mounting by UUID survives device renames. `noatime` is the standard performance tweak.

**Expected output:**

```text
TARGET           SOURCE        FSTYPE OPTIONS
/mnt/rhcsa-xfs   /dev/loop9p1  xfs    rw,noatime,seclabel,attr2,inode64,...
```

---

### Task 7 — Inspect with `xfs_info`

```bash
cd /root/xfs-lab

sudo xfs_info /mnt/rhcsa-xfs | tee 07-xfs-info.txt
```

**The story:** `xfs_info` only works on a **mounted** XFS. It shows the same geometry as `mkfs.xfs` printed at creation. Use it to verify that the FS in production matches what you intended (e.g., correct block size on database volumes).

---

### Task 8 — Add a persistent fstab entry, validate with `mount -a`

```bash
cd /root/xfs-lab

sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
ls -lh /etc/fstab.bak.* | tee 08-fstab-backup.txt

sudo umount /mnt/rhcsa-xfs
echo "UUID=$UUID  /mnt/rhcsa-xfs  xfs  defaults,noatime  0 0" | sudo tee -a /etc/fstab

sudo systemctl daemon-reload
sudo mount -a
findmnt /mnt/rhcsa-xfs | tee 08-after-fstab.txt
```

**Human-Readable Breakdown:** Back up `/etc/fstab` first (RHCSA habit), unmount the manual mount, append the fstab line, reload systemd's view of mount units, and run `mount -a` to mount everything in fstab. The fact that `mount -a` succeeds without error is the proof that the fstab entry is syntactically and semantically correct — if you reboot without testing `mount -a` first you may end up in emergency mode.

**Reading it left to right:** Fstab fields are `device  mount_point  fstype  options  dump  pass`. `0 0` = no dump, no fsck pass on boot (XFS doesn't use fsck anyway). `systemctl daemon-reload` makes systemd re-read fstab → `*.mount` units.

**Expected output:**

```text
TARGET           SOURCE        FSTYPE OPTIONS
/mnt/rhcsa-xfs   /dev/loop9p1  xfs    rw,noatime,seclabel,attr2,inode64,...
```

**Switches**

| Token | Meaning |
|---|---|
| `mount -a` | Mount all fstab entries (skip `noauto`) |
| `tee -a FILE` | Append (don't truncate) |
| `systemctl daemon-reload` | Re-parse fstab → generated mount units |
| `defaults` | rw,suid,dev,exec,auto,nouser,async |
| `noatime` | Don't update access time on read (perf) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount -a` says "wrong fs type" | Typo in fstab — fix and retry |
| `unknown filesystem type` | Should be `xfs` not `XFS` |
| Boot drops to emergency mode after reboot | Fstab entry bad — `mount -a` would have caught it |

---

### Task 9 — Verify everything with multiple tools

```bash
cd /root/xfs-lab

findmnt /mnt/rhcsa-xfs | tee 09-findmnt.txt
df -hT /mnt/rhcsa-xfs | tee 09-df.txt
lsblk -f "$PART" | tee 09-lsblk.txt
sudo blkid "$PART" | tee 09-blkid.txt
sudo xfs_info /mnt/rhcsa-xfs | tee 09-xfs-info.txt

grep '/mnt/rhcsa-xfs' /etc/fstab | tee 09-fstab-line.txt
```

**The story:** Five different views of the same fact (XFS, mounted, persistent). On the exam, redundancy is your friend.

---

### Task 10 — Capstone report + cleanup

**Task statement:** *"Show the full lifecycle: partition → mkfs.xfs labeled → blkid UUID → fstab line → mount -a → xfs_info. Then revert /etc/fstab to the backup and tear down."*

```bash
cd /root/xfs-lab

cat > 10-report.txt <<EOF
XFS lifecycle report — $(hostname) — $(date -Iseconds)

Loop device : $LOOP_DEV
Partition   : $PART
UUID        : $UUID
LABEL       : RHCSA_XFS
Mount point : /mnt/rhcsa-xfs

== /etc/fstab line ==
$(grep '/mnt/rhcsa-xfs' /etc/fstab)

== findmnt ==
$(findmnt /mnt/rhcsa-xfs)

== xfs_info (truncated) ==
$(sudo xfs_info /mnt/rhcsa-xfs | head -n 5)
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo umount /mnt/rhcsa-xfs
sudo sed -i "\|/mnt/rhcsa-xfs|d" /etc/fstab
sudo rmdir /mnt/rhcsa-xfs

sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"

cd /root
rm -rf /root/xfs-lab
exit
```

**The story:** Cleanup order matters: unmount first, then remove the fstab line (so the next `mount -a` doesn't try to remount), then remove the directory, then detach the loop device, then delete the image file.

---

## 🔍 XFS Decision Guide

```
"Format with all defaults"   → mkfs.xfs DEV
"FS already there"           → mkfs.xfs -f DEV
"Want a label"               → mkfs.xfs -f -L LABEL DEV
"Read UUID"                  → blkid DEV
"Mount once"                 → mount UUID=... /mnt/X
"Mount on every boot"        → /etc/fstab + mount -a
"Verify"                     → findmnt + df -hT + xfs_info
"Change label later"         → umount, xfs_admin -L NEW DEV
"Need to shrink"             → Use ext4 instead (Lab 117)
"Need to grow"               → xfs_growfs /MNT (Lab 129)
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Loop device
- [ ] 02 Single GPT partition
- [ ] 03 `mkfs.xfs` default
- [ ] 04 Reformat with `-L`
- [ ] 05 Capture UUID
- [ ] 06 Mount by UUID + `noatime`
- [ ] 07 `xfs_info`
- [ ] 08 Append fstab entry + `mount -a`
- [ ] 09 Five-way verification
- [ ] 10 Capstone + revert fstab + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Fstab with device path | Boot fails when device name changes | Use UUID or LABEL |
| Forgot `mount -a` after editing fstab | Boots into emergency mode | Test every fstab edit before reboot |
| `mkfs.xfs` on mounted partition | Error | `umount` first |
| Label too long | mkfs warns or truncates | Max 12 chars |
| Wrong dump/pass fields | XFS marked for fsck | Always `0 0` for XFS |
| Edit fstab and reboot without testing | Emergency mode | Always `mount -a` first |
| Used `mkfs.xfs` without `-f` over existing FS | Refused | `-f` only when intentional |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize the chain: `mkfs.xfs -f -L LABEL DEV` → `blkid DEV` → fstab line with UUID → `mount -a`. That's a 30-second exam answer.

**RHCE candidate**
- `community.general.filesystem: fstype=xfs dev=/dev/vdb1` + `ansible.posix.mount: path=/mnt/x src=UUID=... fstype=xfs opts=defaults,noatime state=mounted`.

**SRE / Platform interview**
- Be ready to explain `noatime`, `nodiratime`, `relatime`, and why databases like `noatime`.

**DevOps**
- cloud-init `fs_setup: filesystem: xfs label: data` + `mounts:` block.

**AI / MLOps**
- Training scratch XFS: `mkfs.xfs -f -L NVME_SCRATCH /dev/nvme1n1p1`, mount with `noatime,inode64`.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 110 — Inspect Filesystems | Verify with df + findmnt |
| Lab 115 — parted | Created the partition |
| Lab 117 — ext4 format | Counterpart filesystem |
| Lab 129 — xfs_growfs | Online resize |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
