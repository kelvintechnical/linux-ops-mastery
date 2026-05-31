# lab-01c — stdout redirection — verification capstone

The auditor seat. Hand-typed RHCSA inspection only — no Ansible CLI
(Section 17). You prove lab-01a's `>`/`>>` behavior with evidence,
then run a T41 destroy-restore drill that separates volatile `/tmp`
from durable `/root` journal artifacts.

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no more.
Begins after `lab-01a` and `lab-01b` are complete.

---

## LAB HEADER (confirm or correct before Task 1)

```
ENV:   BAREMETAL
DISK:  /dev/sda
NIC:   ens3
SE:    $(getenforce 2>/dev/null || echo n/a)
OS:    $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
TIME:  $(date -Is)
USER:  $(whoami)@$(hostname -s)

TRAPS: T01-A silent > truncation | T01-B unquoted redirect target |
       T44 cleanup orphan audit | T41 persistence reasoning
PRACTICE DIR: /tmp — sandbox scratch space; cleared on reboot
```

Trap selection (Section 12 — exactly 4):
- **T01-A** + **T01-B** — io category (audit the behaviors directly)
- **T44** — repeated from lab-01b (cleanup orphan audit)
- **T41** — Meta/Strategy rotation (destroy-restore persistence drill)

---

## LAB-WIDE SETUP (run once before Task 1; paste output)

```bash
export LAB_NUM=01
export LAB_SLUG=stdout-redirection
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
# Never use USER= — bash reserves it; sudo -i resets it to root silently
export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}
export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}

mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"
getent group  "${GROUP}"    >/dev/null || groupadd "${GROUP}"
getent passwd "${LAB_USER}" >/dev/null || useradd \
    -d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"
chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"

# Recreate lab-01a canonical file for audit
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"

id "${LAB_USER}"
ls -la "${SANDBOX}/"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

Paste output. You should see `notes.txt` and three lines when we `cat` it next.

---

## TASK 1 of 2 — Audit: prove `>` truncates and `>>` preserves

```
LAB:   lab-01c — stdout redirection — verify
TASK:  1 of 2 — audit > vs >> with wc -l, cat, stat
TRAPS: T01-A T01-B T44 T41
```

### Quiz warm-up (from lab-01b)

- **Q1:** Why does `ansible-playbook` show `changed=1` every run for
  a `shell:` task that uses `>`?
- **Q2:** What is T01-B?

Confirm or correct before we proceed.

---

### Step 1 of 5 — Baseline: `wc -l` proves three lines (`>>` worked)

Run this:

```bash
wc -l < "${SANDBOX}/notes.txt"
cat -n "${SANDBOX}/notes.txt"
```

Before I explain — what does `-n` add to `cat`?

**After paste — SYNTAX BREAKDOWN**
- `wc -l` — count newline-terminated lines
- `< "${SANDBOX}/notes.txt"` — feed file as stdin (number only, no filename)
- `cat -n` — print content with line numbers prefixed

**PLAIN ENGLISH:** Prove the setup block built a 3-line file using
`>` once then `>>` twice.

**WHY:** Baseline before we deliberately trigger T01-A.

Paste output. Expect `3` and lines `alpha`, `bravo`, `charlie`.

---

### Step 2 of 5 — T01-A demo: single `>` destroys prior content

Run this:

```bash
echo "only newest" > "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
cat -n "${SANDBOX}/notes.txt"
```

Before I explain — predict `wc -l` after the `>`.

**After paste — SYNTAX BREAKDOWN**
- `echo "only newest"` — string to stdout
- `>` — **truncate** file first, then write (T01-A)
- `wc -l` — now returns `1`, not `3`
- `cat -n` — shows only `only newest`; alpha/bravo/charlie are gone

**PLAIN ENGLISH:** One `>` silently destroyed two lines. No warning.

**WHY:** This is the audit proof of T01-A — numbers don't lie.

Paste output.

---

### Step 3 of 5 — Restore with `>>` and prove preservation

Run this:

```bash
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
cat "${SANDBOX}/notes.txt"
```

**After paste — SYNTAX BREAKDOWN**
- First line MUST use `>` — fresh file or you'd append to stale data
- Lines 2–3 use `>>` — append without truncating (contrast to Step 2)
- `wc -l` — back to `3`

**PLAIN ENGLISH:** Rebuild the canonical 3-line file the correct way.

**WHY:** Audit isn't just "break things" — you must restore to known good.

Paste output.

---

### Step 4 of 5 — RHCSA inspection #1: `stat`

```bash
stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt"
```

**After paste — SYNTAX BREAKDOWN**
- `stat` — read inode metadata
- `-c '%U:%G %a %n'` — print only owner, group, octal mode, name

**PLAIN ENGLISH:** One-line ownership and permission audit.

**WHY:** Section 17 requires >=3 inspection commands; this is #1.

Paste output.

---

### Step 5 of 5 — RHCSA inspection #2 and #3: `ls -l` + `diff`

```bash
ls -l "${SANDBOX}/notes.txt"
cat > /tmp/expected_notes.txt <<'EOF'
alpha
bravo
charlie
EOF
diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" || true
echo "exit was: $?"
```

Before I explain — what does `diff -u` exit code 1 mean?

**After paste — SYNTAX BREAKDOWN**
- `ls -l` — long listing: perms, owner, size, mtime (#2)
- `diff -u` — unified diff expected vs actual (#3)
- `|| true` — keep `$?` at 0 so Section 8 doesn't block on intentional diff

**PLAIN ENGLISH:** Compare what you expect to what's on disk.

**WHY:** Capstone habit — never trust `cat` alone; diff proves byte match.

Capture evidence (Section 17d):

```bash
mkdir -p /root/rhcsa_journal/lab01/task1c
{
  wc -l < "${SANDBOX}/notes.txt"
  stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt"
  ls -l "${SANDBOX}/notes.txt"
  diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" || true
} 2>&1 | tee /root/rhcsa_journal/lab01/task1c/evidence.txt
echo "exit was: $?"
```

Paste the `evidence.txt` path and exit line.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `wc -l < f` | line count without filename | proves > vs >> numerically |
| `>` | truncate then write | T01-A silent data loss |
| `>>` | append | using `>` instead = trap |
| `stat -c` | one-line metadata audit | RHCSA inspection #1 |
| `diff -u` | expected vs actual | exit 1 on mismatch is normal |

---

### Persistence check

```bash
test -f /root/rhcsa_journal/lab01/task1c/evidence.txt && echo "evidence on /root (survives reboot)"
findmnt /tmp | head -2
```

Paste output.

---

### Journal write (before cleanup)

```bash
LAB=lab01
TASK=task1c
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01c-stdout-redirection-verify
TASK:   1 of 2 — audit > vs >> with wc/cat/stat/diff
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    verification — > truncates, >> preserves
EVIDENCE: /root/rhcsa_journal/lab01/task1c/evidence.txt
TRAPS:    T01-A T01-B T44 T41
NEXT:     task2 — T41 destroy-restore drill
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

---

### Cleanup (Section 6)

```bash
set +e
if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"
echo "── cleanup audit ──"
getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"
getent group  "${GROUP}"    && echo "group remains (FAIL)" || echo "group gone (OK)"
test -d "${SANDBOX}"        && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"
set -e
echo "exit was: $?"
```

All rows `(OK)`. **STOP** before Task 2.

---

## TASK 2 of 2 — T41 destroy-restore persistence drill

```
LAB:   lab-01c — stdout redirection — verify
TASK:  2 of 2 — destroy /tmp state, restore from journal, close trilogy
TRAPS: T01-A T01-B T44 T41
```

### Quiz warm-up (from Task 1)

- **Q1:** After `echo x > file`, how many lines does `wc -l` show if
  the file had 10 lines before?
- **Q2:** Where is `evidence.txt` stored — `/tmp` or `/root`?

Confirm or correct. Re-run **LAB-WIDE SETUP** (Task 1 cleanup cleared sandbox).

---

### Step 1 of 4 — Record BEFORE state (T41)

```bash
BEFORE_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')
echo "BEFORE hash: ${BEFORE_HASH}"
wc -l < "${SANDBOX}/notes.txt"
```

**After paste — SYNTAX BREAKDOWN**
- `sha256sum` — cryptographic fingerprint of exact bytes
- `awk '{print $1}'` — capture hash field only
- `$()` — command substitution stores result in a variable

**PLAIN ENGLISH:** Record proof of file state before we simulate reboot.

**WHY:** T41 — you must prove what survived, not assume.

Paste output.

---

### Step 2 of 4 — Destroy volatile state (simulate /tmp cleared)

```bash
rm -rf "${SANDBOX}"
test -d "${SANDBOX}" && echo "sandbox STILL exists (FAIL)" || echo "sandbox gone (OK)"
test -f /root/rhcsa_journal/lab01/task1c/evidence.txt \
  && echo "journal evidence survives (OK)" \
  || echo "evidence missing (FAIL)"
```

**After paste — SYNTAX BREAKDOWN**
- `rm -rf` — remove sandbox tree (simulates /tmp cleared on reboot)
- Second `test` — `/root` journal untouched (different mount)

**PLAIN ENGLISH:** Volatile scratch gone; durable journal remains.

**WHY:** T41 core lesson — know what lives where.

Paste output.

---

### Step 3 of 4 — Restore from known-good procedure

```bash
mkdir -p "${SANDBOX}"
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
AFTER_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')
echo "AFTER hash:  ${AFTER_HASH}"
echo "BEFORE hash: ${BEFORE_HASH}"
test "${BEFORE_HASH}" = "${AFTER_HASH}" && echo "restore MATCH (OK)" || echo "restore MISMATCH (FAIL)"
```

**After paste — SYNTAX BREAKDOWN**
- Rebuild uses `>` then `>>` idiom from lab-01a
- Hash compare proves byte-identical restore

**PLAIN ENGLISH:** Recreate the file from muscle memory, verify with hash.

**WHY:** Exam tasks fail when you can't rebuild without the lab hand-holding.

Paste output. Hashes should match.

---

### Step 4 of 4 — Trilogy closeout audit + rotation tracker

```bash
echo "=== journal checkpoints ==="
find /root/rhcsa_journal/lab01 -name done.txt | sort

echo "=== boundary doc ==="
test -f /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt \
  && cat /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt \
  || echo "run lab-01b first if missing"

mkdir -p /root/rhcsa_journal/lab01/task2c
{
  echo "=== TRILOGY CLOSEOUT $(date -Is) ==="
  find /root/rhcsa_journal/lab01 -type f | sort
  wc -l < "${SANDBOX}/notes.txt"
} 2>&1 | tee /root/rhcsa_journal/lab01/task2c/evidence.txt

echo "last_used=01" > /root/rhcsa_journal/dir_rotation.txt
cat /root/rhcsa_journal/dir_rotation.txt
echo "exit was: $?"
```

**After paste — SYNTAX BREAKDOWN**
- `find ... done.txt` — list trilogy completion checkpoints
- `tee evidence.txt` — append closeout transcript to journal
- `echo last_used=01 > dir_rotation.txt` — Section 1 rotation tracker

**PLAIN ENGLISH:** Prove trilogy artifacts exist; advance directory rotation.

**WHY:** Next topic practice dir is `/etc` (slot 02).

Paste output.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `sha256sum` | byte-exact file fingerprint | `cat` misses trailing newline diffs |
| `rm -rf ${SANDBOX}` | simulate /tmp volatility | T41: fixing live without journal |
| restore `>` then `>>` | rebuild from muscle memory | `>>` first appends to stale data |
| `/root/rhcsa_journal/` | durable exam artifacts | answers on screen = zero points |
| `dir_rotation.txt` | tracks FHS practice dir | slot 02 = /etc next |

---

### Persistence check (final trilogy question)

Write before running:

"If we rebooted now, could you resume topic 01 from the journal alone?
Name three files that prove it."

Then run:

```bash
find /root/rhcsa_journal/lab01 -name done.txt | sort
```

Paste output.

---

### Journal write (before final cleanup)

```bash
LAB=lab01
TASK=task2c
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01c-stdout-redirection-verify
TASK:   2 of 2 — T41 destroy-restore + trilogy closeout
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
TRILOGY: lab-01 stdout redirection CLOSED
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    T41 persistence — /tmp volatile, /root durable
EVIDENCE: /root/rhcsa_journal/lab01/task2c/evidence.txt
TRAPS:    T01-A T01-B T44 T41
ROTATION: last_used=01 (next practice dir /etc)
NEXT:     lab-02a stderr redirection
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

---

### Cleanup (Section 6 — final trilogy teardown)

```bash
set +e
if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi
if getent group  "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"
echo "── cleanup audit ──"
getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"
getent group  "${GROUP}"    && echo "group remains (FAIL)" || echo "group gone (OK)"
test -d "${SANDBOX}"        && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"
set -e
echo "Cleanup complete at $(date -Is)"
echo "exit was: $?"
```

All rows must say `(OK)`.

### Drill (trilogy closeout)

```bash
python3 ~/scripts/rhcsa_drill.py --tier 1
```

**STOP — lab-01 trilogy complete.** Topic 02 begins only after all
`done.txt` checkpoints under `/root/rhcsa_journal/lab01/` exist and
cleanup audit shows `(OK)`.
