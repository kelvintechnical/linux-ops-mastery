# Lab 25a: Extracting Columns with `awk` (RHCSA) — `-F:`, `$1`, `NR==1`, `NF`, `$3>1000`, `BEGIN/END`, `printf`

- **Series:** linux-ops-mastery — Text Processing and Parsing
- **Trilogy:** **`25a`** (RHCSA hand-typed) → [`25b`](../lab-25b-awk-columns-ansible/) (Ansible) → [`25c`](../lab-25c-awk-columns-verify/) (Verify)
- **Prerequisite:** `awk` basics and shell quoting fundamentals
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = parse `/etc/passwd` columns with filters · Task 2 = `BEGIN/END` counting + `printf` report + Tier B `sudo -u` weave)
- **Practice Directory (rotation slot):** `/tmp`
- **Sandbox (Tier B):** `/tmp/lab25a` with `USER=labuser_25_awk`, `GROUP=labgrp_25_awk`
- **Traps rehearsed:** **T25-A** (default field separator is whitespace, including tabs) · **T25-B** (single vs double quotes controls variable expansion) · **T41** (skip destroy-restore drill) · **T44** (cleanup left orphan user/group)

> **This lab's practice directory is `/tmp`**. Tier B resources for this trilogy stay in the `/tmp/lab25*` namespace so teardown is safe and repeatable.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T25-A T25-B T41 T44"
echo "📁  PRACTICE DIR: /tmp"
ls -ld /tmp
df -h /tmp | tail -n 1
echo "exit was: $?"
```

---

## Objective

Build exam-speed reflexes for column extraction in `awk`:

1. Parse colon-delimited records safely with `-F:`.
2. Print specific columns (`$1`) and filter rows (`$3>1000`).
3. Use record/field metadata (`NR`, `NF`) for sanity checks.
4. Build summaries using `BEGIN` and `END`.
5. Format machine-friendly output with `printf`.

---

## Concept: Why `-F:` Matters

By default, `awk` splits each line on runs of whitespace (spaces and tabs). That is great for `ps` output, but wrong for `/etc/passwd`, which is colon-delimited.

```text
Default FS (wrong for passwd):   FS = "[ \t]+"
Passwd FS (correct):             FS = ":"

/etc/passwd line:
root:x:0:0:root:/root:/bin/bash
  $1  $2 $3 $4  $5    $6    $7
```

If you forget `-F:`, filters like `$3>1000` evaluate the wrong field and silently produce bad answers (**T25-A**).

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=25
export LAB_SLUG=awk
export SANDBOX=/tmp/lab25a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-25a/task1 /root/rhcsa_journal/lab-25a/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

---

## Task 1 — Extract login names and numeric UID filters

### Warm-Up

```bash
awk 'NR==1 {print "first-line:", $0}' /etc/passwd
awk -F: 'NR==1 {print "FS=:", "user=" $1, "uid=" $3, "shell=" $7}' /etc/passwd
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab25a/task1.txt

echo "═══ Part A: required command 1 ═══"                           2>&1 | tee $TASKLOG
awk -F: '{print $1}' /etc/passwd | head                            2>&1 | tee -a $TASKLOG

echo "═══ Part B: required command 2 ═══"                          | tee -a $TASKLOG
awk '$3>1000 {print $1}' /etc/passwd                                2>&1 | tee -a $TASKLOG

echo "═══ Part B2: corrected colon-aware filter (T25-A fix) ═══"   | tee -a $TASKLOG
awk -F: '$3>1000 {print $1}' /etc/passwd                            2>&1 | tee -a $TASKLOG

echo "═══ Part C: record metadata (`NR`/`NF`) ═══"                 | tee -a $TASKLOG
awk -F: 'NR==1 {printf "NR=%d NF=%d first_user=%s\n", NR, NF, $1}' /etc/passwd \
                                                                 | tee -a $TASKLOG
awk -F: 'NF!=7 {print "odd-field-count:", NR ":" $0}' /etc/passwd | tee -a $TASKLOG

echo "exit was: $?"
```

### Switches

| Token | Meaning |
|---|---|
| `-F:` | Set field separator to colon |
| `{print $1}` | Print username field |
| `$3>1000` | Keep rows where UID is greater than 1000 |
| `NR==1` | Act only on first record |
| `NF` | Number of fields in current record |

### Concept Card

| Concept | What it does |
|---|---|
| Default separator | Whitespace (spaces and tabs), not colon |
| `awk -F: ... /etc/passwd` | Correct parser for passwd rows |
| `NR` | 1-based line counter |
| `NF` | Number of parsed fields in the current line |
| **🪤 Trap Risk T25-A** | Forgetting `-F:` mis-parses passwd data |

### Journal write

```bash
LAB=lab-25a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25a/task1.txt "$JDIR/evidence.txt"

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

## Task 2 — `BEGIN/END` counting + `printf` formatting + Tier B weave

### Warm-Up

```bash
printf "%-18s %-8s %s\n" "USER" "UID" "SHELL"
awk -F: 'NR==1 {printf "%-18s %-8s %s\n", $1, $3, $7}' /etc/passwd
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab25a/task2.txt
REPORT=/tmp/lab25a/passwd-summary.txt

echo "═══ Part A: BEGIN/END summary with printf ═══"                 2>&1 | tee $TASKLOG
awk -F: '
BEGIN {
  total=0; gt1000=0;
  printf "%-18s %-8s %s\n", "USER", "UID", "SHELL";
}
{
  total++;
  if ($3 > 1000) {
    gt1000++;
    printf "%-18s %-8s %s\n", $1, $3, $7;
  }
}
END {
  printf "TOTAL=%d UID_GT_1000=%d\n", total, gt1000;
}
' /etc/passwd | tee -a $TASKLOG > "${REPORT}"

echo "═══ Part B: single vs double quotes (T25-B) ═══"               | tee -a $TASKLOG
awk -F: 'NR==1 {print "single-quoted shell var literal: ${USER}"}' /etc/passwd | tee -a $TASKLOG
awk -F: "NR==1 {print \"double-quoted shell var expanded: ${USER}\"}" /etc/passwd | tee -a $TASKLOG

echo "═══ Part C: sudo -u Tier B weave ═══"                          | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c \
  'awk -F: "BEGIN{printf \"owned-by-%s\\n\", ENVIRON[\"USER\"]} NR==1{printf \"first:%s uid:%s\\n\", \$1, \$3}" /etc/passwd > "'"${USER_HOME}"'/task2-asuser.txt"'

stat -c '%U:%G %a %n' "${USER_HOME}/task2-asuser.txt"                | tee -a $TASKLOG
cat "${USER_HOME}/task2-asuser.txt"                                  | tee -a $TASKLOG
echo "exit was: $?"
```

### Concept Card

| Concept | What it does |
|---|---|
| `BEGIN` | Initialize counters/headers before first record |
| `END` | Print totals after final record |
| `printf` | Fixed-width formatting for readable columns |
| `ENVIRON["USER"]` | Access environment variable safely inside awk |
| **🪤 Trap Risk T25-B** | Single-quoted shell string blocks `${VAR}` expansion |

### Journal write

```bash
LAB=lab-25a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab25a/task2.txt "$JDIR/evidence.txt"
cp /tmp/lab25a/passwd-summary.txt "$JDIR/passwd-summary.txt"
cp "${USER_HOME}/task2-asuser.txt" "$JDIR/task2-asuser.txt"

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

## Lab Closeout — Section 6 Bulletproof Teardown

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 25a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"
set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> T44 enforcement: do not declare complete until all four audit lines are `✅`.

---

## Lab 25a Checklist

- [ ] Task 1 complete: both required commands executed and captured
- [ ] Task 2 complete: `BEGIN/END` totals + `printf` table + Tier B ownership proof
- [ ] Traps rehearsed: T25-A and T25-B explicitly demonstrated
- [ ] Section 6 closeout passed with four `✅` audit lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
