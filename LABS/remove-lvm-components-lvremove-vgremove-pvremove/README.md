# Lab: Remove LVM Components — `lvremove`, `vgremove`, `pvremove`, `wipefs`

- **Series:** linux-ops-mastery — RHCSA LVM
- **Subjects covered:** the inverse of the PV → VG → LV stack ("destroy in the opposite direction you built"), the strict ordering: **(1) umount → (2) fstab clean → (3) lvremove → (4) vgremove → (5) pvremove → (6) wipefs**, why each step refuses to skip a level, `lvremove -f /dev/VG/LV` (single LV) and `lvremove -f VG` (every LV in the VG), `vgremove -f VG` (won't remove a VG with LVs unless forced — and even then refuses if any LV is in use), `pvremove -ff DEV` (the second `-f` overrides last-defense checks), `wipefs -a DEV` (nuke all FS/LVM signatures so the disk looks raw again — the bookend to `pvcreate`), the **VG-with-active-LV** case (`vgchange -an VG` first to release LVs), the **snapshot-with-origin** case (snapshots remove cleanly with `lvremove`; merging back to origin is `lvconvert --merge`), the **thin-pool teardown** order (thin LVs → pool → VG), the **safe-decom playbook** (umount → swapoff → sed fstab → lvremove → vgremove → pvremove → wipefs → unplug), undoing accidental removal with `/etc/lvm/archive/VG_NNNNN.vg` + `vgcfgrestore -f FILE VG` (Lab 123 covered the backup; this lab uses the restore for real), distinguishing "pure metadata teardown" (`pvremove` only — disk can be re-pvcreated without `wipefs`) from "complete wipe" (`wipefs -a` — every signature gone), the dry-run flags (`-t`/`--test`) on every LVM verb, the journal of removal events in `/etc/lvm/archive/`
- **Career arcs covered:** RHCSA (EX200 — "remove the volume group"), RHCE (Ansible `state=absent` on each lvm module), SRE (decommission-host runbook), DevOps (CI image-bake teardown), AI / MLOps (per-experiment LV cleanup)
- **Prerequisite:** Labs 121–129
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox (full LVM stack mounted) · Task 2 `umount` and fstab clean · Task 3 `lvremove` one LV · Task 4 `lvremove` all LVs · Task 5 `vgremove` · Task 6 `pvremove` · Task 7 `wipefs -a` · Task 8 thin-pool teardown order · Task 9 oops-recovery with `vgcfgrestore` · Task 10 capstone safe-decom script + cleanup

---

## Objective

Destroy a complete LVM stack — and undo a destructive accident — without leaving zombie metadata, broken fstab lines, or stuck mounts behind. By the end you can walk a host through a clean disk decommission and can recover from "I `vgremove`-d the wrong VG."

The capstone is: *"Decommission a VG containing two ext4 LVs and one thin pool with two thin LVs — and produce a 'safe-decom' script that runs end-to-end without manual intervention, plus demonstrate recovering an accidentally-removed VG via `vgcfgrestore`."*

> **Lab safety note:** Loopback only. The commands here are **destructive on real hardware** in exactly the way they appear here. Read the warnings before running on any host that holds data you want to keep.

---

## Concept: Destroy in Reverse

```
   ┌─────────────────────────────────────────────────────────────┐
   │  Build order:    pvcreate → vgcreate → lvcreate → mkfs → mount│
   │                                                              │
   │  Destroy order:  umount → lvremove → vgremove → pvremove     │
   │                          (+ wipefs at the end to be tidy)    │
   │                                                              │
   │  Each step refuses if the next layer above is still present. │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Each LVM tool guards against "the layer above me is still there." Skip a step and you get a refusal. Force a step out of order (`-ff`) and you risk orphaning metadata that requires manual cleanup to remove.

---

## 📜 Why the Removal Tools Are Strict — The Story

Early LVM2 (2002) shipped removal verbs that were forgiving — you could `pvremove` a PV that was still in a VG, and the VG would silently corrupt. The Red Hat team hardened the tools through the 2000s. By RHEL 6 (2010), every removal verb checked the layer above:

- `pvremove` refuses if PV is in a VG.
- `vgremove` refuses if VG has LVs.
- `lvremove` refuses if LV is open (mounted, swapped, in use by dm-crypt, etc.).

`-f` overrides the friendly prompt. `-ff` (double `-f`) overrides the safety check. **You almost never need `-ff`.** If you do, you are probably about to lose data.

> **The point of the story:** Removal is a contract. Honor the contract by removing in reverse order, and the tools will never argue with you.

---

## 👪 The Remove Family

```
LV layer
├── lvremove -f VG/LV                  ← one LV
├── lvremove -f VG                     ← every LV in the VG
└── lvremove --test VG/LV              ← dry run

VG layer
├── vgremove VG                        ← refuses if LVs present
├── vgremove -f VG                     ← removes LVs too (interactive prompts)
└── vgremove -fy VG                    ← no prompts (exam-style)

PV layer
├── pvremove DEV                       ← removes LVM label
├── pvremove -f DEV                    ← suppress "PV-in-VG" check
├── pvremove -ff DEV                   ← overrides "are you sure?"
└── pvremove -fy DEV [DEV ...]         ← multi-PV non-interactive

Bookend
└── wipefs -a DEV                      ← nuke every filesystem/LVM signature

Recovery
├── ls /etc/lvm/archive/               ← rolling history
└── vgcfgrestore -f FILE VG            ← undo a removal
```

---

## 📚 Remove Reference Table

| Goal | Command |
|---|---|
| One LV | `umount` → `lvremove -fy VG/LV` |
| All LVs in VG | `umount each` → `lvremove -fy VG` |
| VG with no LVs | `vgremove -fy VG` |
| VG with active LVs | `vgchange -an VG` → `lvremove -fy VG` → `vgremove -fy VG` |
| Whole PV | `pvremove -fy DEV` |
| Thin pool | `lvremove` thin LVs first, then pool, then VG |
| Total wipe | `pvremove -fy DEV` → `wipefs -a DEV` |
| Undo accidental `vgremove` | `vgcfgrestore -f /etc/lvm/archive/VG_NNNNN.vg VG` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Remove vg_data and its PVs." This is the answer. |
| **RHCE candidate** | Ansible `state=absent` cascade. |
| **SRE / Platform** | Decom-host runbook is incomplete without these verbs. |
| **DevOps** | CI bake cleanup, snapshot pruning. |
| **AI / MLOps** | Per-experiment LV reset between runs. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Sandbox: full stack mounted

```bash
sudo -i
mkdir -p /root/remove-lab && cd /root/remove-lab

for n in 1 2 3; do
  IMG=/var/tmp/rm-pv-$n.img
  truncate -s 1G "$IMG"
  L=$(sudo losetup --find --show "$IMG")
  eval "LOOP_$n=$L"
done

sudo pvcreate "$LOOP_1" "$LOOP_2" "$LOOP_3" >/dev/null
sudo vgcreate vg_rm "$LOOP_1" "$LOOP_2" "$LOOP_3" >/dev/null

sudo lvcreate -L 200M -n lv_app vg_rm  >/dev/null
sudo lvcreate -L 200M -n lv_logs vg_rm >/dev/null
sudo lvcreate --type thin-pool -L 200M -n tpool vg_rm >/dev/null
sudo lvcreate --thin -V 1G -n lv_thin1 vg_rm/tpool   >/dev/null
sudo lvcreate --thin -V 1G -n lv_thin2 vg_rm/tpool   >/dev/null

sudo mkfs.ext4 -L RM_APP  /dev/vg_rm/lv_app  >/dev/null
sudo mkfs.xfs  -L RM_LOGS /dev/vg_rm/lv_logs >/dev/null

sudo mkdir -p /mnt/rm_app /mnt/rm_logs
sudo mount /dev/vg_rm/lv_app  /mnt/rm_app
sudo mount /dev/vg_rm/lv_logs /mnt/rm_logs

UUID_APP=$(sudo blkid -s UUID -o value /dev/vg_rm/lv_app)
UUID_LOGS=$(sudo blkid -s UUID -o value /dev/vg_rm/lv_logs)
echo "UUID=$UUID_APP  /mnt/rm_app  ext4 defaults 0 2"   | sudo tee -a /etc/fstab
echo "UUID=$UUID_LOGS /mnt/rm_logs xfs  defaults 0 0"   | sudo tee -a /etc/fstab

sudo lvs vg_rm | tee 01-lvs.txt
df -hT /mnt/rm_app /mnt/rm_logs | tee 01-df.txt
```

---

### Task 2 — `umount` + fstab clean

```bash
cd /root/remove-lab

sudo umount /mnt/rm_app
sudo umount /mnt/rm_logs

sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
sudo sed -i "\|UUID=$UUID_APP|d"  /etc/fstab
sudo sed -i "\|UUID=$UUID_LOGS|d" /etc/fstab

grep -E "$UUID_APP|$UUID_LOGS" /etc/fstab > 02-fstab-check.txt
[[ ! -s 02-fstab-check.txt ]] && echo "fstab clean" | tee -a 02-fstab-check.txt

sudo rmdir /mnt/rm_app /mnt/rm_logs
```

**Reading it left to right:** This is the **first step** of any decom: detach the FS from the mount point, then remove the fstab entry so the host won't try to remount on next boot. Skip this and `lvremove` will refuse with "logical volume in use."

---

### Task 3 — `lvremove` a single LV

```bash
cd /root/remove-lab

sudo lvs vg_rm | tee 03-lvs-before.txt
sudo lvremove -fy /dev/vg_rm/lv_app | tee 03-lvremove-one.txt
sudo lvs vg_rm | tee 03-lvs-after.txt
```

**Reading it left to right:** `lvremove -fy VG/LV` removes one LV non-interactively. Refuses if the LV is mounted (Task 2 unmounted it).

**Expected output:**

```text
Logical volume "lv_app" successfully removed
```

---

### Task 4 — `lvremove` every LV in the VG

```bash
cd /root/remove-lab

sudo lvremove -fy vg_rm | tee 04-lvremove-all.txt
sudo lvs vg_rm 2>&1 | tee 04-lvs-empty.txt
```

**Reading it left to right:** `lvremove -fy VG` (no LV name) removes **all** LVs in the VG in dependency order — thin LVs before their pool, snapshots before their origin.

**Expected output:**

```text
Logical volume "lv_logs" successfully removed
Logical volume "lv_thin1" successfully removed
Logical volume "lv_thin2" successfully removed
Logical volume "tpool" successfully removed
```

---

### Task 5 — `vgremove`

```bash
cd /root/remove-lab

sudo vgremove -fy vg_rm | tee 05-vgremove.txt
sudo vgs 2>&1 | grep -E 'vg_rm|^$' | tee 05-vgs-after.txt
sudo pvs | tee 05-pvs-after.txt
```

**Reading it left to right:** `vgremove -fy` removes the VG. PVs revert to "no VG" state but **still have LVM labels** (they remain `LVM2_member` until `pvremove`).

**Expected output:**

```text
Volume group "vg_rm" successfully removed
```

```text
PV          VG  Fmt  Attr PSize    PFree
/dev/loop10     lvm2 ---   1.00g   1.00g
/dev/loop11     lvm2 ---   1.00g   1.00g
/dev/loop12     lvm2 ---   1.00g   1.00g
```

---

### Task 6 — `pvremove`

```bash
cd /root/remove-lab

sudo pvremove -fy "$LOOP_1" "$LOOP_2" "$LOOP_3" | tee 06-pvremove.txt
sudo pvs | tee 06-pvs-after.txt
sudo blkid "$LOOP_1" 2>&1 | tee 06-blkid.txt
```

**Reading it left to right:** `pvremove` erases the **LVM label** at sector 1. After this, `blkid` reports the disk has no recognized signature (or whatever signature pre-existed if you `wipefs`-ed it differently).

**Expected output:**

```text
Labels on physical volume "/dev/loop10" successfully wiped.
Labels on physical volume "/dev/loop11" successfully wiped.
Labels on physical volume "/dev/loop12" successfully wiped.
```

---

### Task 7 — `wipefs -a` final bookend

```bash
cd /root/remove-lab

sudo wipefs -a "$LOOP_1" "$LOOP_2" "$LOOP_3" 2>&1 | tee 07-wipefs.txt
sudo blkid "$LOOP_1" 2>&1 | tee 07-blkid.txt
lsblk "$LOOP_1" "$LOOP_2" "$LOOP_3" | tee 07-lsblk.txt
```

**Reading it left to right:** `wipefs -a` clears any remaining FS or LVM signatures the kernel could find. After this the disk is "fresh from the factory" from the OS's point of view.

**The story:** `pvremove` alone removes the LVM label only. `wipefs -a` removes **all** signatures — useful when the disk previously held ext4 metadata that `pvremove` left untouched, and which would confuse a future `pvcreate` ("partition table found").

---

### Task 8 — Thin-pool teardown order

```bash
cd /root/remove-lab

# Rebuild a thin pool for the demo
sudo pvcreate "$LOOP_1" "$LOOP_2" "$LOOP_3" >/dev/null
sudo vgcreate vg_th "$LOOP_1" >/dev/null
sudo lvcreate --type thin-pool -L 200M -n tp vg_th >/dev/null
sudo lvcreate --thin -V 1G -n t1 vg_th/tp >/dev/null
sudo lvcreate --thin -V 1G -n t2 vg_th/tp >/dev/null
sudo lvcreate -s -L 50M -n t1_snap vg_th/t1 >/dev/null

sudo lvs vg_th | tee 08-before.txt

# WRONG order — pool refuses
set +e
sudo lvremove -fy vg_th/tp 2>&1 | tee 08-wrong-order.txt
set -e

# RIGHT order — children first
sudo lvremove -fy vg_th/t1_snap vg_th/t1 vg_th/t2 | tee 08-children.txt
sudo lvremove -fy vg_th/tp | tee 08-pool.txt
sudo lvs vg_th 2>&1 | tee 08-empty.txt

sudo vgremove -fy vg_th
sudo pvremove -fy "$LOOP_1" "$LOOP_2" "$LOOP_3"
```

**Reading it left to right:** A thin pool **cannot** be removed while thin LVs depend on it. The order is: snapshots → thin LVs → pool → VG → PVs.

**The story:** `lvremove -fy VG` (Task 4) figures out the right order automatically. When you target specific LVs, you must do the ordering yourself.

**Expected output (wrong-order error):**

```text
Failed to remove pool tp: pool has used volumes
```

---

### Task 9 — Oops-recovery with `vgcfgrestore`

```bash
cd /root/remove-lab

# Rebuild a VG so we can pretend to mess it up
sudo pvcreate "$LOOP_1" "$LOOP_2" >/dev/null
sudo vgcreate vg_oops "$LOOP_1" "$LOOP_2" >/dev/null
sudo lvcreate -L 200M -n lv_important vg_oops >/dev/null
sudo mkfs.ext4 -L OOPS /dev/vg_oops/lv_important >/dev/null
sudo mkdir -p /mnt/oops
sudo mount /dev/vg_oops/lv_important /mnt/oops
sudo bash -c 'echo "irreplaceable data" > /mnt/oops/keep.txt'
sudo umount /mnt/oops
sudo rmdir /mnt/oops

# Capture pre-disaster archive snapshot
sudo vgcfgbackup vg_oops >/dev/null
LATEST_ARCHIVE=$(sudo ls -1t /etc/lvm/archive/vg_oops_* | head -n 1)
echo "archive snapshot at: $LATEST_ARCHIVE" | tee 09-archive.txt

# Oops!
sudo vgremove -fy vg_oops | tee 09-oops.txt
sudo vgs vg_oops 2>&1 | tee 09-gone.txt

# Recover
sudo vgcfgrestore -f "$LATEST_ARCHIVE" vg_oops 2>&1 | tee 09-restore.txt
sudo vgchange -ay vg_oops 2>&1 | tee 09-activate.txt
sudo lvs vg_oops | tee 09-lvs.txt

sudo mkdir -p /mnt/oops
sudo mount /dev/vg_oops/lv_important /mnt/oops
cat /mnt/oops/keep.txt | tee 09-data.txt
sudo umount /mnt/oops
sudo rmdir /mnt/oops
```

**Reading it left to right:** `/etc/lvm/archive/VG_NNNNN.vg` contains a **text** snapshot of VG metadata taken before every destructive operation. `vgcfgrestore -f FILE VG` rewrites the PV headers from that text. As long as the PVs still exist (you did not `pvremove`), recovery is straightforward.

**The story:** This is the single most under-known LVM feature. If you only learn one thing from this lab, learn it.

**Expected output:**

```text
Volume group "vg_oops" successfully removed
```

```text
Restored volume group vg_oops.
1 logical volume(s) in volume group "vg_oops" now active
irreplaceable data
```

---

### Task 10 — Capstone: safe-decom script + cleanup

```bash
cd /root/remove-lab

# Final teardown of the recovery VG
sudo lvremove -fy vg_oops
sudo vgremove -fy vg_oops
sudo pvremove -fy "$LOOP_1" "$LOOP_2"

cat > 10-safe-decom.sh <<'EOF'
#!/usr/bin/env bash
# Usage: ./safe-decom.sh VG_NAME
set -euo pipefail
VG="$1"

echo "[$VG] safe-decom starting" >&2

# 1. umount every mounted FS on the VG's LVs
for lv_path in $(sudo lvs --noheadings -o lv_path "$VG" 2>/dev/null); do
  MP=$(findmnt -no TARGET "$lv_path" || true)
  if [[ -n "$MP" ]]; then
    echo "  umount $MP" >&2
    sudo umount "$MP"
    sudo sed -i "\|$lv_path|d;\|$MP|d" /etc/fstab
  fi
done

# 2. deactivate the VG (releases any latent holds)
sudo vgchange -an "$VG"

# 3. remove every LV
sudo lvremove -fy "$VG"

# 4. find the PVs for this VG BEFORE we vgremove
PVS=$(sudo pvs --noheadings -o pv_name --select "vg_name=$VG" | xargs)

# 5. take a metadata backup we can restore from if needed
sudo vgcfgbackup "$VG" >/dev/null || true

# 6. remove the VG
sudo vgremove -fy "$VG"

# 7. pvremove + wipefs each PV
for pv in $PVS; do
  sudo pvremove -fy "$pv"
  sudo wipefs -a "$pv"
done

echo "[$VG] safe-decom complete" >&2
EOF
chmod +x 10-safe-decom.sh

# Demonstrate it
sudo pvcreate "$LOOP_1" "$LOOP_2" "$LOOP_3" >/dev/null
sudo vgcreate vg_demo "$LOOP_1" "$LOOP_2" "$LOOP_3" >/dev/null
sudo lvcreate -L 200M -n lv_one vg_demo >/dev/null
sudo mkfs.ext4 -L DEMO /dev/vg_demo/lv_one >/dev/null
sudo mkdir -p /mnt/demo
sudo mount /dev/vg_demo/lv_one /mnt/demo
UUID=$(sudo blkid -s UUID -o value /dev/vg_demo/lv_one)
echo "UUID=$UUID /mnt/demo ext4 defaults 0 2" | sudo tee -a /etc/fstab

./10-safe-decom.sh vg_demo 2>&1 | tee 10-run.txt

sudo pvs | tee 10-pvs.txt
sudo vgs | tee 10-vgs.txt
sudo rmdir /mnt/demo 2>/dev/null || true

cat > 10-report.txt <<EOF
LVM removal report — $(hostname) — $(date -Iseconds)

The strict removal order rehearsed:
  1. umount (release the FS)
  2. fstab clean (no remount on boot)
  3. lvremove (drop LVs)
  4. vgremove (drop the VG)
  5. pvremove (clear LVM label)
  6. wipefs -a (clear all signatures)

Production safety net:
  - /etc/lvm/archive/VG_NNNNN.vg + vgcfgrestore can undo accidental vgremove.
  - Always vgcfgbackup before destructive operations.
  - Thin pools: remove dependent LVs (and snapshots) before the pool.
  - "Force" flags (-ff, -fy) are convenience, not protection — read the prompts.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$LOOP_1" "$LOOP_2" "$LOOP_3"
sudo rm -f /var/tmp/rm-pv-*.img

cd /root
rm -rf /root/remove-lab
exit
```

---

## 🔍 Remove Decision Guide

```
"Drop one LV"
  └→ umount → sed fstab → lvremove -fy VG/LV

"Drop all LVs in a VG"
  └→ vgchange -an VG → lvremove -fy VG

"Drop the whole VG and disks"
  └→ umount/swapoff → sed fstab → lvremove → vgremove → pvremove → wipefs

"Recover from accidental vgremove"
  └→ ls -1t /etc/lvm/archive/VG_*  → vgcfgrestore -f FILE VG → vgchange -ay VG

"Thin pool teardown"
  └→ snapshots → thin LVs → pool → VG
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Sandbox (full LVM stack mounted)
- [ ] 02 `umount` + fstab clean
- [ ] 03 `lvremove` single LV
- [ ] 04 `lvremove` all in VG
- [ ] 05 `vgremove`
- [ ] 06 `pvremove`
- [ ] 07 `wipefs -a`
- [ ] 08 Thin-pool teardown order
- [ ] 09 `vgcfgrestore` recovery
- [ ] 10 Safe-decom script + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `lvremove` while mounted | "LV in use" | `umount` first |
| Forgot fstab cleanup | Next reboot fails (`mount -a` errors) | `sed -i` the entry out |
| `pvremove` while in VG | Refused | `vgremove` first, or `pvremove -f` (knowingly) |
| Thin pool removed before thin LVs | Refused | Remove children first |
| `vgremove` without backup → wrong VG | Data gone | `vgcfgrestore` from `/etc/lvm/archive/` |
| `wipefs -a` on wrong device | Disk wiped | Quadruple-check the device path before running |
| Skipping `wipefs` after `pvremove` | Old FS signature confuses future tools | Run `wipefs -a` on any disk you intend to repurpose |
| Removing root VG remotely | Host unbootable | Never decom the root VG remotely |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Drill: `umount → lvremove -fy → vgremove -fy → pvremove -fy → wipefs -a`.

**RHCE candidate**
- Ansible: cascade `state=absent` on `community.general.lvol` then `lvg` then `lvol` then `parted`.

**SRE / Platform interview**
- Walk through the decom-host runbook end-to-end. Mention `vgcfgrestore`.

**DevOps**
- CI image-bake cleanup script (this lab's Task 10 is the template).

**AI / MLOps**
- Per-experiment LV reset: `lvremove -fy VG/experiment_$ID` between training runs.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 121 — `pvcreate` | Build counterpart of `pvremove` |
| Lab 123 — `vgcreate` | Build counterpart of `vgremove` |
| Lab 125 — `lvcreate` | Build counterpart of `lvremove` |
| Lab 127 — `vgextend`/`vgreduce` | Mid-life modifications |
| Lab 133 — fstab cleanup | Step 2 of every decom |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
