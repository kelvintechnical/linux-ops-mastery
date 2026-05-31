# Lab: Extend a Logical Volume — `lvextend`, `-L`, `-l`, `-r`, `+` Suffix Semantics

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** `lvextend [-L +SIZE|-L SIZE|-l +EXTENTS|-l PERCENT%VG|PERCENT%PVS|PERCENT%ORIGIN] LV`, **`+`** prefix meaning **add to current** vs absolute new size, `lvextend -l +100%FREE` (eat all VG free extents), `lvextend -L +500M /dev/VG/LV`, resizing FS in same step with **`-r`** (calls appropriate `xfs_growfs` or `resize2fs` — RHEL 9), `lvextend --resizefs` (alias of `-r` on supported versions), `lvextend -n` dry run where available, verifying with `lvs` before/after, **cannot shrink** with `lvextend` (use `lvreduce` — out of RHCSA core / dangerous), online vs offline (linear LV extend is online for FS grow), `lvmconf` alignment (mention)
- **Career arcs covered:** RHCSA (EX200 — grow LV), RHCE, SRE
- **Prerequisite:** Labs 125–127
- **Time Estimate:** 25–35 minutes
- **Difficulty arc:** Tasks 1–3 LV with free VG space · Task 4 `lvextend -L +50M` · Task 5 `+100%FREE` · Task 6 absolute `-L` resize to specific total · Task 7 `lvextend -r` with XFS · Task 8 ext4 + `resize2fs` via `-r` · Task 9 `lvs -o` diff · Task 10 capstone + cleanup

---

## Objective

Grow an LV by absolute size, additive size, or **all free extents**, and optionally grow the filesystem in **one** command with `-r`.

**Capstone:** *"Extend `lvdata` by +100 MiB, then grow filesystem with `lvextend -r` on mounted XFS."*

> **Lab safety note:** Loop only. `lvreduce` can destroy data — not used here.

---

## 📚 Reference Table

| Goal | Command |
|---|---|
| Add 200M | `lvextend -L +200M /dev/vg/lv` |
| Set total 1G | `lvextend -L 1G /dev/vg/lv` |
| All VG free | `lvextend -l +100%FREE /dev/vg/lv` |
| + FS grow | `lvextend -r -L +200M /dev/vg/lv` |

---

## 🔧 The 10 Tasks

### Task 1 — Setup: VG with spare space

```bash
sudo -i
mkdir -p /root/lvm-lvext-lab && cd /root/lvm-lvext-lab
IMG=/var/tmp/lvm-lvext.img
truncate -s 512M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 100%
parted -s "$LOOP" set 1 lvm on
partprobe "$LOOP"; udevadm settle
P="${LOOP}p1"
wipefs -a "$P" 2>/dev/null || true
pvcreate "$P"
vgcreate vgext "$P"
lvcreate -L 128M -n lvdata vgext
lvs -o lv_name,lv_size,vg_free vgext | tee 01-start.txt
```

### Task 2 — `lvextend -L +32M` (additive)

```bash
lvextend -L +32M /dev/vgext/lvdata | tee 02-add32.txt
lvs vgext | tee 02-after.txt
```

### Task 3 — Another additive extend `+16M`

```bash
lvextend -L +16M /dev/vgext/lvdata | tee 03-add16.txt
lvs vgext | tee 03-lvs.txt
vgs -o vg_free vgext | tee 03-vgfree.txt
```

### Task 4 — Absolute target size `-L 224M` (must be ≥ current LV size)

```bash
lvextend -L 224M /dev/vgext/lvdata | tee 04-abs.txt
lvs -o lv_name,lv_size vgext | tee 04-lvs.txt
```

### Task 5 — `mkfs.xfs` and mount

```bash
mkfs.xfs -f /dev/vgext/lvdata
mkdir -p /mnt/lvdata
mount /dev/vgext/lvdata /mnt/lvdata
df -h /mnt/lvdata | tee 05-df.txt
```

### Task 6 — Extend **LV only** — `df` unchanged until FS grow

```bash
lvextend -L +64M /dev/vgext/lvdata | tee 06-lv-only.txt
lvs -o lv_name,lv_size vgext | tee 06-lvs-bigger.txt
df -h /mnt/lvdata | tee 06-df-unchanged.txt
```

### Task 7 — Grow XFS manually: `xfs_growfs`

```bash
xfs_growfs /mnt/lvdata | tee 07-xfs_growfs.txt
df -h /mnt/lvdata | tee 07-df-grown.txt
```

### Task 8 — One-shot: `lvextend -r` (LV + FS together)

```bash
lvextend -r -L +32M /dev/vgext/lvdata | tee 08-lvextend-r.txt
df -h /mnt/lvdata | tee 08-df-after-r.txt
```

### Task 9 — Eat remaining VG space: `+100%FREE` then grow FS

```bash
lvextend -l +100%FREE /dev/vgext/lvdata | tee 09-allfree-lv.txt
xfs_growfs /mnt/lvdata | tee 09-xfs-final.txt
df -h /mnt/lvdata | tee 09-df-final.txt
```

### Task 10 — Capstone + cleanup

```bash
umount /mnt/lvdata
lvremove -f /dev/vgext/lvdata
vgremove -f vgext
pvremove -ff "$P"
losetup -d "$LOOP"
rm -f "$IMG"
rmdir /mnt/lvdata
cd /root && rm -rf /root/lvm-lvext-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Extended LV but not FS | `df` unchanged | `xfs_growfs` or `lvextend -r` |
| `-L 200M` when you meant add 200 | LV smaller than expected | Use `-L +200M` |
| XFS shrink | Impossible | Backup + recreate |

---

## Lab Checklist (10 Tasks)

- [ ] 01 Initial VG/LV
- [ ] 02 `+32M`
- [ ] 03 `+16M`
- [ ] 04 absolute `-L 224M`
- [ ] 05 mkfs+mount
- [ ] 06 extend LV only
- [ ] 07 `xfs_growfs`
- [ ] 08 `lvextend -r`
- [ ] 09 `+100%FREE` + `xfs_growfs`
- [ ] 10 Teardown

---

## 🔗 Related Labs

Lab 129 (FS resize theory), Lab 125.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
