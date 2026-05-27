# Lab: Display Volume Groups — `vgs`, `vgdisplay`, `vgscan`, Columns, Tags

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** `vgs` (default columns), `vgs VG` (filter), `vgs -o vg_name,vg_uuid,vg_size,vg_free,vg_extent_size,pv_count,lv_count,vg_attr`, `vgs -v` / `vgs --verbose`, `vgs -S` selection, `vgs --units`, `vgdisplay` (full paragraph per VG), `vgdisplay -v` (include all PV and LV summaries — very long), `vgdisplay -s` (short), `vgscan` (scan VGs), reading **`vg_attr`** bits (`wz--n-` style: writable, resizeable, ...), partial vs complete VG (`pvs` shows `partial` set), `vgck`, comparing `vgs` output to capacity planning spreadsheets
- **Career arcs covered:** RHCSA ("how much free space in VG?"), RHCE, SRE capacity
- **Prerequisite:** Lab 123
- **Time Estimate:** 20–30 minutes
- **Difficulty arc:** Tasks 1–2 VG with LV consumes space · Tasks 3–7 `vgs`/`vgdisplay` variants · Task 8 `vg_attr` decode · Task 9 `vgscan` · Task 10 capstone + cleanup

---

## Objective

Answer *"how much space is left in the VG?"* in one second with `vgs -o vg_free` and know when to use `vgdisplay -v` for deep multi-PV/LV dumps.

**Capstone:** *"Single command: print VG name, total size, free size, #PV, #LV, UUID."*

> **Lab safety note:** Loop only.

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| All VGs | `vgs` |
| One VG | `vgs myvg` |
| Custom cols | `vgs -o vg_name,vg_size,vg_free,pv_count,lv_count` |
| All keys | `vgs -o help` |
| Long | `vgdisplay myvg` |
| Very long | `vgdisplay -v myvg` |
| Short | `vgdisplay -s` |

---

## 🔧 The 10 Tasks

### Task 1 — Setup

```bash
sudo -i
mkdir -p /root/lvm-vgs-lab && cd /root/lvm-vgs-lab
```

### Task 2 — VG + two LVs (fragment free space)

```bash
IMG=/var/tmp/lvm-vgs.img
truncate -s 512M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 100%
parted -s "$LOOP" set 1 lvm on
partprobe "$LOOP"; udevadm settle
P="${LOOP}p1"
wipefs -a "$P" 2>/dev/null || true
pvcreate "$P"
vgcreate vgreport "$P"
lvcreate -L 128M -n lv_a vgreport
lvcreate -L 128M -n lv_b vgreport
lsblk "$LOOP" | tee 02-lsblk.txt
```

### Task 3 — `vgs`

```bash
vgs | tee 03-vgs.txt
```

### Task 4 — `vgs -o` capacity report

```bash
vgs -o vg_name,vg_size,vg_free,vg_uuid,pv_count,lv_count,vg_extent_size vgreport | tee 04-capacity.txt
```

### Task 5 — `vgs -v` (one VG)

```bash
vgs -v vgreport 2>&1 | head -n 40 | tee 05-verbose.txt
```

### Task 6 — `vgdisplay` default

```bash
vgdisplay vgreport | tee 06-vgdisplay.txt
```

### Task 7 — `vgdisplay -s` all VGs

```bash
vgdisplay -s | tee 07-short-all.txt
```

### Task 8 — Decode `vg_attr`

```bash
vgs -o vg_name,vg_attr vgreport | tee 08-attr.txt
man lvm-fullreport 2>/dev/null | head -n 1 || vgs -o help | grep vg_attr
```

**Story:** `vg_attr` is a compact state string — for full decode see `lvmreport(7)` / `pvs -o help` field descriptions.

### Task 9 — `vgscan`

```bash
vgscan 2>&1 | tee 09-vgscan.txt
```

### Task 10 — Capstone + cleanup

```bash
vgs -o vg_name,vg_size,vg_free,pv_count,lv_count,vg_uuid vgreport | tee 10-capstone.txt
cat 10-capstone.txt

lvremove -f /dev/vgreport/lv_a /dev/vgreport/lv_b
vgremove -f vgreport
pvremove -ff "$P"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-vgs-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `vgdisplay` without VG name | Floods all VGs | Specify VG or use `-s` |
| `-v` in automation | Huge output | Use `vgs -o` |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01–02 VG + 2 LVs
- [ ] 03 `vgs`
- [ ] 04 Custom `-o`
- [ ] 05 `vgs -v`
- [ ] 06 `vgdisplay`
- [ ] 07 `vgdisplay -s`
- [ ] 08 `vg_attr`
- [ ] 09 `vgscan`
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Labs 123, 125–126.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
