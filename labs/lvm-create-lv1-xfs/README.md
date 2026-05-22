# Lab: Create LV `lv1` (XFS, 8 MiB PE, 10 LEs) and Mount Persistently

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Subjects covered:** PV / VG / LV mental model with **custom PE size**, `pvcreate`, `vgcreate -s 8M`, `lvcreate -l 10`, `mkfs.xfs`, `xfs_info`, `xfs_growfs`, `blkid`, UUID-based `/etc/fstab` entries, `mount -a`, `systemctl daemon-reload`, loopback devices for safe practice
**Career arcs covered:** RHCSA (Storage objective — guaranteed exam question, XFS is the RHEL 7+ default), RHCE (Ansible `community.general.lvol` + `community.general.filesystem` modules), SRE (online growth of root volumes), DevOps (XFS as the default for container-host workloads)
**Prerequisite:** [lvm-create-lvol1-ext4](../lvm-create-lvol1-ext4/) (the ext4 sibling lab) — comfort with `pvcreate / vgcreate / lvcreate` basics
**Time Estimate:** 60 to 90 minutes
**Difficulty arc:** Tasks 1–5 foundation · 6–13 the PV→VG(custom PE)→LV(extent count)→XFS→mount pipeline · 14–18 making it persistent and verified · 19–20 RHCSA exam-realistic capstone

---

## Objective

Build the **PV → VG (custom PE) → LV (extent count) → XFS → mount → fstab** muscle memory so you can answer any RHCSA storage question — whether the question phrases the size in MiB, in extents, or in percent-free. By the end of this lab you can take an empty block device and turn it into a persistently-mounted XFS filesystem in seven commands while honoring a non-default PE size.

The capstone is the **RHCSA sample exam Task (samplerhcsa2.txt)**: create a logical volume called `lv1` in volume group `vg1` using **8 MiB physical extents** and exactly **10 logical extents** (so the LV is 80 MiB), format it XFS, and mount it persistently to `/mnt/lvfs1` with a test file written into it.

> **Lab safety note:** This lab uses **loopback devices** (`losetup` + a sparse file) instead of real disks, so you can practice the full PV/VG/LV pipeline on any RHEL VM. Every command transfers identically to a real `/dev/vdb` or `/dev/nvme1n1` when you do get an extra disk.

> **Companion to the ext4 lab:** Where [lvm-create-lvol1-ext4](../lvm-create-lvol1-ext4/) uses the default 4 MiB PE size and sizes the LV in MiB (`-L 280M`), this lab uses an **explicit 8 MiB PE size** and sizes the LV by **extent count** (`-l 10`). Both are valid exam phrasings; you must be fluent in both.

---

## Concept: Why PE Size and Extent Count Both Matter

LVM allocates storage in fixed-size chunks called **Physical Extents (PE)** on the PV side and **Logical Extents (LE)** on the LV side. They are 1-to-1 in a linear LV: LE 0 maps to PE 0 of some PV, LE 1 to PE 1, and so on.

The default PE size is **4 MiB**. The VG-level directive `-s` overrides it at `vgcreate` time. Once set, the PE size is **fixed for the life of the VG** — every PV added to that VG must use the same PE size, and every LV carved from it uses LEs of that same size.

```
   ┌─────────────────────────────────────────────────────┐
   │  XFS filesystem                ← what users see      │
   ├─────────────────────────────────────────────────────┤
   │  LV  lv1 (10 LEs × 8 MiB = 80 MiB)                  │  ┐
   ├─────────────────────────────────────────────────────┤  │ LVM
   │  VG  vg1 (PE size 8 MiB, set at vgcreate)           │  │ layer
   ├─────────────────────────────────────────────────────┤  │
   │  PV  /dev/loop0 (1 GiB)                             │  ┘
   ├─────────────────────────────────────────────────────┤
   │  Block device (loopback / partition / disk)          │
   └─────────────────────────────────────────────────────┘
```

**Why a non-default PE size matters:**

- Very small PEs (1 MiB) → fine-grained allocation, but bigger metadata overhead and a cap on max VG size.
- Default PE (4 MiB) → the right balance for nearly every workload.
- Larger PEs (8 MiB, 16 MiB, 64 MiB) → less metadata, larger allowed VG sizes — historically required for >2 TiB VGs on legacy LVM1.
- **Exam questions often specify PE size and extent count explicitly to confirm you know `-s SIZE` and `-l COUNT`.**

> **Why this matters:** Real RHCSA candidates fail this question because they default-mode the VG with `vgcreate vg1 /dev/loop0` (4 MiB PE), then `lvcreate -l 10 -n lv1 vg1` and end up with a 40 MiB LV instead of 80 MiB. Read the question, set the PE size *first*, then size the LV in the unit the question demanded.

---

## 📜 Why XFS Exists — The Story

XFS was created by **Silicon Graphics (SGI)** in **1993** for IRIX. It was open-sourced in 1999, ported to Linux in 2001, and became the **default RHEL filesystem in RHEL 7** (2014). Why did Red Hat replace ext4?

### What ext4 does well (and where it ends)

ext4 is the workhorse Linux filesystem: small footprint, fast on small files, well-understood by every admin. But it carries three legacy limits:

- **16 TiB maximum filesystem size** (in practice; the on-disk format allows more, but `e2fsprogs` historically didn't).
- **Single-threaded journal**, which becomes a bottleneck under heavy parallel write loads.
- **No online shrink** beyond what ext4 was designed for — and online *grow* requires resize2fs, which is slower for very large filesystems.

### What XFS was designed for

- **64-bit everywhere from day one.** Filesystems can grow to 8 EiB (exabytes). The exam-day version: "XFS doesn't run out."
- **Allocation groups.** XFS splits the filesystem into independent allocation groups (AGs) — typically 4 to 1024 of them — each with its own metadata. Two threads writing to different AGs don't contend, giving XFS its famous parallel-write throughput.
- **Delayed allocation.** XFS doesn't decide *where* on disk to put your bytes until it has to flush them. The longer the delay, the larger the contiguous chunks it can write — minimizing fragmentation.
- **Online grow only (never shrink).** This is a deliberate design tradeoff: by not supporting shrink, XFS keeps its allocation-group metadata simple and fast. If you need to shrink, you back up, recreate, restore.

### Why Red Hat made it the default in RHEL 7

By 2014, the average enterprise server had 24+ cores, 128+ GiB RAM, and multi-terabyte storage. ext4's single-thread journal was a measurable bottleneck on virtualization hosts. Red Hat tested both filesystems at scale and concluded XFS was the better default — faster on multi-core, scales further, more mature for the workloads RHEL customers run.

### When ext4 is still the right answer

- The exam question explicitly says "ext4."
- You need to **shrink** the filesystem.
- You're on a system smaller than ~10 GiB total — XFS's overhead is meaningful at tiny sizes.

> **The point of the story:** XFS is the RHEL 7/8/9 default because Red Hat made a deliberate engineering bet on parallelism, scalability, and online growth. ext4 is still everywhere — but every time an exam question says "create a filesystem and mount it persistently" without specifying the type, the safe answer is **XFS**.

---

## 👪 The XFS Family — Who Lives There

XFS has a smaller toolkit than ext4 because it deliberately offers fewer knobs. Memorize this family.

### Creation and inspection

| Command | What it does |
|---|---|
| `mkfs.xfs DEV` | Format a block device as XFS |
| `mkfs.xfs -f DEV` | Force-format even if a signature is present |
| `mkfs.xfs -L LABEL DEV` | Set the filesystem label |
| `xfs_info MOUNTPOINT` | Print geometry: AG count, block size, sectsz, log size, ... |
| `xfs_info DEV` | Same, by device path (newer xfsprogs only) |
| `blkid DEV` | Show UUID, LABEL, TYPE (works on any FS) |

### Growth (the headline online feature)

| Command | What it does |
|---|---|
| `xfs_growfs MOUNTPOINT` | Grow XFS to fill the underlying device. **Filesystem must be mounted.** |
| `xfs_growfs -D SIZE MOUNTPOINT` | Grow to a specific size (rare; full-grow is usual) |

### Repair (the offline path)

| Command | What it does |
|---|---|
| `xfs_repair DEV` | Check and repair the filesystem. **Filesystem must be unmounted.** |
| `xfs_repair -n DEV` | Dry-run check only |
| `xfs_repair -L DEV` | Last-resort: zero the log (only if `xfs_repair` insists you do) |

### Comparison with ext4

| Task | ext4 | XFS |
|---|---|---|
| Format | `mkfs.ext4 DEV` | `mkfs.xfs DEV` |
| Set label | `mkfs.ext4 -L name DEV` | `mkfs.xfs -L name DEV` |
| Show geometry | `dumpe2fs -h DEV` | `xfs_info MOUNTPOINT` |
| Online grow | `resize2fs DEV` (after `lvextend`) | `xfs_growfs MOUNTPOINT` (after `lvextend`) |
| Online shrink | `resize2fs DEV SIZE` (with care) | **Not supported** |
| Offline check | `e2fsck -f DEV` | `xfs_repair DEV` |
| Default in RHEL | 6 and older | 7 and newer |

> **The point of the family tree:** XFS deliberately has fewer commands than ext4 because its design philosophy is "fewer ways to break it." The cost is no online shrink. The benefit is a faster, more scalable filesystem with simpler operational semantics.

---

## 🔬 The Anatomy of `xfs_info` Output — In One Diagram

```
$ xfs_info /mnt/lvfs1
meta-data=/dev/mapper/vg1-lv1   isize=512    agcount=4, agsize=5120 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=1, sparse=1, rmapbt=0
         =                       reflink=1    bigtime=1 inobtcount=1 nrext64=0
data     =                       bsize=4096   blocks=20480, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
log      =internal log           bsize=4096   blocks=1368, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
└──┬──┘  └──────┬─────────┘     └──┬──┘
   │            │                   └─ Subsection-specific knobs (block size, extent size, ...)
   │            └─ The component being described
   └─ Top-level component: meta-data / data / naming / log / realtime
```

The five sections at a glance:

- **meta-data** — inode size (`isize`), allocation-group count (`agcount`), AG size in blocks (`agsize`), CRC enabled (`crc=1`), reflink support (`reflink=1`).
- **data** — the data section: block size (`bsize`, typically 4096), total blocks (`blocks`), reserved-root percentage (`imaxpct`).
- **naming** — directory format (`version 2`), filename block size.
- **log** — the journal: `internal log` means it lives inside the data section (default); the log size in blocks and sector size.
- **realtime** — optional realtime device for guaranteed I/O latency (rare; almost always `none`).

For a 10-LE × 8 MiB = 80 MiB LV, you'll see `blocks=20480` (80 MiB ÷ 4 KiB = 20,480 blocks) and `agcount=4` (XFS's default AG count for small filesystems).

> **Reading rule:** When something's wrong with an XFS filesystem, `xfs_info` is your first call. It tells you whether the geometry matches the underlying device's size, whether CRC is enabled (essential for modern RHEL), and whether the log is internal or external.

---

## 📚 LVM + XFS Reference Table

| Task | Command | Notes |
|---|---|---|
| Initialize a disk for LVM | `pvcreate /dev/sdX` | Same for ext4 or XFS workflows |
| Create a VG with custom PE size | `vgcreate -s 8M VGNAME /dev/sdX` | **`-s` must come at VG creation** — cannot be changed later |
| Inspect PE size after creation | `vgdisplay VGNAME \| grep "PE Size"` | Sanity check before sizing the LV |
| Create an LV by extent count | `lvcreate -l 10 -n LVNAME VGNAME` | 10 LEs × PE size = total LV size |
| Create an LV by size | `lvcreate -L 80M -n LVNAME VGNAME` | Equivalent when PE=8M (10 LEs) |
| Format XFS | `mkfs.xfs /dev/VGNAME/LVNAME` | RHEL default since RHEL 7 |
| Format XFS with label | `mkfs.xfs -L lv1 /dev/VGNAME/LVNAME` | Label appears in `lsblk -f` and `blkid` |
| Get UUID | `blkid /dev/VGNAME/LVNAME` | The UUID you'll paste into `/etc/fstab` |
| Persistent mount | `UUID=... /mnt/lvfs1 xfs defaults 0 0` in `/etc/fstab` | Then `mount -a` |
| Inspect XFS geometry | `xfs_info /mnt/lvfs1` | Must be mounted |
| Grow XFS online | `lvextend -L +SIZE /dev/VG/LV && xfs_growfs /mnt/lvfs1` | Two commands, no unmount |
| Repair XFS | `umount && xfs_repair /dev/VG/LV` | Always unmount first |
| Remove an LV | `umount → lvremove /dev/VG/LV` | Unmount first |

> **Rule one of XFS:** never try to shrink it. If the exam asks "shrink the filesystem," you're on ext4 (or the exam is testing whether you'll refuse the impossible task on XFS).

> **Rule one of custom PE size:** set `-s` **at `vgcreate` time**. It cannot be changed afterwards without destroying and recreating the VG.

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Create an LV in a VG with a specific PE size and extent count, format XFS, mount persistently" is the canonical sample-exam phrasing (samplerhcsa2.txt, Task 12 variant). |
| **RHCE candidate** | `community.general.lvg` accepts `pesize=8M`; `community.general.lvol` accepts `size=10g` or `size=80m`; `community.general.filesystem` accepts `fstype=xfs`. Ship this via a role. |
| **SRE / Platform** | Growing `/` (XFS) without downtime: `vgextend → lvextend → xfs_growfs`. Three commands; zero unmount; classic on-call task. |
| **DevOps** | `/var/lib/containers` and `/var/lib/docker` are XFS on RHEL by default. Knowing the geometry helps when tuning thin-pool storage. |
| **AI / MLOps** | Big checkpoint volumes for distributed training are XFS for the parallel-write throughput; the grow-while-mounted property matters when a training run fills the disk. |

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

**Purpose:** Confirm you have root, a working LVM toolchain, and the XFS userspace tools (`xfsprogs`) installed.

```bash
sudo -i
dnf install -y lvm2 xfsprogs util-linux
mkdir -p /root/lvm-xfs-lab && cd /root/lvm-xfs-lab
which pvcreate vgcreate lvcreate mkfs.xfs xfs_info xfs_growfs blkid mount
```

**Human-Readable Breakdown:**
> "Become root for the whole lab. Make sure the three packages we'll need are installed: `lvm2` (the PV/VG/LV tools), `xfsprogs` (the XFS family — `mkfs.xfs`, `xfs_info`, `xfs_growfs`, `xfs_repair`), and `util-linux` (which provides `blkid`, `mount`, `losetup`, `lsblk`). Create a clean working directory under `/root`. Confirm every command we'll need is on the `PATH`."

**Reading it left to right:**
- `sudo -i` → "interactive root login shell."
- `dnf install -y lvm2 xfsprogs util-linux` → "ensure all three packages; `-y` says yes to prompts."
- `mkdir -p /root/lvm-xfs-lab && cd /root/lvm-xfs-lab` → "workspace; `-p` won't error if it exists."
- `which pvcreate vgcreate ...` → "verify each binary has a real path on `$PATH`."

**The story:** On a stock RHEL 9 install, `xfsprogs` is installed by default — XFS is the system's default filesystem. On AWS RHEL AMIs and minimal cloud images, it's still installed because `/` is XFS. But on slim containers and custom-built images, `xfsprogs` is sometimes stripped. Five seconds of `which` upfront beats a confused "command not found" later. The combined-`which` pattern is also a great "did anything fail to install?" smoke test.

**Analogy:** A surgeon checking the tray for every instrument before scrubbing in. You don't notice the missing scalpel later — you notice it now.

**Expected output:**

```
/usr/sbin/pvcreate
/usr/sbin/vgcreate
/usr/sbin/lvcreate
/usr/sbin/mkfs.xfs
/usr/sbin/xfs_info
/usr/sbin/xfs_growfs
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
| `which: no mkfs.xfs` | `dnf install -y xfsprogs` |
| `which: no xfs_growfs` | Same — `xfs_growfs` is part of `xfsprogs` |
| `Error: Unable to find a match: xfsprogs` | Bad repo config; check `dnf repolist` |

---

### Task 2 — Inspect existing storage

**Purpose:** Read the current PV/VG/LV state before changing anything. Always know the starting point.

```bash
lsblk
pvs
vgs
lvs
findmnt -t xfs
```

**Human-Readable Breakdown:**
> "Hey kernel, show me every block device in a tree. Hey LVM, list every Physical Volume, every Volume Group, every Logical Volume. Hey `findmnt`, show me every currently-mounted XFS filesystem so I can see how RHEL uses XFS for `/` by default."

**Reading it left to right:**
- `lsblk` → "tree of block devices."
- `pvs` / `vgs` / `lvs` → "LVM summary tables."
- `findmnt -t xfs` → "tree of every mount whose filesystem type is `xfs`."

**The story:** RHEL 7+ default installs put `/` and most filesystems on XFS. Running `findmnt -t xfs` on a fresh box reveals the existing XFS deployment so you can mentally separate "OS-default XFS" from "the XFS I'm about to create." Combine this with the `lsblk`/`pvs`/`vgs`/`lvs` quartet from the ext4 lab — those four are the universal "current state" check.

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

TARGET SOURCE                 FSTYPE OPTIONS
/      /dev/mapper/rhel-root  xfs    rw,relatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,noquota
/boot  /dev/nvme0n1p1         xfs    rw,relatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,noquota
```

**Switches**

| Token | Meaning |
|---|---|
| `lsblk` | Tree view of block devices |
| `pvs` / `vgs` / `lvs` | LVM tabular summaries |
| `findmnt -t TYPE` | Mount tree filtered by FS type |

**Output decoded**

| Line | Meaning |
|---|---|
| `/` on XFS | RHEL 7+ default — confirms you're on a modern RHEL |
| `inode64,attr2` in options | XFS modern defaults — large-inode support, extended attributes v2 |
| `PFree 0` on existing PV | Root VG is fully consumed; we can't expand it without adding another PV |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `No volume groups found` | Either you have a non-LVM install, or `lvm2` isn't loaded — re-run Task 1 |
| `findmnt: unrecognized option '-t'` | Very old util-linux; upgrade or skip the flag |

---

### Task 3 — Create a loopback device to safely practice on

**Purpose:** Most lab VMs don't have a spare disk. A loopback device lets us pretend a file is a block device.

```bash
truncate -s 1G /root/lvm-xfs-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-xfs-lab/disk1.img)
echo "Using loopback: $LOOP"
losetup -a
```

**Human-Readable Breakdown:**
> "Hey shell, create a sparse 1 GiB file called `disk1.img`. Hey kernel, find the first free loop device (`-f`), attach `disk1.img` to it, also scan it for partitions (`-P`), print the loop device name you chose (`--show`), and capture that name into a shell variable `$LOOP` so we can reuse it in later commands. Then list all attached loop devices to confirm."

**Reading it left to right:**
- `truncate -s 1G FILE` → "create or grow a file to exactly the given size; on most filesystems this is *sparse* — no blocks consumed until written."
- `losetup -fP --show FILE` → "attach FILE to a loop device. `-f` = first free `/dev/loopN`; `-P` = re-read partition table; `--show` = print the chosen device name."
- `LOOP=$(...)` → "capture stdout into a shell variable for the rest of the lab."
- `losetup -a` → "list all active loopback associations."

**The story:** Loopback devices are an underrated superpower. They let you mock up disks, USB sticks, encrypted volumes, and partitioned drives entirely in software — perfect for labs, CI, and reproducing bug reports. Capturing the device name into `$LOOP` is a small ergonomic win: it makes the rest of the script self-documenting and resilient to which loop number the kernel happened to pick.

**Analogy:** A flight simulator. Same controls, same instruments, no risk of crashing a real airliner.

**Expected output:**

```
Using loopback: /dev/loop0
/dev/loop0: []: (/root/lvm-xfs-lab/disk1.img)
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
| `(/root/lvm-xfs-lab/disk1.img)` | The backing file |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `losetup: cannot find an unused loop device` | All loops in use; release one with `losetup -d /dev/loopN` |
| `Permission denied` writing the file | You're not root; rerun under `sudo -i` |

---

### Task 4 — Initialize the loopback as a Physical Volume

**Purpose:** Mark the loop device as available for LVM.

```bash
pvcreate "$LOOP"
pvs
pvdisplay "$LOOP"
```

**Human-Readable Breakdown:**
> "Hey LVM, write your metadata header onto the loop device so you know this device is fair game for your use. Then list all PVs to confirm the new entry. Finally print the verbose details for our specific PV — size, free space, UUID."

**Reading it left to right:**
- `pvcreate "$LOOP"` → "write LVM's PV header. From this moment on the device is owned by LVM."
- `pvs` → "table view."
- `pvdisplay "$LOOP"` → "verbose view."

**The story:** `pvcreate` writes a small (~1 MiB) metadata header to the device. It does *not* erase the data; it just tells LVM "you may use this device." If the device already had a filesystem, `pvcreate` will warn and ask for confirmation. **Read the warnings before you confirm** — wiping `/dev/sda` instead of `/dev/sdb` is the most common LVM career-ender.

**Analogy:** Putting a "FOR LVM USE" sticker on a USB stick. The data underneath isn't gone yet, but you've told the OS "this is my LVM scratch space now."

**Expected output:**

```
  Physical volume "/dev/loop0" successfully created.

  PV             VG   Fmt  Attr PSize    PFree
  /dev/loop0          lvm2 ---   1.00g   1.00g
  /dev/nvme0n1p2 rhel lvm2 a--  <29.00g     0

  --- Physical volume ---
  PV Name               /dev/loop0
  VG Name
  PV Size               1.00 GiB
  Allocatable           NO
  PE Size               0
  Total PE              0
  ...
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
| `PE Size: 0`, `Total PE: 0` | PE size is set by the VG, not the PV — empty until joined |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device /dev/loop0 not found` | Re-run Task 3 |
| `WARNING: ext4 signature detected` | Pre-existing signature; `wipefs -a $LOOP` first if you're sure |

---

### Task 5 — Create the Volume Group `vg1` with 8 MiB PE size

**Purpose:** The **headline difference from the ext4 lab.** We override the default PE size with `-s 8M` at `vgcreate` time.

```bash
vgcreate -s 8M vg1 "$LOOP"
vgs
vgdisplay vg1
```

**Human-Readable Breakdown:**
> "Hey LVM, create a Volume Group named `vg1` and put the loop device in it. Set the Physical Extent size to 8 MiB (`-s 8M`) **at creation time** because that size is fixed for the life of the VG. Then list all VGs to confirm. Then print the verbose details — paying close attention to the `PE Size` line."

**Reading it left to right:**
- `vgcreate` → "create-a-VG command."
- `-s 8M` → "**set the Physical Extent size to 8 MiB.** This is the one knob you can only set at creation."
- `vg1` → "the new VG name."
- `"$LOOP"` → "the PV(s) to pool. You can list multiple here."
- `vgs` / `vgdisplay vg1` → "tabular / verbose confirmation."

**The story:** **`-s SIZE` at `vgcreate` is the difference between a passing and failing exam answer when the question specifies a PE size.** Three rules to memorize: (1) **PE size is set once, at VG creation, and cannot be changed.** (2) **Every PV added later (via `vgextend`) inherits the VG's PE size.** (3) **The total number of PEs the VG can hold is roughly `PV size / PE size`.** With a 1020 MiB usable PV and 8 MiB PEs, you get 127 PEs (1016 MiB rounded down to a multiple of 8). That's plenty of room for our 10-extent LV.

**Analogy:** Choosing the brick size when you start building a wall. Once you've laid the first course, every brick after that must be the same size — you can't switch to bigger bricks halfway up.

**Expected output:**

```
  Volume group "vg1" successfully created

  VG     #PV #LV #SN Attr   VSize    VFree
  rhel     1   2   0 wz--n- <29.00g     0
  vg1      1   0   0 wz--n- 1016.00m 1016.00m

  --- Volume group ---
  VG Name               vg1
  System ID
  Format                lvm2
  Metadata Areas        1
  Metadata Sequence No  1
  VG Access             read/write
  VG Status             resizable
  MAX LV                0
  Cur LV                0
  Open LV               0
  Max PV                0
  Cur PV                1
  Act PV                1
  VG Size               1016.00 MiB
  PE Size               8.00 MiB
  Total PE              127
  Alloc PE / Size       0 / 0
  Free  PE / Size       127 / 1016.00 MiB
  VG UUID               4Hb6sN-...
```

**Switches**

| Token | Meaning |
|---|---|
| `vgcreate -s SIZE` | Set the Physical Extent size at VG creation |
| `vgcreate VG_NAME PVs...` | Make a new VG from one or more PVs |
| `vgs` / `vgdisplay` | Tabular / verbose VG views |

**Output decoded**

| Line | Meaning |
|---|---|
| `PE Size 8.00 MiB` | ✅ Confirms our `-s 8M` was honored |
| `Total PE 127` | 1016 MiB ÷ 8 MiB = 127 extents available |
| `Free PE / Size 127 / 1016.00 MiB` | Plenty of headroom for a 10-extent LV |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `PE Size 4.00 MiB` after creation | You forgot `-s 8M`. `vgremove vg1` and re-do this task. |
| `VG name vg1 already exists` | Either reuse it (confirm PE size is 8M) or `vgremove vg1` first |
| `Device /dev/loop0 excluded by a filter` | Pre-existing signature; `wipefs -a "$LOOP"` then retry |

---

### Task 6 — Verify the PE size with `vgdisplay` before sizing the LV

**Purpose:** **Always confirm PE size before `lvcreate`.** A wrong PE size silently produces a wrong-sized LV.

```bash
vgdisplay vg1 | grep -E "PE Size|Total PE|Free  PE"
```

**Human-Readable Breakdown:**
> "Hey shell, dump the verbose details of `vg1` but filter to just the three lines I care about: the PE Size (confirm it's 8 MiB), the Total PE count (confirm we have at least 10), and the Free PE count (confirm we haven't already allocated extents to some other LV by accident)."

**Reading it left to right:**
- `vgdisplay vg1` → "full verbose dump."
- `\|` → "pipe stdout."
- `grep -E "PE Size\|Total PE\|Free  PE"` → "extended regex matching any of three phrases. **Note the double space in `Free  PE`** — that's how `vgdisplay` formats it."

**The story:** The single most common RHCSA-storage mistake is sizing an LV by extent count (`-l 10`) without first confirming the VG's PE size. If the PE is 4 MiB you get a 40 MiB LV; if it's 8 MiB you get 80 MiB; if it's 16 MiB you get 160 MiB. Same command, three different filesystems. **`vgdisplay | grep "PE Size"` is the 2-second sanity check that prevents this.**

**Analogy:** Reading the scale on the ruler before you start measuring. Centimeters and inches look similar from a distance.

**Expected output:**

```
  PE Size               8.00 MiB
  Total PE              127
  Free  PE / Size       127 / 1016.00 MiB
```

**Switches**

| Token | Meaning |
|---|---|
| `grep -E PATTERN` | Extended regex grep |
| `\|` (alternation) | Match any of multiple patterns |

**Output decoded**

| Line | Meaning |
|---|---|
| `PE Size 8.00 MiB` | ✅ Required for the exam answer |
| `Total PE 127` | ≥ 10 — we have room |
| `Free PE 127` | All extents available; no other LVs in this VG |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `PE Size 4.00 MiB` | Wrong! Go back to Task 5 and re-create vg1 with `-s 8M` |
| `Free PE < 10` | Some other LV exists; `lvs` to find it, `lvremove` if appropriate |

---

### Task 7 — Create the Logical Volume `lv1` with 10 extents

**Purpose:** Carve an LV out of `vg1` using **10 logical extents** (`-l 10`), which at 8 MiB PE = **80 MiB total**.

```bash
lvcreate -l 10 -n lv1 vg1
lvs -o +seg_size,extents
lvdisplay /dev/vg1/lv1
```

**Human-Readable Breakdown:**
> "Hey LVM, carve an LV out of the `vg1` pool. Size it by **extent count** (`-l 10`), not by absolute bytes — that's how the exam phrased the question. Name it `lv1` (`-n lv1`). Then list all LVs but add columns for segment size and extent count. Then print the verbose details to confirm `Current LE = 10` and `LV Size = 80.00 MiB`."

**Reading it left to right:**
- `lvcreate` → "create-an-LV command."
- `-l 10` → "**lowercase `l` is extent count.** Uppercase `-L` is size. They are different flags."
- `-n lv1` → "name the LV `lv1`."
- `vg1` → "the VG to carve from."
- `lvs -o +seg_size,extents` → "default columns plus segment size and extent count."

**The story:** **Memorize the case distinction:** `-L 80M` is "80 megabytes by size" and `-l 10` is "10 extents by count." The two produce the same LV when PE=8M, but `-L 80M` would also work if PE were 4M (giving you 80 MiB = 20 extents). The exam often phrases questions as "10 extents" or "use 10 LEs" precisely to force you to remember the lowercase-`l` form. Other useful forms: `-l 50%FREE` (half the remaining VG space), `-l 100%VG` (all of the VG, including extents already used — wait, that's `100%FREE`).

**Analogy:** Two ways to order a pizza — by diameter (`-L 12in`) or by slice count (`-l 8 slices`). Both describe the same pizza if you've agreed on slice-size; one of them silently changes if you haven't.

**Expected output:**

```
  Logical volume "lv1" created.

  LV    VG   Attr       LSize   ... SegSize  #Ext
  root  rhel -wi-ao---- <26.00g       <26.00g  6655
  swap  rhel -wi-ao----   3.00g         3.00g   768
  lv1   vg1  -wi-a-----   80.00m       80.00m    10

  --- Logical volume ---
  LV Path                /dev/vg1/lv1
  LV Name                lv1
  VG Name                vg1
  LV UUID                pQ4nKr-...
  LV Status              available
  # open                 0
  LV Size                80.00 MiB
  Current LE             10
  Segments               1
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     256
  Block device           253:2
```

**Switches**

| Token | Meaning |
|---|---|
| `lvcreate -l COUNT` | Size by extent count |
| `lvcreate -L SIZE` | Size by absolute bytes |
| `lvcreate -l 100%FREE` | Use all remaining free space |
| `lvcreate -n NAME` | Name the new LV |
| `lvs -o +COLS` | Append columns to the default output |

**Output decoded**

| Field | Meaning |
|---|---|
| `LSize 80.00m` | ✅ Exactly what we expected: 10 × 8 MiB |
| `Current LE 10` | ✅ Confirms we got the extent count we asked for |
| `LV Path /dev/vg1/lv1` | The path you use in `mkfs.xfs` |
| `Attr -wi-a-----` | `w`=writable, `i`=inherited allocation, `a`=active. `o` appears after mount. |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `LSize 40.00m` | You're on a VG with 4 MiB PE size, not 8 MiB. Re-do Task 5. |
| `Volume group "vg1" has insufficient free space` | Should not happen with a 1 GiB loop; check Task 5 output |
| `Logical volume "lv1" already exists` | `lvremove /dev/vg1/lv1` then retry |

---

### Task 8 — Format the LV with XFS

**Purpose:** Lay an XFS filesystem on top of the LV block device.

```bash
mkfs.xfs -L lv1 /dev/vg1/lv1
```

**Human-Readable Breakdown:**
> "Hey `mkfs.xfs`, format the block device at `/dev/vg1/lv1` as XFS, and give it the human-readable label `lv1` (`-L lv1`) so it'll show up nicely in `lsblk -f` and `blkid`. Print the geometry you chose so I can sanity-check block size, AG count, and log size."

**Reading it left to right:**
- `mkfs.xfs` → "the XFS formatter."
- `-L lv1` → "filesystem label (max 12 chars for XFS — *shorter than ext4's 16*)."
- `/dev/vg1/lv1` → "the block device to format. **Double-check this path before pressing Enter.**"

**The story:** Three rules with `mkfs.xfs`: (1) **There is no undo.** The command instantly destroys whatever was on the device. (2) **XFS labels are max 12 characters.** ext4 allows 16. Cross-FS scripting often uses ≤12 to stay safe. (3) **`mkfs.xfs` chooses sensible defaults** — 4 KiB block size, 4 allocation groups for small FSes, internal log, CRC enabled (since RHEL 7). You almost never override these. On very small filesystems (under ~10 MiB) XFS may refuse to format ("must be at least 16 MiB") — another reason XFS isn't a great choice for tiny volumes.

**Analogy:** Painting the inside of the LV with XFS so it can hold files. Pre-paint, the LV is a block device. Post-paint, it's a filesystem.

**Expected output:**

```
meta-data=/dev/vg1/lv1           isize=512    agcount=4, agsize=5120 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=1, sparse=1, rmapbt=0
         =                       reflink=1    bigtime=1 inobtcount=1 nrext64=0
data     =                       bsize=4096   blocks=20480, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
log      =internal log           bsize=4096   blocks=1368, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
Discarding blocks...Done.
```

**Switches**

| Token | Meaning |
|---|---|
| `mkfs.xfs` | The XFS formatter |
| `-L LABEL` | Set the filesystem label (max 12 chars) |
| `-f` | Force-format even if a signature exists |
| `-b size=N` | Override block size (rare) |

**Output decoded**

| Line | Meaning |
|---|---|
| `agcount=4, agsize=5120 blks` | 4 allocation groups × 5120 blocks × 4096 = 80 MiB ✅ |
| `crc=1` | CRC checksumming enabled (RHEL 7+ default) |
| `bsize=4096` | 4 KiB block size (default; matches page size) |
| `blocks=20480` | 80 MiB ÷ 4 KiB = 20480 blocks ✅ |
| `internal log` | Journal lives inside the data section (default) |
| `Discarding blocks` | XFS issues TRIM/discard at format time for SSD-friendly behavior |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `/dev/vg1/lv1 appears to contain an existing filesystem` | `mkfs.xfs -f /dev/vg1/lv1` to force, *if you're sure* |
| `size must be at least 16 MiB` | Your LV is too small; bump the extent count |
| `mkfs.xfs: command not found` | `dnf install -y xfsprogs` |

---

### Task 9 — Inspect the new XFS filesystem

**Purpose:** Confirm the XFS superblock looks sane *before* mounting.

```bash
blkid /dev/vg1/lv1
lsblk -f /dev/vg1/lv1
xfs_info /dev/vg1/lv1 2>/dev/null || echo "xfs_info on unmounted device requires newer xfsprogs"
```

**Human-Readable Breakdown:**
> "Hey kernel, tell me about the new XFS filesystem three ways: (1) the UUID via `blkid`, (2) the label and FS-type via `lsblk -f`, and (3) the full geometry via `xfs_info` — falling back to a friendly message if our `xfsprogs` is too old to read an unmounted device (older versions require it to be mounted first)."

**Reading it left to right:**
- `blkid /dev/vg1/lv1` → "print UUID, LABEL, TYPE."
- `lsblk -f /dev/vg1/lv1` → "block-device tree with FS info."
- `xfs_info /dev/vg1/lv1` → "XFS geometry; on newer xfsprogs reads from device, on older only from mountpoint."
- `2>/dev/null || echo ...` → "if `xfs_info` errors (older version), suppress stderr and print a friendly hint."

**The story:** `blkid` is the **fstab-prep workhorse** — you copy its UUID straight into `/etc/fstab`. `lsblk -f` is the **at-a-glance** view. `xfs_info` is the **deep-dive** that we'll come back to in Task 11 after we've mounted. The fallback pattern (`cmd || echo`) is a clean way to handle "this might not work on older systems" without polluting the lab with error messages.

**Analogy:** Three different X-rays of the same chest — frontal, side, and 3D reconstruction. Each one shows you something the others miss.

**Expected output:**

```
/dev/vg1/lv1: LABEL="lv1" UUID="8b3f4e2a-1234-5678-9abc-def012345678" TYPE="xfs"

NAME FSTYPE FSVER LABEL UUID                                 FSAVAIL FSUSE% MOUNTPOINTS
lv1  xfs    -     lv1   8b3f4e2a-1234-5678-9abc-def012345678

meta-data=/dev/vg1/lv1           isize=512    agcount=4, agsize=5120 blks
...
```

**Switches**

| Token | Meaning |
|---|---|
| `blkid DEV` | Print UUID, LABEL, TYPE |
| `lsblk -f DEV` | Tree view with FS columns |
| `xfs_info DEV\|MOUNTPOINT` | XFS geometry dump |

**Output decoded**

| Field | Meaning |
|---|---|
| `UUID="..."` | The string you'll paste into `/etc/fstab` |
| `TYPE="xfs"` | The fstab `<fstype>` column will be `xfs` |
| `LABEL="lv1"` | Confirms our `-L lv1` at `mkfs.xfs` |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `blkid` shows nothing | `udevadm settle` then retry; cache hadn't refreshed |
| `xfs_info` says "must be mounted" | Skip ahead to Task 10 then re-run `xfs_info` against the mountpoint |

---

### Task 10 — Create the mount point

**Purpose:** A mount point is just an empty directory. Make sure ours exists before mounting.

```bash
mkdir -p /mnt/lvfs1
ls -ld /mnt/lvfs1
```

**Human-Readable Breakdown:**
> "Hey shell, make sure the directory `/mnt/lvfs1` exists. If parent directories are missing, create them too (`-p`). If it already exists, don't error. Then list it in long form to confirm it's an empty directory owned by root."

**Reading it left to right:**
- `mkdir -p /mnt/lvfs1` → "create directory; `-p` = create parents, don't error on existing."
- `ls -ld /mnt/lvfs1` → "list the directory *itself* (`-d`) in long format, not its contents."

**The story:** Mounting a filesystem on top of a directory **hides** whatever was in that directory until you unmount. If you mount on a populated directory, the data underneath is invisible (and reappears on unmount). For safety, always mount on an empty directory you just made. The conventional path for "extra mounts unrelated to the OS hierarchy" is `/mnt/<something>`.

**Analogy:** Setting up a transparent stage over a poker table. Once the stage is in place, you can't see the cards underneath. Take the stage down (`umount`) and they reappear.

**Expected output:**

```
drwxr-xr-x. 2 root root 6 May 22 13:51 /mnt/lvfs1
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
| Pre-existing files in `/mnt/lvfs1` | Move them out first, or pick a different mountpoint |

---

### Task 11 — Mount the LV manually (one-time test)

**Purpose:** Test the mount before persistence. If it fails here, fstab will fail at boot too.

```bash
mount /dev/vg1/lv1 /mnt/lvfs1
mount | grep lvfs1
df -hT /mnt/lvfs1
xfs_info /mnt/lvfs1
```

**Human-Readable Breakdown:**
> "Hey kernel, mount the block device `/dev/vg1/lv1` on the directory `/mnt/lvfs1`. Confirm with `mount | grep`. Print the disk-free with type column. Now that the FS is mounted, dump its full XFS geometry — this is the canonical way to read XFS internals."

**Reading it left to right:**
- `mount SRC DEST` → "attach SRC's filesystem at DEST. FS type is auto-detected via `blkid`."
- `mount | grep lvfs1` → "confirm our LV is now mounted."
- `df -hT /mnt/lvfs1` → "disk-free for that one path; `-h` = human units, `-T` = include TYPE column."
- `xfs_info /mnt/lvfs1` → "full XFS geometry from a mounted filesystem."

**The story:** Always test mounts manually before adding to fstab. A bad fstab entry can render the system unbootable. By rehearsing `mount /dev/vg1/lv1 /mnt/lvfs1` first, you catch every bug on your timescale instead of at boot. `xfs_info` against a mountpoint also works on older xfsprogs — it's the most portable way to inspect XFS geometry.

**Analogy:** Test-driving a car around the block before pulling it onto the freeway. The mount-by-hand step is your block.

**Expected output:**

```
/dev/mapper/vg1-lv1 on /mnt/lvfs1 type xfs (rw,relatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,noquota)

Filesystem          Type Size  Used Avail Use% Mounted on
/dev/mapper/vg1-lv1 xfs   75M  5.5M   70M   8% /mnt/lvfs1

meta-data=/dev/mapper/vg1-lv1    isize=512    agcount=4, agsize=5120 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=1, sparse=1, rmapbt=0
         =                       reflink=1    bigtime=1 inobtcount=1 nrext64=0
data     =                       bsize=4096   blocks=20480, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
log      =internal log           bsize=4096   blocks=1368, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```

**Switches**

| Token | Meaning |
|---|---|
| `mount SRC DEST` | One-shot mount |
| `df -hT` | Human-readable with type column |
| `xfs_info MOUNT` | Full XFS geometry |

**Output decoded**

| Field | Meaning |
|---|---|
| `/dev/mapper/vg1-lv1` | Kernel's device-mapper name (symlinked from `/dev/vg1/lv1`) |
| `type xfs` | Auto-detected filesystem type |
| `attr2,inode64` | XFS modern defaults |
| `Size 75M` | A bit less than 80 MiB — XFS reserves space for the log + AG metadata |
| `agcount=4` | 4 allocation groups for our 80 MiB filesystem |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount: /mnt/lvfs1: special device /dev/vg1/lv1 does not exist` | Wrong VG/LV name; check Task 7 |
| `wrong fs type, bad option, bad superblock` | Forgot `mkfs.xfs` (Task 8) |
| `/mnt/lvfs1: mount point does not exist` | Forgot `mkdir -p` (Task 10) |

---

### Task 12 — Capture the UUID for `/etc/fstab`

**Purpose:** Persistent mounts should reference UUIDs, not device paths. Pull the UUID into a variable.

```bash
UUID=$(blkid -s UUID -o value /dev/vg1/lv1)
echo "UUID is: $UUID"
```

**Human-Readable Breakdown:**
> "Hey `blkid`, print just the UUID *value* of `/dev/vg1/lv1`. No `UUID=` prefix, no quotes. Stuff that string into a shell variable `UUID`. Then echo it so I can see it before I paste it into the next command."

**Reading it left to right:**
- `blkid` → "block-id probe."
- `-s UUID` → "print only the `UUID` tag (skip `TYPE`, `LABEL`, etc.)."
- `-o value` → "output format = just the value, no `KEY=` wrapper."
- `UUID=$(...)` → "shell command substitution; assign the captured stdout to `UUID`."

**The story:** **UUIDs over device paths in fstab.** Device paths like `/dev/sdb1` can change between reboots when disks are added/removed — and the boot will fail with "can't find /dev/sdb1" if the kernel renumbers. UUIDs are baked into the filesystem itself and survive every reorder. The exam grader will accept either, but real production always uses UUIDs.

**Analogy:** Like phone contacts — you don't call your contacts by phone number, you call them by name (the UUID), because phone numbers (device paths) might change.

**Expected output:**

```
UUID is: 8b3f4e2a-1234-5678-9abc-def012345678
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
| Empty `$UUID` | Filesystem not formatted (Task 8) or device wrong |
| Different UUID after re-mkfs | Each `mkfs.xfs` invocation generates a new UUID; re-pull it |

---

### Task 13 — Add the persistent mount line to `/etc/fstab`

**Purpose:** Make the mount survive reboots.

```bash
umount /mnt/lvfs1
echo "UUID=$UUID  /mnt/lvfs1  xfs  defaults  0 0" | tee -a /etc/fstab
tail -1 /etc/fstab
```

**Human-Readable Breakdown:**
> "First unmount the manual mount from Task 11 — we want to remount via fstab to prove fstab works. Then write a new line into `/etc/fstab` with six whitespace-separated fields: the UUID, the mountpoint `/mnt/lvfs1`, the filesystem type `xfs`, default options, no dump backup (`0`), no fsck pass priority (`0` — XFS doesn't use boot-time fsck anyway). Print the last line of fstab to confirm."

**Reading it left to right:**
- `umount /mnt/lvfs1` → "unmount so we can re-mount via fstab and prove fstab is working."
- `echo "UUID=$UUID  /mnt/lvfs1  xfs  defaults  0 0"` → "construct the fstab line. **Six fields**."
- `\| tee -a /etc/fstab` → "append to fstab AND print to stdout simultaneously."
- `tail -1 /etc/fstab` → "echo back the last line as a sanity check."

**The story:** The six fstab fields, in order: **device** (UUID/LABEL/path), **mountpoint**, **fstype**, **options**, **dump** (always `0` on modern systems), **fsck pass** (`0` for XFS — XFS does not use the boot-time fsck mechanism; it self-checks via log replay on mount). **The `pass` column being `0` is the one fstab-syntax difference between XFS and ext4** — ext4 entries for non-root filesystems often use `2`, but XFS *always* uses `0`. Putting `2` for XFS doesn't break boot (the kernel skips it), but it's a tell that the admin doesn't know XFS.

**Analogy:** Adding a reservation to a calendar. The reservation says *at boot, mount this filesystem on this directory with these options*. fstab is read every boot.

**Expected output:**

```
UUID=8b3f4e2a-1234-5678-9abc-def012345678  /mnt/lvfs1  xfs  defaults  0 0
UUID=8b3f4e2a-1234-5678-9abc-def012345678  /mnt/lvfs1  xfs  defaults  0 0
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
| `/mnt/lvfs1` | Mountpoint |
| `xfs` | Filesystem type |
| `defaults` | `rw,suid,dev,exec,auto,nouser,async` |
| `0` (dump) | Skip backup |
| `0` (pass) | **Always `0` for XFS** (XFS uses log replay, not boot fsck) |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `umount: target is busy` | Some process has a file open in `/mnt/lvfs1`; `lsof +D /mnt/lvfs1` to find it |
| `Permission denied` writing fstab | Not root |

---

### Task 14 — Test fstab with `mount -a` *before* rebooting

**Purpose:** A broken fstab line can prevent boot. **Always test with `mount -a` before rebooting.**

```bash
mount -a
mount | grep lvfs1
df -hT /mnt/lvfs1
```

**Human-Readable Breakdown:**
> "Hey kernel, walk through `/etc/fstab` and mount every entry that's not already mounted. If my new line is broken, `mount -a` will fail right now — on the command line — not at next boot when I'm staring at an emergency-mode prompt. Then confirm with `mount` and `df -hT`."

**Reading it left to right:**
- `mount -a` → "mount *all* fstab entries with `auto` in their options (which `defaults` includes)."
- `mount | grep lvfs1` → "confirm our LV is now mounted via fstab."
- `df -hT /mnt/lvfs1` → "size check."

**The story:** **`mount -a` is the seatbelt of fstab editing.** Every senior admin runs it immediately after touching fstab. If the line is wrong — typo in UUID, wrong filesystem type, missing mountpoint — `mount -a` fails *with a clear error* on your terminal. You fix the fstab and reboot with confidence. Skip this step and you'll find out at boot, when the system drops into emergency mode and you have to remember the root password.

**Analogy:** Pulling on the parking brake before driving away. Five seconds; saves a fender-bender.

**Expected output:**

```
/dev/mapper/vg1-lv1 on /mnt/lvfs1 type xfs (rw,relatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,noquota)

Filesystem          Type Size  Used Avail Use% Mounted on
/dev/mapper/vg1-lv1 xfs   75M  5.5M   70M   8% /mnt/lvfs1
```

**Switches**

| Token | Meaning |
|---|---|
| `mount -a` | Mount all `auto` fstab entries |
| `mount` | List active mounts |
| `df -hT PATH` | Human-readable disk usage with type column |

**Output decoded**

| Line | Meaning |
|---|---|
| Mount entry present | fstab line was parsed and the mount succeeded |
| `Size 75M` | Same as before — same filesystem, just mounted via fstab now |
| `Use% 8%` | XFS metadata + log = ~5.5M overhead on an 80M filesystem |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount: /mnt/lvfs1: can't find UUID=...` | UUID typo in fstab; re-pull with Task 12 and re-edit |
| `mount: bad option` | Typo in the options column |
| `wrong fs type` | Wrote `ext4` instead of `xfs` in fstab |

---

### Task 15 — Confirm `systemctl daemon-reload` after fstab edits

**Purpose:** systemd generates `.mount` units from fstab. After editing fstab, ask systemd to regenerate.

```bash
systemctl daemon-reload
systemctl status mnt-lvfs1.mount --no-pager
```

**Human-Readable Breakdown:**
> "Hey systemd, re-scan fstab and regenerate the `.mount` units you build from it. Then show me the status of `mnt-lvfs1.mount` — the unit that corresponds to `/mnt/lvfs1`. Note that systemd derives the unit name by replacing `/` with `-` and stripping the leading `/` (so `/mnt/lvfs1` → `mnt-lvfs1.mount`)."

**Reading it left to right:**
- `systemctl daemon-reload` → "rescan unit files *and* regenerate fstab-derived mount units."
- `systemctl status mnt-lvfs1.mount` → "show the status of the auto-generated unit."
- `--no-pager` → "direct stdout."

**The story:** On modern RHEL, systemd manages mounts *through generated `.mount` units* that mirror fstab entries. Edit fstab and run `daemon-reload`, and you'll see a fresh `.mount` unit. This is also why fstab edits are picked up by `mount -a` immediately — fstab is the source-of-truth, and systemd re-derives the unit graph from it on demand.

**Analogy:** Editing a recipe and asking the chef to re-read the cookbook. Without the re-read, the chef cooks from memory of the old recipe.

**Expected output:**

```
● mnt-lvfs1.mount - /mnt/lvfs1
     Loaded: loaded (/etc/fstab; generated)
     Active: active (mounted) since Fri 2026-05-22 13:55:42 EDT; 2min ago
      Where: /mnt/lvfs1
       What: /dev/mapper/vg1-lv1
       ...
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
| `Where: /mnt/lvfs1` / `What: /dev/...` | The two sides of the mount |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Unit mnt-lvfs1.mount not loaded` | Forgot `daemon-reload`, or the fstab line failed to parse |

---

### Task 16 — Drop a test file and verify writes

**Purpose:** A mount that doesn't accept writes is a broken mount. The sample exam explicitly says "drop a test file."

```bash
echo "hello from lv1 (XFS) at $(date)" | tee /mnt/lvfs1/test.txt
ls -l /mnt/lvfs1
df -hT /mnt/lvfs1
stat /mnt/lvfs1/test.txt
```

**Human-Readable Breakdown:**
> "Hey shell, write a line into `/mnt/lvfs1/test.txt` that includes the current date — proving this is a fresh write, not a leftover. Use `tee` to echo to stdout simultaneously. Then list the directory, check disk-free, and `stat` the file to see its inode info — XFS uses 512-byte inodes by default, much larger than ext4's 256-byte inodes, so it can hold more extended attributes inline."

**Reading it left to right:**
- `echo "hello from lv1 (XFS) at $(date)"` → "construct the line; `$(date)` substitutes the current timestamp."
- `\| tee /mnt/lvfs1/test.txt` → "write to the file AND print to stdout."
- `ls -l /mnt/lvfs1` → "verify the file appears on the LV."
- `df -hT /mnt/lvfs1` → "confirm `Use%` ticked up."
- `stat /mnt/lvfs1/test.txt` → "see inode number, size, atime/mtime/ctime, block count."

**The story:** Always do an end-to-end write test on a fresh mount. The mount can succeed yet the filesystem be read-only (e.g. due to a kernel-detected error remount, or `ro` in fstab options). The only way to know it's truly writable is to *write something*. **`stat` is also a hidden RHCSA favorite** — it shows the inode number, link count, block allocation, all four timestamps (access, modify, change, birth), and the SELinux context. Worth learning to read fluently.

**Analogy:** Turning on the faucet to confirm the new plumbing works. Pipes can be installed correctly and still have no water.

**Expected output:**

```
hello from lv1 (XFS) at Fri May 22 14:02:18 EDT 2026

total 4
-rw-r--r--. 1 root root 38 May 22 14:02 test.txt

Filesystem          Type Size  Used Avail Use% Mounted on
/dev/mapper/vg1-lv1 xfs   75M  5.5M   70M   8% /mnt/lvfs1

  File: /mnt/lvfs1/test.txt
  Size: 38              Blocks: 8          IO Block: 4096   regular file
Device: fc02h/64514d    Inode: 99          Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Context: unconfined_u:object_r:mnt_t:s0
Access: 2026-05-22 14:02:18.000000000 -0400
Modify: 2026-05-22 14:02:18.000000000 -0400
Change: 2026-05-22 14:02:18.000000000 -0400
 Birth: 2026-05-22 14:02:18.000000000 -0400
```

**Switches**

| Token | Meaning |
|---|---|
| `echo "X" \| tee FILE` | Write + echo |
| `ls -l` | Long listing |
| `stat FILE` | Inode and metadata dump |

**Output decoded**

| Field | Meaning |
|---|---|
| `test.txt` exists | Filesystem accepts writes |
| `Blocks: 8` | XFS allocated 8 × 512-byte blocks = 4 KiB for our 38-byte file (one filesystem block) |
| `Birth` timestamp present | XFS supports creation time (`crtime`); ext4 didn't until kernel 4.11 |
| `Context: ... mnt_t` | SELinux assigned the default mount-type context |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Read-only file system` | Mount options have `ro`; check fstab |
| `No space left on device` | The 80 MiB filled up — actually a successful write proof if it took a while |

---

### Task 17 — Compare XFS vs ext4 behaviors

**Purpose:** Internalize the three big XFS-vs-ext4 differences you must remember on exam day.

```bash
# 1. XFS uses xfs_growfs, not resize2fs
which xfs_growfs resize2fs

# 2. XFS cannot shrink — confirm by reading the man page summary
man xfs_growfs 2>/dev/null | grep -A1 -i "cannot.*decrease\|cannot.*shrink\|no.*shrink" | head -5

# 3. XFS fsck-pass is 0 in fstab (uses log replay, not boot fsck)
grep "/mnt/lvfs1" /etc/fstab
```

**Human-Readable Breakdown:**
> "Three quick checks that compare XFS to ext4 on the differences that matter for the exam: (1) `xfs_growfs` and `resize2fs` are both installed but they serve different filesystems — XFS uses the former, ext4 uses the latter; (2) the XFS man page explicitly says it cannot shrink; (3) confirm our fstab line uses `0` for the fsck-pass column, because XFS does log replay on mount instead of boot-time fsck."

**Reading it left to right:**
- `which xfs_growfs resize2fs` → "confirm both are installed so you can see they coexist."
- `man xfs_growfs | grep ...` → "show the man-page text that documents the no-shrink rule."
- `grep "/mnt/lvfs1" /etc/fstab` → "re-read our line and verify `0 0` at the end."

**The story:** **The three XFS-vs-ext4 differences that exam graders care about:** (1) **Grow tool:** `xfs_growfs MOUNTPOINT` for XFS, `resize2fs DEVICE` for ext4 — note the different argument too (mountpoint vs device). (2) **Shrinking:** XFS cannot, ext4 can (with care). (3) **fstab pass column:** XFS = `0`, ext4 non-root = `2`. There's also a fourth difference worth knowing: **XFS uses 512-byte inodes** by default (vs ext4's 256-byte), which holds more extended attributes inline. This last one isn't tested directly but explains why XFS feels "snappier" on SELinux-heavy workloads.

**Analogy:** Two cars from the same factory — same chassis, different transmissions. You drive them the same way 95% of the time, but the 5% where they differ is where the test questions live.

**Expected output:**

```
/usr/sbin/xfs_growfs
/usr/sbin/resize2fs

       Note that the filesystem must be mounted to be grown.  The contents of the filesystem
       remain accessible during the grow operation.  Also note that XFS cannot be shrunk
       once created.

UUID=8b3f4e2a-1234-5678-9abc-def012345678  /mnt/lvfs1  xfs  defaults  0 0
```

**Switches**

| Token | Meaning |
|---|---|
| `which` | Find binaries on PATH |
| `man PAGE \| grep` | Extract a phrase from a man page |
| `grep -A1` | Print 1 line after each match |

**Output decoded**

| Line | Meaning |
|---|---|
| Both `xfs_growfs` and `resize2fs` present | Both filesystem families are usable; you pick by FS type |
| `XFS cannot be shrunk` | Memorize this — exam will test it |
| `0 0` at end of fstab line | XFS uses log replay, not boot fsck |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `man xfs_growfs` empty grep | Older man pages phrase it differently; just read the full page |
| `resize2fs` not installed | `dnf install -y e2fsprogs` |

---

### Task 18 — Simulate a reboot with `umount` + `mount -a`

**Purpose:** The real "does it survive reboot?" test. Faster than rebooting.

```bash
cd /
umount /mnt/lvfs1
mount | grep lvfs1 || echo "Not mounted - good, we will remount via fstab"
mount -a
mount | grep lvfs1
cat /mnt/lvfs1/test.txt
```

**Human-Readable Breakdown:**
> "First `cd /` so our shell isn't sitting inside `/mnt/lvfs1` (which would block the unmount). Then unmount. Confirm it's gone with a friendly message if grep finds nothing. Now ask the kernel to walk fstab — exactly what happens at boot. Confirm `/mnt/lvfs1` came back. Read the test file we wrote in Task 16 to prove the data persisted."

**Reading it left to right:**
- `cd /` → "leave the mountpoint so we don't block our own unmount."
- `umount /mnt/lvfs1` → "unmount."
- `mount | grep lvfs1 \|\| echo "Not mounted..."` → "if grep finds nothing, print a friendly message."
- `mount -a` → "boot-time fstab walk simulated."
- `cat /mnt/lvfs1/test.txt` → "read the file. If you see your line, data survived."

**The story:** `umount + mount -a` is the **poor-person's reboot.** It exercises the exact same code path the kernel runs at boot, but in 0.1 seconds instead of 60. Use it after every fstab edit. The `cd /` reflex is a small but important habit — `umount` will refuse with "target is busy" if your shell is sitting in the directory you're trying to unmount, and beginners spend minutes debugging an error that vanishes the moment they `cd` out.

**Analogy:** Test-firing the reboot without actually rebooting. Same end state, much faster cycle.

**Expected output:**

```
Not mounted - good, we will remount via fstab

/dev/mapper/vg1-lv1 on /mnt/lvfs1 type xfs (rw,relatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,noquota)

hello from lv1 (XFS) at Fri May 22 14:02:18 EDT 2026
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
| `hello from lv1 (XFS)...` | Data persisted across umount/remount |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `umount: target is busy` | Forgot `cd /`; or another process is in the mount — `lsof +D /mnt/lvfs1` |
| Empty `test.txt` after remount | You re-mkfs'd somewhere along the way; data was destroyed |

---

### Task 19 — Clean teardown (bottom-up)

**Purpose:** Remove every layer cleanly so the lab is repeatable. **Tear down bottom-up — opposite of build order.**

```bash
cd /
sed -i '/\/mnt\/lvfs1/d' /etc/fstab
systemctl daemon-reload
umount /mnt/lvfs1
rmdir /mnt/lvfs1
lvremove -y /dev/vg1/lv1
vgremove -y vg1
pvremove -y "$LOOP"
losetup -d "$LOOP"
rm -f /root/lvm-xfs-lab/disk1.img
pvs ; vgs ; lvs
```

**Human-Readable Breakdown:**
> "Hey shell, leave the mount directory first. Strip the fstab line (`sed -i '/MATCH/d'`). Tell systemd to re-scan units. Unmount. Remove the empty mountpoint. Tear the LV down. Tear the VG down. Strip LVM metadata from the loop device. Detach the loop device. Delete the backing file. Print the three LVM summaries to confirm everything's gone."

**Reading it left to right:**
- `cd /` → "leave the mount directory."
- `sed -i '/\/mnt\/lvfs1/d' /etc/fstab` → "in-place delete every line matching `/mnt/lvfs1`. Forward slashes escaped."
- `systemctl daemon-reload` → "regenerate fstab-derived mount units now that the line is gone."
- `umount /mnt/lvfs1` → "unmount."
- `rmdir /mnt/lvfs1` → "remove the empty directory."
- `lvremove -y /dev/vg1/lv1` → "remove LV; `-y` skips the 'are you sure?' prompt."
- `vgremove -y vg1` → "remove VG."
- `pvremove -y "$LOOP"` → "strip LVM signature."
- `losetup -d "$LOOP"` → "detach loop device."
- `rm -f /root/lvm-xfs-lab/disk1.img` → "delete backing file."
- `pvs ; vgs ; lvs` → "confirm everything's gone."

**The story:** Teardown order matters: **fstab → unmount → rmdir → lvremove → vgremove → pvremove → losetup -d.** Skip any step and the next one errors with "in use." This is the most common LVM frustration on the exam — candidates panic, retry, get more errors, and lose minutes. Memorize the order.

**Analogy:** Demolishing a building. You take down the roof before the walls, the walls before the foundation. Try it the other way and the wreckage crushes you on the way down.

**Expected output:**

```
  Logical volume "lv1" successfully removed
  Volume group "vg1" successfully removed
  Labels on physical volume "/dev/loop0" successfully wiped.

  PV             VG   Fmt  Attr PSize    PFree
  /dev/nvme0n1p2 rhel lvm2 a--  <29.00g     0

  VG   #PV #LV #SN Attr   VSize   VFree
  rhel   1   2   0 wz--n- <29.00g     0

  LV   VG   Attr       LSize   ...
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
| `umount: target is busy` | Forgot `cd /`; or process holding the mount |
| `Logical volume vg1/lv1 is used by another device` | Forgot to umount first |
| `Can't open /dev/loop0 exclusively` | LVM hasn't released it; retry after `udevadm settle` |

---

### Task 20 — Capstone: full RHCSA sample-exam scenario, end-to-end

**Task statement:** *"Create a logical volume named `lv1` in volume group `vg1`. Configure the volume group with 8 MiB physical extents and the logical volume with 10 logical extents. Format the LV with XFS and mount it persistently on `/mnt/lvfs1`. Drop a test file into the mounted filesystem to prove it works."*

```bash
# 1. Substrate: a 1 GiB loopback (on a real exam VM, use /dev/sdb instead)
truncate -s 1G /root/lvm-xfs-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-xfs-lab/disk1.img)
echo "Using loopback: $LOOP"

# 2. PV → VG (with 8M PE) → LV (10 extents)
pvcreate "$LOOP"
vgcreate -s 8M vg1 "$LOOP"
lvcreate -l 10 -n lv1 vg1

# 3. Filesystem + mountpoint
mkfs.xfs -L lv1 /dev/vg1/lv1
mkdir -p /mnt/lvfs1

# 4. Persistent mount
UUID=$(blkid -s UUID -o value /dev/vg1/lv1)
echo "UUID=$UUID  /mnt/lvfs1  xfs  defaults  0 0" | tee -a /etc/fstab
systemctl daemon-reload
mount -a

# 5. Drop the test file
echo "hello from lv1 (XFS) at $(date)" | tee /mnt/lvfs1/test.txt

# 6. Verify (the four lines that prove the exam answer)
vgdisplay vg1 | grep "PE Size"
lvs -o lv_name,vg_name,lv_size,seg_size,extents vg1
df -hT /mnt/lvfs1
grep lvfs1 /etc/fstab
cat /mnt/lvfs1/test.txt
```

**Human-Readable Breakdown:**
> "End-to-end exam answer in one block. Set up a 1 GiB loopback (substitute `/dev/sdb` on a real exam VM). Build the LVM stack in three commands with the **PE size set at `vgcreate` time** (`-s 8M`) and the **LV sized by extent count** (`-l 10`). Format XFS with a label. Create the mountpoint. Capture the UUID. Append a `defaults 0 0` fstab line. Reload systemd. Test with `mount -a`. Drop the required test file. Verify with five commands that prove: PE size = 8 MiB, extent count = 10, FS type = XFS, fstab entry persistent, test file readable."

**Reading it left to right:**

| Block | What it does |
|---|---|
| `truncate -s 1G ...` + `losetup -fP --show ...` | Create a virtual disk for safe practice |
| `pvcreate "$LOOP"` | Mark it as an LVM PV |
| `vgcreate -s 8M vg1 "$LOOP"` | Pool into VG `vg1` **with custom 8 MiB PE size** |
| `lvcreate -l 10 -n lv1 vg1` | The headline command: **10 extents** LV named `lv1` |
| `mkfs.xfs -L lv1 /dev/vg1/lv1` | XFS filesystem with a friendly label |
| `mkdir -p /mnt/lvfs1` | Mountpoint |
| `blkid -s UUID -o value ...` | Bare UUID for fstab |
| `tee -a /etc/fstab` | Append `UUID=... /mnt/lvfs1 xfs defaults 0 0` |
| `systemctl daemon-reload` + `mount -a` | Pick up the new line and prove it boots |
| `echo ... \| tee /mnt/lvfs1/test.txt` | The required test file |
| The five verification commands | Prove every requirement of the task statement |

**The story:** This is the **5-minute exam answer.** Memorize the spine: `pvcreate → vgcreate -s 8M → lvcreate -l 10 → mkfs.xfs → mkdir → blkid → tee fstab → daemon-reload → mount -a → test file → verify`. The two things that distinguish this from the ext4 lab capstone are: (1) **`-s 8M` at `vgcreate`** and (2) **`-l 10` at `lvcreate`**. Everything else is identical to the ext4 workflow except `mkfs.xfs` instead of `mkfs.ext4` and `xfs` instead of `ext4` in the fstab line.

**Analogy:** Memorizing the closing argument of a courtroom speech. The structure is fixed; the names and numbers change. If you've memorized the ext4 capstone, this one is two diffs away.

**Expected output (last six blocks):**

```
  PE Size               8.00 MiB

  LV   VG  LSize  SegSize  #Ext
  lv1  vg1 80.00m  80.00m    10

Filesystem          Type Size  Used Avail Use% Mounted on
/dev/mapper/vg1-lv1 xfs   75M  5.5M   70M   8% /mnt/lvfs1

UUID=8b3f4e2a-1234-5678-9abc-def012345678  /mnt/lvfs1  xfs  defaults  0 0

hello from lv1 (XFS) at Fri May 22 14:02:18 EDT 2026
```

**Verification checklist**

| Requirement | Command | Expected |
|---|---|---|
| VG uses 8 MiB PE size | `vgdisplay vg1 \| grep "PE Size"` | `PE Size 8.00 MiB` |
| LV has exactly 10 LEs | `lvs -o lv_name,extents vg1` | `lv1 ... 10` |
| LV size is 80 MiB | `lvs vg1` | `lv1 vg1 ... 80.00m` |
| Filesystem is XFS | `df -hT /mnt/lvfs1` | type `xfs` |
| Persistent via UUID | `grep lvfs1 /etc/fstab` | `UUID=... /mnt/lvfs1 xfs ...` |
| Test file present | `cat /mnt/lvfs1/test.txt` | The line you wrote |
| Survives reboot | `umount && mount -a` | Re-mounts cleanly (Task 18) |

**Cleanup**

```bash
cd /
sed -i '/\/mnt\/lvfs1/d' /etc/fstab
systemctl daemon-reload
umount /mnt/lvfs1
rmdir /mnt/lvfs1
lvremove -y /dev/vg1/lv1
vgremove -y vg1
pvremove -y "$LOOP"
losetup -d "$LOOP"
rm -f /root/lvm-xfs-lab/disk1.img
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `LV Size` is `40.00m` instead of `80.00m` | Forgot `-s 8M` at `vgcreate`. Tear down, re-do Task 5. |
| `mkfs.xfs` complains about a signature | `mkfs.xfs -f /dev/vg1/lv1` (force), if you're sure |
| `mount -a` fails | UUID typo in fstab; re-capture with `blkid -s UUID -o value /dev/vg1/lv1` |
| `xfs_info` not available on unmounted device | Mount first, then `xfs_info /mnt/lvfs1` |

---

## 🔍 LVM + XFS Storage Decision Guide

```
Got a storage task that specifies XFS or specifies PE/extent count?
  │
  ├── "Create LV with PE size X and extent count Y, format XFS"
  │       └── ✅ vgcreate -s XM VG /dev/...
  │           ✅ lvcreate -l Y -n LV VG
  │           ✅ mkfs.xfs /dev/VG/LV
  │           ✅ fstab with xfs and 0 0 in last two columns
  │
  ├── "Grow XFS without unmounting"
  │       └── ✅ lvextend -L +SIZE /dev/VG/LV
  │           ✅ xfs_growfs /MOUNTPOINT     (not the device — the mountpoint!)
  │
  ├── "Shrink XFS"
  │       └── ❌ NOT POSSIBLE on XFS. The exam is testing whether you recognize this.
  │           If shrink is truly required, the answer is: back up, mkfs again at smaller
  │           size, restore. Or use ext4 instead.
  │
  ├── "Repair a damaged XFS"
  │       └── ✅ umount /MOUNTPOINT
  │           ✅ xfs_repair /dev/VG/LV       (note: device, not mountpoint, when offline)
  │           ✅ mount again
  │
  └── "Format something other than XFS on RHEL"
          └── ✅ Use the [lvm-create-lvol1-ext4](../lvm-create-lvol1-ext4/) lab for the ext4 path
```

---

## ✅ Lab Checklist (20 Tasks)

- [ ] 01 Install `lvm2` + `xfsprogs` + verify toolchain
- [ ] 02 Read baseline `lsblk` / `pvs` / `vgs` / `lvs` / `findmnt -t xfs`
- [ ] 03 Create loopback `disk1.img` + capture name in `$LOOP`
- [ ] 04 `pvcreate "$LOOP"`
- [ ] 05 `vgcreate -s 8M vg1 "$LOOP"`     ← **the PE-size step**
- [ ] 06 Verify PE size with `vgdisplay | grep "PE Size"`
- [ ] 07 `lvcreate -l 10 -n lv1 vg1`     ← **the extent-count step**
- [ ] 08 `mkfs.xfs -L lv1 /dev/vg1/lv1`
- [ ] 09 `blkid` + `lsblk -f` inspection
- [ ] 10 `mkdir -p /mnt/lvfs1`
- [ ] 11 Test mount manually + `xfs_info /mnt/lvfs1`
- [ ] 12 Capture UUID with `blkid -s UUID -o value`
- [ ] 13 Append fstab line with `xfs` and `0 0`
- [ ] 14 `mount -a` smoke test
- [ ] 15 `systemctl daemon-reload` + verify `.mount` unit
- [ ] 16 Drop `test.txt` to prove writes
- [ ] 17 Compare XFS vs ext4 behaviors
- [ ] 18 Simulate reboot with `umount` + `mount -a`
- [ ] 19 Clean teardown (bottom-up)
- [ ] 20 Capstone — full sample-exam scenario end-to-end

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot `-s 8M` at `vgcreate` | LV ends up half-sized when sized by extents | Tear down, recreate VG with `-s 8M` |
| Used `-L 10` instead of `-l 10` at `lvcreate` | "Insufficient free extents" or wrong size | `-L` = bytes (uppercase), `-l` = extents (lowercase) |
| Used `mkfs.ext4` by reflex on what should be XFS | Wrong FS type | `mkfs.xfs /dev/vg1/lv1` |
| Put `2` in fstab pass column for XFS | Harmless but wrong | XFS always uses `0` |
| Tried to shrink XFS | `xfs_growfs` has no shrink mode | XFS cannot shrink, ever |
| Ran `xfs_growfs DEV` instead of `xfs_growfs MOUNTPOINT` | "Not a mounted XFS filesystem" | Pass the mountpoint, not the device |
| Used `resize2fs` on XFS | "Bad magic number in super-block" | Use `xfs_growfs` instead |
| Forgot `mount -a` after fstab edit | System fails to boot | Always test fstab with `mount -a` first |
| Teardown out of order | `device busy` errors | Bottom-up: fstab → umount → rmdir → lv → vg → pv → loop |
| Forgot `systemctl daemon-reload` after fstab edit | Mount unit shows stale state | Always reload |
| `cd` inside the mount when umounting | `target is busy` | `cd /` first |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- The "PE size + extent count + XFS + persistent mount + test file" combination is one of the highest-weighted storage questions on EX200. Memorize the Task 20 capstone — type it in 5 minutes from blank slate.

**RHCE candidate**
- Same workflow via Ansible:

  ```yaml
  - community.general.lvg:
      vg: vg1
      pvs: /dev/sdb
      pesize: 8
  - community.general.lvol:
      vg: vg1
      lv: lv1
      size: 10g    # or "80m" — both work
  - community.general.filesystem:
      fstype: xfs
      dev: /dev/vg1/lv1
  - ansible.posix.mount:
      path: /mnt/lvfs1
      src: UUID={{ ... }}
      fstype: xfs
      opts: defaults
      state: mounted
  ```

**SRE / Platform interview**
- Be ready to walk through "growing /home (XFS) without downtime": `pvcreate /dev/sdc → vgextend vgname /dev/sdc → lvextend -L +20G /dev/vgname/home → xfs_growfs /home`. One disk, one VG, one LV, one filesystem grow — four commands, zero downtime.

**DevOps**
- Container storage on RHEL uses XFS for `/var/lib/containers` and `/var/lib/docker` by default. The `overlay2` driver requires XFS with `ftype=1` (which is the modern default — `mkfs.xfs` enables it automatically).

**AI / MLOps**
- Distributed training checkpoint volumes are XFS for the parallel-write throughput. The "grow while mounted" property matters when a training run threatens to fill the volume.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| [lvm-create-lvol1-ext4](../lvm-create-lvol1-ext4/) | The ext4 sibling — same PV/VG/LV pattern, different filesystem |
| [scheduling-jobs-systemd-timer](../scheduling-jobs-systemd-timer/) | Sibling RHCSA scheduled-tasks vs. storage exam question |
| Online Extend an LV and Its Filesystem *(coming soon)* | The next-day question — "grow lv1 to 160 MiB without unmounting" |
| Create a Swap Partition by UUID *(coming soon)* | Same workflow but `mkswap` + `swapon` instead of `mkfs.xfs` + `mount` |
| Create an Ext4 Partition Mounted by LABEL *(coming soon)* | The LABEL-based fstab variant of this lab's UUID approach |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
