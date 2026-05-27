# Lab: Inspect Filesystems — `df -h`, `df -i`, `findmnt`, `mount`, `lsblk -f`, `du -sh`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `df` (filesystem disk usage), `-h` human-readable, `-T` type column, `-i` inodes, `-x TYPE` exclusion, `--total` summary row, `findmnt` (mount tree), `-T PATH` lookup by path, `-o COLS` column selection, `--source` / `--target` filters, `-n` no-header, `--df` df-like output, `mount` legacy view, `lsblk -f` (filesystem + UUID + LABEL per block device), `du -sh DIR` for per-directory totals, distinguishing **block-device free space** (`df`) from **directory content size** (`du`), reading `/proc/mounts` and `/etc/mtab` directly, the "Use% 100%" investigation playbook
- **Career arcs covered:** RHCSA (EX200 — "show free space on every mounted filesystem"), RHCE (Ansible disk-fill alerts), SRE (capacity planning), DevOps (CI runner disk pressure), AI / MLOps (dataset volume monitoring)
- **Prerequisite:** Basic vocabulary for partitions, filesystems, mount points
- **Time Estimate:** 25 to 35 minutes
- **Difficulty arc:** Tasks 1–2 baseline + `df -h` · Tasks 3–4 `-T` / `-i` / `-x` · Tasks 5–6 `findmnt` tree and column views · Task 7 `lsblk -f` for block-device view · Task 8 `du` for directory deep-dive · Task 9 "find the disk hog" playbook · Task 10 capstone fleet-style summary + cleanup

---

## Objective

Stop guessing where the disk is full. By the end of this lab you can identify, in three independent ways, which mounted filesystem has the least free space, which directory is the heaviest contributor, and how to read `df`, `findmnt`, and `lsblk` outputs fluently. You will also know how to filter out pseudo-filesystems (tmpfs, devpts, ...) and read inodes — the *other* way a filesystem fills up.

The capstone is the engineer-realistic prompt: *"On this RHEL 9 host, write a one-paragraph storage summary listing total capacity, total used, the busiest mount by Use%, and the deepest directory hog under `/var`. Include both block usage and inode usage."*

> **Lab safety note:** This lab is read-only. No partitions, mounts, or files are modified.

---

## Concept: Free Space Has Two Axes — Blocks and Inodes

A Linux filesystem can hit 100% in two different ways:

1. **Block-full** — every data block is allocated. `df` Use% shows 100%.
2. **Inode-full** — every inode (per-file metadata slot) is allocated. `df -i` shows 100% even when there are plenty of blocks free.

Inode exhaustion is rarer but devastating: a directory tree full of millions of tiny files (mail spools, cache directories) can exhaust inodes long before blocks. `df -i` is the only way to see it.

```
   ┌─────────────────────────────────────────────────────────────┐
   │  Filesystem health = (block_used ≤ ~85%) AND (inode_used ≤ ~85%) │
   │                                                             │
   │  df -h     → block view  (KiB / MiB / GiB used)             │
   │  df -i     → inode view  (count of file metadata records)   │
   │  findmnt   → tree view + mount options                      │
   │  lsblk -f  → block device + FS + UUID + LABEL               │
   │  du -sh    → per-directory content size (slow on big trees) │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Every "disk full" ticket asks "block or inode?" If you only know `df -h`, you cannot answer.

---

## 📜 Why `df` and `findmnt` Both Exist — The Story

`df` (disk free) was in 4.2BSD and earlier — a simple Unix tool to read the kernel's mount table and statvfs() each mounted filesystem. It is **block-centric**: it asks the kernel "how much space is free on this filesystem?"

`findmnt` is a newer tool from `util-linux` (2010s era) built specifically for systemd-era Linux: it reads `/proc/self/mountinfo` and renders the result as a tree, with column-selectable output and `-T PATH` lookup. Where `df` is "filesystem usage", `findmnt` is "mount topology."

Both tools live on RHEL 9. `df` for usage, `findmnt` for topology. Old habits will reach for `mount | grep`; the modern equivalent is `findmnt`.

> **The point of the story:** Use the right tool. `df` for "how full?" `findmnt` for "how mounted?" `lsblk` for "where on the block layer?"

---

## 👪 The Filesystem-Inspect Family — Who Lives Where

```
Block-device view
└── lsblk                              ← block tree (disk → partition → mount)
    └── lsblk -f                       ← + filesystem, UUID, LABEL

Mount topology view
├── findmnt                            ← tree of mountpoints
├── findmnt -T PATH                    ← mount containing PATH
├── findmnt --df                       ← df-like output
└── /proc/self/mountinfo               ← kernel source of truth

Filesystem usage view
├── df                                 ← block usage
├── df -i                              ← inode usage
├── df -T                              ← +type column
├── df -h / --si                       ← human-readable
└── df -x TYPE                         ← exclude a type

Directory content view
├── du -sh DIR                          ← per-directory total
├── du -h --max-depth=1 DIR             ← one level deep
└── du -ah | sort -h | tail -n 20       ← top 20 largest entries
```

---

## 📚 Inspection Reference Table

| Goal | Command | Notes |
|---|---|---|
| Block usage (default) | `df` | KiB blocks |
| Human-readable | `df -h` | MiB / GiB |
| Add type column | `df -T` | Adds FSTYPE |
| Combine | `df -hT` | Most common form |
| Inode view | `df -i` | Required when files >> blocks |
| Exclude tmpfs/devtmpfs | `df -h -x tmpfs -x devtmpfs` | Hide pseudo-FS |
| Total summary row | `df -h --total` | Aggregate at the bottom |
| Specific path | `df -h /home` | One mount |
| Tree view | `findmnt` | Tree |
| One mount | `findmnt /home` | Filter |
| Path → mount | `findmnt -T /home/user/file` | Lookup |
| Columns | `findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS,USE%,SIZE` | Custom view |
| df-like | `findmnt --df` | Closer to `df` layout |
| No header | `findmnt -n` | Scripts |
| Block-device + FS | `lsblk -f` | FS + UUID + LABEL |
| Live mounts | `mount` | Legacy text |
| Kernel truth | `cat /proc/self/mountinfo` | Underlying source |
| Per-directory | `du -sh DIR` | Slow on big trees |
| Top 20 hogs | `du -ah / 2>/dev/null \| sort -rh \| head -n 20` | Full tree scan |
| One level only | `du -h --max-depth=1 /var` | Faster than `du -ah` |
| Combine FS + path | `df -h $(findmnt -T PATH -n -o TARGET)` | Programmatic |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200: "Show disk usage by filesystem." `df -hT` answers it. |
| **RHCE candidate** | Ansible: `setup` module exposes `ansible_mounts` — same data programmatically. |
| **SRE / Platform** | Capacity planning starts here; `df --total` feeds dashboards. |
| **DevOps** | CI runner disk pressure: pre-build `df -h` + `du -sh /workspace` audit. |
| **AI / MLOps** | Dataset volumes fill mostly via files; both block and inode views matter. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up the sandbox and capture baseline disk view

```bash
sudo -i
mkdir -p /root/fs-inspect-lab && cd /root/fs-inspect-lab

df | tee 01-df-default.txt | head -n 5
df -h | tee 01-df-h.txt
```

**Human-Readable Breakdown:** Become root, create a workspace, capture default `df` output (KiB blocks) and the human-readable form.

**Reading it left to right:** Default `df` columns: Filesystem, 1K-blocks, Used, Available, Use%, Mounted on. `-h` swaps `1K-blocks` for human units (K/M/G/T).

**The story:** `df -h` is the most-typed disk command in the world. Memorize the column order — every other variant just adds or replaces columns.

**Expected output:**

```text
Filesystem     1K-blocks    Used Available Use% Mounted on
devtmpfs            4096       0      4096   0% /dev
tmpfs             405492       0    405492   0% /dev/shm
...
/dev/nvme0n1p4  41947024 8123456  31813900  21% /
```

**Switches**

| Token | Meaning |
|---|---|
| `df` | Default KiB |
| `df -h` | Human-readable |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Long filesystem names wrap | `df -h -P` (POSIX format) keeps one row per FS |

---

### Task 2 — Filesystem type with `-T` and the standard `-hT` form

```bash
cd /root/fs-inspect-lab

df -hT | tee 02-df-hT.txt
df -hT -x tmpfs -x devtmpfs -x squashfs | tee 02-df-hT-no-pseudo.txt
```

**Human-Readable Breakdown:** Add the `Type` column with `-T`, then exclude the noisy pseudo-filesystems to keep only real on-disk filesystems.

**Reading it left to right:** `-T` adds FSTYPE between Filesystem and 1K-blocks. `-x TYPE` excludes; you can repeat it.

**The story:** `df -hT` is the **professional** default. Knowing whether `/var` is ext4 or xfs changes what you can do (resize, shrink, fsck). Pseudo-filesystem rows pollute the view; exclude them.

**Expected output:**

```text
Filesystem     Type     Size  Used Avail Use% Mounted on
/dev/nvme0n1p4 ext4      40G  7.8G   31G  21% /
/dev/nvme0n1p2 xfs      976M   75M  902M   8% /boot
```

**Switches**

| Token | Meaning |
|---|---|
| `-T` | Type column |
| `-x TYPE` | Exclude type (repeatable) |
| `-t TYPE` | Include only that type |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Output too narrow | `df -hT -P` for POSIX format |

---

### Task 3 — Inode view with `df -i`

```bash
cd /root/fs-inspect-lab

df -i | tee 03-df-i.txt | head -n 5
df -ihT -x tmpfs -x devtmpfs | tee 03-df-ihT.txt
df -i / | tee 03-df-i-root.txt
```

**Human-Readable Breakdown:** See inode usage on every FS, then the same view with human units and type column.

**Reading it left to right:** `-i` swaps block columns for inode columns: Inodes / IUsed / IFree / IUse%. Combine with `-h` and `-T` like before.

**The story:** "Disk full" tickets often come with `df -h` showing 50% used — confusing the operator. `df -i` tells you the filesystem ran out of *file slots*, not space. The culprit is usually a directory with millions of tiny files (mail spool, cache).

**Expected output:**

```text
Filesystem      Inodes IUsed   IFree IUse% Mounted on
/dev/nvme0n1p4  2621440 89512 2531928    4% /
/dev/nvme0n1p2  524288    321 523967     1% /boot
```

**Switches**

| Token | Meaning |
|---|---|
| `-i` | Inode counts |
| `-ih` | Human inode counts |
| `-ihT` | + type column |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `IUse% 100%` | Find the directory with the most files — `find DIR -xdev -type f \| wc -l` |
| `Inodes 0` | XFS uses dynamic inodes — count is 0 by design |

---

### Task 4 — `--total` summary and per-path queries

```bash
cd /root/fs-inspect-lab

df -h --total | tee 04-df-total.txt | tail -n 2
df -h /var /home / | tee 04-df-paths.txt
```

**Human-Readable Breakdown:** Add a `total` row at the bottom, then query specific paths to scope the output.

**Reading it left to right:** `--total` appends one summary row aggregating all displayed filesystems. Listing paths restricts to the filesystems containing those paths.

**The story:** `df -h --total` is the report-style view. `df -h /var /home /` answers "what's the state of these three mounts?" in one call.

**Expected output:**

```text
total            40G   8G   30G  21% -
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p4   40G  7.8G   31G  21% /
/dev/nvme0n1p3  100G   18G   80G  19% /var
/dev/nvme0n1p5  500G   12G  482G   3% /home
```

**Switches**

| Token | Meaning |
|---|---|
| `--total` | Summary row |
| `df PATH ...` | Restrict to filesystems containing PATH |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `--total` not honored | Old `df`; install latest `coreutils` |

---

### Task 5 — `findmnt` tree view

```bash
cd /root/fs-inspect-lab

findmnt | tee 05-findmnt-tree.txt | head -n 20
findmnt -t ext4,xfs | tee 05-findmnt-real-fs.txt
findmnt -T /root/fs-inspect-lab | tee 05-findmnt-path-lookup.txt
```

**Human-Readable Breakdown:** Default tree view, then filter to only real on-disk filesystems, then look up which mount contains the lab directory.

**Reading it left to right:** `findmnt` without args prints a tree. `-t TYPE` filters by FSTYPE. `-T PATH` finds the mount containing PATH (one row).

**The story:** `findmnt -T PATH` answers "which mount is this file actually on?" Critical for `du` scoping or for understanding bind mounts.

**Expected output (excerpt):**

```text
TARGET     SOURCE         FSTYPE OPTIONS
/          /dev/nvme0n1p4 ext4   rw,relatime,seclabel
├─/boot    /dev/nvme0n1p2 xfs    rw,relatime,seclabel,attr2,inode64,noquota
├─/var     /dev/nvme0n1p3 ext4   rw,relatime,seclabel
└─/home    /dev/nvme0n1p5 ext4   rw,relatime,seclabel
TARGET SOURCE         FSTYPE OPTIONS
/      /dev/nvme0n1p4 ext4   rw,relatime,seclabel
```

**Switches**

| Token | Meaning |
|---|---|
| `findmnt` | Tree view |
| `-t TYPE,TYPE` | Comma-separated FSTYPE filter |
| `-T PATH` | Mount containing PATH |
| `-r` / `--raw` | Single-column output |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Tree confusing | Use `findmnt --df` for df-like layout |
| Path not found | Check the path exists; `findmnt -T $(realpath PATH)` |

---

### Task 6 — Customize `findmnt` columns and `--df` layout

```bash
cd /root/fs-inspect-lab

findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS,USE%,SIZE,UUID | tee 06-findmnt-custom.txt
findmnt --df | tee 06-findmnt-df.txt
findmnt -n -o TARGET,FSTYPE,OPTIONS | tee 06-findmnt-script.txt
```

**Human-Readable Breakdown:** Choose your columns explicitly, get a df-like layout, and a header-less scriptable version.

**Reading it left to right:** `-o COLS` enumerates columns. `--df` mimics `df` layout. `-n` removes the header for scripts.

**The story:** `findmnt -o ...` is how you generate exactly the report you need. Combine with `-n` for grep-able output.

**Expected output:**

```text
TARGET     SOURCE         FSTYPE OPTIONS                  USE% SIZE UUID
/          /dev/nvme0n1p4 ext4   rw,relatime,seclabel      21%  40G f1234abc-...
SOURCE         FSTYPE   SIZE  USED AVAIL USE% TARGET
/dev/nvme0n1p4 ext4      40G  7.8G   31G  21% /
```

**Switches**

| Token | Meaning |
|---|---|
| `-o COLS` | Comma-separated columns |
| `--df` | df-like output |
| `-n` | No header |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Column unknown | `findmnt --output-all` lists every available column |

---

### Task 7 — `lsblk -f` block-device view

```bash
cd /root/fs-inspect-lab

lsblk | tee 07-lsblk.txt
lsblk -f | tee 07-lsblk-f.txt
lsblk -o NAME,TYPE,FSTYPE,LABEL,UUID,SIZE,MOUNTPOINT | tee 07-lsblk-custom.txt
```

**Human-Readable Breakdown:** Three lsblk variants — default, `-f` (FS-aware), and a custom column set.

**Reading it left to right:** `lsblk` walks the block device tree. `-f` adds FSTYPE, LABEL, UUID, MOUNTPOINT columns. `-o COLS` is custom column selection.

**The story:** `lsblk -f` is the bridge between **mount view** (`findmnt`) and **filesystem view** (`df`). It shows the device tree, the filesystem on each device, the UUID/LABEL (useful for `/etc/fstab`), and where it is mounted.

**Expected output (excerpt):**

```text
NAME        FSTYPE LABEL UUID                                 MOUNTPOINT
nvme0n1
├─nvme0n1p1                                                   
├─nvme0n1p2 xfs    boot  e98a... /boot
├─nvme0n1p3 ext4   var   d1234.../var
├─nvme0n1p4 ext4   root  f1234.../ 
└─nvme0n1p5 ext4   home  a4567.../home
```

**Switches**

| Token | Meaning |
|---|---|
| `lsblk -f` | + FS + UUID + LABEL |
| `-o COLS` | Custom |
| `-p` | Full /dev/ paths |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| FSTYPE empty | Unformatted device |
| UUID missing | Unformatted or wiped device |

---

### Task 8 — `du` for per-directory content

```bash
cd /root/fs-inspect-lab

du -sh /var 2>/dev/null | tee 08-du-var-total.txt
sudo du -h --max-depth=1 /var 2>/dev/null | sort -h | tee 08-du-var-1level.txt
sudo du -ah /var 2>/dev/null | sort -rh | head -n 20 | tee 08-du-top20.txt
```

**Human-Readable Breakdown:** Total `/var` size, one level deep, then top 20 largest entries in `/var` (files or directories).

**Reading it left to right:** `du -sh` summarizes one directory. `-h --max-depth=1` is one level only — much faster than `-ah`. `du -ah | sort -rh` finds the heaviest entries.

**The story:** `df` says "the filesystem is 80% full." `du` says "and here's where most of it lives." Use `--max-depth` to avoid waiting hours on huge trees.

**Expected output:**

```text
18G    /var
0       /var/account
8.0G    /var/cache
4.0G    /var/lib
2.5G    /var/log
...
4.0G    /var/lib/postgresql/data/base/16384/1234567
2.0G    /var/cache/dnf/...
```

**Switches**

| Token | Meaning |
|---|---|
| `du -s DIR` | Summary (total only) |
| `du -h` | Human |
| `du -a` | All files, not just dirs |
| `--max-depth=N` | Limit traversal depth |
| `du -x` | Don't cross filesystem boundaries |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `du` very slow on `/` | Use `--max-depth=1` and walk deeper as needed |
| Permission denied noise | `2>/dev/null` or `sudo` |

---

### Task 9 — "Find the disk hog" playbook

```bash
cd /root/fs-inspect-lab

BUSY_MOUNT=$(df -h --output=pcent,target -x tmpfs -x devtmpfs 2>/dev/null | tail -n +2 | sort -rn | head -n 1 | awk '{print $2}')
echo "Busiest mount: $BUSY_MOUNT" | tee 09-busy-mount.txt

if [ -n "$BUSY_MOUNT" ]; then
  sudo du -h --max-depth=1 "$BUSY_MOUNT" 2>/dev/null | sort -h | tail -n 20 | tee 09-busy-mount-children.txt
fi
```

**Human-Readable Breakdown:** Find the mount with the highest Use%, then list its top-level children by size.

**Reading it left to right:** `df --output=pcent,target` is the modern way to choose columns (older RHELs don't support it — see `awk` fallback). The pipeline keeps the highest Use% line, extracts the mount path, then `du --max-depth=1` lists the heavy children.

**The story:** This is the **30-second disk-hog playbook**. From "alert fires" to "I know which directory" in two commands.

**Expected output:**

```text
Busiest mount: /var
4.0G    /var/cache
2.5G    /var/log
6.0G    /var/lib
```

**Switches**

| Token | Meaning |
|---|---|
| `df --output=COLS` | Modern column selection |
| `sort -rn` | Reverse numeric |
| `tail -n +2` | Skip header |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `--output` rejected | Older df — use `awk '{print $5, $6}'` |
| Empty `BUSY_MOUNT` | All mounts under same threshold |

---

### Task 10 — Capstone: storage summary + cleanup

```bash
cd /root/fs-inspect-lab

TOTAL=$(df -h --total -x tmpfs -x devtmpfs 2>/dev/null | awk '/^total/ {print $2}')
USED=$(df -h --total -x tmpfs -x devtmpfs 2>/dev/null | awk '/^total/ {print $3}')
BUSY=$(df -h -x tmpfs -x devtmpfs 2>/dev/null | tail -n +2 | sort -k5 -rn | head -n 1 | awk '{print $5, $6}')
HEAVY_VAR=$(sudo du -h --max-depth=1 /var 2>/dev/null | sort -h | tail -n 1)
INODES_USED=$(df -i / 2>/dev/null | awk 'NR==2 {print $5, $1}')

cat > 10-report.txt <<EOF
Storage inspection report — $(hostname) — $(date -Iseconds)

Total capacity (real FS only):   ${TOTAL}
Total used (real FS only):       ${USED}
Busiest mount (Use% , target):   ${BUSY}
Heaviest /var subdir (depth=1):  ${HEAVY_VAR}
Root inode usage (root FS):      ${INODES_USED}

How to reproduce:
  df -hT -x tmpfs -x devtmpfs --total
  findmnt --df
  lsblk -f
  du -h --max-depth=1 /var
EOF

cat 10-report.txt
```

**Cleanup**

```bash
cd /root
rm -rf /root/fs-inspect-lab
exit
```

---

## 🔍 Inspection Decision Guide

```
"How full is each FS?"          → df -hT
"Block or inode?"               → df -i
"Where is /home/foo mounted?"   → findmnt -T /home/foo
"What devices and FS labels?"   → lsblk -f
"Which directory is heaviest?"  → du -h --max-depth=1 DIR
"Top 20 biggest files"          → du -ah / | sort -rh | head -n 20
"Total across real FS"          → df -h --total -x tmpfs
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 `df` default + `-h`
- [ ] 02 `df -hT` + `-x` exclusion
- [ ] 03 `df -i` inode view
- [ ] 04 `--total` summary, per-path
- [ ] 05 `findmnt` tree + `-T` path lookup
- [ ] 06 `findmnt -o COLS` and `--df`
- [ ] 07 `lsblk -f` block view
- [ ] 08 `du -sh`, `-h --max-depth=1`, top-20
- [ ] 09 Find-the-disk-hog playbook
- [ ] 10 Capstone storage summary + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trust `df -h` alone | Inode exhaustion missed | Always also check `df -i` |
| Confuse `df` and `du` | Numbers disagree | `df` = block-device; `du` = file content |
| Forget `-x tmpfs` | Pseudo-FS pollute output | `-x tmpfs -x devtmpfs` |
| `du` crosses mounts | Counts other filesystems | Add `-x` |
| `mount | grep` instead of `findmnt` | Verbose, error-prone | Use `findmnt -T PATH` |
| `du -a /` no exclusion | Hours of runtime | `--max-depth=1` first |
| Sort `df` by Use% — column wrong | Sorts wrong column | Use `df --output=pcent,target` + `sort -rn` |
| Ignoring XFS dynamic inodes | `IUsed 0` looks wrong | XFS allocates inodes lazily |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Show me disk usage by filesystem." → `df -hT -x tmpfs -x devtmpfs`. "Show inode usage." → `df -ih`.

**RHCE candidate**
- Ansible: `setup` module's `ansible_mounts` provides programmatic `df` data.

**SRE / Platform interview**
- Be ready to explain Use% calculation: `Used / (Used + Available)` — *not* `Used / Total`.

**DevOps**
- CI workflow: `df -h /workspace` before build, prune cache directories with `du -h --max-depth=1` to identify cleanup candidates.

**AI / MLOps**
- Dataset volumes: monitor both `df -h` and `df -i` — many small image files exhaust inodes.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 111 — `fdisk -l` partition tables | Lower layer below `df` / `findmnt` |
| Lab 116 — Format with XFS | After format, `df -hT` shows the new FS |
| Lab 131 — Mount filesystem | After mount, `findmnt` appears |
| Lab 132 — Retrieve UUIDs | `lsblk -f` shows the UUID |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
