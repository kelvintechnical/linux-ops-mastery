# Lab: Change Partition Types in `fdisk` — `t`, MBR Hex Codes, GPT GUID Aliases

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** the `t` command in interactive `fdisk` to change the partition type identifier, MBR hex codes (`83` Linux, `82` swap, `8e` LVM, `fd` RAID, `7` NTFS, `b` FAT32), GPT type GUIDs and their short aliases (`8300` Linux filesystem, `8200` Linux swap, `8E00` Linux LVM, `EF00` EFI System, `EF02` BIOS Boot, `FD00` Linux RAID), inside fdisk: `l` to list all codes, `L` (capital) for GPT, when type changes require kernel rescan, why the type byte is metadata-only (filesystem layout is not changed by `t`), the practical pattern "create with `83`, change to `8e` for LVM, then `pvcreate`", verifying with `fdisk -l` and `parted print`, programmatic alternatives (`sfdisk --part-type DEV N CODE`, `parted DEV set N lvm on`)
- **Career arcs covered:** RHCSA (EX200 — "set partition 3 to LVM"), RHCE (Ansible `community.general.parted: flags: lvm`), SRE (post-rescue partition repair), DevOps (CI image prep), AI / MLOps (carving GPU-host partitions before mdadm)
- **Prerequisite:** Lab 112 (Create MBR Partition with fdisk)
- **Time Estimate:** 25 to 35 minutes
- **Difficulty arc:** Tasks 1–2 sandbox (loop device with two partitions) · Tasks 3–4 interactive `t` for one partition · Tasks 5–6 `l` to list codes, change to LVM, RAID · Task 7 GPT type aliases (different syntax) · Task 8 non-interactive `sfdisk --part-type` · Task 9 cross-check with `parted` and `lsblk -f` · Task 10 capstone audit + cleanup

---

## Objective

Stop misremembering hex codes. By the end of this lab you can change a partition's type ID interactively (`t N CODE`) or non-interactively (`sfdisk --part-type DEV N CODE`), recall the **six** most-tested codes from memory, and prove the change took effect with `fdisk -l`, `parted print`, and `lsblk -f`. You will also know that changing a type does **not** change the filesystem on the partition — the type is metadata only.

The capstone is the engineer-realistic prompt: *"On a 2-partition MBR test disk, change partition 1 from Linux (`83`) to Linux LVM (`8e`) and partition 2 from Linux swap (`82`) to Linux RAID autodetect (`fd`). Verify with `fdisk -l` and `parted print`. Write a one-paragraph audit."*

> **Lab safety note:** Uses a loop device so the lab is safe on any RHEL 9 VM. The keystrokes apply identically to `/dev/vdb` or `/dev/sdc` on a real host.

---

## Concept: The Type Byte Is Metadata Only

Each MBR partition entry has a 1-byte **type field**. GPT entries have a 16-byte **type GUID**. Tools and bootloaders read the type to decide how to treat the partition:

- `mkfs.xfs` does not care about the type.
- `pvcreate` does not require type `8e`, but most documentation/IaC assumes it.
- LVM autodetection at boot does prefer type `8e`/`8E00`.
- `mdadm` autodetection uses `fd`/`FD00`.

**Changing the type does not reformat or move data.** `t` is purely metadata.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ Type byte is a label, not a filesystem                        │
   │   Partition with type 83 and an XFS filesystem → still XFS   │
   │   After `t 1 8e` → still XFS, but type is now LVM (mismatch) │
   │   To actually convert: `mkfs.xfs` (or `pvcreate`) AFTER `t`   │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** If you `t 1 8e` an XFS partition and then `pvcreate /dev/sdb1`, **pvcreate succeeds** and wipes the XFS magic. The mismatch in step 1 is harmless; the destructive step is `pvcreate`. RHCSA tests this sequence.

---

## 📜 The Type Byte — A 35-Year-Old Pattern — The Story

IBM PC DOS 2.0 (1983) introduced the MBR. Microsoft picked a 1-byte type field — 256 possible values — and gave each OS vendor a small slice. Linux got `83` (filesystem) and `82` (swap). LVM2 (Heinz Mauelshagen, ~2002) reserved `8e`. Linux RAID got `fd` from the autodetect era.

GPT (UEFI Forum, 2000s) chose **16-byte GUIDs** because Microsoft and Apple had run out of 1-byte values. `gdisk` introduced **short aliases** (`8300`, `8200`, `EF00`) so humans don't have to type the full GUID. `fdisk` (modern util-linux) maps both: on MBR disks, the prompt asks for a hex code; on GPT disks, the prompt accepts the gdisk-style short alias.

> **The point of the story:** The codes are arbitrary historical assignments. Memorize the six that matter (`83`, `82`, `8e`, `fd`, `EF00`, `8300`).

---

## 👪 Type-Change Tools

```
Interactive
└── fdisk DEV → t N CODE → w
    (works for both MBR and GPT, code style differs)

Non-interactive
├── sfdisk --part-type DEV N CODE       ← scriptable
├── parted DEV set N FLAG on            ← flag-based (boot, lvm, raid, esp)
└── parted DEV name N "Label"           ← GPT name only

Verify
├── fdisk -l DEV
├── parted DEV print
├── lsblk -f DEV                        ← filesystem unchanged
└── blkid DEV                            ← FS UUID/TYPE
```

### Top six codes to memorize

| MBR hex | GPT alias | Meaning |
|---|---|---|
| `83` | `8300` | Linux filesystem |
| `82` | `8200` | Linux swap |
| `8e` | `8E00` | Linux LVM |
| `fd` | `FD00` | Linux RAID autodetect |
| — | `EF00` | EFI System Partition (ESP) |
| — | `EF02` | BIOS Boot (for GRUB on GPT/BIOS) |

---

## 📚 Type-Change Reference Table

| Goal | Command | Notes |
|---|---|---|
| Interactive change (MBR) | `fdisk DEV` → `t N` → `83`/`82`/`8e`/... → `w` | Single byte hex |
| Interactive change (GPT) | `fdisk DEV` → `t N` → `8300`/`8200`/`8E00`/... → `w` | Short alias |
| List all codes (MBR) | inside fdisk: `l` | One screen |
| List all codes (GPT) | inside fdisk: `l` (modern util-linux shows GPT codes for GPT disks) | |
| Non-interactive | `sfdisk --part-type DEV N CODE` | Idempotent |
| Set LVM flag (parted) | `parted DEV set N lvm on` | Flag-based view |
| Set RAID flag | `parted DEV set N raid on` | |
| Set boot flag | `parted DEV set N boot on` / inside fdisk: `a N` | |
| Confirm | `fdisk -l DEV` / `parted DEV print` | |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 phrasing: "set partition 3 as Linux LVM." `fdisk → t 3 8e` is the answer. |
| **RHCE candidate** | Ansible: `community.general.parted: ... flags: ['lvm']`. |
| **SRE / Platform** | Rescue tickets where a partition shows the wrong type after image restore. |
| **DevOps** | CI image: small `EF00` ESP + `8300` root. |
| **AI / MLOps** | mdadm-managed NVMe carving via `fd`/`FD00`. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up loop device with 2 existing partitions

```bash
sudo -i
mkdir -p /root/parttype-lab && cd /root/parttype-lab

LOOP_IMG=/var/tmp/parttype-lab.img
truncate -s 1G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")

sudo fdisk "$LOOP_DEV" <<'EOF' >/dev/null 2>&1
o
n
p
1

+256M
n
p
2

+256M
w
EOF
sudo partprobe "$LOOP_DEV"
sudo udevadm settle
echo "Loop device: $LOOP_DEV" | tee 01-setup.txt
sudo fdisk -l "$LOOP_DEV" | tee -a 01-setup.txt
```

**The story:** Reproduce the Lab 112 end state (two `83` Linux primary partitions) so Lab 113 has a starting point.

**Expected output (excerpt):**

```text
Loop device: /dev/loop9
Disklabel type: dos
Device       Boot  Start    End Sectors  Size Id Type
/dev/loop9p1       2048 526335  524288  256M 83 Linux
/dev/loop9p2     526336 1050623  524288  256M 83 Linux
```

---

### Task 2 — Baseline: confirm both partitions are type `83`

```bash
cd /root/parttype-lab
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 02-types-before.txt
```

**The story:** Snapshot of the starting types. Every type-change task should record before/after.

**Expected output:**

```text
/dev/loop9p1       2048 526335  524288  256M 83 Linux
/dev/loop9p2     526336 1050623  524288  256M 83 Linux
```

---

### Task 3 — Change partition 1 to LVM (`8e`) interactively

```bash
cd /root/parttype-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 03-t-lvm.txt
t
1
8e
p
w
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 03-types-after-p1.txt
```

**Human-Readable Breakdown:** Drive `t` 1 8e to change partition 1's type to Linux LVM. Verify.

**Reading it left to right:**
- `t` — change type
- `1` — partition number 1
- `8e` — Linux LVM
- `p` — print
- `w` — write

**The story:** This is the **canonical** RHCSA keystroke chain for "set the LVM type." Memorize the four characters: `t 1 8e`.

**Expected output:**

```text
Command (m for help): t
Partition number (1,2, default 2): Hex code or alias (type L to list all): 8e

Changed type of partition 'Linux' to 'Linux LVM'.

/dev/loop9p1       2048 526335  524288  256M 8e Linux LVM
/dev/loop9p2     526336 1050623  524288  256M 83 Linux
```

---

### Task 4 — Inside `fdisk`, list every type with `l`

```bash
cd /root/parttype-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | sed -n '/^Hex code/,/^Command/p' | head -n 30 | tee 04-type-list.txt
l
q
EOF
```

**The story:** The `l` menu shows every type code. Useful reference when you forget a code on exam day.

**Expected output (excerpt):**

```text
Hex code or alias (type L to list all): 
 0  Empty           24  NEC DOS         81  Minix / old Lin bf  Solaris        
 1  FAT12           27  Hidden NTFS Win 82  Linux swap / So c1  DRDOS/sec (FAT-
 2  XENIX root      39  Plan 9          83  Linux           c4  DRDOS/sec (FAT-
 ...
 7  HPFS/NTFS/exFAT 4e  QNX4.x 3rd part 8e  Linux LVM       ef  EFI (FAT-12/16/
 8  AIX             50  OnTrack DM      93  Amoeba          fd  Linux raid auto
```

---

### Task 5 — Change partition 2 to Linux RAID autodetect (`fd`)

```bash
cd /root/parttype-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 05-t-raid.txt
t
2
fd
p
w
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 05-types-after-p2.txt
```

**The story:** `fd` is the legacy RAID autodetect code. Modern mdadm setups use `0xfd` so that the kernel's deprecated raid autodetect routines find the array — but mainstream practice now uses metadata (`mdadm.conf`) instead. The type is still useful as a label.

**Expected output:**

```text
Changed type of partition 'Linux' to 'Linux raid autodetect'.
/dev/loop9p1       2048 526335  524288  256M 8e Linux LVM
/dev/loop9p2     526336 1050623  524288  256M fd Linux raid autodetect
```

---

### Task 6 — Switch a partition to type `82` swap and back to `83`

```bash
cd /root/parttype-lab

sudo fdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 06-t-swap.txt
t
1
82
p
t
1
83
p
w
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 06-types-after-bounce.txt
```

**The story:** Type changes are reversible. Demonstrate by setting `82` (swap), printing, then setting `83` (filesystem) again, printing, write.

**Expected output:**

```text
/dev/loop9p1       2048 526335  524288  256M 82 Linux swap / Solaris
/dev/loop9p1       2048 526335  524288  256M 83 Linux
```

---

### Task 7 — GPT type aliases (different syntax)

```bash
cd /root/parttype-lab

GPT_IMG=/var/tmp/gpt-type-lab.img
truncate -s 512M "$GPT_IMG"
GPT_DEV=$(sudo losetup --find --show "$GPT_IMG")

sudo fdisk "$GPT_DEV" <<'EOF' >/dev/null 2>&1
g
n
1

+128M
n
2

+128M
w
EOF
sudo partprobe "$GPT_DEV"; sudo udevadm settle
sudo fdisk -l "$GPT_DEV" | tee 07-gpt-before.txt

sudo fdisk "$GPT_DEV" <<'EOF' 2>&1 | tee 07-gpt-set-types.txt
t
1
8E00
t
2
EF00
p
w
EOF
sudo partprobe "$GPT_DEV"; sudo udevadm settle
sudo fdisk -l "$GPT_DEV" | tee 07-gpt-after.txt

sudo losetup -d "$GPT_DEV"
sudo rm -f "$GPT_IMG"
```

**Human-Readable Breakdown:** Build a separate GPT loop device, partition it, then change types using GPT short aliases (`8E00` = Linux LVM, `EF00` = EFI System Partition).

**The story:** GPT does not use single-byte hex; it uses 16-byte GUIDs aliased to 4-hex shorthand. `8e` (MBR) ↔ `8E00` (GPT). RHCSA may give either format.

**Expected output (excerpt):**

```text
Created a new GPT disklabel
/dev/loop10p1   ...  Linux filesystem
/dev/loop10p2   ...  Linux filesystem
...
Changed type of partition 'Linux filesystem' to 'Linux LVM'.
Changed type of partition 'Linux filesystem' to 'EFI System'.
/dev/loop10p1   ...  Linux LVM
/dev/loop10p2   ...  EFI System
```

---

### Task 8 — Non-interactive: `sfdisk --part-type`

```bash
cd /root/parttype-lab

sudo sfdisk --part-type "$LOOP_DEV" 1 8e
sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 08-sfdisk-set.txt

sudo sfdisk --part-type "$LOOP_DEV" 1 83
sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo fdisk -l "$LOOP_DEV" | grep '^/dev/' | tee 08-sfdisk-reset.txt
```

**Human-Readable Breakdown:** Use `sfdisk --part-type DEV N CODE` to change types from the command line (no interactive prompt). Useful in Ansible `command:` blocks or kickstart `%post`.

**Reading it left to right:** `sfdisk --part-type` writes only the type byte without rebuilding the partition. Idempotent.

**The story:** RHCSA tests `fdisk`. RHCE / SRE prefer `sfdisk`. Know both.

**Expected output:**

```text
/dev/loop9p1       2048 526335  524288  256M 8e Linux LVM
/dev/loop9p1       2048 526335  524288  256M 83 Linux
```

---

### Task 9 — Cross-check with `parted` and `lsblk -f`

```bash
cd /root/parttype-lab

sudo parted "$LOOP_DEV" print | tee 09-parted-print.txt
lsblk -f "$LOOP_DEV" | tee 09-lsblk-f.txt
sudo blkid "$LOOP_DEV"* 2>/dev/null | tee 09-blkid.txt
```

**The story:** `parted print` shows the **flags** column (`lvm`, `raid`, `boot`, `esp`) instead of the hex code. `lsblk -f` shows the **filesystem** on the partition (unchanged by type changes). `blkid` is empty for partitions without filesystems.

**Expected output:**

```text
Number  Start   End     Size    Type     File system  Flags
 1      1049kB  269MB   268MB   primary               lvm
 2      269MB   538MB   268MB   primary               raid
```

---

### Task 10 — Capstone: audit + cleanup

```bash
cd /root/parttype-lab

BEFORE=$(cat 02-types-before.txt)
AFTER=$(sudo fdisk -l "$LOOP_DEV" | grep '^/dev/')

cat > 10-report.txt <<EOF
Partition type-change audit — $(hostname) — $(date -Iseconds)

Loop device: $LOOP_DEV  (file: $LOOP_IMG)

== Before ==
${BEFORE}

== After ==
${AFTER}

Interactive sequence (lab 113 canonical):
  fdisk $LOOP_DEV
    t   1   8e      (Linux LVM)
    t   2   fd      (Linux RAID autodetect)
    w
Non-interactive equivalent:
  sfdisk --part-type $LOOP_DEV 1 8e
  sfdisk --part-type $LOOP_DEV 2 fd
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"

cd /root
rm -rf /root/parttype-lab
exit
```

---

## 🔍 Type-Change Decision Guide

```
"Make this partition LVM"          → fdisk DEV → t N 8e         (MBR)
                                   → fdisk DEV → t N 8E00      (GPT)
"Make this partition swap"         → t N 82  / 8200
"Make this partition Linux FS"     → t N 83  / 8300
"Make this RAID autodetect"        → t N fd  / FD00
"EFI System Partition"             → t N EF00 (GPT only)
"BIOS Boot"                        → t N EF02 (GPT only)
"Script it"                        → sfdisk --part-type DEV N CODE
"View by flag instead of code"     → parted DEV print
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Sandbox with 2 primary partitions
- [ ] 02 Baseline `83 Linux` for both
- [ ] 03 `t 1 8e` → LVM
- [ ] 04 `l` list type codes
- [ ] 05 `t 2 fd` → RAID
- [ ] 06 Bounce `t 1 82` then `t 1 83`
- [ ] 07 GPT loop with `8E00` and `EF00`
- [ ] 08 `sfdisk --part-type` non-interactive
- [ ] 09 `parted print` flag view + `lsblk -f`
- [ ] 10 Audit + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot `w` | Change not persistent | Always end with `w` |
| MBR code on GPT (or vice versa) | Code rejected | `83` on MBR; `8300` on GPT |
| Expecting `t` to change FS | Filesystem unchanged | `t` is metadata only |
| `pvcreate` on non-`8e` partition | Works anyway, but autodetect later may not | Match type to use |
| `parted set N lvm on` thinking it's a type | parted uses flags, not hex codes | Cross-check `fdisk -l` |
| Typing `0x8e` instead of `8e` | Unknown code | Drop the `0x` |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize the six codes (`83`, `82`, `8e`, `fd`, `8300`, `EF00`).

**RHCE candidate**
- Ansible: `community.general.parted: device=/dev/sdb number=1 part_start=1MiB part_end=257MiB flags=['lvm']`.

**SRE / Platform interview**
- Be ready to explain that the type byte is **a label** the kernel and bootloaders consult for autodetection; it does not change the on-disk data.

**DevOps**
- `sfdisk --part-type` in a kickstart `%post` aligns CI image types in one line per partition.

**AI / MLOps**
- mdadm setup convention: type `fd` on each member partition, then `mdadm --create`.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 112 — Create MBR Partition | Provides the starting partitions |
| Lab 114 — Create GPT Partition | GPT counterpart |
| Lab 115 — `parted` | Flag-based view |
| Lab 121 — `pvcreate` LVM | Logical next step after `t 1 8e` |
| Lab 120 — Swap | After `t N 82`, then `mkswap`, `swapon` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
