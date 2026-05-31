# Lab 22a: Filtering Text with `grep` and Regex (RHCSA) — `-E`, `-P`, anchors, context

- **Series:** linux-ops-mastery — Text Processing and Pattern Matching
- **Trilogy:** **`22a`** (RHCSA hand-typed) → [`22b`](../lab-22b-grep-regex-ansible/) (Ansible regex modules) → [`22c`](../lab-22c-grep-regex-verify/) (audit + destroy-restore)
- **Career arcs covered:** RHCSA EX200 (fast text extraction), RHCE EX294 (regex awareness before automation), SRE (log slicing), DevOps (config validation in pipelines)
- **Prerequisite:** Labs 01a through 10c patterns (journal + cleanup reflexes)
- **Time Estimate:** 30–45 minutes
- **Tasks:** 2 (Task 1 = `grep -E` with anchors/alternation/classes/context on `/etc/passwd` · Task 2 = `grep -P` lookahead on `/etc/services`, with `-E` contrast)
- **Practice Directory (rotation slot):** `/home`
- **Sandbox (Tier B):** `/tmp/lab22a` with `USER=labuser_22_regex`, `GROUP=labgrp_22_regex`
- **Traps rehearsed:** **T22-A** (BRE vs ERE confusion), **T22-B** (`.*` greediness in PCRE), **T41**, **T44**

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T22-A T22-B T41 T44"
echo "📁  PRACTICE DIR: /home"
ls -ld /home
grep --version | head -n 1
```

> **STOP — paste header output before setup.**

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=22
export LAB_SLUG=regex
export SANDBOX=/tmp/lab22a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-22a/task1 /root/rhcsa_journal/lab-22a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

echo "Sandbox built at $(date -Is)"
id "${USER}"
```

---

## Task 1 — `grep -E` on `/etc/passwd`: anchors, alternation, classes, context

### Warm-Up

```bash
grep -n 'bash' /etc/passwd | head -n 3
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Main command block

```bash
TASKLOG=/tmp/lab22a/task1.txt

echo "═══ Part A: anchors + line numbers ═══"                 2>&1 | tee "$TASKLOG"
grep -En '^(root|nobody):' /etc/passwd                        | tee -a "$TASKLOG"

echo "═══ Part B: alternation + character classes ═══"        | tee -a "$TASKLOG"
grep -En '^(daemon|mail|bin|sys):x:[0-9]+:[0-9]+:' /etc/passwd | tee -a "$TASKLOG"
grep -En '^[a-z_][a-z0-9_-]*:x:[0-9]{1,5}:[0-9]{1,5}:' /etc/passwd | tee -a "$TASKLOG"

echo "═══ Part C: word, invert, case-insensitive, counts ═══" | tee -a "$TASKLOG"
grep -Einw 'root' /etc/passwd                                 | tee -a "$TASKLOG"
grep -Evc '/sbin/nologin$' /etc/passwd                        | tee -a "$TASKLOG"

echo "═══ Part D: context lines around root entry ═══"        | tee -a "$TASKLOG"
grep -En -A2 '^root:' /etc/passwd                             | tee -a "$TASKLOG"
grep -En -B2 '^root:' /etc/passwd                             | tee -a "$TASKLOG"
grep -En -C1 '^root:' /etc/passwd                             | tee -a "$TASKLOG"

echo "═══ Part E: recursive file list demo (`-r`, `-l`) ═══"  | tee -a "$TASKLOG"
mkdir -p "${SANDBOX}/scan"
cp /etc/passwd "${SANDBOX}/scan/passwd.copy"
cp /etc/group  "${SANDBOX}/scan/group.copy"
grep -rEl '^root:' "${SANDBOX}/scan"                          | tee -a "$TASKLOG"

echo "exit was: $?"
```

### Switches used this task

| Token | Meaning |
|---|---|
| `-E` | Extended regex (ERE): `+`, `?`, `|`, `{m,n}` without backslashes |
| `-n` | Show line numbers |
| `-i` | Case-insensitive matching |
| `-v` | Invert match (non-matching lines) |
| `-c` | Count matches |
| `-w` | Match whole word |
| `-r` | Recursive search |
| `-l` | Show only file names with matches |
| `-A/-B/-C` | Context lines after/before/both |
| `^` / `$` | Start/end anchors |

### Concept Card

| Concept | What it does |
|---|---|
| BRE vs ERE | In ERE (`-E`), `+` and `|` are operators directly |
| Anchors | `^` and `$` prevent accidental substring matches |
| Character classes | `[a-z0-9_-]` constrains allowed characters |
| **🪤 Trap Risk T22-A** | Forgetting `-E` then writing ERE syntax causes wrong/empty matches |

### Journal write

```bash
LAB=lab-22a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22a/task1.txt "$JDIR/evidence.txt"

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

## Task 2 — `grep -P` lookahead on `/etc/services`, then contrast with `-E`

### Warm-Up

```bash
grep -nE '^(ssh|http)[[:space:]]' /etc/services
echo "Warm-up done by $(whoami) at $(date -Is)"
```

### Main command block

```bash
TASKLOG=/tmp/lab22a/task2.txt

echo "═══ Part A: PCRE lookahead (`-P`) ═══"                  2>&1 | tee "$TASKLOG"
grep -nPo '^[a-z0-9-]+(?=[[:space:]]+443/tcp)' /etc/services | tee -a "$TASKLOG"
grep -nP '^(?!#).*\\b(ssh|smtp)\\b(?=.*tcp)' /etc/services   | tee -a "$TASKLOG"

echo "═══ Part B: greedy trap demo (T22-B) ═══"               | tee -a "$TASKLOG"
grep -nPo '^http.*tcp' /etc/services | head -n 3              | tee -a "$TASKLOG"
grep -nPo '^http[^[:space:]]*[[:space:]]+[0-9]+/tcp' /etc/services | head -n 3 | tee -a "$TASKLOG"

echo "═══ Part C: ERE contrast (`-E` can emulate many checks) ═══" | tee -a "$TASKLOG"
grep -nE '^[a-z0-9-]+[[:space:]]+443/tcp' /etc/services       | tee -a "$TASKLOG"
grep -nE '^(ssh|smtp)[[:space:]].*tcp' /etc/services          | tee -a "$TASKLOG"

echo "═══ Part D: only matching tokens (`-o`) + count ═══"     | tee -a "$TASKLOG"
grep -nEo '(tcp|udp)' /etc/services | head -n 20              | tee -a "$TASKLOG"
grep -Ec '^[a-z0-9-]+[[:space:]]+[0-9]+/tcp' /etc/services    | tee -a "$TASKLOG"

echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| `-P` | Enables PCRE features such as lookahead |
| Lookahead `(?=...)` | Assert following text without consuming it |
| `-o` | Output only matching fragment |
| `|` + groups | Alternation and grouping for compact patterns |
| **🪤 Trap Risk T22-B** | `.*` in PCRE can over-consume; narrow with classes or lazy logic |

### Journal write

```bash
LAB=lab-22a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab22a/task2.txt "$JDIR/evidence.txt"

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    grep -P lookahead on /etc/services, contrasted with grep -E
TRAPS:    T22-A and T22-B rehearsed
NEXT:     lab-22b Ansible regex modules
EOF
```

---

## Lab Closeout — Section 6 teardown + audit

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 22a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
```

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
