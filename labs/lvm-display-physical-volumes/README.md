# Lab: Display Physical Volumes — `pvs`, `pvdisplay`, `pvscan`, Custom Columns, Segments

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** `pvs` (scriptable table), `pvs -o COL1,COL2` (custom columns: `pv_name`, `pv_uuid`, `pv_size`, `pv_free`, `pv_fmt`, `dev_size`, `pv_pe_count`, `pv_tags`, `vg_name`), `pvs -a` (include hidden / internal), `pvs --segments` (PV segment map), `pvs -S 'vg_name=~vg'` (selection), `pvdisplay` (default long), `pvdisplay -m` (PE-to-LV mapping — requires PV in VG), `pvdisplay -C` (columns like pvs), `pvdisplay --columns` (batch), `pvscan` (scan + activate), `pvscan --cache` (udev cache refresh), `lvm pvs` vs `pvs` (same), units `pvs --units g`, sorting `pvs --sort -pv_size`, reading **Allocatable** yes/no, **PE Size** after VG attach, comparing output to `lsblk` + `blkid`
- **Career arcs covered:** RHCSA (EX200 — "show free space on PVs"), RHCE (facts), SRE (capacity planning), DevOps (monitoring scripts)
- **Prerequisite:** Lab 121 (`pvcreate`)
- **Time Estimate:** 25–35 minutes
- **Difficulty arc:** Tasks 1–2 two PVs + optional VG for `-m` · Tasks 3–6 `pvs` variants · Task 7 `pvdisplay` · Task 8 `pvdisplay -m` · Task 9 `pvscan` · Task 10 capstone + cleanup

---

## Objective

Become fluent reading LVM's **short** view (`pvs`) and **long** view (`pvdisplay`), including the PE map (`-m`) once a VG exists.

**Capstone:** *"Produce `pv-report.txt` listing every PV with columns: name, size, free, VG name, UUID — using a single `pvs -o` command."*

> **Lab safety note:** Loop devices only.

---

## Concept: `pvs` for Machines, `pvdisplay` for Humans

```
pvs          → one line per PV, fixed/default columns
pvs -o ...   → exact columns for scripts / exams
pvdisplay    → paragraphs: flags, UUID, export state, device size vs PV size
pvdisplay -m → maps each PE range to LV or "free"
```

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| Default table | `pvs` |
| Custom columns | `pvs -o pv_name,pv_size,pv_free,vg_name` |
| All fields hint | `pvs -o help` |
| Segments | `pvs --segments` |
| Long detail | `pvdisplay /dev/...` |
| PE map | `pvdisplay -m /dev/...` |
| Rescan | `pvscan` |

---

## 🔧 The 10 Tasks

### Task 1 — `sudo -i` and lab dir

```bash
sudo -i
mkdir -p /root/lvm-pvs-lab && cd /root/lvm-pvs-lab
```

### Task 2 — Two PVs + small VG (enables `pvdisplay -m`)

```bash
cd /root/lvm-pvs-lab
IMG=/var/tmp/lvm-pvs.img
truncate -s 400M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 201MiB
parted -s "$LOOP" set 1 lvm on
parted -s "$LOOP" mkpart primary 201MiB 100%
parted -s "$LOOP" set 2 lvm on
partprobe "$LOOP"; udevadm settle
P1="${LOOP}p1"; P2="${LOOP}p2"
wipefs -a "$P1" "$P2" 2>/dev/null || true
pvcreate "$P1" "$P2"
vgcreate vgtest "$P1" "$P2"
lvcreate -L 64M -n lv0 vgtest "$P1"
echo "VG vgtest on $P1 $P2" | tee 02-setup.txt
```

### Task 3 — Baseline `pvs`

```bash
pvs | tee 03-pvs.txt
```

### Task 4 — `pvs -o` custom report

```bash
pvs -o pv_name,pv_uuid,vg_name,pv_size,pv_free,pv_fmt | tee 04-custom.txt
```

### Task 5 — `pvs --segments`

```bash
pvs --segments | tee 05-segments.txt
```

### Task 6 — Units and sort

```bash
pvs --units g --sort -pv_size | tee 06-units-sort.txt
```

### Task 7 — `pvdisplay` both PVs

```bash
pvdisplay "$P1" | tee 07-pv1.txt
pvdisplay "$P2" | tee 07-pv2.txt
```

### Task 8 — `pvdisplay -m` (PE map)

```bash
pvdisplay -m "$P1" | tee 08-map-p1.txt
```

**Read:** Lines like `LV Segment` / physical extent ranges allocated to `lv0`.

### Task 9 — `pvscan` + `pvs -a` (if any hidden)

```bash
pvscan -v 2>&1 | tee 09-pvscan.txt
pvs -a | tee 09-pvs-a.txt
```

### Task 10 — Capstone + cleanup

```bash
pvs -o pv_name,pv_size,pv_free,vg_name,pv_uuid | tee 10-capstone.txt
cat 10-capstone.txt

lvremove -f /dev/vgtest/lv0
vgremove -f vgtest
pvremove -ff "$P1" "$P2"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-pvs-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `pvdisplay -m` on orphan PV | Map empty | Normal until VG+LV |
| Wrong column name in `-o` | Error | Run `pvs -o help` |
| Mixing `MiB` vs `MB` in scripts | Wrong size math | Use `pvs --units b` for bytes |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01–02 Setup + VG + LV
- [ ] 03 `pvs`
- [ ] 04 `pvs -o`
- [ ] 05 `--segments`
- [ ] 06 units/sort
- [ ] 07 `pvdisplay`
- [ ] 08 `pvdisplay -m`
- [ ] 09 `pvscan` / `pvs -a`
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Lab 121 (pvcreate), Lab 123 (vgcreate).

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
