# Lab 18c: Verify Located Command Documentation (Capstone) — Audit + Destroy-Restore Drill

- **Series:** linux-ops-mastery — Package Intelligence & Documentation
- **Trilogy:** [`18a`](../lab-18a-locate-command-docs-rhcsa/) (RHCSA) → [`18b`](../lab-18b-locate-command-docs-ansible/) (Ansible) → **`18c`** (Verify capstone)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = audit 18a evidence files · Task 2 = destroy-restore drill)
- **Practice Directory (rotation #18):** `/lib64` (reference context); docs evidence under `/tmp/lab18a` + journal
- **Sandbox (Tier B):** `/tmp/lab18c` with `USER=labuser_18_doclocate`, `GROUP=labgrp_18_doclocate`, `USER_HOME=/tmp/lab18c/home_labuser_18_doclocate`
- **Traps rehearsed this lab:** **T18-A** (`rpm -qd` audit) · **T18-B** (pattern quality audit) · **T41** (destroy-restore) · **T44** (final teardown audit completeness)

> **Mission:** prove 18a artifacts are correct, then prove they are recoverable after deletion.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /lib64"
echo "🕒  TIME:  $(date -Is)"
echo "⚠️  TRAP REMINDERS THIS LAB: T18-A T18-B T41 T44"
ls -ld /lib64 /usr/share/doc /root/rhcsa_journal 2>/dev/null
```

---

## Objective

1. Audit 18a evidence for completeness and semantic correctness.
2. Cross-check docs discovery from both RPM metadata and filesystem pattern search.
3. Execute full destroy-restore drill and verify restored evidence integrity.

---

## Concept: Verify Means "Can You Re-Prove It?"

Audit is not just "files exist." It is:

- Correct command lineage (`rpm -qf` → `rpm -qd`)
- Correct discovery path (`find /usr/share/doc ... '*grep*'`)
- Correct trap controls (T18-A/T18-B)
- Recoverability after wipe (T41)

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=18
export LAB_SLUG=doclocate
export SANDBOX=/tmp/lab18c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-18c/task1
mkdir -p /root/rhcsa_journal/lab-18c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-18a
```

---

## Task 1 — Audit 18a evidence files

### Warm-Up

```bash
find /root/rhcsa_journal/lab-18a -type f | sort
ls -la /root/rhcsa_journal/lab-18a/task1 /root/rhcsa_journal/lab-18a/task2
```

### Purpose

Validate 18a produced the right artifacts and that they prove the expected commands actually ran.

### Main command block

```bash
TASKLOG=/tmp/lab18c/task1.txt
A_JDIR=/root/rhcsa_journal/lab-18a

echo "═══ Part A: completeness audit ═══" | tee "${TASKLOG}"
for f in \
  "${A_JDIR}/task1/evidence.txt" \
  "${A_JDIR}/task1/output.txt" \
  "${A_JDIR}/task2/evidence.txt" \
  "${A_JDIR}/task2/grep-doc-hits.txt"
do
  if test -s "${f}"; then
    echo "✅ ${f}" | tee -a "${TASKLOG}"
  else
    echo "❌ missing-or-empty: ${f}" | tee -a "${TASKLOG}"
  fi
done

echo "═══ Part B: T18-A semantic check (docs-only) ═══" | tee -a "${TASKLOG}"
grep -E 'rpm -qd|package=' "${A_JDIR}/task1/evidence.txt" | tee -a "${TASKLOG}"
grep -q 'rpm -qd' "${A_JDIR}/task1/evidence.txt" \
  && echo "✅ evidence references rpm -qd" \
  || echo "❌ rpm -qd reference missing" | tee -a "${TASKLOG}"

echo "═══ Part C: T18-B pattern check ═══" | tee -a "${TASKLOG}"
HIT_COUNT=$(wc -l < "${A_JDIR}/task2/grep-doc-hits.txt")
echo "grep-doc-hit-count=${HIT_COUNT}" | tee -a "${TASKLOG}"
test "${HIT_COUNT}" -gt 0 \
  && echo "✅ grep pattern produced hits" \
  || echo "❌ grep pattern produced zero hits" | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| completeness checks | prove required files exist and are non-empty |
| semantic grep checks | verify evidence actually contains expected commands |
| hit-count checks | detect broken search patterns |
| **🪤 T18-A/T18-B** | both become explicit pass/fail conditions |

### Journal write

```bash
LAB=lab-18c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18c/task1.txt "${JDIR}/evidence.txt"
```

---

## Task 2 — Destroy-Restore Drill (T41)

### Warm-Up

```bash
ls -la /tmp/lab18a /tmp/lab18c 2>/dev/null
sha256sum /root/rhcsa_journal/lab-18a/task1/output.txt /root/rhcsa_journal/lab-18a/task2/grep-doc-hits.txt
```

### Purpose

Delete working copies, restore from journal artifacts, and verify hash + line-count integrity.

### Main command block

```bash
TASKLOG=/tmp/lab18c-task2.txt
RESTORE=/tmp/lab18c/restore
A_JDIR=/root/rhcsa_journal/lab-18a

echo "═══ Part A: snapshot hashes ═══" | tee "${TASKLOG}"
H1=$(sha256sum "${A_JDIR}/task1/output.txt" | awk '{print $1}')
H2=$(sha256sum "${A_JDIR}/task2/grep-doc-hits.txt" | awk '{print $1}')
echo "task1-output.sha256=${H1}" | tee -a "${TASKLOG}"
echo "task2-hits.sha256=${H2}"   | tee -a "${TASKLOG}"

echo "═══ Part B: destroy working copies ═══" | tee -a "${TASKLOG}"
rm -rf /tmp/lab18a /tmp/lab18c
test ! -d /tmp/lab18a -a ! -d /tmp/lab18c \
  && echo "✅ destroy clean" \
  || echo "❌ destroy incomplete" | tee -a "${TASKLOG}"

echo "═══ Part C: restore from journal ═══" | tee -a "${TASKLOG}"
mkdir -p "${RESTORE}"
cp "${A_JDIR}/task1/output.txt"        "${RESTORE}/output-restored.txt"
cp "${A_JDIR}/task2/grep-doc-hits.txt" "${RESTORE}/hits-restored.txt"

RH1=$(sha256sum "${RESTORE}/output-restored.txt" | awk '{print $1}')
RH2=$(sha256sum "${RESTORE}/hits-restored.txt"   | awk '{print $1}')
echo "restored-output.sha256=${RH1}" | tee -a "${TASKLOG}"
echo "restored-hits.sha256=${RH2}"   | tee -a "${TASKLOG}"

test "${H1}" = "${RH1}" && echo "✅ output hash matches" || echo "❌ output hash mismatch" | tee -a "${TASKLOG}"
test "${H2}" = "${RH2}" && echo "✅ hits hash matches"   || echo "❌ hits hash mismatch"   | tee -a "${TASKLOG}"

echo "restored-output-lines=$(wc -l < "${RESTORE}/output-restored.txt")" | tee -a "${TASKLOG}"
echo "restored-hits-lines=$(wc -l < "${RESTORE}/hits-restored.txt")"     | tee -a "${TASKLOG}"

echo "exit was: $?" | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| snapshot hash | immutable fingerprint before destruction |
| destroy phase | proves no hidden dependency on live temp files |
| restore phase | journal is operational backup source |
| hash comparison | verifies byte-level restore integrity |
| **🪤 T41** | destroy-restore drill is mandatory, not optional |

### Journal write

```bash
LAB=lab-18c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18c-task2.txt "${JDIR}/evidence.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 18c cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 18c Checklist (2 tasks + closeout)

- [ ] Task 1 audited all required 18a evidence files and trap semantics
- [ ] Task 2 completed destroy-restore with hash integrity checks
- [ ] T41 drill completed and logged
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
