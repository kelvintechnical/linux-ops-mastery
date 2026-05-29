# Lab 09c: Verifying Hard and Soft Links — audit + persistence

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `09a` (RHCSA) → `09b` (Ansible) → **`09c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 verification reflex, RHCE EX294 post-play audit, SRE drift detection, boot incident triage
- **Prerequisite:** Lab 09a and Lab 09b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = state audit, Task 2 = persistence/recovery check)
- **Practice Directory (rotation #09):** `/var/log`
- **Sandbox:** `/tmp/link-lab-09c`
- **Traps rehearsed this lab:** **T17** (masked service link interpretation during recovery), **T18** (wrong assumptions about hard links), **T19** (dangling symlink false confidence from `test -L`)

> **This lab's practice directory is: `/var/log`** — verification examples inspect real links there.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T17 T18 T19"
echo "📁  PRACTICE DIR: /var/log"
echo ""
test -f /root/rhcsa_journal/lab-09a/task2/done.txt && echo "✅ lab-09a complete marker found"
test -f /root/rhcsa_journal/lab-09b/task2/done.txt && echo "✅ lab-09b complete marker found"
find /var/log -maxdepth 2 -type l 2>/dev/null | head -n 5
```

> **STOP — if either done marker is missing, finish 09a/09b first.**

---

## 🎯 Objective

Audit link state without trusting prior task output, then prove the audit is reproducible from persistent journal artifacts after simulated reset conditions.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/link-lab-09c
cat > /tmp/link-lab-09c/expected.txt <<'EOF'
/tmp/link-lab-09b/soft-ansible
/tmp/link-lab-09b/hard-ansible
EOF

# Rehydrate lab-09b targets if that sandbox was cleaned
if test -f /root/rhcsa_journal/lab-09b/playbooks/task1.yml; then
  ansible-playbook /root/rhcsa_journal/lab-09b/playbooks/task1.yml
else
  echo "Missing /root/rhcsa_journal/lab-09b/playbooks/task1.yml — return to Lab 09b Task 1."
fi

ls -la /tmp/link-lab-09c
cat /tmp/link-lab-09c/expected.txt
```

---

## Task 1 — Audit link behavior with RHCSA inspection commands

**Practice directory this task:** `/var/log` and `/tmp/link-lab-09b`

### 🔁 Warm-Up

```bash
ls -l /etc/localtime
readlink -f /etc/localtime
echo "exit was: $?"
```

### Purpose

Use at least three independent commands to verify symlink and hard-link behavior, including dangling detection logic.

### Main command block

```bash
mkdir -p /tmp/link-lab-09c/task1

{
  echo "=== symlink checks ==="
  ls -li /tmp/link-lab-09b/soft-ansible
  readlink /tmp/link-lab-09b/soft-ansible
  readlink -f /tmp/link-lab-09b/soft-ansible
  test -L /tmp/link-lab-09b/soft-ansible && echo "test -L true"
  test -e /tmp/link-lab-09b/soft-ansible && echo "test -e true" || echo "test -e false (dangling)"

  echo "=== hard-link checks ==="
  ls -li /tmp/link-lab-09b/hard-ansible /tmp/link-lab-09b/origin.txt
  stat -c 'inode=%i links=%h %n' /tmp/link-lab-09b/hard-ansible /tmp/link-lab-09b/origin.txt
  inode=$(stat -c '%i' /tmp/link-lab-09b/hard-ansible)
  find /tmp/link-lab-09b -inum "$inode"

  echo "=== T17 recovery marker ==="
  echo "masked units appear as symlinks to /dev/null"
  ls -l /etc/systemd/system/*.service 2>/dev/null | head -n 5
} 2>&1 | tee /tmp/link-lab-09c/task1/audit.txt
```

### Expected outcome

- Symlink path prints with `readlink`
- Hard-link and origin share inode
- `stat -c %h` reflects hard-link count
- `find -inum` lists all names for that inode
- If origin is missing, `test -L` still true while `test -e` false

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-09c/task1
mkdir -p "$JDIR"
cp /tmp/link-lab-09c/task1/audit.txt "$JDIR/audit.txt"
cp /tmp/link-lab-09c/expected.txt "$JDIR/expected.txt"
cat > "$JDIR/done.txt" <<EOF
LAB: lab-09c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 — Persistence + simulated recovery verification

**Practice directory this task:** `/var/log` and `/root/rhcsa_journal`

### 🔁 Warm-Up

```bash
stat -c '%n mountpoint=%m' /tmp /root /root/rhcsa_journal
echo "exit was: $?"
```

### Purpose

Simulate reset of `/tmp` work areas, then prove link-audit artifacts in `/root/rhcsa_journal` still allow verification flow.

### Main command block

```bash
mkdir -p /tmp/link-lab-09c/task2

echo "=== pre-reset snapshot ===" | tee /tmp/link-lab-09c/task2/timeline.txt
find /tmp/link-lab-09c -type f 2>/dev/null | tee -a /tmp/link-lab-09c/task2/timeline.txt

# Simulated reset of tmp workspace
rm -rf /tmp/link-lab-09c/*
mkdir -p /tmp/link-lab-09c
find /tmp/link-lab-09c -type f 2>/dev/null | wc -l | tee -a /root/rhcsa_journal/lab-09c/task2-reset-count.txt

# Reconstruct from persistent journal
JDIR=/root/rhcsa_journal/lab-09c/task2
mkdir -p "$JDIR"
{
  echo "=== post-reset reconstruction ==="
  for f in /root/rhcsa_journal/lab-09c/task1/audit.txt \
           /root/rhcsa_journal/lab-09c/task1/expected.txt \
           /root/rhcsa_journal/lab-09b/playbooks/task1.yml \
           /root/rhcsa_journal/lab-09b/playbooks/task2.yml; do
    test -f "$f" && echo "✅ survived: $f" || echo "❌ missing: $f"
  done

  echo "=== T19 check replay ==="
  test -L /tmp/link-lab-09b/soft-ansible && echo "test -L true" || echo "test -L false"
  test -e /tmp/link-lab-09b/soft-ansible && echo "test -e true" || echo "test -e false"

  echo "=== T17 recovery note ==="
  echo "if service is masked, unmask removes symlink to /dev/null"
} 2>&1 | tee "$JDIR/post-reset-audit.txt"
```

### Trap focus

| Trap | What fails | Reflex |
|---|---|---|
| T17 | Wrongly treating masked state as disabled state | Inspect symlink target and unmask explicitly |
| T18 | Assuming hard links have source/child hierarchy | Treat all hard-link names as peers to one inode |
| T19 | Using only `test -L` in health checks | Pair with `test -e` to detect dangling targets |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-09c/task2
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB: lab-09c
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

### 🧹 Cleanup

```bash
rm -rf /tmp/link-lab-09c
test -d /tmp/link-lab-09c || echo "sandbox gone — clean exit"
```

---

## Lab 09c Checklist (2 tasks)

- [ ] Task 1 — Audited soft/hard links with RHCSA inspection commands
- [ ] Task 2 — Proved journal-based persistence and post-reset replay

---

## 🏁 Lab 09 Trilogy completion check

```bash
find /root/rhcsa_journal/lab-09{a,b,c} -name done.txt | sort
```

Expected: 6 done markers (2 tasks each across 09a/09b/09c).

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
