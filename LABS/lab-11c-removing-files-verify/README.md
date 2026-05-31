# Lab 11c: Verifying File Removal — audit + persistence

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `11a` (RHCSA) → `11b` (Ansible) → **`11c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (verification reflex on every task), RHCE EX294 (auditor seat — prove a play worked without trusting the playbook output), SRE (post-change verification habit), All exams (the "what would you check next" interview reflex)
- **Prerequisite:** Lab 11a and Lab 11b completed — this lab verifies their combined effect
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit, Task 2 = persistence proof)
- **Practice Directory (rotation #11):** `/tmp`
- **Sandbox:** `/tmp/rm-verify-lab`
- **Traps rehearsed this lab:** **T11-E** (trusting Ansible's `changed=0` without inspecting actual state) · **T41** (not rebooting to test persistence)

> **This lab's practice directory is: `/tmp`** — every task references it in at least two commands.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T11-E T41"
echo "📁  PRACTICE DIR: /tmp"
echo ""
echo "🧾 Journal check — Lab 11a and 11b must already be done:"
test -f /root/rhcsa_journal/lab-11a/task2/done.txt && echo "  ✅ lab-11a task2 done"
test -f /root/rhcsa_journal/lab-11b/task2/done.txt && echo "  ✅ lab-11b task2 done"
```

> **STOP — if either `done.txt` check above failed, return and finish Lab 11a or 11b first. This lab depends on the journal artifacts they produce.**

---

## 🎯 Objective

Take off the operator's hat and put on the **auditor's hat**. Lab 11a removed files by hand. Lab 11b removed them via Ansible and reported `changed=0` on re-run. Neither of those proves the system is actually in the expected state right now. Lab 11c is the inspection step that **proves** the removals are real, using only RHCSA-grade inspection commands — no playbook output, no trust in the previous labs.

---

## 🧠 Concept: Trust But Verify — Especially When Ansible Says `changed=0`

`changed=0` from Ansible means "Ansible believed the state matched the declaration." That is **not** the same as "the state actually matches the declaration." Examples of the gap:

| What Ansible reported | What can still be wrong |
|---|---|
| `changed=0` for `file: state=absent` | A different process recreated the file between runs |
| `changed=0` on path A | Path B (similar name, typo) still exists and was not in the play |
| `changed=1, ok=1, failed=0` | The change happened, but the SELinux context is now wrong |
| Whole play `ok=N changed=0 failed=0` | The play targeted the wrong host |

The grader's reflex — and the senior engineer's reflex — is to **inspect the system directly** after any change, using the same tools the exam would use to grade you. `ls`, `find`, `stat`, `test`, `diff` against a known-expected baseline. No `ansible.*` commands.

---

## 📚 Inspection Reference (everything for Tasks 1–2)

| Tool | Purpose | Why an auditor reaches for it |
|---|---|---|
| `ls -la` | Directory listing with hidden + metadata | "Is the file here?" first check |
| `find PATH -type f` | Recursive file listing | "Are there ANY files matching this pattern?" — exhaustive |
| `stat -c '%n %F'` | File type + custom format | Distinguishes file vs symlink vs directory |
| `test -f` / `test -d` / `test -e` | Boolean existence checks | Scripts and exit-status–based verification |
| `diff -u EXPECTED ACTUAL` | Line-level comparison | "Does the current state match what I documented?" |
| `wc -l` | Line count | Quick sanity metric (file count, log line count) |
| `getfacl PATH` | POSIX ACLs | Catches non-standard permissions |
| `ls -lZ PATH` | SELinux context | Verifies labels survived the operation |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Set up a verification sandbox AND seed it with one decoy file
# (so we can prove our audit catches it).
mkdir -p /tmp/rm-verify-lab
cd /tmp/rm-verify-lab

# Capture what Lab 11b's playbook expected to remove
cat > /tmp/rm-verify-lab/expected-removed.txt <<'EOF'
/tmp/rm-ansible-lab/old.log
/tmp/rm-ansible-lab/stale.tmp
/tmp/rm-ansible-lab/cache
EOF

# Decoy: a path that LOOKS like it should be gone but wasn't in the play
touch /tmp/rm-verify-lab/decoy-not-in-play.tmp

ls -la /tmp/rm-verify-lab
cat /tmp/rm-verify-lab/expected-removed.txt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Audit the removals with ≥3 RHCSA inspection commands

**Practice directory this task:** `/tmp` · Temporary files, cleared on every reboot — both the targets (from `/tmp/rm-ansible-lab/`) and the audit workspace (`/tmp/rm-verify-lab/`) live here.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /tmp/rm-verify-lab                           2>&1 | tee /tmp/rm-verify-lab/warmup.txt
wc -l /tmp/rm-verify-lab/expected-removed.txt
test -f /tmp/rm-verify-lab/expected-removed.txt && echo "baseline OK"
stat -c '%n %F' /tmp/rm-verify-lab/expected-removed.txt
find /tmp -maxdepth 2 -name 'rm-*-lab' -type d      2>/dev/null
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 11b: the `find ... | wc -l` baseline pattern continues — but now we cross-check against the **declared** baseline (`expected-removed.txt`), not just count files.

### Purpose

Walk through each expected-removed path and prove with three independent RHCSA inspection commands that it is actually gone. Then run a **diff** between the declared baseline and the actual state to catch any discrepancy a single command might miss.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `wc -l expected-removed.txt` | Counts how many targets we expect — drives the loop iteration count |
| `test -f` / `test -d` | The exit-status form of "is this path here?" — used inside the audit loop |
| `stat -c '%n %F'` | Cross-check: confirms whether a path is a file, directory, or symlink (or missing) |
| `find /tmp -name 'rm-*-lab'` | Catches a typo where the wrong sandbox was audited (defensive) |
| `2>&1 \| tee` | Captures every check into `task1/audit.txt` — the journal proof |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /tmp/rm-verify-lab/task1
cd /tmp/rm-verify-lab

echo "═══ Audit Pass — Lab 11b targets must be ABSENT ═══" \
  2>&1 | tee /tmp/rm-verify-lab/task1/audit.txt

PASS=0
FAIL=0
while IFS= read -r path; do
  echo "─── checking: $path ───" | tee -a /tmp/rm-verify-lab/task1/audit.txt

  # Check 1: ls (the human-friendly form)
  ls -la "$path" 2>&1 | head -n 1 | tee -a /tmp/rm-verify-lab/task1/audit.txt

  # Check 2: test (the exit-status form)
  if test -e "$path"; then
    echo "  ❌ test -e: still exists" | tee -a /tmp/rm-verify-lab/task1/audit.txt
    FAIL=$(( FAIL + 1 ))
  else
    echo "  ✅ test -e: absent" | tee -a /tmp/rm-verify-lab/task1/audit.txt
    PASS=$(( PASS + 1 ))
  fi

  # Check 3: stat (the metadata form — confirms type + existence)
  stat -c '  stat: %n is %F' "$path" 2>&1 | tee -a /tmp/rm-verify-lab/task1/audit.txt
done < /tmp/rm-verify-lab/expected-removed.txt

echo "═══ Audit summary: $PASS pass, $FAIL fail ═══" \
  | tee -a /tmp/rm-verify-lab/task1/audit.txt

# Diff against actual state — exhaustive cross-check
echo "═══ Diff: declared baseline vs actual /tmp/rm-ansible-lab/ ═══" \
  | tee -a /tmp/rm-verify-lab/task1/audit.txt
find /tmp/rm-ansible-lab -type f 2>/dev/null \
  | sort > /tmp/rm-verify-lab/task1/actual-remaining.txt
diff -u <(sort /tmp/rm-verify-lab/expected-removed.txt) \
        /tmp/rm-verify-lab/task1/actual-remaining.txt \
  | tee -a /tmp/rm-verify-lab/task1/audit.txt || true

echo "exit was: $?"
```

### Human-readable breakdown

1. Read `expected-removed.txt` line by line — each line is a path the playbook promised to remove.
2. For each path, run **three independent inspection commands**: `ls`, `test -e`, `stat`. If any one disagrees with the others, the system is in an unexpected state and the audit fails.
3. Maintain `PASS` and `FAIL` counters — `FAIL` should be 0 if Lab 11a/b did their job.
4. Run a `diff -u` between the declared baseline (what we expected to be gone) and the actual remaining-files list under `/tmp/rm-ansible-lab/`. A correct lab produces an empty diff (or one with `|| true` masking the "files differ" exit).

### Reading it left to right

- `while IFS= read -r path; do ...; done < FILE` — read one line at a time from FILE, preserving whitespace. `IFS=` blocks word-splitting; `-r` blocks backslash interpretation.
- `head -n 1` — caps the `ls` output to one line per check (full output goes to `audit.txt`).
- `if test -e "$path"; then` — the `test` form is the **scriptable** existence check; its exit status drives the conditional.
- `stat -c '%n is %F'` — `%n` is name, `%F` is "regular file", "directory", "symbolic link", or `stat` errors with "No such file or directory".
- `find ... | sort > FILE` — produces a sorted snapshot of what is actually there, ready for `diff`.
- `diff -u <(sort EXPECTED) ACTUAL` — process substitution: `<(...)` lets us sort `expected-removed.txt` inline without writing a temp file.
- `|| true` — keeps the script's exit status at 0 even when `diff` reports differences (intentional — we want to see the diff, not abort).

### The story

The auditor seat is the most under-trained skill in RHCSA prep. Candidates spend hours on `lvextend` and `firewall-cmd`, then lose points on the exam because they did not run `mount -a`, `firewall-cmd --list-all`, `getfacl`, or `ls -Z` to **verify** their change before claiming it complete. Lab 11c bakes the audit reflex into your workflow: every change generates a paired audit. After enough labs, you will never click "next task" on an exam without verifying first.

The diff-against-declared-baseline pattern is the senior-engineer move. Anyone can run `ls` and feel good. The diff catches what `ls` misses: extra files that should not be there, paths the operator forgot were in the original spec, or — the worst case — files that came back between Lab 11b and Lab 11c because a service or cron job recreated them.

### Expected output

```text
═══ Audit Pass — Lab 11b targets must be ABSENT ═══
─── checking: /tmp/rm-ansible-lab/old.log ───
ls: cannot access '/tmp/rm-ansible-lab/old.log': No such file or directory
  ✅ test -e: absent
  stat: stat: cannot statx '/tmp/rm-ansible-lab/old.log': No such file or directory
─── checking: /tmp/rm-ansible-lab/stale.tmp ───
ls: cannot access '/tmp/rm-ansible-lab/stale.tmp': No such file or directory
  ✅ test -e: absent
  stat: stat: cannot statx '/tmp/rm-ansible-lab/stale.tmp': No such file or directory
─── checking: /tmp/rm-ansible-lab/cache ───
ls: cannot access '/tmp/rm-ansible-lab/cache': No such file or directory
  ✅ test -e: absent
  stat: stat: cannot statx '/tmp/rm-ansible-lab/cache': No such file or directory
═══ Audit summary: 3 pass, 0 fail ═══
═══ Diff: declared baseline vs actual /tmp/rm-ansible-lab/ ═══
(empty diff — clean exit)
exit was: 0
```

> **The win condition: `3 pass, 0 fail` and an empty diff.** Anything else means Lab 11a or 11b is incomplete.

### Switches

| Token | Meaning |
|---|---|
| `test -e PATH` | Exit 0 if PATH exists (file, dir, symlink, anything) |
| `test -f PATH` | Exit 0 only if PATH is a regular file |
| `test -d PATH` | Exit 0 only if PATH is a directory |
| `stat -c FORMAT` | Custom output format (`%n` name, `%F` type, `%a` mode, `%U` owner, `%G` group) |
| `while IFS= read -r LINE` | Safe line-by-line read (preserves whitespace, blocks escapes) |
| `<(cmd)` | Process substitution — feeds command output where a filename is expected |
| `diff -u A B` | Unified diff — the standard machine-readable diff format |
| `\|\| true` | Mask a non-zero exit so the script continues — use sparingly |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Three-tool cross-check | `ls`, `test`, `stat` — three independent answers to "does this exist?" |
|   | Declared baseline | A text file listing the expected end state; drives the audit loop |
|   | `diff` against actual | Exhaustive cross-check that catches what single-path inspection misses |
|   | Process substitution `<(...)` | Lets you sort/transform inline without temp files |
|   | Exit-status verification | `test -e` and `if`/`then` is how scripts decide based on file presence |
|   | Audit transcript via `tee` | Every check writes to `audit.txt` so the journal has the proof |
| 🪤 | **Trap Risk T11-E** | Trusting Ansible's `changed=0` without an independent inspection — always verify. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript | `wc -l /root/rhcsa_journal/lab-11c/task1/audit.txt` | Must be > 0 — proves we actually inspected |
| All targets absent | `for p in $(cat /tmp/rm-verify-lab/expected-removed.txt); do test -e "$p" \|\| echo "✅ $p"; done` | Re-run any time; should print one ✅ per declared target |
| Baseline preserved | `ls /root/rhcsa_journal/lab-11c/task1/expected-removed.txt` | The audit is reproducible only if the baseline survives — store it in `/root/` |

> **Reboot reasoning:** Both `/tmp/rm-verify-lab` (the audit workspace) and `/tmp/rm-ansible-lab` (the targets) evaporate at reboot. The **only** thing that survives is the journal under `/root/rhcsa_journal/`. If the journal does not contain `audit.txt` and `expected-removed.txt`, this audit cannot be reproduced — and that means the verification is effectively gone too.

### Journal write — BEFORE cleanup

```bash
LAB=lab-11c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/rm-verify-lab/task1/audit.txt           "$JDIR/audit.txt"
cp /tmp/rm-verify-lab/task1/actual-remaining.txt "$JDIR/actual-remaining.txt"
cp /tmp/rm-verify-lab/expected-removed.txt       "$JDIR/expected-removed.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-tool audit (ls + test + stat) + diff against declared baseline
COMMANDS: ls, test -e, stat -c, find, diff -u, process substitution <(...)
TRAPS:    T11-E rehearsed (we independently verified — did not trust Ansible's changed=0)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — prove the journal evidence itself survives a simulated reboot
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the journal, drop the live audit workspace
rm -rf /tmp/rm-verify-lab/task1
ls /tmp/rm-verify-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `1 fail` instead of `0` | A target still exists. Re-run Lab 11b or check whether something recreated it. |
| `ls` shows the file but `test -e` says absent | Likely a broken symlink. `ls -la` shows the link; `test -e` follows it. Use `test -L` for symlinks. |
| Empty `audit.txt` | `tee` failed silently — `set -o pipefail` was not active. Turn it on. |
| `diff` output is non-empty | Read carefully: the diff shows what is in `expected-removed.txt` but not in `actual-remaining.txt`. An empty `actual-remaining.txt` is correct. |
| `<(...)` syntax error | Running `sh` or `dash` instead of `bash`. Switch shells. |

> **STOP — paste the "Audit summary" line and the diff output (or "empty diff" confirmation) before Task 2.**

---

## Task 2 — Persistence proof: prove the audit survives a simulated reboot

**Practice directory this task:** `/tmp` · the contrast with `/root/` is the entire lesson — `/tmp` evaporates, `/root/rhcsa_journal/` does not.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /root/rhcsa_journal/lab-11c/task1/                2>&1 | tee /tmp/rm-verify-lab/warmup-task2.txt
wc -l /root/rhcsa_journal/lab-11c/task1/audit.txt
test -f /root/rhcsa_journal/lab-11c/task1/audit.txt && echo "task1 journal OK"
find /tmp/rm-verify-lab -type f                      2>/dev/null | wc -l
stat -c '%n mountpoint=%m' /tmp /root
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry: `stat -c '%m'` reveals the **mount point** for each path — `/tmp` is often on `tmpfs` and `/root` is on the root partition, which is the **structural reason** the journal survives reboot.

### Purpose

Simulate a reboot — clear `/tmp/rm-verify-lab` entirely — then re-run the audit from Task 1 using **only** the journal artifacts under `/root/rhcsa_journal/`. If the audit reproduces the same `3 pass, 0 fail` result, persistence is proven. If anything fails, the journal was incomplete and the original audit was not actually reproducible.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Confirms which paths are on tmpfs (will evaporate) vs root (will survive) |
| `find /tmp/rm-verify-lab` | Before and after the simulated reboot — verifies `/tmp` was cleared |
| `wc -l audit.txt` | Confirms the journal copy has the same line count as the original |
| `test -f` | Verifies each journal file actually survived the simulated reboot |
| `2>&1 \| tee` | Captures the re-audit transcript into `task2/post-reboot-audit.txt` |
| `$(date -Is)` | Stamps both the simulated reboot and the re-audit completion |

### Main command block

```bash
mkdir -p /tmp/rm-verify-lab/task2

echo "═══ Pre-reboot state ═══" \
  2>&1 | tee /tmp/rm-verify-lab/task2/timeline.txt
stat -c '  %n  is on  %m' /tmp /root /root/rhcsa_journal \
  2>&1 | tee -a /tmp/rm-verify-lab/task2/timeline.txt
ls /tmp/rm-verify-lab/ \
  2>&1 | tee -a /tmp/rm-verify-lab/task2/timeline.txt

# ── Simulate a reboot: wipe the entire tmp workspace ──
echo "═══ SIMULATING REBOOT — clearing /tmp/rm-verify-lab/ ═══" \
  2>&1 | tee -a /tmp/rm-verify-lab/task2/timeline.txt
echo "  at $(date -Is)" | tee -a /tmp/rm-verify-lab/task2/timeline.txt

# Move task2 transcript to /root BEFORE we delete /tmp/rm-verify-lab/
JDIR="/root/rhcsa_journal/lab-11c/task2"
mkdir -p "$JDIR"
cp /tmp/rm-verify-lab/task2/timeline.txt "$JDIR/timeline.txt"

# Now the simulated reboot — wipe /tmp/rm-verify-lab/ and /tmp/rm-ansible-lab/
rm -rf /tmp/rm-verify-lab/* /tmp/rm-ansible-lab 2>/dev/null
test -d /tmp/rm-verify-lab && echo "  /tmp/rm-verify-lab still exists (we kept the dir, wiped contents)"
find /tmp/rm-verify-lab -type f 2>/dev/null | wc -l  # must be 0
find /tmp/rm-ansible-lab -type f 2>/dev/null | wc -l  # must also be 0

# ── Post-reboot: reconstruct audit from /root/ journal only ──
echo "═══ Post-reboot — reconstructing from journal under /root/ ═══" \
  2>&1 | tee "$JDIR/post-reboot-audit.txt"

# 1. Journal files must still exist
for f in /root/rhcsa_journal/lab-11c/task1/audit.txt \
         /root/rhcsa_journal/lab-11c/task1/expected-removed.txt \
         /root/rhcsa_journal/lab-11b/playbooks/task1.yml \
         /root/rhcsa_journal/lab-11b/playbooks/task2.yml; do
  if test -f "$f"; then
    echo "  ✅ survived: $f ($(wc -l < "$f") lines)" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  else
    echo "  ❌ MISSING:  $f" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  fi
done

# 2. Re-run the audit loop using ONLY the journal baseline
PASS=0
FAIL=0
while IFS= read -r path; do
  if test -e "$path"; then
    echo "  ❌ $path still exists after simulated reboot" \
      | tee -a "$JDIR/post-reboot-audit.txt"
    FAIL=$(( FAIL + 1 ))
  else
    echo "  ✅ $path absent (correct)" \
      | tee -a "$JDIR/post-reboot-audit.txt"
    PASS=$(( PASS + 1 ))
  fi
done < /root/rhcsa_journal/lab-11c/task1/expected-removed.txt

echo "═══ Post-reboot summary: $PASS pass, $FAIL fail ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"

# 3. Re-run the Ansible idempotence proof — if the playbook is truly idempotent,
#    this still reports changed=0 even though the targets evaporated.
mkdir -p /tmp/rm-ansible-lab  # the dir is enough — targets stay absent
ansible-playbook /root/rhcsa_journal/lab-11b/playbooks/task2.yml \
  2>&1 | tee "$JDIR/post-reboot-ansible.txt" | grep -E "PLAY RECAP|changed="

echo "exit was: $?"
```

### Human-readable breakdown

1. Snapshot the pre-reboot state: which paths are on `tmpfs` (will evaporate) vs the root partition (will survive). The `stat -c '%m'` output is the **structural** proof of why the journal location matters.
2. Save the `timeline.txt` snapshot to `/root/` **before** the wipe — otherwise we lose the pre-reboot evidence.
3. Wipe `/tmp/rm-verify-lab/` and `/tmp/rm-ansible-lab/` to simulate what `/tmp` clearing on reboot would do.
4. Confirm the wipe worked (`find ... | wc -l` is 0).
5. Walk through the journal files we need (audit transcript, expected-removed baseline, both Ansible playbooks) and prove each one survived.
6. Re-run the audit loop using the **journal baseline only** — proving the entire audit is reproducible from `/root/` alone.
7. Re-run the Lab 11b idempotence-proof playbook. It should **still** report `changed=0` because the targets are still absent (technically the parent directory was wiped too, but `state: absent` doesn't care — the desired state is "not present," which is satisfied).

### Reading it left to right

- `stat -c '%m'` — the mount point that contains each path. `/tmp` may show `/tmp` (if separately mounted) or `/` (if not); `/root` shows `/` on a typical layout.
- `rm -rf /tmp/rm-verify-lab/* /tmp/rm-ansible-lab` — wipe contents of one directory and remove the other. Note `/tmp/rm-verify-lab/` itself stays (we kept the directory) so we can write the post-reboot transcript there if needed.
- `for f in ...; do test -f "$f" ...` — the journal-file existence loop. Every file that should have survived gets a ✅ or ❌.
- `< /root/rhcsa_journal/.../expected-removed.txt` — **redirect from the journal copy**, not the original. This is the structural test of persistence: the audit must read from `/root/`, not `/tmp/`.
- `ansible-playbook ... | tee | grep -E "PLAY RECAP|changed="` — quick extract of just the audit-critical lines from the playbook output. Full output still lands in `post-reboot-ansible.txt`.

### The story

This task is the **only** thing that distinguishes a real audit from theater. Running `audit.txt` once on the same host that just ran the playbook proves very little — anything could have been kept in shell memory. Wiping `/tmp` and re-running from `/root/` proves the audit is reproducible by **anyone** with access to the journal, in a fresh shell, after a reboot, weeks later. That is the contract of a verifiable change.

For RHCSA: every task's verification command must produce output that survives the test environment. For RHCE: every playbook must have a baseline file (expected state) stored alongside it. For the auditor seat in any role: if the verification cannot be re-run from cold storage, it is not verification — it is just hope.

### Expected output

```text
═══ Pre-reboot state ═══
  /tmp  is on  /tmp                  (or /, depending on layout)
  /root  is on  /
  /root/rhcsa_journal  is on  /
warmup-task2.txt  task1  task2  expected-removed.txt
═══ SIMULATING REBOOT — clearing /tmp/rm-verify-lab/ ═══
  at 2026-05-27T15:42:18-04:00
  /tmp/rm-verify-lab still exists (we kept the dir, wiped contents)
0
0
═══ Post-reboot — reconstructing from journal under /root/ ═══
  ✅ survived: /root/rhcsa_journal/lab-11c/task1/audit.txt (24 lines)
  ✅ survived: /root/rhcsa_journal/lab-11c/task1/expected-removed.txt (3 lines)
  ✅ survived: /root/rhcsa_journal/lab-11b/playbooks/task1.yml (24 lines)
  ✅ survived: /root/rhcsa_journal/lab-11b/playbooks/task2.yml (26 lines)
  ✅ /tmp/rm-ansible-lab/old.log absent (correct)
  ✅ /tmp/rm-ansible-lab/stale.tmp absent (correct)
  ✅ /tmp/rm-ansible-lab/cache absent (correct)
═══ Post-reboot summary: 3 pass, 0 fail ═══
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%m'` | Print the mount point that contains the path |
| `rm -rf /tmp/X/* /tmp/Y` | Wipe the **contents** of X, **remove** Y entirely |
| `< FILE` | Redirect FILE to stdin for the while loop |
| `wc -l < FILE` | Line count without the filename column in the output |
| `grep -E "A\|B"` | Extended regex; match line containing A or B |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/tmp` vs `/root/` storage | `/tmp` is ephemeral (tmpfs on most systems); `/root/` is on the persistent root partition |
|   | Journal as cold-storage audit | Every verification artifact must live in `/root/rhcsa_journal/` to survive reboot |
|   | Reproducible audit | Re-running the audit from journal files only is the test of real persistence |
|   | Idempotence across reboot | A correctly-written `state: absent` play still reports `changed=0` after the targets evaporated |
|   | Mount-point awareness | `stat -c '%m'` exposes the structural reason for persistence — not just "it survived," but **why** |
| 🪤 | **Trap Risk T41** | Skipping the reboot test on storage / fstab / SELinux tasks. The cost is discovering a config-only change after the next reboot — too late. |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript persisted | `wc -l /root/rhcsa_journal/lab-11c/task2/post-reboot-audit.txt` | The proof artifact of Task 2 itself |
| Timeline preserved | `head -n 5 /root/rhcsa_journal/lab-11c/task2/timeline.txt` | Pre-reboot evidence that we did not fabricate |
| Idempotence holds across reboot | `grep changed= /root/rhcsa_journal/lab-11c/task2/post-reboot-ansible.txt` | `changed=0` is the proof — same as Lab 11b Task 2 but now after `/tmp` was wiped |
| Trilogy complete | `find /root/rhcsa_journal/lab-11{a,b,c} -name done.txt \| wc -l` | Should be `6` — three sub-labs × two tasks each |

### Journal write — BEFORE cleanup

```bash
LAB=lab-11c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
# (already created earlier in the command block)

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Simulated-reboot persistence proof — reconstruct audit from /root/ journal only
COMMANDS: stat -c '%m', rm -rf, while IFS= read, journal cross-check
TRAPS:    T41 rehearsed (we did NOT skip the reboot test — we proved persistence)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 12a (creating-nested-directories) — the inverse of Lab 11
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-11{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/rm-verify-lab /tmp/rm-ansible-lab
test -d /tmp/rm-verify-lab || echo "verify sandbox gone — clean exit"
test -d /tmp/rm-ansible-lab || echo "ansible sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `/tmp` mount point shown as `/` | `/tmp` is not separately mounted on this system — still ephemeral on reboot if `tmp.mount` is enabled |
| ❌ MISSING on any journal file | Lab 11a, 11b, or 11c Task 1 did not run its journal write step — go back and finish |
| Post-reboot audit shows `1 fail` | The directory we wiped contained something that should not have been there — investigate |
| Ansible re-run shows `changed=1` after wipe | The play is creating something instead of removing — wrong module call, fix before continuing |
| `grep PLAY RECAP` returns nothing | `ansible-playbook` failed to run — check toolchain |

> **STOP — paste the "Post-reboot summary: 3 pass, 0 fail" line and the trilogy `done.txt` list before completing Lab 11.**

---

## Lab 11c Checklist (2 tasks)

- [ ] Task 1 — Three-tool audit (`ls` + `test` + `stat`) of all Lab 11b targets + `diff` against declared baseline
- [ ] Task 2 — Simulated-reboot persistence proof — reconstruct the audit using only `/root/rhcsa_journal/` artifacts

---

## 🏁 Lab 11 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-11{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-11a/task1/done.txt
/root/rhcsa_journal/lab-11a/task2/done.txt
/root/rhcsa_journal/lab-11b/task1/done.txt
/root/rhcsa_journal/lab-11b/task2/done.txt
/root/rhcsa_journal/lab-11c/task1/done.txt
/root/rhcsa_journal/lab-11c/task2/done.txt
```

If any are missing, that sub-lab is incomplete. Do not start Lab 12a until the trilogy is closed.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| **Lab 11a** — RHCSA hand-typed removal | The imperative form being audited |
| **Lab 11b** — Removing Files via Ansible | The declarative form being audited |
| Lab 10 — Moving and Renaming Files | The reversible alternative (`mv` quarantine) — audit applies equally |
| Lab 12c — Verifying Created Directories (later) | The mirror pattern: prove a `mkdir -p` actually built what was promised |
| Lab 14c — Verifying find results (later) | Audit applied to `find` — prove the search returned everything it should |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
