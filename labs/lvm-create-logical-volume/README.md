# Lab: Create Logical Volumes — `lvcreate`, `-L`, `-l`, `-n`, `-r`, Thin (overview)

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** **Logical Volume (LV)** carves extents from a VG, `lvcreate -L Size -n NAME VG` (absolute size: `100M`, `1G`, `512K`), `lvcreate -l 50%VG -n NAME VG` (percent of VG), `lvcreate -l 100%FREE -n NAME VG` (consume remaining), `lvcreate -l N` (exact extent count), `lvcreate -n` name rules, `lvcreate -y` (assume yes), **`lvcreate --type raid1`** (mention only — beyond core RHCSA), **`lvextend -r`** preview here (Lab 128/129), device path `/dev/mapper/VG-LV` vs `/dev/VG/LV`, `lvcreate -W y|n` (zero wipe), `lvcreate -Zy` (y wipe signatures — dangerous), stripes `-i` (optional), verifying with `lvs` immediately, creating **XFS**/**ext4** on LV in same lab (optional mount)
- **Career arcs covered:** RHCSA (EX200 — `lvcreate -L 300M -n lv0 vg0`), RHCE (`lvol` module), SRE, DevOps
- **Prerequisite:** Lab 123
- **Time Estimate:** 25–40 minutes
- **Difficulty arc:** Tasks 1–2 VG · Task 3 fixed `-L` · Task 4 second LV · Task 5 `-l 100%FREE` · Task 6 path inspection `/dev/VG/LV` · Task 7 `mkfs.xfs` on LV · Task 8 mount + `df` · Task 9 `lvcreate -y` idempotent pattern · Task 10 capstone + cleanup

---

## Objective

Allocate space from a VG into one or more LVs using absolute sizes and **percent-of-VG / percent-FREE** forms.

**Capstone:** *"In VG `vglab`, create `lv_app` (128 MiB) and `lv_logs` using 100% of remaining free space; format `lv_app` with XFS; show `lvs`."*

> **Lab safety note:** Loop only.

---

## 📚 `lvcreate` Reference Table

| Goal | Command |
|---|---|
| Fixed size | `lvcreate -L 500M -n lv0 myvg` |
| All remaining | `lvcreate -l 100%FREE -n lv1 myvg` |
| Half VG | `lvcreate -l 50%VG -n lvhalf myvg` |
| N extents | `lvcreate -l 64 -n tiny myvg` |
| Skip prompts | `lvcreate -y ...` |

---

## 🔧 The 10 Tasks

### Task 1 — Lab dir

```bash
sudo -i
mkdir -p /root/lvm-lv-lab && cd /root/lvm-lv-lab
```

### Task 2 — VG `vglab` (one PV 512M)

```bash
IMG=/var/tmp/lvm-lv.img
truncate -s 512M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 100%
parted -s "$LOOP" set 1 lvm on
partprobe "$LOOP"; udevadm settle
P="${LOOP}p1"
wipefs -a "$P" 2>/dev/null || true
pvcreate "$P"
vgcreate vglab "$P"
vgs vglab | tee 02-vg.txt
```

### Task 3 — `lvcreate -L 128M`

```bash
lvcreate -L 128M -n lv_app vglab | tee 03-lvcreate.txt
lvs vglab | tee 03-lvs.txt
```

### Task 4 — Second LV fixed size

```bash
lvcreate -L 64M -n lv_tmp vglab | tee 04-second.txt
lvs -a vglab | tee 04-lvs-all.txt
```

### Task 5 — `100%FREE` third LV

```bash
lvcreate -l 100%FREE -n lv_logs vglab | tee 05-free.txt
lvs -o lv_name,lv_size,vg_name vglab | tee 05-lvs-sizes.txt
```

### Task 6 — Device nodes

```bash
ls -l /dev/vglab/ | tee 06-devmapper-dir.txt
readlink -f /dev/vglab/lv_app | tee 06-realpath.txt
```

### Task 7 — `mkfs.xfs` on `lv_app`

```bash
mkfs.xfs -f -L LV_APP /dev/vglab/lv_app | tee 07-mkfs.txt
blkid /dev/vglab/lv_app | tee 07-blkid.txt
```

### Task 8 — Mount and `df`

```bash
mkdir -p /mnt/lv_app
mount /dev/vglab/lv_app /mnt/lv_app
df -hT /mnt/lv_app | tee 08-df.txt
umount /mnt/lv_app
```

### Task 9 — `lvcreate -y` (scripting)

```bash
lvremove -f /dev/vglab/lv_tmp
lvcreate -y -L 64M -n lv_tmp vglab | tee 09-y.txt
```

### Task 10 — Capstone + cleanup

```bash
lvs -o lv_name,lv_size,pool_lv,origin vglab | tee 10-capstone.txt
cat 10-capstone.txt

lvremove -f /dev/vglab/lv_app /dev/vglab/lv_tmp /dev/vglab/lv_logs
vgremove -f vglab
pvremove -ff "$P"
losetup -d "$LOOP"
rm -f "$IMG"
cd /root && rm -rf /root/lvm-lv-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Not enough free extents | `lvcreate` fails | `vgs -o vg_free` |
| `-L` vs `-l` typo | Wrong size | `-L` = bytes suffix, `-l` = extents/% |
| LV name with `/` | Invalid | Use alphanumeric + `_` |

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Dir
- [ ] 02 `vgcreate`
- [ ] 03 `-L` LV
- [ ] 04 second `-L`
- [ ] 05 `100%FREE`
- [ ] 06 device paths
- [ ] 07 `mkfs.xfs`
- [ ] 08 mount test
- [ ] 09 `-y`
- [ ] 10 Capstone + teardown

---

## 🔗 Related Labs

Labs 126–129.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
