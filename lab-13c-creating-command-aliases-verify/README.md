# Lab 13c: Verifying Aliases — audit + persistence

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `13a` (RHCSA) → `13b` (Ansible) → **`13c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex on rc-file changes), RHCE EX294 (auditor seat for `blockinfile` deployments)
- **Prerequisite:** Lab 13a and Lab 13b complete
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = three-tool audit + cross-user proof, Task 2 = simulated logout/re-login re-source)
- **Practice Directory (rotation #13):** `/srv`
- **Sandbox:** read-only inspection of `/etc/profile.d/lab13b-managed-aliases.sh`
- **Traps rehearsed this lab:** **T13-E** (verifying with `bash -c 'type ll'` instead of `bash -ic` — bare bash never sources rc files) · **T41** (skipping the fresh-login simulation)

> **This lab's practice directory is: `/srv`** — the aliases under audit all reference `/srv`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T13-E T41"
echo "📁  PRACTICE DIR: /srv"
echo ""
echo "🧾 Journal check — 13a and 13b must be done:"
test -f /root/rhcsa_journal/lab-13a/task2/done.txt && echo "  lab-13a task2 done"
test -f /root/rhcsa_journal/lab-13b/task2/done.txt && echo "  lab-13b task2 done"
test -f /etc/profile.d/lab13b-managed-aliases.sh && echo "  managed alias file present (left by 13b)"
```

> **STOP — if either `done.txt` is missing, finish the prior labs first.**

---

## Objective

Audit the managed alias file from three independent angles — file inspection, current-shell `type`, and fresh-subshell `bash -ic` — then prove the aliases survive a simulated logout by re-sourcing the file in a brand-new shell.

---

## Concept: Alias Audit Has Three Levels — Inspect All Three

| Level | Question | Primitive |
|---|---|---|
| **File** | Does the file exist with the right content + mode? | `ls -lZ` + `grep -c '^alias '` + `cat` |
| **Current shell** | Did the source step actually load them? | `type NAME` + `alias NAME` |
| **Fresh shell** | Will every new login session inherit them? | `bash -ic 'type NAME'` (interactive!) |

Verifying only level 1 leaves the question "does sourcing actually work?" unanswered. Verifying only levels 1+2 leaves "what about a different shell?" unanswered. All three are independent and all three are part of the audit.

> **T13-E** is the silent killer: running `bash -c 'type ll'` (NO `-i`) prints "command not found" even though the alias is correctly defined — because bash without `-i` does not source rc files at all. Always use `bash -ic`.

---

## Lab-Wide Setup

```bash
sudo -i
mkdir -p /tmp/lab13c

# Recreate the deployed file from the journal copy (in case Lab 13b's cleanup removed it)
if ! test -f /etc/profile.d/lab13b-managed-aliases.sh; then
  cp /root/rhcsa_journal/lab-13b/task1/deployed-file.sh /etc/profile.d/lab13b-managed-aliases.sh
  chmod 0644 /etc/profile.d/lab13b-managed-aliases.sh
  restorecon -v /etc/profile.d/lab13b-managed-aliases.sh
fi

ls -lZ /etc/profile.d/lab13b-managed-aliases.sh
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Three-level audit (file + current shell + fresh subshell)

**Practice directory this task:** `/srv` · we confirm `alias srv='cd /srv'` works at all three audit levels.

### Warm-Up

```bash
ls -lZ /etc/profile.d/lab13b-managed-aliases.sh           2>&1 | tee /tmp/lab13c/warmup.txt
grep -c '^alias ' /etc/profile.d/lab13b-managed-aliases.sh
cat /etc/profile.d/lab13b-managed-aliases.sh
type srv 2>&1 | head -n 1
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 13a/13b: `type NAME` and `bash -ic 'type NAME'` are the inspection primitives we keep using.

### Purpose

Walk through each of the four aliases in the managed file and prove they pass at all three audit levels: file content correct, current shell sees them, fresh interactive subshell sees them. Tally pass/fail; cross-check the per-shell alias count matches the file's alias count.

### WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `grep -c '^alias '` | Counts file aliases — the **declared count** drives the loop |
| `type NAME` | The inspection primitive used at level 2 (current shell) |
| `cat FILE` | Captures the file content snapshot for the journal |
| `2>&1 \| tee` | Captures the three-level audit transcript |
| `ls -lZ` | Mode + SELinux context — level 1 file inspection |
| `$(date -Is)` | Journal timestamp |

### Main command block

```bash
mkdir -p /tmp/lab13c/task1
TASKLOG=/tmp/lab13c/task1/audit.txt

# ── Level 1: file inspection ─────────────────────────────────────────
echo "═══ Level 1 — File inspection ═══" 2>&1 | tee $TASKLOG
ls -lZ /etc/profile.d/lab13b-managed-aliases.sh           2>&1 | tee -a $TASKLOG
grep -c "LAB 13B ALIASES" /etc/profile.d/lab13b-managed-aliases.sh \
  | awk '{print "  marker count: "$1}'                    2>&1 | tee -a $TASKLOG
FILE_ALIAS_COUNT=$(grep -c '^alias ' /etc/profile.d/lab13b-managed-aliases.sh)
echo "  file alias count: $FILE_ALIAS_COUNT"              2>&1 | tee -a $TASKLOG

# Build the list of expected alias names from the file
mapfile -t EXPECTED_ALIASES < <(grep -oE "^alias [a-zA-Z_][a-zA-Z0-9_]*" /etc/profile.d/lab13b-managed-aliases.sh \
                                | awk '{print $2}')
echo "  expected aliases: ${EXPECTED_ALIASES[*]}"         2>&1 | tee -a $TASKLOG

# ── Level 2: current shell ───────────────────────────────────────────
echo "═══ Level 2 — Current shell ═══" 2>&1 | tee -a $TASKLOG
source /etc/profile.d/lab13b-managed-aliases.sh
PASS_L2=0
FAIL_L2=0
for name in "${EXPECTED_ALIASES[@]}"; do
  if type "$name" 2>/dev/null | grep -q "is aliased"; then
    echo "  PASS  $name" | tee -a $TASKLOG
    PASS_L2=$(( PASS_L2 + 1 ))
  else
    echo "  FAIL  $name (not aliased in current shell)" | tee -a $TASKLOG
    FAIL_L2=$(( FAIL_L2 + 1 ))
  fi
done

# ── Level 3: fresh interactive subshell ──────────────────────────────
echo "═══ Level 3 — Fresh interactive subshell (bash -ic) ═══" 2>&1 | tee -a $TASKLOG
PASS_L3=0
FAIL_L3=0
for name in "${EXPECTED_ALIASES[@]}"; do
  if bash -ic "type $name" 2>/dev/null | grep -q "is aliased"; then
    echo "  PASS  $name" | tee -a $TASKLOG
    PASS_L3=$(( PASS_L3 + 1 ))
  else
    echo "  FAIL  $name (not aliased in fresh subshell)" | tee -a $TASKLOG
    FAIL_L3=$(( FAIL_L3 + 1 ))
  fi
done

# ── Cross-check level counts ─────────────────────────────────────────
echo "═══ Summary ═══" 2>&1 | tee -a $TASKLOG
echo "  Level 1 (file):           $FILE_ALIAS_COUNT aliases declared" | tee -a $TASKLOG
echo "  Level 2 (current shell):  $PASS_L2 pass / $FAIL_L2 fail" | tee -a $TASKLOG
echo "  Level 3 (fresh subshell): $PASS_L3 pass / $FAIL_L3 fail" | tee -a $TASKLOG

if [ "$FILE_ALIAS_COUNT" = "$PASS_L2" ] && [ "$PASS_L2" = "$PASS_L3" ]; then
  echo "  ALL THREE LEVELS AGREE — audit OK" | tee -a $TASKLOG
else
  echo "  LEVELS DISAGREE — investigate" | tee -a $TASKLOG
fi

# Demonstrate T13-E: bash -c (no -i) returns nothing
echo "═══ T13-E demonstration: bash -c (no -i) — should print 'not found' ═══" \
  2>&1 | tee -a $TASKLOG
bash -c 'type ll' 2>&1 | tee -a $TASKLOG

echo "exit was: $?"
```

### Human-readable breakdown

1. **Level 1.** `ls -lZ` shows mode + SELinux context. `grep -c '^alias '` counts alias lines. `grep -oE "^alias \w+"` extracts the alias names into a bash array.
2. **Level 2.** Source the file (so the aliases load into the current shell). Loop over the alias names; for each, run `type NAME` and check if "is aliased" appears in the output. PASS/FAIL counter.
3. **Level 3.** Same loop, but run `bash -ic 'type NAME'` for each — fresh subshell, interactive mode, sources rc files. PASS/FAIL counter.
4. **Cross-check.** All three counts must agree. If Level 1 says four aliases but Level 3 says only three, one alias is broken (typo, syntax error, name collision with builtin).
5. **T13-E demo.** Run `bash -c 'type ll'` (NO `-i`). Returns "command not found" because non-interactive bash never sources rc files. This is the trap — looks like the alias is broken; actually the test is broken.

### Reading it left to right

- `mapfile -t ARR < <(cmd)` — read command output line-by-line into bash array; `-t` strips trailing newlines.
- `grep -oE 'PATTERN'` — `-o` print only matching part, `-E` extended regex.
- `for name in "${ARR[@]}"; do ... done` — iterate array elements with double-quotes to preserve any with spaces (defensive — alias names can't have spaces, but the pattern matters).
- `type "$name" 2>/dev/null | grep -q "is aliased"` — `type` reports "X is aliased to '...'" for aliases; `-q` makes grep silent and returns 0/1 via exit code.
- `bash -ic "type $name"` — fresh interactive subshell.

### The story

The three-level audit is the analog of Lab 12c's four-property audit for directories. Instead of `existence × mode × owner × group`, it's `file content × current shell × fresh subshell`. The pedagogical point is the same: surface verification (level 1) is necessary but not sufficient. Functional verification (levels 2 and 3) is what proves the system actually works the way the file declares.

T13-E is the failure mode where candidates lose points by running `bash -c '...'` instead of `bash -ic '...'`. The fix is one letter. The cost of not knowing it is hours of debugging "why doesn't my alias work?" when in fact it works perfectly — only the test is wrong.

### Expected output

```text
═══ Level 1 — File inspection ═══
-rw-r--r--. 1 root root system_u:object_r:bin_t:s0 ... lab13b-managed-aliases.sh
  marker count: 2
  file alias count: 4
  expected aliases: ll srv svc listen
═══ Level 2 — Current shell ═══
  PASS  ll
  PASS  srv
  PASS  svc
  PASS  listen
═══ Level 3 — Fresh interactive subshell (bash -ic) ═══
  PASS  ll
  PASS  srv
  PASS  svc
  PASS  listen
═══ Summary ═══
  Level 1 (file):           4 aliases declared
  Level 2 (current shell):  4 pass / 0 fail
  Level 3 (fresh subshell): 4 pass / 0 fail
  ALL THREE LEVELS AGREE — audit OK
═══ T13-E demonstration: bash -c (no -i) — should print 'not found' ═══
bash: line 1: type: ll: not found
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Three-level audit | File + current shell + fresh subshell — three independent checks |
| `mapfile -t ARR < <(cmd)` | Read command output into bash array, line-per-element |
| `type NAME \| grep -q "is aliased"` | Scriptable alias presence check |
| `bash -ic` not `bash -c` | The `-i` flag is what triggers rc-file sourcing |
| Cross-count check | File count must equal Level 2 count must equal Level 3 count |
| **🪤 Trap Risk T13-E** | Using `bash -c` (no -i) in tests. Always `bash -ic` for fresh-shell alias verification. |

### PERSISTENCE CHECK

| What was verified | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-13c/task1/audit.txt` | Journal evidence |
| Three levels agree | `grep "ALL THREE LEVELS AGREE" /root/rhcsa_journal/lab-13c/task1/audit.txt` | The single-line win condition |
| T13-E demo captured | `grep "not found" /root/rhcsa_journal/lab-13c/task1/audit.txt` | The contrast that teaches the lesson |

### Journal write

```bash
LAB=lab-13c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab13c/task1/audit.txt "$JDIR/audit.txt"
cp /etc/profile.d/lab13b-managed-aliases.sh "$JDIR/file-snapshot.sh"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-level audit (file + current shell + bash -ic)
COMMANDS: ls -lZ, grep -oE, mapfile, type NAME, bash -ic 'type NAME', cross-count check
TRAPS:    T13-E rehearsed (demonstrated bash -c FAILS; bash -ic PASSES)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — simulated logout + re-source from /root journal copy
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/lab13c/task1
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Level 1 count differs from Level 2 | A line in the file is malformed (typo in `alias` keyword, syntax error). |
| Level 2 passes but Level 3 fails | The file isn't in `/etc/profile.d/` or doesn't end `.sh` |
| All levels fail | File missing entirely. Re-run Lab 13b task1.yml. |
| `bash -ic` reports "Inappropriate ioctl" | Some systems print this when bash detects no TTY. The alias still works; the warning is noise. |
| `mapfile` not found | Old bash (pre-4.0). Use `IFS=$'\n' ARR=( $(cmd) )` instead. |

> **STOP — paste the "ALL THREE LEVELS AGREE" line and the T13-E "not found" demo before Task 2.**

---

## Task 2 — Simulated logout: re-source from journal copy

**Practice directory this task:** `/srv` · we destroy then restore the system-wide alias file from the journal backup, simulating what a fresh-host bootstrap would look like.

### Warm-Up

```bash
test -f /etc/profile.d/lab13b-managed-aliases.sh && echo "managed file present"
test -f /root/rhcsa_journal/lab-13c/task1/file-snapshot.sh && echo "journal snapshot present"
stat -c '%n mountpoint=%m' /etc/profile.d /root/rhcsa_journal
ls -la /etc/profile.d/lab13b-managed-aliases.sh
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Three phases:

1. Confirm baseline: aliases work via `bash -ic`.
2. Destroy `/etc/profile.d/lab13b-managed-aliases.sh` (simulates fresh host or accidental deletion).
3. Restore from the journal snapshot under `/root/rhcsa_journal/lab-13c/task1/file-snapshot.sh`. Verify aliases work again via `bash -ic`.

This proves the **journal is reconstruction-grade**: a brand-new host could be brought into compliance by copying the snapshot back into `/etc/profile.d/`.

### WEAVE TRACE

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Shows mount points — explains WHY `/root/` survives reboot and tmpfs files don't |
| `test -f` on both files | Verifies preconditions for both the destroy and restore steps |
| `2>&1 \| tee` | Captures the timeline to `task2/timeline.txt` |
| `set -o pipefail` | Catches `tee` failures |
| `$(date -Is)` | Stamps each phase boundary |

### Main command block

```bash
mkdir -p /tmp/lab13c/task2
JDIR="/root/rhcsa_journal/lab-13c/task2"
mkdir -p "$JDIR"
TIMELINE="$JDIR/timeline.txt"

echo "═══ Phase 1: baseline (aliases work via bash -ic) ═══" \
  2>&1 | tee "$TIMELINE"
stat -c '  %n  is on  %m' /etc/profile.d /root/rhcsa_journal \
  | tee -a "$TIMELINE"
bash -ic 'type ll srv svc listen' 2>&1 | tee -a "$TIMELINE"

echo "═══ Phase 2: destroy the managed file ═══" | tee -a "$TIMELINE"
echo "  at $(date -Is)" | tee -a "$TIMELINE"
rm -f /etc/profile.d/lab13b-managed-aliases.sh
test ! -f /etc/profile.d/lab13b-managed-aliases.sh && echo "  managed file gone — expected" | tee -a "$TIMELINE"
bash -ic 'type ll' 2>&1 | tee -a "$TIMELINE"

echo "═══ Phase 3: restore from journal snapshot ═══" | tee -a "$TIMELINE"
cp /root/rhcsa_journal/lab-13c/task1/file-snapshot.sh /etc/profile.d/lab13b-managed-aliases.sh
chmod 0644 /etc/profile.d/lab13b-managed-aliases.sh
restorecon -v /etc/profile.d/lab13b-managed-aliases.sh 2>&1 | tee -a "$TIMELINE"
ls -lZ /etc/profile.d/lab13b-managed-aliases.sh        2>&1 | tee -a "$TIMELINE"

echo "═══ Phase 4: verify aliases work again via bash -ic ═══" | tee -a "$TIMELINE"
PASS=0
FAIL=0
for name in ll srv svc listen; do
  if bash -ic "type $name" 2>/dev/null | grep -q "is aliased"; then
    echo "  PASS  $name (restored)" | tee -a "$TIMELINE"
    PASS=$(( PASS + 1 ))
  else
    echo "  FAIL  $name" | tee -a "$TIMELINE"
    FAIL=$(( FAIL + 1 ))
  fi
done

echo "═══ Restoration summary: $PASS pass, $FAIL fail ═══" | tee -a "$TIMELINE"
test "$PASS" = "4" && echo "RESTORED — journal is reconstruction-grade" | tee -a "$TIMELINE"
echo "exit was: $?"
```

### Human-readable breakdown

1. **Phase 1** — baseline. All four aliases work via `bash -ic`. Mount points captured as context.
2. **Phase 2** — destroy. `rm -f` the managed file. Now `bash -ic 'type ll'` returns "not found." Same shell flag as before, different result — because the underlying file is gone.
3. **Phase 3** — restore from `/root/rhcsa_journal/lab-13c/task1/file-snapshot.sh`. Copy back to `/etc/profile.d/`, set mode 0644, restore SELinux context.
4. **Phase 4** — re-verify. Same `bash -ic` test, but now returns the aliases again. Tally pass/fail — all four must pass for the journal to be considered reconstruction-grade.

### The story

A journal that contains only `done.txt` and `notes.txt` is documentation. A journal that contains the actual deployed artifact (the alias file, the playbook, the configuration) is **reconstruction material**. On a real disaster — fresh VM, accidentally wiped `/etc`, host migration — you should be able to copy from the journal back into place and have a working system in minutes.

For this lab, the snapshot at `/root/rhcsa_journal/lab-13c/task1/file-snapshot.sh` is that reconstruction artifact. Task 2 proves it by destroying and rebuilding from it. If you ever need to seed a fresh host with the same aliases, that file is your source.

### Expected output

```text
═══ Phase 1: baseline (aliases work via bash -ic) ═══
  /etc/profile.d  is on  /
  /root/rhcsa_journal  is on  /
ll is aliased to `ls -lhA --color=auto'
srv is aliased to `cd /srv'
svc is aliased to `systemctl --no-pager status'
listen is aliased to `ss -tunap'
═══ Phase 2: destroy the managed file ═══
  at 2026-05-27T16:15:00-04:00
  managed file gone — expected
bash: line 1: type: ll: not found
═══ Phase 3: restore from journal snapshot ═══
Relabeled /etc/profile.d/lab13b-managed-aliases.sh from ...
-rw-r--r--. 1 root root system_u:object_r:bin_t:s0 ... lab13b-managed-aliases.sh
═══ Phase 4: verify aliases work again via bash -ic ═══
  PASS  ll (restored)
  PASS  srv (restored)
  PASS  svc (restored)
  PASS  listen (restored)
═══ Restoration summary: 4 pass, 0 fail ═══
RESTORED — journal is reconstruction-grade
exit was: 0
```

### Concept Card

| Concept | What it does |
|---|---|
| Journal as reconstruction artifact | Snapshot file enables fresh-host recovery in minutes |
| Mount-point awareness | `/etc/profile.d` on root partition; `/root/rhcsa_journal` on root partition — both survive |
| Destroy-then-restore drill | The only honest test that reconstruction actually works |
| `restorecon -v` after copy | SELinux context must be re-asserted after any non-Ansible file copy |
| Pass/fail tally + win condition | "RESTORED" line is the auditable success marker |
| **🪤 Trap Risk T41** | Skipping the destroy-restore test. The journal is only as good as its proven ability to rebuild. |

### PERSISTENCE CHECK (this lab IS persistence verification)

| What was verified | Verification command | Why it matters |
|---|---|---|
| Timeline saved | `wc -l /root/rhcsa_journal/lab-13c/task2/timeline.txt` | Journal proof |
| Restoration succeeded | `grep RESTORED /root/rhcsa_journal/lab-13c/task2/timeline.txt` | Single-line win |
| Trilogy complete | `find /root/rhcsa_journal/lab-13{a,b,c} -name done.txt \| wc -l` | Should be `6` |
| Managed file alive again | `bash -ic 'type ll srv svc listen'` | Functional re-verification |

### Journal write

```bash
LAB=lab-13c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Destroy + restore from journal snapshot — reconstruction proof
COMMANDS: rm -f + cp + chmod + restorecon, bash -ic loop verification
TRAPS:    T41 rehearsed (we did NOT skip the destroy-restore test)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-14a (searching-with-find)
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-13{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/lab13c
# Leave /etc/profile.d/lab13b-managed-aliases.sh in place — it's a deliberate test artifact
# Optional: rm -f /etc/profile.d/lab13b-managed-aliases.sh ~/.bashrc.bak.lab13.*
ls -la /etc/profile.d/lab13b-managed-aliases.sh
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Phase 3 restorecon errors | The `bin_t` context might not apply on non-RHEL distros. Skip and use the default. |
| Phase 4 some aliases FAIL | The journal snapshot was corrupted or had different content. Re-run Lab 13b task1.yml. |
| `bash -ic` warnings about no TTY | Cosmetic; the alias still works. |
| `restorecon` says no change | Mode was already correct on the source file — that's a success, not an error. |

> **STOP — paste the "RESTORED" line and the trilogy `done.txt` list before moving to Lab 14.**

---

## Lab 13c Checklist (2 tasks)

- [ ] Task 1 — Three-level audit (file + current shell + `bash -ic` fresh subshell) + T13-E demo
- [ ] Task 2 — Destroy and restore the managed file from journal snapshot; prove reconstruction-grade

---

## Lab 13 Trilogy — completion check

```bash
find /root/rhcsa_journal/lab-13{a,b,c} -name done.txt | sort
```

Expected: six paths. Do not start Lab 14a until the trilogy is closed.

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 13a** — RHCSA hand-typed aliases | The imperative source |
| **Lab 13b** — Aliases via Ansible | The declarative source |
| Lab 12c — Verifying Created Directories | Same audit pattern, different domain (mode/owner/group instead of file/shell/subshell) |
| Lab 14a — Searching with find | The first lab that doesn't deploy a persistent artifact — verification will look different |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
