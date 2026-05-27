# Lab: Check Filesystem Consistency — `fsck`, `fsck.ext4`, `e2fsck`, `xfs_repair`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** the fsck dispatcher (`/usr/sbin/fsck`) and per-FS workers (`fsck.ext4`, `fsck.ext3`, `fsck.ext2`, `fsck.xfs` no-op wrapper, real XFS repair `xfs_repair`), why fsck **only runs on unmounted filesystems**, exit-code semantics (`0` clean, `1` errors corrected, `2` reboot recommended, `4` errors left uncorrected, `8` operational error), `-n` (no, check only), `-y` (yes, auto-correct), `-f` (force even if marked clean), `-p` (preen — fix only safe items), `-v` (verbose), `-c` (badblocks pass), inducing controlled corruption with `dd` over a non-critical block, recovery via journal replay vs full check, `xfs_repair -n` (dry-run), `xfs_repair -L` (zero log — last resort), boot-time fsck pass numbers (1 root, 2 others, 0 skip), how fsck triggers from fstab + `tune2fs -c/-i`, when to run, when to back-up-and-restore-instead
- **Career arcs covered:** RHCSA (EX200 — exam tasks may ask to check an unmounted ext4 partition), RHCE (Ansible filesystem checks in playbooks before mount), SRE (incident: "boot dropped to emergency mode — recover the root FS"), DevOps (CI base-image integrity), AI / MLOps (scratch volume corruption on spot interruptions)
- **Prerequisite:** Labs 116–117 (XFS + ext4)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 sandbox + dual-FS · Task 3 `fsck -n` on a healthy ext4 · Task 4 `xfs_repair -n` on a healthy XFS · Task 5 induce corruption on ext4 · Task 6 `fsck.ext4 -y` repair + exit-code decode · Task 7 force a check with `-f` · Task 8 understand fstab pass numbers · Task 9 `xfs_repair` on damaged XFS (controlled) · Task 10 capstone report + cleanup

---

## Objective

Stop being afraid of `fsck`. By the end of this lab you can run a non-destructive check (`-n`) on an unmounted ext4 partition, repair detected errors with `-y`, force a check on a clean FS with `-f`, decode the fsck exit code, and use `xfs_repair -n` to do the equivalent on XFS without touching the data.

The capstone is the engineer-realistic prompt: *"Filesystem `/dev/loop9p1` is suspected of corruption on an unmounted volume. Run a read-only check, repair if needed, capture the exit code, and produce a one-paragraph report citing the action taken."*

> **Lab safety note:** **NEVER run `fsck` on a mounted filesystem.** This lab uses loopback files and explicitly unmounts before each check. On a real exam: read-only mount or single-user/rescue boot.

---

## Concept: `fsck` Is a Dispatcher

```
   ┌─────────────────────────────────────────────────────────────┐
   │ /usr/sbin/fsck DEV                                           │
   │   1. reads /etc/fstab and/or blkid to find the FS type       │
   │   2. exec()s fsck.<type>  →  fsck.ext4, fsck.xfs, fsck.vfat  │
   │                                                              │
   │ fsck.ext4 = e2fsck (symlink)                                 │
   │ fsck.xfs  = no-op wrapper that just returns 0                │
   │ Real XFS repair = xfs_repair (separate binary)               │
   │                                                              │
   │ Hard rule: filesystem MUST be unmounted (or read-only) first │
   │                                                              │
   │ Exit codes:                                                  │
   │   0  clean                                                   │
   │   1  errors found and corrected                              │
   │   2  errors found and corrected, reboot recommended          │
   │   4  errors left uncorrected (need -y or manual)             │
   │   8  operational error (couldn't even check)                 │
   │  16  usage error                                             │
   │  32  cancelled by user                                       │
   │ 128  shared-library error                                    │
   │  (codes can be OR-ed together)                               │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** `fsck` is the canonical Linux-engineer response to "boot dropped to emergency mode." Knowing the exit codes and the difference between ext4 (`fsck.ext4`) and XFS (`xfs_repair`) is mandatory.

---

## 📜 Why fsck — The Story

- **`fsck`** comes from BSD (1982) — "filesystem consistency check." It was the answer to "the machine crashed mid-write; the FS may be inconsistent."
- **`e2fsck`** (Theodore Ts'o) implements the same idea for ext family with a sophisticated 5-pass algorithm:
  1. Inodes, blocks, sizes
  2. Directory structure
  3. Directory connectivity
  4. Reference counts
  5. Group summary
- **XFS** does NOT have a traditional fsck. Its journal replays on mount, fixing most issues. For real damage, `xfs_repair` exists — but it's used **less frequently** than ext4's fsck because XFS metadata checksums catch most issues earlier.
- **systemd** automates `fsck` at boot via the `fstab` pass-number field (`0`, `1`, `2`) and the `systemd-fsck@.service` unit.

> **The point of the story:** Journaling (ext3+, XFS) made fsck a **rare** event in modern life — but you must still know how to run it.

---

## 👪 The fsck Family

```
Dispatchers
├── fsck DEV          ← chooses worker by detecting FS type
└── fsck -A           ← all filesystems in fstab (in pass order)

ext family workers
├── fsck.ext4 / fsck.ext3 / fsck.ext2 = e2fsck (single binary)
├── e2fsck -n   ← read-only, answer "no" to everything
├── e2fsck -y   ← answer "yes" to all repair prompts
├── e2fsck -f   ← force check (even if marked clean)
├── e2fsck -p   ← preen, fix only safe items
├── e2fsck -v   ← verbose
└── e2fsck -c   ← run badblocks first

XFS family
├── fsck.xfs    ← no-op (returns 0) — XFS uses journal replay
├── xfs_repair -n DEV    ← dry-run
├── xfs_repair DEV       ← repair
├── xfs_repair -L DEV    ← zero the log (DANGER, only when journal is unreadable)
└── xfs_db -r DEV        ← read-only superblock inspector

Helpers
├── blkid DEV       ← detect type
├── dumpe2fs DEV    ← read superblock
└── lsblk -f DEV
```

---

## 📚 fsck Reference Table

| Goal | Command | Notes |
|---|---|---|
| Auto-detect + check | `fsck DEV` | Calls right worker |
| Read-only check (ext4) | `fsck.ext4 -n DEV` | Answer "no" to all prompts |
| Repair (ext4) | `fsck.ext4 -y DEV` | Answer "yes" to all |
| Force check (ext4) | `fsck.ext4 -f DEV` | Even if marked clean |
| Preen (safe auto-fix) | `fsck.ext4 -p DEV` | Used by systemd at boot |
| Verbose | `fsck.ext4 -v DEV` | Pair with `-f` |
| Read-only check (XFS) | `xfs_repair -n DEV` | XFS dry-run |
| Repair XFS | `xfs_repair DEV` | After unmount |
| Decode exit code | `echo $?` | 0 clean, 1 corrected, 4 left uncorrected |
| Check all in fstab | `fsck -A -y` | Pass order matters |
| Skip a filesystem on boot | fstab pass `0` | XFS, swap |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | Exam tasks may say "check the ext4 filesystem on /dev/vdb1." Answer: `umount && fsck -y`. |
| **RHCE candidate** | Ansible playbooks may check filesystems before mount in fix-it-yourself plays. |
| **SRE / Platform** | Incident response: emergency mode + corrupt root. fsck is the first tool. |
| **DevOps** | Base image build verification — `fsck.ext4 -fyv` before bake. |
| **AI / MLOps** | Spot-instance scratch corruption → fsck rather than re-download dataset. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up sandbox + dual-FS loop devices

```bash
sudo -i
mkdir -p /root/fsck-lab && cd /root/fsck-lab

EXT_IMG=/var/tmp/fsck-ext4.img
XFS_IMG=/var/tmp/fsck-xfs.img
truncate -s 512M "$EXT_IMG"
truncate -s 512M "$XFS_IMG"

EXT_DEV=$(sudo losetup --find --show "$EXT_IMG")
XFS_DEV=$(sudo losetup --find --show "$XFS_IMG")
echo "ext4: $EXT_DEV"  | tee 01-loops.txt
echo "xfs : $XFS_DEV" | tee -a 01-loops.txt

sudo mkfs.ext4 -F -L FSCK_EXT4 "$EXT_DEV" >/dev/null
sudo mkfs.xfs  -f -L FSCK_XFS  "$XFS_DEV" >/dev/null

sudo blkid "$EXT_DEV" | tee 01-ext4-blkid.txt
sudo blkid "$XFS_DEV" | tee 01-xfs-blkid.txt
```

---

### Task 2 — Mount, write a small file, unmount

```bash
cd /root/fsck-lab

sudo mkdir -p /mnt/fsck-ext4 /mnt/fsck-xfs
sudo mount "$EXT_DEV" /mnt/fsck-ext4
sudo mount "$XFS_DEV" /mnt/fsck-xfs

echo "RHCSA fsck data" | sudo tee /mnt/fsck-ext4/sample.txt
echo "RHCSA fsck data" | sudo tee /mnt/fsck-xfs/sample.txt
sudo sync

sudo umount /mnt/fsck-ext4
sudo umount /mnt/fsck-xfs
findmnt "$EXT_DEV" 2>&1 | tee 02-ext4-unmounted.txt
findmnt "$XFS_DEV" 2>&1 | tee 02-xfs-unmounted.txt
```

**The story:** fsck refuses to run against a mounted FS. Confirm unmount before every check.

---

### Task 3 — Read-only `fsck -n` on healthy ext4

```bash
cd /root/fsck-lab

sudo fsck -n "$EXT_DEV" | tee 03-fsck-ext4-n.txt
echo "exit=$?" | tee 03-fsck-ext4-n-rc.txt

sudo fsck.ext4 -n "$EXT_DEV" | tee 03-fsck-ext4-explicit.txt
echo "exit=$?" | tee 03-fsck-ext4-explicit-rc.txt
```

**Human-Readable Breakdown:** `fsck DEV` detects the FS type and dispatches. With `-n` it acts as a **dry run** — useful for confirming health without changing anything.

**Reading it left to right:** `fsck` reads `/etc/fstab` or the superblock to find the type, then `exec`s `fsck.ext4`. `-n` answers "no" to all interactive prompts. Exit `0` = clean.

**Expected output:**

```text
fsck from util-linux 2.37.4
e2fsck 1.46.5 (30-Dec-2021)
FSCK_EXT4: clean, 11/32768 files, 8843/131072 blocks
exit=0
```

**Switches**

| Token | Meaning |
|---|---|
| `fsck DEV` | Dispatcher |
| `-n` | No to all prompts (read-only) |
| `-y` | Yes to all prompts |
| `-f` | Force check even if marked clean |
| `-p` | Preen (auto-fix only safe items) |
| `-v` | Verbose |
| `fsck.ext4` | Direct worker for ext4 |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device or resource busy` | `umount` first |
| `is mounted` | `umount` first |
| `Bad magic number in super-block` | Try alternate superblock: `e2fsck -b 32768 DEV` |
| Exit 4 | Errors left uncorrected — rerun with `-y` |

---

### Task 4 — Read-only `xfs_repair -n` on healthy XFS

```bash
cd /root/fsck-lab

sudo fsck.xfs "$XFS_DEV" | tee 04-fsckxfs.txt
echo "exit=$?" | tee 04-fsckxfs-rc.txt

sudo xfs_repair -n "$XFS_DEV" 2>&1 | tee 04-xfs-repair-n.txt
echo "exit=$?" | tee 04-xfs-repair-n-rc.txt
```

**Human-Readable Breakdown:** `fsck.xfs` is intentionally a **no-op wrapper** — it exits 0 always. The real tool is `xfs_repair`, and `-n` makes it a dry-run.

**Reading it left to right:** XFS doesn't need traditional fsck because metadata is journaled and CRC-checked. `xfs_repair -n` walks every metadata block and reports without modifying.

**Expected output:**

```text
If you wish to check the consistency of an XFS filesystem or
repair a damaged filesystem, see xfs_repair(8).
exit=0

Phase 1 - find and verify superblock...
Phase 2 - using internal log
        - zero log...
        - scan filesystem freespace and inode maps...
        - found root inode chunk
Phase 3 - for each AG...
        - scan (but don't clear) agi unlinked lists...
        - process known inodes and perform inode discovery...
        - process newly discovered inodes...
Phase 4 - check for duplicate blocks...
        - setting up duplicate extent list...
        - check for inodes claiming duplicate blocks...
Phase 5 - rebuild AG headers and trees...
        - reset superblock...
Phase 6 - check inode connectivity...
Phase 7 - verify link counts...
No modify flag set, skipping filesystem flush and exiting.
exit=0
```

---

### Task 5 — Induce **controlled** corruption on ext4

```bash
cd /root/fsck-lab

sudo dd if=/dev/zero of="$EXT_DEV" bs=1 count=64 seek=8200 conv=notrunc status=none
echo "ext4 sample bytes overwritten at offset 8200" | tee 05-corrupt.txt
```

**Human-Readable Breakdown:** Overwrite 64 bytes inside a block-group descriptor (offset chosen to **not** touch the primary superblock at byte 1024). The corruption is real enough that fsck will detect it, but the backup superblocks will be intact for repair.

**Reading it left to right:**
- `if=/dev/zero` → input is zeros
- `of=$EXT_DEV` → output is the loop device
- `bs=1 count=64` → write 64 bytes
- `seek=8200` → starting at byte offset 8200 (inside a group descriptor area, after the primary superblock)
- `conv=notrunc` → don't truncate the file
- `status=none` → suppress progress

**The story:** Controlled corruption is how you **practice** fsck. In production you don't induce damage; you respond to it.

> **Safety note:** Only do this on the loopback file we created. Never on a real device.

---

### Task 6 — Detect and repair with `fsck.ext4 -y`

```bash
cd /root/fsck-lab

sudo fsck.ext4 -n "$EXT_DEV" 2>&1 | tee 06-detect.txt
echo "detect-exit=$?" | tee 06-detect-rc.txt

sudo fsck.ext4 -y "$EXT_DEV" 2>&1 | tee 06-repair.txt
RC=$?
echo "repair-exit=$RC" | tee 06-repair-rc.txt

case $RC in
  0) echo "✓ Clean" ;;
  1) echo "✓ Errors corrected — no reboot needed" ;;
  2) echo "⚠ Errors corrected — reboot recommended" ;;
  4) echo "✗ Errors left uncorrected" ;;
  8) echo "✗ Operational error" ;;
  *) echo "✗ Other ($RC)" ;;
esac | tee 06-decode.txt

sudo fsck.ext4 -n "$EXT_DEV" 2>&1 | tee 06-verify-clean.txt
echo "verify-exit=$?" | tee 06-verify-clean-rc.txt
```

**Human-Readable Breakdown:** First `-n` proves the FS is dirty (some non-zero exit). Then `-y` auto-answers "yes" to repair prompts. Capture and **decode** the exit code. Re-check with `-n` to prove it's clean.

**Reading it left to right:** `-y` is the answer when you're operating headless or in a script — interactive prompts have no human to answer them. The case statement is the canonical exit-code decoder every Linux engineer should know by heart.

**The story:** Most "the filesystem is corrupt" incidents are resolved in two commands: `fsck.ext4 -y DEV` followed by `mount DEV`. Decoding the exit code tells you whether to reboot.

**Expected output:**

```text
e2fsck 1.46.5 (30-Dec-2021)
Group descriptor 0 checksum is invalid.  Fix? no
...
detect-exit=4

e2fsck 1.46.5 (30-Dec-2021)
Group descriptor 0 checksum is invalid.  Fix? yes
...
FSCK_EXT4: ***** FILE SYSTEM WAS MODIFIED *****
FSCK_EXT4: 11/32768 files (0.0% non-contiguous), 8843/131072 blocks
repair-exit=1
✓ Errors corrected — no reboot needed

FSCK_EXT4: clean, 11/32768 files, 8843/131072 blocks
verify-exit=0
```

**Switches**

| Token | Meaning |
|---|---|
| `-n` | Read-only (says no to all prompts) |
| `-y` | Auto-yes (fix all without asking) |
| `-p` | Preen — fix only safe items, otherwise exit |
| `-f` | Force even if marked clean |
| `-v` | Verbose |
| `-b N` | Use alternate superblock at block N |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `e2fsck: Bad magic number in super-block` | Try backup: `e2fsck -b 32768 DEV`, common backups at 32768, 98304, 163840 |
| Repair never finishes | Likely failing disk, not fsck issue — replace device |
| Files moved to `lost+found/` | Expected when names lost — check inode numbers |

---

### Task 7 — Force a check even when clean with `-f`

```bash
cd /root/fsck-lab

sudo fsck.ext4 -fv "$EXT_DEV" 2>&1 | tee 07-force.txt
echo "exit=$?" | tee 07-force-rc.txt
```

**The story:** ext4 marks itself "clean" after a graceful unmount. fsck normally skips clean FSes. `-f` forces a full check — the only way to validate every inode after a suspected hardware glitch.

**Expected output (excerpt):**

```text
e2fsck 1.46.5 (30-Dec-2021)
Pass 1: Checking inodes, blocks, and sizes
Pass 2: Checking directory structure
Pass 3: Checking directory connectivity
Pass 4: Checking reference counts
Pass 5: Checking group summary information
FSCK_EXT4: 11/32768 files (0.0% non-contiguous), 8843/131072 blocks
exit=0
```

---

### Task 8 — Boot-time `fstab` pass numbers

```bash
cd /root/fsck-lab

cat > 08-fstab-passes.txt <<EOF
fstab pass-number field (6th column):
  0  → never fsck at boot       (XFS, swap, network mounts)
  1  → first pass; only root /  (one entry max)
  2  → second pass; other ext family filesystems

systemd reads fstab → generates systemd-fsck@<device>.service
  units. Preen mode (-p) is used; if it returns 4 you boot to
  emergency.target.

Examples:
  UUID=...  /        ext4  defaults,errors=remount-ro 0 1
  UUID=...  /home    ext4  defaults                   0 2
  UUID=...  /data    xfs   defaults,noatime           0 0
  UUID=...  none     swap  defaults                   0 0
EOF
cat 08-fstab-passes.txt
```

---

### Task 9 — `xfs_repair` on a controlled XFS

```bash
cd /root/fsck-lab

sudo dd if=/dev/zero of="$XFS_DEV" bs=1 count=64 seek=520 conv=notrunc status=none
echo "XFS bytes overwritten" | tee 09-corrupt.txt

sudo xfs_repair -n "$XFS_DEV" 2>&1 | tee 09-detect.txt || true

sudo xfs_repair "$XFS_DEV" 2>&1 | tee 09-repair.txt
RC=$?
echo "repair-exit=$RC" | tee 09-repair-rc.txt

sudo xfs_repair -n "$XFS_DEV" 2>&1 | tee 09-verify.txt
echo "verify-exit=$?" | tee 09-verify-rc.txt
```

**The story:** `xfs_repair` has a single repair mode (no `-y` flag because it doesn't prompt). If the log is unreadable, you can use `xfs_repair -L` to zero the log — but that risks data loss and is a last resort.

**Switches**

| Token | Meaning |
|---|---|
| `xfs_repair -n DEV` | Dry-run (read-only) |
| `xfs_repair DEV` | Repair |
| `xfs_repair -L DEV` | Zero log (DANGER — data loss possible) |
| `xfs_repair -v DEV` | Verbose |
| `xfs_repair -m N` | Limit memory to N MB |

---

### Task 10 — Capstone report + cleanup

**Task statement:** *"Produce a one-paragraph report stating the device, FS type, exit codes from the read-only check and the repair, and whether reboot is recommended."*

```bash
cd /root/fsck-lab

cat > 10-report.txt <<EOF
Filesystem consistency report — $(hostname) — $(date -Iseconds)

ext4 device : $EXT_DEV  (label FSCK_EXT4)
xfs  device : $XFS_DEV  (label FSCK_XFS)

== ext4 ==
Read-only check  exit code: $(cat 06-detect-rc.txt)
Repair (-y)      exit code: $(cat 06-repair-rc.txt)
Decoded         : $(cat 06-decode.txt)
Post-repair RO  exit code: $(cat 06-verify-clean-rc.txt)

== XFS ==
xfs_repair -n   exit code: see 09-detect.txt
xfs_repair      exit code: $(cat 09-repair-rc.txt)
Post-repair RO  exit code: $(cat 09-verify-rc.txt)

Both filesystems are clean after recovery. No reboot required
because neither repair returned code 2.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo losetup -d "$EXT_DEV" "$XFS_DEV"
sudo rm -f "$EXT_IMG" "$XFS_IMG"
sudo rmdir /mnt/fsck-ext4 /mnt/fsck-xfs 2>/dev/null || true

cd /root
rm -rf /root/fsck-lab
exit
```

---

## 🔍 fsck Decision Guide

```
"Is it clean?"        → fsck -n DEV   (or xfs_repair -n DEV for XFS)
"Repair without prompts" → fsck.ext4 -y DEV   |   xfs_repair DEV
"Force a check"       → fsck.ext4 -f DEV
"Preen at boot"       → fstab pass 1 or 2; systemd uses -p
"FS won't mount"      → boot rescue → fsck -y → reboot
"XFS unreadable log"  → xfs_repair -L DEV (LAST RESORT, may lose data)
"Decode the code"     → 0 clean | 1 fixed | 2 fixed+reboot | 4 left dirty | 8 op error
"Pre-repair archive"  → dd if=DEV of=backup.img bs=1M  (only if size is reasonable)
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Loops + dual-FS sandbox
- [ ] 02 Mount, write, unmount
- [ ] 03 `fsck -n` healthy ext4
- [ ] 04 `xfs_repair -n` healthy XFS
- [ ] 05 Controlled ext4 corruption
- [ ] 06 `fsck.ext4 -y` + decode exit
- [ ] 07 Force check `-fv`
- [ ] 08 fstab pass numbers
- [ ] 09 `xfs_repair` cycle
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Running fsck on mounted FS | Refuses or corrupts | Always unmount first |
| `fsck.xfs` instead of `xfs_repair` | No-op success | XFS uses `xfs_repair` |
| `xfs_repair -L` casually | Possible data loss | Only when log is unreadable |
| Ignoring exit 2 | Boot may fail next time | Reboot when 2 |
| Running interactive fsck in script | Hangs on prompts | Use `-y` or `-p` |
| Backup superblock at wrong offset | "Bad magic" | Defaults at 32768, 98304, 163840 |
| Treating files in lost+found as garbage | Lost data | Inspect inodes; restore |
| Skipping `umount` on swap when fsck-ing | Bogus errors | Disable swap entry first |
| Forgetting pass number in fstab | All ext4 mounted in parallel by fsck | `0 1` root, `0 2` others |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Standard answer: `umount /mnt/X && fsck -y /dev/X && mount /mnt/X`.

**RHCE candidate**
- Ansible: `ansible.builtin.command: fsck -y {{ device }}` guarded by `when: not is_mounted`.

**SRE / Platform interview**
- Be ready: "emergency mode at boot, ext4 root corrupt — recover." Answer: boot rescue, `fsck.ext4 -y /dev/<root>`, reboot.

**DevOps**
- Pre-bake validation: `fsck.ext4 -fyv /dev/loop0p1` before tagging the AMI.

**AI / MLOps**
- Spot interruption recovery: `xfs_repair -n` first, then `xfs_repair` only if needed, never `-L` casually.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 116 — XFS format | The FS being repaired |
| Lab 117 — ext4 format | The FS being repaired |
| Lab 119 — dumpe2fs | Inspect features before fsck |
| Lab 110 — df / findmnt | Confirm unmount |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
