# Lab 23a: Comparing File Differences (RHCSA) - `diff`, `diff -u`, `diff -r`, `diff -y`, `diff --brief`, `sdiff`, `comm`, `vimdiff`

- **Series:** linux-ops-mastery - File Inspection and Verification
- **Trilogy:** **`23a` (RHCSA - you are here)** -> `23b` (Ansible) -> `23c` (Verify)
- **Career arcs covered:** RHCSA EX200 (prove config edits before restart), RHCE EX294 (pair shell diffs with playbook output), SRE (rapid config drift detection), DevOps (release artifact comparison)
- **Prerequisite:** Labs 08a/08c (copy and verify reflex), Lab 19a (`cat` baselines), and basic `vi` editing
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 single-file unified diff, Task 2 recursive snapshot compare + exit code handling)
- **Practice Directory (rotation #23):** `/root`
- **Sandbox (Tier B):** `/tmp/lab23a` with `USER=labuser_23_diff`, `GROUP=labgrp_23_diff`
- **Traps rehearsed this lab:** **T23-A** (`diff` exit codes are status signals, not failures: `0` same, `1` different, `2` error) · **T23-B** (`diff -r` with symlinks can compare link targets you did not intend) · **T41** (skip destroy-restore drill) · **T44** (forget teardown audit and leave lab accounts behind)

> **This lab's practice directory is `/root`**. Work files are built in `/tmp/lab23a`; journal artifacts persist in `/root/rhcsa_journal/lab-23a/`.

---

## LAB HEADER BLOCK

```bash
echo "ENV:   ${ENV:-DECLARE_ME}"
echo "DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "TRAP REMINDERS THIS LAB: T23-A T23-B T41 T44"
echo "PRACTICE DIR: /root"
```

> **STOP - paste header output before setup.**

---

## Objective

Build a reliable `diff` reflex for exam and production troubleshooting:

1. Compare one config file against its modified copy with unified output (`diff -u`) and explain the hunk.
2. Compare two directory snapshots recursively (`diff -r`) and interpret exit status correctly.
3. Use compact signal modes (`--brief`, `-y`, `sdiff`, `comm`) when full hunks are too noisy.
4. Use `vimdiff` to inspect and merge with keyboard-level speed.

---

## Core Concept: `diff` exit code is the verdict

`diff` is unusual because exit status `1` is often "success with differences", not command failure:

- `0` = files are identical
- `1` = files/directories differ
- `2` = trouble reading path, permission, or invalid option

This is **T23-A**. If you treat `1` as fatal in scripts, you misclassify normal drift as an error.

---

## Quick Reference

| Command | Meaning | Best use |
|---|---|---|
| `diff A B` | Default line diff | Fast single-file compare |
| `diff -u A B` | Unified diff with context | Patch-like readable output |
| `diff -r D1 D2` | Recursive directory compare | Snapshot drift checks |
| `diff -y A B` | Side-by-side view | Human review on wide terminal |
| `diff --brief A B` | Report only "same/different" | Script gate conditions |
| `sdiff A B` | Side-by-side with merge cues | Line-level reconciliation |
| `comm F1 F2` | 3-column compare (sorted files) | Set/list comparison |
| `vimdiff A B` | Visual interactive diff | Manual triage and merge |

---

## Lab-Wide Setup - Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=23
export LAB_SLUG=diff
export SANDBOX=/tmp/lab23a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-23a/task1 /root/rhcsa_journal/lab-23a/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> **STOP - paste the `id` + `ls -ld` lines before Task 1.**

---

## Task 1 - Single-file diff with `diff -u`

**Practice directory this task:** `/root` (reference) + `/tmp/lab23a` (work)

### Warm-Up

```bash
test -f /etc/ssh/sshd_config && echo "sshd_config exists"
cp -p /etc/ssh/sshd_config /tmp/lab23a/sshd.original
ls -l /tmp/lab23a/sshd.original
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Purpose

Create a backup, make controlled edits, and read the unified diff as if you are reviewing a teammate's patch.

### Main command block

```bash
TASKLOG=/tmp/lab23a/task1.txt

# Required step from lab prompt:
cp /etc/ssh/sshd_config /tmp/lab23a/sshd.bak
cp /tmp/lab23a/sshd.bak /tmp/lab23a/sshd.modified

# Controlled edits in modified copy only
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /tmp/lab23a/sshd.modified
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /tmp/lab23a/sshd.modified
echo "# lab23a marker $(date -Is)" >> /tmp/lab23a/sshd.modified

diff -u /tmp/lab23a/sshd.bak /tmp/lab23a/sshd.modified | tee "${TASKLOG}"
DIFF_EXIT=${PIPESTATUS[0]}
echo "diff -u exit code: ${DIFF_EXIT}" | tee -a "${TASKLOG}"

# Additional compare views
diff -y /tmp/lab23a/sshd.bak /tmp/lab23a/sshd.modified | head -n 25 | tee -a "${TASKLOG}"
sdiff /tmp/lab23a/sshd.bak /tmp/lab23a/sshd.modified | head -n 25 | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected output highlights

- Unified headers start with `---` and `+++`
- Hunk headers look like `@@ -old,+new @@`
- Removed lines begin with `-`, added lines with `+`
- `diff -u exit code` should be `1` (difference found, not failure)

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-23a/task1
mkdir -p "${JDIR}"
cp /tmp/lab23a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab23a/sshd.bak "${JDIR}/sshd.bak"
cp /tmp/lab23a/sshd.modified "${JDIR}/sshd.modified"
```

---

## Task 2 - Recursive snapshot compare with `diff -r` and `--brief`

**Practice directory this task:** `/root` (journal) + `/tmp/lab23a` (snapshots)

### Warm-Up

```bash
mkdir -p /tmp/lab23a/snapA/etc /tmp/lab23a/snapB/etc
cp -a /etc/ssh /tmp/lab23a/snapA/etc/
cp -a /etc/ssh /tmp/lab23a/snapB/etc/
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Purpose

Compare two directory trees, capture exit status correctly (T23-A), and demonstrate concise drift output using `--brief`.

### Main command block

```bash
TASKLOG=/tmp/lab23a/task2.txt

# Introduce deliberate drift in snapshot B
echo "Lab23 snapshot delta $(date -Is)" >> /tmp/lab23a/snapB/etc/ssh/ssh_config
rm -f /tmp/lab23a/snapB/etc/ssh/ssh_config.d/* 2>/dev/null || true

# T23-B safe mode: avoid traversing unexpected symlink targets
find /tmp/lab23a/snapA -type l -ls | tee "${TASKLOG}"
find /tmp/lab23a/snapB -type l -ls | tee -a "${TASKLOG}"

diff -r /tmp/lab23a/snapA /tmp/lab23a/snapB | tee -a "${TASKLOG}"
R_EXIT=${PIPESTATUS[0]}
echo "diff -r exit code: ${R_EXIT}" | tee -a "${TASKLOG}"

diff -r --brief /tmp/lab23a/snapA /tmp/lab23a/snapB | tee -a "${TASKLOG}"
BRIEF_EXIT=${PIPESTATUS[0]}
echo "diff -r --brief exit code: ${BRIEF_EXIT}" | tee -a "${TASKLOG}"

# comm demonstration (requires sorted single-line files)
printf "AllowUsers\nPasswordAuthentication\nPermitRootLogin\n" | sort > /tmp/lab23a/keysA.txt
printf "AllowUsers\nPermitRootLogin\nPubkeyAuthentication\n" | sort > /tmp/lab23a/keysB.txt
comm /tmp/lab23a/keysA.txt /tmp/lab23a/keysB.txt | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-23a/task2
mkdir -p "${JDIR}"
cp /tmp/lab23a/task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout - Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null
getent passwd "${USER}" >/dev/null 2>&1 && userdel -r "${USER}" 2>/dev/null
getent group  "${GROUP}" >/dev/null 2>&1 && groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

echo "-- Lab 23a cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"

set -e
```

> **STOP - do not declare complete unless all four audit lines are `OK`.**

---

## Lab 23a Checklist

- [ ] Tier B setup completed (`labuser_23_diff`, `labgrp_23_diff`, `/tmp/lab23a`)
- [ ] Task 1 produced unified diff from `/tmp/lab23a/sshd.bak` vs `/tmp/lab23a/sshd.modified`
- [ ] Task 1 captured `diff -u` exit code and recognized `1` as "differences found"
- [ ] Task 2 ran `diff -r` and `diff -r --brief` with captured exit status
- [ ] Task 2 used at least one of `diff -y`, `sdiff`, `comm`, or `vimdiff`
- [ ] Section 6 closeout audit showed no Tier B residue (T44 defended)

---

## Related Labs

| Lab | Connection |
|---|---|
| `23b` | Expresses this comparison flow in Ansible playbooks (`backup` and `--diff`) |
| `23c` | Auditor seat: replay, validate artifacts, run destroy-restore drill (T41) |
| `08c` | Verification mindset and evidence-first journaling |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
