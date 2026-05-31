# lab-01c — stdout redirection — verification capstone

The auditor seat. No Ansible CLI in this lab — hand-typed RHCSA
inspection only (Section 17). You audit the artifacts the trilogy
produced, then run a destroy-restore drill that proves you understand
what survives a reboot and what does not.

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no
more. Begins after `lab-01a` and `lab-01b` are complete and drill
scores are >= 80%.

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

TRAPS THIS LAB: T41 T44
PRACTICE DIR:   /tmp — sandbox scratch space; cleared on reboot; safe to write without sudo
```

Trap rationale (per Sections 11 and 12 — different category from 01b's
T43/T44 pair where possible):

- **T41** (persistence reasoning) — the entire c-lab is a persistence
  proof. Task 2 is literally "if we rebooted, what survives?"
- **T44** (cleanup orphan audit) — Task 2 ends with a full Section 6
  audit that must show every `(OK)` row before the trilogy closes.

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
id    "${LAB_USER}"
ls -ld "${SANDBOX}" "${LAB_USER_HOME}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/tmp is sandbox scratch space; cleared on reboot.
RHCSA labs use it because nothing here survives reboot and no sudo is needed to write.
EOF

echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Recreate the canonical file from lab-01a so Task 1 has something to
audit:

```bash
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
echo "written by labuser" | sudo -u "${LAB_USER}" tee "${SANDBOX}/labuser_note.txt" >/dev/null
ls -la "${SANDBOX}/"
echo "exit was: $?"
```

Paste output.

---

## TASK 1 of 2 — Audit artifacts from the trilogy

```
LAB:   lab-01c — stdout redirection — verification capstone
TASK:  1 of 2 — inspect state with >=3 RHCSA inspection commands
TRAPS: T44 (cleanup orphan audit at end of task)
```

Section 17 requires at least 3 hand-typed RHCSA inspection commands
with no Ansible CLI. This task uses five: `stat`, `wc -l`, `cat`,
`ls -lZ`, and `diff`.

### Quiz warm-up (from lab-01b)

- **Q1:** Why does `ansible-playbook` report `changed=1` on every run
  for a `shell:` task that uses `>`?
- **Q2:** What is the difference between `command:` and `shell:` for
  a redirect?

Confirm or correct before we proceed.

---

### Step 1 of 5 — Inspect ownership and mode with `stat`

Run this:

```bash
stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt" \
                      "${SANDBOX}/labuser_note.txt"
```

Before I explain — what does `%a` show, and why is it octal?

**After you've answered:**

`%a` is the file mode in octal (e.g. `644`, `664`). Octal is how
RHCSA expects you to read and set permissions — `chmod 644`, not
`chmod u=rw,g=r,o=r` unless the exam asks for symbolic. The `%U:%G`
pair proves who owns each file: `notes.txt` should be root-owned
(you wrote it as root), `labuser_note.txt` should be
`${LAB_USER}:${GROUP}` (you used `sudo -u ... tee` in the setup).

Paste your output.

---

### Step 2 of 5 — Count lines with `wc -l < file`

Run this:

```bash
wc -l < "${SANDBOX}/notes.txt"
```

Before I explain — why `<` here instead of `wc -l file`?

**After you've answered:**

Same lab-01a callback: `< file` feeds stdin without printing the
filename in the output. You get a clean number (`3`) suitable for
capturing in `$()` or comparing in a script. `wc -l file` prints
`3 /tmp/labsandbox_01/notes.txt` — fine for humans, noisy for
automation.

Paste your output. You should see `3`.

---

### Step 3 of 5 — Read content with `cat` and verify line order

Run this:

```bash
cat -n "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

Before I explain — what does `-n` add?

**After you've answered:**

`-n` prefixes each line with its line number. Useful when you are
comparing expected vs actual and need to cite "line 2 is wrong".
The order should be alpha, bravo, charlie — proving `>` then `>>`
built the file correctly in lab-01a.

Paste your output.

---

### Step 4 of 5 — SELinux context with `ls -lZ`

Run this:

```bash
ls -lZ "${SANDBOX}/" 2>/dev/null || ls -l "${SANDBOX}/"
echo "exit was: $?"
```

Before I explain — what column does `-Z` add?

**After you've answered:**

`-Z` adds the SELinux security context (e.g. `unconfined_u:object_r:tmp_t:s0`
for files under /tmp). On systems without SELinux the command falls
back to plain `ls -l`. RHCSA capstones on enforcing systems expect
you to read this column and know when a context is wrong.

Paste your output.

---

### Step 5 of 5 — Compare expected vs actual with `diff`

Run this:

```bash
cat > /tmp/expected_notes.txt <<'EOF'
alpha
bravo
charlie
EOF

diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" || true
echo "exit was: $?"
```

Before I explain — why `|| true` at the end?

**After you've answered:**

`diff` exits 0 when files match, 1 when they differ. Without `|| true`,
a mismatch would make `$?` non-zero and Section 8 would block you —
even though finding a difference IS the point of the capstone. `|| true`
forces `$?` to 0 so you can paste the diff and discuss it without
triggering the blocker. If the files match, diff prints nothing and
exits 0 anyway.

Paste your output. No diff output means the files match exactly.

Capture evidence to the journal (Section 17d):

```bash
mkdir -p /root/rhcsa_journal/lab01/task1c
{
  stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt" "${SANDBOX}/labuser_note.txt"
  wc -l < "${SANDBOX}/notes.txt"
  cat -n "${SANDBOX}/notes.txt"
  ls -lZ "${SANDBOX}/" 2>/dev/null || ls -l "${SANDBOX}/"
  diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" || true
} 2>&1 | tee /root/rhcsa_journal/lab01/task1c/evidence.txt
echo "exit was: $?"
```

Paste the last two lines (`evidence.txt` path and exit status).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `stat -c '%U:%G %a %n'` | one-line ownership + mode audit | the RHCSA-canonical inspection format |
| `wc -l < file` | line count without filename noise | `<` vs bare filename argument |
| `cat -n` | show content with line numbers | cite "line N" in your answer |
| `ls -lZ` | list with SELinux context | wrong context = service won't start |
| `diff -u expected actual` | unified diff of two files | exit 1 on mismatch is normal |
| `\|\| true` after diff | keep capstone going on mismatch | without it, Section 8 blocks on intentional diff |
| `tee evidence.txt` | capture transcript to journal | Section 17d requires evidence on disk |

Drill mapping: every row above → `--category io`.

Trap-Risk row (Section 17f): trusting ansible-playbook's `changed=1`
without inspecting state with >=3 RHCSA commands. This task IS the
inspection.

---

### Persistence check

Question: If we rebooted right now, would
`/root/rhcsa_journal/lab01/task1c/evidence.txt` survive? Would
`${SANDBOX}/notes.txt`?

```bash
findmnt /root /tmp
ls -l /root/rhcsa_journal/lab01/task1c/evidence.txt
```

Paste output and state the answer in one sentence each.

---

### Journal write (run before cleanup)

```bash
LAB=lab01
TASK=task1c
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01c-stdout-redirection-verify
TASK:   1 of 2 — audit trilogy artifacts with stat/wc/cat/ls/diff
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    verification capstone — RHCSA inspection commands
COMMANDS: stat, wc -l, cat -n, ls -lZ, diff -u, tee
EVIDENCE: /root/rhcsa_journal/lab01/task1c/evidence.txt
TRAPS:    T44 (cleanup audit at task end)
MISSED:   [list any quiz question you got wrong, or "none"]
NEXT:     task2 — destroy-restore persistence drill
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Paste output.

---

### Cleanup (Section 6 teardown)

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Every audit row must say `(OK)`.

**STOP.** Task 2 is below. Do not look until Task 1 outputs,
persistence check, journal, and all `(OK)` audit lines are pasted.

---

## TASK 2 of 2 — Destroy-restore persistence drill

```
LAB:   lab-01c — stdout redirection — verification capstone
TASK:  2 of 2 — prove what survives reboot vs what does not
TRAPS: T41 (persistence reasoning), T44 (final trilogy cleanup audit)
```

This task simulates "we rebooted" without rebooting: you destroy
volatile state, verify what is gone, restore from persistent artifacts,
and prove the restore worked.

### Quiz warm-up (from Task 1)

- **Q1:** What does `diff -u` exit code 1 mean?
- **Q2:** Where did we save the audit transcript in Task 1?

Confirm or correct before we proceed.

---

### Prerequisite — re-run lab-wide setup + recreate notes

The Task 1 cleanup destroyed `${SANDBOX}`. Re-run **LAB-WIDE SETUP**
and the notes recreation block from the top of this file. Paste the
`Sandbox built by ...` and `ls -la` lines as proof.

---

### Step 1 of 4 — Record "before" state

Run this:

```bash
BEFORE="${SANDBOX}/notes.txt"
echo "BEFORE lines: $(wc -l < "${BEFORE}")"
stat -c '%U:%G %a %n' "${BEFORE}" "${SANDBOX}/labuser_note.txt"
sha256sum "${BEFORE}"
echo "exit was: $?"
```

Before I explain — what does `sha256sum` give you that `cat` does not?

**After you've answered:**

A cryptographic fingerprint of the exact byte content. Two files can
look identical to `cat` but differ in trailing newlines or invisible
characters. `sha256sum` catches that. It is the RHCSA-grade "prove
this file is exactly what I think it is" check.

Paste your output. Save the hash — you will compare after restore.

---

### Step 2 of 4 — Destroy volatile state (simulate reboot of /tmp)

Run this:

```bash
rm -rf "${SANDBOX}"
test -d "${SANDBOX}" && echo "sandbox STILL exists (FAIL)" || echo "sandbox gone (OK)"
test -f "${BEFORE}"    && echo "notes STILL exists (FAIL)" || echo "notes gone (OK)"
echo "exit was: $?"
```

Before I explain — predict whether
`/root/rhcsa_journal/lab01/task1c/evidence.txt` still exists after
this `rm -rf`.

**After you've answered:**

It still exists. You deleted only `${SANDBOX}` under `/tmp`. The
journal under `/root` is on a different mount and was never touched.
That is the persistence lesson in one move: volatile scratch vs
durable evidence.

Verify:

```bash
test -f /root/rhcsa_journal/lab01/task1c/evidence.txt \
  && echo "evidence.txt survives (OK)" \
  || echo "evidence.txt missing (FAIL)"
```

Paste both blocks' output.

---

### Step 3 of 4 — Restore from the expected template

Run this:

```bash
mkdir -p "${SANDBOX}"
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
echo "written by labuser" | sudo -u "${LAB_USER}" tee "${SANDBOX}/labuser_note.txt" >/dev/null

AFTER="${SANDBOX}/notes.txt"
echo "AFTER lines: $(wc -l < "${AFTER}")"
sha256sum "${AFTER}"
echo "exit was: $?"
```

Before I explain — compare the BEFORE and AFTER `sha256sum` lines.
Do they match?

**After you've answered:**

They should match if you restored identically. If they differ, find
the diff with `diff -u` — trailing newline, extra space, or wrong
line order. A mismatch here means your restore procedure is wrong,
not that persistence failed.

Paste output including both hashes.

---

### Step 4 of 4 — Final trilogy audit

Run this:

```bash
echo "=== journal tree ==="
find /root/rhcsa_journal/lab01 -type f | sort

echo "=== playbook survives ==="
test -f /root/rhcsa_journal/lab01/playbooks/task2.yml \
  && echo "task2.yml present (OK)" || echo "task2.yml missing (FAIL)"

echo "=== boundary statement survives ==="
test -f /root/rhcsa_journal/lab01/playbooks/BOUNDARY.txt \
  && echo "BOUNDARY.txt present (OK)" || echo "BOUNDARY.txt missing (FAIL)"

echo "=== restored sandbox ==="
stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt" "${SANDBOX}/labuser_note.txt"
wc -l < "${SANDBOX}/notes.txt"

echo "exit was: $?"
```

Before I explain — list three things that WOULD survive a real reboot
and three that would NOT, based on everything you ran in this trilogy.

**After you've answered:**

**Survive reboot:**

- `/root/rhcsa_journal/` tree (done.txt, notes.txt, evidence.txt,
  playbooks, BOUNDARY.txt)
- `${LAB_USER}` in `/etc/passwd` (until cleanup — T44)
- `/root/rhcsa_journal/dir_rotation.txt`

**Do NOT survive reboot:**

- `${SANDBOX}/notes.txt` (under /tmp)
- `${SANDBOX}/labuser_note.txt`
- Any process state, open FDs, shell variables

T41 is the exam trap: fixing live state in /tmp without writing the
persistent config (journal + playbook) means you cannot resume after
reboot. This trilogy's design forces the durable artifacts.

Paste output.

Append final evidence:

```bash
{
  echo "=== TRILOGY CLOSEOUT $(date -Is) ==="
  find /root/rhcsa_journal/lab01 -type f | sort
  stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt" "${SANDBOX}/labuser_note.txt"
  wc -l < "${SANDBOX}/notes.txt"
} 2>&1 | tee -a /root/rhcsa_journal/lab01/task2c/evidence.txt
mkdir -p /root/rhcsa_journal/lab01/task2c
echo "exit was: $?"
```

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---------|--------------|-----------|
| `sha256sum file` | fingerprint exact file bytes | `cat` misses trailing-newline diffs |
| `rm -rf ${SANDBOX}` | simulate /tmp cleared on reboot | forgetting /root journal survives |
| restore with `>` then `>>` | rebuild file from known good state | using `>>` first appends to stale data |
| `find /root/rhcsa_journal` | prove durable artifacts exist | exam answer only on screen, not on disk |
| T41 persistence | durable config vs volatile scratch | fixing live without saving to /etc or journal |
| T44 cleanup | `${LAB_USER}` survives until userdel | next lab inherits broken state |

Drill mapping: every row above → `--category io`.

---

### Persistence check (final trilogy question)

Write your answer before running the command:

"If we rebooted right now, could you resume this topic from the
journal alone? What three files prove it?"

Then run:

```bash
find /root/rhcsa_journal/lab01 -name done.txt | sort
tail -3 /root/rhcsa_journal/lab01/task2c/evidence.txt 2>/dev/null || echo "run evidence block first"
```

Paste output. You should see done.txt entries for task1, task1b,
task2b, task1c, task2c (or equivalent paths you completed).

---

### Journal write (run before final cleanup)

```bash
LAB=lab01
TASK=task2c
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"

cat > "$JDIR/done.txt" <<EOF
LAB:    lab-01c-stdout-redirection-verify
TASK:   2 of 2 — destroy-restore persistence drill
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname -s)
STATUS: COMPLETE
TRILOGY: lab-01 stdout redirection CLOSED
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    persistence — /tmp volatile, /root journal durable
COMMANDS: sha256sum, rm -rf, restore > and >>, find, stat, wc
EVIDENCE: /root/rhcsa_journal/lab01/task2c/evidence.txt
TRAPS:    T41 (persistence), T44 (final cleanup audit)
MISSED:   [list any quiz question you got wrong, or "none"]
NEXT:     lab-02a (stderr redirection) — rotation dir becomes /etc
EOF

echo "Journal written: $(ls -la $JDIR)"
echo "exit was: $?"
```

Paste output.

---

### Cleanup (Section 6 — final trilogy teardown)

Run the full Section 6 block from lab-01a. Every audit row must say
`(OK)`. This is the last chance to catch T44 before starting lab-02.

```bash
set +e

podman ps -aq --filter "name=^${CTR}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy  "${VG}"          2>/dev/null
    vgremove -fy  "${VG}"          2>/dev/null
fi

losetup -j "${SANDBOX}/disk.img" 2>/dev/null \
    | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

if getent passwd "${LAB_USER}" >/dev/null 2>&1; then
    userdel -r "${LAB_USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}"  2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── cleanup audit ──"
getent passwd "${LAB_USER}"  && echo "user remains (FAIL)"   || echo "user gone (OK)"
getent group  "${GROUP}"     && echo "group remains (FAIL)"  || echo "group gone (OK)"
test -d "${SANDBOX}"         && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

Paste all `(OK)` rows.

---

### Drill + rotation (trilogy closeout)

```bash
python3 ~/scripts/rhcsa_drill.py --category io
python3 ~/scripts/rhcsa_drill.py --category fhs
echo "last_used=01" > /root/rhcsa_journal/dir_rotation.txt
cat                  /root/rhcsa_journal/dir_rotation.txt
```

Paste drill scores and rotation file. Next topic's practice directory
is `/etc` (rotation slot 02).

**STOP — lab-01 trilogy complete.** Topic 01 stdout redirection is
closed. Resume agent will read `/root/rhcsa_journal/lab01/` and refuse
to start lab-02a until all three `done.txt` checkpoints exist.
