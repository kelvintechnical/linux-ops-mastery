# Lab 29a: Searching Manuals by Keyword (RHCSA) — `whatis`, `apropos`, `mandb`

- **Series:** linux-ops-mastery — Documentation Discovery and Command Fluency
- **Trilogy:** **`29a`** (RHCSA hand-typed) → [`29b`](../lab-29b-apropos-whatis-ansible/) (Ansible trap practice across a Section 18 boundary) → [`29c`](../lab-29c-apropos-whatis-verify/) (Verify capstone: audit + destroy-restore)
- **Time Estimate:** 30-40 minutes
- **Tasks:** 2 (Task 1 = capture `whatis` and `apropos` evidence with `tee` · Task 2 = rebuild the man index with `sudo mandb -c` and prove before/after counts)
- **Practice Directory (rotation #29):** `/proc`
- **Sandbox (Tier B):** `/tmp/lab29a` with `USER=labuser_29_apropos`, `GROUP=labgrp_29_apropos`, `USER_HOME=/tmp/lab29a/home_labuser_29_apropos`
- **Traps rehearsed:** **T29-A** (stale man cache means `whatis` may return nothing until `mandb` runs) · **T29-B** (regex vs literal matching in `apropos`) · **T41** · **T44**

> **Focus:** build reflexes for keyword-first manual lookup and index repair when cache state drifts.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T29-A T29-B T41 T44"
echo "📁  PRACTICE DIR: /proc"
ls -ld /proc
whatis --version 2>/dev/null | head -n 1 || echo "whatis version banner unavailable"
apropos --version 2>/dev/null | head -n 1 || echo "apropos version banner unavailable"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Use `whatis` for one-line command descriptions and `apropos` for keyword-driven discovery.
2. Capture reproducible evidence using `tee`.
3. Diagnose and fix stale man index behavior with `mandb -c`.
4. Prove the cache-rebuild effect with before/after query counts.

---

## Concept: `whatis` and `apropos` Read the Man-DB Index

- `whatis <command>` queries short descriptions by command/topic name.
- `apropos <keyword>` searches the whatis database by keyword pattern.
- Both depend on the indexed database under `/var/cache/man`.
- If the index is stale or missing, results can be incomplete or empty until `mandb` rebuilds it.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=29
export LAB_SLUG=apropos
export SANDBOX=/tmp/lab29a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-29a/task1 /root/rhcsa_journal/lab-29a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /proc /var/cache/man
```

> **STOP — paste setup output before Task 1.**

---

## Task 1 — Capture `whatis` and `apropos` evidence with `tee`

### Warm-Up

```bash
ls /proc | head -n 5
man -k ls | head -n 5
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Purpose

Produce the exact two core outputs for this lab, then add T29-B contrast evidence:

1. `whatis grep | tee ...`
2. `apropos 'list directory' | tee ...`

### Main command block

```bash
TASKLOG=/tmp/lab29a/task1.txt

echo "═══ Part A: exact required evidence commands ═══"            2>&1 | tee "$TASKLOG"
whatis grep                                                      2>&1 | tee /tmp/lab29a/whatis-grep.txt | tee -a "$TASKLOG"
apropos 'list directory'                                         2>&1 | tee /tmp/lab29a/apropos-list-directory.txt | tee -a "$TASKLOG"

echo "═══ Part B: T29-B regex vs literal mode contrast ═══"       | tee -a "$TASKLOG"
apropos 'list directory'                                          | tee -a "$TASKLOG"
apropos -e 'list directory'                                       | tee -a "$TASKLOG"
apropos 'list.*directory'                                         | tee -a "$TASKLOG"

echo "═══ Part C: Tier B sudo -u query copy ═══"                  | tee -a "$TASKLOG"
sudo -u "${USER}" bash -c \
  "apropos 'list directory' > '${USER_HOME}/apropos-asuser.txt'"
stat -c '%U:%G %a %n' "${USER_HOME}/apropos-asuser.txt"          | tee -a "$TASKLOG"
wc -l "${USER_HOME}/apropos-asuser.txt"                          | tee -a "$TASKLOG"

echo "exit was: $?"                                              | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `whatis grep` | One-line definition lookup for the exact topic name |
| `apropos 'list directory'` | Keyword pattern search across whatis index |
| `apropos -e PATTERN` | Exact (literal) topic matching, not regex pattern scan |
| `tee FILE` | Preserve terminal output as evidence |
| **🪤 Trap Risk T29-B** | Assuming `apropos` is always literal; default matching is pattern-driven. Use `-e` when exact literal behavior is required. |

### Journal write

```bash
LAB=lab-29a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab29a/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab29a/whatis-grep.txt "$JDIR/whatis-grep.txt"
cp /tmp/lab29a/apropos-list-directory.txt "$JDIR/apropos-list-directory.txt"
cp "${USER_HOME}/apropos-asuser.txt" "$JDIR/apropos-asuser.txt"

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    whatis and apropos keyword/manual index lookup
COMMANDS: whatis grep, apropos 'list directory', apropos -e, tee, sudo -u ${USER}
TRAPS:    T29-B rehearsed (pattern vs literal)
NEXT:     task2 — rebuild cache with mandb -c and compare counts
EOF
```

---

## Task 2 — Rebuild index with `sudo mandb -c` and verify before/after counts

### Warm-Up

```bash
whatis grep 2>/dev/null | wc -l
ls -ld /var/cache/man
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Purpose

Rehearse **T29-A** by proving cache rebuild impact with measured counts.

### Main command block

```bash
TASKLOG=/tmp/lab29a/task2.txt

echo "═══ Part A: before counts ═══"                               2>&1 | tee "$TASKLOG"
BEFORE_WHATIS=$(whatis grep 2>/dev/null | wc -l)
BEFORE_APROPOS=$(apropos 'list directory' 2>/dev/null | wc -l)
echo "before whatis grep count: ${BEFORE_WHATIS}"                  | tee -a "$TASKLOG"
echo "before apropos count:     ${BEFORE_APROPOS}"                 | tee -a "$TASKLOG"

echo "═══ Part B: rebuild man index with sudo mandb -c ═══"        | tee -a "$TASKLOG"
sudo mandb -c                                                      2>&1 | tee /tmp/lab29a/mandb-rebuild.txt | tee -a "$TASKLOG"

echo "═══ Part C: after counts ═══"                                | tee -a "$TASKLOG"
AFTER_WHATIS=$(whatis grep 2>/dev/null | wc -l)
AFTER_APROPOS=$(apropos 'list directory' 2>/dev/null | wc -l)
echo "after whatis grep count: ${AFTER_WHATIS}"                    | tee -a "$TASKLOG"
echo "after apropos count:     ${AFTER_APROPOS}"                   | tee -a "$TASKLOG"

test "${AFTER_WHATIS}" -ge "${BEFORE_WHATIS}" \
  && echo "✅ whatis count did not regress after mandb -c" \
  || echo "❌ whatis count regressed unexpectedly"                  | tee -a "$TASKLOG"

test "${AFTER_APROPOS}" -gt 0 \
  && echo "✅ apropos returns >0 entries after rebuild (T29-A covered)" \
  || echo "❌ apropos still empty; inspect mandb output and man-pages install" | tee -a "$TASKLOG"

echo "exit was: $?"                                                | tee -a "$TASKLOG"
```

### Concept Card

| Concept | What it does |
|---|---|
| `mandb -c` | Rebuilds the whatis database from scratch |
| Before/after counts | Quantifies cache repair effect |
| `/var/cache/man` | Location of generated manual index data |
| **🪤 Trap Risk T29-A** | Fresh man pages but stale index causes empty/partial `whatis`/`apropos` results until `mandb` runs |

### Journal write

```bash
LAB=lab-29a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cp /tmp/lab29a/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab29a/mandb-rebuild.txt "$JDIR/mandb-rebuild.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 29a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains"   || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}"               && echo "❌ sandbox remains"|| echo "✅ sandbox gone"
test -d "${USER_HOME}"             && echo "❌ home remains"   || echo "✅ home gone"

set -e
```

---

## Lab 29a Checklist (2 tasks + closeout)

- [ ] Task 1 captured exact required commands: `whatis grep | tee ...` and `apropos 'list directory' | tee ...`
- [ ] Task 2 ran `sudo mandb -c` and recorded before/after whatis + apropos counts
- [ ] T29-A and T29-B evidence captured in journal
- [ ] Section 6 closeout ended with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
