# Lab: Format a Partition with Ext4 — `mkfs.ext4`, `tune2fs`, `e2label`, `/etc/fstab`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** ext4 as the legacy/portable default, `mkfs.ext4` (defaults on RHEL 9, `-F` force, `-L LABEL`, `-U UUID`, `-b 4096` block size, `-i bytes_per_inode`, `-N inodes`, `-m 1` reserved-blocks percent, `-O ^has_journal` to skip journal, `-E lazy_itable_init=0` slow but immediate ready), journal vs no-journal (ext2 vs ext3 vs ext4), `tune2fs -l DEV` to read superblock, `tune2fs -L NEWLABEL`, `tune2fs -U random|time|clear|NEWUUID`, `tune2fs -m PERCENT` for reserved block %, `tune2fs -c COUNT` and `tune2fs -i INTERVAL` for fsck schedules, `e2label DEV` short relabel, `dumpe2fs -h` summary (covered in Lab 119), mount with `defaults,noatime,errors=remount-ro`, UUID vs LABEL in fstab, `resize2fs` placeholder (Lab 129), `fsck.ext4` placeholder (Lab 118), comparing ext4 to XFS (shrink-capable vs not)
- **Career arcs covered:** RHCSA (EX200 — "create an ext4 filesystem"), RHCE (Ansible `community.general.filesystem: fstype=ext4`), SRE (boot/efi/legacy disks, ARM ext4 defaults), DevOps (Ubuntu base images), AI / MLOps (ext4 still common on shared NFS backings)
- **Prerequisite:** Lab 116 (XFS), Labs 110–115 (partitioning)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Tasks 1–2 sandbox + partition · Task 3 `mkfs.ext4` default · Task 4 `-L LABEL` · Task 5 `tune2fs -l` read · Task 6 `tune2fs -L` / `e2label` · Task 7 `tune2fs -m` reserved blocks · Task 8 mount + fstab · Task 9 `tune2fs -c/-i` fsck schedule · Task 10 capstone + cleanup

---

## Objective

Format an ext4 filesystem, set a label, adjust the reserved-block percentage, mount by UUID with safe options, and persist via `/etc/fstab` — and know the two or three places ext4 should still be your first choice in RHEL 9 (small `/boot`, shrinkable volumes, cross-distro portability).

The capstone is: *"Format `/dev/loop9p1` as ext4 labeled `RHCSA_EXT4`, set reserved-blocks to 1 %, mount by UUID at `/mnt/rhcsa-ext4` with `defaults,noatime,errors=remount-ro`, persist in fstab, then `mount -a` and verify."*

> **Lab safety note:** Loopback only. Never run `mkfs.ext4` against a partition that already has data unless you intend to destroy it.

---

## Concept: ext4 Is the Portable Default

ext4 is **not RHEL 9's default** (XFS is), but you will still meet it on:
- `/boot` (where GRUB compatibility matters)
- shrinkable volumes (you can `resize2fs` smaller, you cannot shrink XFS)
- cross-distro disks (Ubuntu, Debian default to ext4)
- USB sticks formatted on Linux

```
   ┌─────────────────────────────────────────────────────────────┐
   │ mkfs.ext4 DEV                                                │
   │   ├── superblock (one primary + backups)                     │
   │   ├── block groups (each with its own superblock copy)       │
   │   ├── journal (default; ext4 = ext3 + extents + ...)         │
   │   ├── UUID generated automatically                            │
   │   └── reserved blocks: 5 % by default                         │
   │                                                              │
   │ tune2fs -l DEV  ←  read superblock                            │
   │ tune2fs -L LABEL DEV   |   e2label DEV LABEL                  │
   │ tune2fs -m PERCENT DEV  ← reserved blocks                     │
   │ tune2fs -U random DEV   ← change UUID                         │
   │ tune2fs -c COUNT -i INTERVAL DEV   ← fsck schedule            │
   └─────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Most RHCSA "create a filesystem" tasks accept XFS, but some explicitly say `ext4`. Be ready for both.

---

## 📜 Why ext4 — The Story

- **ext** (1992, Rémy Card) — the first Linux-native FS.
- **ext2** (1993) — added the modern layout, no journal.
- **ext3** (2001, Stephen Tweedie) — added journaling on top of ext2.
- **ext4** (2008, Theodore Ts'o, Andrew Morton) — added extents (instead of indirect blocks), bigger sizes, faster fsck, delayed allocation, multiblock allocator.

Red Hat shipped ext4 as RHEL 6 default, then switched to XFS in RHEL 7. ext4 remains a **first-class citizen** in RHEL 9 — `mkfs.ext4`, `tune2fs`, `e2fsck`, `resize2fs` are all installed by default.

> **The point of the story:** ext4 is the universally-portable choice. XFS is the RHEL-preferred performance choice. You should be fluent in both.

---

## 👪 The ext4 Family

```
Creation
├── mkfs.ext4 DEV               ← format
├── mkfs.ext4 -F DEV            ← force overwrite
├── mkfs.ext4 -L LABEL DEV
├── mkfs.ext4 -U UUID DEV
├── mkfs.ext4 -m 1 DEV          ← reserved-blocks %
├── mkfs.ext4 -O ^has_journal   ← ext2-style, no journal
└── mkfs.ext3 DEV / mkfs.ext2 DEV  ← variants

Inspection
├── tune2fs -l DEV              ← full superblock
├── dumpe2fs -h DEV             ← superblock summary (Lab 119)
├── blkid DEV
└── lsblk -f DEV

Administration
├── tune2fs -L NEW DEV          ← relabel
├── e2label DEV NEW             ← short form of -L
├── tune2fs -U NEW|random DEV   ← change UUID
├── tune2fs -m PERCENT DEV      ← reserved blocks
├── tune2fs -c COUNT DEV        ← mount-count fsck
├── tune2fs -i INTERVAL DEV     ← time-based fsck
├── resize2fs DEV [SIZE]        ← shrink/grow (Lab 129)
└── fsck.ext4 / e2fsck DEV      ← repair (Lab 118)
```

---

## 📚 ext4 Reference Table

| Goal | Command | Notes |
|---|---|---|
| Default format | `mkfs.ext4 /dev/X` | |
| Force | `mkfs.ext4 -F /dev/X` | |
| Label at format | `mkfs.ext4 -L LABEL /dev/X` | Max 16 chars |
| Set reserved % | `mkfs.ext4 -m 1 /dev/X` | Default 5 |
| No journal (ext2 style) | `mkfs.ext4 -O ^has_journal /dev/X` | |
| Immediate-ready | `mkfs.ext4 -E lazy_itable_init=0 /dev/X` | Slower mkfs but no late inode-table writes |
| Read superblock | `tune2fs -l /dev/X` | |
| Relabel | `tune2fs -L NEW /dev/X` or `e2label /dev/X NEW` | |
| Change UUID | `tune2fs -U random /dev/X` | Or specific UUID, `time`, `clear` |
| Reserved % later | `tune2fs -m 1 /dev/X` | |
| fsck after N mounts | `tune2fs -c N /dev/X` | |
| fsck after T seconds | `tune2fs -i 30d /dev/X` | |
| Mount safely | `mount -o defaults,noatime,errors=remount-ro UUID=... /mnt/X` | |
| fstab dump/pass | `0 2` (root) or `0 0` (data) | XFS uses `0 0` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | Some exam tasks say "ext4" — `mkfs.ext4` + UUID fstab. |
| **RHCE candidate** | Ansible `community.general.filesystem: fstype=ext4`. |
| **SRE / Platform** | `/boot` is almost always ext4. `tune2fs -c 0 -i 0` to silence fsck on appliances. |
| **DevOps** | Ubuntu/Debian base images default to ext4. |
| **AI / MLOps** | Shared NFS-backed scratch sometimes still ext4 for compat. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up sandbox & loop device

```bash
sudo -i
mkdir -p /root/ext4-lab && cd /root/ext4-lab

LOOP_IMG=/var/tmp/ext4-lab.img
truncate -s 1G "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "$LOOP_DEV" | tee 01-loop.txt
```

---

### Task 2 — Create a single partition with `parted`

```bash
cd /root/ext4-lab

sudo parted -s "$LOOP_DEV" mklabel gpt
sudo parted -s "$LOOP_DEV" mkpart primary ext4 1MiB 100%
sudo partprobe "$LOOP_DEV"; sudo udevadm settle

PART="${LOOP_DEV}p1"
echo "$PART" | tee 02-partition.txt
lsblk "$LOOP_DEV" | tee 02-lsblk.txt
```

---

### Task 3 — Format with defaults using `mkfs.ext4`

```bash
cd /root/ext4-lab

sudo mkfs.ext4 "$PART" | tee 03-mkfs-default.txt
```

**Reading it left to right:** `mkfs.ext4` (alias `mke2fs -t ext4`) writes superblock, block-group descriptors, inode tables, the journal, and root directory.

**The story:** RHEL 9 defaults are sensible: 4 KiB blocks, has_journal on, 5 % reserved, 64bit on, extents on, dir_index on. Don't change them unless you have a measured reason.

**Expected output:**

```text
mke2fs 1.46.5 (30-Dec-2021)
Creating filesystem with 261888 4k blocks and 65536 inodes
Filesystem UUID: a1b2c3d4-...
Superblock backups stored on blocks:
        32768, 98304, 163840, 229376

Allocating group tables: done
Writing inode tables: done
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done
```

**Switches**

| Token | Meaning |
|---|---|
| `mkfs.ext4 DEV` | Default format |
| `-F` | Force |
| `-L LABEL` | Label |
| `-U UUID` | Specific UUID at format |
| `-m PERCENT` | Reserved blocks (default 5) |
| `-N N` | Inode count |
| `-O FEAT` / `-O ^FEAT` | Enable/disable feature |
| `-E lazy_itable_init=0` | Write inode tables now, not lazily |

**Troubleshoot**

| Symptom | Fix |
|---|---|
| `Device contains a ... file system` | Add `-F` to overwrite |
| `device busy` | `umount` first |
| `inode table not yet ready` warnings | Lazy init — wait or use `-E lazy_itable_init=0` |

---

### Task 4 — Reformat with a label `RHCSA_EXT4`

```bash
cd /root/ext4-lab

sudo mkfs.ext4 -F -L RHCSA_EXT4 "$PART" | tee 04-mkfs-label.txt
sudo blkid "$PART" | tee 04-blkid.txt
UUID=$(sudo blkid -s UUID -o value "$PART")
echo "$UUID" | tee 04-uuid.txt
```

**Expected output:**

```text
/dev/loop9p1: LABEL="RHCSA_EXT4" UUID="a1b2c3d4-..." BLOCK_SIZE="4096" TYPE="ext4" PARTUUID="..."
```

---

### Task 5 — Read the superblock with `tune2fs -l`

```bash
cd /root/ext4-lab

sudo tune2fs -l "$PART" | tee 05-tune2fs.txt
sudo tune2fs -l "$PART" | grep -E 'Filesystem (UUID|features|created|state)|Block count|Reserved block count|Inode count|Mount count|Maximum mount count|Last (mount|write)' | tee 05-key.txt
```

**Human-Readable Breakdown:** `tune2fs -l` prints every field in the ext4 superblock. `grep -E` distills the must-know items: UUID, features, block & inode counts, reserved blocks, mount counters.

**Expected output (excerpt):**

```text
Filesystem volume name:   RHCSA_EXT4
Filesystem UUID:          a1b2c3d4-...
Filesystem features:      has_journal ext_attr resize_inode dir_index filetype
                          needs_recovery extent 64bit flex_bg sparse_super large_file
                          huge_file dir_nlink extra_isize metadata_csum
Block count:              261888
Reserved block count:     13094
Inode count:              65536
Maximum mount count:      -1
Check interval:           0 (<none>)
```

---

### Task 6 — Relabel with `tune2fs -L` and `e2label`

```bash
cd /root/ext4-lab

sudo tune2fs -L EXT4_TUNE2FS "$PART"
sudo blkid "$PART" | tee 06-after-tune2fs-L.txt

sudo e2label "$PART" EXT4_E2LABEL
sudo blkid "$PART" | tee 06-after-e2label.txt

sudo e2label "$PART" RHCSA_EXT4
sudo blkid "$PART" | tee 06-restored.txt
```

**The story:** `e2label DEV NEWLABEL` is the **shortest** way to relabel an ext family FS — designed to be muscle-memory on the exam. `tune2fs -L` does the same thing.

---

### Task 7 — Reduce reserved blocks to 1 % with `tune2fs -m`

```bash
cd /root/ext4-lab

sudo tune2fs -m 1 "$PART" | tee 07-tune2fs-m.txt
sudo tune2fs -l "$PART" | grep -E 'Reserved block count|Reserved blocks uid|Reserved blocks gid' | tee 07-reserved.txt
```

**Human-Readable Breakdown:** `tune2fs -m PERCENT` changes the **reserved blocks** percentage. Default is 5 % — historically reserved for root so a runaway log file doesn't fill the disk and lock out essential daemons. On a 1 TB **data** volume, 5 % = 50 GiB wasted; dropping to 1 % is normal practice for non-root data volumes.

**Reading it left to right:** `tune2fs -m 1` updates the in-superblock counter `s_r_blocks_count`. Verifying with `tune2fs -l | grep Reserved` confirms.

**The story:** On root (`/`) keep 5 %. On `/var/log`, databases, or any data-only volume, 1 % or even 0 % is normal. RHCSA tasks sometimes specifically say "set reserved blocks to 1 %" — this is the command.

**Expected output:**

```text
tune2fs 1.46.5 (30-Dec-2021)
Setting reserved blocks percentage to 1% (2618 blocks)
Reserved block count:     2618
Reserved blocks uid:      0 (user root)
Reserved blocks gid:      0 (group root)
```

**Switches**

| Token | Meaning |
|---|---|
| `tune2fs -m PCT` | Set reserved-blocks percent |
| `tune2fs -r N` | Set absolute reserved blocks count |
| `tune2fs -u USER` | Set reserved-blocks owner uid |
| `tune2fs -g GRP` | Set reserved-blocks owner gid |

---

### Task 8 — Mount and add to fstab

```bash
cd /root/ext4-lab

sudo mkdir -p /mnt/rhcsa-ext4

sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)
echo "UUID=$UUID  /mnt/rhcsa-ext4  ext4  defaults,noatime,errors=remount-ro  0 2" | sudo tee -a /etc/fstab

sudo systemctl daemon-reload
sudo mount -a
findmnt /mnt/rhcsa-ext4 | tee 08-findmnt.txt
df -hT /mnt/rhcsa-ext4 | tee 08-df.txt
```

**Reading it left to right:** `errors=remount-ro` is the **defining ext4 safety option** — if the filesystem encounters an error, remount it read-only rather than continue corrupting. `0 2` = no dump, fsck pass 2 (root is pass 1, swap is 0).

**The story:** Default ext4 mount options should always include `errors=remount-ro` on production volumes. The kernel will catch a problem and freeze the FS read-only rather than amplify damage.

**Expected output:**

```text
TARGET             SOURCE        FSTYPE OPTIONS
/mnt/rhcsa-ext4    /dev/loop9p1  ext4   rw,noatime,errors=remount-ro,...
```

---

### Task 9 — Set fsck schedule with `tune2fs -c` / `-i`

```bash
cd /root/ext4-lab

sudo tune2fs -c 50 "$PART"
sudo tune2fs -i 30d "$PART"
sudo tune2fs -l "$PART" | grep -E 'Maximum mount count|Check interval' | tee 09-fsck-schedule.txt

sudo tune2fs -c 0 -i 0 "$PART"
sudo tune2fs -l "$PART" | grep -E 'Maximum mount count|Check interval' | tee 09-fsck-disabled.txt
```

**The story:** ext4 can auto-fsck at boot every N mounts (`-c N`) or every T time (`-i 30d`). Modern enterprise practice usually **disables this** with `-c 0 -i 0` because XFS-style checksums + monitoring + backups beat surprise fsck delays at boot.

**Expected output:**

```text
Maximum mount count:      50
Check interval:           2592000 (1 month)
Maximum mount count:      -1
Check interval:           0 (<none>)
```

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/ext4-lab

cat > 10-report.txt <<EOF
ext4 lifecycle report — $(hostname) — $(date -Iseconds)

Loop device : $LOOP_DEV
Partition   : $PART
UUID        : $UUID
LABEL       : RHCSA_EXT4
Mount point : /mnt/rhcsa-ext4

== /etc/fstab line ==
$(grep '/mnt/rhcsa-ext4' /etc/fstab)

== findmnt ==
$(findmnt /mnt/rhcsa-ext4)

== reserved blocks + fsck schedule ==
$(sudo tune2fs -l "$PART" | grep -E 'Reserved block count|Maximum mount count|Check interval')
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo umount /mnt/rhcsa-ext4
sudo sed -i "\|/mnt/rhcsa-ext4|d" /etc/fstab
sudo rmdir /mnt/rhcsa-ext4

sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"

cd /root
rm -rf /root/ext4-lab
exit
```

---

## 🔍 ext4 Decision Guide

```
"Format ext4"                → mkfs.ext4 [-F] DEV
"Label"                      → mkfs.ext4 -L NAME DEV   |   e2label DEV NAME
"Reserved blocks 1%"         → tune2fs -m 1 DEV
"Disable fsck schedule"      → tune2fs -c 0 -i 0 DEV
"Change UUID"                → tune2fs -U random DEV
"Read superblock"            → tune2fs -l DEV   |   dumpe2fs -h DEV
"Mount safely"               → mount -o defaults,noatime,errors=remount-ro UUID=... /mnt/X
"Persist"                    → /etc/fstab + mount -a
"Need shrink"                → ext4 (resize2fs -M / resize2fs SIZE)
"Need extreme parallelism"   → Use XFS instead
```

---

## ✅ Lab Checklist (10 Tasks)

- [ ] 01 Loop device
- [ ] 02 GPT partition
- [ ] 03 `mkfs.ext4` default
- [ ] 04 Reformat with `-L`
- [ ] 05 `tune2fs -l` superblock
- [ ] 06 `tune2fs -L` + `e2label`
- [ ] 07 `tune2fs -m 1`
- [ ] 08 fstab `errors=remount-ro` + `mount -a`
- [ ] 09 `tune2fs -c 0 -i 0`
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `mkfs.ext4` over a live mount | "Device busy" | `umount` first |
| Forgot `-F` over existing FS | mkfs prompts | Confirm or pass `-F` |
| Reserved blocks = 0 on root | Root cannot recover from full disk | Keep 5 % on `/` |
| Used XFS dump/pass `0 0` for ext4 root | No fsck pass | Use `0 1` for `/`, `0 2` for other ext4 |
| `errors=continue` on production | Corrupted writes after error | Use `errors=remount-ro` |
| `tune2fs -L` with quotes that include spaces | Treated as part of label | Avoid spaces |
| `mkfs.ext4` with `-O ^has_journal` for important data | No crash safety | Only for scratch / ext2-style use |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize: `mkfs.ext4 -F -L LABEL DEV` → `blkid` → fstab UUID + `defaults,noatime,errors=remount-ro 0 2` → `mount -a`.

**RHCE candidate**
- Ansible: `community.general.filesystem: fstype=ext4 dev=/dev/vdb1 opts=-L RHCSA_EXT4`.

**SRE / Platform interview**
- Be ready: when ext4, when XFS? (shrink, /boot, cross-distro → ext4; everything else → XFS.)

**DevOps**
- Ubuntu base images: ext4 default. cloud-init `fs_setup: filesystem: ext4`.

**AI / MLOps**
- ext4 still appears on shared NFS exports — be ready to mount with `noatime,errors=remount-ro`.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 116 — XFS | Counterpart format |
| Lab 118 — fsck.ext4 | Repair |
| Lab 119 — dumpe2fs | Inspect features |
| Lab 129 — resize2fs | Online/offline resize |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
