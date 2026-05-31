# Lab 18a: Locate Command Documentation (RHCSA) — `rpm -qf`, `rpm -qd`, `find /usr/share/doc`

- **Series:** linux-ops-mastery — Package Intelligence & Documentation
- **Trilogy:** **`18a`** (RHCSA hand-typed) → [`18b`](../lab-18b-locate-command-docs-ansible/) (Ansible mirror) → [`18c`](../lab-18c-locate-command-docs-verify/) (Verify capstone)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = owner package + docs via `rpm -qf`/`rpm -qd` · Task 2 = search docs tree with `find` and filter)
- **Practice Directory (rotation #18):** `/lib64` (reference-only path for environment orientation)
- **Sandbox (Tier B):** `/tmp/lab18a` with `USER=labuser_18_doclocate`, `GROUP=labgrp_18_doclocate`, `USER_HOME=/tmp/lab18a/home_labuser_18_doclocate`
- **Traps rehearsed this lab:** **T18-A** (`rpm -ql` vs `rpm -qd` confusion) · **T18-B** (broken name pattern misses files in `/usr/share/doc`) · **T41** (destroy-restore drill deferred to 18c) · **T44** (cleanup audit must end with four `✅`)

> **This lab's topic:** locate command documentation reliably using package ownership + package docs metadata + filesystem search.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  RPM:   $(rpm --version 2>/dev/null)"
echo "📁  PRACTICE DIR: /lib64"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "🕒  TIME:  $(date -Is)"
echo "⚠️  TRAP REMINDERS THIS LAB: T18-A T18-B T41 T44"
ls -ld /lib64 /usr/share/doc
echo "grep binary path check:"
ls -l /usr/bin/grep
```

> **STOP — paste header output before setup.**

---

## Objective

Build a no-guess workflow for docs lookup:

1. Start from a command path (`/usr/bin/grep`).
2. Resolve owning package with `rpm -qf`.
3. Ask RPM for documentation files only using `rpm -qd`.
4. Independently search `/usr/share/doc` with a controlled pattern.
5. Avoid T18-A and T18-B every time.

---

## Concept: Three Paths to Command Documentation

```text
Command path        Package owner          Documentation list
/usr/bin/grep  ->   rpm -qf path     ->    rpm -qd package

Fallback tree search:
find /usr/share/doc -type f -name '*grep*' 2>/dev/null
```

- `rpm -qf` answers: "which package owns this file?"
- `rpm -qd` answers: "which files in that package are marked as docs?"
- `find /usr/share/doc` answers: "what doc files match my naming signal?"

**T18-A risk:** using `rpm -ql` when asked for docs only.  
**T18-B risk:** using overly specific broken patterns that miss real filenames.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=18
export LAB_SLUG=doclocate
export SANDBOX=/tmp/lab18a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-18a/task1
mkdir -p /root/rhcsa_journal/lab-18a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /usr/share/doc /lib64
getent group "${GROUP}"
getent passwd "${USER}"
echo "Sandbox built at $(date -Is)"
```

> **STOP — paste `id`, `ls -ld`, and both `getent` lines before Task 1.**

---

## Task 1 — Map `/usr/bin/grep` to docs with `rpm -qf` then `rpm -qd`

### Warm-Up

```bash
rpm -qf /usr/bin/grep
rpm -qf /usr/bin/grep | xargs rpm -qi | head -n 8
echo "Warm-up done at $(date -Is)"
```

### Purpose

Execute the exact exam pattern:

1. Run `rpm -qf /usr/bin/grep`.
2. Feed that package into `rpm -qd`.
3. Save evidence via `tee` in task log and `output.txt`.

### Main command block

```bash
TASKLOG=/tmp/lab18a/task1.txt
OUT=/tmp/lab18a/output.txt

PKG=$(rpm -qf /usr/bin/grep)
echo "package=${PKG}"                                      | tee "${TASKLOG}"

# Required Task 1 flow
rpm -qf /usr/bin/grep                                      | tee -a "${TASKLOG}"
rpm -qd "${PKG}"                                           | tee "${OUT}" | tee -a "${TASKLOG}"

# Trap contrast: docs-only vs all files
echo "T18-A contrast (docs-only count vs all-files count)" | tee -a "${TASKLOG}"
echo "rpm -qd count: $(rpm -qd "${PKG}" | wc -l)"          | tee -a "${TASKLOG}"
echo "rpm -ql count: $(rpm -ql "${PKG}" | wc -l)"          | tee -a "${TASKLOG}"

test -s "${OUT}" && echo "✅ output.txt populated" || echo "❌ output.txt empty" | tee -a "${TASKLOG}"
echo "exit was: $?"                                        | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| `rpm -qf PATH` | Finds owning package for a file path |
| `rpm -qd PKG` | Lists only documentation files for that package |
| `rpm -ql PKG` | Lists all files (not docs-only) |
| **🪤 T18-A** | `-ql` is not acceptable when prompt asks docs |

### PERSISTENCE CHECK

| What was configured | Verification command |
|---|---|
| Package identified | `rpm -qf /usr/bin/grep` |
| Docs captured | `test -s /tmp/lab18a/output.txt` |
| Evidence log created | `test -s /tmp/lab18a/task1.txt` |

### Journal write

```bash
LAB=lab-18a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18a/task1.txt  "${JDIR}/evidence.txt"
cp /tmp/lab18a/output.txt "${JDIR}/output.txt"
```

---

## Task 2 — Search `/usr/share/doc` for grep-related files

### Warm-Up

```bash
find /usr/share/doc -maxdepth 2 -type d | head -n 10
echo "Warm-up done at $(date -Is)"
```

### Purpose

Use filesystem search to confirm doc discovery independently from RPM metadata.

### Main command block

```bash
TASKLOG=/tmp/lab18a/task2.txt
HITS=/tmp/lab18a/grep-doc-hits.txt

# Required Task 2 flow
find /usr/share/doc -type f -name '*grep*' 2>/dev/null | grep -E 'grep|README|NEWS|AUTHORS' \
    | tee "${HITS}" | tee "${TASKLOG}"

echo "hit-count=$(wc -l < "${HITS}")"                     | tee -a "${TASKLOG}"

# T18-B trap demo: broken pattern likely misses expected files
BROKEN=$(find /usr/share/doc -type f -name '*grep-doc-NOTREAL*' 2>/dev/null | wc -l)
echo "broken-pattern-count=${BROKEN}"                     | tee -a "${TASKLOG}"
echo "✅ T18-B lesson: prefer resilient pattern '*grep*'" | tee -a "${TASKLOG}"

echo "exit was: $?"                                       | tee -a "${TASKLOG}"
```

### Concept Card

| Concept | What it does |
|---|---|
| `find ... -name '*grep*'` | Pattern-based discovery in docs tree |
| `2>/dev/null` | Suppresses non-critical permission noise |
| post-filter `grep -E` | Narrows noisy results to useful hints |
| **🪤 T18-B** | Broken literal names miss valid docs |

### PERSISTENCE CHECK

| What was configured | Verification command |
|---|---|
| Hit list written | `test -s /tmp/lab18a/grep-doc-hits.txt` |
| Task evidence written | `test -s /tmp/lab18a/task2.txt` |

### Journal write

```bash
LAB=lab-18a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp /tmp/lab18a/task2.txt         "${JDIR}/evidence.txt"
cp /tmp/lab18a/grep-doc-hits.txt "${JDIR}/grep-doc-hits.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 18a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
echo "Cleanup complete at $(date -Is)"
```

---

## Lab 18a Checklist (2 tasks + closeout)

- [ ] Task 1 ran exact `rpm -qf /usr/bin/grep` then `rpm -qd` flow and wrote `output.txt`
- [ ] Task 2 ran exact `find /usr/share/doc -type f -name '*grep*' 2>/dev/null` flow with filter
- [ ] T18-A and T18-B trap contrasts were recorded in evidence logs
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
