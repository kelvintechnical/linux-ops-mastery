# Lab: Create LV `lvol1` (ext4, 280 MB) and Mount Persistently

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Subjects covered:** PV / VG / LV mental model, `pvcreate`, `vgcreate`, `lvcreate`, `mkfs.ext4`, `blkid`, UUID-based `/etc/fstab` entries, `mount -a`, `systemctl daemon-reload`, loopback devices for safe practice
**Career arcs covered:** RHCSA (Storage objective — guaranteed exam question), RHCE (Ansible `community.general.lvol` module), SRE (resizing root volumes without downtime), DevOps (thin-provisioned LVs for container storage drivers)
**Prerequisite:** Comfort with `lsblk`, `df -h`, `mount`, `/etc/fstab` basics
**Time Estimate:** 60 to 90 minutes
**Difficulty arc:** Tasks 1–5 foundation · 6–13 the PV→VG→LV→mount pipeline · 14–18 making it persistent and verified · 19–20 RHCSA exam-realistic capstone

---

## Objective

Build the **PV → VG → LV → filesystem → mount → fstab** muscle memory so you can answer any RHCSA storage question without reaching for documentation. By the end of this lab you can take an empty block device and turn it into a persistently-mounted ext4 filesystem in seven commands.

The capstone is the **RHCSA sample exam Task 12**: create a logical volume called `lvol1` of size 280 MB in volume group `vgtest`, format it ext4, and mount it persistently to `/mnt/mnt1`.

> **Lab safety note:** This lab uses **loopback devices** (`losetup` + a sparse file) instead of real disks, so you can practice the full PV/VG/LV pipeline on any RHEL VM — even one without an attached EBS volume. Every command transfers identically to a real `/dev/vdb` or `/dev/nvme1n1` when you do get an extra disk.

---

## Concept: LVM Is an Indirection Layer Between Disks and Filesystems

Without LVM, a filesystem lives directly on a partition. The partition's size is fixed at creation; resizing it later means unmounting, repartitioning, possibly destroying data, and rebooting.

With LVM, three new layers sit between the disk and the filesystem:

```
   ┌─────────────────────────────────────────────────────┐
   │  Filesystem (ext4 / xfs)        ← what users see    │
   ├─────────────────────────────────────────────────────┤
   │  Logical Volume (LV)            ← lvcreate          │  ┐
   ├─────────────────────────────────────────────────────┤  │ LVM
   │  Volume Group (VG)              ← vgcreate          │  │ layer
   ├─────────────────────────────────────────────────────┤  │
   │  Physical Volume (PV)           ← pvcreate          │  ┘
   ├─────────────────────────────────────────────────────┤
   │  Partition (/dev/sda3)          ← fdisk / parted    │
   ├─────────────────────────────────────────────────────┤
   │  Disk (/dev/sda)                ← the physical disk │
   └─────────────────────────────────────────────────────┘
```

Each LVM layer is a thin abstraction over the one below it:

- **PV (Physical Volume)** — a disk or partition marked "available for LVM" with a small metadata header.
- **VG (Volume Group)** — a *pool* of one or more PVs glued together. Conceptually a soft-disk of arbitrary size.
- **LV (Logical Volume)** — a slice carved out of the VG. *This* is where you put the filesystem.

Because the VG is a pool, **the LV can grow or shrink without touching the underlying disks**. That's the whole point.

> **Why this matters:** Every modern Linux installation uses LVM by default (RHEL, CentOS, Ubuntu Desktop, Fedora). When `/` runs out of space, you don't reinstall — you grow the LV and run `xfs_growfs` or `resize2fs`. Mastering LVM is what separates "I can install Linux" from "I can keep Linux running."

---

## 📜 Why LVM Exists — The Story

In 1994, Heinz Mauelshagen ported HP-UX's Logical Volume Manager to Linux. By 1999, LVM1 was shipping in the kernel. By 2002, LVM2 (still the version we use today) replaced it with the `device-mapper` driver — the same kernel subsystem that powers `dm-crypt`, `dm-cache`, `dm-thin`, and Docker's old `devicemapper` storage driver.

### The pain LVM was invented to solve

- **Fixed partitions.** Before LVM, `/var/log` and `/home` were sized at install time. Run out of space in `/var/log` and your only option was to repartition the disk — which meant booting from a rescue CD, hoping `parted` could shrink your `/home`, and praying nothing went wrong.
- **Cross-disk filesystems.** Pre-LVM, a single filesystem couldn't span multiple disks. If your data didn't fit on one disk, you sharded across mount points — `/data1`, `/data2`, `/data3` — and updated every script that touched them.
- **Snapshots.** Without LVM, "back up the database mid-transaction" meant stopping the database, taking a copy, and starting it again. With LVM snapshots, you freeze the LV's view of the world in milliseconds, take a leisurely backup, and discard the snapshot — *while the database keeps running.*
- **Online resizing.** Every grow/shrink required unmounting. With LVM + xfs/ext4's online growth support, you grow `/home` while users are logged into it.

### The killer feature most beginners miss: thin provisioning

Modern LVM2 supports **thin-provisioned LVs**: you can `lvcreate -V 1T --thin` a one-terabyte LV inside a 50 GB pool — and the LV reports as 1 TB to the filesystem, but only consumes blocks as they're written. This is the underlying technology for container storage drivers, hypervisor disk overcommit, and most "thin clones" features in commercial storage products.

### Why exam-day still drills the basics

RHCSA tests the **fundamentals** — `pvcreate` / `vgcreate` / `lvcreate` / `mkfs` / `mount` — because those are the muscle-memory commands you'll type once a week for the rest of your career. Snapshots and thin pools come later (RHCE-level, or vendor courses). Get the basics into your fingers and the rest is a `man` page away.

> **The point of the story:** Every storage decision in modern Linux — root-on-LVM, encrypted home, container thin pools, KVM disk images — assumes you understand the PV/VG/LV stack. The 30 minutes you spend on this lab buys you 30 years of "yeah, I can resize that for you" answers.

---

## 👪 The LVM Family — Who Lives There

LVM has more relatives than most admins realize.

### By layer

| Layer | Command family | What it represents |
|---|---|---|
| **PV** | `pvcreate`, `pvs`, `pvdisplay`, `pvscan`, `pvremove`, `pvmove` | A physical disk or partition prepared for LVM |
| **VG** | `vgcreate`, `vgs`, `vgdisplay`, `vgextend`, `vgreduce`, `vgremove` | A pool of one or more PVs |
| **LV** | `lvcreate`, `lvs`, `lvdisplay`, `lvextend`, `lvreduce`, `lvresize`, `lvremove`, `lvrename` | A slice of the VG that holds a filesystem |
| **PE / LE** | (no direct command; shown in `*display`) | Physical / Logical Extents — the atomic unit of LVM allocation (4 MiB by default) |

### By LV type

| Type | `lvcreate` flag | Behavior | Use case |
|---|---|---|---|
| **Linear** | (default) | Allocate sequential extents on one or more PVs | The plain-vanilla LV. *What we'll build today.* |
| **Striped** | `-i N` | Stripe data across N PVs RAID-0 style | Performance: parallelize I/O across disks |
| **Mirrored** | `-m N` | Maintain N+1 copies | Redundancy: tolerate disk failures |
| **Thin-provisioned** | `--thin --thinpool POOL --virtualsize SIZE` | Reports SIZE to filesystem; allocates extents on demand | Container storage, overcommit |
| **Snapshot** | `-s -L SIZE ORIGIN_LV` | Copy-on-write view of another LV at one moment | Backups, rollback testing |
| **Cache LV** | `--type cache` | Front a slow LV with a fast SSD LV | SSD acceleration for HDD storage |

### By filesystem layered on top

| Filesystem | mkfs command | Online grow | Online shrink | Default on RHEL |
|---|---|---|---|---|
| **ext4** | `mkfs.ext4` | ✅ via `resize2fs` | ✅ (requires unmount) | RHEL 6 and older — *what the exam often asks for* |
| **xfs** | `mkfs.xfs` | ✅ via `xfs_growfs` | ❌ never | RHEL 7+ default |
| **Btrfs** | `mkfs.btrfs` | ✅ | ✅ | Not on RHEL (removed in 8) |

> **The point of the family tree:** Every storage question on the exam reduces to *"which layer is this question about?"* A "resize the filesystem" question is mostly about the FS layer (`resize2fs` / `xfs_growfs`). A "make `/home` bigger" question is the LV layer (`lvextend`) followed by the FS layer. A "add a new disk to the existing pool" question is the VG layer (`vgextend`). Recognizing which layer the question lives at narrows your command choices instantly.

---

## 🔬 The Anatomy of `pvs` / `vgs` / `lvs` Output — In One Diagram

### What `pvs` shows you

```
$ pvs
  PV             VG       Fmt  Attr PSize    PFree
  /dev/loop0     vgtest   lvm2 a--  1020.00m 740.00m
  └─────┬────┘   └──┬─┘   └─┬┘ └┬┘ └───┬───┘ └──┬──┘
        │           │       │   │      │        │
        │           │       │   │      │        └─ Free space in the PV (not yet allocated to any LV)
        │           │       │   │      └─ Physical Volume size after metadata reserved
        │           │       │   └─ Attributes: a=allocatable, u=used, --=no special flags
        │           │       └─ Format: lvm2 (current); lvm1 is legacy
        │           └─ Volume Group this PV belongs to (empty if PV exists but isn't joined to a VG)
        └─ Physical Volume device path (a real disk, partition, or loopback)
```

### What `vgs` shows you

```
$ vgs
  VG     #PV #LV #SN Attr   VSize   VFree
  vgtest   1   1   0 wz--n- 1020.00m 740.00m
  └─┬─┘  └┬┘ └┬┘ └┬┘ └─┬──┘ └──┬──┘ └──┬──┘
    │     │   │   │    │       │       └─ Free extents (the VG's spare capacity)
    │     │   │   │    │       └─ Total VG size (sum of contained PVs minus metadata)
    │     │   │   │    └─ Attributes: w=writable, z=resizable, --=allocation policy, n=not clustered
    │     │   │   └─ Number of snapshots in this VG
    │     │   └─ Number of logical volumes carved out
    │     └─ Number of physical volumes pooled
    └─ Volume Group name
```

### What `lvs` shows you

```
$ lvs
  LV     VG     Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  lvol1  vgtest -wi-ao----  280.00m
  └─┬─┘  └─┬─┘  └────┬───┘ └──┬──┘
    │      │         │        └─ LV size
    │      │         └─ Attributes (10 chars). Position 1: type (-=linear, m=mirrored, s=snapshot, ...).
    │      │                       Position 5: state (a=active, --=inactive). Position 6: device (o=open=mounted).
    │      └─ Volume Group it lives in
    └─ Logical Volume name (gets a symlink at /dev/<VG>/<LV>)
```

> **Reading rule:** Always inspect bottom-up — `pvs` first to confirm the disks are visible to LVM, then `vgs` to confirm they're pooled, then `lvs` to confirm the slices are carved. Any storage bug becomes obvious once you find the *first* layer that's wrong.

---

## 📚 LVM Reference Table

| Task | Command | Notes |
|---|---|---|
| Initialize a disk for LVM | `pvcreate /dev/sdX` | The disk is no longer usable as a plain partition after this |
| Create a VG | `vgcreate VGNAME /dev/sdX` | One VG can contain multiple PVs |
| Add another disk to a VG | `vgextend VGNAME /dev/sdY` | Grow the pool |
| Create an LV by size | `lvcreate -L 280M -n LVNAME VGNAME` | `M` = MiB (1024² bytes), not MB |
| Create an LV by extent count | `lvcreate -l 70 -n LVNAME VGNAME` | 70 PEs × 4 MiB = 280 MiB |
| Create an LV using free space % | `lvcreate -l 100%FREE -n LVNAME VGNAME` | Common pattern for "use all remaining space" |
| Format ext4 | `mkfs.ext4 /dev/VGNAME/LVNAME` | Device path is `/dev/VG/LV` |
| Get UUID | `blkid /dev/VGNAME/LVNAME` | The UUID you'll paste into `/etc/fstab` |
| Persistent mount | `UUID=... /mnt/mnt1 ext4 defaults 0 0` in `/etc/fstab` | Then `mount -a` |
| Grow an LV | `lvextend -L +500M /dev/VG/LV` | Then `resize2fs /dev/VG/LV` for ext4 |
| Shrink an LV (ext4 only, with care) | unmount → `e2fsck -f` → `resize2fs SIZE` → `lvreduce` | xfs cannot shrink |
| Remove an LV | `lvremove /dev/VG/LV` | Unmount first |
| Tear down a VG | `vgremove VGNAME` | LVs must be removed first |
| Strip LVM metadata | `pvremove /dev/sdX` | Final step in cleanup |

> **Rule one of LVM:** Build top-down (PV → VG → LV → FS → mount), but **tear down bottom-up** (unmount → remove FS line in fstab → `lvremove` → `vgremove` → `pvremove`). Skip a step at teardown and you'll see weird "device busy" errors.

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | LVM is one of the highest-weighted Storage objectives on EX200. *"Create a 280 MB LV called lvol1 in vgtest, format ext4, mount persistently"* is the canonical exam phrasing. |
| **RHCE candidate** | The `community.general.lvg`, `community.general.lvol`, and `community.general.filesystem` Ansible modules automate this exact workflow. |
| **SRE / Platform** | "Root filesystem is 90% full" tickets always go to whoever can run `vgextend && lvextend && xfs_growfs` in under 60 seconds. |
| **DevOps** | Container storage drivers (`devicemapper`, `overlay2` with backing fs) often sit on thin-pool LVs. |
| **AI / MLOps** | Big checkpoint volumes, scratch space for distributed training, and model registry storage all live on LVM in most on-prem clusters. |

---

## 🔧 The 20 Tasks

> Each task is structured for maximum understanding, not just maximum typing. After the **Purpose** and the code, every task includes:
>
> - **Human-Readable Breakdown** — a conversational walkthrough of the whole snippet in one paragraph.
> - **Reading it left to right** — a token-by-token gloss so you can read every symbol like an English sentence.
> - **The story** — the *why* behind the pattern: when you'll reach for it in real ops work, what bug class it prevents.
> - **Analogy** — a one-line metaphor to anchor the concept in something physical.
> - **Expected output** — exactly what you should see in your terminal.
> - **Switches / Output decoded / Troubleshoot** — three small reference tables.

---

### Task 1 — Set up the lab workspace and confirm tooling

**Purpose:** Confirm you have root, an empty 1 GiB loopback file to play with, and the LVM toolchain installed.

```bash
sudo -i
dnf install -y lvm2 e2fsprogs util-linux
mkdir -p /root/lvm-lab && cd /root/lvm-lab
which pvcreate vgcreate lvcreate mkfs.ext4 blkid mount
```

**Human-Readable Breakdown:**
> "Become root for the whole lab. Make sure the three packages that supply our commands are installed: `lvm2` (the PV/VG/LV tools), `e2fsprogs` (the ext4 family), and `util-linux` (which provides `blkid`, `mount`, `losetup`, `lsblk`). Create a clean working directory under `/root`. Confirm every command we'll need is on the `PATH`."

**Reading it left to right:**
- `sudo -i` → "interactive root login shell."
- `dnf install -y lvm2 e2fsprogs util-linux` → "ensure all three packages; `-y` says yes to prompts."
- `mkdir -p /root/lvm-lab && cd /root/lvm-lab` → "workspace; `-p` won't error if it exists."
- `which pvcreate vgcreate ...` → "verify each binary has a real path on `$PATH`."

**The story:** Stock RHEL ships LVM tools by default, so `dnf install` is normally a no-op. But on minimal AWS RHEL AMIs and inside slim container images, `lvm2` is often absent. Five seconds of `which` upfront beats a confused "command not found" later. The `which` for multiple binaries at once is a great "did anything fail to install?" smoke test.

**Analogy:** A surgeon checking the tray for every instrument before scrubbing in. You don't notice the missing scalpel later — you notice it now.

**Expected output:**

```
/usr/sbin/pvcreate
/usr/sbin/vgcreate
/usr/sbin/lvcreate
/usr/sbin/mkfs.ext4
/usr/sbin/blkid
/usr/bin/mount
```

**Switches**

| Token | Meaning |
|---|---|
| `sudo -i` | Real root shell |
| `dnf install -y` | Install packages, no prompts |
| `which CMD1 CMD2 ...` | Print absolute paths of all listed binaries |

**Output decoded**

| Line | Meaning |
|---|---|
| Each command on its own line | Each binary is installed and on `$PATH` |
| Missing line | That command isn't installed; check `dnf install` errors |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Error: Unable to find a match: lvm2` | Bad repo config; check `dnf repolist` |
| `which: no pvcreate` | Add `/usr/sbin` to `$PATH` or use `sudo -i` (which already does) |

---

### Task 2 — Inspect existing storage

**Purpose:** Read the current PV/VG/LV state before changing anything. Always know the starting point.

```bash
lsblk
pvs
vgs
lvs
```

**Human-Readable Breakdown:**
> "Hey kernel, show me every block device — disks, partitions, mounts — in a tree. Hey LVM, list every Physical Volume, every Volume Group, every Logical Volume. These four commands together are the 'current state' baseline I'll come back to between every change."

**Reading it left to right:**
- `lsblk` → "tree of block devices: disk → partition → LV → mountpoint."
- `pvs` → "PV summary table (`pvdisplay` for verbose)."
- `vgs` → "VG summary table."
- `lvs` → "LV summary table."

**The story:** Every senior storage engineer runs this exact four-command sequence between every step. It's the heartbeat check — *"what state is the system in right now?"* — that prevents you from `vgcreate`-ing on top of an existing VG named the same thing, or `pvcreate`-ing the wrong disk because you misread `lsblk`. Burn it into muscle memory: `lsblk`, `pvs`, `vgs`, `lvs`, then do the thing.

**Analogy:** A pilot's pre-flight checklist read in order, every flight, even after 10,000 hours.

**Expected output (on a fresh RHEL VM):**

```
NAME          MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
nvme0n1       259:0    0   30G  0 disk
├─nvme0n1p1   259:1    0    1G  0 part /boot
└─nvme0n1p2   259:2    0   29G  0 part
  ├─rhel-root 253:0    0   26G  0 lvm  /
  └─rhel-swap 253:1    0    3G  0 lvm  [SWAP]

  PV             VG   Fmt  Attr PSize   PFree
  /dev/nvme0n1p2 rhel lvm2 a--  <29.00g    0

  VG   #PV #LV #SN Attr   VSize   VFree
  rhel   1   2   0 wz--n- <29.00g    0

  LV   VG   Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  root rhel -wi-ao---- <26.00g
  swap rhel -wi-ao----   3.00g
```

**Switches**

| Token | Meaning |
|---|---|
| `lsblk` | Tree view of block devices |
| `pvs` / `vgs` / `lvs` | Tabular summaries |

**Output decoded**

| Line | Meaning |
|---|---|
| `rhel-root` is an LV | Your root filesystem is already on LVM (RHEL default) |
| `PFree 0` on the existing PV | The root VG is fully consumed; we can't expand it without adding another PV |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `No volume groups found` | Either you have a non-LVM install, or the `lvm2` package wasn't loaded — re-run Task 1 |

---

### Task 3 — Create a loopback device to safely practice on

**Purpose:** Most lab VMs don't have a spare disk. A loopback device lets us pretend a file is a block device.

```bash
truncate -s 1G /root/lvm-lab/disk1.img
losetup -fP --show /root/lvm-lab/disk1.img
losetup -a
```

**Human-Readable Breakdown:**
> "Hey shell, create a sparse 1 GiB file called `disk1.img`. Hey kernel, find the first free loop device (`-f`), attach `disk1.img` to it, also scan it for partitions (`-P`), and print the loop device name you chose (`--show`). Then list all attached loop devices so I can confirm."

**Reading it left to right:**
- `truncate -s 1G FILE` → "create or grow a file to exactly the given size; on most filesystems this is *sparse* — no blocks consumed until written."
- `losetup -fP --show FILE` → "attach FILE to a loop device. `-f` = find the first free `/dev/loopN`; `-P` = re-read its partition table; `--show` = print the chosen device name."
- `losetup -a` → "list all active loopback associations."

**The story:** Loopback devices are an underrated superpower. They let you mock up disks, USB sticks, encrypted volumes, and partitioned drives entirely in software — perfect for labs, CI, and reproducing bug reports. Every Docker image you've ever built was layered atop loopback devices in some form. For RHCSA practice, they let you `pvcreate /dev/loop0` exactly the same way you'd `pvcreate /dev/sdb` on a real disk, and your commands transfer one-to-one to real hardware.

**Analogy:** A flight simulator. Same controls, same instruments, no risk of crashing a real airliner. Once you graduate to a real disk, every reflex transfers.

**Expected output:**

```
/dev/loop0
/dev/loop0: []: (/root/lvm-lab/disk1.img)
```

**Switches**

| Token | Meaning |
|---|---|
| `truncate -s SIZE FILE` | Create/resize a sparse file |
| `losetup -f` | Find the first free loop device |
| `losetup -P` | Re-read partition table after attach |
| `losetup --show` | Print the loop device name to stdout |
| `losetup -a` | List active loops |

**Output decoded**

| Line | Meaning |
|---|---|
| `/dev/loop0` | The loop device the kernel chose |
| `(/root/lvm-lab/disk1.img)` | The backing file |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `losetup: cannot find an unused loop device` | All loops in use; release one with `losetup -d /dev/loopN` |
| `Permission denied` writing the file | You're not root; rerun under `sudo -i` |

---

### Task 4 — Initialize the loopback as a Physical Volume

**Purpose:** Mark `/dev/loop0` as available for LVM.

```bash
pvcreate /dev/loop0
pvs
pvdisplay /dev/loop0
```

**Human-Readable Breakdown:**
> "Hey LVM, write your metadata header onto `/dev/loop0` so you know this device is fair game for your use. Then list all PVs to confirm the new entry. Finally print the verbose details for our specific PV — size, free space, UUID, all the metadata."

**Reading it left to right:**
- `pvcreate /dev/loop0` → "write LVM's PV header. From this moment on the device is owned by LVM, not by any partition table or filesystem."
- `pvs` → "table view to confirm `/dev/loop0` now appears as a PV (likely with empty `VG` column)."
- `pvdisplay /dev/loop0` → "verbose view: size, free space, allocatable status, UUID."

**The story:** `pvcreate` writes a small (~1 MiB) metadata header to the device. It does *not* erase the data; it just tells LVM "you may use this device." If the device already had a filesystem, `pvcreate` will warn you and ask for confirmation — that warning has saved more careers than any other LVM safety check. **Read the warnings before you confirm.** Wiping `/dev/sda` instead of `/dev/sdb` is how junior engineers become unemployed.

**Analogy:** Putting a "FOR LVM USE" sticker on a USB stick. The data underneath isn't gone yet, but you've told the OS *"this is my LVM scratch space now."*

**Expected output:**

```
  Physical volume "/dev/loop0" successfully created.

  PV             VG   Fmt  Attr PSize   PFree
  /dev/loop0          lvm2 ---   1.00g  1.00g
  /dev/nvme0n1p2 rhel lvm2 a--  <29.00g    0

  --- Physical volume ---
  PV Name               /dev/loop0
  VG Name
  PV Size               1.00 GiB
  Allocatable           NO
  PE Size               0
  Total PE              0
  Free PE               0
  Allocated PE          0
  PV UUID               6yPi8M-jL3w-…
```

**Switches**

| Token | Meaning |
|---|---|
| `pvcreate DEV` | Mark a device as available for LVM |
| `pvs` | Tabular PV list |
| `pvdisplay DEV` | Verbose PV details |

**Output decoded**

| Line | Meaning |
|---|---|
| `Allocatable: NO` | Correct *before* it joins a VG; turns to `yes` after `vgcreate` |
| `PE Size: 0`, `Total PE: 0` | Extents are configured by the VG, not the PV — empty until joined |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device /dev/loop0 not found` | Re-run Task 3; the loopback wasn't attached |
| `WARNING: ext4 signature detected` | Confirm only if you're *sure* the device is safe to wipe |

---

### Task 5 — Create the Volume Group `vgtest`

**Purpose:** Pool the PV into a named VG that we'll carve LVs out of.

```bash
vgcreate vgtest /dev/loop0
vgs
vgdisplay vgtest
```

**Human-Readable Breakdown:**
> "Hey LVM, create a Volume Group named `vgtest` and put `/dev/loop0` in it as the only PV. Then list all VGs to confirm. Then print the verbose details of `vgtest` — total size, free extents, PE size, UUID."

**Reading it left to right:**
- `vgcreate vgtest /dev/loop0` → "create a VG named `vgtest` using the listed PV(s). You can list multiple devices to pool them."
- `vgs` → "tabular VG list."
- `vgdisplay vgtest` → "verbose view."

**The story:** The VG is the **unit of LVM administration.** All your `lvcreate`, `lvextend`, and `lvremove` commands target an LV *inside a VG*. The VG abstracts away which physical disk(s) actually back the extents — that's how you can grow a VG by `vgextend vgtest /dev/loop1` and then `lvextend` an existing LV without anyone caring which disk the new space came from. Default Physical Extent (PE) size is 4 MiB, which means 280 MiB rounds to 70 PEs — a number you'll see in the next task.

**Analogy:** Pouring water from several bottles into one pitcher. After you pour, individual glasses you fill don't care which bottle the water came from.

**Expected output:**

```
  Volume group "vgtest" successfully created

  VG     #PV #LV #SN Attr   VSize    VFree
  rhel     1   2   0 wz--n- <29.00g     0
  vgtest   1   0   0 wz--n- 1020.00m 1020.00m

  --- Volume group ---
  VG Name               vgtest
  System ID
  Format                lvm2
  …
  VG Size               1020.00 MiB
  PE Size               4.00 MiB
  Total PE              255
  Alloc PE / Size       0 / 0
  Free  PE / Size       255 / 1020.00 MiB
  VG UUID               B2y4mF-…
```

**Switches**

| Token | Meaning |
|---|---|
| `vgcreate VG_NAME PVs...` | Make a new VG from one or more PVs |
| `-s SIZE` | Override default 4 MiB PE size (rare) |
| `vgs` / `vgdisplay` | Tabular / verbose VG views |

**Output decoded**

| Line | Meaning |
|---|---|
| `VG Size 1020.00 MiB` | A bit less than the 1024 MiB of `disk1.img` — the rest is LVM metadata |
| `PE Size 4.00 MiB` | Default; 280 MiB / 4 MiB = 70 extents (next task) |
| `Total PE 255` | Plenty of room for our 70-PE LV |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device /dev/loop0 excluded by a filter` | Pre-existing signature; `wipefs -a /dev/loop0` then retry |
| `VG name vgtest already exists` | Either reuse it or `vgremove vgtest` first (Task 19) |

---

### Task 6 — Create the Logical Volume `lvol1` of size 280 MiB

**Purpose:** The headline exam task. Slice 280 MiB out of `vgtest` and name it `lvol1`.

```bash
lvcreate -L 280M -n lvol1 vgtest
lvs
lvdisplay /dev/vgtest/lvol1
ls -l /dev/vgtest/lvol1
```

**Human-Readable Breakdown:**
> "Hey LVM, carve an LV out of the `vgtest` pool. Make it 280 MiB in size (`-L 280M`) and name it `lvol1` (`-n lvol1`). Then list all LVs to confirm. Then print the verbose details of `lvol1`. Finally list the device-mapper symlink at `/dev/vgtest/lvol1` to prove the device node exists."

**Reading it left to right:**
- `lvcreate` → "create-an-LV command."
- `-L 280M` → "size by absolute bytes; `M` = MiB. Alternative is `-l 70` for *extent count*. `M` (capital) here is base-2 MiB; lowercase `m` is also accepted."
- `-n lvol1` → "name the LV `lvol1`."
- `vgtest` → "the VG to carve it out of."
- `/dev/vgtest/lvol1` → "the device node systemd-udev created. Symlink to `/dev/dm-N`."

**The story:** `lvcreate` is the headline command — most exam questions test some variation of it. Three things to memorize: (1) **`-L` is size, `-l` is extents.** `-L 280M` and `-l 70` produce the same LV in our case (`70 × 4 MiB = 280 MiB`), but `-L` is more readable. (2) **`-n NAME` is the LV's name.** (3) **The VG is the last positional argument**, not a flag. The device node lives at *both* `/dev/<VG>/<LV>` (recommended) *and* `/dev/mapper/<VG>-<LV>` (the kernel's actual device-mapper name). Use the `/dev/<VG>/<LV>` path in every command; it's clearer and survives udev re-runs.

**Analogy:** Cutting a slice out of the pitcher of water you just poured. The slice has a name (`lvol1`), a size (280 mL), and lives inside the labeled pitcher (`vgtest`).

**Expected output:**

```
  Logical volume "lvol1" created.

  LV    VG     Attr       LSize   …
  root  rhel   -wi-ao---- <26.00g
  swap  rhel   -wi-ao----   3.00g
  lvol1 vgtest -wi-a-----  280.00m

  --- Logical volume ---
  LV Path                /dev/vgtest/lvol1
  LV Name                lvol1
  VG Name                vgtest
  LV UUID                qK4hMr-…
  LV Status              available
  LV Size                280.00 MiB
  Current LE             70
  …
lrwxrwxrwx. 1 root root 7 May 22 13:42 /dev/vgtest/lvol1 -> ../dm-2
```

**Switches**

| Token | Meaning |
|---|---|
| `lvcreate -L SIZE` | Size in absolute bytes (`M`, `G`, `T`) |
| `lvcreate -l COUNT` | Size in extents |
| `lvcreate -l 100%FREE` | Use all remaining free space in the VG |
| `lvcreate -n NAME` | Name the new LV |

**Output decoded**

| Line | Meaning |
|---|---|
| `LSize 280.00m` | Exactly the size we asked for |
| `Current LE 70` | 70 logical extents × 4 MiB = 280 MiB ✅ |
| `LV Path /dev/vgtest/lvol1` | The path you use in `mkfs.ext4` |
| `Attr -wi-a-----` | `w`=writable, `i`=inherited allocation policy, `a`=active. `o` (open) appears after `mount`. |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Volume group "vgtest" has insufficient free space` | Make the LV smaller, or `vgextend` to add another PV |
| `Logical volume "lvol1" already exists` | `lvremove /dev/vgtest/lvol1` then retry |

---

### Task 7 — Format the LV with ext4

**Purpose:** An LV is just a block device. The filesystem on top is what users actually see.

```bash
mkfs.ext4 -L lvol1 /dev/vgtest/lvol1
```

**Human-Readable Breakdown:**
> "Hey mkfs.ext4, format the block device at `/dev/vgtest/lvol1` as an ext4 filesystem, and give it the human-readable label `lvol1` so it'll show up nicely in `lsblk -f` and `blkid`. Print the parameters you chose so I can confirm size, block count, inode count."

**Reading it left to right:**
- `mkfs.ext4` → "ext4 filesystem builder."
- `-L lvol1` → "filesystem *label* (max 16 chars). Optional but useful — shows in `lsblk -f` and is usable in `/etc/fstab` as `LABEL=lvol1`."
- `/dev/vgtest/lvol1` → "the block device to format. **Double-check this path before pressing Enter** — `mkfs.ext4 /dev/sda` would wipe your root disk."

**The story:** Three rules with `mkfs`: (1) **There is no undo.** The command instantly destroys whatever was on the device. (2) **Use UUIDs in fstab, but labels in `lsblk -f` and human conversation.** Labels are mutable, UUIDs aren't — but UUIDs are 36 ugly hex characters and labels are short and meaningful. (3) **`mkfs.ext4` chooses sensible defaults** — 4 KiB blocks, inode-per-16-KiB, journal enabled. You almost never override these for general-purpose volumes.

**Analogy:** Painting the inside of the slice with ext4 so it can hold files. Pre-paint, the LV is a block device — just bare metal. Post-paint, it's a filesystem that knows about files and directories.

**Expected output:**

```
mke2fs 1.46.5 (30-Dec-2021)
Creating filesystem with 286720 1k blocks and 71680 inodes
Filesystem UUID: 1f8a3b5c-…-…-…-…
Superblock backups stored on blocks:
        8193, 24577, 40961, 57345, 73729, 204801, 221185
Allocating group tables: done
Writing inode tables: done
Creating journal (8192 blocks): done
Writing superblocks and filesystem accounting information: done
```

**Switches**

| Token | Meaning |
|---|---|
| `mkfs.ext4` | The ext4 formatter |
| `-L LABEL` | Set the filesystem label |
| `-N N` | Override inode count (rare; only for very-many-files workloads) |
| `-b SIZE` | Override block size (rare) |

**Output decoded**

| Line | Meaning |
|---|---|
| `286720 1k blocks` | 280 MiB ÷ 1 KiB block size = 286,720 blocks |
| `Filesystem UUID: …` | The string you'll paste into `/etc/fstab` (next tasks) |
| `Creating journal` | ext4 journals by default — survival across crashes |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `/dev/vgtest/lvol1 is mounted; will not make a filesystem here!` | Unmount first, or you're targeting the wrong device |
| `Found a dos partition table` | Pre-existing data; `wipefs -a` first if you're sure |

---

### Task 8 — Inspect the new filesystem

**Purpose:** Confirm the ext4 superblock looks sane before mounting.

```bash
blkid /dev/vgtest/lvol1
lsblk -f /dev/vgtest/lvol1
dumpe2fs -h /dev/vgtest/lvol1 2>/dev/null | head -20
```

**Human-Readable Breakdown:**
> "Hey kernel, tell me three things about the new filesystem on `/dev/vgtest/lvol1`: (1) the UUID via `blkid`, (2) the label and mount info via `lsblk -f`, and (3) the first 20 lines of the superblock dump via `dumpe2fs -h` — which includes block count, free blocks, inode count, and journal mode."

**Reading it left to right:**
- `blkid /dev/vgtest/lvol1` → "print the device's UUID, LABEL, and TYPE. Comes from the cache at `/run/blkid/blkid.tab` or by direct read."
- `lsblk -f /dev/vgtest/lvol1` → "block-device tree with FS info: NAME, FSTYPE, LABEL, UUID, MOUNTPOINTS."
- `dumpe2fs -h /dev/vgtest/lvol1` → "ext2/3/4 superblock dump; `-h` = header-only (skip the per-group detail)."
- `2>/dev/null` → "suppress the harmless `dumpe2fs: Couldn't find valid filesystem superblock` warnings from probing."

**The story:** Three commands, three angles on the same filesystem. `blkid` is the **fstab-prep workhorse** — you copy its UUID output straight into `/etc/fstab`. `lsblk -f` is the **at-a-glance** view that shows the FS tree of the whole system. `dumpe2fs -h` is the **deep-dive** for when something's wrong and you need the journal size, inode density, last-mount time, or feature flags. Use all three regularly.

**Analogy:** Three different X-rays of the same chest — frontal, side, and 3D reconstruction. Each one shows you something the others miss.

**Expected output:**

```
/dev/vgtest/lvol1: LABEL="lvol1" UUID="1f8a3b5c-…" BLOCK_SIZE="1024" TYPE="ext4"

NAME  FSTYPE FSVER LABEL UUID                                 FSAVAIL FSUSE% MOUNTPOINTS
lvol1 ext4   1.0   lvol1 1f8a3b5c-…

dumpe2fs 1.46.5 (30-Dec-2021)
Filesystem volume name:   lvol1
Last mounted on:          <not available>
Filesystem UUID:          1f8a3b5c-…
Filesystem magic number:  0xEF53
Filesystem revision #:    1 (dynamic)
Filesystem features:      has_journal ext_attr resize_inode dir_index filetype …
Filesystem flags:         signed_directory_hash
Default mount options:    user_xattr acl
Filesystem state:         clean
…
Block size:               1024
…
```

**Switches**

| Token | Meaning |
|---|---|
| `blkid DEV` | Print UUID, LABEL, TYPE |
| `lsblk -f DEV` | Tree view with FS columns |
| `dumpe2fs -h DEV` | Superblock header only |

**Output decoded**

| Field | Meaning |
|---|---|
| `UUID="..."` | The string you'll paste into `/etc/fstab` |
| `TYPE="ext4"` | The fstab `<fstype>` column will be `ext4` |
| `Filesystem state: clean` | Last unmount was orderly |
| `has_journal` | ext4 with journal (the default) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `blkid` shows nothing | `udevadm settle` then retry; cache hadn't refreshed |
| Wrong UUID in cache | `blkid -g` to flush cache |

---

### Task 9 — Create the mount point

**Purpose:** A mount point is just an empty directory. Make sure ours exists before mounting.

```bash
mkdir -p /mnt/mnt1
ls -ld /mnt/mnt1
```

**Human-Readable Breakdown:**
> "Hey shell, make sure the directory `/mnt/mnt1` exists. If parent directories are missing, create them too (`-p`). If it already exists, don't error. Then list it in long form to confirm it's an empty directory owned by root."

**Reading it left to right:**
- `mkdir -p /mnt/mnt1` → "create directory; `-p` = create parents as needed, don't error on existing."
- `ls -ld /mnt/mnt1` → "list the directory *itself* (`-d`) in long format, not its contents."

**The story:** Mounting a filesystem on top of a directory **hides** whatever was in that directory until you unmount. If you mount on a populated directory, the data underneath is invisible (and reappears on unmount). For safety, always mount on an empty directory you just made. The conventional path for "extra mounts unrelated to the OS hierarchy" is `/mnt/<something>` — exactly what the exam asks for.

**Analogy:** Setting up a transparent stage over a poker table. Once the stage is in place, you can't see the cards underneath. Take the stage down (`umount`) and they reappear.

**Expected output:**

```
drwxr-xr-x. 2 root root 6 May 22 13:51 /mnt/mnt1
```

**Switches**

| Token | Meaning |
|---|---|
| `mkdir -p` | Make directory + parents; no error if exists |
| `ls -ld` | Long listing of directory itself |

**Output decoded**

| Field | Meaning |
|---|---|
| `drwxr-xr-x` | Permissions: directory, root rwx, group r-x, other r-x |
| Size `6` | Empty directory (just `.` and `..` entries) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Permission denied` | You're not root |
| Pre-existing files in `/mnt/mnt1` | Move them out first, or pick a different mountpoint |

---

### Task 10 — Mount the LV manually (one-time test)

**Purpose:** Test the mount before persistence. If it fails here, fstab will fail at boot too.

```bash
mount /dev/vgtest/lvol1 /mnt/mnt1
mount | grep mnt1
df -h /mnt/mnt1
```

**Human-Readable Breakdown:**
> "Hey kernel, mount the block device `/dev/vgtest/lvol1` on the directory `/mnt/mnt1`. Then grep `mount`'s output to confirm the new entry. Then ask `df` how much human-readable space is on `/mnt/mnt1` to prove the mount is live."

**Reading it left to right:**
- `mount SRC DEST` → "ask the kernel to attach SRC's filesystem at DEST. Filesystem type is auto-detected via `blkid`."
- `mount` (no args) → "print every active mount."
- `\| grep mnt1` → "filter to ours."
- `df -h /mnt/mnt1` → "disk-free for that one path; `-h` = human units."

**The story:** Always test mounts manually before adding to fstab. A bad fstab entry can render the system unbootable — you boot, fstab is read, the bad entry fails, and emergency mode catches you. By rehearsing `mount /dev/vgtest/lvol1 /mnt/mnt1` first, you catch *every* bug (wrong device path, missing mount point, FS type mismatch) on your timescale instead of at boot.

**Analogy:** Test-driving a car around the block before pulling it onto the freeway. The mount-by-hand step is your block.

**Expected output:**

```
/dev/mapper/vgtest-lvol1 on /mnt/mnt1 type ext4 (rw,relatime,seclabel)

Filesystem               Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 252M   24K  234M   1% /mnt/mnt1
```

**Switches**

| Token | Meaning |
|---|---|
| `mount SRC DEST` | One-shot mount |
| `mount` | List active mounts |
| `df -h` | Human-readable disk usage |

**Output decoded**

| Field | Meaning |
|---|---|
| `/dev/mapper/vgtest-lvol1` | Kernel's actual device-mapper name (symlinked from `/dev/vgtest/lvol1`) |
| `type ext4` | Auto-detected filesystem type |
| `(rw,relatime,seclabel)` | Mount options: read-write, relative-atime, SELinux labels enabled |
| `Size 252M` | A bit less than 280 MiB — reserved blocks + journal |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount: /mnt/mnt1: special device /dev/vgtest/lvol1 does not exist` | Forgot `lvcreate` (Task 6), or wrong VG/LV name |
| `wrong fs type, bad option, bad superblock` | Forgot `mkfs.ext4` (Task 7) |
| `/mnt/mnt1: mount point does not exist` | Forgot `mkdir -p` (Task 9) |

---

### Task 11 — Capture the UUID for `/etc/fstab`

**Purpose:** Persistent mounts should reference UUIDs, not device paths. Pull the UUID into a variable for the next task.

```bash
UUID=$(blkid -s UUID -o value /dev/vgtest/lvol1)
echo "UUID is: $UUID"
```

**Human-Readable Breakdown:**
> "Hey `blkid`, print just the UUID *value* (no `UUID=` prefix, no quotes) of `/dev/vgtest/lvol1`. Stuff that string into a shell variable called `UUID`. Then echo it so I can see it before I paste it into the next command."

**Reading it left to right:**
- `blkid` → "block-id probe."
- `-s UUID` → "print only the `UUID` tag (skip `TYPE`, `LABEL`, etc.)."
- `-o value` → "output format = just the value, no `KEY=` wrapper."
- `/dev/vgtest/lvol1` → "the device to probe."
- `UUID=$(...)` → "shell command substitution; assign the captured stdout to the variable `UUID`."

**The story:** **UUIDs over device paths in fstab.** Device paths like `/dev/sdb1` can change between reboots when disks are added/removed — and the boot will fail with "can't find /dev/sdb1" if the kernel renumbers. UUIDs are baked into the filesystem itself and survive every reorder. The exam grader will accept either, but real production always uses UUIDs. The `blkid -s UUID -o value` trick produces a clean, unquoted UUID perfect for piping into `sed` or `printf`-ing into a fstab line.

**Analogy:** Like phone contacts — you don't call your contacts by phone number, you call them by name (the UUID), because phone numbers (device paths) might change.

**Expected output:**

```
UUID is: 1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7
```

**Switches**

| Token | Meaning |
|---|---|
| `blkid -s TAG` | Only output the given tag |
| `blkid -o value` | Bare value, no `KEY=` |
| `$(CMD)` | Shell substitution: replace with stdout of CMD |

**Output decoded**

| Output | Meaning |
|---|---|
| 36-char hex string with dashes | A standard RFC 4122 UUID |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Empty `$UUID` | Filesystem not formatted (Task 7) or device wrong |
| Different UUID after re-mkfs | Each `mkfs.ext4` invocation generates a new UUID; re-pull it |

---

### Task 12 — Add the persistent mount line to `/etc/fstab`

**Purpose:** Make the mount survive reboots.

```bash
umount /mnt/mnt1
echo "UUID=$UUID  /mnt/mnt1  ext4  defaults  0 0" | tee -a /etc/fstab
tail -1 /etc/fstab
```

**Human-Readable Breakdown:**
> "First unmount the manual mount from Task 10 — we want to remount via fstab to prove fstab works. Then write a new line into `/etc/fstab` with six tab-separated fields: the UUID, the mountpoint `/mnt/mnt1`, the filesystem type `ext4`, default options, no dump backup (`0`), no fsck pass priority (`0`). Use `tee -a` to append. Print the last line of fstab to confirm."

**Reading it left to right:**
- `umount /mnt/mnt1` → "unmount so we can re-mount via fstab and prove fstab is working."
- `echo "UUID=$UUID  /mnt/mnt1  ext4  defaults  0 0"` → "construct the fstab line. **Six fields** separated by whitespace."
- `\| tee -a /etc/fstab` → "append to fstab (`tee -a`) **and** print to stdout simultaneously. Cleaner than `>>` because you see what got written."
- `tail -1 /etc/fstab` → "echo back the last line as a sanity check."

**The story:** The six fstab fields, in order: **device** (UUID/LABEL/path), **mountpoint**, **fstype**, **options**, **dump** (always `0` on modern systems — `dump` is dead), **fsck pass** (`0` for "skip fsck at boot"; `1` is root only; `2` for non-root filesystems you want fsck'd). For most exam answers, `defaults 0 0` is the safe bet. The `defaults` keyword is shorthand for `rw,suid,dev,exec,auto,nouser,async` — exactly what you want for a general filesystem.

**Analogy:** Adding a reservation to a calendar. The reservation says *at boot, mount this filesystem on this directory with these options*. fstab is read every boot.

**Expected output:**

```
UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
```

(Two copies — `tee` prints once to stdout, then we `tail -1` to confirm the appended line.)

**Switches**

| Token | Meaning |
|---|---|
| `umount` | Detach filesystem |
| `echo "..." \| tee -a FILE` | Append to file + echo to stdout |
| `tail -1` | Last line of a file |

**Output decoded**

| Field | Meaning |
|---|---|
| `UUID=...` | Filesystem identifier (preferred over device path) |
| `/mnt/mnt1` | Mountpoint |
| `ext4` | Filesystem type |
| `defaults` | `rw,suid,dev,exec,auto,nouser,async` |
| `0` (dump) | Skip backup (dump is obsolete) |
| `0` (pass) | Skip fsck at boot for non-root FS |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `umount: target is busy` | Some process has a file open on `/mnt/mnt1`; `lsof +D /mnt/mnt1` to find it |
| `Permission denied` writing fstab | Not root |

---

### Task 13 — Test fstab with `mount -a` *before* rebooting

**Purpose:** A broken fstab line can prevent boot. **Always test with `mount -a` before rebooting.**

```bash
mount -a
mount | grep mnt1
df -h /mnt/mnt1
```

**Human-Readable Breakdown:**
> "Hey kernel, walk through `/etc/fstab` and mount every entry that's not already mounted. If my new line is broken, `mount -a` will fail right now — on the command line — not at next boot when I'm staring at an emergency-mode prompt. Then confirm with `mount` and `df -h`."

**Reading it left to right:**
- `mount -a` → "mount *all* fstab entries with `auto` in their options (which `defaults` includes)."
- `mount | grep mnt1` → "confirm our LV is now mounted."
- `df -h /mnt/mnt1` → "size check."

**The story:** **`mount -a` is the seatbelt of fstab editing.** Every senior admin runs it immediately after touching fstab. If the line is wrong — typo in UUID, wrong filesystem type, missing mountpoint — `mount -a` fails *with a clear error* on your terminal. You fix the fstab and reboot with confidence. Skip this step and you'll find out at boot, when the system drops into emergency mode and you have to remember the root password.

**Analogy:** Pulling on the parking brake before driving away. Five seconds; saves a fender-bender.

**Expected output:**

```
/dev/mapper/vgtest-lvol1 on /mnt/mnt1 type ext4 (rw,relatime,seclabel)

Filesystem               Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 252M   24K  234M   1% /mnt/mnt1
```

**Switches**

| Token | Meaning |
|---|---|
| `mount -a` | Mount all `auto` fstab entries |
| `mount` | List active mounts |
| `df -h PATH` | Disk-free for a path |

**Output decoded**

| Line | Meaning |
|---|---|
| Mount entry present | fstab line was parsed and the mount succeeded |
| `Size 252M` | Same as before — same filesystem, just mounted via fstab now |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount: /mnt/mnt1: can't find UUID=...` | UUID typo in fstab; re-pull with Task 11 and re-edit |
| `mount: bad option` | Typo in the options column |
| `wrong fs type` | Wrong type in fstab (e.g. wrote `xfs` instead of `ext4`) |

---

### Task 14 — Confirm `systemctl daemon-reload` after fstab edits

**Purpose:** systemd generates `.mount` units from fstab. After editing fstab, ask systemd to regenerate.

```bash
systemctl daemon-reload
systemctl status mnt-mnt1.mount --no-pager
```

**Human-Readable Breakdown:**
> "Hey systemd, re-scan fstab and regenerate the `.mount` units you build from it. Then show me the status of `mnt-mnt1.mount` (the unit that corresponds to `/mnt/mnt1` — note the path is mangled into the unit name by escaping `/` as `-`)."

**Reading it left to right:**
- `systemctl daemon-reload` → "rescan unit files *and* regenerate fstab-derived mount units."
- `systemctl status mnt-mnt1.mount` → "show the status of the unit corresponding to `/mnt/mnt1`. Systemd derives the name by replacing `/` with `-` and stripping the leading `/` (so `/mnt/mnt1` → `mnt-mnt1.mount`)."
- `--no-pager` → "direct stdout."

**The story:** On modern RHEL, systemd manages mounts *through generated `.mount` units* that mirror fstab entries. Edit fstab and run `daemon-reload`, and you'll see a fresh `.mount` unit. This is also why fstab edits are picked up by `mount -a` immediately — fstab is the source-of-truth, and systemd re-derives the unit graph from it on demand. You can manually `systemctl start mnt-mnt1.mount` or `systemctl stop mnt-mnt1.mount` — they're real units now, not just fstab strings.

**Analogy:** Editing a recipe and asking the chef to re-read the cookbook. Without the re-read, the chef cooks from memory of the old recipe.

**Expected output:**

```
● mnt-mnt1.mount - /mnt/mnt1
     Loaded: loaded (/etc/fstab; generated)
     Active: active (mounted) since Fri 2026-05-22 13:55:42 EDT; 2min ago
      Where: /mnt/mnt1
       What: /dev/mapper/vgtest-lvol1
       …
```

**Switches**

| Token | Meaning |
|---|---|
| `daemon-reload` | Re-scan units + regenerate from fstab |
| `systemctl status MOUNT.mount` | Status of a mount unit |

**Output decoded**

| Field | Meaning |
|---|---|
| `Loaded: (/etc/fstab; generated)` | Confirms the unit was derived from fstab |
| `Active: active (mounted)` | Mount is live |
| `Where: /mnt/mnt1` / `What: /dev/...` | The two sides of the mount |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Unit mnt-mnt1.mount not loaded` | Forgot `daemon-reload`, or the fstab line failed to parse |

---

### Task 15 — Write a file to prove the mount is actually usable

**Purpose:** A mount that doesn't accept writes is a broken mount.

```bash
echo "hello from lvol1 at $(date)" | tee /mnt/mnt1/hello.txt
ls -l /mnt/mnt1
df -h /mnt/mnt1
```

**Human-Readable Breakdown:**
> "Hey shell, write a line into `/mnt/mnt1/hello.txt` that includes the current date so I can prove this is a fresh write, not a leftover. Use `tee` to echo to stdout simultaneously. Then list the directory contents to confirm the file is on the LV. Then `df -h` to see the byte count tick up."

**Reading it left to right:**
- `echo "hello from lvol1 at $(date)"` → "construct the line; `$(date)` substitutes the current timestamp."
- `\| tee /mnt/mnt1/hello.txt` → "write to the file AND print to stdout."
- `ls -l /mnt/mnt1` → "verify the file appears on the LV."
- `df -h /mnt/mnt1` → "confirm `Use%` ticked up (slightly)."

**The story:** Always do an end-to-end write test on a fresh mount. The mount can succeed yet the filesystem be read-only (e.g. due to a kernel-detected error remount, or `ro` in fstab options). The only way to know it's truly writable is to *write something*. Five seconds; rules out half the post-mount bug class.

**Analogy:** Turning on the faucet to confirm the new plumbing works. Pipes can be installed correctly and still have no water.

**Expected output:**

```
hello from lvol1 at Fri May 22 13:58:14 EDT 2026

total 16
-rw-r--r--. 1 root root    49 May 22 13:58 hello.txt
drwx------. 2 root root 12288 May 22 13:48 lost+found

Filesystem               Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 252M   28K  234M   1% /mnt/mnt1
```

**Switches**

| Token | Meaning |
|---|---|
| `echo "X" \| tee FILE` | Write + echo |
| `ls -l` | Long listing |
| `lost+found` | Auto-created ext4 directory for fsck-recovered orphans |

**Output decoded**

| Line | Meaning |
|---|---|
| `hello.txt` exists | Filesystem accepts writes |
| `lost+found` directory | Confirms ext4 — this directory is created by `mkfs.ext4` |
| `Use%` went up | Real bytes were written |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Read-only file system` | Mount options have `ro`, or the FS was force-remounted ro after an error — check `dmesg` |
| `No space left on device` | The 280 MiB filled up; that's actually a successful write proof if it took a while |

---

### Task 16 — Inspect the LV's runtime state

**Purpose:** A mounted, in-use LV shows different attributes than an idle one. Read them.

```bash
lvs -o +devices,segtype,stripes
lvdisplay --maps /dev/vgtest/lvol1 | head -30
```

**Human-Readable Breakdown:**
> "Hey LVM, show me the tabular view of all LVs but add three extra columns: which devices back them, what segment type each uses, and how many stripes. Then show me the verbose view with extent maps so I can see exactly which physical extents on which PV are backing our LV."

**Reading it left to right:**
- `lvs -o +devices,segtype,stripes` → "**append** (`+`) the listed columns to the default. `-o devices` alone would *replace* the defaults; `-o +devices` *adds* to them."
- `lvdisplay --maps DEV` → "verbose plus per-segment extent map."
- `head -30` → "trim — the map can be long."

**The story:** `lvs -o +...` is the **power-user lvs**. Real ops engineers use it daily because the default columns are the bare minimum; you almost always want to know "which PV is backing this LV?" especially when you have multi-PV VGs and a disk needs replacing. `lvdisplay --maps` is even deeper — you see "LE 0–69 → PE 0–69 on /dev/loop0." That kind of detail saves you when a disk dies and you need to know what data lived on it.

**Analogy:** Reading the wiring diagram, not just the floorplan. The floorplan says where the lamps are; the diagram says which breakers feed which sockets.

**Expected output:**

```
  LV    VG     Attr       LSize   … Devices         Type   #Str
  root  rhel   -wi-ao---- <26.00g   /dev/nvme0n1p2(0) linear 1
  swap  rhel   -wi-ao----   3.00g   /dev/nvme0n1p2(6656) linear 1
  lvol1 vgtest -wi-ao----  280.00m  /dev/loop0(0)    linear 1

  --- Logical volume ---
  LV Path                /dev/vgtest/lvol1
  LV Name                lvol1
  VG Name                vgtest
  …
  Segments               1
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     256
  Block device           253:2

  --- Segments ---
  Logical extents 0 to 69:
    Type        linear
    Physical volume       /dev/loop0
    Physical extents      0 to 69
```

**Switches**

| Token | Meaning |
|---|---|
| `lvs -o +COLS` | Append columns |
| `lvdisplay --maps` | Show extent map |

**Output decoded**

| Field | Meaning |
|---|---|
| `Attr -wi-ao----` | `o` (open) appears because the LV is mounted |
| `Devices /dev/loop0(0)` | LV is backed by `/dev/loop0` starting at PE 0 |
| `Type linear` | A simple, non-striped, non-mirrored LV |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Attr` doesn't show `o` (open) | LV isn't mounted; re-run `mount -a` |

---

### Task 17 — Simulate a reboot with umount + mount -a

**Purpose:** The real "does it survive reboot?" test is `umount` + `mount -a`. Faster than rebooting.

```bash
umount /mnt/mnt1
mount | grep mnt1 || echo "Not mounted - good, we will remount via fstab"
mount -a
mount | grep mnt1
cat /mnt/mnt1/hello.txt
```

**Human-Readable Breakdown:**
> "Hey kernel, unmount `/mnt/mnt1`. Confirm it's gone with `mount | grep`. Now ask kernel to walk fstab and mount everything — exactly what happens at boot. Confirm `/mnt/mnt1` came back via fstab. Read the file we wrote in Task 15 to prove the data persisted."

**Reading it left to right:**
- `umount /mnt/mnt1` → "unmount."
- `mount | grep mnt1 \|\| echo "Not mounted..."` → "if grep finds nothing, print a friendly message instead of an empty line."
- `mount -a` → "boot-time fstab walk simulated."
- `cat /mnt/mnt1/hello.txt` → "read the file. If you see your line from Task 15, the data survived."

**The story:** `umount + mount -a` is the **poor-person's reboot.** It exercises the exact same code path the kernel runs at boot, but in 0.1 seconds instead of 60. Use it after every fstab edit. If it works here, it'll work at boot — barring kernel command-line surprises (e.g. `rd.lvm.lv=` filters that hide your VG from the initramfs, but that's an RHCE-level concern).

**Analogy:** Test-firing the reboot without actually rebooting. Same end state, much faster cycle.

**Expected output:**

```
Not mounted - good, we will remount via fstab

/dev/mapper/vgtest-lvol1 on /mnt/mnt1 type ext4 (rw,relatime,seclabel)

hello from lvol1 at Fri May 22 13:58:14 EDT 2026
```

**Switches**

| Token | Meaning |
|---|---|
| `umount` | Detach |
| `\|\|` | OR — run next only if previous failed |
| `cat` | Print file contents |

**Output decoded**

| Line | Meaning |
|---|---|
| `Not mounted` message | umount succeeded |
| Mount line after `mount -a` | fstab re-mounted it |
| `hello from lvol1 at ...` | Data persisted across umount/remount |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `umount: target is busy` | You're currently in `/mnt/mnt1`; `cd /` first |
| Empty `hello.txt` after remount | You re-mkfs'd somewhere along the way; data was destroyed |

---

### Task 18 — Document the layer stack you just built

**Purpose:** Sanity-check the whole stack with one command per layer.

```bash
losetup -a
pvs
vgs
lvs -o +devices
lsblk -f
df -hT /mnt/mnt1
grep mnt1 /etc/fstab
```

**Human-Readable Breakdown:**
> "Hey shell, take a snapshot of every layer in the stack — loop devices, PVs, VGs, LVs with backing devices, the full block-device tree with FS info, the disk-free for our mount, and the fstab line that makes it persistent. This is the 'I built it correctly' proof page."

**Reading it left to right:**
- `losetup -a` → "loop-device layer."
- `pvs` → "physical volume layer."
- `vgs` → "volume group layer."
- `lvs -o +devices` → "logical volume layer + backing device column."
- `lsblk -f` → "kernel block tree with FS info."
- `df -hT` → "user-facing disk free with TYPE column."
- `grep mnt1 /etc/fstab` → "the persistence line."

**The story:** Every senior admin can rattle off this exact verification sequence. It walks the stack from the bottom (raw block device via loopback) up to the top (mounted filesystem with fstab persistence) and proves each layer is correctly hooked to the one above. Memorize this sequence and you can audit any storage setup on any RHEL box in 30 seconds.

**Analogy:** Walking around a finished house and ticking off the inspection list — foundation, framing, plumbing, electrical, roof, finish — one per layer.

**Expected output:**

```
/dev/loop0: []: (/root/lvm-lab/disk1.img)

  PV             VG     Fmt  Attr PSize    PFree
  /dev/loop0     vgtest lvm2 a--  1020.00m 740.00m
  /dev/nvme0n1p2 rhel   lvm2 a--  <29.00g     0

  VG     #PV #LV #SN Attr   VSize    VFree
  rhel     1   2   0 wz--n- <29.00g     0
  vgtest   1   1   0 wz--n- 1020.00m 740.00m

  LV    VG     Attr       LSize   … Devices
  root  rhel   -wi-ao---- <26.00g   /dev/nvme0n1p2(0)
  swap  rhel   -wi-ao----   3.00g   /dev/nvme0n1p2(6656)
  lvol1 vgtest -wi-ao----  280.00m  /dev/loop0(0)

NAME            FSTYPE FSVER LABEL UUID                                 …
loop0           LVM2_…   …
└─vgtest-lvol1 ext4     1.0 lvol1 1f8a3b5c-…                            … /mnt/mnt1

Filesystem               Type Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 ext4 252M   28K  234M   1% /mnt/mnt1

UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
```

**Switches**

| Token | Meaning |
|---|---|
| `df -hT` | Human-readable, with TYPE column |
| `lsblk -f` | With FSTYPE/LABEL/UUID columns |

**Output decoded**

| Layer | Proof |
|---|---|
| Loop | `losetup -a` shows the backing file |
| PV | `pvs` row for `/dev/loop0` |
| VG | `vgs` row for `vgtest` |
| LV | `lvs` row for `lvol1` showing 280m and backing device |
| FS | `lsblk -f` ext4 line |
| Mount | `df -hT` line |
| Persistence | `grep mnt1 /etc/fstab` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| Any layer missing | Re-run the corresponding earlier task |

---

### Task 19 — Clean teardown (bottom-up)

**Purpose:** Remove every layer cleanly so the lab is repeatable. **Tear down bottom-up — opposite of build order.**

```bash
sed -i '/\/mnt\/mnt1/d' /etc/fstab
systemctl daemon-reload
umount /mnt/mnt1
rmdir /mnt/mnt1
lvremove -y /dev/vgtest/lvol1
vgremove -y vgtest
pvremove -y /dev/loop0
losetup -d /dev/loop0
rm -f /root/lvm-lab/disk1.img
pvs ; vgs ; lvs
```

**Human-Readable Breakdown:**
> "Hey shell, strip the fstab line for `/mnt/mnt1` (`sed -i '/MATCH/d'`). Tell systemd to re-scan units. Unmount. Remove the now-empty mountpoint directory. Tear the LV down (`lvremove`). Tear the VG down (`vgremove`). Strip LVM metadata from the loop device (`pvremove`). Detach the loop device. Delete the backing file. Print the three LVM summaries — they should all be back to pre-lab state."

**Reading it left to right:**
- `sed -i '/\/mnt\/mnt1/d' /etc/fstab` → "in-place delete (`d`) every line matching `/mnt/mnt1`. Forward slashes are escaped inside the pattern."
- `systemctl daemon-reload` → "regenerate fstab-derived mount units now that the line is gone."
- `umount /mnt/mnt1` → "unmount."
- `rmdir /mnt/mnt1` → "remove the now-empty directory."
- `lvremove -y /dev/vgtest/lvol1` → "remove LV; `-y` skips the 'are you sure?' prompt."
- `vgremove -y vgtest` → "remove VG."
- `pvremove -y /dev/loop0` → "strip LVM signature."
- `losetup -d /dev/loop0` → "detach loop device."
- `rm -f /root/lvm-lab/disk1.img` → "delete backing file."
- `pvs ; vgs ; lvs` → "confirm everything's gone (semicolons run them sequentially regardless of success)."

**The story:** Teardown order matters: **fstab → unmount → rmdir → lvremove → vgremove → pvremove → losetup -d.** Skip any step and the next one errors with "in use." This is the most common LVM frustration on the exam — candidates panic, retry, get more errors, and lose minutes. Memorize the order. The `sed -i '/PATH/d'` idiom for removing fstab lines by path is also worth burning in — much safer than re-typing the file by hand.

**Analogy:** Demolishing a building. You take down the roof before the walls, the walls before the foundation. Try it the other way and the wreckage crushes you on the way down.

**Expected output:**

```
  Logical volume "lvol1" successfully removed
  Volume group "vgtest" successfully removed
  Labels on physical volume "/dev/loop0" successfully wiped.

  PV             VG   Fmt  Attr PSize    PFree
  /dev/nvme0n1p2 rhel lvm2 a--  <29.00g     0

  VG   #PV #LV #SN Attr   VSize   VFree
  rhel   1   2   0 wz--n- <29.00g     0

  LV   VG   Attr       LSize   …
  root rhel -wi-ao---- <26.00g
  swap rhel -wi-ao----   3.00g
```

**Switches**

| Token | Meaning |
|---|---|
| `sed -i '/PAT/d' FILE` | In-place delete matching lines |
| `lvremove -y` / `vgremove -y` / `pvremove -y` | Skip confirmation |
| `losetup -d` | Detach loop device |

**Output decoded**

| Line | Meaning |
|---|---|
| Removal messages | Each layer torn down successfully |
| Final `pvs`/`vgs`/`lvs` | System is back to pre-lab state |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `umount: target is busy` | Process holding the mount; `lsof +D /mnt/mnt1` |
| `Logical volume vgtest/lvol1 is used by another device` | Forgot to umount first |
| `Can't open /dev/loop0 exclusively` | LVM hasn't released it; retry after a `udevadm settle` |

---

### Task 20 — Capstone: full RHCSA Task 12 end-to-end

**Task statement:** *"Create a logical volume called `lvol1` of size 280 MB in the `vgtest` volume group. Mount the ext4 file system persistently to `/mnt/mnt1`."*

```bash
# 1. Substrate: a 1 GiB loopback (skip this block on a real disk; use /dev/sdb instead)
truncate -s 1G /root/lvm-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-lab/disk1.img)
echo "Using loopback: $LOOP"

# 2. PV → VG → LV
pvcreate "$LOOP"
vgcreate vgtest "$LOOP"
lvcreate -L 280M -n lvol1 vgtest

# 3. Filesystem + mountpoint
mkfs.ext4 -L lvol1 /dev/vgtest/lvol1
mkdir -p /mnt/mnt1

# 4. Persistent mount
UUID=$(blkid -s UUID -o value /dev/vgtest/lvol1)
echo "UUID=$UUID  /mnt/mnt1  ext4  defaults  0 0" | tee -a /etc/fstab
systemctl daemon-reload
mount -a

# 5. Verify
lvs -o +devices
df -hT /mnt/mnt1
grep mnt1 /etc/fstab
```

**Human-Readable Breakdown:**
> "End-to-end exam answer in one block. Set up a 1 GiB loopback (substitute `/dev/sdb` on a real exam VM). Build the LVM stack in three commands: `pvcreate`, `vgcreate`, `lvcreate`. Format ext4 with a label. Create the mountpoint. Capture the UUID. Append a `defaults 0 0` fstab line. Reload systemd. Test with `mount -a`. Verify with three commands proving the LV exists at the right size, the filesystem is mounted, and the fstab line is persistent."

**Reading it left to right:**

| Block | What it does |
|---|---|
| `truncate -s 1G ...` + `losetup -fP --show ...` | Create a virtual disk for safe practice |
| `pvcreate "$LOOP"` | Mark it as an LVM PV |
| `vgcreate vgtest "$LOOP"` | Pool into VG `vgtest` |
| `lvcreate -L 280M -n lvol1 vgtest` | The headline command: 280 MiB LV named `lvol1` |
| `mkfs.ext4 -L lvol1 /dev/vgtest/lvol1` | ext4 filesystem with a friendly label |
| `mkdir -p /mnt/mnt1` | Mountpoint |
| `blkid -s UUID -o value ...` | Bare UUID for fstab |
| `tee -a /etc/fstab` | Append `UUID=... /mnt/mnt1 ext4 defaults 0 0` |
| `systemctl daemon-reload` + `mount -a` | Pick up the new line and prove it boots |
| `lvs`, `df -hT`, `grep mnt1` | Three-line verification |

**The story:** This is the **5-minute exam answer.** Memorize the spine: `pvcreate → vgcreate → lvcreate -L 280M -n lvol1 vgtest → mkfs.ext4 → mkdir → blkid → tee fstab → daemon-reload → mount -a → verify`. Everything else (`-L lvol1` label, capturing `$UUID` to a variable, the verification triplet) is polish you add once the bones are right. If you can type this block from memory in under 5 minutes, every storage-creation question on the exam is a freebie.

**Analogy:** Memorizing the closing argument of a courtroom speech. The structure is fixed; the names and numbers change.

**Expected output (last three blocks):**

```
  LV    VG     Attr       LSize   … Devices
  …
  lvol1 vgtest -wi-ao----  280.00m  /dev/loop0(0)

Filesystem               Type Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 ext4 252M   24K  234M   1% /mnt/mnt1

UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
```

**Verification checklist**

| Step | Expected |
|---|---|
| `lvs` shows `lvol1 vgtest ... 280.00m` | ✅ |
| `df -hT /mnt/mnt1` shows `ext4` type | ✅ |
| `grep mnt1 /etc/fstab` shows UUID-based entry | ✅ |
| `umount /mnt/mnt1 && mount -a` re-mounts | ✅ (Task 17) |

**Cleanup**

```bash
sed -i '/\/mnt\/mnt1/d' /etc/fstab
systemctl daemon-reload
umount /mnt/mnt1
rmdir /mnt/mnt1
lvremove -y /dev/vgtest/lvol1
vgremove -y vgtest
pvremove -y "$LOOP"
losetup -d "$LOOP"
rm -f /root/lvm-lab/disk1.img
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Volume group "vgtest" has insufficient free space` | The `disk1.img` was too small; bump to 2 GiB |
| Capstone fails at `mount -a` | UUID typo. Re-capture with `blkid -s UUID -o value /dev/vgtest/lvol1` |
| `mkfs.ext4` complains about a signature | `wipefs -a /dev/vgtest/lvol1` first |
| `vgcreate` fails: device excluded by filter | Pre-existing signature; `wipefs -a $LOOP` first |

---

## 🔍 LVM Storage Decision Guide

```
Got a storage task to solve?
  │
  ├── "Make a new filesystem and mount it persistently"
  │       └── ✅ Full pipeline: pvcreate → vgcreate → lvcreate → mkfs → mkdir → fstab → mount -a
  │
  ├── "Make / bigger" / "Make /home bigger"
  │       └── ✅ vgextend (if more disk needed) → lvextend → resize2fs (ext) / xfs_growfs (xfs)
  │
  ├── "Take a backup snapshot of a live database"
  │       └── ✅ lvcreate -s -L 1G -n backup /dev/VG/LV
  │
  ├── "Add a new disk to existing storage pool"
  │       └── ✅ pvcreate /dev/newdisk → vgextend VG /dev/newdisk
  │
  ├── "Shrink /home (rare and risky)"
  │       └── ✅ Only with ext4: unmount → e2fsck -f → resize2fs SIZE → lvreduce -L SIZE
  │       └── ❌ Never with xfs — it cannot shrink
  │
  └── "Replace a dying disk in the VG"
          └── ✅ pvmove /dev/dyingdisk → vgreduce → pvremove → physically swap → pvcreate new → vgextend
```

---

## ✅ Lab Checklist (20 Tasks)

- [ ] 01 Install `lvm2` + verify toolchain
- [ ] 02 Read baseline `lsblk` / `pvs` / `vgs` / `lvs`
- [ ] 03 Create loopback `disk1.img` + `losetup -fP --show`
- [ ] 04 `pvcreate /dev/loop0`
- [ ] 05 `vgcreate vgtest /dev/loop0`
- [ ] 06 `lvcreate -L 280M -n lvol1 vgtest`
- [ ] 07 `mkfs.ext4 -L lvol1 /dev/vgtest/lvol1`
- [ ] 08 `blkid` + `lsblk -f` + `dumpe2fs -h` inspection
- [ ] 09 `mkdir -p /mnt/mnt1`
- [ ] 10 Test mount manually
- [ ] 11 Capture UUID with `blkid -s UUID -o value`
- [ ] 12 Append fstab line + `tee -a`
- [ ] 13 `mount -a` smoke test
- [ ] 14 `systemctl daemon-reload` + verify `.mount` unit
- [ ] 15 Write a file to prove the mount works
- [ ] 16 Inspect runtime state with `lvs -o +devices`
- [ ] 17 Simulate reboot with `umount` + `mount -a`
- [ ] 18 Full stack documentation snapshot
- [ ] 19 Clean teardown (bottom-up)
- [ ] 20 Capstone — full RHCSA Task 12 end-to-end

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot `mkfs.ext4` after `lvcreate` | `mount: wrong fs type, bad option, bad superblock` | Format first |
| Used device path in fstab instead of UUID | Boot fails after disk reorder | Use `UUID=...` |
| Skipped `mount -a` test before reboot | System won't boot; emergency mode | Always `mount -a` after fstab edit |
| Teardown out of order | `device busy` errors | Bottom-up: fstab → umount → rmdir → lv → vg → pv → loop |
| `M` vs `m` confusion in `lvcreate -L` | None (both work — `M` = `m` = MiB) | Just be consistent |
| `MB` (decimal) vs `MiB` (binary) confusion | Slight size mismatch | `mkfs` reports usable size after journal + reserves |
| Forgot `systemctl daemon-reload` after fstab edit | Mount unit shows stale state | Always reload |
| `mkfs.ext4` on a mounted device | `will not make a filesystem here!` | Unmount first |
| Used `/dev/dm-N` in scripts | Numbers change across boots | Use `/dev/VG/LV` symlink instead |
| `lvremove` before unmount | "Logical volume in use" | Unmount, then `lvremove` |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- "Create a 280 MB LV called lvol1 in vgtest and mount it persistently" is a near-guaranteed exam question. Memorize the Task 20 capstone block — type it in 5 minutes from blank slate.

**RHCE candidate**
- Same workflow via Ansible: `community.general.lvg`, `community.general.lvol`, `community.general.filesystem`, and `ansible.posix.mount`. Practice writing a playbook that recreates Task 20.

**SRE / Platform interview**
- Be ready to walk through "growing /home without downtime": `pvcreate /dev/sdc → vgextend vgname /dev/sdc → lvextend -L +20G /dev/vgname/home → xfs_growfs /home` (or `resize2fs` for ext4). One disk, one VG, one LV, one filesystem grow — five commands, zero downtime.

**DevOps**
- Container storage drivers (`devicemapper`, modern `overlay2` with backing fs) sit on LVM. Knowing how to inspect and grow the underlying thin pool is bread-and-butter for Kubernetes node operations.

**AI / MLOps**
- Big checkpoint volumes, scratch space for distributed training, and dataset caches are often LVM. The PV/VG/LV mental model also transfers directly to ZFS (zpool/dataset) and EBS-based cloud storage.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab — Scheduling Jobs (systemd timer, Mon–Fri 2 AM) | Sibling RHCSA scheduled-tasks vs. storage exam question |
| Configure Persistent Mounts fstab *(coming soon)* | The fstab-only piece of this lab, decoupled from LVM |
| Extend Logical Volume *(coming soon)* | The next-day question — "grow lvol1 to 500 MB without losing data" |
| Resize Filesystem After Extend *(coming soon)* | `xfs_growfs` / `resize2fs` after `lvextend` |
| Create and Activate Swap Space *(coming soon)* | Same workflow as this lab but `mkswap` + `swapon` instead of `mkfs.ext4` + `mount` |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
