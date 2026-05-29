# Lab 10c: Verifying Move/Rename Behavior — atomicity, cross-fs, hard links

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `10a` (RHCSA) → `10b` (Ansible) → **`10c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 verification reflex, RHCE auditor seat, SRE change validation
- **Prerequisite:** Lab 10a and 10b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2
- **Practice Directory (rotation #10):** `/var`
- **Sandbox:** `/tmp/mv-verify-lab`
- **Traps rehearsed this lab:** **T10-A** (assuming all `mv` are atomic) · **T10-B** (not auditing overwrite fallout) · **T10-C** (trusting automation output without state checks)

> **This lab's practice directory is: `/var`** — each task references `/var` while verification runs in `/tmp/mv-verify-lab`.

---

## LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T10-A T10-B T10-C"
echo "📁  PRACTICE DIR: /var"
ls -ld /var /var/log
test -f /root/rhcsa_journal/lab-10b/task2/rerun.txt && echo "✅ lab-10b evidence present"
```

---

## Objective

Prove, using direct inspection commands, that:

1. Same-fs rename preserves inode and hard-link relationship.
2. Cross-fs move changes inode and breaks hard-link relationship.
3. Ansible boundary outcomes from `10b` match real filesystem state.

---

## Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/mv-verify-lab/{samefs,crossfs}
mkdir -p /root/rhcsa_journal/lab-10c
echo "payload" > /tmp/mv-verify-lab/samefs/original.txt
ln /tmp/mv-verify-lab/samefs/original.txt /tmp/mv-verify-lab/samefs/original.hard
ls -li /tmp/mv-verify-lab/samefs
```

---

## Task 1 — Verify same-fs rename and hard-link survival

**Practice directory this task:** `/var` and `/tmp/mv-verify-lab`

### Warm-Up

```bash
ls -lt /var/log 2>/dev/null | head -n 3
stat -c '%n inode=%i links=%h fs=%m' /tmp/mv-verify-lab/samefs/original.txt
stat -c '%n inode=%i links=%h fs=%m' /tmp/mv-verify-lab/samefs/original.hard
```

### Purpose

Rename one hard-linked path on the same filesystem and confirm both names still point to one inode.

### Main command block

```bash
mkdir -p /tmp/mv-verify-lab/task1
mv /tmp/mv-verify-lab/samefs/original.txt /tmp/mv-verify-lab/samefs/renamed.txt

stat -c '%n inode=%i links=%h fs=%m' /tmp/mv-verify-lab/samefs/renamed.txt \
  /tmp/mv-verify-lab/samefs/original.hard \
  | tee /tmp/mv-verify-lab/task1/stat.txt

find /tmp/mv-verify-lab/samefs -maxdepth 1 -inum "$(stat -c '%i' /tmp/mv-verify-lab/samefs/renamed.txt)" \
  | tee -a /tmp/mv-verify-lab/task1/stat.txt

ls -li /tmp/mv-verify-lab/samefs | tee -a /tmp/mv-verify-lab/task1/stat.txt
```

### Concept Card

| Concept | One-line |
|---|---|
| Same-fs rename | Name changes, inode does not |
| Hard-link survival | Links still valid because inode is unchanged |
| 🪤 T10-A | Atomic assumption only valid on same filesystem |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-10c/task1
mkdir -p "$JDIR"
cp /tmp/mv-verify-lab/task1/stat.txt "$JDIR/evidence.txt"
```

---

## Task 2 — Verify cross-fs move behavior + Ansible outputs

**Practice directory this task:** `/var` and `/tmp/mv-verify-lab`

### Warm-Up

```bash
ls -ld /var /var/log
echo "cross-fs-payload" > /tmp/mv-verify-lab/crossfs/cross.txt
stat -c '%n inode=%i fs=%m' /tmp/mv-verify-lab/crossfs/cross.txt
```

### Purpose

Check whether move crossed filesystems, evaluate inode result, and audit Lab 10b outcome files.

### Main command block

```bash
mkdir -p /tmp/mv-verify-lab/task2
src=/tmp/mv-verify-lab/crossfs/cross.txt
dst=/var/tmp/lab10-cross.txt

src_fs=$(df --output=source "$src" | tail -1)
src_inode=$(stat -c '%i' "$src")
mv "$src" "$dst"
dst_fs=$(df --output=source "$dst" | tail -1)
dst_inode=$(stat -c '%i' "$dst")

{
  echo "src_fs=$src_fs dst_fs=$dst_fs"
  echo "src_inode=$src_inode dst_inode=$dst_inode"
  if [ "$src_fs" = "$dst_fs" ]; then
    echo "SAME_FS_RESULT"
  else
    echo "CROSS_FS_RESULT"
  fi
  echo "=== lab10b audit ==="
  grep -E "PLAY RECAP|changed=" /root/rhcsa_journal/lab-10b/task1/rerun.txt || true
  grep -E "PLAY RECAP|changed=" /root/rhcsa_journal/lab-10b/task2/rerun.txt || true
  test -f /tmp/mv-ansible-lab/dst/app.log && echo "mv-target-present"
  test -f /tmp/mv-ansible-lab/dst/service.conf && echo "config-present"
  ls /tmp/mv-ansible-lab/dst/service.conf*~ 2>/dev/null && echo "backup-present"
} | tee /tmp/mv-verify-lab/task2/audit.txt
```

### Concept Card

| Concept | One-line |
|---|---|
| Cross-fs `mv` | Falls back to copy + remove; not one-step atomic rename |
| Inode change signal | Different inode strongly indicates new file created on destination fs |
| Verification discipline | Confirm with `stat`, `df`, `test`, and prior logs |
| 🪤 T10-C | Never trust recap alone; inspect state |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-10c/task2
mkdir -p "$JDIR"
cp /tmp/mv-verify-lab/task2/audit.txt "$JDIR/evidence.txt"
```

---

## Checklist

- [ ] Task 1 proved same-fs inode preservation and hard-link survival
- [ ] Task 2 classified same-fs vs cross-fs and audited Lab 10b artifacts

---

## Related Labs

| Lab | Connection |
|---|---|
| `10a` | Manual `mv` behavior and option drills |
| `10b` | Boundary-safe automation patterns verified here |
