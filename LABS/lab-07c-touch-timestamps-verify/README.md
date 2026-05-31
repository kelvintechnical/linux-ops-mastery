# Lab 07c: Verifying Timestamps — audit + persistence proof

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `07a` (RHCSA) → `07b` (Ansible) → **`07c` (Verify — you are here)**
- **Career arcs covered:** RHCSA EX200 (timestamp verification reflex), RHCE EX294 (auditor seat — prove a play's `modification_time:` claim is real), SRE (post-change verification habit), AI/MLOps (stale-checkpoint detection — audit mtime against expected cleanup window)
- **Prerequisite:** Lab 07a and Lab 07b completed — this lab verifies their combined effect
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = three-tool audit, Task 2 = simulated-reboot persistence proof)
- **Practice Directory (rotation #07):** `/var/log`
- **Sandbox:** `/tmp/touch-lab/`
- **Traps rehearsed this lab:** **T11-E equivalent** (trusting `ls` time column without `--time=atime`/`--time=ctime` — `ls -l` defaults to mtime, so a verifier who asks "when was this last read?" and looks at `ls -l` gets the wrong answer) · **T41** (skipping the reboot persistence test — the pinned-timestamp playbook is the only thing that proves a wiped `/tmp/touch-lab/` can be reconstructed with the original mtimes)

> **This lab's practice directory is: `/var/log`** — every task references it as the real-world cross-reference for `ls --time=` output. We **read** `/var/log` only; the audit workspace is `/tmp/touch-lab/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T11-E(equiv) T41"
echo "📁  PRACTICE DIR: /var/log"
echo ""
echo "🧾 Journal check — Lab 07a and 07b must already be done:"
test -f /root/rhcsa_journal/lab-07a/task2/done.txt && echo "  ✅ lab-07a task2 done"
test -f /root/rhcsa_journal/lab-07b/task2/done.txt && echo "  ✅ lab-07b task2 done"
test -f /root/rhcsa_journal/lab-07b/playbooks/task1.yml && echo "  ✅ lab-07b playbook present"
```

> **STOP — if any check above failed, return and finish Lab 07a or 07b first. This lab depends on the journal artifacts AND the Lab 07b playbook.**

---

## 🎯 Objective

Take off the operator's hat and put on the **auditor's hat**. Lab 07a backdated files by hand. Lab 07b backdated files via Ansible and reported `changed=0` on the pinned task's re-run. Neither of those **proves** the timestamps on disk match what was claimed. Lab 07c is the inspection step that proves it, using only RHCSA-grade inspection commands — `stat`, `find -newer`, `ls --time=atime`, `ls --time=ctime`, and a `diff` against an expected-timestamp baseline. No `ansible.*` commands until the very end of Task 2, where we use the playbook only to **prove persistence after a simulated reboot**.

---

## 🧠 Concept: Trust But Verify — Especially the `ls` Time Column

`ls -l` shows **mtime** by default. That single fact hides three other timestamps from the unwary auditor:

| What the question asks | What an unwary `ls -l` shows | What you actually need |
|---|---|---|
| "When was this last modified?" | mtime ✅ | mtime (`ls -l` default, or `stat -c '%y'`) |
| "When was this last read?" | mtime ❌ | atime — `ls --time=atime -l` or `stat -c '%x'` |
| "When was its metadata last changed?" | mtime ❌ | ctime — `ls --time=ctime -l` or `stat -c '%z'` |
| "When was the file actually created?" | mtime ❌ | btime — `stat -c '%w'` (`-` if unsupported) |

A grader asking "when was `/etc/shadow` last accessed?" and seeing your `ls -l /etc/shadow` answer will mark you down because that column is mtime, not atime. Same for `ls -lt` (sorts by mtime), `ls -lc` (sorts by ctime — note the difference between `-c` for sort and `--time=ctime` for column), and `ls -lu` (sorts by atime). The senior reflex is `stat` first; `ls --time=` second.

> **The auditor's failure mode (T11-E equivalent for timestamps):** glancing at `ls -l` and treating the date column as a general-purpose "when was something done to this file" answer. It is mtime only. Use `stat` or `ls --time=` to ask a specific question.

> **The persistence failure mode (T41):** writing the playbook in Lab 07b, applying it once, declaring success, and never proving the playbook can RECONSTRUCT the files after `/tmp/touch-lab/` is wiped. The pinned `modification_time:` form is the **only** form that survives this test — Task 2 proves it end-to-end.

---

## 📚 Inspection Reference (everything for Tasks 1–2)

| Tool | Purpose | Why an auditor reaches for it |
|---|---|---|
| `stat FILE` | Full metadata block (3 timestamps + btime + size + perms + inode) | Primary inspection — single command, all four timestamps |
| `stat -c '%n mtime=%y atime=%x ctime=%z'` | Custom multi-field format | Compact one-liner for scripts |
| `stat -c '%w'` | btime (creation) | `-` if unsupported; informational |
| `find PATH -newer REF` | Files modified after REF's mtime | Exhaustive cross-check; no day rounding |
| `find PATH -mtime -1` | Files modified in the last 24h | Log-rotation trigger style |
| `ls --time=atime -l` | Listing sorted/shown with atime in the date column | "When was each of these last read?" |
| `ls --time=ctime -l` | Listing with ctime in the date column | "When did each inode last change?" |
| `ls -l --full-time` | Full nanosecond precision in the date column | Resolves sub-second drift questions |
| `diff -u EXPECTED ACTUAL` | Line-level comparison | "Do the actual timestamps match the expected baseline?" |
| `getfacl PATH` | POSIX ACLs | Catches non-standard permissions |

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# Set up the audit workspace
mkdir -p /tmp/touch-lab
mkdir -p /root/rhcsa_journal/lab-07c
cd /tmp/touch-lab

# Re-create the seed reference file if Lab 07b's cleanup removed it
test -f /tmp/touch-lab/reference.txt || echo "lab07c reference content" > /tmp/touch-lab/reference.txt

# Capture the expected-timestamp baseline (what Lab 07b's pinned task claimed)
cat > /tmp/touch-lab/expected-timestamps.txt <<'EOF'
/tmp/touch-lab/ansible-pinned.txt mtime=2024-01-15 atime=2020-01-01 mode=644
EOF

# Make sure the Lab 07b playbook artefacts exist
ls -la /tmp/touch-lab
cat /tmp/touch-lab/expected-timestamps.txt
test -f /root/rhcsa_journal/lab-07b/playbooks/task1.yml && echo "playbook OK"
echo "exit was: $?"
```

> **STOP — paste output before Task 1. The expected-timestamps baseline AND the Lab 07b playbook must both be present.**

---

## Task 1 — Three-tool audit + diff against expected-timestamp baseline

**Practice directory this task:** `/var/log` (real-world cross-reference for `ls --time=atime`) · `/tmp/touch-lab/` (the playbook's output we are auditing) · `/root/rhcsa_journal/lab-07c/` (the journal — where the baseline survives).

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /tmp/touch-lab                                2>&1 | tee /tmp/touch-lab/warmup.txt
wc -l /tmp/touch-lab/expected-timestamps.txt
test -f /tmp/touch-lab/expected-timestamps.txt && echo "baseline OK"
stat -c '%n %F' /tmp/touch-lab/expected-timestamps.txt
ls -lt /var/log 2>/dev/null | head -3
ls --time=atime -lt /var/log 2>/dev/null | head -3
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 07b: the `stat -c '%y'` reflex carries forward — but we now widen the inspection to **three independent tools** (`stat`, `find -newer`, `ls --time=`) so the audit is multi-sourced.

### Purpose

Audit `ansible-pinned.txt` with **three independent inspection methods**: `stat -c '%n mtime=%y atime=%x ctime=%z'` for explicit fields, `find /tmp/touch-lab -newer REFERENCE` for relative comparison, and `ls --time=atime/--time=ctime` to prove the three timestamps are **independent** (the listing changes column depending on which time you ask for). Then `diff` the actual timestamps against the expected-timestamp baseline file. Any discrepancy is a real signal.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `wc -l expected-timestamps.txt` | Counts how many files we expect to audit — drives the loop iteration count |
| `stat -c '%n %F'` | Cross-check: confirms whether each expected path actually exists as a regular file |
| `ls --time=atime -lt /var/log` | Real-world demo of the alternate time column — primes the cross-reference at end of task |
| `2>&1 \| tee` | Captures every check into `task1/audit.txt` — the proof artifact |
| `set -o pipefail` | Ensures `tee` chain fails honestly |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
mkdir -p /tmp/touch-lab/task1
cd /tmp/touch-lab

# 0) Pre-flight — make sure Lab 07b's pinned file exists
if ! test -f /tmp/touch-lab/ansible-pinned.txt; then
  echo "ansible-pinned.txt MISSING — re-running Lab 07b playbook to reconstruct"
  ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
    2>&1 | tail -n 10
fi

echo "═══ Three-tool audit of ansible-pinned.txt ═══" \
  2>&1 | tee /tmp/touch-lab/task1/audit.txt

# Tool 1: stat — explicit multi-field
echo "─── Tool 1: stat -c '%n mtime=%y atime=%x ctime=%z' ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
stat -c '%n mtime=%y atime=%x ctime=%z' /tmp/touch-lab/ansible-pinned.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt
stat -c '  birth=%w' /tmp/touch-lab/ansible-pinned.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt

# Tool 2: find -newer — relative comparison
echo "─── Tool 2: find -newer reference.txt (must INCLUDE pinned file? NO — pinned is 2024) ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
find /tmp/touch-lab -maxdepth 1 -type f -newer /tmp/touch-lab/reference.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt
echo "─── find /tmp/touch-lab -mtime -1 (files modified in last 24h) ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
find /tmp/touch-lab -maxdepth 1 -type f -mtime -1 \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt

# Tool 3: ls --time=atime / --time=ctime — proves timestamps are INDEPENDENT
echo "─── Tool 3a: ls -l (default → mtime column) ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
ls -l /tmp/touch-lab/ansible-pinned.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt
echo "─── Tool 3b: ls --time=atime -l (atime column — must show 2020) ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
ls --time=atime -l /tmp/touch-lab/ansible-pinned.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt
echo "─── Tool 3c: ls --time=ctime -l (ctime column — must show today, not 2024) ───" \
  | tee -a /tmp/touch-lab/task1/audit.txt
ls --time=ctime -l /tmp/touch-lab/ansible-pinned.txt \
  2>&1 | tee -a /tmp/touch-lab/task1/audit.txt

# Diff: actual timestamps vs expected baseline
echo "═══ DIFF: actual vs expected-timestamps.txt ═══" \
  | tee -a /tmp/touch-lab/task1/audit.txt

actual_mtime=$(stat -c '%y' /tmp/touch-lab/ansible-pinned.txt | cut -d' ' -f1)
actual_atime=$(stat -c '%x' /tmp/touch-lab/ansible-pinned.txt | cut -d' ' -f1)
actual_mode=$(stat -c '%a' /tmp/touch-lab/ansible-pinned.txt)
echo "/tmp/touch-lab/ansible-pinned.txt mtime=$actual_mtime atime=$actual_atime mode=$actual_mode" \
  > /tmp/touch-lab/task1/actual-timestamps.txt

diff -u /tmp/touch-lab/expected-timestamps.txt /tmp/touch-lab/task1/actual-timestamps.txt \
  | tee -a /tmp/touch-lab/task1/audit.txt || true

if diff -q /tmp/touch-lab/expected-timestamps.txt /tmp/touch-lab/task1/actual-timestamps.txt >/dev/null; then
  echo "═══ AUDIT: ✅ MATCH — actual timestamps == expected baseline ═══" \
    | tee -a /tmp/touch-lab/task1/audit.txt
else
  echo "═══ AUDIT: ❌ MISMATCH — see diff above ═══" \
    | tee -a /tmp/touch-lab/task1/audit.txt
fi

echo "exit was: $?"
```

### Human-readable breakdown

1. Pre-flight: if Lab 07b's `ansible-pinned.txt` is missing (because the previous lab cleaned up), re-run the Lab 07b playbook to reconstruct it. This is the **first** demonstration that the pinned-timestamp playbook is reproducible — the test in Task 2 makes this explicit.
2. **Tool 1 — `stat -c '%n mtime=%y atime=%x ctime=%z'`** is the primary inspection. One command, three (four with `%w` for btime) independent fields. The audit reads each timestamp explicitly so there is no ambiguity about which column is which.
3. **Tool 2 — `find -newer reference.txt`** is the relative-comparison form. Because `ansible-pinned.txt` has mtime `2024-01-15` and `reference.txt` has mtime "today," `find -newer reference.txt` should NOT include the pinned file. That negative result is a real signal — it proves the pinned mtime is genuinely older than the reference.
4. **Tool 3 — `ls -l` vs `ls --time=atime -l` vs `ls --time=ctime -l`** proves the three timestamps are independent. The default `ls -l` shows mtime (`2024-01-15`); `--time=atime` shows atime (`2020-01-01`); `--time=ctime` shows ctime (today, because the inode was last modified by the playbook today). Three different dates in three different columns on the same file — that is the visual proof.
5. The diff compares actual vs expected. An empty diff means the playbook's claim matches reality. A non-empty diff is the real failure signal — investigate before claiming completion.

### Reading it left to right

- `if ! test -f FILE; then ... fi` — bash conditional; runs the body only if FILE is missing.
- `stat -c '%n mtime=%y atime=%x ctime=%z'` — multi-field custom format; all three timestamps in one line.
- `find /tmp/touch-lab -maxdepth 1 -type f -newer /tmp/touch-lab/reference.txt` — `-newer REF` means "files whose mtime is greater than REF's mtime." Lists only files NEWER than `reference.txt`. The pinned file (mtime `2024-01-15`) is OLDER than `reference.txt` (mtime today), so it does NOT appear — that omission is the proof.
- `ls --time=atime -l FILE` — `--time=` selects which timestamp goes in the date column. Choices: `atime`, `access`, `use`, `ctime`, `status`, plus the default mtime.
- `ls --time=ctime -l FILE` — ctime in the column. Note the difference from `ls -lc` (which sorts by ctime but still shows mtime in the column unless combined with `--time=ctime`).
- `stat -c '%y' FILE | cut -d' ' -f1` — strips the time portion, leaving just `YYYY-MM-DD`. Used for string-equality compares.
- `diff -u EXPECTED ACTUAL || true` — `|| true` masks the diff's non-zero exit when files differ, so the script continues to print the verdict.

### The story

The auditor seat is the most under-trained skill in RHCSA prep. Candidates spend hours on `lvextend` and `firewall-cmd`, then lose points on the exam because they did not run `mount -a`, `firewall-cmd --list-all`, or — in our case — `stat -c '%x %y %z'` to **verify** their timestamp change before claiming the task complete. Lab 07c bakes the audit reflex into the workflow.

The three-tool cross-check is the senior-engineer move. Anyone can run `stat` and feel good. The cross-check catches what one command misses:
- A filesystem with `noatime` mounted will silently return wrong atime to `stat`. `ls --time=atime` shows the same value but in a different code path — disagreement between them is a real signal.
- A file with the right mtime but wrong mode (Lab 07b promised mode `0644` but the playbook is run with `umask 0077` shenanigans) will pass an mtime-only check and fail the diff against the full baseline.
- A file recreated between Lab 07b and Lab 07c by some background process will have a fresh ctime but the same mtime — `find -newer reference.txt` would catch that.

### Expected output

```text
═══ Three-tool audit of ansible-pinned.txt ═══
─── Tool 1: stat -c '%n mtime=%y atime=%x ctime=%z' ───
/tmp/touch-lab/ansible-pinned.txt mtime=2024-01-15 12:00:00.000000000 -0500 atime=2020-01-01 00:00:00.000000000 -0500 ctime=2026-05-27 15:00:01.xxx -0400
  birth=2026-05-27 15:00:01.xxx -0400
─── Tool 2: find -newer reference.txt ───
(empty — pinned file is OLDER than reference.txt — correct)
─── find /tmp/touch-lab -mtime -1 (files modified in last 24h) ───
/tmp/touch-lab/reference.txt
/tmp/touch-lab/ansible-now.txt
(ansible-pinned.txt is NOT in this list — its mtime is 2024 — correct)
─── Tool 3a: ls -l (default → mtime column) ───
-rw-r--r--. 1 root root 0 Jan 15  2024 /tmp/touch-lab/ansible-pinned.txt
─── Tool 3b: ls --time=atime -l (atime column — must show 2020) ───
-rw-r--r--. 1 root root 0 Jan  1  2020 /tmp/touch-lab/ansible-pinned.txt
─── Tool 3c: ls --time=ctime -l (ctime column — must show today, not 2024) ───
-rw-r--r--. 1 root root 0 May 27 15:00 /tmp/touch-lab/ansible-pinned.txt
═══ DIFF: actual vs expected-timestamps.txt ═══
═══ AUDIT: ✅ MATCH — actual timestamps == expected baseline ═══
exit was: 0
```

> The win condition: three different dates in three different `ls --time=` columns on the same file (`Jan 15 2024` mtime, `Jan 1 2020` atime, today's date ctime) AND an empty diff against the baseline.

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%y'` | mtime human-readable |
| `stat -c '%x'` | atime human-readable |
| `stat -c '%z'` | ctime human-readable |
| `stat -c '%w'` | btime (`-` if unsupported) |
| `find -newer REF` | Files modified AFTER REF's mtime (exact, no day rounding) |
| `find -mtime -1` | Modified in last 24h |
| `ls -l` | Default — mtime in date column |
| `ls --time=atime -l` | atime in date column |
| `ls --time=ctime -l` | ctime in date column |
| `ls -l --full-time` | Full nanosecond precision |
| `cut -d' ' -f1` | Strip time, keep YYYY-MM-DD |
| `diff -u A B` | Unified diff |
| `\|\| true` | Mask non-zero exit (use sparingly) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Three-tool cross-check | `stat`, `find -newer`, `ls --time=` — three independent answers to "what is this timestamp?" |
|   | `ls --time=atime` | Puts atime in the date column — proves the column changes with the request |
|   | `ls --time=ctime` | Puts ctime in the column — proves ctime ≠ creation (it tracks today's inode change) |
|   | Declared baseline | A text file with `expected mtime/atime/mode` per path; drives the diff |
|   | Three timestamps independent | The visual proof: same file, three different dates depending on `--time=` |
|   | `find -newer` precision | Exact comparison — catches off-by-day issues that `-mtime` rounds away |
| 🪤 | **Trap Risk T11-E (timestamps)** | Reading `ls -l` and reporting it as "atime" or "ctime" — that column is mtime by default |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Audit transcript captured | `wc -l /root/rhcsa_journal/lab-07c/task1/audit.txt` | Must be > 0 — proves the three-tool inspection happened |
| Baseline preserved | `ls /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt` | The diff is reproducible only if the baseline survives — store it in `/root/` |
| Diff match | `grep -c '✅ MATCH' /root/rhcsa_journal/lab-07c/task1/audit.txt` | Must be `1` |

> **Reboot reasoning:** Both `/tmp/touch-lab/` (the audited target) and the audit workspace will evaporate at reboot. The **only** thing that survives is the journal under `/root/rhcsa_journal/lab-07c/`. If the journal does not contain `audit.txt` AND `expected-timestamps.txt`, the audit cannot be reproduced — and that is what Task 2 deliberately tests.

### Journal write — BEFORE cleanup

```bash
LAB=lab-07c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/touch-lab/task1/audit.txt              "$JDIR/audit.txt"
cp /tmp/touch-lab/task1/actual-timestamps.txt  "$JDIR/actual-timestamps.txt"
cp /tmp/touch-lab/expected-timestamps.txt      "$JDIR/expected-timestamps.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Three-tool audit (stat + find -newer + ls --time=) + diff against expected baseline
COMMANDS: stat -c '%n %x %y %z %w', find -newer, find -mtime -1, ls --time=atime/ctime, diff -u
TRAPS:    T11-E(equiv) rehearsed (cross-checked with --time=atime / --time=ctime — never trusted ls -l alone)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — wipe /tmp/touch-lab and prove the pinned playbook reconstructs the timestamps
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
# Keep the journal AND the live files — Task 2 wipes them deliberately
rm -rf /tmp/touch-lab/task1
ls /tmp/touch-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ansible-pinned.txt missing` despite pre-flight | Lab 07b playbook is broken — re-run by hand and inspect the apply log |
| `ls --time=atime` shows mtime instead of atime | Some `ls` aliases override `--time=` — try `\ls --time=atime -l FILE` (escaped) |
| `find -newer reference.txt` includes the pinned file | The pinned file's mtime is somehow newer than `reference.txt` — re-touch `reference.txt` then re-run |
| Diff shows MISMATCH | Either the playbook ran with a different `target_mtime` than the baseline expects, or the baseline file has a typo — read both line by line |
| `birth=-` shown | Filesystem (older ext4 / unsupported XFS) — informational, not a bug |

> **STOP — paste the `═══ AUDIT: ✅ MATCH ═══` line AND the three `ls --time=` lines (different dates per column) before Task 2.**

---

## Task 2 — Simulated-reboot persistence proof — wipe `/tmp/touch-lab/` and prove the pinned playbook reconstructs the timestamps

**Practice directory this task:** `/tmp/touch-lab/` (about to be wiped) · `/root/rhcsa_journal/lab-07b/playbooks/` (the persistent playbook) · `/root/rhcsa_journal/lab-07c/` (the persistent journal). The contrast `/tmp` vs `/root/` is the entire lesson — `/tmp` evaporates, `/root/rhcsa_journal/` does not.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls /root/rhcsa_journal/lab-07c/task1/                2>&1 | tee /tmp/touch-lab/warmup-task2.txt
wc -l /root/rhcsa_journal/lab-07c/task1/audit.txt
test -f /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt && echo "baseline journal OK"
test -f /root/rhcsa_journal/lab-07b/playbooks/task1.yml          && echo "playbook journal OK"
stat -c '%n mountpoint=%m' /tmp /root /root/rhcsa_journal
find /tmp/touch-lab -type f                          2>/dev/null | wc -l
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry: `stat -c '%m'` reveals the **mount point** for each path. `/tmp` is typically tmpfs (evaporates) and `/root` is on the persistent root partition. That mount-point difference is the structural reason the journal survives reboot — the lab is built around it.

### Purpose

Simulate a reboot — wipe `/tmp/touch-lab/` entirely — then **prove the pinned playbook reconstructs the file with the original mtime**. The first re-run reports `changed=1` (because the file no longer exists, so the module recreates it with pinned mtime `2024-01-15`). The second re-run reports `changed=0` (because the pinned mtime now matches the desired state). The bare-touch task — if you kept it from Lab 07b — reports `changed=1` on **both** runs, demonstrating that only the pinned form survives a wipe correctly.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `stat -c '%m'` | Confirms which paths are on tmpfs (will evaporate) vs root (will survive) |
| `find /tmp/touch-lab` | Before and after the simulated reboot — verifies `/tmp` was cleared |
| `wc -l audit.txt` | Confirms the journal copy is intact across the simulated reboot |
| `test -f` | Verifies each journal file actually survived |
| `2>&1 \| tee` | Captures the timeline + re-audit into `task2/` files |
| `$(date -Is)` | Stamps the simulated reboot moment |

### Main command block

```bash
mkdir -p /tmp/touch-lab/task2
JDIR="/root/rhcsa_journal/lab-07c/task2"
mkdir -p "$JDIR"

# 1) Pre-reboot snapshot
echo "═══ Pre-reboot state ═══" \
  2>&1 | tee /tmp/touch-lab/task2/timeline.txt
stat -c '  %n  is on  %m' /tmp /root /root/rhcsa_journal \
  2>&1 | tee -a /tmp/touch-lab/task2/timeline.txt
stat -c '  %n  mtime=%y' /tmp/touch-lab/ansible-pinned.txt 2>/dev/null \
  | tee -a /tmp/touch-lab/task2/timeline.txt
ls /tmp/touch-lab/ \
  2>&1 | tee -a /tmp/touch-lab/task2/timeline.txt

# Move the timeline to /root BEFORE the wipe
cp /tmp/touch-lab/task2/timeline.txt "$JDIR/timeline.txt"

# 2) SIMULATE REBOOT — wipe the entire sandbox
echo "═══ SIMULATING REBOOT — wiping /tmp/touch-lab/ at $(date -Is) ═══" \
  | tee -a "$JDIR/timeline.txt"
rm -rf /tmp/touch-lab
test -d /tmp/touch-lab && echo "  /tmp/touch-lab unexpectedly still exists" \
  | tee -a "$JDIR/timeline.txt"
find /tmp/touch-lab -type f 2>/dev/null | wc -l   # must be 0 (or error — directory gone)

# 3) Journal-file existence check — these MUST survive a reboot
echo "═══ Post-reboot journal-file check ═══" \
  2>&1 | tee "$JDIR/post-reboot-audit.txt"
for f in /root/rhcsa_journal/lab-07c/task1/audit.txt \
         /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt \
         /root/rhcsa_journal/lab-07b/playbooks/task1.yml; do
  if test -f "$f"; then
    echo "  ✅ survived: $f ($(wc -l < "$f") lines)" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  else
    echo "  ❌ MISSING:  $f" \
      | tee -a "$JDIR/post-reboot-audit.txt"
  fi
done

# 4) FIRST re-run of the pinned playbook — must report changed=1 (recreate)
echo "═══ First post-reboot apply — pinned task expected: changed=1 (recreate) ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
  2>&1 | tee "$JDIR/post-reboot-apply-1.txt" \
  | grep -E "TASK \[Touch|PLAY RECAP|changed=|ok: \[localhost\]|changed: \[localhost\]"

# 5) Verify the pinned timestamp survived (should be 2024-01-15 again)
echo "═══ Stat after first re-run ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
stat -c '%n mtime=%y atime=%x' /tmp/touch-lab/ansible-pinned.txt \
  | tee -a "$JDIR/post-reboot-audit.txt"

# 6) SECOND re-run — pinned must report changed=0; bare-touch will still report changed=1
echo "═══ Second post-reboot apply — pinned expected: changed=0 / bare expected: changed=1 ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
ansible-playbook /root/rhcsa_journal/lab-07b/playbooks/task1.yml \
  2>&1 | tee "$JDIR/post-reboot-apply-2.txt" \
  | grep -E "TASK \[Touch|PLAY RECAP|changed=|ok: \[localhost\]|changed: \[localhost\]"

# 7) Diff actual vs original baseline after the simulated reboot
actual_mtime=$(stat -c '%y' /tmp/touch-lab/ansible-pinned.txt | cut -d' ' -f1)
actual_atime=$(stat -c '%x' /tmp/touch-lab/ansible-pinned.txt | cut -d' ' -f1)
actual_mode=$(stat -c '%a' /tmp/touch-lab/ansible-pinned.txt)
echo "/tmp/touch-lab/ansible-pinned.txt mtime=$actual_mtime atime=$actual_atime mode=$actual_mode" \
  > "$JDIR/actual-after-reboot.txt"

echo "═══ DIFF after simulated reboot: original baseline vs reconstructed file ═══" \
  | tee -a "$JDIR/post-reboot-audit.txt"
diff -u /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt \
        "$JDIR/actual-after-reboot.txt" \
  | tee -a "$JDIR/post-reboot-audit.txt" || true

if diff -q /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt \
           "$JDIR/actual-after-reboot.txt" >/dev/null; then
  echo "═══ PERSISTENCE: ✅ PROVEN — pinned playbook reconstructed identical timestamps after wipe ═══" \
    | tee -a "$JDIR/post-reboot-audit.txt"
else
  echo "═══ PERSISTENCE: ❌ FAILED — timestamps drifted after wipe — see diff above ═══" \
    | tee -a "$JDIR/post-reboot-audit.txt"
fi

echo "exit was: $?"
```

### Human-readable breakdown

1. **Pre-reboot snapshot** captures the state of the world before we delete anything: which mount points are tmpfs vs persistent, what the pinned file's mtime currently is, what is in `/tmp/touch-lab/`. The snapshot is **immediately copied to `/root/`** because the wipe is about to destroy the original.
2. **Simulated reboot** = `rm -rf /tmp/touch-lab`. This mimics what `systemd-tmpfiles` does on boot for `/tmp` (or what tmpfs unmounting does). Everything in the sandbox is gone; the playbook in `/root/` is not.
3. **Journal-file existence check** walks the list of files the audit depends on (the original `audit.txt`, the baseline, the playbook). Every file must show ✅ — if any is missing, the journal was incomplete and the reproduction will fail at a later step.
4. **First post-reboot apply** — the pinned task reports `changed=1` because `ansible-pinned.txt` does not exist anymore; the module creates it AND applies the pinned timestamps from the playbook (`modification_time: "202401151200.00"`, `access_time: "202001010000.00"`). The `ansible-now.txt` task also reports `changed=1` because — well, it always does (T07-A demo from Lab 07b).
5. **Stat after first re-run** — the pinned file once again shows mtime `2024-01-15` and atime `2020-01-01`. The wipe + replay round-trip restored the **exact** original timestamps. That is the persistence proof.
6. **Second post-reboot apply** — now `ansible-pinned.txt` already has the pinned timestamps, so the module reports `changed=0`. The bare-touch task still reports `changed=1`. That contrast is the same as Lab 07b Task 2, but now after a real wipe — proving the idempotence claim survives the reboot.
7. **Final diff** — re-builds the actual-timestamp line and diffs it against the baseline file from Lab 07c Task 1. Empty diff → persistence proven. Any non-empty diff means the playbook drifted (the most common cause is editing `target_mtime` between Lab 07b and Lab 07c).

### Reading it left to right

- `stat -c '%m'` — the mount point that contains each path. `/tmp` may show `/tmp` (if separately mounted) or `/` (if not); `/root` shows `/` on a typical layout. The output is the **structural** reason the journal survives reboot.
- `rm -rf /tmp/touch-lab` — wipes the directory entirely (contrast with `rm -rf /tmp/touch-lab/*` which would keep the directory). We use the full wipe to mimic `systemd-tmpfiles` clean-on-boot.
- `for f in ...; do test -f "$f" ...` — the journal-file existence loop; every file gets a ✅ or ❌.
- `ansible-playbook ... | tee | grep -E "TASK \[Touch|PLAY RECAP|changed="` — extract just the audit-critical lines; full transcript still lands in `post-reboot-apply-1.txt`.
- `diff -u BASELINE ACTUAL || true` — print the diff but do not abort on a non-zero exit; the verdict logic below decides PASS/FAIL.

### The story

This task is **the** thing that distinguishes a real audit from theater. Running `audit.txt` once on the same host that just ran the playbook proves very little — anything could have been left in shell memory or filesystem caches. Wiping `/tmp` and re-running from `/root/` proves the audit is reproducible by **anyone** with access to the journal, in a fresh shell, weeks later. That is the contract of a verifiable change.

For Lab 07b specifically: the pinned `modification_time:` form is the **only** form that survives this test. If you skipped the pinning (Trap T07-A) and shipped a bare `state: touch`, the wipe + replay round-trip would produce a file with mtime "now" — not `2024-01-15`. The diff would show MISMATCH, the persistence proof would fail, and you would understand viscerally why the pinned form matters.

For Lab 11c by comparison: `state: absent` is idempotent for free — the desired state ("not present") is satisfied by either an existing wipe OR a successful playbook removal. `state: touch` is the more demanding case because the desired state includes a specific timestamp, not just presence.

### Expected output

```text
═══ Pre-reboot state ═══
  /tmp  is on  /tmp
  /root  is on  /
  /root/rhcsa_journal  is on  /
  /tmp/touch-lab/ansible-pinned.txt  mtime=2024-01-15 12:00:00.000000000 -0500
ansible-now.txt  ansible-pinned.txt  expected-timestamps.txt  reference.txt
═══ SIMULATING REBOOT — wiping /tmp/touch-lab/ at 2026-05-27T15:42:18-04:00 ═══
0
═══ Post-reboot journal-file check ═══
  ✅ survived: /root/rhcsa_journal/lab-07c/task1/audit.txt (24 lines)
  ✅ survived: /root/rhcsa_journal/lab-07c/task1/expected-timestamps.txt (1 lines)
  ✅ survived: /root/rhcsa_journal/lab-07b/playbooks/task1.yml (35 lines)
═══ First post-reboot apply — pinned task expected: changed=1 (recreate) ═══
TASK [Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)] ******
changed: [localhost]
TASK [Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)]
changed: [localhost]
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=2    unreachable=0    failed=0
═══ Stat after first re-run ═══
/tmp/touch-lab/ansible-pinned.txt mtime=2024-01-15 12:00:00.000000000 -0500 atime=2020-01-01 00:00:00.000000000 -0500
═══ Second post-reboot apply — pinned expected: changed=0 / bare expected: changed=1 ═══
TASK [Touch ansible-pinned.txt — pinned mtime + atime (IDEMPOTENT FORM)] ******
ok: [localhost]
TASK [Touch ansible-now.txt — NO timestamps pinned (NON-IDEMPOTENT — T07-A demo)]
changed: [localhost]
PLAY RECAP ********************************************************************
localhost                  : ok=4    changed=1    unreachable=0    failed=0
═══ DIFF after simulated reboot: original baseline vs reconstructed file ═══
═══ PERSISTENCE: ✅ PROVEN — pinned playbook reconstructed identical timestamps after wipe ═══
exit was: 0
```

> The win condition: post-wipe replay produces `ansible-pinned.txt` with mtime `2024-01-15` AND atime `2020-01-01`. The second re-run reports `changed=0` for the pinned task. The diff against the original baseline is empty. Persistence proven.

### Switches

| Token | Meaning |
|---|---|
| `stat -c '%m'` | Print the mount point that contains the path |
| `rm -rf /tmp/X` | Wipe the directory entirely (contrast with `rm -rf /tmp/X/*` which keeps the dir) |
| `for f in ...; do test -f "$f" ...` | Per-file existence loop |
| `ansible-playbook ... \| tee \| grep -E "A\|B"` | Capture full + extract audit lines |
| `diff -q A B` | Quiet diff — exit 0 if identical, 1 if differ — drives the PASS/FAIL verdict |
| `\|\| true` | Mask non-zero exit so the script continues |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `/tmp` vs `/root/` storage | `/tmp` is ephemeral (tmpfs on most systems); `/root/` is on the persistent root partition |
|   | Journal as cold-storage audit | Every verification artifact must live in `/root/rhcsa_journal/` to survive reboot |
|   | Reproducible audit | Re-running the audit from journal files only is the test of real persistence |
|   | Pinned timestamps survive | `modification_time:` in the playbook is the **only** thing that lets a wiped `/tmp` come back with the original mtime |
|   | Mount-point awareness | `stat -c '%m'` exposes the structural reason for persistence — not just "it survived," but **why** |
| 🪤 | **Trap Risk T41** | Skipping the reboot test on storage / fstab / SELinux / timestamp-pinning tasks. The cost is discovering a config-only change after the next reboot — too late. |

### 🔁 PERSISTENCE CHECK (this lab IS the persistence check)

| What was configured | Verification command | Why it matters |
|---|---|---|
| Persistence transcript saved | `wc -l /root/rhcsa_journal/lab-07c/task2/post-reboot-audit.txt` | The proof artifact of Task 2 itself |
| Timeline preserved | `head -n 5 /root/rhcsa_journal/lab-07c/task2/timeline.txt` | Pre-reboot evidence that we did not fabricate the run |
| Persistence verdict | `grep -c '✅ PROVEN' /root/rhcsa_journal/lab-07c/task2/post-reboot-audit.txt` | Must be `1` |
| Trilogy complete | `find /root/rhcsa_journal/lab-07{a,b,c} -name done.txt \| wc -l` | Should be `6` — three sub-labs × two tasks each |

### Journal write — BEFORE cleanup

```bash
LAB=lab-07c
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
TOPIC:    Simulated-reboot persistence proof — wiped /tmp/touch-lab/ and reconstructed via pinned playbook
COMMANDS: stat -c '%m', rm -rf, ansible-playbook (re-run x2), diff -u baseline vs reconstructed
TRAPS:    T41 rehearsed (did NOT skip the reboot test — wiped /tmp and proved the playbook reconstructs)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     Lab 08a or the next series — Lab 07 trilogy complete
EOF

ls -la "$JDIR"
echo "── Trilogy state ──"
find /root/rhcsa_journal/lab-07{a,b,c} -name done.txt | sort
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/touch-lab
test -d /tmp/touch-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `/tmp` mount point shown as `/` | `/tmp` is not separately mounted on this system — still ephemeral on reboot if `tmp.mount` is enabled |
| ❌ MISSING on any journal file | Lab 07a, 07b, or 07c Task 1 did not run its journal write step — go back and finish |
| First re-run reports `changed=0` for pinned task | Something else is recreating the file on its own — investigate. Most likely a tmpfiles.d rule or another playbook. |
| Second re-run reports `changed=1` for pinned task | The playbook's `target_mtime` was edited between Lab 07b and Lab 07c, OR the filesystem cannot resolve sub-second precision. Re-pin with `.00` seconds in the format. |
| `grep PLAY RECAP` returns nothing | `ansible-playbook` failed to run — check toolchain |
| Diff shows MISMATCH after reboot | The pinned format in `task1.yml` and the baseline string in `expected-timestamps.txt` do not match — verify both spell `2024-01-15`. |

> **STOP — paste the `═══ PERSISTENCE: ✅ PROVEN ═══` line AND the trilogy `done.txt` list before completing Lab 07.**

---

## Lab 07c Checklist (2 tasks)

- [ ] Task 1 — Three-tool audit (`stat` + `find -newer` + `ls --time=atime/ctime`) of `ansible-pinned.txt` + diff against expected-timestamp baseline + journal evidence
- [ ] Task 2 — Simulated-reboot persistence proof: wipe `/tmp/touch-lab/`, re-run the pinned playbook, prove the mtime/atime reconstructs identically + journal evidence

---

## 🏁 Lab 07 Trilogy — completion check

After all three sub-labs are done, this command should show **six** `done.txt` files:

```bash
find /root/rhcsa_journal/lab-07{a,b,c} -name done.txt | sort
```

Expected output:

```text
/root/rhcsa_journal/lab-07a/task1/done.txt
/root/rhcsa_journal/lab-07a/task2/done.txt
/root/rhcsa_journal/lab-07b/task1/done.txt
/root/rhcsa_journal/lab-07b/task2/done.txt
/root/rhcsa_journal/lab-07c/task1/done.txt
/root/rhcsa_journal/lab-07c/task2/done.txt
```

If any are missing, that sub-lab is incomplete. Do not start the next lab until the trilogy is closed.

---

## 🔗 Related Labs

| Lab | Connection |
|---|---|
| **Lab 07a** — RHCSA hand-typed timestamps | The imperative form being audited |
| **Lab 07b** — Creating Files & Setting Timestamps via Ansible | The declarative form being audited; the pinned playbook is the persistence anchor |
| Lab 06 — `ls -l`, `ls -lZ` | `ls -l` defaults to mtime; this lab teaches `ls --time=atime/ctime` for the other timestamps |
| Lab 11c — Verifying File Removal | The mirror pattern: audit a `state=absent` play instead of a `state=touch` play |
| Lab 14c — Verifying find results | Audit applied to `find` — prove `-mtime` returned exactly what it should |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
