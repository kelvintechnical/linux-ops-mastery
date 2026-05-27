# Lab: Extend a Volume Group — `vgextend`, `vgreduce`, `pvmove`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** the canonical "I need more space" workflow (`pvcreate NEWDISK` → `vgextend VG NEWDISK` → `lvextend -L +SIZE VG/LV` → `xfs_growfs` or `resize2fs`), `vgextend VG PV [PV ...]` (basic syntax), online extension (no umount, no reboot), `vgextend --restoremissing` (special case when a missing PV has come back), the inverse `vgreduce VG PV` (remove a PV — only safe when the PV holds zero allocated extents) and `vgreduce --removemissing VG` (mark gone-PV unusable, must follow `vgreduce`), `pvmove SRC_PV [DEST_PV]` (live-migrate allocated extents off a PV before reducing — the production pattern for replacing a failing disk), the "before / during / after" `pvs` and `vgs` snapshots, the at-most-one-PV rule for `vgextend` interaction with `--metadatacopies` (rarely changed), pre-flight checks (`pvscan --cache`, `partprobe`, `udevadm settle`) when the new disk just appeared, the SAN/EBS hot-add flow with `echo 1 > /sys/block/sdX/device/rescan`, the AWS-specific `growpart` step when extending the parent partition, the "vg is full" pattern (`vg_free=0` → cannot allocate new LVs even though disks exist), idempotency: how Ansible's `community.general.lvg` reconciles the desired PV list against the actual one, why production never mixes `vgextend` and `vgcreate` in the same play
- **Career arcs covered:** RHCSA (EX200 — "add /dev/vdc1 to vgrhcsa"), RHCE (Ansible `community.general.lvg`), SRE (live storage expansion runbook), DevOps (cloud-init + cloud disk hot-add automation), AI / MLOps (per-rig storage scale-up without downtime)
- **Prerequisite:** Lab 121 (pvcreate), Lab 123 (vgcreate)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox · Task 2 baseline `vgs`/`pvs` · Task 3 hot-add: new PV · Task 4 `vgextend` · Task 5 verify new free space · Task 6 demonstrate LV across new PV · Task 7 `pvmove` extents off a PV · Task 8 `vgreduce` the drained PV · Task 9 `vgreduce --removemissing` simulation · Task 10 capstone + cleanup

---

## Objective

Live-extend a Volume Group with a new disk, prove the new free space is available, then practice the inverse: drain a PV with `pvmove` and remove it with `vgreduce`. By the end you can answer "I just attached EBS volume `/dev/sdd` — extend `vg_data` to use it" without writing it down.

The capstone is: *"Add a new PV to an existing VG, allocate an LV that uses extents from the new PV, then `pvmove` those extents back onto the original PV and `vgreduce` the new PV out — proving live in/out is symmetric."*

> **Lab safety note:** Loopback only. `pvmove` and `vgreduce` are safe on a live VG when used in the order shown.

---

## Concept: The Extend Workflow Is Always the Same

```
   ┌─────────────────────────────────────────────────────────────┐
   │ 1. New disk appears        ← cloud hot-add or new SAN LUN    │
   │       │                                                       │
   │ 2. pvcreate /dev/NEW       ← write LVM label                  │
   │       │                                                       │
   │ 3. vgextend VG /dev/NEW    ← add to pool                      │
   │       │                                                       │
   │ 4. (optional) verify       ← vgs shows new VFree              │
   │       │                                                       │
   │ 5. lvextend -L +SIZE VG/LV ← consume                          │
   │       │                                                       │
   │ 6. xfs_growfs / resize2fs  ← grow FS to match LV              │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** This 6-step pattern is the single most common LVM operation in production. RHCSA tests it directly. SRE runbooks call it "the storage scale-up loop." Every cloud auto-scaler does it.

---

## 📜 Why `vgextend` Exists — The Story

Static-partition systems answered "I need more space" with: backup, repartition, restore, reboot. Total outage: hours. The first commercial LVMs (HP-UX 1988, AIX 1989) introduced `vgextend` specifically to make live extension a one-command operation.

LVM2 on Linux (2002) inherited the verb. Crucially, `vgextend` only updates **metadata** — it does not move any data, does not interrupt any IO. The VG simply grows.

When `vgextend` fails, it is almost always one of these:
1. The disk is not a PV yet (`pvcreate` first).
2. The disk has another VG's metadata on it (`pvremove` + `pvcreate` first).
3. The kernel does not see the disk yet (`pvscan --cache` or `partprobe`).

> **The point of the story:** `vgextend` is a metadata-only operation. It is fast, online, and forgiving.

---

## 👪 The Extend Family

```
Add capacity
├── vgextend VG PV [PV ...]            ← the workhorse
├── vgextend --restoremissing VG PV    ← previously-missing PV came back
└── pvcreate -ffy PV                    ← prep first if needed

Remove capacity
├── pvmove SRC_PV [DEST_PV]            ← drain a PV onto remaining ones
├── vgreduce VG PV                     ← remove an empty PV
├── vgreduce --removemissing VG        ← mark gone-PV unusable
└── vgreduce --removemissing --force VG ← also remove LVs allocated on it

Cloud hot-add prelude
├── echo 1 > /sys/block/sdX/device/rescan
├── partprobe /dev/sdX
├── udevadm settle
└── pvscan --cache
```

---

## 📚 vgextend Reference Table

| Goal | Command |
|---|---|
| Add one new PV | `vgextend vg_data /dev/sdd1` |
| Add multiple at once | `vgextend vg_data /dev/sdd1 /dev/sde1` |
| Restore missing PV | `vgextend --restoremissing vg_data /dev/sdd1` |
| Drain a PV | `pvmove /dev/sdc1` |
| Drain to a specific PV | `pvmove /dev/sdc1 /dev/sdd1` |
| Drain selected LV | `pvmove -n /dev/vg_data/lv_app /dev/sdc1` |
| Remove drained PV | `vgreduce vg_data /dev/sdc1` |
| Remove missing PV | `vgreduce --removemissing vg_data` |
| Cloud rescan | `echo 1 > /sys/block/sdX/device/rescan` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Add /dev/vdc1 to vgrhcsa." This is the answer. |
| **RHCE candidate** | Ansible `community.general.lvg` declares the desired PV list. |
| **SRE / Platform** | Storage scale-up runbook entrypoint. |
| **DevOps** | cloud-init hot-add + `vgextend` automation. |
| **AI / MLOps** | Per-rig live capacity scale-up before training-data growth. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox: VG with 1 PV and one LV

```bash
sudo -i
mkdir -p /root/vgextend-lab && cd /root/vgextend-lab

IMG_OLD=/var/tmp/vge-old.img
truncate -s 1G "$IMG_OLD"
LOOP_OLD=$(sudo losetup --find --show "$IMG_OLD")

IMG_NEW=/var/tmp/vge-new.img
truncate -s 1G "$IMG_NEW"
LOOP_NEW=$(sudo losetup --find --show "$IMG_NEW")

echo "$LOOP_OLD" | tee 01-loop-old.txt
echo "$LOOP_NEW" | tee 01-loop-new.txt

sudo pvcreate "$LOOP_OLD" >/dev/null
sudo vgcreate vg_grow "$LOOP_OLD" >/dev/null
sudo lvcreate -L 500M -n lv_app vg_grow >/dev/null

sudo vgs vg_grow | tee 01-vgs-before.txt
sudo pvs        | tee 01-pvs-before.txt
```

**Reading it left to right:** Two loop devices, one already a PV inside `vg_grow`, the other unused. We will treat `LOOP_NEW` as the hot-added disk.

---

### Task 2 — Baseline `vgs` and `pvs`

```bash
cd /root/vgextend-lab

sudo vgs -o vg_name,pv_count,vg_size,vg_free vg_grow | tee 02-vgs.txt
sudo pvs -o pv_name,vg_name,pv_size,pv_free | tee 02-pvs.txt
```

**Expected output:**

```text
  VG      #PV VSize   VFree
  vg_grow   1   1.00g 524.00m
```

```text
  PV          VG      PSize   PFree
  /dev/loop10 vg_grow   1.00g 524.00m
  /dev/loop11           1.00g 1.00g
```

`LOOP_NEW` shows up in `pvs` with no VG — it is just an LVM label, ready to join.

---

### Task 3 — Hot-add: `pvcreate` on the new disk

```bash
cd /root/vgextend-lab

sudo pvcreate "$LOOP_NEW" | tee 03-pvcreate.txt
sudo pvscan --cache 2>&1 | tee 03-pvscan.txt
sudo blkid "$LOOP_NEW" | tee 03-blkid.txt
```

**Reading it left to right:** On a real cloud host, this is preceded by `echo 1 > /sys/block/sdX/device/rescan` so the kernel sees the new device. On loopback, the loop driver already exposed it.

**Expected output:**

```text
Physical volume "/dev/loop11" successfully created.
/dev/loop11: UUID="..." TYPE="LVM2_member"
```

---

### Task 4 — `vgextend`

```bash
cd /root/vgextend-lab

sudo vgextend vg_grow "$LOOP_NEW" | tee 04-vgextend.txt
sudo vgs vg_grow | tee 04-vgs-after.txt
sudo pvs         | tee 04-pvs-after.txt
```

**Reading it left to right:** Two changes:
- `vgs vg_grow` shows `#PV 2` and `VSize ~2 GiB` (up from 1 GiB).
- `pvs` shows `LOOP_NEW` with `VG=vg_grow`.

**The story:** Total elapsed time on a real system: < 1 second. No IO suspension, no remount. This is what makes LVM the storage substrate of choice for production.

**Expected output:**

```text
Volume group "vg_grow" successfully extended
```

```text
  VG      #PV VSize    VFree
  vg_grow   2   2.00g  1.51g
```

---

### Task 5 — Verify new free space

```bash
cd /root/vgextend-lab

sudo vgs -o vg_name,pv_count,vg_size,vg_free,vg_extent_count,vg_free_count vg_grow | tee 05-vgs.txt
sudo vgdisplay vg_grow | grep -E 'PE Size|Total PE|Alloc PE / Size|Free  PE / Size|Cur PV|Act PV' | tee 05-vgdisplay.txt
```

**Expected output:**

```text
  VG      #PV VSize   VFree   #Ext  #PFree
  vg_grow   2  2.00g  1.51g    510     386
```

---

### Task 6 — Allocate LV that uses the new PV

```bash
cd /root/vgextend-lab

sudo lvcreate -L 800M -n lv_spans vg_grow | tee 06-lvcreate.txt
sudo lvdisplay --maps /dev/vg_grow/lv_spans | sed -n '/--- Segments/,/Open count/p' | head -n 30 | tee 06-maps.txt
sudo pvs | tee 06-pvs.txt
```

**Reading it left to right:** `lv_spans` is 800 MiB — bigger than the free space remaining on `LOOP_OLD`. LVM's default allocator therefore spans the LV across both PVs. `lvdisplay --maps` proves it.

**Expected output (excerpt):**

```text
  --- Segments ---
  Logical extents 0 to 5:
    Type            linear
    Physical volume   /dev/loop10
    Physical extents  131 to 136

  Logical extents 6 to 199:
    Type            linear
    Physical volume   /dev/loop11
    Physical extents  0 to 193
```

---

### Task 7 — `pvmove` extents off the new PV

```bash
cd /root/vgextend-lab

sudo lvremove -fy vg_grow/lv_app
sudo lvcreate -L 400M -n lv_to_move vg_grow "$LOOP_NEW" | tee 07-create-on-new.txt

sudo lvdisplay --maps /dev/vg_grow/lv_to_move | grep -E 'Physical volume' | tee 07-pre-move.txt

sudo pvmove -v "$LOOP_NEW" 2>&1 | tail -n 5 | tee 07-pvmove.txt

sudo lvdisplay --maps /dev/vg_grow/lv_to_move | grep -E 'Physical volume' | tee 07-post-move.txt
```

**Reading it left to right:** `pvmove SRC_PV` migrates **every allocated extent** off `SRC_PV` onto remaining PVs in the same VG. It does this online — the LV stays mounted, applications keep reading and writing, copy progress is reported.

**The story:** This is the production pattern for replacing a failing disk. `pvmove` first (live migrate data away), then `vgreduce` (remove the empty PV), then physically replace the disk.

**Expected output (excerpt):**

```text
/dev/loop11: Moved: 100.00%
```

```text
    Physical volume   /dev/loop10
```

---

### Task 8 — `vgreduce` the drained PV

```bash
cd /root/vgextend-lab

sudo pvs | tee 08-pvs-before.txt
sudo vgreduce vg_grow "$LOOP_NEW" | tee 08-vgreduce.txt
sudo pvs | tee 08-pvs-after.txt
sudo vgs vg_grow | tee 08-vgs.txt
```

**Reading it left to right:** `vgreduce` is the inverse of `vgextend`. It is only safe when the PV holds **zero allocated extents** (`pv_used = 0`). Otherwise LVM refuses unless you pass `--force`.

**The story:** A clean "shrink the VG" requires `pvmove` first. `vgreduce` is the second step.

**Expected output:**

```text
Removed "/dev/loop11" from volume group "vg_grow"
```

---

### Task 9 — `vgreduce --removemissing` simulation

```bash
cd /root/vgextend-lab

# Re-add the new PV so we can simulate it "going missing"
sudo pvcreate "$LOOP_NEW" >/dev/null
sudo vgextend vg_grow "$LOOP_NEW" >/dev/null
sudo lvcreate -L 200M -n lv_doomed vg_grow "$LOOP_NEW" >/dev/null

# Yank the disk
sudo losetup -d "$LOOP_NEW"

sudo pvs 2>&1 | tee 09-pvs-with-missing.txt
sudo vgs vg_grow 2>&1 | tee 09-vgs-with-missing.txt

sudo vgreduce --removemissing --force vg_grow 2>&1 | tee 09-removemissing.txt
sudo pvs 2>&1 | tee 09-pvs-after.txt
sudo vgs vg_grow | tee 09-vgs-after.txt
```

**Reading it left to right:**
- `losetup -d` simulates a yanked disk. `pvs` now shows `WARNING: Couldn't find device with uuid ...` and the VG shows partial flag.
- `vgreduce --removemissing` removes the gone-PV entry. `--force` is required because there is an LV (`lv_doomed`) allocated on it — that LV is removed in the same operation.

**The story:** This is the recovery sequence after a disk physically fails. You will see this in production. The data on the failed disk is **gone**. `vgreduce --removemissing` only fixes the metadata.

**Expected output (excerpt):**

```text
WARNING: Couldn't find device with uuid ...
WARNING: VG vg_grow is missing PV ... (last written to ...)
WARNING: Removing partial LV vg_grow/lv_doomed.
  Logical volume "lv_doomed" successfully removed
  Wrote out consistent volume group vg_grow.
```

```text
  VG      #PV VSize    VFree
  vg_grow   1   1.00g 524.00m
```

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/vgextend-lab

# Re-create LOOP_NEW for the report
truncate -s 1G "$IMG_NEW"
LOOP_NEW=$(sudo losetup --find --show "$IMG_NEW")
sudo pvcreate "$LOOP_NEW" >/dev/null
sudo vgextend vg_grow "$LOOP_NEW" >/dev/null

cat > 10-report.txt <<EOF
VG extension report — $(hostname) — $(date -Iseconds)

Final state:
$(sudo vgs vg_grow)

PVs in vg_grow:
$(sudo pvs --select 'vg_name=vg_grow')

Workflow exercised:
  pvcreate $LOOP_NEW
  vgextend vg_grow $LOOP_NEW       (adds capacity, online)
  lvcreate (spans both PVs)        (consumer of new capacity)
  pvmove   $LOOP_NEW               (live migrate off)
  vgreduce vg_grow $LOOP_NEW       (clean removal)
  vgreduce --removemissing --force (simulated failed disk recovery)

Recommendation:
  - Standard hot-add: pvcreate → vgextend → lvextend → xfs_growfs/resize2fs.
  - Always pvmove BEFORE vgreduce on a healthy disk you are decommissioning.
  - vgreduce --removemissing is for failed-disk metadata cleanup, not normal removal.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo lvremove -fy vg_grow
sudo vgremove -fy vg_grow
sudo pvremove -fy "$LOOP_OLD" "$LOOP_NEW"
sudo losetup -d "$LOOP_OLD"
sudo losetup -d "$LOOP_NEW"
sudo rm -f "$IMG_OLD" "$IMG_NEW"

cd /root
rm -rf /root/vgextend-lab
exit
```

---

## 🔍 Extend Decision Guide

```
"Add capacity to a VG"
  └→ pvcreate NEW → vgextend VG NEW → lvextend → xfs_growfs/resize2fs

"Replace a healthy disk"
  └→ vgextend with replacement → pvmove from OLD to NEW → vgreduce VG OLD

"Recover from a failed disk"
  └→ vgreduce --removemissing --force VG   (data on failed disk is gone)

"PV came back after temporary failure"
  └→ vgextend --restoremissing VG PV

"Cloud hot-add (AWS/Azure)"
  └→ echo 1 > /sys/block/sdX/device/rescan → partprobe → pvcreate → vgextend
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Sandbox: VG with 1 PV
- [ ] 02 Baseline `vgs`/`pvs`
- [ ] 03 `pvcreate` new disk
- [ ] 04 `vgextend`
- [ ] 05 Verify new free space
- [ ] 06 LV spans new PV
- [ ] 07 `pvmove` to drain
- [ ] 08 `vgreduce` clean removal
- [ ] 09 `vgreduce --removemissing` simulated failure
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `vgextend` without `pvcreate` first | "must initialize PV" | `pvcreate` first |
| New disk not visible after attach | `vgextend` says "not found" | `echo 1 > /sys/block/sdX/device/rescan` + `partprobe` |
| `vgreduce` on PV with allocated extents | Refused | `pvmove` first |
| `pvmove` with no free space elsewhere | "insufficient free space" | Extend with more PVs before draining |
| `vgreduce --removemissing` without `--force` | LVs on missing PV block it | Add `--force` (data lost on missing PV) |
| Mixed PV sizes producing uneven striped LVs | Underutilized larger PVs | Use `--type striped` only on equal-size PVs |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize 6-step extend: pvcreate → vgextend → lvextend → xfs_growfs/resize2fs.

**RHCE candidate**
- Ansible: `community.general.lvg: vg=data pvs=[/dev/sdb1,/dev/sdc1] state=present` — module reconciles to add `sdc1` if missing.

**SRE / Platform interview**
- Walk through the `pvmove → vgreduce` disk-replacement runbook end-to-end.

**DevOps**
- cloud-init: declarative `lvm:` block with multi-PV VG.

**AI / MLOps**
- Live scale-up: attach new EBS, run pvcreate+vgextend+lvextend+xfs_growfs in a 10-line script.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 121 — `pvcreate` | Prep step |
| Lab 123 — `vgcreate` | Original VG creation |
| Lab 124 — `vgs`/`vgdisplay` | Verify free space |
| Lab 128 — `lvextend` | Next step (consume the new free) |
| Lab 130 — `vgremove` | Full teardown |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
