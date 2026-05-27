# Lab: Display Logical Volumes — `lvs`, `lvdisplay`, Segments, Snapshots (`-a`)

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** `lvs` (default table), `lvs VG` / `lvs /dev/VG/LV`, `lvs -o lv_name,lv_uuid,vg_name,lv_size,lv_attr,devices,data_percent,metadata_percent,pool_lv,origin`, `lvs -a` (show **internal** volumes: RAID images, thin pool meta, snapshot cow), `lvs --segments`, `lvs -S`, `lvdisplay` (long), `lvdisplay -m` (LE map from LV to PV extents), `lvdisplay -c` (colon-separated for scripts), `lvscan`, reading **`lv_attr`** (e.g. `-wi-ao----` open, active), thin pool `data_percent` monitoring, comparing `lsblk` tree under VG
- **Career arcs covered:** RHCSA, RHCE, SRE monitoring
- **Prerequisite:** Lab 125
- **Time Estimate:** 20–30 minutes
- **Difficulty arc:** Tasks 1–2 multi-LV VG · Tasks 3–6 `lvs` variants · Task 7 `lvdisplay` · Task 8 `lvdisplay -m` · Task 9 optional snapshot + `lvs -a` · Task 10 capstone + cleanup

---

## Objective

Read LV state quickly (`lvs`) and deeply (`lvdisplay -m` extent map).

**Capstone:** *"One `lvs -o` line listing every LV: name, size, attr, underlying devices."*

> **Lab safety note:** Loop only.

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| Table | `lvs` |
| Columns | `lvs -o lv_name,lv_size,lv_attr,devices` |
| Help fields | `lvs -o help` |
| All (internal) | `lvs -a` |
| Segments | `lvs --segments` |
| Long | `lvdisplay /dev/VG/LV` |
| Map | `lvdisplay -m /dev/VG/LV` |

---

## 🔧 The 10 Tasks

### Task 1 — Setup

```bash
sudo -i
mkdir -p /root/lvm-lvs-lab && cd /root/lvm-lvs-lab
```

### Task 2 — VG + two LVs

```bash
IMG=/var/tmp/lvm-lvs.img
truncate -s 400M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 100%
parted -s "$LOOP" set 1 lvm on
partprobe "$LOOP"; udevadm settle
P="${LOOP}p1"
wipefs -a "$P" 2>/dev/null || true
pvcreate "$P"
vgcreate vgshow "$P"
lvcreate -L 100M -n lv1 vgshow
lvcreate -L 100M -n lv2 vgshow
lvs vgshow | tee 02-lvs.txt
```

### Task 3 — `lvs` default

```bash
lvs | tee 03-all.txt
```

### Task 4 — `lvs -o` custom

```bash
lvs -o lv_name,vg_name,lv_size,lv_attr,lv_uuid,devices vgshow | tee 04-custom.txt
```

### Task 5 — `lvs --segments`

```bash
lvs --segments vgshow | tee 05-seg.txt
```

### Task 6 — `lvs -a` (baseline — no thin)

```bash
lvs -a vgshow | tee 06-hidden.txt
```

### Task 7 — `lvdisplay` each LV

```bash
lvdisplay /dev/vgshow/lv1 | tee 07-lv1.txt
lvdisplay /dev/vgshow/lv2 | tee 07-lv2.txt
```

### Task 8 — `lvdisplay -m` extent map

```bash
lvdisplay -m /dev/vgshow/lv1 | tee 08-map.txt
```

### Task 9 — Snapshot (optional `lvs -a` richness)

```bash
lvcreate -s -n lv1_snap -L 32M /dev/vgshow/lv1 | tee 09-snap.txt
lvs -a vgshow | tee 09-with-snap.txt
```

### Task 10 — Capstone + cleanup

```bash
lvs -o lv_name,lv_size,lv_attr,devices,origin vgshow | tee 10-capstone.txt
cat 10-capstone.txt

lvremove -f /dev/vgshow/lv1_snap
lvremove -f /dev/vgshow/lv1 /dev/vgshow/lv2
vgremove -f vgshow
pvremove -ff "$P"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-lvs-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `lvdisplay` wrong path | not found | Use `/dev/VG/LV` or `/dev/mapper/VG-LV` |
| Expecting `-a` rows on plain linear LV | Only main LVs | Create thin or snap |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01–02 Setup
- [ ] 03 `lvs`
- [ ] 04 `-o`
- [ ] 05 segments
- [ ] 06 `-a`
- [ ] 07 `lvdisplay`
- [ ] 08 `-m`
- [ ] 09 snapshot
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Labs 125, 127–130.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
