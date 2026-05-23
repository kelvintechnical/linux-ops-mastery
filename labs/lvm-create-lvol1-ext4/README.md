# Lab: Create LV `lvol1` (ext4, 280 MB) and Mount Persistently

**Series:** linux-ops-mastery — RHCSA LVM & Storage Management
**Subjects covered:** PV / VG / LV mental model, `pvcreate`, `vgcreate`, `lvcreate`, `mkfs.ext4`, `blkid`, UUID-based `/etc/fstab` entries, `mount -a`, `systemctl daemon-reload`, loopback devices for safe practice
**Career arcs covered:** RHCSA (Storage objective — guaranteed exam question), RHCE (Ansible `community.general.lvol` module), SRE (resizing root volumes without downtime), DevOps (thin-provisioned LVs for container storage drivers)
**Prerequisite:** Comfort with `lsblk`, `df -h`, `mount`, `/etc/fstab` basics
**Time Estimate:** 60 to 90 minutes
**Difficulty arc:** Task 1 foundation · 2–3 the PV→VG→LV→filesystem pipeline · 4–5 mount + persistence · 6 RHCSA exam-realistic capstone

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

## 🔧 The 6 Tasks

> This lab is grouped into six exam-realistic phases so the full **PV -> VG -> LV -> ext4 -> mount -> fstab** workflow is easier to read, rehearse, and memorize.

---

### Task 1 — Set up the sandbox and inspect existing storage

**Purpose:** Become root, confirm the LVM/ext4 tools exist, create a safe 1 GiB loopback disk, and record the baseline storage state before changing anything.

```bash
sudo -i
dnf install -y lvm2 e2fsprogs util-linux
mkdir -p /root/lvm-lab && cd /root/lvm-lab
which pvcreate vgcreate lvcreate mkfs.ext4 blkid mount losetup lsblk

lsblk
pvs
vgs
lvs

truncate -s 1G /root/lvm-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-lab/disk1.img)
echo "Using loopback: $LOOP"
lsblk "$LOOP"
```

**Human-Readable Breakdown:** Become root, make sure the tools are installed, create a clean working directory, inspect the current disk/LVM state, then create a disposable file-backed disk and attach it as `/dev/loopN`. The loopback device behaves like a real disk for LVM practice, but it is safe to delete at the end.

**Reading it left to right:** `sudo -i` opens a root shell. `dnf install` makes sure `lvm2`, `e2fsprogs`, and `util-linux` are present. `lsblk`, `pvs`, `vgs`, and `lvs` capture the before-state. `truncate` creates the backing file. `losetup -fP --show` attaches that file to the first free loop device and prints the path, which we store in `$LOOP`.

**The story:** Real exam systems usually give you a real empty disk like `/dev/vdb`; a home lab often does not. Loopback devices let you practice the exact same LVM commands without touching real storage. The baseline commands are how you prove what changed and avoid overwriting the wrong device.

**Expected output:**

```text
/usr/sbin/pvcreate
/usr/sbin/vgcreate
/usr/sbin/lvcreate
/usr/sbin/mkfs.ext4
/usr/sbin/blkid
/usr/bin/mount
/usr/sbin/losetup
/usr/bin/lsblk

Using loopback: /dev/loop0
NAME  MAJ:MIN RM SIZE RO TYPE MOUNTPOINTS
loop0   7:0    0   1G  0 loop
```

**Switches**

| Token | Meaning |
|---|---|
| `truncate -s 1G` | Create a sparse 1 GiB file |
| `losetup -fP --show FILE` | Attach FILE to the first free loop device and print the path |
| `pvs` / `vgs` / `lvs` | Short LVM inventory commands |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `pvcreate: command not found` | Install `lvm2` and confirm repos work with `dnf repolist` |
| `losetup: cannot find an unused loop device` | Detach stale devices with `losetup -a` then `losetup -d /dev/loopN` |
| Old lab objects appear in `pvs` / `vgs` / `lvs` | Run the cleanup block from Task 6 before starting again |

---

### Task 2 — Build the PV -> VG -> LV stack

**Purpose:** Convert the loopback disk into an LVM Physical Volume, pool it into a Volume Group named `vgtest`, and carve out a 280 MiB Logical Volume named `lvol1`.

```bash
pvcreate "$LOOP"
pvs

vgcreate vgtest "$LOOP"
vgs

lvcreate -L 280M -n lvol1 vgtest
lvs -o +devices
lsblk "$LOOP"
```

**Human-Readable Breakdown:** Mark the loopback disk as an LVM Physical Volume, create a storage pool named `vgtest`, allocate a 280 MiB LV named `lvol1`, then inspect the result.

**Reading it left to right:** `pvcreate "$LOOP"` writes LVM metadata to the block device. `vgcreate vgtest "$LOOP"` creates the storage pool. `lvcreate -L 280M -n lvol1 vgtest` allocates a 280 MiB LV from that pool. `lvs -o +devices` shows the LV and the backing device/extents.

**The story:** LVM's power is the separation of concerns. The PV is the raw material, the VG is the storage pool, and the LV is the usable block device. RHCSA storage tasks test whether you can keep those names and command positions straight under pressure.

**Expected output:**

```text
  Physical volume "/dev/loop0" successfully created.
  Volume group "vgtest" successfully created
  Logical volume "lvol1" created.

  LV    VG     Attr       LSize   Devices
  lvol1 vgtest -wi-a----- 280.00m /dev/loop0(0)
```

**Switches**

| Token | Meaning |
|---|---|
| `pvcreate DEVICE` | Marks a disk/partition as an LVM Physical Volume |
| `vgcreate VG DEVICE` | Creates a Volume Group pool |
| `lvcreate -L 280M` | Create an LV with an absolute size of 280 MiB |
| `lvcreate -n lvol1` | Name the new LV `lvol1` |
| `lvs -o +devices` | Add backing-device details to the normal LV table |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device ... excluded by a filter` | Use the correct disk, or wipe stale metadata with `wipefs -a "$LOOP"` if this is your lab device |
| `Volume group "vgtest" already exists` | You have stale state; run Task 6 cleanup or choose a different VG name |
| `Insufficient free space` | The backing disk is too small or already has extents allocated |

---

### Task 3 — Format the LV with ext4 and inspect the filesystem

**Purpose:** Put an ext4 filesystem on `/dev/vgtest/lvol1`, give it a label, and verify the filesystem metadata before mounting it.

```bash
mkfs.ext4 -L lvol1 /dev/vgtest/lvol1

blkid /dev/vgtest/lvol1
lsblk -f "$LOOP"
tune2fs -l /dev/vgtest/lvol1 | grep -E 'Filesystem volume name|Filesystem UUID|Block size|Block count'
```

**Human-Readable Breakdown:** The LV is only a block device until you format it. `mkfs.ext4` creates the ext4 structures, `-L lvol1` gives the filesystem a label, and `blkid`/`lsblk -f`/`tune2fs` prove the result before the mount step.

**Reading it left to right:** `mkfs.ext4` creates the filesystem. `-L lvol1` applies the label. `/dev/vgtest/lvol1` is the stable friendly LV path. `blkid` shows UUID/type/label. `lsblk -f` shows the tree. `tune2fs -l` shows ext4-specific metadata.

**The story:** LVM creates storage; `mkfs` makes that storage usable by files. If you skip this step, `mount` fails with a vague "wrong fs type" error. The UUID from `blkid` is also the value you will use for `/etc/fstab`.

**Expected output:**

```text
Creating filesystem with 286720 1k blocks and 71680 inodes
Filesystem UUID: 1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7

/dev/vgtest/lvol1: LABEL="lvol1" UUID="1f8a..." BLOCK_SIZE="1024" TYPE="ext4"
```

**Switches**

| Token | Meaning |
|---|---|
| `mkfs.ext4` | Create an ext4 filesystem |
| `-L NAME` | Apply a filesystem label |
| `blkid DEVICE` | Print UUID, label, and filesystem type |
| `lsblk -f` | Show block-device tree plus filesystem metadata |
| `tune2fs -l` | Display ext-family filesystem internals |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mkfs.ext4: command not found` | Install `e2fsprogs` |
| `is mounted; will not make a filesystem here!` | Unmount the device first; never format a mounted filesystem |
| `blkid` prints nothing | `mkfs.ext4` did not complete; rerun it and read the error |

---

### Task 4 — Mount manually, capture the UUID, and prove usability

**Purpose:** Create `/mnt/mnt1`, mount the filesystem manually for a one-time test, capture the UUID for persistence, and prove the mounted filesystem can store data.

```bash
mkdir -p /mnt/mnt1
mount /dev/vgtest/lvol1 /mnt/mnt1

findmnt /mnt/mnt1
df -hT /mnt/mnt1

UUID=$(blkid -s UUID -o value /dev/vgtest/lvol1)
echo "UUID=$UUID"

echo "lvm ext4 lab $(date -Is)" > /mnt/mnt1/proof.txt
cat /mnt/mnt1/proof.txt

lvs -o +devices
vgs
pvs
```

**Human-Readable Breakdown:** Make the mount point, mount the LV manually, verify the mount, store the filesystem UUID in a variable, write a proof file, and inspect the LVM runtime state.

**Reading it left to right:** `mkdir -p` creates the mount point. `mount DEVICE DIR` attaches the filesystem. `findmnt` asks the kernel what backs that path. `df -hT` shows size and filesystem type. `blkid -s UUID -o value` prints only the bare UUID. The proof file proves real writes land on the mounted filesystem.

**The story:** Always test a mount manually before making it persistent. If manual mounting fails, fstab will fail too. UUID capture is the bridge between runtime success and boot-time persistence.

**Expected output:**

```text
TARGET    SOURCE                  FSTYPE OPTIONS
/mnt/mnt1 /dev/mapper/vgtest-lvol1 ext4   rw,relatime

Filesystem               Type Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 ext4 252M   24K  234M   1% /mnt/mnt1

UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7
lvm ext4 lab 2026-05-23T19:10:00-04:00
```

**Switches**

| Token | Meaning |
|---|---|
| `mkdir -p` | Create the mount point and do nothing if it already exists |
| `mount DEVICE DIR` | Attach a filesystem to the directory tree |
| `findmnt PATH` | Show the source device and options for a mount point |
| `df -hT` | Human-readable filesystem capacity plus filesystem type |
| `blkid -s UUID -o value` | Print only the UUID value |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount point does not exist` | Run `mkdir -p /mnt/mnt1` |
| `wrong fs type, bad option, bad superblock` | The LV is not formatted; rerun Task 3 |
| `findmnt` returns nothing | The mount command failed; inspect `dmesg` or rerun mount and read stderr |

---

### Task 5 — Make the mount persistent and verify before reboot

**Purpose:** Add a UUID-based `/etc/fstab` entry, reload systemd's generated mount units, test with `mount -a`, and simulate a reboot by unmounting and remounting from fstab.

```bash
cp /etc/fstab /etc/fstab.bak.$(date +%F-%H%M%S)
echo "UUID=$UUID  /mnt/mnt1  ext4  defaults  0 0" | tee -a /etc/fstab

tail -n 3 /etc/fstab
systemctl daemon-reload
mount -a

findmnt /mnt/mnt1
df -hT /mnt/mnt1

umount /mnt/mnt1
mount -a
findmnt /mnt/mnt1
cat /mnt/mnt1/proof.txt
```

**Human-Readable Breakdown:** Back up fstab, append a UUID-based line, reload systemd so it notices the fstab-generated mount unit, run `mount -a` to test before rebooting, then unmount and remount through `mount -a` to simulate the boot path.

**Reading it left to right:** `cp /etc/fstab` creates a rollback point. `tee -a /etc/fstab` appends the persistent line. `systemctl daemon-reload` refreshes systemd's generated `.mount` units. `mount -a` tests the file. `umount` plus another `mount -a` proves fstab alone can bring it back.

**The story:** A bad fstab line can boot a machine into emergency mode. That is why `mount -a` is mandatory after every fstab edit. If it fails now, you can fix it now.

**Expected fstab line:**

```text
UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
```

**Switches**

| Field | Meaning |
|---|---|
| `UUID=...` | Stable filesystem identifier |
| `/mnt/mnt1` | Mount point |
| `ext4` | Filesystem type |
| `defaults` | Standard mount options |
| `0 0` | No dump; no automatic fsck in this lab |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `mount -a` says UUID not found | Re-run `blkid -s UUID -o value /dev/vgtest/lvol1` and fix fstab |
| `unknown filesystem type` | fstab type typo; use `ext4` |
| `systemd` warns fstab changed | Run `systemctl daemon-reload` |
| `target is busy` during `umount` | Leave the directory first: `cd /root/lvm-lab`, then retry |

---

### Task 6 — Capstone, document the stack, and clean up

**Task statement:** *"Create a logical volume called `lvol1` of size 280 MB in the `vgtest` volume group. Mount the ext4 file system persistently to `/mnt/mnt1`."*

**Purpose:** Run the full RHCSA answer from a blank slate, verify the layer stack, and tear it down cleanly when you are done practicing.

```bash
sudo -i
mkdir -p /root/lvm-lab && cd /root/lvm-lab
truncate -s 1G /root/lvm-lab/disk1.img
LOOP=$(losetup -fP --show /root/lvm-lab/disk1.img)
echo "Using loopback: $LOOP"

pvcreate "$LOOP"
vgcreate vgtest "$LOOP"
lvcreate -L 280M -n lvol1 vgtest

mkfs.ext4 -L lvol1 /dev/vgtest/lvol1
mkdir -p /mnt/mnt1

UUID=$(blkid -s UUID -o value /dev/vgtest/lvol1)
echo "UUID=$UUID  /mnt/mnt1  ext4  defaults  0 0" | tee -a /etc/fstab
systemctl daemon-reload
mount -a

lvs -o +devices
findmnt /mnt/mnt1
df -hT /mnt/mnt1
grep mnt1 /etc/fstab
```

**Human-Readable Breakdown:** Create the safe disk, build the LVM stack, format ext4, create the mount point, write the UUID-based fstab line, reload systemd, mount everything from fstab, and verify with `lvs`, `findmnt`, `df`, and `grep`.

**Layer stack you built:**

```text
/mnt/mnt1                         <- mount point users access
└── ext4 filesystem               <- mkfs.ext4 -L lvol1
    └── /dev/vgtest/lvol1         <- logical volume (280 MiB)
        └── vgtest                <- volume group / storage pool
            └── /dev/loop0        <- physical volume (practice disk)
                └── disk1.img     <- sparse backing file for lab safety
```

**The story:** This is the **5-minute exam answer**. Memorize the spine: `pvcreate -> vgcreate -> lvcreate -> mkfs.ext4 -> mkdir -> blkid -> fstab -> daemon-reload -> mount -a -> verify`. The names and sizes change, but the order does not.

**Expected verification output:**

```text
  LV    VG     Attr       LSize   Devices
  lvol1 vgtest -wi-ao---- 280.00m /dev/loop0(0)

TARGET    SOURCE                  FSTYPE OPTIONS
/mnt/mnt1 /dev/mapper/vgtest-lvol1 ext4   rw,relatime

Filesystem               Type Size  Used Avail Use% Mounted on
/dev/mapper/vgtest-lvol1 ext4 252M   24K  234M   1% /mnt/mnt1

UUID=1f8a3b5c-9e1d-4a8b-bb44-2dcef091e0b7  /mnt/mnt1  ext4  defaults  0 0
```

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
| `Volume group "vgtest" has insufficient free space` | The practice disk is too small or already allocated; use a fresh 1 GiB loopback |
| Capstone fails at `mount -a` | UUID typo; re-capture with `blkid -s UUID -o value /dev/vgtest/lvol1` |
| Cleanup says device is busy | `cd /root/lvm-lab`, close shells under `/mnt/mnt1`, then retry `umount` |

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

## ✅ Lab Checklist (6 Tasks)

- [ ] 01 Set up the sandbox, confirm tooling, inspect baseline storage, and create the loopback disk
- [ ] 02 Build the LVM stack: `pvcreate` -> `vgcreate vgtest` -> `lvcreate -L 280M -n lvol1`
- [ ] 03 Format `/dev/vgtest/lvol1` with ext4 and inspect UUID/label/filesystem metadata
- [ ] 04 Mount manually at `/mnt/mnt1`, capture the UUID, and write a proof file
- [ ] 05 Add the UUID-based `/etc/fstab` line, run `systemctl daemon-reload`, and verify with `mount -a`
- [ ] 06 Run the RHCSA capstone, document the layer stack, and clean up bottom-up

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
- "Create a 280 MB LV called lvol1 in vgtest and mount it persistently" is a near-guaranteed exam question. Memorize the Task 6 capstone block — type it in 5 minutes from blank slate.

**RHCE candidate**
- Same workflow via Ansible: `community.general.lvg`, `community.general.lvol`, `community.general.filesystem`, and `ansible.posix.mount`. Practice writing a playbook that recreates Task 6.

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
