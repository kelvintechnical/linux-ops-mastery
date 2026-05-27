# Lab: Initialize Physical Volumes with `pvcreate` — LVM Stack, `wipefs`, `pvs`, `pvremove`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** LVM three-layer model (PV → VG → LV), **Physical Volume (PV)** = disk or partition with LVM metadata header, `pvcreate [-v] [-y] [--dataalignment OFFSET] DEV [...]`, wiping prior signatures (`wipefs -a`, `dd`), partition types `8e` (MBR LVM) / `8E00` (GPT LVM) / `parted set N lvm on`, `pvscan` (discover PVs), `pvs` / `pvdisplay` (verify — Lab 122 deep dive), `pvremove [-ff] DEV` (strip metadata), `lvm dumpconfig` (global settings), `pvck` (header check), duplicate PV UUID hazards, whole-disk vs partition PV trade-offs
- **Career arcs covered:** RHCSA (EX200 — `pvcreate /dev/vdb1`), RHCE (`lvg` / `community.general.lvg` prerequisites), SRE (EBS attach → PV), DevOps (Terraform null_resource + pvcreate), AI / MLOps (data volume pools)
- **Prerequisite:** Labs 111–115 (partitioning), Lab 110 (`lsblk`)
- **Time Estimate:** 25–40 minutes
- **Difficulty arc:** Tasks 1–2 theory + loop partition · Task 3 wipe signatures · Task 4 `pvcreate` · Task 5 `pvs`/`pvscan` · Task 6 `pvdisplay` one-liner · Task 7 second PV · Task 8 `pvcreate -v` · Task 9 `pvremove` + re-init · Task 10 capstone + cleanup

---

## Objective

Take a raw partition and make it an LVM **Physical Volume** — the bottom brick of every VG/LV stack. You will wipe competing signatures safely, run `pvcreate`, verify with `pvs`, and tear down with `pvremove`.

**Capstone:** *"On `/dev/loopXp1` and `/dev/loopXp2`, run `pvcreate` on both, show `pvs` listing VG name as empty, then `pvremove` both and prove headers are gone with `pvs`."*

> **Lab safety note:** Loop devices only. On real disks, `pvcreate` overwrites the partition start — backup first.

---

## Concept: PV = LVM Label on a Block Device

```
   Disk/Partition
        │
        ▼
   pvcreate  ──►  writes LVM label (metadata area at start of device)
        │
        ├── PV UUID
        ├── VG name (empty until vgcreate)
        └── PE (physical extent) size inherited when VG created

   pvremove  ──►  removes label (device returns to "unknown" to LVM)
```

> **Why this matters:** Every `vgcreate` fails until **PVs exist**. `pvcreate` is the first command in the RHCSA LVM chain.

---

## 📜 Why LVM PVs — The Story

**Heinz Mauelshagen (1998)** merged the original Linux LVM into the 2.4 kernel era so storage could be **pooled and sliced** without repartitioning running applications. The PV header is a small on-disk structure; the heavy lifting (extent maps, snapshots) lives in VG metadata.

---

## 👪 The `pvcreate` Family

| Command | Role |
|---|---|
| `pvcreate` | Write LVM label to device |
| `pvscan` | Rescan all block devices for PVs |
| `pvs` | Short listing (scripting) |
| `pvdisplay` | Long listing (human triage) |
| `pvremove` | Remove label (PV must not belong to active VG) |
| `pvck` | Check metadata headers |
| `pvchange` | Attributes, UUID refresh |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA** | First step of almost every storage task. |
| **RHCE** | `lvg` module requires PVs already created or uses `pvs` facts. |
| **SRE** | New EBS volume → `pvcreate` before pool extend. |

---

## 📚 Reference Table

| Goal | Command | Notes |
|---|---|---|
| Create PV | `pvcreate /dev/sdX1` | |
| Verbose | `pvcreate -v DEV` | |
| Assume yes | `pvcreate -y DEV` | Overwrite prompts |
| Scan | `pvscan` | |
| List | `pvs` | Short |
| Detail | `pvdisplay DEV` | Long |
| Remove | `pvremove DEV` | |
| Force remove | `pvremove -ff DEV` | Broken VG only |

---

## 🔍 PV Decision Guide

```
"Is this disk LVM-ready?"     → wipefs -a DEV; blkid DEV
"Label as PV"               → pvcreate DEV
"List PVs"                  → pvs  OR  pvscan
"Details one PV"            → pvdisplay DEV
"Undo PV only"              → pvremove DEV
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Working dir + sudo
- [ ] 02 Two GPT partitions + `lvm` flag
- [ ] 03 `wipefs` / clean blkid
- [ ] 04 `pvcreate` first PV
- [ ] 05 `pvscan` + `pvs -o`
- [ ] 06 `pvdisplay`
- [ ] 07 Second `pvcreate`
- [ ] 08 `pvcreate -v` after `pvremove`
- [ ] 09 Remove both + recreate
- [ ] 10 Capstone + detach loop

---

## 🎯 Career & Interview Strategy

- **Exam one-liner:** `pvcreate /dev/vdb1 && pvs`
- **Interview:** Whole-disk PV vs partition PV — whole disk is supported but destroys partition table; exams usually use partitions.

---

## 🔧 The 10 Tasks

### Task 1 — Working directory and variables

```bash
sudo -i
mkdir -p /root/lvm-pv-lab && cd /root/lvm-pv-lab
```

### Task 2 — Loop image with two partitions (LVM types)

```bash
cd /root/lvm-pv-lab
IMG=/var/tmp/lvm-pv.img
truncate -s 512M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 256MiB
parted -s "$LOOP" set 1 lvm on
parted -s "$LOOP" mkpart primary 256MiB 100%
parted -s "$LOOP" set 2 lvm on
partprobe "$LOOP"; udevadm settle
P1="${LOOP}p1"; P2="${LOOP}p2"
echo "P1=$P1 P2=$P2" | tee 02-devices.txt
lsblk "$LOOP" | tee 02-lsblk.txt
```

### Task 3 — Wipe old filesystem/swap signatures

```bash
cd /root/lvm-pv-lab
wipefs -a "$P1" 2>/dev/null || true
wipefs -a "$P2" 2>/dev/null || true
blkid "$P1" "$P2" 2>&1 | tee 03-blkid.txt
```

### Task 4 — `pvcreate` on first partition

```bash
cd /root/lvm-pv-lab
pvcreate "$P1" | tee 04-pvcreate.txt
pvs "$P1" | tee 04-pvs.txt
```

**Expected `pvs`:** `PSize` set, `VG` column empty or `-`.

### Task 5 — `pvscan` and `pvs -o +pv_pe_count`

```bash
cd /root/lvm-pv-lab
pvscan | tee 05-pvscan.txt
pvs -o pv_name,pv_uuid,vg_name,pv_size,pv_free "$P1" | tee 05-pvs-o.txt
```

### Task 6 — `pvdisplay` (summary)

```bash
cd /root/lvm-pv-lab
pvdisplay "$P1" | tee 06-pvdisplay.txt
```

**Read:** `PV Name`, `PV UUID`, `PE Size` (0 until in VG — actually on RHEL, PE size may show after vgcreate; pvdisplay still shows PV UUID).

### Task 7 — `pvcreate` second PV

```bash
cd /root/lvm-pv-lab
pvcreate "$P2" | tee 07-pvcreate2.txt
pvs | tee 07-pvs-all.txt
```

### Task 8 — Verbose create (destroy and recreate P2)

```bash
cd /root/lvm-pv-lab
pvremove "$P2"
pvcreate -v "$P2" 2>&1 | tee 08-verbose.txt
```

### Task 9 — `pvremove` cycle

```bash
cd /root/lvm-pv-lab
pvremove "$P1" "$P2" | tee 09-removed.txt
pvs 2>&1 | tee 09-pvs-empty.txt
pvcreate "$P1" "$P2" | tee 09-recreated.txt
```

### Task 10 — Capstone report + cleanup

```bash
cd /root/lvm-pv-lab
pvs -o pv_name,pv_uuid,vg_name "$P1" "$P2" | tee 10-capstone.txt
cat 10-capstone.txt

pvremove -ff "$P1" "$P2"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-pv-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `pvcreate` on mounted FS | Refused / dangerous | Unmount |
| Existing partition table + whole disk PV | Destroys table | Use partitions |
| `pvremove` while in VG | Error | `vgreduce` + `pvremove` order (Lab 130) |
| Duplicate PV on SAN clone | VG won't activate | `pvchange -u` or recreate UUID |

---

## 🔗 Related Labs

Labs 122–130 (VG/LV/extend/remove).

---

## 👤 Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical)
