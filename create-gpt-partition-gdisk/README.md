# Lab: Create a GPT Partition with `gdisk` — `o`, `n`, GUID Codes, `c` Name, `w`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `gdisk` (gptfdisk) as the GPT-native interactive partitioner, `o` to create a new empty GPT, `n` to add a partition with start/end and a 4-hex GPT type code (`8300`, `8200`, `8E00`, `EF00`, `EF02`, `FD00`), `+SIZE` and `+SECTORS` sizing forms, partition names with `c` (GPT-only naming, distinct from filesystem labels), `t` to change a type after creation, `p` to print, `i` to inspect a single partition (shows partition GUID and unique GUID), `w` to write, `q` to abort, the partition entry limit (128 by default), comparing the same operations in `fdisk` GPT mode, kernel rescan with `partprobe`/`udevadm settle`, validation with `gdisk -l`, `lsblk -f`, and `parted print`
- **Career arcs covered:** RHCSA (EX200 — "create a 1 GiB EFI System Partition"), RHCE (Ansible parted with `label: gpt`), SRE (UEFI / NVMe layouts), DevOps (CI cloud images use GPT), AI / MLOps (large NVMe partitions > 2 TiB)
- **Prerequisite:** Labs 111 (Display Partition Tables) and 112 (Create MBR Partition with `fdisk`)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 sandbox loop device · Task 3 `o` create empty GPT · Tasks 4–5 first partition with explicit size + type · Task 6 name with `c` · Task 7 change type with `t` after creation · Task 8 second partition with sector-form size · Task 9 `i` per-partition inspection · Task 10 capstone (3-partition GPT layout: BIOS Boot + EFI + Linux LVM, plus cleanup)

---

## Objective

Stop fearing GPT. By the end of this lab you can drive `gdisk` from `o` → `n` → number → first sector → `+SIZE` → 4-hex type code → `c` name → `w`, then verify with `gdisk -l`, `lsblk -f`, and `parted print`. You will also know how `gdisk` differs from `fdisk` (richer GPT output, partition-unique GUIDs, per-partition `i` inspection) and when each tool is the right choice.

The capstone is the engineer-realistic prompt: *"On a 2 GiB loopback test disk, create a GPT partition table with three partitions: 2 MiB BIOS Boot (`EF02`), 256 MiB EFI System (`EF00`, named `EFI System Partition`), and the remainder as Linux LVM (`8E00`). Verify and write a one-paragraph layout report."*

> **Lab safety note:** Uses a loop device so the lab is safe on any RHEL 9 VM. All keystrokes apply identically to `/dev/vdb` or `/dev/sdc` on real hosts.

---

## Concept: GPT — 128 Slots, GUIDs, Backup Header

GPT (GUID Partition Table) ships a few critical differences from MBR:

- **128 partition entries** by default (configurable up to several thousand).
- **GUIDs everywhere.** Each partition has both a *type GUID* (what kind of partition) and a *partition-unique GUID* (which specific partition).
- **Redundant headers.** A primary header at LBA 1 and a backup at the last LBA, so partition info survives single-sector damage.
- **No primary/extended distinction.** All entries are equal.
- **Protective MBR.** Sector 0 still has an MBR with a single `0xEE` partition spanning the disk, so legacy tools don't think the disk is empty and try to "fix" it.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ Sector 0:  Protective MBR (0xEE)                              │
   │ Sector 1:  GPT primary header                                 │
   │ Sector 2..N: 128 partition entries (each ~128 bytes)          │
   │ ... data ...                                                  │
   │ Last sector-1..(N): backup partition entries                  │
   │ Last sector:  GPT backup header                                │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Cloud images are universally GPT now. RHEL 9 anaconda installs default to GPT. If you cannot drive `gdisk`, you cannot inspect or modify any modern cloud or UEFI host.

---

## 📜 Why `gdisk` Exists — The Story

`fdisk` learned GPT in 2013 (util-linux 2.23). Before that, **`gdisk` (by Rod Smith, 2009)** was the only interactive tool that could read and write GPT cleanly on Linux. `gdisk` lives on for three reasons:

1. **GUI parity with `fdisk`.** Same `n`/`d`/`t`/`p`/`w` keystrokes — easy to switch.
2. **Native GPT output.** Shows partition unique GUID, type GUID, name field — `fdisk` shows only the type.
3. **Conversion utilities.** `sgdisk` (script-friendly) and `cgdisk` (curses GUI) cover all use cases.

RHEL 9 ships modern `fdisk` (GPT-capable) and `gdisk` side by side. RHCSA accepts either; exam wording sometimes points specifically at `gdisk`.

> **The point of the story:** `fdisk` works on GPT. `gdisk` is preferred when you need GPT-native output (GUIDs, names, partition info `i`).

---

## 👪 The `gdisk` Family

```
Interactive
├── gdisk /dev/DEV               ← UI similar to fdisk
└── cgdisk /dev/DEV              ← curses

Script-friendly
└── sgdisk /dev/DEV ...          ← non-interactive (used in kickstart)

Inspection
├── gdisk -l /dev/DEV            ← list partitions with GUIDs
├── sgdisk -p /dev/DEV           ← same as gdisk -l in script form
└── parted DEV print             ← cross-check

Inside gdisk
├── ?     help
├── o     new empty GPT
├── n     new partition
├── d     delete partition
├── t     set type code (4 hex)
├── c     set partition name
├── i     inspect one partition (GUIDs)
├── L     list type codes (capital L)
├── p     print
├── x     enter expert menu
├── w     write and quit
└── q     quit without saving
```

### Type code reference (GPT short aliases used by gdisk)

| Code | Meaning |
|---|---|
| `8300` | Linux filesystem |
| `8200` | Linux swap |
| `8E00` | Linux LVM |
| `FD00` | Linux RAID |
| `0700` | Microsoft basic data |
| `EF00` | EFI System Partition |
| `EF02` | BIOS Boot |
| `A500` | FreeBSD disklabel |

---

## 📚 gdisk Reference Table

| Goal | Inside gdisk | Notes |
|---|---|---|
| New GPT | `o` | Wipes existing partition table |
| New partition | `n` then number then start then `+SIZE` then `<TYPE>` | |
| Delete | `d` then number | |
| Change type | `t` then number then `<TYPE>` | |
| Name partition | `c` then number then name | GPT-only field |
| Inspect one partition | `i` then number | Shows GUIDs |
| List codes | `L` (capital) | All known GPT codes |
| Print table | `p` | Always before `w` |
| Write | `w` then `Y` | Confirms before commit |
| Quit | `q` | No save |
| Expert menu | `x` | Extra options (recover GPT, expand entries) |
| Inventory | `gdisk -l DEV` | |
| Scriptable | `sgdisk` | `sgdisk -n 1:0:+256M -t 1:8E00 DEV` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Create a 200 MiB EFI System Partition on /dev/vdb." `gdisk` keystroke chain. |
| **RHCE candidate** | `sgdisk -n N:0:+SIZE -t N:CODE` in Ansible `command:` blocks. |
| **SRE / Platform** | NVMe carving for cache / WAL / scratch with GPT. |
| **DevOps** | Cloud images (AWS, Azure, GCP) all use GPT — every CI image touches this. |
| **AI / MLOps** | GPU hosts >2 TiB scratch require GPT. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up loop device

```bash
sudo -i
mkdir -p /root/gdisk-lab && cd /root/gdisk-lab

which gdisk sgdisk || dnf install -y gdisk
LOOP_IMG=/var/tmp/gdisk-lab.img
truncate -s 2G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "Loop device: $LOOP_DEV" | tee 01-loop.txt
lsblk "$LOOP_DEV" | tee -a 01-loop.txt
```

**The story:** 2 GiB is big enough to demonstrate BIOS Boot + EFI + LVM partitions.

---

### Task 2 — Pre-flight baseline

```bash
cd /root/gdisk-lab
sudo gdisk -l "$LOOP_DEV" 2>&1 | tee 02-pre.txt
```

**The story:** Empty device — `gdisk` will create the protective MBR and the GPT header.

---

### Task 3 — Create empty GPT with `o`

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 03-create-gpt.txt
o
Y
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 03-after-gpt.txt
```

**Human-Readable Breakdown:** `o` creates a new empty GPT (confirm with `Y`), `p` prints, `w` writes (confirms with `Y`).

**Reading it left to right:**
- `o` — new empty GPT
- `Y` — confirm wipe of any existing table
- `p` — print
- `w` — write
- `Y` — confirm write

**The story:** Unlike `fdisk` which writes silently with `w`, `gdisk` confirms with `Y` because GPT writes destroy data. The double-confirm is a feature.

**Expected output (excerpt):**

```text
Partition table scan:
  MBR: not present
  BSD: not present
  APM: not present
  GPT: not present

Creating new GPT entries in memory.

Command (? for help): Number  Start (sector)    End (sector)  Size       Code  Name

Command (? for help): Final checks complete. About to write GPT data. THIS WILL OVERWRITE EXISTING
PARTITIONS!!

Do you want to proceed? (Y/N): The operation has completed successfully.
```

---

### Task 4 — First partition: BIOS Boot 2 MiB (`EF02`)

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 04-create-bios-boot.txt
n
1

+2M
EF02
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 04-after-bios-boot.txt
```

**Human-Readable Breakdown:** `n` → partition number 1 → accept default first sector → `+2M` size → `EF02` type → print → write.

**Reading it left to right (each input):**
- `n` — new
- `1` — partition number
- *(blank)* — accept default start sector (`2048`)
- `+2M` — 2 MiB size
- `EF02` — BIOS Boot

**The story:** BIOS Boot partitions are tiny (1-4 MiB), unformatted, and used by GRUB on GPT/BIOS systems to embed its core. They are not mounted.

**Expected output:**

```text
Created partition 1, type 'BIOS boot partition'.
Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048            6143   2.0 MiB     EF02  BIOS boot partition
```

---

### Task 5 — Second partition: EFI 256 MiB (`EF00`)

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 05-create-efi.txt
n
2

+256M
EF00
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 05-after-efi.txt
```

**The story:** EFI System Partition is the FAT-formatted mount that UEFI firmware looks for. RHEL anaconda creates one of ~600 MiB; cloud images often use 100-256 MiB.

**Expected output:**

```text
Created partition 2, type 'EFI System'.
Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048            6143   2.0 MiB     EF02  BIOS boot partition
   2            6144          530431   256.0 MiB   EF00  EFI System
```

---

### Task 6 — Name partition 2 with `c`

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 06-name-efi.txt
c
2
EFI System Partition
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 06-after-name.txt
```

**Human-Readable Breakdown:** `c` (change name) → 2 (partition) → name → print → write.

**The story:** GPT names are partition-table-level (visible in `gdisk -l` and `lsblk -o PARTLABEL`). They are **not** the same as filesystem labels (`mkfs -L`). Both can be set; both are useful.

**Expected output:**

```text
Enter name: 
Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048            6143   2.0 MiB     EF02  BIOS boot partition
   2            6144          530431   256.0 MiB   EF00  EFI System Partition
```

---

### Task 7 — Change a type after creation with `t`

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 07-t-change.txt
t
2
0700
p
t
2
EF00
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 07-after-t.txt
```

**The story:** Change EFI to Microsoft basic data (0700), print, change back to EFI (`EF00`). Demonstrates the `t` workflow and reversibility.

---

### Task 8 — Third partition: Linux LVM remainder (`8E00`)

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 08-create-lvm.txt
n
3


8E00
c
3
Linux LVM PV
p
w
Y
EOF

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo gdisk -l "$LOOP_DEV" | tee 08-after-lvm.txt
```

**Human-Readable Breakdown:** `n 3` with **both** start and end blank means "first available start" through "last available sector" — i.e., fill the rest of the disk. Type `8E00` LVM. Name `Linux LVM PV`.

**Reading it left to right:**
- `n` — new
- `3` — partition number
- *(blank)* — default first sector (right after partition 2)
- *(blank)* — default last sector (end of disk)
- `8E00` — Linux LVM
- `c 3 "Linux LVM PV"` — partition name

**The story:** "Use the rest of the disk" is the most common partition pattern. Two blank inputs do exactly that.

**Expected output:**

```text
Created partition 3, type 'Linux LVM'.
Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048            6143   2.0 MiB     EF02  BIOS boot partition
   2            6144          530431   256.0 MiB   EF00  EFI System Partition
   3          530432         4194270   1.7 GiB     8E00  Linux LVM PV
```

---

### Task 9 — Inspect each partition with `i`

```bash
cd /root/gdisk-lab

sudo gdisk "$LOOP_DEV" <<'EOF' 2>&1 | tee 09-inspect.txt
i
1
i
2
i
3
q
EOF
```

**The story:** `i N` prints everything about partition N: partition GUID, unique partition GUID, first/last sectors, attribute flags, and partition name. This is what `fdisk` does not show.

**Expected output (excerpt):**

```text
Partition GUID code: 21686148-6449-6E6F-744E-656564454649 (BIOS boot partition)
Partition unique GUID: 4D...
First sector: 2048 (at 1024.0 KiB)
Last sector: 6143 (at 3.0 MiB)
Partition size: 4096 sectors (2.0 MiB)
Attribute flags: 0000000000000000
Partition name: ''

Partition GUID code: C12A7328-F81F-11D2-BA4B-00A0C93EC93B (EFI System)
Partition name: 'EFI System Partition'

Partition GUID code: E6D6D379-F507-44C2-A23C-238F2A3DF928 (Linux LVM)
Partition name: 'Linux LVM PV'
```

---

### Task 10 — Capstone: 3-partition layout report + cleanup

```bash
cd /root/gdisk-lab

cat > 10-report.txt <<EOF
GPT partition creation report — $(hostname) — $(date -Iseconds)

Loop device: $LOOP_DEV (file: $LOOP_IMG)

== Final layout ==
$(sudo gdisk -l "$LOOP_DEV" | tail -n 10)

== gdisk sequence used (canonical) ==
  o Y                       (new GPT)
  n 1 <ent> +2M   EF02      (BIOS Boot)
  n 2 <ent> +256M EF00      (EFI System)
  c 2 "EFI System Partition"
  n 3 <ent> <ent> 8E00      (LVM PV)
  c 3 "Linux LVM PV"
  w Y

== Non-interactive (sgdisk) equivalent ==
  sgdisk -n 1:0:+2M     -t 1:EF02 -c 1:"BIOS boot partition" \$LOOP_DEV
  sgdisk -n 2:0:+256M   -t 2:EF00 -c 2:"EFI System Partition" \$LOOP_DEV
  sgdisk -n 3:0:0       -t 3:8E00 -c 3:"Linux LVM PV"          \$LOOP_DEV
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"

cd /root
rm -rf /root/gdisk-lab
exit
```

---

## 🔍 `gdisk` Decision Guide

```
"New GPT table"          → o Y
"New partition"          → n N <start> <end-or-+SIZE> <TYPE>
"Fill remainder"         → n N <ent> <ent> <TYPE>
"Change type"            → t N <TYPE>
"Set partition name"     → c N <NAME>
"Inspect one partition"  → i N
"List type codes"        → L (capital)
"Save and exit"          → w Y
"Abort"                  → q
"Non-interactive"        → sgdisk -n N:start:end -t N:CODE DEV
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Loop device setup
- [ ] 02 Pre-flight baseline
- [ ] 03 `o` create empty GPT
- [ ] 04 BIOS Boot 2 MiB `EF02`
- [ ] 05 EFI 256 MiB `EF00`
- [ ] 06 Name with `c`
- [ ] 07 `t` change type and revert
- [ ] 08 LVM remainder `8E00`
- [ ] 09 `i` per-partition GUID inspection
- [ ] 10 Capstone layout report + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Hex code instead of GPT alias | "Bad input" | Use 4-hex GPT code (`8E00` not `8e`) |
| Confusing partition name with FS label | Two different fields | Use `c` for name, `mkfs -L` for FS label |
| Forgetting `Y` after `w` | Changes not saved | Always confirm |
| `o` on a populated disk | Data lost | Confirm device path |
| BIOS Boot mounted | mount fails | BIOS Boot is unformatted |
| 5+ partitions with `fdisk` (MBR) | "All primary in use" | Use GPT — no primary/extended distinction |
| Using GPT on tiny disks | Wastes space | OK; GPT works on any size |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Create a 200 MiB EFI System Partition." `gdisk` → `n 1 <ent> +200M EF00` → `w Y`.

**RHCE candidate**
- `sgdisk` in kickstart `%post` or Ansible `command:` blocks is idempotent.

**SRE / Platform interview**
- Be ready to explain backup-header recovery (GPT auto-recovers if primary header is damaged via the backup at the end of the disk).

**DevOps**
- Cloud image partition layouts are all GPT — `sgdisk` scripts replay them.

**AI / MLOps**
- NVMe carving: a single `8E00` LVM partition on each NVMe, joined by `pvcreate` + `vgcreate` for striped scratch.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 111 — Display Partition Tables | Read view |
| Lab 112 — `fdisk` MBR | Comparable interactive UI |
| Lab 113 — Change Partition Types | Deep on `t` |
| Lab 115 — `parted` | Script-friendly partitioning |
| Lab 121 — `pvcreate` LVM | Next step after `8E00` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
