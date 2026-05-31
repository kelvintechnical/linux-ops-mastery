# Lab: Resize Filesystem After LV Extend — `xfs_growfs`, `resize2fs`, Online vs Offline

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** **LV larger than FS** after `lvextend` without `-r`, growing **XFS** with `xfs_growfs MOUNTPOINT` (online, no shrink), growing **ext4** with `resize2fs DEVICE` (online when mounted on modern kernels, or unmounted), `resize2fs -p` (progress), `resize2fs -M` (shrink to minimum — dangerous), `xfs_growfs -d` max data (default), `xfs_info` before/after, `df -h` / `lsblk` verification, `lvextend -r` as preferred one-shot (Lab 128), **cannot shrink XFS** — must backup/mkfs smaller, ext4 shrink via `resize2fs` then `lvreduce` (advanced), block size alignment, pairing with `findmnt`
- **Career arcs covered:** RHCSA (EX200 — "grow the filesystem to use new LV space"), RHCE, SRE
- **Prerequisite:** Labs 116–117, 128
- **Time Estimate:** 25–40 minutes
- **Difficulty arc:** Tasks 1–3 XFS LV extend + `xfs_growfs` · Task 4 `xfs_info` diff · Tasks 5–8 ext4 LV extend + `resize2fs` · Task 9 compare `lvextend -r` workflow · Task 10 capstone + cleanup

---

## Objective

After extending a logical volume, grow the **filesystem** to fill the new extents — using the correct tool per fstype.

**Capstone:** *"One LV formatted XFS: extend LV by 100 MiB, grow FS, capture `df` before/after. Second LV ext4: same with `resize2fs`."*

> **Lab safety note:** Loop only.

---

## 📚 Reference Table

| Fstype | Grow command | Shrink |
|---|---|---|
| xfs | `xfs_growfs /mountpoint` | Not supported |
| ext4 | `resize2fs /dev/VG/LV` | Advanced (`resize2fs -M`) |
| Both | `lvextend -r ...` | N/A |

---

## 🔧 The 10 Tasks

### Task 1 — VG with two LVs (xfs + ext4)

```bash
sudo -i
mkdir -p /root/lvm-fsresize-lab && cd /root/lvm-fsresize-lab
IMG=/var/tmp/lvm-fsresize.img
truncate -s 768M "$IMG"
LOOP=$(losetup --find --show "$IMG")
parted -s "$LOOP" mklabel gpt
parted -s "$LOOP" mkpart primary 1MiB 100%
parted -s "$LOOP" set 1 lvm on
partprobe "$LOOP"; udevadm settle
P="${LOOP}p1"
wipefs -a "$P" 2>/dev/null || true
pvcreate "$P"
vgcreate vgfsgrow "$P"
lvcreate -L 200M -n lvxfs vgfsgrow
lvcreate -L 200M -n lvext4 vgfsgrow
lvs vgfsgrow | tee 01-lvs.txt
```

### Task 2 — XFS: format, mount, baseline `df`

```bash
mkfs.xfs -f -L LVXFS /dev/vgfsgrow/lvxfs
mkdir -p /mnt/xfsgrow
mount /dev/vgfsgrow/lvxfs /mnt/xfsgrow
df -h /mnt/xfsgrow | tee 02-df-xfs-before.txt
```

### Task 3 — `lvextend` LV only + `xfs_growfs`

```bash
lvextend -L +128M /dev/vgfsgrow/lvxfs
df -h /mnt/xfsgrow | tee 03-df-before-growfs.txt
xfs_growfs /mnt/xfsgrow | tee 03-xfs_growfs.txt
df -h /mnt/xfsgrow | tee 03-df-xfs-after.txt
```

### Task 4 — `xfs_info` snapshot

```bash
xfs_info /mnt/xfsgrow | tee 04-xfs_info.txt
```

### Task 5 — ext4: format, mount, baseline

```bash
mkfs.ext4 -F -L LVEXT4 /dev/vgfsgrow/lvext4
mkdir -p /mnt/ext4grow
mount /dev/vgfsgrow/lvext4 /mnt/ext4grow
df -h /mnt/ext4grow | tee 05-df-ext4-before.txt
```

### Task 6 — `lvextend` + `resize2fs` (device path)

```bash
lvextend -L +128M /dev/vgfsgrow/lvext4
df -h /mnt/ext4grow | tee 06-df-ext4-stale.txt
resize2fs /dev/vgfsgrow/lvext4 | tee 06-resize2fs.txt
df -h /mnt/ext4grow | tee 06-df-ext4-after.txt
```

### Task 7 — `dumpe2fs -h` block count sanity

```bash
dumpe2fs -h /dev/vgfsgrow/lvext4 | grep -E 'Block count|Block size|Free blocks' | tee 07-dumpe2fs.txt
```

### Task 8 — Second grow ext4 with `resize2fs -p`

```bash
lvextend -L +64M /dev/vgfsgrow/lvext4
resize2fs -p /dev/vgfsgrow/lvext4 | tee 08-resize2fs-p.txt
```

### Task 9 — `lvextend -r` demonstration on `lvxfs` (add small slice if VG has room)

```bash
vgs -o vg_free vgfsgrow | tee 09-vgfree.txt
lvextend -r -L +32M /dev/vgfsgrow/lvxfs 2>&1 | tee 09-lvextend-r.txt
df -h /mnt/xfsgrow | tee 09-df-r.txt
```

### Task 10 — Capstone + cleanup

```bash
cat > 10-report.txt <<EOF
XFS df: $(df -h /mnt/xfsgrow | tail -1)
ext4 df: $(df -h /mnt/ext4grow | tail -1)
EOF
cat 10-report.txt

umount /mnt/xfsgrow /mnt/ext4grow
lvremove -f /dev/vgfsgrow/lvxfs /dev/vgfsgrow/lvext4
vgremove -f vgfsgrow
pvremove -ff "$P"
losetup -d "$LOOP"
rm -f "$IMG"
rmdir /mnt/xfsgrow /mnt/ext4grow
cd /root && rm -rf /root/lvm-fsresize-lab
exit
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `xfs_growfs` on block device while unmounted | Use mountpoint or `xfs_growfs /dev/VG/LV` | Mount first or use dev path per man page |
| `resize2fs` on XFS | error | Wrong tool |
| Shrink XFS | impossible | Rebuild LV |

---

## Lab Checklist (10 Tasks)

- [ ] 01 Two LVs
- [ ] 02 XFS mount
- [ ] 03 `xfs_growfs`
- [ ] 04 `xfs_info`
- [ ] 05 ext4 mount
- [ ] 06 `resize2fs`
- [ ] 07 `dumpe2fs -h`
- [ ] 08 `resize2fs -p`
- [ ] 09 `lvextend -r`
- [ ] 10 Report + teardown

---

## 🔗 Related Labs

Labs 116–117, 128, 130.

---

## 👤 Author

**Kelvin R. Tobias** — [GitHub](https://github.com/kelvintechnical)
