# Lab: Create a Volume Group — `vgcreate`, `-s` PE Size, Multi-PV, `vgs`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** **Volume Group (VG)** pools PV extents, `vgcreate [-s|--physicalextentsize SIZE] VG PV [PV...]`, default PE size **4 MiB** on RHEL 9, maximum PVs/LVs (`--maxphysicalvolumes`, `--maxlogicalvolumes`), `vgcreate --clustered n` (legacy), naming rules (no `/`), `vgs` immediate verification, partial failure if one PV busy, `vgck` (metadata consistency), exporting (`vgexport`) mention only, relationship between **PE size** and max VG size
- **Career arcs covered:** RHCSA (EX200 — `vgcreate vgname /dev/vdb1 /dev/vdb2`), RHCE (`lvg` module), SRE (pool naming), DevOps (IaC idempotency)
- **Prerequisite:** Lab 121
- **Time Estimate:** 20–35 minutes
- **Difficulty arc:** Tasks 1–3 PVs · Task 4 default `vgcreate` · Task 5 `vgs`/`vgdisplay` · Task 6 destroy + recreate with `-s 8M` · Task 7 verify PE math · Task 8 `vgcreate` with max limits · Task 9 `vgck` · Task 10 capstone + cleanup

---

## Objective

Pool one or more PVs into a **volume group** with a chosen physical extent size, and verify the VG with `vgs` / `vgdisplay`.

**Capstone:** *"Create `vgdata` from two loop PVs using PE size 8 MiB, show `vgs -o vg_name,vg_size,vg_free,vg_extent_size`."*

> **Lab safety note:** Loop only.

---

## Concept: VG = Named Pool of Extents

```
PV1 (extents) ──┐
                ├──► vgcreate vgdata ──► VG metadata (written on all PVs in VG)
PV2 (extents) ──┘
```

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| Default PE (4 MiB) | `vgcreate myvg /dev/sd{b,c}1` |
| Custom PE | `vgcreate -s 8M myvg DEV...` |
| Max PVs | `vgcreate --maxphysicalvolumes 128 myvg DEV` |
| Check | `vgs myvg` |
| Metadata check | `vgck myvg` |
| Remove empty VG | `vgremove myvg` |

---

## 🔧 The 10 Tasks

### Task 1 — Lab directory

```bash
sudo -i
mkdir -p /root/lvm-vg-lab && cd /root/lvm-vg-lab
```

### Task 2 — Image + two PVs

```bash
IMG=/var/tmp/lvm-vg.img
truncate -s 512M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 256MiB
parted -s "$LOOP" set 1 lvm on
parted -s "$LOOP" mkpart primary 256MiB 100%
parted -s "$LOOP" set 2 lvm on
partprobe "$LOOP"; udevadm settle
P1="${LOOP}p1"; P2="${LOOP}p2"
wipefs -a "$P1" "$P2" 2>/dev/null || true
pvcreate "$P1" "$P2"
echo "$P1 $P2" | tee 02-pvs.txt
```

### Task 3 — Confirm PVs not in any VG

```bash
pvs -o pv_name,vg_name "$P1" "$P2" | tee 03-orphan.txt
```

### Task 4 — `vgcreate` default PE

```bash
vgcreate vgtest "$P1" "$P2" | tee 04-vgcreate.txt
vgs vgtest | tee 04-vgs.txt
```

### Task 5 — `vgdisplay` summary

```bash
vgdisplay vgtest | tee 05-vgdisplay.txt
```

**Read:** `VG Size`, `PE Size`, `Total PE`, `Free PE / Size`, `UUID`.

### Task 6 — Tear down and recreate with `-s 8M`

```bash
vgremove -f vgtest
vgcreate -s 8M vgtest "$P1" "$P2" | tee 06-vgcreate-8m.txt
vgs -o vg_name,vg_extent_size,vg_size,vg_free vgtest | tee 06-vgs-pe.txt
```

### Task 7 — PE count sanity check

```bash
vgdisplay vgtest | grep -E 'PE / Size|PE Size' | tee 07-pe-math.txt
```

### Task 8 — `vgcreate` with `--maxlogicalvolumes` and `--maxphysicalvolumes`

```bash
vgremove -f vgtest
vgcreate -s 4M --maxlogicalvolumes 10 --maxphysicalvolumes 4 vgtest "$P1" "$P2" | tee 08-limits.txt
vgdisplay vgtest | grep -i max | tee 08-max.txt
```

### Task 9 — `vgck`

```bash
vgck vgtest 2>&1 | tee 09-vgck.txt
```

### Task 10 — Capstone + cleanup

```bash
vgs -o vg_name,vg_size,vg_free,vg_extent_size vgtest | tee 10-capstone.txt
cat 10-capstone.txt

vgremove -f vgtest
pvremove -ff "$P1" "$P2"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-vg-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| PV already in another VG | `vgcreate` fails | `pvs` to see VG |
| PE size too large for tiny VG | Not enough PEs | Smaller `-s` or bigger disk |
| Typo in VG name | Wrong device later | Consistent naming (`vg_sys`, `vg_data`) |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Dir
- [ ] 02 Two PVs
- [ ] 03 Orphan PVs
- [ ] 04 `vgcreate` default
- [ ] 05 `vgdisplay`
- [ ] 06 `-s 8M` recreate
- [ ] 07 PE math
- [ ] 08 max limits
- [ ] 09 `vgck`
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Labs 121, 124–126.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
