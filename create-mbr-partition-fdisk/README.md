# Lab: Create an MBR Partition with `fdisk` — `n`, `p`, `+SIZE`, `t`, `w`, `partprobe`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `fdisk /dev/DEVICE` interactive prompt, `m` for menu, `p` for print, `n` for new partition, choosing **p**rimary vs **e**xtended, partition numbers (1–4 primary), first sector defaults, size specifications (`+1G`, `+500M`, `+10485760` sectors), `t` to set type code (`83 Linux`, `82 swap`, `8e LVM`), `w` to write and exit, `q` to quit without saving, `d` to delete, `l` to list type codes, the safe practice of always running `p` before `w`, post-write rescans (`partprobe`, `udevadm settle`, `kpartx -u`), confirming with `lsblk` and `fdisk -l`, loopback `losetup` setup for lab-safe practice, the standard MBR rule of 4 primaries (or 3 primaries + 1 extended with multiple logicals)
- **Career arcs covered:** RHCSA (EX200 — "create a 1 GiB Linux partition on /dev/vdb"), RHCE (Ansible `community.general.parted` module), SRE (provisioning new data volumes), DevOps (CI base-image partition shaping), AI / MLOps (cache partition carving on NVMe)
- **Prerequisite:** Lab 111 (Display Partition Tables)
- **Time Estimate:** 35 to 50 minutes
- **Difficulty arc:** Tasks 1–2 set up a safe loop device (so the lab works without spare disks) · Tasks 3–4 enter fdisk and print baseline · Tasks 5–6 create the first primary partition step-by-step · Task 7 size variants (`+SIZE`, `+SECTORS`, default to end) · Task 8 set type with `t` · Task 9 write + rescan + verify · Task 10 capstone (2 partitions + report + cleanup)

---

## Objective

Stop hand-waving "create a partition." By the end of this lab you can drive `fdisk` interactively from `n` → `p` → number → first sector → `+SIZE` → `t` → type code → `w`, then prove the kernel sees the new partition with `lsblk`. You will do it on a **loopback** device so the lab is safe on any RHEL 9 VM — and the keystrokes transfer 1:1 to a real `/dev/vdb` or `/dev/nvme1n1`.

The capstone is the engineer-realistic prompt: *"On `/dev/loop9` (representing a new 1 GiB data disk), create an MBR partition table, a 256 MiB primary partition of type Linux (`83`), and a 256 MiB primary partition of type Linux swap (`82`). Verify with `lsblk` and `fdisk -l`."*

> **Lab safety note:** This lab uses **a loopback file in `/var/tmp/`** so it works on any RHEL 9 VM without spare disks. The same `fdisk` keystrokes apply to `/dev/vdb` or `/dev/nvme1n1` on a real host. Task 10 cleans up the loop device and the file.

---

## Concept: MBR's Four-Slot Rule

The Master Boot Record has **four** partition slots at LBA 0. The rules:

- Slots 1–4 are **primary**.
- One slot may be **extended**, which contains **logical** partitions inside it.
- Typical pattern: 3 primary + 1 extended (containing many logicals).

In `fdisk`, when you choose `n`, you pick a partition number 1–4 (or accept the default). If you set one as extended, subsequent partition numbers start at 5.

```
   ┌───────────────────────────────────────────────────────────────┐
   │ /dev/sdb                                                      │
   │ ┌─────────┬─────────┬─────────┬───────────────────────────────┐│
   │ │ sdb1    │ sdb2    │ sdb3    │ sdb4 (extended)               ││
   │ │ primary │ primary │ primary │ ┌─────┬─────┬─────┬─────────┐ ││
   │ │ type 83 │ type 82 │ type 83 │ │ sdb5│ sdb6│ sdb7│ ...     │ ││
   │ │         │         │         │ │ log │ log │ log │         │ ││
   │ └─────────┴─────────┴─────────┴─┴─────┴─────┴─────┴─────────┘ ││
   └───────────────────────────────────────────────────────────────┘
```

> **Why this matters:** On MBR, you cannot create a 5th primary. If `fdisk` says "All primary partitions are in use," you must convert one to extended (or use GPT instead).

---

## 📜 Why `fdisk` Still Matters — The Story

`fdisk` is the oldest partition tool on Linux — its UI (menu-driven, single-letter commands) is unchanged since the 1990s. Newer tools (`parted`, `sfdisk`) are scriptable; `fdisk` is **interactive**.

So why is `fdisk` still everywhere? Three reasons:

1. **Universal availability** — `util-linux` ships it on every Linux distro.
2. **Mental model** — the `n`/`p`/`d`/`t`/`w` keys are the same vocabulary Red Hat documentation has used for 20+ years; exam questions use the same words.
3. **GPT support** — `util-linux` 2.23 added GPT support; one tool now does both tables.

RHCSA EX200 expects you to drive `fdisk` interactively. RHCE / Ansible expects you to drive `parted` non-interactively. Both labs exist in this series; this one is `fdisk`.

> **The point of the story:** Master `fdisk` for interactive exam-day work; master `parted` (Lab 115) for automation.

---

## 👪 The `fdisk` Interactive Family

```
Top-level
└── fdisk /dev/DEV       ← enter interactive mode

Menu key map
├── m    help (lists every command)
├── p    print current table
├── n    new partition
├── d    delete partition
├── t    set partition type
├── l    list known type codes
├── a    toggle the boot flag on a primary partition
├── i    print info about one partition
├── x    enter expert mode (extra options)
├── v    verify the partition table
├── F    list free space
├── w    write changes and quit
└── q    quit without writing
```

### `n` subprompts

```
Command (m for help): n
Partition type
   p   primary (default if free slots remain)
   e   extended
Partition number (1-4, default N): <enter>
First sector (DEFAULT-DEFAULT, default DEFAULT): <enter to use first free>
Last sector, +/-sectors or +/-size{K,M,G,T,P} (DEFAULT-DEFAULT, default DEFAULT): +1G
```

### Most-used type codes (MBR)

| Code | Meaning |
|---|---|
| `83` | Linux filesystem (default) |
| `82` | Linux swap / Solaris |
| `8e` | Linux LVM |
| `fd` | Linux RAID autodetect |
| `b`  | W95 FAT32 |
| `7`  | NTFS/HPFS/exFAT |

---

## 📚 fdisk Reference Table

| Goal | Inside fdisk | Notes |
|---|---|---|
| Enter | `fdisk /dev/X` | Interactive |
| Help | `m` | Lists every command |
| Print | `p` | Always run `p` before `w` |
| New | `n` then `p`/`e` then number then start then `+SIZE` | Sequence |
| Delete | `d` then number | |
| Set type | `t` then number then code | |
| Toggle boot | `a` then number | MBR only |
| List free | `F` | Show gaps |
| Verify | `v` | Check geometry/consistency |
| Write | `w` | Commits to disk |
| Quit no-save | `q` | Safety button |
| Rescan kernel | `partprobe /dev/X` | After write |
| Rescan udev | `udevadm settle` | Wait for events |
| Confirm | `lsblk /dev/X` | New partition row |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200: "Create a 1 GiB primary partition on /dev/vdb." `fdisk` is the canonical answer. |
| **RHCE candidate** | Ansible `community.general.parted` is the IaC twin of `fdisk`. |
| **SRE / Platform** | Provisioning new EBS volumes — single-partition then `pvcreate` for LVM. |
| **DevOps** | CI base-image partition shaping; small swap partition aids ephemeral runners. |
| **AI / MLOps** | NVMe scratch carving for fast intermediate writes. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up the sandbox and create a loop-device "disk"

```bash
sudo -i
mkdir -p /root/fdisk-mbr-lab && cd /root/fdisk-mbr-lab

LOOP_IMG=/var/tmp/mbr-lab.img
truncate -s 1G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "Loop device: $LOOP_DEV" | tee 01-loop-device.txt
ls -lh "$LOOP_IMG" | tee -a 01-loop-device.txt
lsblk "$LOOP_DEV" | tee -a 01-loop-device.txt
```

**Human-Readable Breakdown:** Allocate a 1 GiB sparse file with `truncate`, attach it as a loop block device with `losetup --find --show`, and capture the path.

**Reading it left to right:** `truncate -s 1G FILE` creates a sparse file. `losetup --find --show FILE` attaches and prints the resulting device path (e.g., `/dev/loop9`).

**The story:** Loop devices behave exactly like real disks for `fdisk`, `mkfs`, `mount`, etc. Use them whenever you don't have a spare disk — every keystroke transfers to a real device.

**Expected output:**

```text
Loop device: /dev/loop9
-rw-r--r--. 1 root root 1.0G Jan 14 09:00 /var/tmp/mbr-lab.img
NAME    MAJ:MIN RM SIZE RO TYPE MOUNTPOINTS
loop9     7:9    0   1G  0 loop
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `losetup: no available loop device` | `sudo modprobe loop` or use `losetup -f` |
| `truncate: cannot create` | Wrong path / no space |

---

### Task 2 — Pre-flight check: confirm the loop has no partition table yet

```bash
cd /root/fdisk-mbr-lab

sudo fdisk -l "$LOOP_DEV" | tee 02-fdisk-pre.txt
sudo blkid "$LOOP_DEV" 2>&1 | tee 02-blkid-pre.txt
```

**The story:** Before partitioning, prove the device is empty. If `fdisk -l` shows a `Disklabel type:` line, the device already has a table — we will create a new MBR table in Task 3.

**Expected output:**

```text
Disk /dev/loop9: 1 GiB, 1073741824 bytes, 2097152 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
(no partition table)
```

---

### Task 3 — Enter `fdisk` and create an MBR table with `o`

```bash
cd /root/fdisk-mbr-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 03-fdisk-create-mbr.txt
o
p
w
EOF
```

**Human-Readable Breakdown:** Pipe a series of `fdisk` commands via heredoc. `o` creates a new MBR (dos) disklabel, `p` prints it, `w` writes and quits.

**Reading it left to right:** `o` is the "new empty DOS partition table" command. `p` confirms the new empty MBR. `w` commits.

**The story:** RHCSA expects you to drive this interactively. The heredoc here is for **reproducibility** in the lab. On the exam, type each letter at the prompt.

**Expected output (excerpt):**

```text
Welcome to fdisk (util-linux 2.37.4).
Changes will remain in memory only, until you decide to write them.
Be careful before using the write command.

Created a new DOS disklabel with disk identifier 0xabcd1234.

Command (m for help): Disk /dev/loop9: 1 GiB, ...
Disklabel type: dos

Command (m for help): The partition table has been altered.
Calling ioctl() to re-read partition table.
Syncing disks.
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Re-reading the partition table failed` | Run `sudo partprobe $LOOP_DEV` |
| `w` says "Device or resource busy" | Unmount partitions first |

---

### Task 4 — Print the empty table to baseline

```bash
cd /root/fdisk-mbr-lab

sudo fdisk -l "$LOOP_DEV" | tee 04-empty-mbr.txt
```

**The story:** Two `Disk` lines, a `Disklabel type: dos` line, and **no** Device rows. That is what an empty MBR looks like.

**Expected output:**

```text
Disk /dev/loop9: 1 GiB, 1073741824 bytes, 2097152 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0xabcd1234
```

---

### Task 5 — Create the first primary partition: 256 MiB Linux (`83`)

```bash
cd /root/fdisk-mbr-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 05-fdisk-create-p1.txt
n
p
1

+256M
p
w
EOF
```

**Human-Readable Breakdown:** Drive the new-primary-partition sequence step by step.

**Reading it left to right (each input line):**
- `n` — new partition
- `p` — primary (the default)
- `1` — partition number 1
- *(blank line)* — accept default first sector (2048)
- `+256M` — partition size 256 MiB
- `p` — print
- `w` — write

**The story:** The five-line sequence `n p 1 <enter> +256M` is the **muscle memory** of every RHCSA candidate. Practice this until you can type it without looking.

**Expected output (excerpt):**

```text
Command (m for help): n
Partition type
   p   primary (0 primary, 0 extended, 4 free)
   e   extended (container for logical partitions)
Select (default p): Partition number (1-4, default 1): First sector (2048-2097151, default 2048): Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-2097151, default 2097151): 

Created a new partition 1 of type 'Linux' and of size 256 MiB.

Command (m for help): Device       Boot Start    End Sectors  Size Id Type
/dev/loop9p1       2048 526335  524288  256M 83 Linux

Command (m for help): The partition table has been altered.
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Size is wrong | Reread the prompt: `+SIZE` (with `+`) not `SIZE` alone |
| Partition number rejected | Earlier partitions exist — adjust |

---

### Task 6 — Print to confirm

```bash
cd /root/fdisk-mbr-lab

sudo partprobe "$LOOP_DEV"
sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | tee 06-after-p1.txt
lsblk "$LOOP_DEV" | tee -a 06-after-p1.txt
```

**The story:** `partprobe` re-reads the partition table into the kernel; `udevadm settle` waits for udev events to finish. Without these, `lsblk` may not yet show the new partition.

**Expected output:**

```text
Disklabel type: dos
Device       Boot Start    End Sectors  Size Id Type
/dev/loop9p1       2048 526335  524288  256M 83 Linux
NAME      MAJ:MIN RM SIZE RO TYPE MOUNTPOINTS
loop9       7:9    0   1G  0 loop
└─loop9p1   259:5    0 256M  0 part
```

---

### Task 7 — Create partition 2 with a size in **sectors** instead

```bash
cd /root/fdisk-mbr-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 07-fdisk-create-p2.txt
n
p
2

+524288
p
w
EOF

sudo partprobe "$LOOP_DEV"
sudo udevadm settle
lsblk "$LOOP_DEV" | tee 07-after-p2.txt
```

**Human-Readable Breakdown:** Same `n p 2` sequence, but the size is specified as `+524288` (sectors, no `M/G` suffix). 524288 sectors × 512 B/sector = 256 MiB — identical size, different unit.

**The story:** Sector-based sizing matters when the exam phrases the question as "create a 524288-sector partition" (rare) or when you need to align with PE boundaries for LVM (Lab 115/123).

**Expected output:**

```text
Created a new partition 2 of type 'Linux' and of size 256 MiB.
/dev/loop9p2     526336 1050623  524288  256M 83 Linux
```

---

### Task 8 — Change partition 2's type to Linux swap (`82`) using `t`

```bash
cd /root/fdisk-mbr-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 08-fdisk-set-type.txt
t
2
82
p
w
EOF

sudo partprobe "$LOOP_DEV"
sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | tee 08-after-type-change.txt
```

**Human-Readable Breakdown:** Drive the type-change sequence: `t` → partition number → hex code.

**Reading it left to right:**
- `t` — change type
- `2` — partition number 2
- `82` — Linux swap

**The story:** RHCSA may say "create a swap partition." Two steps: `n p ... +SIZE` then `t N 82`. The type code does **not** activate swap — that requires `mkswap` + `swapon` (Lab 120). But the type marker tells future tools the intent.

**Expected output:**

```text
Command (m for help): t
Partition number (1,2, default 2): Hex code or alias (type L to list all): 82

Changed type of partition 'Linux' to 'Linux swap / Solaris'.

Command (m for help): /dev/loop9p2     526336 1050623  524288  256M 82 Linux swap / Solaris
```

---

### Task 9 — Verify, capture artifacts, and explore `l` (type list)

```bash
cd /root/fdisk-mbr-lab

sudo fdisk -l "$LOOP_DEV" | tee 09-final-table.txt
lsblk -f "$LOOP_DEV" | tee 09-lsblk-f.txt
sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | sed -n '/^Hex code/,/^$/p' | tee 09-type-list.txt
l
q
EOF
```

**Human-Readable Breakdown:** Final `fdisk -l`, `lsblk -f`, then a quick peek at the `l` (type list) inside fdisk and quit with `q`.

**The story:** The `l` menu lists every known partition type code with its name. Useful when you forget whether LVM is `8e` or `8a`.

**Expected output:**

```text
Device       Boot   Start     End Sectors  Size Id Type
/dev/loop9p1         2048  526335  524288  256M 83 Linux
/dev/loop9p2       526336 1050623  524288  256M 82 Linux swap / Solaris
NAME      FSTYPE FSVER LABEL UUID FSAVAIL FSUSE% MOUNTPOINTS
loop9
├─loop9p1
└─loop9p2
```

---

### Task 10 — Capstone: 2-partition report + cleanup

```bash
cd /root/fdisk-mbr-lab

P_COUNT=$(lsblk -no NAME "$LOOP_DEV" | grep -c "^loop9p" || true)
TABLE=$(sudo fdisk -l "$LOOP_DEV" | grep '^Disklabel type:')

cat > 10-report.txt <<EOF
MBR partition creation report — $(hostname) — $(date -Iseconds)

Loop device:           $LOOP_DEV
Backing file:          $LOOP_IMG
Partition table:       ${TABLE}
Number of partitions:  ${P_COUNT}

Layout (from fdisk -l):
$(sudo fdisk -l "$LOOP_DEV" | grep -E '^/dev/')

Source sequence:
  o            (new MBR)
  n p 1 <enter> +256M
  n p 2 <enter> +524288
  t 2 82       (swap)
  w
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"
losetup -a | grep "$LOOP_IMG" || echo "loop detached"

cd /root
rm -rf /root/fdisk-mbr-lab
exit
```

---

## 🔍 fdisk Decision Guide

```
"Create a partition"        → fdisk DEV → n p <num> <enter> +SIZE
"Delete a partition"        → fdisk DEV → d <num>
"Change type"               → fdisk DEV → t <num> <code>
"Toggle boot flag"          → fdisk DEV → a <num>
"Save changes"              → fdisk DEV → w
"Abort changes"             → fdisk DEV → q
"Tell kernel to rescan"     → partprobe DEV; udevadm settle
"Verify result"             → fdisk -l DEV; lsblk DEV
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Set up `losetup` loop device
- [ ] 02 Pre-flight `fdisk -l` baseline
- [ ] 03 `o` create MBR table
- [ ] 04 Print empty table
- [ ] 05 First primary `+256M` Linux (`83`)
- [ ] 06 `partprobe` + verify
- [ ] 07 Second primary by sector count
- [ ] 08 `t 2 82` swap type change
- [ ] 09 `l` type list + final verify
- [ ] 10 Report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot `+` before size | Partition uses absolute sector instead of size | Always `+1G`, `+256M` |
| `w` on the wrong device | Catastrophic data loss | Always confirm device path |
| No `partprobe` after write | `lsblk` doesn't show new partition | Always `partprobe DEV` |
| 5th primary attempt | "All primary partitions are in use" | Make one extended |
| Confusing MBR hex with GPT GUID | Wrong code | `83` MBR = `8300` GPT |
| Quitting with `q` thinking it saves | No changes applied | Use `w` |
| Setting type on non-existent partition | "Partition N does not exist" | Create first |
| Type `83` on swap | `swapon` fails | Use `82` for swap |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize the keystroke chain `n p <num> <enter> +SIZE w`. Practice on loop devices until automatic.

**RHCE candidate**
- Ansible `community.general.parted` does this idempotently: `parted: device=/dev/sdb number=1 part_type=primary part_start=1MiB part_end=257MiB state=present`.

**SRE / Platform interview**
- Be ready to explain why MBR caps at 2 TiB (32-bit LBA × 512 B sectors) and how GPT solves it.

**DevOps**
- CI base image: small `+200M` swap, then primary for `/` — fdisk script via `<<EOF` heredoc.

**AI / MLOps**
- NVMe scratch: single large primary, type `83`, then `mkfs.xfs` and mount.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 111 — Display Partition Tables | Read view; this lab is the write view |
| Lab 113 — Change Partition Types | Drills `t` independently |
| Lab 114 — GPT with `gdisk` | GPT counterpart |
| Lab 115 — `parted` | Script-friendly partitioning |
| Lab 116 — Format with XFS | Logical next step after partition |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
