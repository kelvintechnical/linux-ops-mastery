# Lab: Display Partition Tables — `fdisk -l`, `parted -l`, `gdisk -l`, `lsblk`, `blkid`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `fdisk -l` (list partitions on every attached block device, MBR + GPT), `fdisk -l DEVICE` (one device), `parted -l` (parted's list view including GPT), `gdisk -l DEVICE` (GPT-specific viewer), `lsblk` for the device tree, `blkid` for filesystem UUID/LABEL/TYPE, distinguishing MBR (`Disklabel type: dos`) vs GPT (`Disklabel type: gpt`), reading partition type IDs (`83 Linux`, `8e Linux LVM`, `82 Linux swap`, `EF00 EFI System`), comparing cylinder/sector geometry, decoding `Start` / `End` / `Sectors` / `Size` / `Type` columns, identifying the system disk, dumping a sectors-only summary with `fdisk -s`, the diagnostic combo `lsblk -f && fdisk -l`
- **Career arcs covered:** RHCSA (EX200 — "list all partitions on this host"), RHCE (Ansible `parted` module read mode), SRE (capacity assessment before adding storage), DevOps (CI runner storage inventory), AI / MLOps (NVMe layout for dataset/cache partitions)
- **Prerequisite:** Lab 110
- **Time Estimate:** 25 to 35 minutes
- **Difficulty arc:** Tasks 1–2 baseline + `lsblk` · Task 3 `fdisk -l` all devices · Tasks 4–5 single-device + MBR vs GPT recognition · Task 6 `parted -l` · Task 7 `gdisk -l` · Task 8 `blkid` and `lsblk -f` correlation · Task 9 partition-type ID lookup · Task 10 capstone inventory + cleanup

---

## Objective

Stop guessing what's on the disks. By the end of this lab you can run **one command per tool** to inventory every partition on a host, identify which disks use MBR vs GPT, read partition type IDs, and produce a one-paragraph inventory citing exact partition counts and sizes. You will also learn to triangulate `fdisk -l`, `parted -l`, `lsblk`, and `blkid` — each shows different facets of the same truth.

The capstone is the engineer-realistic prompt: *"Inventory every block device on this host. For each disk, name the partition table type (MBR/GPT), list every partition with its size and type, and write a one-paragraph summary."*

> **Lab safety note:** This lab is **read-only**. None of the commands change a partition table; this lab pairs with Labs 112 (fdisk write) and 114 (gdisk write) for the change operations.

---

## Concept: Two Partition Tables — MBR (`dos`) and GPT

A block device must declare a **partition table** at sector 0. Two formats dominate:

- **MBR (a.k.a. `dos`)** — 1980s, 512-byte first sector, 4 primary partitions max (or 3 + 1 extended → many logical), up to ~2 TiB disks.
- **GPT** — 2000s UEFI-era, redundant headers at start and end, **up to 128 partitions by default**, addresses to ~9.4 ZiB.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ MBR (dos)                       GPT                           │
   │   Sector 0: 512 B               Sector 0: protective MBR      │
   │   4 primary partition slots     Sector 1: GPT header           │
   │   Optional extended → logicals  Sector 2..N: partition entries │
   │   Max disk ~2 TiB                Backup header at end          │
   │   Type IDs 1 byte hex (83, 82)  Type GUIDs (8300, EF00, 8E00)  │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** RHCSA exam may ask you to "convert MBR to GPT" or "list every GPT partition." Knowing how each is structured guides which tool to reach for: `fdisk` works on both, but `gdisk` is GPT-native and shows GUIDs cleanly.

---

## 📜 Why Three Listing Tools Exist — The Story

`fdisk` is the **classic** tool — originally MBR-only, gained GPT support in `util-linux` 2.23 (~2013). Today's `fdisk` happily prints both.

`parted` was created to handle GPT properly with a non-curses CLI that allowed scripted partition operations. `parted -l` is its inventory mode.

`gdisk` (a.k.a. `gptfdisk`) is the **GPT-specific** counterpart with a UI that mirrors classic `fdisk` interaction. RHCSA references both names because both are installed on many systems.

`lsblk` and `blkid` are not partition-table tools — they are block-device/filesystem inventory tools. Use them alongside `fdisk -l` for the complete picture: `fdisk -l` says "this is partition `/dev/sda1`, type 83, 1.0 GiB"; `lsblk -f` says "and that partition contains an XFS filesystem with UUID xxx mounted at `/boot`."

> **The point of the story:** Each tool has one strength. Use them together.

---

## 👪 The Partition-Table Inspection Family

```
Partition-table viewers
├── fdisk -l                  ← MBR + GPT
├── fdisk -l /dev/DEVICE      ← single device
├── parted -l                 ← parted's view
├── parted DEV print          ← single device
├── gdisk -l /dev/DEVICE      ← GPT specifically
└── sfdisk -d /dev/DEVICE     ← machine-readable dump

Block-device + FS viewers
├── lsblk                     ← tree
├── lsblk -f                  ← + FSTYPE / UUID / LABEL / MOUNTPOINT
├── blkid                     ← UUID/TYPE/LABEL per partition
└── /proc/partitions          ← kernel's own list

Sector and size helpers
├── fdisk -s /dev/sdXn        ← size in 1K blocks
├── blockdev --getsize64      ← size in bytes
└── cat /sys/block/*/size     ← raw sector counts
```

### Common partition type IDs

| Hex (MBR) | GUID prefix (GPT) | Meaning |
|---|---|---|
| `83` | `8300` (`0FC63DAF-8483-4772-8E79-3D69D8477DE4`) | Linux filesystem |
| `82` | `8200` (`0657FD6D-A4AB-43C4-84E5-0933C84B4F4F`) | Linux swap |
| `8e` | `8E00` (`E6D6D379-F507-44C2-A23C-238F2A3DF928`) | Linux LVM |
| `fd` | `FD00` (`A19D880F-05FC-4D3B-A006-743F0F84911E`) | Linux RAID |
| — | `EF00` (`C12A7328-F81F-11D2-BA4B-00A0C93EC93B`) | EFI System |
| — | `EF02` (`21686148-6449-6E6F-744E-656564454649`) | BIOS Boot |

---

## 📚 Display Reference Table

| Goal | Command | Notes |
|---|---|---|
| List every partition on every disk | `sudo fdisk -l` | The default first command |
| Same, one disk | `sudo fdisk -l /dev/sda` | Limit |
| parted overview | `sudo parted -l` | Includes GPT details |
| parted single | `sudo parted /dev/sda print` | Interactive subcommand |
| gdisk overview | `sudo gdisk -l /dev/sda` | GPT-focused |
| Block tree | `lsblk` | No FS info |
| Block tree + FS | `lsblk -f` | + FSTYPE / UUID / LABEL / MOUNTPOINT |
| Sizes only | `lsblk -o NAME,SIZE,TYPE,FSTYPE` | Custom |
| Partition UUIDs | `sudo blkid` | One line per FS-bearing partition |
| Size in bytes | `sudo blockdev --getsize64 /dev/sdXn` | Programmatic |
| Sectors | `cat /sys/block/sda/size` | Sector count |
| Kernel view | `cat /proc/partitions` | Major/minor + size |
| Machine-readable dump | `sudo sfdisk -d /dev/sda` | Use for backup |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200: "List partitions." `fdisk -l` is the answer. |
| **RHCE candidate** | Ansible: `parted` module in `state: info` mode does this programmatically. |
| **SRE / Platform** | Pre-resize audits — never resize without knowing the table type and free sectors. |
| **DevOps** | CI images frequently use a single partition layout — verify before deployment. |
| **AI / MLOps** | NVMe RAID0 caches need to know which devices and partitions are involved. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up the sandbox and capture the device tree

```bash
sudo -i
mkdir -p /root/parttable-lab && cd /root/parttable-lab

lsblk | tee 01-lsblk.txt
cat /proc/partitions | tee 01-proc-partitions.txt
```

**Human-Readable Breakdown:** Build the workspace and capture the block-device tree from two sources — `lsblk` (human) and `/proc/partitions` (kernel).

**The story:** `lsblk` is for humans; `/proc/partitions` is the kernel-truth source.

**Expected output:**

```text
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
nvme0n1     259:0    0   100G  0 disk
├─nvme0n1p1 259:1    0     1M  0 part
├─nvme0n1p2 259:2    0   1G    0 part /boot
├─nvme0n1p3 259:3    0   100G  0 part /var
├─nvme0n1p4 259:4    0   40G   0 part /
└─nvme0n1p5 259:5    0   500G  0 part /home
major minor  #blocks  name
259      0 104857600 nvme0n1
259      1     1024 nvme0n1p1
...
```

---

### Task 2 — `fdisk -l` for every device

```bash
cd /root/parttable-lab

sudo fdisk -l | tee 02-fdisk-l-all.txt | head -n 30
sudo fdisk -l 2>/dev/null | grep -E '^Disk /dev/' | tee 02-disks-only.txt
```

**Human-Readable Breakdown:** Run `fdisk -l` for every device; then pull out just the `Disk /dev/...` summary lines so you can count and identify each.

**Reading it left to right:** `fdisk -l` walks `/proc/partitions`. Output per device starts with `Disk /dev/X: SIZE` then a few summary lines (sector size, partition table type) and a table.

**The story:** This is the **first** command for any partition-inventory task. RHCSA may present a host with `/dev/vda` (the system disk) and `/dev/vdb` (an empty disk) — your job is to recognize both.

**Expected output (excerpt):**

```text
Disk /dev/nvme0n1: 100 GiB, 107374182400 bytes, 209715200 sectors
Disk model: Amazon Elastic Block Store
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: F1234ABC-...

Device          Start       End   Sectors  Size Type
/dev/nvme0n1p1   2048      4095      2048    1M BIOS boot
/dev/nvme0n1p2   4096   2101247   2097152    1G Linux filesystem
/dev/nvme0n1p3 2101248 211814399 209713152  100G Linux LVM
```

**Switches**

| Token | Meaning |
|---|---|
| `fdisk -l` | List all |
| `fdisk -l DEVICE` | One device |
| `fdisk -l -u` | Force sectors as units |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| "fdisk: cannot open ..." | Use `sudo` |
| Empty output | No disks attached |

---

### Task 3 — Single-device focus

```bash
cd /root/parttable-lab

SYSTEM_DISK=$(lsblk -no PKNAME $(findmnt -n -o SOURCE /))
[ -z "$SYSTEM_DISK" ] && SYSTEM_DISK=$(lsblk -dno NAME | head -n 1)
echo "System disk: /dev/$SYSTEM_DISK" | tee 03-system-disk.txt

sudo fdisk -l "/dev/$SYSTEM_DISK" | tee 03-system-disk-fdisk.txt
```

**Human-Readable Breakdown:** Identify the disk that hosts the root filesystem, then run `fdisk -l` on just that disk.

**Reading it left to right:** `findmnt -n -o SOURCE /` returns the device behind `/`. `lsblk -no PKNAME` returns the parent device of a partition (e.g., `/dev/nvme0n1p4` → `nvme0n1`). The fallback covers cases where root is on LVM.

**The story:** Knowing **which disk is the system disk** prevents disasters. Never `fdisk` the system disk without thinking.

---

### Task 4 — Recognize MBR vs GPT in `fdisk -l` output

```bash
cd /root/parttable-lab

sudo fdisk -l 2>/dev/null | grep -E 'Disk /dev|Disklabel type' | tee 04-disk-types.txt

GPT_DISKS=$(sudo fdisk -l 2>/dev/null | awk '/^Disk \/dev\// {d=$2} /Disklabel type: gpt/ {print d}' | tr -d ':')
MBR_DISKS=$(sudo fdisk -l 2>/dev/null | awk '/^Disk \/dev\// {d=$2} /Disklabel type: dos/ {print d}' | tr -d ':')
echo "GPT disks: ${GPT_DISKS:-(none)}" | tee 04-gpt-list.txt
echo "MBR disks: ${MBR_DISKS:-(none)}" | tee 04-mbr-list.txt
```

**Human-Readable Breakdown:** Walk `fdisk -l` output, capture every `Disk /dev/...` and the following `Disklabel type:`, and produce two lists.

**Reading it left to right:** `awk` remembers the last `Disk /dev/...` name in `d`, prints `d` when it sees `Disklabel type: gpt` (or `dos`). `tr -d ':'` removes the trailing colon.

**The story:** This is the **first decision** when you need to add or modify a partition: MBR uses `fdisk`, GPT can use `fdisk` or `gdisk`. The decision drives tool choice for Labs 112 and 114.

**Expected output:**

```text
Disk /dev/nvme0n1: 100 GiB, 107374182400 bytes, 209715200 sectors
Disklabel type: gpt
Disk /dev/vdb: 5 GiB, 5368709120 bytes, 10485760 sectors
Disklabel type: dos
GPT disks: /dev/nvme0n1
MBR disks: /dev/vdb
```

---

### Task 5 — Read the Type column for each partition

```bash
cd /root/parttable-lab

sudo fdisk -l 2>/dev/null | awk '/^Device/{flag=1; next} flag && /^$/{flag=0} flag' | tee 05-partition-rows.txt
sudo fdisk -l 2>/dev/null | grep -E '^/dev/' | awk '{print $1, $NF}' | tee 05-device-type-pairs.txt
```

**Human-Readable Breakdown:** Extract the partition rows (everything between the `Device` header and the next blank line), then a tighter view: device path + final column (which is Type on GPT-aware fdisk).

**The story:** The `Type` column distinguishes `Linux filesystem`, `Linux LVM`, `Linux swap`, `EFI System`, `BIOS boot`. Type guides next steps — `mkfs.xfs` for filesystem, `pvcreate` for LVM, `mkswap` for swap.

**Expected output:**

```text
Device          Start       End   Sectors  Size Type
/dev/nvme0n1p1   2048      4095      2048    1M BIOS boot
/dev/nvme0n1p2   4096   2101247   2097152    1G Linux filesystem
/dev/nvme0n1p3 2101248 211814399 209713152  100G Linux LVM
/dev/nvme0n1p1 BIOS
/dev/nvme0n1p2 filesystem
/dev/nvme0n1p3 LVM
```

---

### Task 6 — `parted -l` overview

```bash
cd /root/parttable-lab

sudo parted -l 2>/dev/null | tee 06-parted-l.txt | head -n 30
sudo parted -s /dev/$SYSTEM_DISK print 2>/dev/null | tee 06-parted-one.txt
```

**Human-Readable Breakdown:** Run `parted -l` for an overview; then `parted -s DEV print` for one device, in script mode.

**Reading it left to right:** `parted -l` lists every device and partition table. `-s` suppresses interactive prompts. `print` is a subcommand.

**The story:** `parted` shows the **partition flag** column (e.g., `boot`, `lvm`, `esp`), which `fdisk` does not. Useful for spotting the EFI System Partition or the boot flag on legacy MBR.

**Expected output:**

```text
Model: Amazon EBS NVMe Instance Storage (nvme)
Disk /dev/nvme0n1: 107GB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:

Number  Start   End     Size   File system  Name              Flags
 1      1049kB  2097kB  1049kB                                bios_grub
 2      2097kB  1076MB  1074MB xfs          /boot
 3      1076MB  108GB   107GB                                 lvm
```

**Switches**

| Token | Meaning |
|---|---|
| `parted -l` | List all |
| `parted -s` | Script mode |
| `parted DEV print` | One device |
| `parted DEV unit s print` | Sectors instead of bytes |

---

### Task 7 — `gdisk -l` for GPT details

```bash
cd /root/parttable-lab

if command -v gdisk >/dev/null 2>&1; then
  sudo gdisk -l /dev/$SYSTEM_DISK 2>/dev/null | tee 07-gdisk-l.txt
else
  echo "gdisk not installed — dnf install gdisk" | tee 07-gdisk-missing.txt
fi
```

**Human-Readable Breakdown:** Run `gdisk -l` if it exists; otherwise note the install command.

**Reading it left to right:** `gdisk -l DEV` prints the GPT header status, partition entries with their **GUID type codes**, sizes, partition names, and unique GUIDs. Far richer than `fdisk -l` for GPT.

**The story:** `gdisk` exposes the GPT-native fields `Partition unique GUID` and `Partition type GUID`. RHCSA may not test gdisk directly, but RHCE/SRE work often requires reading these.

**Expected output (excerpt):**

```text
GPT fdisk (gdisk) version 1.0.7

Partition table scan:
  MBR: protective
  BSD: not present
  APM: not present
  GPT: present

Found valid GPT with protective MBR; using GPT.
Disk /dev/nvme0n1: 209715200 sectors, 100.0 GiB
Model: Amazon Elastic Block Store
Sector size (logical/physical): 512/512 bytes
Disk identifier (GUID): F1234ABC-...
Partition table holds up to 128 entries
...
Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048            4095   1024.0 KiB  EF02  BIOS boot partition
   2            4096         2101247   1024.0 MiB  EF00  EFI System
   3         2101248       211814399   100.0  GiB  8E00  Linux LVM
```

---

### Task 8 — Correlate with `blkid` and `lsblk -f`

```bash
cd /root/parttable-lab

sudo blkid | tee 08-blkid.txt
lsblk -f | tee 08-lsblk-f.txt
```

**Human-Readable Breakdown:** Print every formatted partition's UUID, LABEL, TYPE — once with `blkid` (one line per device), once with `lsblk -f` (tree).

**The story:** A partition without a filesystem appears in `fdisk -l` but **not** in `blkid` (no FS) and not as a row with FSTYPE in `lsblk -f`. This is how you spot "raw" partitions waiting for `mkfs`.

**Expected output:**

```text
/dev/nvme0n1p2: UUID="e98a..." TYPE="xfs" PARTUUID="..." 
/dev/nvme0n1p3: UUID="d1234..." TYPE="LVM2_member" PARTUUID="..."
```

---

### Task 9 — Partition type ID reference and lookup

```bash
cd /root/parttable-lab

cat <<'EOF' | tee 09-type-ids.txt
MBR hex IDs (from 'fdisk' 't' menu)
  83  Linux filesystem
  82  Linux swap
  8e  Linux LVM
  fd  Linux RAID autodetect
  07  HPFS/NTFS/exFAT
  0b  W95 FAT32
  05/0f  Extended (legacy/LBA)

GPT GUIDs (short code in gdisk)
  0700  Microsoft basic data
  8200  Linux swap
  8300  Linux filesystem
  8E00  Linux LVM
  FD00  Linux RAID
  EF00  EFI System
  EF02  BIOS Boot
  A503  FreeBSD ZFS
EOF
cat 09-type-ids.txt
```

**Human-Readable Breakdown:** Save the table you'll consult repeatedly during partition creation labs.

**The story:** RHCSA may ask you to "set partition type to LVM" (which means hex `8e` in MBR or GUID code `8E00` in GPT). This table is your reference card.

---

### Task 10 — Capstone: full host partition inventory + cleanup

```bash
cd /root/parttable-lab

DISKS=$(lsblk -dno NAME)
> 10-inventory.txt
for D in $DISKS; do
  echo "== /dev/$D =="
  echo -n "  Disklabel: "
  sudo fdisk -l "/dev/$D" 2>/dev/null | grep -E '^Disklabel type:' | awk -F': ' '{print $2}' || echo "(none)"
  echo "  Size: $(lsblk -dno SIZE /dev/$D)"
  echo "  Partitions:"
  lsblk -no NAME,SIZE,TYPE,FSTYPE "/dev/$D" | awk 'NR>1' | sed 's/^/    /'
  echo
done | tee 10-inventory.txt

cat > 10-report.txt <<EOF
Partition inventory — $(hostname) — $(date -Iseconds)

$(cat 10-inventory.txt)

Source commands:
  lsblk -dno NAME
  fdisk -l DEV
  lsblk -no NAME,SIZE,TYPE,FSTYPE DEV
EOF

cat 10-report.txt
```

**Cleanup**

```bash
cd /root
rm -rf /root/parttable-lab
exit
```

---

## 🔍 Display Decision Guide

```
"Inventory all partitions"         → fdisk -l
"One specific disk"                → fdisk -l /dev/X
"What FS lives on each part?"      → lsblk -f / blkid
"Show partition flags (boot/esp)"  → parted -l
"GPT GUIDs and partition names"    → gdisk -l /dev/X
"Pure block tree"                  → lsblk
"Backup partition layout"          → sfdisk -d /dev/X > backup.txt
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 `lsblk` + `/proc/partitions`
- [ ] 02 `fdisk -l` all devices
- [ ] 03 Identify system disk
- [ ] 04 Classify MBR vs GPT
- [ ] 05 Extract partition Type column
- [ ] 06 `parted -l`
- [ ] 07 `gdisk -l`
- [ ] 08 `blkid` + `lsblk -f`
- [ ] 09 Type ID reference
- [ ] 10 Capstone inventory + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `fdisk -l` without sudo | "Permission denied" | Add `sudo` |
| Mistaking MBR Disklabel for GPT | Wrong tool for next step | Read the `Disklabel type:` line |
| Trusting `lsblk` alone for FS | LVM PVs not shown as FS | Use `blkid` |
| Forgetting `gdisk` lists GUIDs | Type ID confusion | Use gdisk for GPT detail |
| `parted` interactive prompts | Hangs in scripts | Use `-s` |
| Editing the wrong disk | Data loss | Always verify the device path |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- One command answer: `sudo fdisk -l`. Read the `Disklabel type:` line for table type.

**RHCE candidate**
- Ansible `parted` module reads layouts: `parted: device=/dev/sda state=info`.

**SRE / Platform interview**
- Be ready to explain why GPT is preferred for >2 TiB and for UEFI.

**DevOps**
- Pre-image audit: `sfdisk -d /dev/sda` to capture, `sfdisk /dev/sda < layout.txt` to replay.

**AI / MLOps**
- NVMe RAID layouts visible via `lsblk` + `mdadm --detail` — first know your partitions.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 110 — Inspect Filesystems | `df` + `findmnt` are the filesystem-level view |
| Lab 112 — Create MBR Partition with fdisk | Write operation that follows this read |
| Lab 114 — Create GPT Partition with gdisk | GPT write counterpart |
| Lab 115 — Partitioning with parted | Script-friendly partitioning |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
