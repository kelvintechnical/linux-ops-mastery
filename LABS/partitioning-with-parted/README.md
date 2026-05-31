# Lab: Command-Line Partitioning with `parted` — `mklabel`, `mkpart`, `set FLAG`, `name`, `resizepart`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** `parted` interactive vs `-s` (script) modes, `mklabel msdos`/`mklabel gpt` (create partition table), `mkpart PART-TYPE FS-TYPE START END` (one-line partition creation), units (`unit MiB`, `unit s`, `unit %`), partition alignment (`mkpart primary 1MiB 257MiB` for 1 MiB-aligned), flags (`set N boot|lvm|raid|esp on`), naming GPT partitions (`name N "Label"`), `rm N` to delete, `resizepart N END` (RHEL 9), `print` and `print free`, `align-check optimal N`, scriptable Ansible-friendly form, comparison with `fdisk` (`parted` is faster but less forgiving), the canonical pattern `parted -s DEV mklabel gpt mkpart primary 1MiB 257MiB set 1 esp on`
- **Career arcs covered:** RHCSA (EX200 — "use `parted` to create a 500 MiB LVM partition"), RHCE (Ansible `community.general.parted`), SRE (cloud-init partition shaping), DevOps (CI image partitioning), AI / MLOps (NVMe carving in startup scripts)
- **Prerequisite:** Labs 111–114 (display + fdisk + gdisk)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 sandbox + `mklabel` · Task 3 first `mkpart` with `MiB` units · Tasks 4–5 flags (`set N FLAG on`) and `name` · Task 6 multi-partition in one call · Task 7 `resizepart` · Task 8 `print free` · Task 9 alignment check · Task 10 capstone scripted multi-partition layout + cleanup

---

## Objective

Stop opening interactive editors when you don't need to. By the end of this lab you can use `parted -s DEV ...` to create, name, and flag partitions in a single command. You will also know when `parted` is the right tool (anytime you want a one-liner, anytime you want to set flags by name instead of hex codes) and when `fdisk`/`gdisk` is better (interactive RHCSA exam tasks, GPT GUID inspection).

The capstone is the engineer-realistic prompt: *"In one `parted -s` invocation per partition, build a 2 GiB GPT disk with a 256 MiB ESP (set `esp` flag), a 1 GiB Linux primary, and a 700 MiB LVM partition (set `lvm` flag). Verify with `parted print` and `lsblk -f`."*

> **Lab safety note:** Uses loopback files in `/var/tmp/` — safe on any RHEL 9 VM.

---

## Concept: `parted` Is Script-First

`parted` was designed from day one to be **non-interactive**. The shape `parted -s DEV SUBCOMMAND ARGS...` runs the subcommand and exits — no prompts. This is exactly what you want in:

- Ansible playbooks
- Kickstart `%post`
- CI images / cloud-init
- Quick one-liners on the exam

The interactive UI exists too (`parted /dev/X` drops you into a prompt) but RHCSA and RHCE prefer the script form.

```
   ┌──────────────────────────────────────────────────────────────┐
   │ parted -s DEV [unit UNIT] SUBCOMMAND ARGS...                  │
   │                                                              │
   │ Common subcommands:                                          │
   │   mklabel msdos|gpt          ← create partition table        │
   │   mkpart PART-TYPE FS START END                              │
   │   rm N                                                       │
   │   resizepart N END                                            │
   │   set N FLAG on|off          ← boot|lvm|raid|esp|...         │
   │   name N "Label"             ← GPT only                       │
   │   print, print free                                          │
   │   align-check optimal N                                       │
   │                                                              │
   │ Units:                                                       │
   │   parted -s DEV unit MiB ...   parted -s DEV unit s ...      │
   │   parted -s DEV unit %  ...    parted -s DEV unit B  ...     │
   └──────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Anything you can do interactively with `fdisk` or `gdisk`, you can do as a one-line `parted -s` command. Exam time loves one-liners.

---

## 📜 Why `parted` Exists — The Story

`parted` (Andrew Clausen, late 1990s) was created to do something **`fdisk` could not at the time**: edit existing partition tables (resize, move) without losing data, and write GPT tables. `fdisk` was MBR-only and read-modify-write through an interactive prompt; `parted` could grow ext2 partitions and rewrite tables non-interactively.

Today `fdisk` has caught up on GPT, and `parted` no longer does online resize of most filesystems. What remains is **`parted`'s scriptability** — the `-s` flag and the named-flag model (`set N boot on` instead of MBR hex `a 1`) make `parted` the natural Ansible / cloud-init choice.

> **The point of the story:** `parted` is the **script-friendly** partition tool. `fdisk` is interactive. Pick the right one for the moment.

---

## 👪 The `parted` Family

```
Modes
├── parted DEV               ← interactive
├── parted -s DEV SUB ARGS   ← script (no prompts)
└── parted -l                ← list all devices

Subcommands
├── mklabel msdos | gpt | bsd | mac | sun | loop
├── mkpart PART FS START END
│       PART = primary | extended | logical (MBR only)
│       FS   = ext4 | xfs | linux-swap | fat32 | ... (advisory only)
├── rm N
├── resizepart N END
├── set N FLAG state
│       FLAGs: boot, lvm, raid, esp, bios_grub, swap, lba, hidden, ...
├── name N "NAME"            ← GPT partition name
├── print, print all, print free
├── align-check optimal N
└── unit UNIT                ← change units globally

Helpers
├── partprobe DEV            ← rescan kernel
├── udevadm settle           ← wait for udev
└── lsblk -f, blkid          ← verify
```

### `parted` flag reference

| Flag | Effect |
|---|---|
| `boot` | MBR boot flag |
| `esp` | EFI System Partition (alias of `boot` on GPT) |
| `bios_grub` | BIOS boot partition (for GRUB on GPT/BIOS) |
| `lvm` | Type = Linux LVM |
| `raid` | Type = Linux RAID |
| `swap` | Type = Linux swap |
| `legacy_boot` | Legacy BIOS bootable (GPT) |
| `hidden` | Hide from boot menu |

---

## 📚 `parted` Reference Table

| Goal | Command | Notes |
|---|---|---|
| Create GPT | `parted -s DEV mklabel gpt` | Wipes table |
| Create MBR | `parted -s DEV mklabel msdos` | "msdos" = MBR |
| Add partition | `parted -s DEV mkpart PART FS START END` | One line |
| MBR primary | `parted -s DEV mkpart primary ext4 1MiB 257MiB` | |
| GPT generic | `parted -s DEV mkpart primary 1MiB 257MiB` | FS optional |
| ESP | `parted -s DEV mkpart ESP fat32 1MiB 257MiB && parted -s DEV set 1 esp on` | |
| LVM | `parted -s DEV mkpart primary 1MiB 100% && parted -s DEV set 1 lvm on` | |
| Delete | `parted -s DEV rm N` | |
| Resize | `parted -s DEV resizepart N 500MiB` | |
| Set flag | `parted -s DEV set N FLAG on/off` | |
| Name (GPT) | `parted -s DEV name N "Label"` | |
| Print | `parted -s DEV print` | |
| Print + free | `parted -s DEV print free` | Shows gaps |
| Alignment | `parted -s DEV align-check optimal N` | |
| Change unit | `parted -s DEV unit MiB print` | One-shot unit |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | EX200 also accepts `parted`. One-liners save exam time. |
| **RHCE candidate** | `community.general.parted` module is a 1:1 wrapper. |
| **SRE / Platform** | cloud-init `parted` step in `bootcmd`. |
| **DevOps** | Base AMI partition shaping. |
| **AI / MLOps** | NVMe carving in startup scripts. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up loop device

```bash
sudo -i
mkdir -p /root/parted-lab && cd /root/parted-lab

LOOP_IMG=/var/tmp/parted-lab.img
truncate -s 2G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "Loop device: $LOOP_DEV" | tee 01-loop.txt
```

---

### Task 2 — Create the GPT table

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" mklabel gpt
sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 02-empty-gpt.txt
```

**Reading it left to right:** `-s` = script mode. `mklabel gpt` creates an empty GPT partition table.

**Expected output:**

```text
Model: Loopback device (loop)
Disk /dev/loop9: 2147MB
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:

Number  Start  End  Size  File system  Name  Flags
```

---

### Task 3 — Create the first partition (256 MiB, FAT32, ESP)

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" mkpart primary fat32 1MiB 257MiB
sudo parted -s "$LOOP_DEV" set 1 esp on
sudo parted -s "$LOOP_DEV" name 1 "EFI System Partition"

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 03-esp.txt
```

**Human-Readable Breakdown:** Create partition 1 from 1 MiB to 257 MiB (256 MiB total), set the `esp` flag, give it a GPT name.

**Reading it left to right:**
- `mkpart primary fat32 1MiB 257MiB` — type primary, advisory FS fat32, START 1 MiB, END 257 MiB
- `set 1 esp on` — flag partition 1 as EFI System
- `name 1 "..."` — set the GPT partition name

**The story:** Three `parted -s` calls = three keystroke sequences in `gdisk`. RHCSA candidates love `parted` for this reason.

**Expected output:**

```text
Number  Start   End     Size    File system  Name                  Flags
 1      1049kB  269MB   268MB                EFI System Partition  esp
```

---

### Task 4 — Set the boot flag (alias on GPT)

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" set 1 boot on
sudo parted -s "$LOOP_DEV" print | tee 04-with-boot.txt
sudo parted -s "$LOOP_DEV" set 1 boot off
sudo parted -s "$LOOP_DEV" print | tee 04-without-boot.txt
```

**The story:** On GPT, the `boot` flag is an alias of `esp`. On MBR, `boot` is the classic active/bootable flag. RHCSA exam wording may say either; `parted` accepts both.

---

### Task 5 — Add a 1 GiB Linux primary partition

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" mkpart primary 257MiB 1281MiB
sudo parted -s "$LOOP_DEV" name 2 "Linux Root"

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 05-root.txt
```

**The story:** START = previous END for adjacent partitions. END − START = size. 1281 − 257 = 1024 MiB = 1 GiB.

**Expected output:**

```text
 2      269MB   1343MB  1074MB                Linux Root
```

---

### Task 6 — Create an LVM partition using `100%` (rest of disk)

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" mkpart primary 1281MiB 100%
sudo parted -s "$LOOP_DEV" set 3 lvm on
sudo parted -s "$LOOP_DEV" name 3 "Linux LVM PV"

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 06-lvm.txt
```

**The story:** `100%` as END means "use the rest of the disk." Useful when the exact tail sector doesn't matter. `set N lvm on` is the flag-based equivalent of `t N 8E00` in gdisk.

**Expected output:**

```text
 3      1343MB  2147MB  804MB                 Linux LVM PV          lvm
```

---

### Task 7 — Resize partition 2 to 1.5 GiB

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" rm 3
sudo parted -s "$LOOP_DEV" resizepart 2 1793MiB
sudo parted -s "$LOOP_DEV" mkpart primary 1793MiB 100%
sudo parted -s "$LOOP_DEV" set 3 lvm on
sudo parted -s "$LOOP_DEV" name 3 "Linux LVM PV"

sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 07-resized.txt
```

**The story:** `resizepart N END` changes the end of partition N — but only if partition N is **not followed** by another partition. So we delete partition 3, resize partition 2 to 1793 MiB, then re-create partition 3 starting at 1793 MiB. Without an existing filesystem the resize is trivial; with one you would also `xfs_growfs` or `resize2fs` (Lab 129).

**Expected output:**

```text
 2      269MB   1880MB  1611MB                Linux Root
 3      1880MB  2147MB  266MB                 Linux LVM PV          lvm
```

---

### Task 8 — `print free` to see gaps

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" rm 2
sudo parted -s "$LOOP_DEV" print free | tee 08-print-free.txt

# Restore partition 2 with the same name and label
sudo parted -s "$LOOP_DEV" mkpart primary 257MiB 1793MiB
sudo parted -s "$LOOP_DEV" name 2 "Linux Root"
sudo partprobe "$LOOP_DEV"; sudo udevadm settle
sudo parted -s "$LOOP_DEV" print | tee 08-after-restore.txt
```

**The story:** `print free` adds rows for every **gap** between partitions. Crucial when planning where to insert a new partition.

**Expected output (excerpt):**

```text
        17.4kB  1049kB  1031kB                                Free Space
 1      1049kB  269MB   268MB                EFI System Partition  esp
        269MB   1880MB  1611MB                                Free Space
 3      1880MB  2147MB  266MB                 Linux LVM PV          lvm
```

---

### Task 9 — Verify alignment

```bash
cd /root/parted-lab

sudo parted -s "$LOOP_DEV" align-check optimal 1 | tee 09-align-1.txt
sudo parted -s "$LOOP_DEV" align-check optimal 2 | tee 09-align-2.txt
sudo parted -s "$LOOP_DEV" align-check optimal 3 | tee 09-align-3.txt
```

**The story:** Modern SSDs and arrays benefit from partitions starting at **1 MiB-aligned** boundaries. `align-check optimal N` returns "1 aligned" or a number explaining the misalignment.

**Expected output:**

```text
1 aligned
2 aligned
3 aligned
```

---

### Task 10 — Capstone: scripted multi-partition layout + cleanup

**Task statement:** *"In one shell with `parted -s` calls only, build a 2 GiB GPT disk: 256 MiB ESP (`esp` flag), 1 GiB Linux primary, 700 MiB LVM (`lvm` flag). Verify."*

```bash
cd /root/parted-lab

CAP_IMG=/var/tmp/parted-capstone.img
truncate -s 2G "$CAP_IMG"
CAP_DEV=$(sudo losetup --find --show "$CAP_IMG")

sudo parted -s "$CAP_DEV" mklabel gpt
sudo parted -s "$CAP_DEV" mkpart primary fat32 1MiB 257MiB
sudo parted -s "$CAP_DEV" set 1 esp on
sudo parted -s "$CAP_DEV" name 1 "EFI System Partition"
sudo parted -s "$CAP_DEV" mkpart primary 257MiB 1281MiB
sudo parted -s "$CAP_DEV" name 2 "Linux Root"
sudo parted -s "$CAP_DEV" mkpart primary 1281MiB 1981MiB
sudo parted -s "$CAP_DEV" set 3 lvm on
sudo parted -s "$CAP_DEV" name 3 "Linux LVM PV"

sudo partprobe "$CAP_DEV"; sudo udevadm settle
sudo parted -s "$CAP_DEV" print | tee 10-final.txt
lsblk -f "$CAP_DEV" | tee 10-lsblk.txt

cat > 10-report.txt <<EOF
Parted scripted layout report — $(hostname) — $(date -Iseconds)

Loop devices:
  $LOOP_DEV (file: $LOOP_IMG)
  $CAP_DEV  (file: $CAP_IMG)

== Capstone layout ($CAP_DEV) ==
$(sudo parted -s "$CAP_DEV" print)

Reproducible script (used above):
  parted -s DEV mklabel gpt
  parted -s DEV mkpart primary fat32 1MiB 257MiB
  parted -s DEV set 1 esp on
  parted -s DEV name 1 "EFI System Partition"
  parted -s DEV mkpart primary 257MiB 1281MiB
  parted -s DEV name 2 "Linux Root"
  parted -s DEV mkpart primary 1281MiB 1981MiB
  parted -s DEV set 3 lvm on
  parted -s DEV name 3 "Linux LVM PV"
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$LOOP_DEV" "$CAP_DEV"
sudo rm -f "$LOOP_IMG" "$CAP_IMG"

cd /root
rm -rf /root/parted-lab
exit
```

---

## 🔍 `parted` Decision Guide

```
"Create a table"        → parted -s DEV mklabel gpt|msdos
"Add partition"         → parted -s DEV mkpart PART [FS] START END
"Set LVM"               → parted -s DEV set N lvm on
"ESP"                   → mkpart + set N esp on
"Boot (MBR)"            → set N boot on
"Resize"                → parted -s DEV resizepart N END
"Delete"                → parted -s DEV rm N
"Free space"            → parted -s DEV print free
"Alignment OK?"         → parted -s DEV align-check optimal N
"GPT name"              → parted -s DEV name N "Label"
"Use rest of disk"      → END = 100%
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Loop device
- [ ] 02 `mklabel gpt`
- [ ] 03 First partition + `set esp on` + `name`
- [ ] 04 boot vs esp alias
- [ ] 05 Linux primary
- [ ] 06 LVM with `100%` end
- [ ] 07 `resizepart` (with rm-then-recreate dance)
- [ ] 08 `print free` gaps
- [ ] 09 `align-check optimal`
- [ ] 10 Capstone scripted layout + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Bare `parted DEV` in script | Interactive prompts | Use `-s` |
| `mkpart primary 1 257` (no units) | Defaults to MiB sometimes; mismatches expected size | Always state units: `1MiB 257MiB` |
| Start at 1MiB not 0 | Aligned but uses 1 MiB more | Intentional — 1 MiB-aligned |
| Resize a partition with a partition after it | Fails | rm next, resize, recreate (Lab 129 covers FS too) |
| Set `lvm` flag and expect FS | No format applied | Run `pvcreate`/`mkfs` after |
| `mklabel msdos` on a 4 TiB disk | Cannot create partition >2 TiB | Use `gpt` |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- One-liner: `parted -s /dev/vdb mklabel gpt mkpart primary 1MiB 100% set 1 lvm on`.

**RHCE candidate**
- `community.general.parted: device=/dev/sdb number=1 part_start=1MiB part_end=257MiB flags=['esp']`.

**SRE / Platform interview**
- Be ready to explain alignment (1 MiB start) and why `100%` end is preferred over numeric end-of-disk.

**DevOps**
- `parted -s` is what cloud-init `bootcmd` uses.

**AI / MLOps**
- NVMe scratch: `parted -s /dev/nvme1n1 mklabel gpt mkpart primary 1MiB 100% set 1 lvm on` then `pvcreate /dev/nvme1n1p1`.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 111 — Display Partition Tables | Reading layouts |
| Lab 112 — fdisk MBR | Interactive twin |
| Lab 114 — gdisk GPT | Interactive twin |
| Lab 129 — Resize Filesystem | After `resizepart`, then grow FS |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
