# Lab: Extend a Volume Group — `vgextend`, New PV, `pvmove` (overview)

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** `vgextend VG PV [PV...]` (add PVs to existing VG), prerequisites (`pvcreate` on new device), verifying with `vgs -o +pv_count,vg_size,vg_free`, **cannot `vgextend` with PV already in another VG**, shrinking VG via `vgreduce` (Lab 130), optional **`pvmove`** to evacuate extents before `vgreduce` (long operation — overview only), `vgmerge` / `vgsplit` (naming only), cloud workflow (attach new EBS → `pvcreate` → `vgextend`)
- **Career arcs covered:** RHCSA (EX200 — add disk to VG), RHCE, SRE storage expansion
- **Prerequisite:** Labs 121–125
- **Time Estimate:** 25–35 minutes
- **Difficulty arc:** Tasks 1–3 VG with one PV + LV · Task 4 observe free space · Task 5 second disk/PV · Task 6 `vgextend` · Task 7 `vgs`/`pvs` after extend · Task 8 grow LV into new space (`lvextend` preview) · Task 9 optional `pvmove` dry discussion · Task 10 capstone + cleanup

---

## Objective

Add a new Physical Volume to an existing Volume Group and confirm **free extents** increased.

**Capstone:** *"Start with VG on one 256 MiB PV nearly full; add second 256 MiB PV; `vgextend`; show `vgs` before/after `vg_free`."*

> **Lab safety note:** Two loop images or one image with two partitions — this lab uses **two loop files** for clarity.

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| Add PV to VG | `vgextend myvg /dev/sdc1` |
| Verify | `vgs -o vg_name,vg_size,vg_free,pv_count myvg` |
| Move extents | `pvmove /dev/old /dev/new` (slow) |

---

## 🔧 The 10 Tasks

### Task 1 — Dir

```bash
sudo -i
mkdir -p /root/lvm-vgext-lab && cd /root/lvm-vgext-lab
```

### Task 2 — First disk: PV + VG + LV (use most space)

```bash
IMG1=/var/tmp/lvm-vgx-a.img
truncate -s 256M "$IMG1"
L1=$(losetup --find --show "$IMG1")
parted -s "$L1" mklabel gpt
parted -s "$L1" mkpart primary 1MiB 100%
parted -s "$L1" set 1 lvm on
partprobe "$L1"; udevadm settle
P1="${L1}p1"
wipefs -a "$P1" 2>/dev/null || true
pvcreate "$P1"
vgcreate vgext "$P1"
lvcreate -l 90%FREE -n lv1 vgext
vgs -o vg_name,vg_size,vg_free,pv_count vgext | tee 02-before.txt
```

### Task 3 — Record baseline free

```bash
vgs -o vg_free --noheadings vgext | tee 03-free1.txt
```

### Task 4 — Second disk: PV only

```bash
IMG2=/var/tmp/lvm-vgx-b.img
truncate -s 256M "$IMG2"
L2=$(losetup --find --show "$IMG2")
parted -s "$L2" mklabel gpt
parted -s "$L2" mkpart primary 1MiB 100%
parted -s "$L2" set 1 lvm on
partprobe "$L2"; udevadm settle
P2="${L2}p1"
wipefs -a "$P2" 2>/dev/null || true
pvcreate "$P2"
pvs -o pv_name,vg_name "$P2" | tee 04-orphan-p2.txt
```

### Task 5 — `vgextend`

```bash
vgextend vgext "$P2" | tee 05-vgextend.txt
```

### Task 6 — Verify PV count and free space

```bash
vgs -o vg_name,vg_size,vg_free,pv_count vgext | tee 06-after.txt
pvs -o pv_name,vg_name,pv_size,pv_free | grep vgext | tee 06-pvs.txt
```

### Task 7 — Grow LV into new space

```bash
lvextend -l +100%FREE /dev/vgext/lv1 | tee 07-lvextend.txt
lvs vgext | tee 07-lvs.txt
```

### Task 8 — `vgs` after LV grow (free should drop)

```bash
vgs -o vg_name,vg_free vgext | tee 08-free-after-lvextend.txt
```

### Task 9 — `pvmove` (conceptual — skip run or tiny test)

```bash
cat > 09-pvmove-note.txt <<'EOF'
pvmove OLD_PV [NEW_PV]  moves used PEs off OLD_PV so you can vgreduce.
Can take hours on large disks. Exam rarely requires live pvmove.
EOF
cat 09-pvmove-note.txt
```

### Task 10 — Capstone + cleanup

```bash
diff 02-before.txt 06-after.txt | tee 10-diff.txt || true
lvremove -f /dev/vgext/lv1
vgremove -f vgext
pvremove -ff "$P1" "$P2"
losetup -d "$L1" "$L2"
rm -f "$IMG1" "$IMG2"
cd /root && rm -rf /root/lvm-vgext-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| PV in other VG | `vgextend` fails | `pvs` |
| Forgot `pvcreate` | not a PV | `pvcreate` first |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Dir
- [ ] 02 Tight VG+LV
- [ ] 03 Baseline free
- [ ] 04 Second PV
- [ ] 05 `vgextend`
- [ ] 06 Verify
- [ ] 07 `lvextend +100%FREE`
- [ ] 08 Free after grow
- [ ] 09 `pvmove` notes
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Labs 128–130.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
