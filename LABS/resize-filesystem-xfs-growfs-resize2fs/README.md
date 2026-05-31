# Lab: Resize Filesystem After Extend — `xfs_growfs`, `resize2fs`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** the second half of the "grow a volume" workflow that the block layer cannot complete on its own, why ext4 and XFS need their own resize verb (the FS layer has its own block-bitmap / AG-map accounting independent of the LV size), `xfs_growfs MOUNTPOINT` (XFS — accepts mountpoint, **not** device path, online-only — FS must be mounted), `xfs_growfs -D blocks MP` (grow to a specific block count rather than fill the device), `xfs_growfs -d MP` (grow data section — the common case), `xfs_growfs -L blocks MP` (grow log — rare, dangerous), the fact XFS **only grows** and cannot shrink, `resize2fs DEV` (ext4/3/2 — accepts device path, can run online if FS supports it, can run offline), `resize2fs DEV NEW_SIZE` (resize to a specific size — supports `K`/`M`/`G` suffixes), `resize2fs DEV` with no size (grow to fill device — the common case), `resize2fs -M DEV` (shrink to minimum possible — used in image-bake), the **online resize support flag** (`resize_inode` feature — present by default since e2fsprogs 1.39, but ext2 may lack it), `e2fsck -f DEV` before/after shrink for safety, the manual two-step pattern (`lvextend` then this lab) vs the one-shot (`lvextend -r`), the rare case of resizing a **partition-backed** FS (no LVM): grow the partition with `growpart` or `parted resizepart`, then run the FS resize, the "FS shows wrong size after growpart" pitfall, the device-mapper symlink chain (`/dev/VG/LV` → `/dev/mapper/VG-LV` → `/dev/dm-N`) and how all three accept `resize2fs`, scripting integration (`growpart + resize2fs/xfs_growfs` as a cloud-init pair)
- **Career arcs covered:** RHCSA (EX200 — "grow the filesystem to fill the LV"), RHCE (Ansible `community.general.lvol resizefs=yes` is just a wrapper around this), SRE (mid-incident "df says full but lvs shows free" → run the FS resize), DevOps (cloud-init `growpart` + FS-resize pair on first boot), AI / MLOps (training-data ingest scale-up between epochs)
- **Prerequisite:** Lab 128 (lvextend)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox · Task 2 ext4 LV grow + `resize2fs` · Task 3 grow ext4 to specific size · Task 4 XFS LV grow + `xfs_growfs` · Task 5 demonstrate "you forgot the FS step" failure · Task 6 ext4 online vs offline resize · Task 7 `growpart` + `resize2fs` (no LVM) · Task 8 ext4 minimum-shrink with `resize2fs -M` · Task 9 idempotent fill-to-device script · Task 10 capstone + cleanup

---

## Objective

Master the FS-layer resize verbs that complete every `lvextend` (and every `growpart`). By the end you can grow ext4 and XFS in any direction supported by the FS, know exactly when each verb is online and when it is offline, and never again leave free space "trapped" between the block layer and the filesystem.

The capstone is: *"On a single mounted host: complete an ext4 grow with `resize2fs`, complete an XFS grow with `xfs_growfs`, demonstrate the no-LVM `growpart` + `resize2fs` pair, and shrink an ext4 FS to its minimum with `resize2fs -M`."*

> **Lab safety note:** Loopback. The shrink in Task 8 is performed offline with `e2fsck -f` guarding before and after.

---

## Concept: The FS Has Its Own Size Field

```
   ┌─────────────────────────────────────────────────────────────┐
   │  Block layer (LV)              │  FS layer (superblock)      │
   │   "I'm 2 GiB."                 │   "I'm 200 MiB."            │
   │       │                        │       │                     │
   │       │ lvextend                │       │  (untouched)        │
   │       ▼                        │       ▼                     │
   │   2 GiB available              │   only 200 MiB visible      │
   │                                                              │
   │   resize2fs / xfs_growfs       ───→ FS rewrites superblock   │
   │                                     and accounting           │
   │                                                              │
   │   "I'm 2 GiB."                 │   "I'm 2 GiB."              │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Without the second step, the LV is bigger but no application sees it. `df` reports the old size. Allocation refuses past the FS's known boundary. The fix is always one of the two verbs in this lab.

---

## 📜 Why XFS and ext4 Have Different Verbs — The Story

ext4's resize logic lives in `e2fsprogs` (Theodore Ts'o, the ext maintainer for decades). The `resize2fs` binary uses the ext4 superblock's `resize_inode` reservation — a small area set aside at format time precisely for online growth. RHEL 9 enables it by default.

XFS originated at SGI (1994) for IRIX, ported to Linux around 2001. SGI designed it explicitly for online operations: every administrative knob has an online verb. `xfs_growfs` reads the XFS-specific allocation-group map and adds new AGs at the end. It cannot shrink because the AG layout is monotonic — removing AGs would invalidate every inode reference past the new edge.

The two verbs differ in surface area:

| Trait | `resize2fs` | `xfs_growfs` |
|---|---|---|
| Argument | **device** (or LV path) | **mountpoint** |
| Online? | yes (if `resize_inode` flag present) | yes (mandatory; FS must be mounted) |
| Offline? | yes | no |
| Shrink? | yes | **no** |
| Grow to specific size? | `resize2fs DEV NEW` | `xfs_growfs -D BLOCKS MP` |
| Implicit grow-to-fill? | `resize2fs DEV` | `xfs_growfs MP` |
| Min-shrink? | `resize2fs -M DEV` | not supported |

> **The point of the story:** Pick the right verb based on FS type. Pass it the right argument shape. The rest is muscle memory.

---

## 👪 The Resize Family

```
ext family
├── resize2fs DEV                       ← grow to fill device
├── resize2fs DEV NEWSIZE               ← grow / shrink to NEWSIZE
├── resize2fs -p DEV                    ← print progress
├── resize2fs -M DEV                    ← shrink to minimum
├── e2fsck -f DEV                       ← required before shrink
└── tune2fs -l DEV  | grep -E 'Block count|Reserved' ← verify

XFS family
├── xfs_growfs MOUNTPOINT               ← grow to fill device
├── xfs_growfs -D BLOCKS MOUNTPOINT     ← grow to specific block count
├── xfs_growfs -d MOUNTPOINT            ← grow data section
└── xfs_info MOUNTPOINT                 ← verify

Partition-grow companion (no LVM)
├── growpart /dev/sdX 1                 ← grow GPT partition #1
├── parted /dev/sdX resizepart 1 100%   ← parted equivalent
└── partprobe /dev/sdX                  ← re-read partition table
```

---

## 📚 Resize Reference Table

| FS | Goal | Command |
|---|---|---|
| ext4 | Grow to fill | `resize2fs /dev/VG/LV` |
| ext4 | Grow to 5 GiB | `resize2fs /dev/VG/LV 5G` |
| ext4 | Shrink to 1 GiB | `umount` → `e2fsck -f` → `resize2fs DEV 1G` → `lvreduce` |
| ext4 | Shrink to minimum | `e2fsck -f` → `resize2fs -M DEV` |
| XFS | Grow to fill | `xfs_growfs /mountpoint` |
| XFS | Grow to N blocks | `xfs_growfs -D N /mountpoint` |
| XFS | Shrink | not supported (dump/restore) |
| any | Inspect | `xfs_info MP` or `tune2fs -l DEV` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Grow the filesystem to fill the LV." This is the answer. |
| **RHCE candidate** | Ansible `community.general.filesystem: resizefs=yes` runs this. |
| **SRE / Platform** | Disk-fill incident → `lvextend` + `xfs_growfs` resolution. |
| **DevOps** | cloud-init `growpart` + FS resize pair. |
| **AI / MLOps** | Online grow per training epoch. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox

```bash
sudo -i
mkdir -p /root/resizefs-lab && cd /root/resizefs-lab

for n in 1 2; do
  IMG=/var/tmp/rzfs-$n.img
  truncate -s 1G "$IMG"
  L=$(sudo losetup --find --show "$IMG")
  eval "LOOP_$n=$L"
done

sudo pvcreate "$LOOP_1" "$LOOP_2" >/dev/null
sudo vgcreate vg_rzfs "$LOOP_1" "$LOOP_2" >/dev/null

sudo lvcreate -L 200M -n lv_ext4 vg_rzfs >/dev/null
sudo lvcreate -L 200M -n lv_xfs  vg_rzfs >/dev/null

sudo mkfs.ext4 -L RZFS_EXT4 /dev/vg_rzfs/lv_ext4 >/dev/null
sudo mkfs.xfs  -L RZFS_XFS  /dev/vg_rzfs/lv_xfs  >/dev/null

sudo mkdir -p /mnt/rz_ext4 /mnt/rz_xfs
sudo mount /dev/vg_rzfs/lv_ext4 /mnt/rz_ext4
sudo mount /dev/vg_rzfs/lv_xfs  /mnt/rz_xfs

df -hT /mnt/rz_ext4 /mnt/rz_xfs | tee 01-baseline.txt
```

---

### Task 2 — Grow ext4 with `resize2fs DEV`

```bash
cd /root/resizefs-lab

sudo lvextend -L +200M /dev/vg_rzfs/lv_ext4 | tee 02-lvextend.txt
df -hT /mnt/rz_ext4 | tee 02-df-before.txt

sudo resize2fs /dev/vg_rzfs/lv_ext4 | tee 02-resize2fs.txt
df -hT /mnt/rz_ext4 | tee 02-df-after.txt
```

**Reading it left to right:** With no size argument, `resize2fs` grows the FS to **fill** the underlying device. The kernel reports it can do this online because `resize_inode` is on by default.

**Expected output:**

```text
resize2fs 1.46.5 (30-Dec-2021)
Filesystem at /dev/vg_rzfs/lv_ext4 is mounted on /mnt/rz_ext4; on-line resizing required
old_desc_blocks = 2, new_desc_blocks = 4
The filesystem on /dev/vg_rzfs/lv_ext4 is now 409600 (1k) blocks long.
```

---

### Task 3 — Grow ext4 to a specific size

```bash
cd /root/resizefs-lab

sudo lvextend -L +200M /dev/vg_rzfs/lv_ext4 | tee 03-lvextend.txt

sudo resize2fs /dev/vg_rzfs/lv_ext4 500M | tee 03-resize2fs-500m.txt
df -hT /mnt/rz_ext4 | tee 03-df.txt
```

**Reading it left to right:** `resize2fs DEV SIZE` resizes to the given size (with `K`/`M`/`G` suffix). If `SIZE > current_size`, the call grows. If `SIZE < current_size`, the call shrinks (only legal offline or when supported).

---

### Task 4 — Grow XFS with `xfs_growfs MOUNTPOINT`

```bash
cd /root/resizefs-lab

sudo lvextend -L +200M /dev/vg_rzfs/lv_xfs | tee 04-lvextend.txt
df -hT /mnt/rz_xfs | tee 04-df-before.txt

sudo xfs_growfs /mnt/rz_xfs | tee 04-xfsgrow.txt
df -hT /mnt/rz_xfs | tee 04-df-after.txt
xfs_info /mnt/rz_xfs | tee 04-xfs-info.txt
```

**Reading it left to right:** `xfs_growfs` takes the **mountpoint**, not the device. It is **online-only**. If you accidentally unmount before running it, `xfs_growfs` fails with "not a mount point."

**Expected output (excerpt):**

```text
data blocks changed from 51200 to 102400
```

---

### Task 5 — Demonstrate the "forgot the FS step" failure

```bash
cd /root/resizefs-lab

# Grow LV but DO NOT grow the FS
sudo lvextend -L +100M /dev/vg_rzfs/lv_xfs | tee 05-grew-LV-only.txt
sudo lvs -o lv_name,lv_size /dev/vg_rzfs/lv_xfs | tee 05-lvs.txt

# Observation: df still shows the OLD size
df -hT /mnt/rz_xfs | tee 05-df-stale.txt

# Now do the FS step
sudo xfs_growfs /mnt/rz_xfs | tee 05-xfsgrow.txt
df -hT /mnt/rz_xfs | tee 05-df-current.txt
```

**Reading it left to right:** The most common LVM-grow ticket: "I ran `lvextend` and `df` still shows the old size." The diagnosis: missing FS step.

**The story:** This is why `lvextend -r` (Lab 128) exists. Use it whenever you do not have a reason to verify between steps.

---

### Task 6 — ext4 online vs offline resize

```bash
cd /root/resizefs-lab

sudo lvextend -L +200M /dev/vg_rzfs/lv_ext4 | tee 06-lvextend.txt

# Online resize
sudo resize2fs /dev/vg_rzfs/lv_ext4 | tee 06-online.txt

# Offline resize (must umount)
sudo umount /mnt/rz_ext4
sudo e2fsck -fy /dev/vg_rzfs/lv_ext4 | tee 06-e2fsck.txt
sudo resize2fs /dev/vg_rzfs/lv_ext4 | tee 06-offline.txt
sudo mount /dev/vg_rzfs/lv_ext4 /mnt/rz_ext4
df -hT /mnt/rz_ext4 | tee 06-df.txt
```

**Reading it left to right:** ext4 grows the same way online or offline — the difference is whether the FS is mounted. Online resize requires the `resize_inode` feature (Lab 119 inspector confirms it). Offline resize is universal.

**The story:** Production grows are almost always online. Offline grows are common during image-bake when the FS is not yet active.

---

### Task 7 — No-LVM: `growpart` + `resize2fs`

```bash
cd /root/resizefs-lab

if command -v growpart >/dev/null; then
  IMG_RAW=/var/tmp/rzfs-raw.img
  truncate -s 200M "$IMG_RAW"
  LOOP_RAW=$(sudo losetup --find --show "$IMG_RAW")
  sudo parted -s "$LOOP_RAW" mklabel gpt
  sudo parted -s "$LOOP_RAW" mkpart primary ext4 1MiB 100MiB
  sudo partprobe "$LOOP_RAW"; sudo udevadm settle

  PART="${LOOP_RAW}p1"
  sudo mkfs.ext4 -F "$PART" >/dev/null
  sudo mkdir -p /mnt/rz_raw
  sudo mount "$PART" /mnt/rz_raw
  df -hT /mnt/rz_raw | tee 07-pre-grow.txt

  sudo truncate -s 400M "$IMG_RAW"
  sudo losetup -c "$LOOP_RAW"

  sudo growpart "$LOOP_RAW" 1 | tee 07-growpart.txt
  sudo partprobe "$LOOP_RAW"; sudo udevadm settle

  sudo resize2fs "$PART" | tee 07-resize2fs.txt
  df -hT /mnt/rz_raw | tee 07-post-grow.txt
else
  echo "growpart not installed (provided by cloud-utils-growpart). Skipping demo." | tee 07-skip.txt
fi
```

**Reading it left to right:** Without LVM, the "grow partition" step uses `growpart` (from `cloud-utils-growpart`) or `parted resizepart`. Then `resize2fs` (or `xfs_growfs`) for the FS step.

**The story:** This is exactly what cloud-init runs on AWS/Azure/GCP when the root EBS is expanded and you reboot the instance — no LVM required.

---

### Task 8 — ext4 shrink to minimum (`resize2fs -M`)

```bash
cd /root/resizefs-lab

sudo umount /mnt/rz_ext4

sudo e2fsck -fy /dev/vg_rzfs/lv_ext4 | tee 08-e2fsck.txt
sudo resize2fs -M /dev/vg_rzfs/lv_ext4 | tee 08-shrink-min.txt
sudo tune2fs -l /dev/vg_rzfs/lv_ext4 | grep -E 'Block count|Free blocks|Reserved' | tee 08-after.txt
sudo mount /dev/vg_rzfs/lv_ext4 /mnt/rz_ext4
df -hT /mnt/rz_ext4 | tee 08-df.txt
```

**Reading it left to right:** `-M` (minimum) shrinks the FS to the smallest possible size that still holds its data. Used in **image-bake** pipelines: format big, populate, shrink to min, dd-out the image, distribute.

**The story:** XFS has no equivalent. If you need a small XFS image, you must `mkfs.xfs` at the target size and copy data in.

**Expected output (excerpt):**

```text
The filesystem on /dev/vg_rzfs/lv_ext4 is now 21504 (4k) blocks long.
```

---

### Task 9 — Idempotent fill-to-device script

```bash
cd /root/resizefs-lab

cat > 09-fill-fs.sh <<'EOF'
#!/usr/bin/env bash
# Usage: ./09-fill-fs.sh /dev/vg/lv MOUNTPOINT
DEV="$1"
MP="$2"
FSTYPE=$(sudo findmnt -no FSTYPE "$MP" 2>/dev/null || sudo blkid -o value -s TYPE "$DEV")

case "$FSTYPE" in
  ext4|ext3|ext2)
    sudo resize2fs "$DEV"
    ;;
  xfs)
    sudo xfs_growfs "$MP"
    ;;
  *)
    echo "[$DEV] unsupported FS '$FSTYPE'"
    exit 1
    ;;
esac
EOF
chmod +x 09-fill-fs.sh

./09-fill-fs.sh /dev/vg_rzfs/lv_ext4 /mnt/rz_ext4 | tee 09-ext4.txt
./09-fill-fs.sh /dev/vg_rzfs/lv_xfs  /mnt/rz_xfs  | tee 09-xfs.txt
```

**Reading it left to right:** One wrapper that picks the right verb based on FS type. Useful as a building block for Ansible `command:` modules when you cannot use `community.general.filesystem`.

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/resizefs-lab

cat > 10-report.txt <<EOF
FS resize report — $(hostname) — $(date -Iseconds)

ext4 LV final df:
$(df -hT /mnt/rz_ext4)

XFS LV final df:
$(df -hT /mnt/rz_xfs)

xfs_info excerpt:
$(xfs_info /mnt/rz_xfs | head -n 8)

ext4 tune2fs excerpt:
$(sudo tune2fs -l /dev/vg_rzfs/lv_ext4 | grep -E 'Block count|Free blocks|Block size')

Recommendation:
  - Use lvextend -r for the one-shot path.
  - When you need verification between steps: lvextend → resize2fs (ext4) or xfs_growfs (XFS).
  - Always pass MOUNTPOINT to xfs_growfs; always pass DEVICE to resize2fs.
  - XFS cannot shrink; for image bake, use ext4 + resize2fs -M.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo umount /mnt/rz_ext4 /mnt/rz_xfs
[[ -d /mnt/rz_raw ]] && sudo umount /mnt/rz_raw 2>/dev/null && sudo rmdir /mnt/rz_raw
sudo rmdir /mnt/rz_ext4 /mnt/rz_xfs

sudo lvremove -fy vg_rzfs
sudo vgremove -fy vg_rzfs
sudo pvremove -fy "$LOOP_1" "$LOOP_2"
sudo losetup -d "$LOOP_1" "$LOOP_2"
[[ -n "${LOOP_RAW:-}" ]] && sudo losetup -d "$LOOP_RAW"
sudo rm -f /var/tmp/rzfs-*.img /var/tmp/rzfs-raw.img

cd /root
rm -rf /root/resizefs-lab
exit
```

---

## 🔍 Resize Decision Guide

```
"Grow ext4 to fill LV"      → resize2fs /dev/VG/LV
"Grow XFS to fill LV"       → xfs_growfs /mountpoint
"Grow ext4 to specific size"→ resize2fs /dev/VG/LV 5G
"Grow XFS to N blocks"      → xfs_growfs -D N /mountpoint
"Shrink ext4 to N"          → umount → e2fsck -f → resize2fs DEV N → mount
"Shrink ext4 to min"        → umount → e2fsck -f → resize2fs -M DEV → mount
"Shrink XFS"                → not supported; dump+mkfs.xfs+restore
"Cloud no-LVM grow"         → growpart DEV N → resize2fs/xfs_growfs
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Sandbox: ext4 + XFS LVs mounted
- [ ] 02 ext4 `resize2fs DEV` fill
- [ ] 03 ext4 `resize2fs DEV SIZE`
- [ ] 04 XFS `xfs_growfs MP`
- [ ] 05 "Forgot FS step" failure mode
- [ ] 06 ext4 online vs offline
- [ ] 07 `growpart` + `resize2fs` (no LVM)
- [ ] 08 ext4 `-M` minimum-shrink
- [ ] 09 Idempotent fill-fs script
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `xfs_growfs /dev/VG/LV` | "not a mount point" | Pass the mountpoint, not the device |
| `resize2fs /mnt/X` | "device path expected" | Pass the device, not the mountpoint |
| Forgot FS step | `df` shows old size | Run `resize2fs` or `xfs_growfs` |
| Shrink XFS | Tool refuses | Not supported — recreate or migrate |
| Online shrink ext4 | "online shrink not supported" | Unmount + e2fsck -f first |
| `growpart` without `partprobe` | Kernel still sees old size | `partprobe DEV; udevadm settle` |
| `resize2fs -M` on mounted FS | "must be unmounted" | umount first |
| `xfs_growfs` with `-L` log-section flag | Risky log resize | Almost never the right flag |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Two-step muscle memory: `lvextend -L +SIZE LV` → `xfs_growfs MP` (XFS) or `resize2fs LV` (ext4). Or `-r` for the one-shot.

**RHCE candidate**
- Ansible: `community.general.filesystem: fstype=xfs dev=/dev/VG/LV resizefs=yes`.

**SRE / Platform interview**
- Mid-incident: "df is full, lvs shows free." → run the FS resize.

**DevOps**
- cloud-init: `growpart` + matching FS resize.

**AI / MLOps**
- Cron-driven grow: monitor `df`, `lvextend -r` if > 85%.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 116 — Format XFS | Counterpart format step |
| Lab 117 — Format ext4 | Counterpart format step |
| Lab 118 — fsck | Used in shrink |
| Lab 119 — `dumpe2fs` | Verify `resize_inode` feature |
| Lab 128 — `lvextend` | Step 1 of the grow workflow |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
