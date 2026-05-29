# Lab 24c: Verifying `sed` Stream Editing (Capstone) — backup audit + destroy-restore

- **Series:** linux-ops-mastery — Text Processing & Validation
- **Trilogy:** [`24a`](../lab-24a-sed-stream-editor-rhcsa/) (RHCSA hand-typed) → [`24b`](../lab-24b-sed-stream-editor-ansible/) (Ansible equivalent) → **`24c`** (Verify — you are here)
- **Prerequisite:** Lab 24a completed with journal artifacts in `/root/rhcsa_journal/lab-24a/task1` and `task2`
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = audit `.bak` + diff evidence from 24a; Task 2 = destroy-restore and re-run sed as verify user)
- **Practice Directory (rotation #24):** `/var` source context; verification writes in `/tmp/lab24c`
- **Sandbox (Tier B):** `/tmp/lab24c` with `USER=labuser_24_sed`, `GROUP=labgrp_24_sed`, `USER_HOME=/tmp/lab24c/home_labuser_24_sed`
- **Traps rehearsed this lab:** **T24-A** (no backup means no rollback), **T24-B** (missing `g` leaves silent drift), **T41** (destroy-restore skipped), **T44** (closeout residue)

> **This lab's practice directory is: `/var`** — we validate edit patterns against realistic files while preserving safety in sandbox paths.

---

## LAB HEADER BLOCK

```bash
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /var"
echo "⚠️  TRAPS: T24-A T24-B T41 T44"
ls -ld /var /etc/services
ls -la /root/rhcsa_journal/lab-24a/task1 /root/rhcsa_journal/lab-24a/task2
echo "exit was: $?"
```

> **STOP — paste header output. If 24a artifacts are missing, complete 24a first.**

---

## Objective

Take the auditor seat:

1. Prove that 24a used backups (`.bak`) and captured diffs (rollback evidence).
2. Rehearse **T41** destroy-restore: wipe working copy, restore from journal, continue safely.
3. Re-run `sed` as the verify lab user (`sudo -u ${USER}`) and validate ownership/output.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=24
export LAB_SLUG=sed
export SANDBOX=/tmp/lab24c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-24c/task1
mkdir -p /root/rhcsa_journal/lab-24c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
echo "exit was: $?"
```

---

## Task 1 — Audit 24a backup and diff evidence

**Practice directory this task:** `/tmp/lab24c` (reads from 24a journal)

### Warm-Up

```bash
find /root/rhcsa_journal/lab-24a -maxdepth 2 -type f | sort
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab24c/task1.txt
J24A=/root/rhcsa_journal/lab-24a/task1

echo "═══ Part A: required files exist ═══"                          | tee "${TASKLOG}"
for f in \
  "${J24A}/app.conf.before" \
  "${J24A}/app.conf.after" \
  "${J24A}/app.diff" \
  "${J24A}/evidence.txt"
do
  test -s "${f}" && echo "✅ ${f}" || echo "❌ missing ${f}"
done                                                             | tee -a "${TASKLOG}"

echo "═══ Part B: backup still contains old tokens ═══"          | tee -a "${TASKLOG}"
grep -n 'old' "${J24A}/app.conf.before" | head -n 5             | tee -a "${TASKLOG}"

echo "═══ Part C: after-file has new tokens and no old leftovers ═══" | tee -a "${TASKLOG}"
grep -n 'new' "${J24A}/app.conf.after" | head -n 5              | tee -a "${TASKLOG}"
grep -n 'old' "${J24A}/app.conf.after"                           | tee -a "${TASKLOG}" || true

echo "═══ Part D: diff contains old->new transitions ═══"        | tee -a "${TASKLOG}"
grep -nE '^-.*old|^\\+.*new' "${J24A}/app.diff" | head -n 10     | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24c/task1
mkdir -p "${JDIR}"
cp /tmp/lab24c/task1.txt "${JDIR}/evidence.txt"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Task 2 — Destroy-restore + re-run `sed` as verify user

**Practice directory this task:** `/tmp/lab24c`

### Purpose

Destroy current working copy, restore from audited backup, then execute the replacement as `${USER}` to prove ownership and reproducibility.

### Main command block

```bash
TASKLOG=/tmp/lab24c/task2.txt
SRC_BEFORE=/root/rhcsa_journal/lab-24a/task1/app.conf.before
RESTORED=/tmp/lab24c/app.conf

echo "═══ Part A: snapshot + destroy (T41) ═══"                 | tee "${TASKLOG}"
wc -l "${SRC_BEFORE}"                                           | tee -a "${TASKLOG}"
rm -f "${RESTORED}" "${RESTORED}.bak"
test ! -e "${RESTORED}" && echo "✅ destroy clean" || echo "❌ destroy failed" | tee -a "${TASKLOG}"

echo "═══ Part B: restore from 24a journal backup ═══"          | tee -a "${TASKLOG}"
cp "${SRC_BEFORE}" "${RESTORED}"
chown "${USER}:${GROUP}" "${RESTORED}"
stat -c '%U:%G %a %n' "${RESTORED}"                              | tee -a "${TASKLOG}"

echo "═══ Part C: re-run sed AS verify user ═══"                 | tee -a "${TASKLOG}"
sudo -u "${USER}" sed -i.bak 's/old/new/g' "${RESTORED}"
stat -c '%U:%G %a %n' "${RESTORED}" "${RESTORED}.bak"            | tee -a "${TASKLOG}"

echo "═══ Part D: verify transition and trap protection ═══"     | tee -a "${TASKLOG}"
diff -u "${RESTORED}.bak" "${RESTORED}"                          | tee -a "${TASKLOG}"
grep -n 'old' "${RESTORED}"                                      | tee -a "${TASKLOG}" || true
grep -n 'new' "${RESTORED}" | head -n 5                          | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-24c/task2
mkdir -p "${JDIR}"
cp /tmp/lab24c/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab24c/app.conf "${JDIR}/app.conf.after-verify"
cp /tmp/lab24c/app.conf.bak "${JDIR}/app.conf.before-verify"
ls -la "${JDIR}"
echo "exit was: $?"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 24c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"  || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the four `✅` audit lines.**

---

## Lab 24c Checklist (2 tasks + closeout)

- [ ] Task 1: 24a backup and diff artifacts audited and validated
- [ ] Task 2: destroy-restore complete; `sed -i.bak` re-run as `${USER}`; diff evidence captured
- [ ] T41 rehearsal done and T24-A/T24-B safeguards re-proven
- [ ] Section 6 closeout completed with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
