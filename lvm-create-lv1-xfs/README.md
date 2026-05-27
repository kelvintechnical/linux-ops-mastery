# Lab: Create LV `lv1` (XFS, 8 MiB PE, 10 LEs) and Mount Persistently

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Subjects covered:** PV / VG / LV mental model with **custom PE size**, `pvcreate`, `vgcreate -s 8M`, `lvcreate -l 10`, `mkfs.xfs`, `xfs_info`, `xfs_growfs`, `blkid`, UUID-based `/etc/fstab` entries, `mount -a`, `systemctl daemon-reload`, loopback devices for safe practice
**Career arcs covered:** RHCSA (Storage objective — guaranteed exam question, XFS is the RHEL 7+ default), RHCE (Ansible `community.general.lvol` + `community.general.filesystem` modules), SRE (online growth of root volumes), DevOps (XFS as the default for container-host workloads)
**Prerequisite:** [lvm-create-lvol1-ext4](../lvm-create-lvol1-ext4/) (the ext4 sibling lab) — comfort with `pvcreate / vgcreate / lvcreate` basics
**Time Estimate:** 60 to 90 minutes
**Difficulty arc:** Task 1 foundation · 2–3 the custom-PE VG → extent-count LV → XFS pipeline · 4–5 mount + persistence · 6 RHCSA exam-realistic capstone

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

## The 6 Tasks

> Six exam-realistic phases for the full custom-PE-size XFS LVM workflow: **PV -> VG with 8 MiB PEs -> 10-extent LV -> XFS -> mount -> fstab**.

---

### Task 1 - Set up the sandbox and inspect existing storage

**Purpose:** Confirm the toolchain, capture the before-state, and create a disposable loopback disk for safe practice.

```bash
sudo -i
dnf install -y lvm2 xfsprogs util-linux
mkdir -p /root/lvm-xfs-lab && cd /root/lvm-xfs-lab
which pvcreate vgcreate lvcreate mkfs.xfs xfs_info blkid mount losetup lsblk

lsblk
pvs
vgs
lvs
findmnt -t xfs

truncate -s 1G /root/lvm-xfs-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-xfs-lab/disk1.img)
echo "Using loopback: $LOOP"
lsblk "$LOOP"
```

**Human-Readable Breakdown:** Become root, install/verify LVM and XFS tools, inspect current storage, then attach a 1 GiB sparse file as a loop device. On a real exam, replace the loopback with the provided empty disk.

**Key idea:** Loopback practice gives you the same command path without risking a real disk.

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mkfs.xfs: command not found` | Install `xfsprogs` |
| No free loop device | Check `losetup -a`, then detach stale lab loops with `losetup -d /dev/loopN` |
| Old `vg1`/`lv1` already exists | Run the cleanup block in Task 6 |

---

### Task 2 - Build the PV and custom-PE Volume Group

**Purpose:** Initialize the disk as an LVM Physical Volume and create `vg1` with **8 MiB physical extents**.

```bash
pvcreate "$LOOP"
pvs

vgcreate -s 8M vg1 "$LOOP"
vgs
vgdisplay vg1 | grep -E 'VG Name|PE Size|Total PE|Free  PE'
```

**Human-Readable Breakdown:** `pvcreate` marks the disk for LVM. `vgcreate -s 8M` creates the pool and sets its physical extent size. Verify the PE size now, because it is fixed for the life of the VG.

**Key idea:** The exam trap is forgetting `-s 8M`. If PE size stays at the default 4 MiB, then `lvcreate -l 10` creates the wrong LV size.

**Expected output:**

```text
  Physical volume "/dev/loop0" successfully created.
  Volume group "vg1" successfully created
  VG Name               vg1
  PE Size               8.00 MiB
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `PE Size` shows `4.00 MiB` | Tear down and recreate the VG with `vgcreate -s 8M` |
| `vg1` already exists | Remove stale state or choose a different VG name |
| Device is excluded by filter | Verify disk path; for lab loops only, use `wipefs -a "$LOOP"` |

---

### Task 3 - Create the 10-extent LV and format it with XFS

**Purpose:** Create `lv1` with exactly **10 logical extents**, then format it as XFS.

```bash
lvcreate -l 10 -n lv1 vg1
lvs -o +devices

mkfs.xfs -L lv1 /dev/vg1/lv1
blkid /dev/vg1/lv1
lsblk -f "$LOOP"
```

**Human-Readable Breakdown:** Lowercase `-l 10` means "10 logical extents." Because `vg1` uses 8 MiB PEs, the LV is 80 MiB. Then `mkfs.xfs` creates the filesystem and `blkid`/`lsblk -f` prove the label, UUID, and type.

**Key idea:** `-L` means size; `-l` means extents. This lab exists because exam wording often uses extents.

**Expected output:**

```text
  Logical volume "lv1" created.
  LV  VG  Attr       LSize  Devices
  lv1 vg1 -wi-a----- 80.00m /dev/loop0(0)

/dev/vg1/lv1: LABEL="lv1" UUID="..." TYPE="xfs"
```

**Troubleshoot**

| Symptom | Fix |
|---|---|
| LV is not 80 MiB | Confirm `PE Size 8.00 MiB`; recreate VG if needed |
| Used `-L 10` by mistake | Remove the LV and recreate with lowercase `-l 10` |
| XFS refuses a tiny LV | Keep this lab at 80 MiB or larger |

---

### Task 4 - Mount manually, inspect XFS, and prove writes

**Purpose:** Mount the XFS filesystem at `/mnt/lvfs1`, inspect it with `xfs_info`, capture the UUID, and create the required test file.

```bash
mkdir -p /mnt/lvfs1
mount /dev/vg1/lv1 /mnt/lvfs1

findmnt /mnt/lvfs1
df -hT /mnt/lvfs1
xfs_info /mnt/lvfs1

UUID=$(blkid -s UUID -o value /dev/vg1/lv1)
echo "UUID=$UUID"

echo "xfs lvm lab $(date -Is)" > /mnt/lvfs1/test.txt
cat /mnt/lvfs1/test.txt
```

**Human-Readable Breakdown:** Test the mount manually before editing fstab. `xfs_info` reads the mounted XFS geometry, `blkid` gives the UUID for persistence, and the test file proves the filesystem is writable.

**Key idea:** XFS inspection/growth commands usually use the **mount point**, not the raw device.

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `xfs_info: not a mounted XFS filesystem` | Run it against `/mnt/lvfs1`, after mounting |
| `wrong fs type` during mount | Confirm Task 3 used `mkfs.xfs` |
| `findmnt` returns nothing | The mount failed; rerun `mount` and read stderr |

---

### Task 5 - Make the XFS mount persistent and verify before reboot

**Purpose:** Add a UUID-based XFS fstab entry, reload systemd, test with `mount -a`, and simulate a reboot path.

```bash
cp /etc/fstab /etc/fstab.bak.$(date +%F-%H%M%S)
echo "UUID=$UUID  /mnt/lvfs1  xfs  defaults  0 0" | tee -a /etc/fstab

tail -n 3 /etc/fstab
systemctl daemon-reload
mount -a

findmnt /mnt/lvfs1
df -hT /mnt/lvfs1

umount /mnt/lvfs1
mount -a
findmnt /mnt/lvfs1
cat /mnt/lvfs1/test.txt
```

**Human-Readable Breakdown:** Back up fstab, append the persistent XFS mount, reload systemd's generated mount units, and use `mount -a` as the pre-reboot safety test.

**Expected fstab line:**

```text
UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/lvfs1  xfs  defaults  0 0
```

**Key idea:** XFS fstab entries usually use `0 0` at the end. XFS is not checked with traditional boot-time fsck passes.

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount -a` says UUID not found | Re-capture with `blkid -s UUID -o value /dev/vg1/lv1` |
| `unknown filesystem type` | Use `xfs` in the third fstab column |
| `target is busy` during `umount` | `cd /root/lvm-xfs-lab`, then retry |

---

### Task 6 - Capstone, XFS behavior notes, and cleanup

**Task statement:** *"Create a logical volume called `lv1` in volume group `vg1` using 8 MiB physical extents and exactly 10 logical extents. Format it XFS, mount it persistently to `/mnt/lvfs1`, and write a test file."*

```bash
sudo -i
mkdir -p /root/lvm-xfs-lab && cd /root/lvm-xfs-lab
truncate -s 1G /root/lvm-xfs-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-xfs-lab/disk1.img)
echo "Using loopback: $LOOP"

pvcreate "$LOOP"
vgcreate -s 8M vg1 "$LOOP"
vgdisplay vg1 | grep -E 'VG Name|PE Size'

lvcreate -l 10 -n lv1 vg1
lvs -o +devices

mkfs.xfs -L lv1 /dev/vg1/lv1
mkdir -p /mnt/lvfs1

UUID=$(blkid -s UUID -o value /dev/vg1/lv1)
echo "UUID=$UUID  /mnt/lvfs1  xfs  defaults  0 0" | tee -a /etc/fstab
systemctl daemon-reload
mount -a

echo "RHCSA XFS LVM complete" > /mnt/lvfs1/test.txt
findmnt /mnt/lvfs1
df -hT /mnt/lvfs1
xfs_info /mnt/lvfs1 | head
grep lvfs1 /etc/fstab
cat /mnt/lvfs1/test.txt
```

**Layer stack you built:**

```text
/mnt/lvfs1                        <- mount point users access
└── XFS filesystem                <- mkfs.xfs -L lv1
    └── /dev/vg1/lv1              <- logical volume (10 extents x 8 MiB = 80 MiB)
        └── vg1                   <- volume group with PE Size 8 MiB
            └── /dev/loop0        <- physical volume (practice disk)
                └── disk1.img     <- sparse backing file for lab safety
```

**XFS vs ext4 quick comparison:**

| Topic | XFS | ext4 |
|---|---|---|
| Default on RHEL 9 | Yes | No, but supported |
| Online grow | `xfs_growfs /mountpoint` | `resize2fs /dev/VG/LV` or online grow depending on state |
| Shrink | Not supported | Supported offline with care |
| fstab pass column | Usually `0` | Often `2` for non-root filesystems |
| Info command | `xfs_info /mountpoint` | `tune2fs -l /dev/device` |

**Cleanup**

```bash
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
| `PE Size` is not 8 MiB | Recreate the VG with `vgcreate -s 8M vg1 DEVICE` |
| `lv1` is not 80 MiB | Verify `PE Size 8.00 MiB` and use lowercase `-l 10` |
| `xfs_info` fails | Run it against `/mnt/lvfs1`, not the raw device |
| Cleanup says device is busy | `cd /root/lvm-xfs-lab`, close shells under `/mnt/lvfs1`, then retry |

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

## Lab Checklist (6 Tasks)

- [ ] 01 Set up the sandbox, confirm XFS/LVM tooling, inspect baseline storage, and create the loopback disk
- [ ] 02 Build the PV and create `vg1` with `vgcreate -s 8M`
- [ ] 03 Create `lv1` with `lvcreate -l 10`, format it XFS, and inspect metadata
- [ ] 04 Mount manually at `/mnt/lvfs1`, run `xfs_info`, capture UUID, and write `test.txt`
- [ ] 05 Add the UUID-based XFS `/etc/fstab` line, reload systemd, and verify with `mount -a`
- [ ] 06 Run the RHCSA capstone, review XFS behavior differences, and clean up bottom-up

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
- The "PE size + extent count + XFS + persistent mount + test file" combination is one of the highest-weighted storage questions on EX200. Memorize the Task 6 capstone — type it in 5 minutes from blank slate.

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
