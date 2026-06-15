# lab-01c — stdout redirection — verification capstone

The auditor seat. Hand-typed RHCSA inspection only — no Ansible CLI
(Section 17). You *prove* lab-01a's `>`/`>>` behavior with evidence, then
run a T41 destroy-restore drill that separates volatile `/tmp` from durable
`/root` journal artifacts.

This is a VERIFY lab, so we never hide the checking — the checking IS the
lesson. Every step is shaped the same way: **run an audit command, then read
its result in plain English.** An "audit" here just means *a command you run
to prove a fact about the system instead of trusting your memory.* For every
audit line you'll see three things spelled out: what it checks, what a PASS
looks like, and what a FAIL would mean.

Built per `cursor-adhd-lab-prompt.txt` sections 0–20. Two tasks, no more.
Begins after `lab-01a` and `lab-01b` are complete.

---

## LAB HEADER (confirm or correct before Task 1)

**In plain English:** This block records the machine you're on so we agree on
the environment. The lines with `$(...)` mean "run this and paste its answer
here" — the shell runs what's inside the parentheses and substitutes the
result.

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

Line by line:

- `ENV: BAREMETAL` — Note this runs on real hardware, not a virtual
  machine.
- `DISK: /dev/sda` / `NIC: ens3` — The names Linux gives the first disk and
  the network card; labels only here.
- `SE: $(getenforce 2>/dev/null || echo n/a)` — Ask SELinux what mode it's
  in; `2>/dev/null` discards any error, and `||` ("or else") prints `n/a`
  if the command fails.
- `OS: $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')` —
  Find the friendly OS name: `grep` pulls the line, the `|` (pipe) hands it
  to `cut` which keeps the part after `=`, and `tr -d '"'` deletes the
  quotes.
- `TIME: $(date -Is)` — Print the current time in tidy ISO format (`-Is` =
  ISO, to the second).
- `USER: $(whoami)@$(hostname -s)` — Show your login name and the short
  machine name (`-s` = short, no domain).
- `TRAPS:` line — The four mistakes this lab audits for: a silent `>`
  truncation, an unquoted redirect target, a cleanup orphan, and faulty
  persistence reasoning.
- `PRACTICE DIR: /tmp` — Where we scribble; wiped on reboot.

Trap selection (Section 12 — exactly 4):
- **T01-A** + **T01-B** — io category (audit the behaviors directly)
- **T44** — repeated from lab-01b (cleanup orphan audit)
- **T41** — Meta/Strategy rotation (destroy-restore persistence drill)

---

## LAB-WIDE SETUP (run once before Task 1; paste output)

**In plain English:** Build the workspace, the throwaway group and user that
own it, and re-create the canonical three-line file from lab-01a so we have
something correct to audit. Run this whole block once.

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

Line by line:

- `export LAB_NUM=01` — Save the number `01` so we can reuse it everywhere
  instead of retyping it. (`export` makes the variable visible to other
  commands.)
- `export LAB_SLUG=stdout-redirection` — Save the topic's short text label.
- `export SANDBOX=/tmp/labsandbox_${LAB_NUM}` — Build the playground path;
  `${LAB_NUM}` pastes in the `01`.
- `export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}` — Save the owning group's
  name.
- `# Never use USER= ...` — A comment (`#` = "ignore this line") warning
  that `USER` is special to bash.
- `export LAB_USER=labuser_${LAB_NUM}_${LAB_SLUG}` — Save the throwaway
  user's name.
- `export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}` — Save that user's home
  path inside the sandbox.
- `mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"` — Create both folders; `-p` =
  "don't error if they exist, and make parent folders as needed."
- `getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"` — Check if the
  group exists; if not, create it. (`>/dev/null` = "hide normal output.")
- `getent passwd "${LAB_USER}" >/dev/null || useradd \` — Check if the user
  exists; if not, create it. The `\` continues the command on the next line.
- `-d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"` —
  `useradd` options: `-d` sets the home folder, `-M` means "don't make a
  home directory," `-s` sets the login shell, `-g` sets the main group.
- `chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"` — Give the sandbox to our
  user and group; `-R` = "recursively, including everything inside."
- `echo "alpha" > "${SANDBOX}/notes.txt"` — Start the file fresh with
  `alpha`; the single `>` *truncates* (empties to zero bytes) first.
- `echo "bravo" >> "${SANDBOX}/notes.txt"` — Append `bravo` without erasing;
  `>>` (two of them) means "add to the bottom."
- `echo "charlie" >> "${SANDBOX}/notes.txt"` — Append `charlie` the same
  way, giving us the canonical three-line file to audit.
- `id "${LAB_USER}"` — Print the user's IDs and groups to confirm it was
  created.
- `ls -la "${SANDBOX}/"` — List the sandbox contents; `-l` = long format,
  `-a` = include hidden files.
- `echo "Sandbox ready at $(date -Is)"` — Print a confirmation with the
  current time.
- `echo "exit was: $?"` — Print the *exit status* (the success/failure code
  the last command left behind; `0` = success, non-zero = failure) of the
  previous line.

**New words in this step:**
- **audit** — running a command to *prove* a fact about the system instead
  of trusting your memory.
- **exit status** — the number a command leaves behind to report success
  (`0`) or failure (non-zero).
- **truncate** — to instantly empty a file to zero bytes (what a single `>`
  does before writing).

Paste output. You should see `notes.txt` and three lines when we `cat` it
next.

---

## TASK 1 of 2 — Audit: prove `>` truncates and `>>` preserves

**In plain English:** We verify a correctly-built file with hard evidence:
count its lines, watch a single `>` destroy two of them, rebuild it the
right way, then inspect ownership and compare it byte-for-byte against what
we expect. The numbers do the talking.

```
LAB:   lab-01c — stdout redirection — verify
TASK:  1 of 2 — audit > vs >> with wc -l, cat, stat
TRAPS: T01-A T01-B T44 T41
```

### Quiz warm-up (from lab-01b)

- **Q1:** Why does `ansible-playbook` show `changed=1` every run for a
  `shell:` task that uses `>`? (Hint: that's a failure of *idempotence* —
  running a thing twice not giving the same end-state-with-no-extra-change.)
- **Q2:** What is T01-B?

Confirm or correct before we proceed.

---

### Step 1 of 2 — Audit line counts to prove `>` destroys and `>>` preserves

**In plain English:** This whole step is one audit told as a story in numbers.
First we count the good file's lines (proof `>>` built it). Then we fire a
single `>` and re-count (the count drops — proof of the T01-A silent
truncation). Then we rebuild correctly and re-count (the count returns —
proof `>>` preserves). Read the `wc -l` number after each block; that number
is the verdict.

Run the baseline audit:

```bash
wc -l < "${SANDBOX}/notes.txt"
cat -n "${SANDBOX}/notes.txt"
```

Before I explain — what does `-n` add to `cat`?

**After you've answered, line by line:**

- `wc -l < "${SANDBOX}/notes.txt"` — **Checks:** how many lines the file
  has; `-l` = count lines, `<` feeds the file as input so the output is just
  the bare number. **PASS:** prints `3`. **FAIL:** any other number means
  the file isn't the canonical three lines.
- `cat -n "${SANDBOX}/notes.txt"` — **Checks:** the actual contents; `-n`
  numbers each line. **PASS:** shows `1 alpha`, `2 bravo`, `3 charlie`.
  **FAIL:** missing or reordered lines.

Now trigger T01-A on purpose and re-audit:

```bash
echo "only newest" > "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
cat -n "${SANDBOX}/notes.txt"
```

Before I explain — predict `wc -l` after the `>`.

**After you've answered, line by line:**

- `echo "only newest" > "${SANDBOX}/notes.txt"` — A single `>` truncates the
  file to empty, then writes one line; this is T01-A, the silent
  destruction.
- `wc -l < "${SANDBOX}/notes.txt"` — **Checks:** the new line count.
  **PASS (trap confirmed):** prints `1`, proving two lines were silently
  lost. **FAIL:** still `3` would mean the `>` somehow didn't truncate.
- `cat -n "${SANDBOX}/notes.txt"` — **Checks:** contents. **PASS:** shows
  only `1 only newest`; `alpha`/`bravo`/`charlie` are gone with no warning.

Now restore it correctly and audit again:

```bash
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
wc -l < "${SANDBOX}/notes.txt"
cat "${SANDBOX}/notes.txt"
```

**After you've answered, line by line:**

- `echo "alpha" > "${SANDBOX}/notes.txt"` — The first line MUST use `>` to
  start fresh; using `>>` here would append onto stale data.
- `echo "bravo" >> ...` / `echo "charlie" >> ...` — Append the other two
  lines without truncating (the contrast to the `>` above).
- `wc -l < "${SANDBOX}/notes.txt"` — **Checks:** line count is restored.
  **PASS:** back to `3`. **FAIL:** anything else means the rebuild went
  wrong.
- `cat "${SANDBOX}/notes.txt"` — **Checks:** all three lines are present and
  in order.

An audit isn't only about breaking things — you must also prove you can
*restore to a known-good state*. Paste all three blocks' output.

**New words in this step:**
- **idempotence** — the property that running something twice leaves the
  same end state with no extra change (a `>` timestamp write is *not*
  idempotent).

---

### Step 2 of 2 — Inspection audit: `stat`, `ls -l`, `diff`, and capture evidence

**In plain English:** Now we run the three classic RHCSA inspection commands
on the restored file — ownership/permissions, the long listing, and a
byte-for-byte comparison against an expected copy — then save the whole audit
transcript to the durable journal as proof.

Run the metadata and content audits:

```bash
stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt"
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

**After you've answered, line by line:**

- `stat -c '%U:%G %a %n' "${SANDBOX}/notes.txt"` — **Checks:** ownership and
  permissions; `stat` reads file metadata and `-c '%U:%G %a %n'` prints just
  the user owner, group owner, octal mode, and name. **PASS:** owner/group
  match the lab user/group from setup. **FAIL:** `root:root` or wrong
  permissions means ownership drifted.
- `ls -l "${SANDBOX}/notes.txt"` — **Checks:** the long listing (permissions,
  owner, size, modified time). **PASS:** a normal `-rw-` regular file with a
  non-zero size. **FAIL:** zero size would mean the file got truncated
  again.
- `cat > /tmp/expected_notes.txt <<'EOF' ... EOF` — Write a *heredoc* (a
  block of inline text fed straight into a file) holding the three lines we
  expect; the quoted `'EOF'` means "write the text exactly, no variable
  substitution."
- `diff -u /tmp/expected_notes.txt "${SANDBOX}/notes.txt" || true` —
  **Checks:** whether the real file matches the expected file byte-for-byte;
  `diff -u` shows a unified diff, and `|| true` ("or else succeed") keeps the
  exit status at `0` so an intentional difference doesn't halt the lab.
  **PASS:** no output (files identical). **FAIL:** any `-`/`+` lines mean the
  file content differs from expected.
- `echo "exit was: $?"` — Print the exit status; thanks to `|| true` it
  should read `0`.

A `diff -u` exit code of `1` on its own just means "the files differ" — it's
not an error, which is why we wrap it in `|| true`.

Now capture the evidence to the durable journal (Section 17d):

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

Line by line:

- `mkdir -p /root/rhcsa_journal/lab01/task1c` — Create the journal folder
  for this task's evidence (`-p` = make parents, don't error if present).
- `{ ... }` — Group several commands so their combined output can be
  redirected as one stream.
- the four commands inside the braces — Re-run the same line count, stat,
  listing, and diff audits so the evidence file holds the full proof.
- `} 2>&1 | tee /root/rhcsa_journal/lab01/task1c/evidence.txt` — `2>&1` sends
  error text into the same stream as normal output, then `|` (pipe) hands it
  to `tee`, which both writes it to `evidence.txt` and shows it on screen.
- `echo "exit was: $?"` — Print the exit status of the capture.

**Checks:** that a durable, timestamp-able record of the audit now exists on
`/root`. **PASS:** `evidence.txt` is written and printed. **FAIL:** a write
error (e.g. permission denied) means the journal capture didn't happen.

**New words in this step:**
- **heredoc** — a block of text typed inline that gets fed into a command or
  file, ending at a marker word like `EOF`.

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

**In plain English:** "Persistence" is the question *would this survive a
reboot?* We confirm the evidence lives on durable `/root` while `/tmp` is
volatile.

```bash
test -f /root/rhcsa_journal/lab01/task1c/evidence.txt && echo "evidence on /root (survives reboot)"
findmnt /tmp | head -2
```

Line by line:

- `test -f /root/rhcsa_journal/lab01/task1c/evidence.txt && echo "evidence on /root (survives reboot)"`
  — **Checks:** the evidence file exists; `test -f` asks "is this a regular
  file?" and `&&` runs the echo only if so. **PASS:** prints the message,
  proving the proof is on durable storage. **FAIL:** silence means the
  evidence didn't get saved.
- `findmnt /tmp | head -2` — **Checks:** what `/tmp` is mounted on; `head -2`
  keeps just the header and first line. **PASS/reading:** `tmpfs` (or a
  filesystem cleaned at boot) confirms `/tmp` is volatile, so the sandbox
  file would NOT survive reboot.

**New words in this step:**
- **persistence** — whether a file *survives a reboot* (stays) or disappears.

Paste output.

---

### Journal write (before cleanup)

**In plain English:** Write the "I finished Task 1" record into the durable
`/root` journal.

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

Line by line:

- `LAB=lab01` / `TASK=task1c` — Save short labels for this lab and task.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the journal folder
  path.
- `mkdir -p "$JDIR"` — Create it, making parents as needed.
- `cat > "$JDIR/done.txt" <<EOF` plus its lines — Write the completion record;
  this unquoted `EOF` lets `$(date -Is)` and `$(whoami)`/`$(hostname -s)` run
  and paste their answers in.
- `cat > "$JDIR/notes.txt" <<EOF` plus its lines — Write the study notes:
  topic, where the evidence lives, the traps, and what's next.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm by listing the folder.
- `echo "exit was: $?"` — Print the exit status.

---

### Cleanup (Section 6)

**In plain English:** Tear down the lab user, group, and sandbox, then *audit*
that nothing was left behind. A leftover account, group, or folder is an
"orphan," and leaving one is the T44 mistake.

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

Line by line:

- `set +e` — Turn OFF "stop on first error" so cleanup keeps going even if a
  step has nothing to remove.
- `if getent passwd "${LAB_USER}" >/dev/null 2>&1; then userdel -r "${LAB_USER}" 2>/dev/null; fi`
  — If the lab user exists, delete it; `-r` also removes its home directory.
- `if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi`
  — If the lab group exists, delete it.
- `rm -rf "${SANDBOX}"` — Delete the sandbox and everything in it; `-r` =
  recursive, `-f` = force (no prompts, no error if missing).
- `echo "── cleanup audit ──"` — Print a header for the verification lines.
- `getent passwd "${LAB_USER}" && echo "user remains (FAIL)" || echo "user gone (OK)"`
  — **Checks:** is the user still there? **PASS:** `user gone (OK)` — it's
  removed. **FAIL:** `user remains (FAIL)` — an orphan account is left.
- `getent group "${GROUP}" && echo "group remains (FAIL)" || echo "group gone (OK)"`
  — **Checks:** the group. **PASS:** `group gone (OK)`. **FAIL:** orphan
  group remains.
- `test -d "${SANDBOX}" && echo "sandbox remains (FAIL)" || echo "sandbox gone (OK)"`
  — **Checks:** the folder; `test -d` asks "is this a directory?" **PASS:**
  `sandbox gone (OK)`. **FAIL:** the folder is still on disk.
- `set -e` — Turn "stop on first error" back on.
- `echo "exit was: $?"` — Print the final exit status.

**New words in this step:**
- **orphan** — a leftover user, group, or directory that cleanup missed.

All rows `(OK)`. **STOP** before Task 2.

---

## TASK 2 of 2 — T41 destroy-restore persistence drill

**In plain English:** This task proves you can survive a "reboot." We
fingerprint the file, wipe the volatile `/tmp` sandbox, confirm the durable
`/root` journal is untouched, rebuild the file from muscle memory, and prove
the rebuild is byte-identical — then close out the trilogy with a final
audit. Every step is "destroy or rebuild, then audit the result."

```
LAB:   lab-01c — stdout redirection — verify
TASK:  2 of 2 — destroy /tmp state, restore from journal, close trilogy
TRAPS: T01-A T01-B T44 T41
```

### Quiz warm-up (from Task 1)

- **Q1:** After `echo x > file`, how many lines does `wc -l` show if the
  file had 10 lines before?
- **Q2:** Where is `evidence.txt` stored — `/tmp` or `/root`?

Confirm or correct. Re-run **LAB-WIDE SETUP** (Task 1 cleanup cleared
sandbox).

---

### Step 1 of 2 — Record the before-state, then destroy volatile state and audit what survives

**In plain English:** First we take a cryptographic fingerprint of the file so
we can later prove an exact match. Then we delete the whole `/tmp` sandbox to
simulate a reboot, and audit two things: the sandbox is gone (volatile) and
the `/root` evidence is still there (durable). That contrast is the entire
T41 lesson.

Record the before-state:

```bash
BEFORE_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')
echo "BEFORE hash: ${BEFORE_HASH}"
wc -l < "${SANDBOX}/notes.txt"
```

**After you've answered, line by line:**

- `BEFORE_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')` —
  Compute a `sha256sum` (a fingerprint that changes if even one byte
  changes) and store it; `$(...)` means "run this and paste its answer here,"
  the `|` pipes the result to `awk '{print $1}'` which keeps only the hash
  (the first field), and `BEFORE_HASH=` saves it in a variable.
- `echo "BEFORE hash: ${BEFORE_HASH}"` — Print the saved fingerprint so you
  can see it.
- `wc -l < "${SANDBOX}/notes.txt"` — **Checks:** the starting line count.
  **PASS:** `3`. **FAIL:** anything else means setup didn't rebuild the file.

Now destroy the volatile state and audit:

```bash
rm -rf "${SANDBOX}"
test -d "${SANDBOX}" && echo "sandbox STILL exists (FAIL)" || echo "sandbox gone (OK)"
test -f /root/rhcsa_journal/lab01/task1c/evidence.txt \
  && echo "journal evidence survives (OK)" \
  || echo "evidence missing (FAIL)"
```

**After you've answered, line by line:**

- `rm -rf "${SANDBOX}"` — Delete the sandbox tree, simulating `/tmp` being
  cleared on reboot; `-r` = recursive, `-f` = force.
- `test -d "${SANDBOX}" && echo "sandbox STILL exists (FAIL)" || echo "sandbox gone (OK)"`
  — **Checks:** did the volatile folder really disappear? **PASS:** `sandbox
  gone (OK)`. **FAIL:** `sandbox STILL exists (FAIL)` means the delete
  didn't take.
- `test -f /root/rhcsa_journal/lab01/task1c/evidence.txt && echo "journal evidence survives (OK)" || echo "evidence missing (FAIL)"`
  — **Checks:** did the durable journal survive the "reboot"? **PASS:**
  `journal evidence survives (OK)` — `/root` is a different, persistent
  mount. **FAIL:** `evidence missing (FAIL)` means Task 1's capture never
  happened.

The pair of audits is the whole point of T41: volatile scratch is gone,
durable journal remains. Paste both blocks' output.

**New words in this step:**
- **`sha256sum`** — a tool that produces a fixed fingerprint of a file's
  exact bytes; identical files share a hash, any change flips it.

---

### Step 2 of 2 — Restore from muscle memory, prove byte-identical, then trilogy closeout audit

**In plain English:** We rebuild the file using the same `>`-then-`>>` idiom
from lab-01a, fingerprint it again, and prove the new hash matches the old
one (byte-identical restore). Then we audit the whole trilogy's journal
artifacts and advance the practice-directory rotation.

Restore and verify the match:

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

**After you've answered, line by line:**

- `mkdir -p "${SANDBOX}"` — Recreate the sandbox folder we just deleted.
- `echo "alpha" > "${SANDBOX}/notes.txt"` — Start fresh with `>` (using `>>`
  here would append to stale data).
- `echo "bravo" >> ...` / `echo "charlie" >> ...` — Append the other two
  lines, exactly reproducing the original file.
- `AFTER_HASH=$(sha256sum "${SANDBOX}/notes.txt" | awk '{print $1}')` —
  Fingerprint the rebuilt file and store it.
- `echo "AFTER hash:  ${AFTER_HASH}"` / `echo "BEFORE hash: ${BEFORE_HASH}"`
  — Print both fingerprints side by side so you can eyeball them.
- `test "${BEFORE_HASH}" = "${AFTER_HASH}" && echo "restore MATCH (OK)" || echo "restore MISMATCH (FAIL)"`
  — **Checks:** are the two fingerprints identical? **PASS:** `restore MATCH
  (OK)` — your rebuild is byte-for-byte the same as before the "reboot."
  **FAIL:** `restore MISMATCH (FAIL)` means a stray space, extra line, or
  `>>`-vs-`>` slip changed the bytes.

Now the trilogy closeout audit and rotation tracker:

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

Line by line:

- `echo "=== journal checkpoints ==="` — Print a header for the next audit.
- `find /root/rhcsa_journal/lab01 -name done.txt | sort` — **Checks:** which
  task-completion records exist; `find` lists files named `done.txt` and
  `sort` orders them. **PASS:** all three labs' `done.txt` files appear.
  **FAIL:** a missing one means a lab/task wasn't finished.
- `echo "=== boundary doc ==="` — Header for the boundary-document audit.
- `test -f .../BOUNDARY.txt && cat ... || echo "run lab-01b first if missing"`
  — **Checks:** lab-01b's boundary note exists; `test -f` confirms it, then
  `cat` prints it, or else the `||` message reminds you to run lab-01b.
  **PASS:** the boundary text prints. **FAIL:** the reminder prints.
- `mkdir -p /root/rhcsa_journal/lab01/task2c` — Create the closeout evidence
  folder.
- `{ ... } 2>&1 | tee /root/rhcsa_journal/lab01/task2c/evidence.txt` — Group
  the closeout commands, merge errors into normal output (`2>&1`), and `tee`
  the combined transcript both to screen and to `evidence.txt`.
- inside the braces: `echo "=== TRILOGY CLOSEOUT $(date -Is) ==="`,
  `find ... -type f | sort`, `wc -l < ...` — Stamp the time, list every
  journal file, and record the final line count as the closeout proof.
- `echo "last_used=01" > /root/rhcsa_journal/dir_rotation.txt` — Write the
  rotation marker (overwriting the file with `>`).
- `cat /root/rhcsa_journal/dir_rotation.txt` — Read it back to confirm.
- `echo "exit was: $?"` — Print the final exit status.

Paste output. Hashes should match and every checkpoint should be listed.

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

"If we rebooted now, could you resume topic 01 from the journal alone? Name
three files that prove it."

Then run:

```bash
find /root/rhcsa_journal/lab01 -name done.txt | sort
```

- `find /root/rhcsa_journal/lab01 -name done.txt | sort` — **Checks:** the
  durable completion records survive independent of `/tmp`. **PASS:** the
  three `done.txt` files list out, proving you could resume from `/root`
  alone. **FAIL:** a gap means a checkpoint wasn't written.

Paste output.

---

### Journal write (before final cleanup)

**In plain English:** Write the final "trilogy closed" record into the durable
journal.

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

Line by line:

- `LAB=lab01` / `TASK=task2c` — Short labels for this lab and task.
- `JDIR="/root/rhcsa_journal/${LAB}/${TASK}"` — Build the journal folder
  path.
- `mkdir -p "$JDIR"` — Create it, making parents as needed.
- `cat > "$JDIR/done.txt" <<EOF` plus its lines — Write the completion record,
  including the `TRILOGY: ... CLOSED` line; the unquoted `EOF` lets the
  `$(...)` parts run.
- `cat > "$JDIR/notes.txt" <<EOF` plus its lines — Write the closing notes:
  the persistence lesson, evidence path, traps, rotation, and next topic.
- `echo "Journal written: $(ls -la $JDIR)"` — Confirm by listing the folder.
- `echo "exit was: $?"` — Print the exit status.

---

### Cleanup (Section 6 — final trilogy teardown)

**In plain English:** Final teardown and orphan audit for the whole trilogy.
Every row must read `(OK)`.

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

Line by line:

- `set +e` — Turn off stop-on-error so cleanup runs to the end.
- `if getent passwd "${LAB_USER}" ...; then userdel -r "${LAB_USER}" ...; fi`
  — If the lab user exists, delete it along with its home (`-r`).
- `if getent group "${GROUP}" ...; then groupdel "${GROUP}" ...; fi` — If the
  lab group exists, delete it.
- `rm -rf "${SANDBOX}"` — Delete the sandbox tree (`-r` recursive, `-f`
  force).
- `echo "── cleanup audit ──"` — Header for the verification lines.
- `getent passwd "${LAB_USER}" && ... (FAIL) || ... (OK)` — **Checks:** the
  user is gone. **PASS:** `user gone (OK)`. **FAIL:** orphan user remains.
- `getent group "${GROUP}" && ... (FAIL) || ... (OK)` — **Checks:** the group
  is gone. **PASS:** `group gone (OK)`. **FAIL:** orphan group remains.
- `test -d "${SANDBOX}" && ... (FAIL) || ... (OK)` — **Checks:** the folder is
  gone. **PASS:** `sandbox gone (OK)`. **FAIL:** folder remains.
- `set -e` — Re-enable stop-on-error.
- `echo "Cleanup complete at $(date -Is)"` / `echo "exit was: $?"` — Print a
  timestamped confirmation and the final exit status.

All rows must say `(OK)`.

### Drill (trilogy closeout)

**In plain English:** Run the tier-1 practice quiz to confirm the whole topic
stuck.

```bash
python3 ~/scripts/rhcsa_drill.py --tier 1
```

- `python3 ~/scripts/rhcsa_drill.py --tier 1` — Run the drill script limited
  to tier-1 questions.

**STOP — lab-01 trilogy complete.** Topic 02 begins only after all `done.txt`
checkpoints under `/root/rhcsa_journal/lab01/` exist and cleanup audit shows
`(OK)`.
