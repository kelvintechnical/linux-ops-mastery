# Lab 07b: Touch + Timestamps (Ansible) — `ansible.builtin.file: state=touch`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `07a` (RHCSA) -> `07b` (Ansible) -> `07c` (Verify)
- **Prerequisite:** Lab 07a complete
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #07):** `/var/log` (read-only context) + `/tmp/touch-ansible-lab` (writes)
- **Traps rehearsed this lab:** **T07** (assuming ctime is "last edit"), **T08** (wrong timestamp string format)

> This lab mirrors manual `touch` operations with `ansible.builtin.file`.

---

## Objective

Translate shell timestamp work into declarative Ansible tasks:

1. Create files with `state=touch` and explicit `modification_time` / `access_time`.
2. Prove idempotence behavior: explicit timestamps can settle to `changed=false`; default touch-style behavior continues changing.

---

## Reference mapping

| Shell | Ansible |
|---|---|
| `touch FILE` | `ansible.builtin.file: path=FILE state=touch` |
| `touch -t 202401151230.00 FILE` | `modification_time: "202401151230.00"` |
| `touch -a -t ... FILE` | `access_time: "..."` |
| `stat -c '%x %y %z' FILE` | `ansible.builtin.stat` + `debug` |

> Timestamp format used by module defaults to `%Y%m%d%H%M.%S`.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /root/rhcsa_journal/lab-07b/{task1,task2,playbooks}
mkdir -p /tmp/touch-ansible-lab
ansible --version | head -n 1
echo "exit was: $?"
```

Copy playbooks from this folder into `/root/rhcsa_journal/lab-07b/playbooks/` or run them directly from this repo path.

---

## Task 1 — Create timestamp-controlled files declaratively

**Practice directory:** `/var/log` (warm-up reads) and `/tmp/touch-ansible-lab` (writes)

### Warm-Up

```bash
ls -lt /var/log | head -n 5
test -d /tmp/touch-ansible-lab && echo "sandbox OK"
echo "exit was: $?"
```

### Purpose

Run one playbook that creates:

- `fixed.txt` with explicit atime/mtime.
- `rolling.txt` using current time behavior (similar to plain `touch`).

### Run

```bash
ansible-playbook \
  /run/media/redhat/Seagate\ Portable\ Drive/Linux/linux-ops-mastery/lab-07b-touch-timestamps-ansible/playbooks/task1.yml \
  2>&1 | tee /root/rhcsa_journal/lab-07b/task1/op.txt

stat -c '%n atime=%x mtime=%y ctime=%z' /tmp/touch-ansible-lab/fixed.txt /tmp/touch-ansible-lab/rolling.txt
echo "exit was: $?"
```

### Journal write

```bash
cat > /root/rhcsa_journal/lab-07b/task1/done.txt <<EOF
LAB: lab-07b
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

> **STOP - confirm `fixed.txt` date includes 2024-01-15 before Task 2.**

---

## Task 2 — Idempotence check + timestamp verification

**Practice directory:** `/tmp/touch-ansible-lab` and `/var/log` (context)

### Warm-Up

```bash
stat -c '%n mtime=%y' /tmp/touch-ansible-lab/fixed.txt /tmp/touch-ansible-lab/rolling.txt
find /var/log -maxdepth 1 -type f -mtime -1 2>/dev/null | head -n 3
echo "exit was: $?"
```

### Purpose

Re-run with assertions:

- `fixed.txt` should report stable target times.
- `rolling.txt` should show a fresh mtime update.

### Run

```bash
ansible-playbook \
  /run/media/redhat/Seagate\ Portable\ Drive/Linux/linux-ops-mastery/lab-07b-touch-timestamps-ansible/playbooks/task2.yml \
  2>&1 | tee /root/rhcsa_journal/lab-07b/task2/op.txt

stat -c '%n atime=%x mtime=%y ctime=%z' /tmp/touch-ansible-lab/fixed.txt /tmp/touch-ansible-lab/rolling.txt
echo "exit was: $?"
```

### Trap notes

- **T07:** When mode/owner changes, ctime (`%z`) changes even if mtime stays fixed.
- **T08:** If `modification_time` string is malformed, module fails or sets unintended times.

### Journal write

```bash
cat > /root/rhcsa_journal/lab-07b/task2/done.txt <<EOF
LAB: lab-07b
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

### Cleanup

```bash
# Leave /tmp/touch-ansible-lab for verification lab 07c.
ls -l /tmp/touch-ansible-lab
```

---

## Lab 07b Checklist

- [ ] Task 1 - `ansible.builtin.file state=touch` created `fixed.txt` and `rolling.txt`
- [ ] Task 2 - playbook validated explicit timestamp behavior vs rolling timestamp behavior
- [ ] Journal evidence exists in `/root/rhcsa_journal/lab-07b/task1` and `task2`

---

## Author

**Kelvin R. Tobias** — [kelvinintech.com](https://kelvinintech.com)
