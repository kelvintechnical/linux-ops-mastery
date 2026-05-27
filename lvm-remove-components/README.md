# Lab: Remove LVM Components — `lvremove`, `vgreduce`, `vgremove`, `pvremove`, Order & Safety

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** Safe teardown order: **`umount`** (or `swapoff`) → **`lvremove`** → **`vgremove`** (or `vgreduce` first if multi-PV) → **`pvremove`**, `lvremove -f` (force), `lvremove --yes` batch, `vgremove [-f|--force] VG`, `vgreduce VG PV` (remove PV from VG after `pvmove` or if empty), `pvremove [-ff]`, **cannot `pvremove` PV still in VG**, `lvmchange -an` / `-ay` (deactivate all — rare rescue), verifying nothing left with `pvs`, `vgs`, `lvs`, wiping with `wipefs -a` after PV remove for clean disk reuse, snapshot removal order (remove snap before origin if needed — depends), emergency `dmsetup remove` (avoid — use lvm tools)
- **Career arcs covered:** RHCSA (EX200 — decommission storage), RHCE (playbook teardown), SRE (prevent duplicate PV UUID)
- **Prerequisite:** Labs 121–129
- **Time Estimate:** 25–40 minutes
- **Difficulty arc:** Tasks 1–3 stack VG+2LV+mount · Task 4 remove one LV while other mounted · Task 5 `vgreduce` second PV from VG · Task 6 `pvremove` evacuated PV · Task 7 remove remaining LV · Task 8 `vgremove` · Task 9 `pvremove` last PV · Task 10 capstone + wipefs proof

---

## Objective

Tear down an LVM stack **without** leaving orphan devices, duplicate headers, or busy mounts.

**Capstone:** *"Fully remove VG `vgteardown` and all PVs; prove `pvs` and `vgs` show empty for this lab's devices."*

> **Lab safety note:** Loop only. On exams, **unmount first** — always.

---

## Concept: Reverse of Create

```
Create:  pvcreate → vgcreate → lvcreate → mkfs → mount
Remove:  umount   → lvremove → vgremove → pvremove
         (vgreduce/pvmove when shrinking multi-PV VG)
```

---

## 📚 Reference Table

| Step | Command |
|---|---|
| Unmount | `umount /mnt/X` |
| Remove LV | `lvremove /dev/VG/LV` |
| Reduce VG | `vgreduce VG PV` |
| Remove VG | `vgremove VG` |
| Remove PV label | `pvremove PV` |

---

## 🔧 The 10 Tasks

### Task 1 — Two-PV VG + two LVs

```bash
sudo -i
mkdir -p /root/lvm-rm-lab && cd /root/lvm-rm-lab
IMG1=/var/tmp/lvm-rm-a.img; IMG2=/var/tmp/lvm-rm-b.img
truncate -s 256M "$IMG1"; truncate -s 256M "$IMG2"
L1=$(losetup --find --show "$IMG1"); L2=$(losetup --find --show "$IMG2")
for L in "$L1" "$L2"; do
  parted -s "$L" mklabel gpt
  parted -s "$L" mkpart primary 1MiB 100%
  parted -s "$L" set 1 lvm on
  partprobe "$L"
done
udevadm settle
P1="${L1}p1"; P2="${L2}p1"
wipefs -a "$P1" "$P2" 2>/dev/null || true
pvcreate "$P1" "$P2"
vgcreate vgteardown "$P1" "$P2"
lvcreate -L 128M -n lv1 vgteardown "$P1"
lvcreate -L 128M -n lv2 vgteardown "$P2"
lvs vgteardown | tee 01-lvs.txt
```

### Task 2 — mkfs + mount both

```bash
mkfs.xfs -f /dev/vgteardown/lv1
mkfs.xfs -f /dev/vgteardown/lv2
mkdir -p /mnt/lv1 /mnt/lv2
mount /dev/vgteardown/lv1 /mnt/lv1
mount /dev/vgteardown/lv2 /mnt/lv2
findmnt | grep lv | tee 02-findmnt.txt
```

### Task 3 — Attempt `lvremove` while mounted (expect failure)

```bash
lvremove /dev/vgteardown/lv1 2>&1 | tee 03-busy-fail.txt || true
```

### Task 4 — Correct: `umount` then `lvremove`

```bash
umount /mnt/lv1
lvremove -f /dev/vgteardown/lv1 | tee 04-removed.txt
lvs vgteardown | tee 04-lvs.txt
```

### Task 5 — `vgreduce` to drop PV2 from VG (after LV on it gone — move lv2 first)

```bash
umount /mnt/lv2
lvremove -f /dev/vgteardown/lv2
vgreduce vgteardown "$P2" | tee 05-vgreduce.txt
pvs -o pv_name,vg_name "$P1" "$P2" | tee 05-pvs.txt
```

### Task 6 — `pvremove` orphaned PV2

```bash
pvremove "$P2" | tee 06-pvremove2.txt
pvs "$P2" 2>&1 | tee 06-p2-gone.txt
```

### Task 7 — Create tiny LV again on remaining PV then remove (practice cycle)

```bash
lvcreate -L 64M -n lvtmp vgteardown
lvremove -f /dev/vgteardown/lvtmp | tee 07-cycle.txt
```

### Task 8 — `vgremove`

```bash
vgremove -f vgteardown | tee 08-vgremove.txt
vgs 2>&1 | grep vgteardown | tee 08-gone.txt || echo "vgteardown removed" | tee 08-gone.txt
```

### Task 9 — `pvremove` last PV

```bash
pvremove -ff "$P1" | tee 09-pvremove1.txt
pvs "$P1" 2>&1 | tee 09-p1-gone.txt
```

### Task 10 — Capstone: `wipefs` proof + loop detach

```bash
wipefs -n "$P1" 2>&1 | tee 10-wipefs.txt
losetup -d "$L1" "$L2"
rm -f "$IMG1" "$IMG2"
rmdir /mnt/lv1 /mnt/lv2
cd /root && rm -rf /root/lvm-rm-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `vgremove` with LV still present | Error | `lvremove` first |
| `pvremove` on PV in VG | Error | `vgreduce` or `vgremove` |
| Skip umount | `lvremove` fails | `umount` |

---

## Lab Checklist (10 Tasks)

- [ ] 01 Two-PV VG + LVs
- [ ] 02 Mount both
- [ ] 03 Busy remove fails
- [ ] 04 umount + `lvremove`
- [ ] 05 `vgreduce`
- [ ] 06 `pvremove` P2
- [ ] 07 LV cycle
- [ ] 08 `vgremove`
- [ ] 09 `pvremove` P1
- [ ] 10 wipefs + detach

---

## 🔗 Related Labs

Labs 121–129.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
