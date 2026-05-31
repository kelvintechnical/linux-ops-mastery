# Lab: Create and Activate Swap Space — `mkswap`, `swapon`, `swapoff`, `/etc/fstab`

- **Series:** linux-ops-mastery — RHCSA Storage Management
- **Subjects covered:** what swap is (anonymous-page evictee, not "extra RAM"), partition swap vs file swap, `mkswap DEV/FILE` (`-L LABEL`, `-U UUID`, `-c` bad-block check), `swapon DEV` (manual activation), `swapon -a` (read fstab and activate all marked `swap`), `swapon --show` (modern verbose listing), `swapon -s` (legacy `/proc/swaps` mirror), `swapoff DEV` (deactivate one) and `swapoff -a` (deactivate all), the `/etc/fstab` swap line (UUID/LABEL/path, type `swap`, options `defaults` or `sw,pri=N`, dump `0`, pass `0`), swap priority (`pri=N` in fstab or `-p N` to swapon — higher number = used first), why production prefers multiple equal-priority swap devices over one big one (round-robin parallel writes), creating a swap file with `fallocate`/`dd` (`fallocate` does **not** work for swap on XFS — must use `dd`), `chmod 0600` on swap files (kernel refuses world-readable swap), `/proc/swaps` and `free -h` verification, `vm.swappiness` sysctl as the swap aggressiveness knob, sizing recommendations (RHEL 9 table: ≤2 GB RAM → 2× RAM; 2–8 GB → equal; 8–64 GB → 4 GB min; >64 GB → workload-dependent)
- **Career arcs covered:** RHCSA (EX200 — "add 512 MB of swap and make it persistent"), RHCE (Ansible `ansible.posix.mount: state=present fstype=swap`), SRE (OOM-kill triage: confirm swap is actually being used), DevOps (cloud-init `swap: filename: ...` directive), AI / MLOps (disable swap on Kubernetes worker nodes — required by kubelet)
- **Prerequisite:** Labs 110–115 (partitioning), Lab 117 (mkfs concepts)
- **Time Estimate:** 30 to 45 minutes
- **Difficulty arc:** Task 1 sandbox · Task 2 partition swap with `mkswap` · Task 3 activate with `swapon` · Task 4 verify with `swapon --show` and `/proc/swaps` · Task 5 deactivate · Task 6 swap file (`dd` + `mkswap` + `chmod`) · Task 7 fstab UUID line + `swapon -a` · Task 8 swap priority demonstration · Task 9 `vm.swappiness` tuning · Task 10 capstone + cleanup

---

## Objective

Build two pieces of swap — one **partition-based** and one **file-based** — register both in `/etc/fstab`, activate them with `swapon -a`, verify them in `/proc/swaps`, deactivate cleanly, and tune `vm.swappiness`. By the end you can answer "how do I add 512 MB of persistent swap to a running RHEL 9 host?" without looking anything up.

The capstone is: *"On a RHEL 9 host: create a 256 MiB swap partition labeled `SWAP_LAB`, create a 256 MiB swap file at `/swapfile`, register both in fstab with explicit priorities (`pri=10` and `pri=5`), activate both with `swapon -a`, and confirm `/proc/swaps` shows two entries totaling 512 MiB."*

> **Lab safety note:** Loopback only for the partition portion. The swap file is real but small (256 MiB) and is removed in the cleanup task.

---

## Concept: Swap Is the Anonymous-Page Reservoir

Linux memory comes in two flavors that the kernel handles very differently when free RAM runs low:

```
   ┌───────────────────────────────────────────────────────────────┐
   │  File-backed pages         |  Anonymous pages                 │
   │  (mmap'd files, page cache)|  (heap, stack, BSS, malloc)      │
   │           │                |              │                   │
   │           │ reclaim cost = │              │ reclaim cost =    │
   │           │   drop and re- │              │   write to SWAP   │
   │           │   read on need │              │   then drop       │
   │           ▼                │              ▼                   │
   │      DISK FILE             │           SWAP DEVICE             │
   └───────────────────────────────────────────────────────────────┘
```

> **Why this matters:** Without swap, the kernel *cannot reclaim anonymous pages* under memory pressure — it can only invoke the OOM-killer. Swap is what gives the kernel room to write out cold anonymous pages so it can satisfy a new allocation without killing a process.

---

## 📜 Why Swap Exists — The Story

Original Unix on the PDP-11 (1970s) literally **swapped entire processes** in and out of secondary store — not pages, the whole address space. Demand paging (one 4 KiB page at a time) arrived with BSD VM on the VAX in the early 1980s and replaced whole-process swap, but the name `swap` stuck.

On Linux the swap device serves three purposes:
1. **Anonymous-page backing store** under memory pressure (the textbook use)
2. **Hibernate target** (`systemd-hibernate` writes RAM to swap, kernel reads it back on resume)
3. **Memory deduplication overflow** when KSM cannot merge enough pages

Modern RHEL 9 swap is almost always a **logical volume** named `swap` inside the `rhel` volume group (look in `/etc/fstab` on any default install). Swap *files* and swap *partitions* both still work, and both are RHCSA territory.

> **The point of the story:** swap is not "extra RAM" — it is the kernel's anonymous-page evictee. Sizing depends on workload, not just on RAM size.

---

## 👪 The Swap Family

```
Create
├── mkswap DEV              ← write swap signature + UUID to a partition
├── mkswap FILE             ← same, on a file
├── mkswap -L LABEL DEV     ← labeled swap (for fstab)
├── mkswap -U UUID DEV      ← specific UUID
└── mkswap -c DEV           ← bad-block check first

Activate
├── swapon DEV              ← turn one swap device on
├── swapon -p N DEV         ← with priority N (higher = used first)
├── swapon -a               ← read fstab, activate every `swap` line
├── swapon --show           ← modern listing (NAME, TYPE, SIZE, USED, PRIO)
└── swapon -s               ← legacy mirror of /proc/swaps

Deactivate
├── swapoff DEV             ← turn one off (kernel reads pages back to RAM)
└── swapoff -a              ← turn all off

Inspect
├── cat /proc/swaps          ← kernel-authoritative listing
├── free -h                  ← shows Swap line
├── grep VmSwap /proc/PID/status   ← per-process swap usage
└── smem -t                  ← (optional) per-process PSS + SWAP

Tune
├── sysctl vm.swappiness=N  ← 0–200, default 60 on RHEL 9
└── sysctl vm.vfs_cache_pressure=N
```

---

## 📚 Swap Reference Table

| Goal | Command |
|---|---|
| Format a partition for swap | `mkswap /dev/loop9p1` |
| Format with label | `mkswap -L SWAP_LAB /dev/loop9p1` |
| Activate one device | `swapon /dev/loop9p1` |
| Activate with priority | `swapon -p 10 /dev/loop9p1` |
| Activate everything in fstab | `swapon -a` |
| List active swap (modern) | `swapon --show` |
| List active swap (legacy) | `cat /proc/swaps` |
| Deactivate one | `swapoff /dev/loop9p1` |
| Deactivate all | `swapoff -a` |
| Swap file (XFS-safe) | `dd if=/dev/zero of=/swapfile bs=1M count=256 status=progress` |
| Swap file permissions | `chmod 0600 /swapfile` |
| fstab line (UUID) | `UUID=... none swap defaults,pri=10 0 0` |
| fstab line (file) | `/swapfile none swap defaults,pri=5 0 0` |
| Persistent swappiness | `/etc/sysctl.d/99-swap.conf` |

---

## 🎯 Career Pathway Sidebar

| Level | Why this lab matters |
|---|---|
| **RHCSA candidate** | "Add 512 MB of persistent swap." This lab is the answer. |
| **RHCE candidate** | Ansible `ansible.posix.mount` with `fstype=swap`. |
| **SRE / Platform** | OOM postmortem: confirm swap activated and being used (`/proc/swaps`). |
| **DevOps** | cloud-init `swap` module bakes swap into base AMIs. |
| **AI / MLOps** | **Disable** swap on Kubernetes nodes (`swapoff -a` + remove fstab line) — kubelet refuses to start otherwise. |

---

## 🔧 The 10 Tasks

---

### Task 1 — Set up sandbox + loop partition

```bash
sudo -i
mkdir -p /root/swap-lab && cd /root/swap-lab

LOOP_IMG=/var/tmp/swap-lab.img
truncate -s 512M "$LOOP_IMG"
LOOP_DEV=$(sudo losetup --find --show "$LOOP_IMG")
echo "$LOOP_DEV" | tee 01-loop.txt

sudo parted -s "$LOOP_DEV" mklabel gpt
sudo parted -s "$LOOP_DEV" mkpart primary linux-swap 1MiB 257MiB
sudo partprobe "$LOOP_DEV"; sudo udevadm settle

PART="${LOOP_DEV}p1"
echo "$PART" | tee 01-partition.txt
lsblk "$LOOP_DEV" | tee 01-lsblk.txt
```

**Reading it left to right:** `parted ... mkpart primary linux-swap ...` sets the partition **type GUID** to "Linux swap" (GPT type `0657FD6D-...`). The type GUID is advisory — `mkswap` writes the actual swap signature in Task 2 — but it makes the partition self-documenting.

---

### Task 2 — Format the partition with `mkswap`

```bash
cd /root/swap-lab

sudo mkswap -L SWAP_LAB "$PART" | tee 02-mkswap.txt
sudo blkid "$PART" | tee 02-blkid.txt
SWAP_UUID=$(sudo blkid -s UUID -o value "$PART")
echo "$SWAP_UUID" | tee 02-uuid.txt
```

**Reading it left to right:** `mkswap` writes a 4 KiB swap header at the start of the device. The header contains the magic string `SWAPSPACE2`, a UUID, an optional 16-byte label, and the page size used (must match `getconf PAGE_SIZE` of the running kernel, typically 4096).

**The story:** `mkswap` is intentionally minimal — it is the simplest filesystem-style format in the kernel. Read the swap header back with `blkid` to confirm the UUID and label landed.

**Expected output:**

```text
Setting up swapspace version 1, size = 256 MiB (268431360 bytes)
LABEL=SWAP_LAB, UUID=a1b2c3d4-...
/dev/loop9p1: LABEL="SWAP_LAB" UUID="a1b2c3d4-..." TYPE="swap"
```

---

### Task 3 — Activate with `swapon`

```bash
cd /root/swap-lab

free -h | tee 03-free-before.txt
sudo swapon -v "$PART" | tee 03-swapon.txt
free -h | tee 03-free-after.txt
```

**Reading it left to right:** `swapon -v DEV` activates the swap signature on the device, registers it with the kernel's swap subsystem, and starts accepting anonymous-page writes. `free -h` now shows the new total in the `Swap:` row.

**The story:** Activation is **transient** — a reboot loses it. The fstab line in Task 7 makes it persist.

**Expected output:**

```text
swapon: /dev/loop9p1: found signature [pagesize=4096, signature=swap]
swapon: /dev/loop9p1: pagesize=4096, swapsize=268435456, devsize=268435456
```

```text
               total        used        free      shared  buff/cache   available
Mem:           7.7Gi       1.2Gi       5.0Gi        16Mi       1.6Gi       6.2Gi
Swap:          256Mi          0B       256Mi
```

---

### Task 4 — List active swap

```bash
cd /root/swap-lab

sudo swapon --show | tee 04-swapon-show.txt
cat /proc/swaps | tee 04-proc-swaps.txt
sudo swapon -s | tee 04-swapon-s.txt
```

**Reading it left to right:** Three ways to view the same data:
- `swapon --show` — modern table (NAME, TYPE, SIZE, USED, PRIO)
- `cat /proc/swaps` — kernel-authoritative source (same data, fixed format)
- `swapon -s` — legacy summary, identical content to `/proc/swaps`

**Expected output (`swapon --show`):**

```text
NAME          TYPE      SIZE USED PRIO
/dev/loop9p1  partition 256M   0B   -2
```

> **Note:** The default priority on RHEL 9 is `-2` (auto-assigned, descending) unless you specify `-p N` or `pri=N`.

---

### Task 5 — Deactivate with `swapoff`

```bash
cd /root/swap-lab

sudo swapoff -v "$PART" | tee 05-swapoff.txt
swapon --show | tee 05-after.txt
free -h | tee 05-free-after.txt
```

**Reading it left to right:** `swapoff DEV` tells the kernel "stop using this swap; read every page currently on it back into RAM." If RAM is too full to absorb the pages, `swapoff` returns ENOMEM and the device stays active — that is the safety guarantee.

**The story:** `swapoff` is the command kubeadm requires you to run before joining a node (with `swapoff -a` + fstab line removal). It is also what you reach for before unmounting a parent volume that contains a swap partition.

**Expected output:**

```text
swapoff /dev/loop9p1
```

```text
               total        used        free      shared  buff/cache   available
Swap:             0B          0B          0B
```

---

### Task 6 — Create a swap **file** (XFS-safe method)

```bash
cd /root/swap-lab

SWAPFILE=/root/swap-lab/swapfile-256m
sudo dd if=/dev/zero of="$SWAPFILE" bs=1M count=256 status=progress conv=notrunc
sudo chmod 0600 "$SWAPFILE"
sudo mkswap -L SWAP_FILE "$SWAPFILE" | tee 06-mkswap-file.txt
sudo swapon -v -p 5 "$SWAPFILE" | tee 06-swapon-file.txt
swapon --show | tee 06-after.txt
```

**Reading it left to right:**
- `dd if=/dev/zero ... conv=notrunc` allocates **real** disk blocks (no holes). XFS does **not** support `fallocate`-created swap files; the kernel rejects them with "swapon: ... has holes".
- `chmod 0600` is **required** — the kernel refuses to swap onto a world-readable file.
- `mkswap` writes the swap signature into the file.
- `swapon -p 5` activates at priority 5.

**The story:** Swap files are the modern recommendation when you cannot afford to repartition. They are flexible (resize by recreate) but slightly slower than a swap partition because they go through the filesystem layer.

**Expected output:**

```text
Setting up swapspace version 1, size = 256 MiB (268431360 bytes)
LABEL=SWAP_FILE, UUID=...
swapon: /root/swap-lab/swapfile-256m: pagesize=4096, swapsize=268435456, devsize=268435456
NAME                          TYPE      SIZE USED PRIO
/root/swap-lab/swapfile-256m  file      256M   0B    5
```

---

### Task 7 — Persistent activation via `/etc/fstab`

```bash
cd /root/swap-lab

sudo swapoff -a

sudo cp /etc/fstab /etc/fstab.bak.$(date +%s)

echo "UUID=$SWAP_UUID none swap defaults,pri=10 0 0"      | sudo tee -a /etc/fstab
echo "$SWAPFILE       none swap defaults,pri=5  0 0"      | sudo tee -a /etc/fstab

grep -E '^(UUID='"$SWAP_UUID"'|'"$SWAPFILE"')' /etc/fstab | tee 07-fstab-lines.txt

sudo systemctl daemon-reload
sudo swapon -a
swapon --show | tee 07-swapon-show.txt
```

**Reading it left to right:**
- Field 1: device — UUID for partition, absolute path for file
- Field 2: `none` — swap has no mount point (it is not a filesystem)
- Field 3: `swap` — type
- Field 4: `defaults,pri=N` — options (priority is the noteworthy one)
- Field 5: `0` — dump (irrelevant for swap)
- Field 6: `0` — fsck pass (always 0 for swap)

**The story:** Two swap entries with different priorities lets the kernel exercise the **partition** first (pri=10) and only spill to the **file** (pri=5) when partition swap is full. Equal priorities → round-robin parallel writes.

**Expected output:**

```text
UUID=a1b2c3d4-... none swap defaults,pri=10 0 0
/root/swap-lab/swapfile-256m       none swap defaults,pri=5  0 0
```

```text
NAME                          TYPE      SIZE USED PRIO
/dev/loop9p1                  partition 256M   0B   10
/root/swap-lab/swapfile-256m  file      256M   0B    5
```

---

### Task 8 — Demonstrate swap priority

```bash
cd /root/swap-lab

cat > 08-priority.txt <<'EOF'
Priority rules (from `man swapon`):
  -2 → auto-assigned, descending
   0 → lowest user-set
  ...
  32767 → highest user-set

Behavior under memory pressure:
  - Higher PRIO devices are used FIRST.
  - Equal PRIO → round-robin parallel writes (the "RAID0-style" pattern).
  - Lower PRIO devices act as overflow.

This lab fstab choices:
  PARTITION  pri=10  ← preferred (faster — direct device IO)
  SWAP FILE  pri=5   ← overflow only
EOF
cat 08-priority.txt
```

> **Sanity check (optional):** Run `stress --vm 1 --vm-bytes 6G --timeout 30s` if `stress` is installed. Watch `swapon --show` — the USED column climbs on `/dev/loop9p1` (pri=10) before the swapfile (pri=5).

---

### Task 9 — Tune `vm.swappiness`

```bash
cd /root/swap-lab

cat /proc/sys/vm/swappiness | tee 09-default.txt

sudo sysctl vm.swappiness=10 | tee 09-runtime.txt
cat /proc/sys/vm/swappiness | tee 09-now.txt

cat <<EOF | sudo tee /etc/sysctl.d/99-swap-lab.conf
# Lab 120 — keep swap usage low until RAM is really tight
vm.swappiness = 10
EOF

sudo sysctl --system 2>&1 | grep -E '99-swap-lab|vm.swappiness' | tee 09-persist.txt
```

**Reading it left to right:**
- `vm.swappiness` ranges 0–200 on modern kernels (was 0–100 before kernel 5.8).
- Default on RHEL 9 is **60**.
- Higher = swap more aggressively. Lower = prefer reclaim from file cache first.
- **Workload guidance:** databases → 10. Workstations → 60 (default). Hibernate users → 100.
- `0` is **not** "no swap" — it means "almost never swap" (kernel can still swap to avoid OOM).

**The story:** `vm.swappiness` controls only the tip-over point between reclaiming **anon** pages (swap) and **file** pages (drop cache). It does **not** disable swap.

**Expected output:**

```text
60
vm.swappiness = 10
10
* Applying /etc/sysctl.d/99-swap-lab.conf ...
vm.swappiness = 10
```

---

### Task 10 — Capstone report + cleanup

```bash
cd /root/swap-lab

cat > 10-report.txt <<EOF
Swap report — $(hostname) — $(date -Iseconds)

Partition       : $PART     UUID=$SWAP_UUID     LABEL=SWAP_LAB    pri=10
Swap file       : $SWAPFILE                                       pri=5
fstab entries   :
$(grep -E '(UUID='"$SWAP_UUID"'|'"$SWAPFILE"')' /etc/fstab)

Active swap     :
$(swapon --show)

Free / used     :
$(free -h | awk '/^Swap:/')

swappiness      : $(cat /proc/sys/vm/swappiness)   (default 60; lab set to 10)

Recommendation:
  - Production: prefer LVM swap volume over swap file (LVM lets you grow/shrink without recreate).
  - Kubernetes worker: swapoff -a + remove fstab line before kubelet starts.
  - Database hosts: vm.swappiness=10 in /etc/sysctl.d/.
EOF
cat 10-report.txt
```

**Cleanup**

```bash
sudo swapoff -a

sudo sed -i "\|UUID=$SWAP_UUID|d" /etc/fstab
sudo sed -i "\|$SWAPFILE|d" /etc/fstab
sudo rm -f /etc/sysctl.d/99-swap-lab.conf
sudo sysctl --system >/dev/null

# Re-activate any production swap that was disabled by `swapoff -a`
sudo swapon -a

sudo rm -f "$SWAPFILE"

sudo losetup -d "$LOOP_DEV"
sudo rm -f "$LOOP_IMG"

cd /root
rm -rf /root/swap-lab
exit
```

> **Cleanup safety note:** `swapon -a` after the sed lines is important — if the host has a real fstab swap entry (e.g. `/dev/mapper/rhel-swap`), `swapoff -a` deactivated it. The `swapon -a` re-reads fstab and brings it back.

---

## 🔍 Swap Decision Guide

```
"Add persistent swap"
  ├─ Have a free partition?  → mkswap + UUID + fstab line
  ├─ LVM available?           → lvcreate -L 1G -n swap rhel + mkswap + fstab
  └─ Otherwise                → dd-allocated swap file + chmod 0600 + fstab

"Why isn't swap being used?"
  ├─ Activated?               → swapon --show / cat /proc/swaps
  ├─ swappiness low?          → cat /proc/sys/vm/swappiness
  └─ Plenty of free RAM?      → No reason to swap. Working as designed.

"Kubernetes refusing to start kubelet"
  └─ swapoff -a, sed out fstab swap line, sysctl: nothing — kubelet just wants 0 swap.

"Hibernate target"
  └─ Swap >= total RAM, on a single contiguous device. The fstab line gets `discard` removed.
```

---

## Lab Checklist (10 Tasks)

- [ ] 01 Loop + linux-swap partition
- [ ] 02 `mkswap -L SWAP_LAB`
- [ ] 03 `swapon -v`
- [ ] 04 `swapon --show` / `/proc/swaps`
- [ ] 05 `swapoff`
- [ ] 06 Swap file (`dd` + `mkswap` + `chmod 0600`)
- [ ] 07 fstab UUID + file entries, `swapon -a`
- [ ] 08 Priority concept
- [ ] 09 `vm.swappiness` runtime + `/etc/sysctl.d/`
- [ ] 10 Capstone + cleanup

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `fallocate` swap file on XFS | "has holes" on `swapon` | Use `dd if=/dev/zero ... conv=notrunc` |
| World-readable swap file | `swapon: insecure permissions` | `chmod 0600` |
| Forgot `pri=N` in fstab | All swap at -2, no ordering | Add `pri=N` to each line |
| `swapoff -a` then forgot `swapon -a` | Production swap stays off | Always re-`swapon -a` after maintenance |
| `vm.swappiness=0` expecting "no swap" | Still swaps near OOM | Use `swapoff -a` + remove fstab to truly disable |
| Swap on tmpfs/ramfs | Defeats the purpose | Swap to disk, not RAM |
| Kubernetes worker with active swap | kubelet won't start | `swapoff -a` + remove fstab line |
| Swap file on btrfs without `chattr +C` | Errors on activation | Set `+C` (no-COW) before `mkswap` |

---

## 🎯 Career & Interview Strategy

**RHCSA candidate**
- Memorize: `mkswap -L NAME DEV` → `blkid` → fstab `UUID=... none swap defaults,pri=N 0 0` → `swapon -a`.

**RHCE candidate**
- Ansible: `ansible.posix.mount: src=UUID=... path=none fstype=swap state=present opts=defaults,pri=10`.

**SRE / Platform interview**
- "How do you confirm swap is active and being used?" → `swapon --show` (active), `free -h` (used field).

**DevOps**
- cloud-init `swap: filename: /swapfile  size: 1G  maxsize: 1G` — bakes it into AMIs.

**AI / MLOps**
- Kubernetes: `swapoff -a` + `sed -i '/ swap / s/^/#/' /etc/fstab` before kubeadm join.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| Lab 115 — `parted` | How you carved the partition |
| Lab 117 — Format ext4 | Sibling format step |
| Lab 125 — `lvcreate` | LVM swap volume is the production pattern |
| Lab 133 — fstab persistence | Same file, different filesystem types |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
