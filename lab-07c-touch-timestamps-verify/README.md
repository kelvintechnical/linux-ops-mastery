# Lab 07c: Touch + Timestamps (Verify) — audit shell vs Ansible results

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `07a` (RHCSA) -> `07b` (Ansible) -> `07c` (Verify)
- **Prerequisite:** Labs 07a and 07b complete
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2
- **Practice Directory (rotation #07):** `/var/log` + `/tmp/touch-lab` + `/tmp/touch-ansible-lab`
- **Traps rehearsed this lab:** **T07** (ctime vs mtime confusion in audits), **T08** (invalid time format causes false verification assumptions)

---

## Objective

Validate timestamp work from both tracks:

1. Verify shell-created artifacts from 07a with `stat` and `find`.
2. Verify Ansible-managed artifacts from 07b and compare expected behavior (`fixed` vs `rolling`).

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-07c/{task1,task2}
echo "07a done files:"
ls -l /root/rhcsa_journal/lab-07a/task*/done.txt
echo "07b done files:"
ls -l /root/rhcsa_journal/lab-07b/task*/done.txt
echo "exit was: $?"
```

---

## Task 1 — Verify RHCSA shell timestamp evidence

**Practice directory:** `/var/log` and `/tmp/touch-lab`

### Warm-Up

```bash
test -d /tmp/touch-lab && echo "/tmp/touch-lab present"
find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null | head -n 5
echo "exit was: $?"
```

### Purpose

Confirm timestamp manipulation from 07a is still visible and searchable.

### Main command block

```bash
{
  echo "=== stat checks ==="
  stat -c '%n atime=%x mtime=%y ctime=%z' \
    /tmp/touch-lab/t08-format.txt \
    /tmp/touch-lab/t-d.txt \
    /tmp/touch-lab/t-r.txt

  echo "=== mtime filters ==="
  find /tmp/touch-lab -type f -mtime +7 | sort
  find /tmp/touch-lab -type f -mmin -60 | sort
  find /tmp/touch-lab -type f -newer /tmp/touch-lab/older-8d.log | sort

  echo "=== /var/log recency sample ==="
  find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null | head -n 5
} 2>&1 | tee /root/rhcsa_journal/lab-07c/task1/evidence.txt

echo "exit was: $?"
```

### Checkpoint

- T07 guard: When comparing "last edited," inspect `mtime` (`%y`) first, not `ctime` (`%z`).
- T08 guard: If expected dates do not match, confirm original `touch -t` string had full `[[CC]YY]MMDDhhmm[.ss]`.

### Journal write

```bash
cat > /root/rhcsa_journal/lab-07c/task1/done.txt <<EOF
LAB: lab-07c
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

> **STOP - confirm evidence file contains at least one `find` result line from `/tmp/touch-lab`.**

---

## Task 2 — Verify Ansible timestamp behavior

**Practice directory:** `/tmp/touch-ansible-lab` and `/var/log` (context)

### Warm-Up

```bash
test -f /tmp/touch-ansible-lab/fixed.txt && echo "fixed exists"
test -f /tmp/touch-ansible-lab/rolling.txt && echo "rolling exists"
echo "exit was: $?"
```

### Purpose

Audit that:

- `fixed.txt` still reflects the declared historical timestamp intent.
- `rolling.txt` behaves like "touch now" and keeps moving.

### Main command block

```bash
{
  echo "=== fixed + rolling stat ==="
  stat -c '%n atime=%x mtime=%y ctime=%z' \
    /tmp/touch-ansible-lab/fixed.txt \
    /tmp/touch-ansible-lab/rolling.txt

  echo "=== date prefix checks ==="
  stat -c 'fixed mtime=%y' /tmp/touch-ansible-lab/fixed.txt | cut -d' ' -f1
  stat -c 'fixed atime=%x' /tmp/touch-ansible-lab/fixed.txt | cut -d' ' -f1

  echo "=== compare with recent ansible logs ==="
  grep -E 'fixed changed=|rolling changed=' /root/rhcsa_journal/lab-07b/task2/op.txt 2>/dev/null || true

  echo "=== /var/log reference search ==="
  find /var/log -maxdepth 1 -type f -mmin -30 2>/dev/null | head -n 5
} 2>&1 | tee /root/rhcsa_journal/lab-07c/task2/evidence.txt

echo "exit was: $?"
```

### Journal write

```bash
cat > /root/rhcsa_journal/lab-07c/task2/done.txt <<EOF
LAB: lab-07c
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

### Cleanup

```bash
# Optional cleanup after full trilogy verification:
# rm -rf /tmp/touch-lab /tmp/touch-ansible-lab
ls -ld /tmp/touch-lab /tmp/touch-ansible-lab 2>/dev/null
```

---

## Lab 07c Checklist

- [ ] Task 1 - verified 07a timestamp artifacts with `stat` and `find`
- [ ] Task 2 - verified 07b fixed vs rolling timestamp behavior
- [ ] Evidence and done files saved under `/root/rhcsa_journal/lab-07c/task1` and `task2`

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
