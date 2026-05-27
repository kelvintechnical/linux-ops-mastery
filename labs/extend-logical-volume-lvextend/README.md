# Lab: Extend a Logical Volume — `lvextend`, `lvextend --resizefs`, `lvreduce`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** the canonical "grow this LV" workflow, `lvextend -L SIZE VG/LV` (absolute target size), `lvextend -L +SIZE VG/LV` (additive — the friendly form), `lvextend -l +N VG/LV` (extent count), `lvextend -l +100%FREE VG/LV` (consume all VG free space — the production one-liner), `lvextend --resizefs` / `-r` (grow the filesystem in the same command — works for ext4 and XFS), the manual two-step pattern (`lvextend` then `xfs_growfs` or `resize2fs`) and when to prefer it over `-r`, online vs offline behavior (ext4 and XFS both grow online with the FS mounted), the inverse `lvreduce` (XFS cannot shrink — ext4 can), the safe-shrink sequence for ext4 (`umount` → `e2fsck -f` → `resize2fs LV NEW_SIZE` → `lvreduce -L NEW_SIZE`), `lvextend --type striped --stripes N` to grow into a striped layout, the "VG is full" failure (`Insufficient free space`) and its remedy (`vgextend` first — Lab 127), the `lvextend -L 1G --use-policies` thin-pool autoextend pattern, `lvconvert --merge` for snapshot rollback (sibling op), idempotency: how Ansible `lvol` reconciles desired size against current, percentage forms (`+50%FREE`, `+25%VG`, `+100%ORIGIN` for snapshots)
- **Career arcs covered:** RHCSA (EX200 — "grow lv_data by 500 MiB"), RHCE (Ansible `community.general.lvol: lv=data size=+500m`), SRE (filesystem-fill alert → live extend), DevOps (cloud-init or CI hot-grow), AI / MLOps (training-data LV scale-up per epoch)
- **Prerequisite:** Lab 125 (lvcreate), Lab 127 (vgextend)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox · Task 2 baseline LV + FS · Task 3 absolute size extend · Task 4 additive `+SIZE` extend · Task 5 percentage `+100%FREE` · Task 6 one-shot `lvextend -r` · Task 7 manual `xfs_growfs` step · Task 8 ext4 shrink with `lvreduce` · Task 9 idempotent ensure-size script · Task 10 capstone + cleanup

---

## Objective

Grow an LV every way the exam asks (absolute, additive, percentage), with and without `--resizefs`, and master the ext4-only safe shrink. By the end you can answer "grow lv_data by 500 MiB and grow its XFS" in one line, and you know why the XFS shrink question is a trap.

The capstone is: *"On a mounted ext4 LV: grow by absolute size (Task 3), additive (Task 4), percentage (Task 5), one-shot with `-r` (Task 6); on a mounted XFS LV: grow then manually `xfs_growfs`; then safely shrink the ext4 LV by 100 MiB."*

> **Lab safety note:** Loopback only. `lvreduce` is **destructive** if you shrink the LV below the filesystem size — the safe-shrink sequence in Task 8 is the only correct way.

---

## Concept: Two Layers Must Grow Together

```
   ┌─────────────────────────────────────────────────────────────┐
   │  Block layer        |  Filesystem layer                      │
   │     (LV)            |     (ext4, xfs)                        │
   │      │              |        │                               │
   │      │ lvextend     |        │ resize2fs / xfs_growfs        │
   │      ▼              |        ▼                               │
   │   ┌────────┐  ←  ─  ─  ─  ─  ─  the FS sees the new bytes    │
   │   │ LV new │       only after BOTH steps complete            │
   │   │  size  │                                                  │
   │   └────────┘                                                  │
   │                                                              │
   │  Forget step 2  →  free space is "wasted" (allocated to LV   │
   │                       but not visible to the FS).             │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** `lvextend -r` is the one-shot. Without `-r`, you must remember step 2 (`xfs_growfs` or `resize2fs`). The most common production mistake is "I ran `lvextend` and the disk is still full." The cause is always: filesystem was not grown.

---

## 📜 Why `lvextend` Has `-r` — The Story

For LVM's first decade, growing an LV meant: `lvextend` first, then the FS-specific resize tool second. The two-step nature was scriptable but error-prone for humans — half the support tickets to Red Hat were "I ran lvextend but `df` still shows the old size."

The LVM team added `--resizefs` (short `-r`) around 2014 as a convenience wrapper that:
1. Reads the FS type from the LV.
2. Runs the matching FS-resize tool after the metadata change lands.

It is the recommended form on RHEL 7+. The two-step pattern remains for scripts that want to verify between steps, or grow an LV without growing the FS (rare — usually because the FS will be re-formatted).

> **The point of the story:** Use `-r` unless you have a specific reason not to.

---

## 👪 The Extend Family

```
Grow
├── lvextend -L SIZE VG/LV                ← absolute target
├── lvextend -L +SIZE VG/LV               ← additive
├── lvextend -l +N VG/LV                  ← extent count
├── lvextend -l +100%FREE VG/LV           ← consume VG free
├── lvextend -L +SIZE -r VG/LV            ← grow LV + grow FS in one shot
├── lvextend -L SIZE -r VG/LV --resizefs
└── lvextend ... --use-policies           ← thin-pool autoextend

Shrink (ext4 only; XFS cannot shrink)
├── umount /mnt/X
├── e2fsck -f /dev/VG/LV
├── resize2fs /dev/VG/LV NEW_SIZE
├── lvreduce -L NEW_SIZE VG/LV
└── mount /dev/VG/LV /mnt/X

Filesystem-only resize
├── xfs_growfs /mountpoint                 ← MUST be mounted
└── resize2fs /dev/VG/LV [NEW_SIZE]        ← can be mounted or not
```

---

## 📚 lvextend Reference Table

| Goal | Command |
|---|---|
| Absolute 2 GiB | `lvextend -L 2G vg_data/lv_app` |
| Add 500 MiB | `lvextend -L +500M vg_data/lv_app` |
| Add 25 extents | `lvextend -l +25 vg_data/lv_app` |
| Consume all free | `lvextend -l +100%FREE vg_data/lv_app` |
| Grow + FS (one shot) | `lvextend -L +500M -r vg_data/lv_app` |
| Add and grow XFS | `lvextend -L +500M vg_data/lv_app && xfs_growfs /mnt/data` |
| Shrink ext4 by 100 MiB | safe-shrink sequence (Task 8) |
| Shrink XFS | **NOT POSSIBLE** — recreate FS |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Grow lv_data by 500 MiB" is on the exam. |
| **RHCE candidate** | Ansible `community.general.lvol: lv=app size=+500m`. |
| **SRE / Platform** | Filesystem-fill page → `lvextend -r` resolution. |
| **DevOps** | cloud-init growpart + `lvextend -r` after EBS expand. |
| **AI / MLOps** | Per-epoch dataset growth → live LV extend. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox: VG with 4 PVs

```bash
sudo -i
mkdir -p /root/lvextend-lab && cd /root/lvextend-lab

for n in 1 2 3 4; do
  IMG=/var/tmp/lvex-pv-$n.img
  truncate -s 1G "$IMG"
  L=$(sudo losetup --find --show "$IMG")
  eval "LOOP_$n=$L"
done

sudo pvcreate "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4" >/dev/null
sudo vgcreate vg_grow "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4" >/dev/null

sudo vgs vg_grow | tee 01-vgs.txt
```

---

### Task 2 — Baseline LV + ext4 mounted

```bash
cd /root/lvextend-lab

sudo lvcreate -L 200M -n lv_ext4 vg_grow >/dev/null
sudo mkfs.ext4 -L LVEXT4 /dev/vg_grow/lv_ext4 >/dev/null

sudo mkdir -p /mnt/lv_ext4
sudo mount /dev/vg_grow/lv_ext4 /mnt/lv_ext4

sudo lvcreate -L 200M -n lv_xfs vg_grow >/dev/null
sudo mkfs.xfs -L LVXFS /dev/vg_grow/lv_xfs >/dev/null
sudo mkdir -p /mnt/lv_xfs
sudo mount /dev/vg_grow/lv_xfs /mnt/lv_xfs

sudo lvs -o lv_name,lv_size,segtype vg_grow | tee 02-lvs.txt
df -hT /mnt/lv_ext4 /mnt/lv_xfs | tee 02-df.txt
```

---

### Task 3 — Absolute extend (`-L SIZE`)

```bash
cd /root/lvextend-lab

sudo lvextend -L 400M /dev/vg_grow/lv_ext4 | tee 03-lvextend.txt
sudo lvs -o lv_name,lv_size /dev/vg_grow/lv_ext4 | tee 03-lvs.txt
df -hT /mnt/lv_ext4 | tee 03-df-before-resizefs.txt

sudo resize2fs /dev/vg_grow/lv_ext4 | tee 03-resize2fs.txt
df -hT /mnt/lv_ext4 | tee 03-df-after.txt
```

**Reading it left to right:** `-L 400M` is **absolute target size** — not additive. After `lvextend`, the LV is 400 MiB but the FS still believes it is 200 MiB. `resize2fs` (online) tells the FS about the new bytes.

**The story:** This is the **two-step** pattern. Useful when you want to verify the LV grew before touching the FS.

**Expected output:**

```text
  Size of logical volume vg_grow/lv_ext4 changed from 200.00 MiB to 400.00 MiB.
  Logical volume vg_grow/lv_ext4 successfully resized.
```

```text
resize2fs 1.46.5 (30-Dec-2021)
Filesystem at /dev/vg_grow/lv_ext4 is mounted on /mnt/lv_ext4; on-line resizing required
The filesystem on /dev/vg_grow/lv_ext4 is now 409600 (1k) blocks long.
```

---

### Task 4 — Additive extend (`-L +SIZE`)

```bash
cd /root/lvextend-lab

sudo lvextend -L +100M /dev/vg_grow/lv_ext4 | tee 04-lvextend.txt
sudo resize2fs /dev/vg_grow/lv_ext4 | tee 04-resize2fs.txt
df -hT /mnt/lv_ext4 | tee 04-df.txt
```

**Reading it left to right:** `-L +100M` adds 100 MiB to the **current** size. This is the friendliest form when you do not know (or care) about the current size — you just want more.

**The story:** Most `lvextend` invocations in the wild use this form. It composes cleanly: "I always add 25%" is one command, regardless of starting size.

---

### Task 5 — Percentage (`-l +100%FREE`)

```bash
cd /root/lvextend-lab

sudo vgs -o vg_name,vg_free vg_grow | tee 05-pre.txt

sudo lvextend -l +100%FREE /dev/vg_grow/lv_xfs | tee 05-lvextend.txt
sudo lvs -o lv_name,lv_size /dev/vg_grow/lv_xfs | tee 05-lvs.txt
sudo vgs -o vg_name,vg_free vg_grow | tee 05-post.txt

sudo xfs_growfs /mnt/lv_xfs | tee 05-xfsgrow.txt
df -hT /mnt/lv_xfs | tee 05-df.txt
```

**Reading it left to right:** `-l +100%FREE` consumes every remaining extent in the VG. After this command, `vg_free` is `0` (or a few MiB of rounding).

**The story:** This is the **production one-liner** for "fill this LV to the brim of the VG." Combine with `--resizefs` for the most common form: `lvextend -l +100%FREE -r VG/LV`.

**Expected output:**

```text
  Size of logical volume vg_grow/lv_xfs changed from 200.00 MiB to <3.42 GiB.
  Logical volume vg_grow/lv_xfs successfully resized.
```

```text
meta-data=/dev/mapper/vg_grow-lv_xfs isize=512 agcount=4, ...
data blocks changed from 51200 to 896000
```

---

### Task 6 — One-shot `lvextend -r`

```bash
cd /root/lvextend-lab

# First, shrink ext4 LV to make room
sudo umount /mnt/lv_ext4
sudo e2fsck -fy /dev/vg_grow/lv_ext4 >/dev/null
sudo resize2fs /dev/vg_grow/lv_ext4 100M >/dev/null
sudo lvreduce -L 100M -fy /dev/vg_grow/lv_ext4 >/dev/null
sudo mount /dev/vg_grow/lv_ext4 /mnt/lv_ext4

# Now do the canonical one-shot
sudo lvextend -L +200M -r /dev/vg_grow/lv_ext4 | tee 06-oneshot.txt
df -hT /mnt/lv_ext4 | tee 06-df.txt
```

**Reading it left to right:** `-r` (also `--resizefs`) tells `lvextend` to detect the FS type and run the matching resize tool after the block-layer growth. One command, both layers.

**The story:** This is the **right** form for daily use. It is shorter, atomic in feel, and matches what Ansible's `community.general.lvol` calls when `resizefs: yes` is set.

**Expected output (excerpt):**

```text
  Size of logical volume vg_grow/lv_ext4 changed from 100.00 MiB to 300.00 MiB.
  Logical volume vg_grow/lv_ext4 successfully resized.
resize2fs 1.46.5 (30-Dec-2021)
Filesystem at /dev/vg_grow/lv_ext4 is mounted on /mnt/lv_ext4; on-line resizing required
The filesystem on /dev/vg_grow/lv_ext4 is now 307200 (1k) blocks long.
```

---

### Task 7 — Manual `xfs_growfs` workflow

```bash
cd /root/lvextend-lab

sudo lvextend -L +200M /dev/vg_grow/lv_xfs 2>&1 | tee 07-lvextend.txt || true

sudo vgs -o vg_name,vg_free vg_grow | tee 07-vgs.txt

# If there's no room, lvextend fails — that's the "VG full" lesson
echo "(if 'Insufficient free space', remember Lab 127 — vgextend first)"

# Free 100 MiB and try again
sudo umount /mnt/lv_ext4
sudo e2fsck -fy /dev/vg_grow/lv_ext4 >/dev/null
sudo resize2fs /dev/vg_grow/lv_ext4 50M >/dev/null
sudo lvreduce -L 50M -fy /dev/vg_grow/lv_ext4 >/dev/null
sudo mount /dev/vg_grow/lv_ext4 /mnt/lv_ext4

sudo lvextend -L +100M /dev/vg_grow/lv_xfs | tee 07-lvextend2.txt
sudo xfs_growfs /mnt/lv_xfs | tee 07-xfsgrow.txt
df -hT /mnt/lv_xfs | tee 07-df.txt
```

**Reading it left to right:** XFS is the RHEL default FS. The two-step pattern (`lvextend` then `xfs_growfs MOUNTPOINT`) is the workflow you must know cold for the exam, even though `-r` does both at once.

**The story:** `xfs_growfs` takes a **mountpoint**, not a device. It is online-only — the FS must be mounted.

---

### Task 8 — ext4 safe shrink

```bash
cd /root/lvextend-lab

sudo lvs -o lv_name,lv_size /dev/vg_grow/lv_ext4 | tee 08-before.txt

sudo umount /mnt/lv_ext4
sudo e2fsck -fy /dev/vg_grow/lv_ext4 | tee 08-fsck.txt
sudo resize2fs /dev/vg_grow/lv_ext4 30M | tee 08-resize2fs.txt
sudo lvreduce -L 30M -fy /dev/vg_grow/lv_ext4 | tee 08-lvreduce.txt
sudo mount /dev/vg_grow/lv_ext4 /mnt/lv_ext4

sudo lvs -o lv_name,lv_size /dev/vg_grow/lv_ext4 | tee 08-after.txt
df -hT /mnt/lv_ext4 | tee 08-df.txt
```

**Reading it left to right:** Five strict steps:
1. `umount` — the FS must be offline.
2. `e2fsck -fy` — force a full check (any inconsistency now would cause data loss during shrink).
3. `resize2fs LV NEW_SIZE` — shrink the FS first to the new size.
4. `lvreduce -L NEW_SIZE -fy LV` — only now is it safe to shrink the LV.
5. `mount` — back online.

**The story:** Reverse this order and you destroy the filesystem. Step 3 must precede step 4. **XFS cannot do this at all** — it has no shrink primitive. The XFS answer to "make this smaller" is `xfs_dump | xfs_restore` into a smaller FS, or recreate.

**Expected output:**

```text
  WARNING: Reducing active and open logical volume to 30.00 MiB.
  THIS MAY DESTROY YOUR DATA (filesystem etc.)
  Size of logical volume vg_grow/lv_ext4 changed from 50.00 MiB to 30.00 MiB.
```

---

### Task 9 — Idempotent ensure-size script

```bash
cd /root/lvextend-lab

cat > 09-ensure-size.sh <<'EOF'
#!/usr/bin/env bash
# Usage: ./09-ensure-size.sh VG/LV TARGET_SIZE   (e.g. vg_grow/lv_ext4 500M)
LV="$1"
TARGET="$2"

CURRENT=$(sudo lvs --noheadings --units b -o lv_size "$LV" | xargs | sed 's/B$//')
case "$TARGET" in
  *G|*g) TGT_BYTES=$(( ${TARGET%[Gg]} * 1024 * 1024 * 1024 )) ;;
  *M|*m) TGT_BYTES=$(( ${TARGET%[Mm]} * 1024 * 1024 )) ;;
  *)     TGT_BYTES="$TARGET" ;;
esac

if (( CURRENT == TGT_BYTES )); then
  echo "[$LV] already at $TARGET"
elif (( CURRENT < TGT_BYTES )); then
  sudo lvextend -L "$TARGET" -r "/dev/$LV"
  echo "[$LV] grown to $TARGET"
else
  echo "[$LV] is larger than $TARGET — shrink not automated (run safe-shrink manually)"
fi
EOF
chmod +x 09-ensure-size.sh

./09-ensure-size.sh vg_grow/lv_ext4 250M | tee 09-grow.txt
./09-ensure-size.sh vg_grow/lv_ext4 250M | tee 09-noop.txt
./09-ensure-size.sh vg_grow/lv_ext4 100M | tee 09-shrink-refused.txt
```

**Reading it left to right:** The script reconciles desired-size against current-size:
- equal → no-op
- grow needed → `lvextend -L TARGET -r`
- shrink needed → **refuse** (shrink should be manual and observed)

**The story:** This is the idempotency contract Ansible `lvol` honors. Real automation never shrinks blindly.

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/lvextend-lab

cat > 10-report.txt <<EOF
LV extension report — $(hostname) — $(date -Iseconds)

Final LV sizes:
$(sudo lvs -o lv_name,lv_size,segtype vg_grow)

Filesystem sizes:
$(df -hT /mnt/lv_ext4 /mnt/lv_xfs)

Workflow rehearsed:
  lvextend -L 400M VG/LV          ← absolute
  lvextend -L +100M VG/LV         ← additive
  lvextend -l +100%FREE VG/LV     ← consume free
  lvextend -L +200M -r VG/LV      ← one-shot with --resizefs
  lvextend -L +100M VG/LV ; xfs_growfs MP   ← manual XFS two-step
  e2fsck → resize2fs → lvreduce   ← ext4 safe-shrink

Recommendation:
  - Default: lvextend -L +SIZE -r VG/LV
  - Always umount + e2fsck before shrinking ext4.
  - XFS cannot shrink — provision generously up front.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo umount /mnt/lv_ext4 /mnt/lv_xfs
sudo rmdir  /mnt/lv_ext4 /mnt/lv_xfs

sudo lvremove -fy vg_grow
sudo vgremove -fy vg_grow
sudo pvremove -fy "$LOOP_1" "$LOOP_2" "$LOOP_3" "$LOOP_4"
for n in 1 2 3 4; do
  eval "L=\$LOOP_$n"
  sudo losetup -d "$L"
done
sudo rm -f /var/tmp/lvex-pv-*.img

cd /root
rm -rf /root/lvextend-lab
exit
```

---

## 🔍 Extend Decision Guide

```
"Grow LV by N MiB and grow FS"
  └→ lvextend -L +NM -r VG/LV          ← the canonical form

"Grow LV only (FS step later)"
  └→ lvextend -L +NM VG/LV
     then  resize2fs LV       (ext4)
       or  xfs_growfs MP       (XFS — needs mountpoint)

"Consume all free space"
  └→ lvextend -l +100%FREE -r VG/LV

"Set absolute size"
  └→ lvextend -L NM VG/LV         (no '+' = absolute target)

"Shrink ext4"
  └→ umount → e2fsck -f → resize2fs LV NEW → lvreduce -L NEW LV → mount

"Shrink XFS"
  └→ not supported; dump/restore into smaller FS
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 4-PV VG sandbox
- [ ] 02 Baseline ext4 + XFS LVs
- [ ] 03 Absolute `-L SIZE`
- [ ] 04 Additive `-L +SIZE`
- [ ] 05 Percentage `-l +100%FREE`
- [ ] 06 One-shot `-r`
- [ ] 07 Manual `xfs_growfs`
- [ ] 08 ext4 safe-shrink
- [ ] 09 Idempotent ensure-size
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgot FS resize step | `df` shows old size | `resize2fs` or `xfs_growfs` — or use `-r` |
| `lvreduce` before `resize2fs` | FS corrupted | Always shrink FS FIRST |
| Tried to shrink XFS | "shrink not supported" | XFS cannot shrink — recreate |
| `-l +100%FREE` then can't allocate | Other LVs starved | Plan VG sizing |
| `lvextend -L 500M` (no +) ↗ unexpectedly small | Set to absolute 500 MiB | Use `-L +500M` for additive |
| Forget `--use-policies` on thin pool autoextend | Pool runs out | Configure policy in `/etc/lvm/lvm.conf` |
| `xfs_growfs DEVICE` instead of mountpoint | "must be mounted" | Pass the mountpoint |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize: `lvextend -L +SIZE -r VG/LV`.

**RHCE candidate**
- Ansible: `community.general.lvol: vg=data lv=app size=+500m resizefs=yes`.

**SRE / Platform interview**
- Walk through the FS-fill page → `lvextend -r` resolution loop.

**DevOps**
- cloud-init: `growpart` → `lvextend -l +100%FREE -r` on first boot after EBS expand.

**AI / MLOps**
- Per-epoch dataset growth: cron checks `df`, runs `lvextend -L +500M -r` if > 90% full.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 125 — `lvcreate` | LVs you extend here |
| Lab 127 — `vgextend` | When VG is full, extend it first |
| Lab 129 — `resize2fs`/`xfs_growfs` | Filesystem resize tools |
| Lab 130 — `lvremove` | Counterpart teardown |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
