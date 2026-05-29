# Lab 08c: Verifying Copy Results — content + metadata audit

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `08a` (RHCSA) → `08b` (Ansible) → **`08c` (Verify)**
- **Prerequisite:** Labs 08a and 08b completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2
- **Practice Directory (rotation #08):** `/etc/skel` (reference only)
- **Sandbox:** `/tmp/cp-verify-lab`
- **Traps rehearsed this lab:** **T08-A** (assuming metadata preserved without checking) · **T08-B** (confusing recursive data equality with full metadata equality) · **T08-C** (trusting automation output without independent inspection)

> Verification lab rule: trust no prior command output until you prove state with inspection tools.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /etc/skel"
echo "⚠️  TRAP REMINDERS THIS LAB: T08-A T08-B T08-C"
ls -la /etc/skel
```

---

## Objective

Audit copy operations from 08a/08b with RHCSA-grade verification commands:

- content identity (`diff`, `cmp`, `md5sum`)
- metadata fidelity (`stat`, `ls -lZ`)
- link fidelity (`test -L`, `readlink`)
- Ansible outcome sanity (`changed=0` on rerun + actual filesystem checks)

---

## Setup (run once)

```bash
sudo mkdir -p /tmp/cp-verify-lab
sudo cp -a /tmp/cp-lab/src /tmp/cp-verify-lab/src-baseline 2>/dev/null || true
sudo cp -a /tmp/cp-lab/dst-a /tmp/cp-verify-lab/dst-a-snapshot 2>/dev/null || true
sudo cp -a /tmp/cp-ansible-lab /tmp/cp-verify-lab/ansible-snapshot 2>/dev/null || true
ls -la /tmp/cp-verify-lab
```

---

## Task 1 — Verify RHCSA copy outcomes (`cp`, `cp -R`, `cp -a`)

**Practice directory this task:** `/etc/skel` (reference), `/tmp/cp-lab` (audit target)

### Purpose

Prove where plain/recursive copy diverged and where archive copy stayed faithful.

### Main Command Block

```bash
sudo mkdir -p /root/rhcsa_journal/lab-08c/task1

# Content checks
diff /tmp/cp-lab/src/demo.txt /tmp/cp-lab/dst/plain.txt && echo "plain_content_match"
cmp /tmp/cp-lab/src/demo.txt /tmp/cp-lab/dst-a/demo.txt && echo "archive_content_match"
md5sum /tmp/cp-lab/src/demo.txt /tmp/cp-lab/dst/plain.txt /tmp/cp-lab/dst-a/demo.txt

# Metadata checks
stat -c 'src mode=%a owner=%U:%G mtime=%y' /tmp/cp-lab/src/demo.txt
stat -c 'plain mode=%a owner=%U:%G mtime=%y' /tmp/cp-lab/dst/plain.txt
stat -c 'dst-a mode=%a owner=%U:%G mtime=%y' /tmp/cp-lab/dst-a/demo.txt
ls -lZ /tmp/cp-lab/src/demo.txt /tmp/cp-lab/dst/plain.txt /tmp/cp-lab/dst-a/demo.txt

# Link checks (T08-B focus)
test -L /tmp/cp-lab/dst-R/demo-link && echo "dst-R-link=yes" || echo "dst-R-link=no"
test -L /tmp/cp-lab/dst-a/demo-link && echo "dst-a-link=yes" || echo "dst-a-link=no"
readlink /tmp/cp-lab/dst-a/demo-link
```

### Journal Write

```bash
{
  echo "lab=08c task=1"
  echo "when=$(date -Is)"
  test -L /tmp/cp-lab/dst-R/demo-link && echo "dstR_symlink=yes" || echo "dstR_symlink=no"
  test -L /tmp/cp-lab/dst-a/demo-link && echo "dstA_symlink=yes" || echo "dstA_symlink=no"
  stat -c 'src=%Y plain=%Y dsta=%Y' /tmp/cp-lab/src/demo.txt /tmp/cp-lab/dst/plain.txt /tmp/cp-lab/dst-a/demo.txt
} | sudo tee /root/rhcsa_journal/lab-08c/task1/done.txt
```

---

## Task 2 — Verify Ansible copy outcomes independently

**Practice directory this task:** `/etc/skel` (reference), `/tmp/cp-ansible-lab` (audit target)

### Purpose

Validate that Ansible-produced copies are correct by state inspection, not by trusting play recap alone.

### Main Command Block

```bash
sudo mkdir -p /root/rhcsa_journal/lab-08c/task2

# Re-run idempotence signal (should trend changed=0 if state converged)
ansible-playbook /root/rhcsa_journal/lab-08b/playbooks/task2.yml | tee /tmp/cp-verify-lab/task2-rerun.log

# Independent file checks
diff /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/input.txt && echo "ansible_input_match"
diff /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/preserved.txt && echo "ansible_preserved_match"
stat -c 'src_mode=%a dst_mode=%a pres_mode=%a' /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/input.txt /tmp/cp-ansible-lab/dst/preserved.txt
ls -l /tmp/cp-ansible-lab/dst/preserved.txt*

# Optional SELinux visibility
ls -lZ /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/preserved.txt
```

### Trap Calls

- **T08-C:** `changed=0` without inspection is not proof; always inspect files directly.
- **T08-A/T08-B:** verify mode, mtime, and link expectations explicitly.

### Journal Write

```bash
{
  echo "lab=08c task=2"
  echo "when=$(date -Is)"
  grep -E 'changed=[0-9]+' /tmp/cp-verify-lab/task2-rerun.log | tail -n 1
  stat -c 'src=%a dst=%a preserved=%a' /tmp/cp-ansible-lab/src/input.txt /tmp/cp-ansible-lab/dst/input.txt /tmp/cp-ansible-lab/dst/preserved.txt
} | sudo tee /root/rhcsa_journal/lab-08c/task2/done.txt
```

---

## Lab 08c Checklist

- [ ] Task 1: audited `cp`, `cp -R`, and `cp -a` content + metadata + symlink behavior
- [ ] Task 2: audited Ansible copy outcomes with independent file inspection

---

## Trilogy Completion Check

```bash
ls /root/rhcsa_journal/lab-08a/task{1,2}/done.txt
ls /root/rhcsa_journal/lab-08b/task{1,2}/done.txt
ls /root/rhcsa_journal/lab-08c/task{1,2}/done.txt
```

If all six files exist, Lab 08 trilogy is complete.
