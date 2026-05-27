# Lab: Inspect ext Filesystem Features with `dumpe2fs` — `-h`, Block Groups, Journal, `grep features`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `dumpe2fs` (dump ext2/3/4 superblock + group descriptors + inode tables + journal), `dumpe2fs -h` (superblock header only — fast), `dumpe2fs -o superblock=N` (alternate superblock), `dumpe2fs -o blocksize=N`, `dumpe2fs -g GROUP` (single block group), `dumpe2fs -f` (force read dirty FS), `dumpe2fs -x` (extended options), interpreting **Filesystem features** (`has_journal`, `extent`, `dir_index`, `metadata_csum`, `64bit`, `flex_bg`, `sparse_super`, `large_file`, `huge_file`, `extra_isize`, `dir_nlink`, `filetype`, `resize_inode`, `needs_recovery`), **Default mount options**, **Journal inode** vs external journal, **Reserved blocks** and **Reserved GIDs**, **Inode count** vs **Free inodes**, **Block count** vs **Free blocks**, **Superblock backup locations**, pairing with `tune2fs -l` and `dumpe2fs -h | grep -E 'features|Filesystem state'`
- **Career arcs covered:** RHCSA (EX200 — "what features does this ext4 have?"), RHCE (Ansible facts + pre-flight checks), SRE (upgrade planning: does FS support metadata checksums?), DevOps (AMI bake verification), AI / MLOps (scratch volume tuning)
- **Prerequisite:** Labs 117–118 (ext4 format + fsck)
- **Time Estimate:** 25–40 minutes
- **Difficulty arc:** Tasks 1–2 sandbox + ext4 · Task 3 `dumpe2fs -h` · Task 4 `grep features` · Task 5 full dump + size control · Task 6 `-g 0` block group · Task 7 journal section · Task 8 superblock backups · Task 9 compare `tune2fs -l` vs `dumpe2fs -h` · Task 10 capstone + cleanup

---

## Objective

Answer *"what is actually inside this ext4?"* without mounting it. By the end of this lab you can run `dumpe2fs -h` on an unmounted device, decode the **Filesystem features** line, locate journal geometry, list superblock backup block numbers, and explain when `dumpe2fs` disagrees with `tune2fs -l` (it shouldn't — both read the same superblock).

The capstone: *"On unmounted `/dev/loop9p1`, produce `features.txt` containing only the Features line and the Default mount options line, plus one sentence stating whether the journal is internal or external."*

> **Lab safety note:** Loopback only. `dumpe2fs` is read-only unless you use write paths elsewhere — still prefer unmounted FS for consistency with fsck workflows.

---

## Concept: `dumpe2fs` Walks the On-Disk Layout

```
   ┌─────────────────────────────────────────────────────────────┐
   │ dumpe2fs [options] DEV                                       │
   │   Phase 1: read primary superblock (byte offset 1024)       │
   │   Phase 2: for each block group, dump group descriptor       │
   │   Phase 3: inode table / bitmap summaries                    │
   │   Phase 4: journal superblock (if has_journal)              │
   │                                                              │
   │ -h   → only superblock summary (fast, exam-friendly)         │
   │ -g N → only block group N                                    │
   │ -o superblock=N,blocksize=B → recovery read                   │
   │ -f   → force even if FS marked dirty                         │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Interviewers love *"what ext4 features enable extents?"* The answer is on the **Filesystem features** line — `extent`.

---

## 📜 Why `dumpe2fs` Exists — The Story

`dumpe2fs` ships with **e2fsprogs** (same package as `mkfs.ext4`, `tune2fs`, `e2fsck`). It predates modern GUIs — the whole point is to **serialize the superblock and block-group metadata to stdout** so a human or script can audit a filesystem offline.

> **The point of the story:** When `fsck` says "try alternate superblock," `dumpe2fs` tells you **which block numbers** are valid backups.

---

## 👪 The `dumpe2fs` Family

```
Read-only inspection
├── dumpe2fs DEV              ← full walk (can be long)
├── dumpe2fs -h DEV           ← header / superblock summary only
├── dumpe2fs -g N DEV         ← one block group
├── dumpe2fs -f DEV           ← force (dirty FS)
└── dumpe2fs -o superblock=N,blocksize=4096 DEV

Close relatives
├── tune2fs -l DEV            ← same superblock fields, different format
├── blkid DEV                 ← UUID/TYPE/LABEL
└── fsck.ext4 -n DEV        ← consistency (Lab 118)
```

---

## 📚 `dumpe2fs` Reference Table

| Goal | Command | Notes |
|---|---|---|
| Superblock summary | `dumpe2fs -h DEV` | Start here |
| Features only | `dumpe2fs -h DEV \| grep -i features` | |
| Default mount opts | `dumpe2fs -h DEV \| grep -i 'default mount'` | |
| Full metadata | `dumpe2fs DEV` | Large output |
| One block group | `dumpe2fs -g 0 DEV` | |
| Alternate superblock | `dumpe2fs -o superblock=32768,blocksize=4096 DEV` | |
| Force dirty | `dumpe2fs -f DEV` | Rare |
| Journal section | `dumpe2fs DEV \| grep -A20 '^Journal'` | |
| Backup superblocks | `dumpe2fs -h DEV \| grep 'Superblock backups'` | |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | Quick wins: `dumpe2fs -h` + `grep features`. |
| **RHCE candidate** | Pre-task: assert `metadata_csum` before applying play. |
| **SRE / Platform** | Post-incident: confirm journal internal vs external. |
| **DevOps** | Bake-time: capture `dumpe2fs -h` into build artifact. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox: loop + ext4

```bash
sudo -i
mkdir -p /root/dumpe2fs-lab && cd /root/dumpe2fs-lab

IMG=/var/tmp/dumpe2fs-lab.img
truncate -s 256M "$IMG"
DEV=$(sudo losetup --find --show "$IMG")
sudo mkfs.ext4 -F -L DUMPE2FS_LAB "$DEV" >/dev/null
echo "$DEV" | tee 01-device.txt
```

---

### Task 2 — Confirm unmounted + `blkid`

```bash
cd /root/dumpe2fs-lab
sudo umount "$DEV" 2>/dev/null || true
findmnt "$DEV" 2>&1 | tee 02-findmnt.txt
sudo blkid "$DEV" | tee 02-blkid.txt
```

---

### Task 3 — `dumpe2fs -h` (header only)

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs -h "$DEV" | tee 03-header.txt
```

**Human-Readable Breakdown:** `-h` prints **Filesystem volume name**, **UUID**, **Filesystem features**, **Filesystem flags**, inode/block counts, fragment size, **Reserved block count**, **Default mount options**, **Filesystem state**, dates, **Filesystem OS type**, **Inode size**, **Journal inode**, etc. — without walking every block group.

**Expected output (excerpt):**

```text
Filesystem volume name:   DUMPE2FS_LAB
Filesystem UUID:          ...
Filesystem magic number:  0xEF53
Filesystem revision #:    1 (dynamic)
Filesystem features:      has_journal ext_attr resize_inode ...
Filesystem flags:         signed_directory_hash
Default mount options:    user_xattr acl
Filesystem state:         clean
...
Inode count:              16384
Block count:              65536
Reserved block count:     3276
Free blocks:              ...
Free inodes:              ...
First block:              0
Block size:               4096
...
Journal inode:            8
Journal backup:           inode blocks
```

**Switches**

| Token | Meaning |
|---|---|
| `-h` | Header / superblock summary only |
| `-g N` | Dump only block group N |
| `-f` | Force read even if marked dirty |
| `-o superblock=N` | Read from backup superblock at block N |
| `-o blocksize=B` | Block size when using alternate superblock |
| `-x` | Extended attribute blocks (verbose) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Couldn't find valid filesystem superblock` | Wrong device or wiped disk — verify `blkid` |
| `Permission denied` | Run with `sudo` |
| Huge output without `-h` | Normal — pipe to `less` or use `-h` |

---

### Task 4 — `dumpe2fs -h | grep -i features`

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs -h "$DEV" | grep -i features | tee 04-features.txt
```

**The story:** This is the **exam one-liner** from the roadmap: *`dumpe2fs -h | grep features`*.

---

### Task 5 — Full dump (first 80 lines) + line count

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs "$DEV" 2>&1 | head -n 80 | tee 05-full-head.txt
sudo dumpe2fs "$DEV" 2>&1 | wc -l | tee 05-full-lines.txt
```

**The story:** Full `dumpe2fs` walks **every block group** — on a 20 TiB disk the output is enormous. Always start with `-h`, then drill with `-g` or `grep`.

---

### Task 6 — Block group 0 only: `dumpe2fs -g 0`

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs -g 0 "$DEV" | tee 06-group0.txt
```

**Reading it left to right:** Block group 0 holds the primary superblock, block bitmap, inode bitmap, inode table start — the **heart** of the filesystem.

---

### Task 7 — Journal block layout

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs "$DEV" 2>&1 | grep -A30 '^Journal features:' | tee 07-journal.txt
```

**The story:** `has_journal` in features + **Journal inode: 8** means **internal journal** stored as a special inode, not a separate partition.

---

### Task 8 — Superblock backup locations

```bash
cd /root/dumpe2fs-lab
sudo dumpe2fs -h "$DEV" | grep -E 'Superblock backups|Filesystem UUID|Block size' | tee 08-backups.txt
```

**The story:** When primary superblock corrupts, `e2fsck -b 32768 DEV` uses backup at block 32768 (typical first backup for 4 KiB block FS).

---

### Task 9 — Diff mental model: `tune2fs -l` vs `dumpe2fs -h`

```bash
cd /root/dumpe2fs-lab
sudo tune2fs -l "$DEV" | head -n 25 | tee 09-tune2fs-head.txt
sudo dumpe2fs -h "$DEV" | head -n 25 | tee 09-dumpe2fs-head.txt
```

**The story:** Both read the same on-disk superblock — different column names and ordering. `tune2fs -l` is tuned for **administration**; `dumpe2fs` is tuned for **forensics**.

---

### Task 10 — Capstone `features.txt` + cleanup

**Task statement:** *"Write `features.txt` with the Features line + Default mount options line + one sentence internal/external journal."*

```bash
cd /root/dumpe2fs-lab

sudo dumpe2fs -h "$DEV" | grep -iE '^(Filesystem features|Default mount options)' > features.txt
JIN=$(sudo dumpe2fs -h "$DEV" | awk '/^Journal inode:/ {print $3}')
if [ "$JIN" != "0" ]; then
  echo "Journal is internal (journal inode $JIN)." >> features.txt
else
  echo "Journal is external or absent (check full dumpe2fs)." >> features.txt
fi
cat features.txt | tee 10-capstone.txt
```

**Cleanup**

```bash
sudo losetup -d "$DEV"
sudo rm -f "$IMG"
cd /root && rm -rf /root/dumpe2fs-lab
exit
```

---

## 🔍 Decision Guide

```
"Quick feature audit"     → dumpe2fs -h DEV | grep -i features
"Why fsck wants backup SB" → dumpe2fs -h DEV | grep Superblock
"One group forensics"     → dumpe2fs -g 0 DEV
"Dirty but must read"     → dumpe2fs -f DEV
"Same data, admin view"   → tune2fs -l DEV
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Loop + ext4
- [ ] 02 Unmounted + blkid
- [ ] 03 `dumpe2fs -h`
- [ ] 04 `grep features`
- [ ] 05 Full dump sample + wc -l
- [ ] 06 `-g 0`
- [ ] 07 Journal section
- [ ] 08 Superblock backups
- [ ] 09 `tune2fs -l` compare
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Running on wrong `/dev/sdX` | Data panic | Always `blkid` first |
| Expecting XFS output | `Bad magic` | Use `xfs_info` / `xfs_db` for XFS |
| Full dump on huge FS | Terminal flood | `-h` or `-g` |
| Ignoring `Filesystem state: not clean` | fsck needed | Run `fsck -n` then repair |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate** — Memorize: `dumpe2fs -h /dev/... | grep -E 'features|Default mount'`.

**SRE interview** — *"What does `extent` buy you?"* → Extents replace indirect block chains for large files = fewer metadata reads.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 117 | Created the ext4 |
| Lab 118 | fsck after corruption |
| Lab 117 | `tune2fs -l` twin |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
