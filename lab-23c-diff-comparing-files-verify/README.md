# Lab 23c: Verifying File Differences - audit captures and destroy-restore re-diff

- **Series:** linux-ops-mastery - File Inspection and Verification
- **Trilogy:** `23a` (RHCSA) -> `23b` (Ansible) -> **`23c` (Verify - you are here)**
- **Career arcs covered:** RHCSA/RHCE verification muscle, SRE post-change audits, incident rollback validation
- **Prerequisite:** Lab 23a and Lab 23b completed
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2 (Task 1 audit 23a diff artifacts, Task 2 destroy-restore and re-diff drill)
- **Practice Directory (rotation #23):** `/root`
- **Sandbox (Tier B):** `/tmp/lab23c` with `USER=labuser_23_diff`, `GROUP=labgrp_23_diff`
- **Traps rehearsed this lab:** **T23-A** (`diff` status interpretation), **T23-B** (recursive compare + symlink caution), **T41** (skip destroy-restore drill), **T44** (skip teardown audit)

> **This verification lab is the auditor seat:** do not trust memory, only trust captured artifacts and reproducible reruns.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "PRACTICE DIR: /root"
echo "TRAP REMINDERS THIS LAB: T23-A T23-B T41 T44"
test -f /root/rhcsa_journal/lab-23a/task1/evidence.txt && echo "OK lab-23a task1 evidence present"
test -f /root/rhcsa_journal/lab-23a/task2/evidence.txt && echo "OK lab-23a task2 evidence present"
```

> **STOP - if either evidence file is missing, complete 23a first.**

---

## Objective

Prove that your diff workflow is durable and repeatable:

1. Audit Lab 23a evidence and confirm it demonstrates required exit codes and compare modes.
2. Run a destroy-restore drill, reproduce differences, and verify your compare tools still catch drift.

---

## Verification Reference

| Check | Command |
|---|---|
| Exit code semantics | `grep -E 'exit code: (0|1|2)' evidence.txt` |
| Unified diff present | `rg '^@@|^\-\-\-|^\+\+\+' evidence.txt` |
| Recursive drift compare | `diff -r --brief snap1 snap2` |
| Side-by-side compare | `diff -y A B` or `sdiff A B` |
| Sorted list compare | `comm F1 F2` |
| Visual manual compare | `vimdiff A B` |

---

## Lab-Wide Setup - Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=23
export LAB_SLUG=diff
export SANDBOX=/tmp/lab23c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-23c/task1 /root/rhcsa_journal/lab-23c/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 - Audit Lab 23a diff captures

**Practice directory this task:** `/root/rhcsa_journal/lab-23a`

### Purpose

Validate that previous evidence proves required behaviors instead of only showing command output.

### Main command block

```bash
TASKLOG=/tmp/lab23c/task1.txt

echo "=== audit lab-23a task1 evidence ===" | tee "${TASKLOG}"
test -f /root/rhcsa_journal/lab-23a/task1/evidence.txt && echo "OK task1 evidence file exists" | tee -a "${TASKLOG}"
rg '^--- |^\+\+\+ |^@@ ' /root/rhcsa_journal/lab-23a/task1/evidence.txt | tee -a "${TASKLOG}"
rg 'diff -u exit code: 1|diff -u exit code: 0|diff -u exit code: 2' /root/rhcsa_journal/lab-23a/task1/evidence.txt | tee -a "${TASKLOG}"

echo "=== audit lab-23a task2 evidence ===" | tee -a "${TASKLOG}"
test -f /root/rhcsa_journal/lab-23a/task2/evidence.txt && echo "OK task2 evidence file exists" | tee -a "${TASKLOG}"
rg 'diff -r exit code:|diff -r --brief exit code:' /root/rhcsa_journal/lab-23a/task2/evidence.txt | tee -a "${TASKLOG}"
rg 'Only in |Files .* differ' /root/rhcsa_journal/lab-23a/task2/evidence.txt | tee -a "${TASKLOG}"

# T23-B check: symlink awareness line captured
rg 'type l|symlink|find .* -type l' /root/rhcsa_journal/lab-23a/task2/evidence.txt | tee -a "${TASKLOG}" || true

echo "Audit complete at $(date -Is)" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab23c/task1.txt /root/rhcsa_journal/lab-23c/task1/evidence.txt
```

---

## Task 2 - Destroy-restore and re-diff drill

**Practice directory this task:** `/root` + `/tmp/lab23c`

### Purpose

Defend against **T41** by proving you can rebuild, reintroduce drift, and still detect it with the same compare methods.

### Main command block

```bash
TASKLOG=/tmp/lab23c/task2.txt

# Destroy
rm -rf /tmp/lab23c/drillA /tmp/lab23c/drillB
mkdir -p /tmp/lab23c/drillA /tmp/lab23c/drillB

# Restore clean state
cp -a /etc/ssh /tmp/lab23c/drillA/
cp -a /etc/ssh /tmp/lab23c/drillB/

# Reintroduce controlled drift
echo "# drill delta $(date -Is)" >> /tmp/lab23c/drillB/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /tmp/lab23c/drillB/ssh/sshd_config

# Re-diff with multiple modes
diff -u /tmp/lab23c/drillA/ssh/sshd_config /tmp/lab23c/drillB/ssh/sshd_config | tee "${TASKLOG}"
echo "diff -u exit code: ${PIPESTATUS[0]}" | tee -a "${TASKLOG}"

diff -r --brief /tmp/lab23c/drillA /tmp/lab23c/drillB | tee -a "${TASKLOG}"
echo "diff -r --brief exit code: ${PIPESTATUS[0]}" | tee -a "${TASKLOG}"

diff -y /tmp/lab23c/drillA/ssh/sshd_config /tmp/lab23c/drillB/ssh/sshd_config | head -n 20 | tee -a "${TASKLOG}"
sdiff /tmp/lab23c/drillA/ssh/sshd_config /tmp/lab23c/drillB/ssh/sshd_config | head -n 20 | tee -a "${TASKLOG}"

# Optional interactive visual proof
echo "Optional manual step: vimdiff /tmp/lab23c/drillA/ssh/sshd_config /tmp/lab23c/drillB/ssh/sshd_config" | tee -a "${TASKLOG}"
```

### Journal write

```bash
cp /tmp/lab23c/task2.txt /root/rhcsa_journal/lab-23c/task2/evidence.txt
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
getent passwd "${USER}" >/dev/null 2>&1 && userdel -r "${USER}" 2>/dev/null
getent group "${GROUP}" >/dev/null 2>&1 && groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "-- Lab 23c cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"
set -e
```

> **STOP - all four audit lines must be `OK` to close T44.**

---

## Lab 23c Checklist

- [ ] Task 1 validated presence and quality of Lab 23a evidence captures
- [ ] Task 1 confirmed unified and recursive diff traces are present
- [ ] Task 2 completed destroy-restore drill (T41 defended)
- [ ] Task 2 re-ran `diff -u` and `diff -r --brief` with captured exit codes
- [ ] Task 2 ran at least one side-by-side compare (`diff -y` or `sdiff`)
- [ ] Section 6 closeout produced four `OK` lines

---

## Related Labs

| Lab | Connection |
|---|---|
| `23a` | Original RHCSA manual diff capture this lab audits |
| `23b` | Ansible diff preview and backup workflows validated here |
| `08c` | Prior verification pattern for attribute and content proof |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
