# Lab 217c: Monitor Security Updates (Verify) — `test -s`, `grep -c`, exit-code auditing

**Series:** linux-ops-mastery — Security Administration · **Lab 217c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (confirming an update survey is correct), RHCE EX294 (validating a playbook's reports and rc handling), SRE/DevOps (artifact validation, patch-report sanity checks)  
**Prerequisite:** [Lab 217a](../lab-217a-monitor-security-updates-rhcsa/) and [Lab 217b](../lab-217b-monitor-security-updates-ansible/) completed, on a RHEL 9 / Rocky / Alma sandbox you can `sudo` on  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Audit the update survey produced by 217a/217b without ever patching the box. You will prove the report artifacts exist and are non-empty with `test -s`, re-run `dnf check-update` and assert its exit code is a *sane* `0` or `100` (never a repo/network failure), count the security advisories with `grep -c` and compare that number to the report on disk, and read `needs-restarting -r` purely as a verdict. The whole lab stays read-only — it confirms the work without changing a single package.

---

## 🧠 Concept

Verifying a patch *survey* (as opposed to a patch *action*) is about three questions: did the survey actually produce its evidence, is that evidence internally consistent, and were the exit codes healthy? `test -s <file>` answers "does this report exist and contain bytes?" in one expression. Re-running `dnf check-update` and capturing `$?` lets you assert the code is in the *allowed* set `{0, 100}` — anything else (typically `1`) means a real repo or network problem that would have poisoned the original survey. `grep -c` turns "how many security advisories?" into a number you can compare against the saved `security-advisories.txt`, catching a truncated or stale report. None of this installs anything; it only reads, counts, and asserts.

```
test -s pending.txt              → file exists AND non-empty   (evidence present)
dnf check-update; echo $?        → 0 or 100 = healthy, 1 = broken survey
grep -c 'Sec\.' advisories.txt   → N security advisories       (a comparable number)
needs-restarting -r; echo $?     → 0 = no reboot, 1 = reboot advised (verdict only)
```

> **Why this matters:** A report file that exists but is empty, or a survey that secretly failed with rc=1, gives false confidence. Verification catches the silent failure *before* you make a patch decision off bad data — the same discipline a grader uses to confirm your survey was real.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `test -s <file>` / `[ -s ... ]` | True only if a file exists and is non-empty | `-s` = size greater than zero; `! -s` catches empty reports |
| `dnf check-update` | Re-run the availability query to audit its exit code | exit `0`/`100` are healthy; `1` is a real failure |
| `grep -c <pattern> <file>` | Count matching lines as a bare number | `-c` prints the count; pair with `-E` for extended regex |
| `needs-restarting -r` | Read the reboot-recommended verdict | `-r` exit `0` = no reboot, `1` = reboot advised |
| `wc -l < file` | Count lines in a report without printing the name | feeding via `<` keeps the filename out of the output |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We point at the same `/tmp/lab-217` sandbox the earlier labs used and, if its report files are missing, regenerate them read-only so this verify lab has artifacts to audit — without patching anything.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-217
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

# Regenerate the reports read-only if 217a/217b were torn down already.
[ -s "$LAB_ROOT/pending.txt" ] || dnf check-update > "$LAB_ROOT/pending.txt" 2>/dev/null
[ -s "$LAB_ROOT/security-advisories.txt" ] || \
  dnf updateinfo list security > "$LAB_ROOT/security-advisories.txt" 2>/dev/null

ls -l "$LAB_ROOT"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 412 Jun 15 17:55 pending.txt
-rw-r--r--. 1 root root 120 Jun 15 17:55 security-advisories.txt
Sandbox ready at 2026-06-15T17:55:02-04:00
exit was: 0
```

---

## TASK 1 of 2 — Prove the report artifacts exist and are sane

**In plain English:** We assert the survey's report files are present and non-empty, then re-run `dnf check-update` and prove its exit code is one of the two healthy values — catching any survey that silently failed.

---

### Step 1 of 2 — Assert each report file is non-empty with `test -s`

**In plain English:** We check that `pending.txt` and `security-advisories.txt` both exist and contain bytes, printing an explicit OK/FAIL for each.

```bash
for f in pending.txt security-advisories.txt; do
  if test -s "$LAB_ROOT/$f"; then
    echo "FILE OK: $f ($(wc -l < "$LAB_ROOT/$f") lines)"
  else
    echo "FILE FAIL: $f missing or empty"
  fi
done
echo "exit was: $?"
```

**Expected output:**

```
FILE OK: pending.txt (6 lines)
FILE OK: security-advisories.txt (2 lines)
exit was: 0
```

**Line-by-line breakdown:**

- `for f in pending.txt security-advisories.txt; do` → Loop over the two report artifacts the survey was supposed to produce.
- `if test -s "$LAB_ROOT/$f"; then` → `test -s` is true only when the file exists *and* is non-empty; this single check catches both "never created" and "created but blank."
- `echo "FILE OK: $f ($(wc -l < ...) lines)"` → On success, report the file and its line count (`wc -l < file` keeps the filename out so only the number prints).
- `else echo "FILE FAIL: ..."` → On failure, name exactly which report is bad so you know what to regenerate.

**New words in this step:**

- **`test -s`** — a file test that passes only when the file exists and has a size greater than zero.
- **artifact** — a file produced as evidence of a task (here, the survey's report files).

---

### Step 2 of 2 — Re-run `check-update` and assert a healthy exit code

**In plain English:** We run the availability query again, capture its exit code, and assert it is `0` or `100` — proving the survey ran against working repos rather than failing silently.

```bash
dnf check-update >/dev/null 2>&1; rc=$?
echo "check-update exit: $rc"
case "$rc" in
  0|100) echo "RC OK: healthy survey (0=none, 100=updates available)";;
  *)     echo "RC FAIL: real repo/network error (rc=$rc)";;
esac
```

**Expected output:**

```
check-update exit: 100
RC OK: healthy survey (0=none, 100=updates available)
```

**Line-by-line breakdown:**

- `dnf check-update >/dev/null 2>&1; rc=$?` → Re-run the query, discard its output (we only want the verdict), and capture the exit code immediately into `rc`.
- `echo "check-update exit: $rc"` → Surface the raw exit code for the record.
- `case "$rc" in 0|100) ... ;;` → Assert the code is in the *allowed* set: `0` (up to date) or `100` (updates available) are both healthy outcomes.
- `*) echo "RC FAIL: ..."` → Any other code (usually `1`) means a genuine repo/network failure that would have invalidated the original survey.

**New words in this step:**

- **allowed exit set** — the specific codes that count as success for a command (`{0, 100}` for `check-update`).
- **silent failure** — a command that appears to run but actually errored; caught here by auditing the exit code.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `test -s file` | passes only for a non-empty file | a created-but-empty report still fails `-s` |
| `check-update` rc `{0,100}` | the healthy survey codes | rc `1` is the failure case to flag |
| capturing `$?` immediately | preserves the real exit code | the next command overwrites `$?` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `FILE FAIL: ... missing or empty` | 217a/217b reports were torn down | Re-run the setup block to regenerate them read-only |
| `RC FAIL: ... rc=1` | Repo unreachable or metadata broken | `sudo dnf clean all && sudo dnf makecache`, then retry |

---

## TASK 2 of 2 — Cross-check the advisory count and reboot verdict

**In plain English:** We count the security advisories two ways and assert the numbers agree, then read `needs-restarting -r` purely as a pass/fail verdict — closing the survey audit.

---

### Step 1 of 2 — Count advisories with `grep -c` and compare to the report

**In plain English:** We count security advisories live with `dnf updateinfo`, count the lines saved in the report with `grep -c`, and assert the two counts match.

```bash
live=$(dnf updateinfo list security 2>/dev/null | grep -c 'Sec\.')
saved=$(grep -c 'Sec\.' "$LAB_ROOT/security-advisories.txt")
echo "live advisories: $live | saved advisories: $saved"
test "$live" = "$saved" && echo "COUNT OK: report matches live" \
  || echo "COUNT WARN: report is stale (live=$live saved=$saved)"
```

**Expected output:**

```
live advisories: 2 | saved advisories: 2
COUNT OK: report matches live
```

**Line-by-line breakdown:**

- `live=$(dnf updateinfo list security 2>/dev/null | grep -c 'Sec\.')` → Count the live security advisories; each advisory line contains the literal `Sec.` marker, and `grep -c` returns just the count.
- `saved=$(grep -c 'Sec\.' "$LAB_ROOT/security-advisories.txt")` → Count the same marker in the report the survey saved earlier.
- `echo "live advisories: $live | saved advisories: $saved"` → Print both numbers side by side for the record.
- `test "$live" = "$saved" && ... || ...` → Assert the counts agree; a mismatch means the saved report is stale (new errata published since the survey), reported as a WARN rather than a hard fail.

**New words in this step:**

- **`grep -c`** — counts the number of matching lines instead of printing them.
- **stale report** — a saved artifact that no longer matches the live system because state changed after it was written.

---

### Step 2 of 2 — Read the reboot verdict from `needs-restarting -r`

**In plain English:** We run the reboot-recommended check and translate its exit code into a clear "reboot needed / not needed" verdict, without rebooting anything.

```bash
if command -v needs-restarting >/dev/null; then
  needs-restarting -r >/dev/null 2>&1; rc=$?
  case "$rc" in
    0) echo "REBOOT VERDICT: not required (rc=0)";;
    1) echo "REBOOT VERDICT: recommended (rc=1)";;
    *) echo "REBOOT VERDICT: unknown (rc=$rc)";;
  esac
else
  echo "needs-restarting not installed — skipping reboot verdict"
fi
echo "exit was: $?"
```

**Expected output:**

```
REBOOT VERDICT: recommended (rc=1)
exit was: 0
```

**Line-by-line breakdown:**

- `if command -v needs-restarting >/dev/null; then` → Only run the check if the helper (from `dnf-plugins-core`) is present, so the lab degrades gracefully.
- `needs-restarting -r >/dev/null 2>&1; rc=$?` → Run the reboot-recommended check silently and capture only its exit code, the actual verdict.
- `case "$rc" in 0) ... 1) ... ;;` → Translate the code: `0` = no reboot needed, `1` = reboot recommended — read as information, never as an error.
- `else echo "needs-restarting not installed ..."` → If the plugin is absent, say so instead of failing.

**New words in this step:**

- **reboot verdict** — the pass/fail interpretation of `needs-restarting -r`'s exit code.
- **graceful degradation** — a script that skips a check cleanly when an optional tool is missing.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -c 'Sec\.'` | counts security advisory lines | `.` in the pattern is escaped to match a literal dot |
| live-vs-saved compare | detects a stale report | a mismatch is a WARN (new errata), not always a bug |
| `needs-restarting -r` rc | reboot recommendation | rc `1` means "reboot advised," not "command failed" |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `COUNT WARN` every run | New errata published after the survey | Regenerate `security-advisories.txt`, then recount |
| `needs-restarting: command not found` | `dnf-plugins-core` absent | `sudo dnf install -y dnf-plugins-core` (note in Teardown) |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert each report file is non-empty with `test -s`
- [ ] Task 1 · Step 2 — Re-run `check-update` and assert a healthy exit code
- [ ] Task 2 · Step 1 — Count advisories with `grep -c` and compare to the report
- [ ] Task 2 · Step 2 — Read the reboot verdict from `needs-restarting -r`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-217
```

This lab is **read-only**: it queries DNF and reads report files but installs nothing, so there is no system state to reverse. Optionally refresh metadata with `sudo dnf clean all`, and — **only if you installed it for this lab and the system did not already need it** — remove the plugin with `sudo dnf remove -y dnf-plugins-core`.

**Expected output:**

```
✅ Removed /tmp/lab-217 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking only that a file exists (`-e`) | An empty report passes the check | Use `test -s` so empty reports fail |
| Treating `check-update` rc `100` as a failure | A healthy survey is flagged broken | Allow `{0,100}`; only `1` is a real error |
| Reading `needs-restarting -r` rc `1` as an error | You panic over a normal "reboot advised" | rc `1` is the reboot verdict, not a failure |

---

## 📌 Exam Strategy

Verifying a survey is about proving the *evidence* is real and the *exit codes* are healthy. Lead with `test -s` on every artifact, audit `dnf check-update`'s code against the `{0,100}` allow-set, and cross-check counts so a stale report cannot fool you. Treat `needs-restarting -r` and `check-update`'s `100` as verdicts to interpret, never as errors to fix.

- `test -s` beats `test -e` — an empty report is a failed report.
- Memorize the healthy set: `check-update` returns `0` or `100`; `1` means investigate.
- Cross-check counts (live vs saved) to catch stale or truncated reports.

---

## 🔗 Related Labs

- [Lab 217a — Monitor Security Updates (RHCSA)](../lab-217a-monitor-security-updates-rhcsa/) — the hand-typed survey whose reports you audit here
- [Lab 217b — Monitor Security Updates (Ansible)](../lab-217b-monitor-security-updates-ansible/) — the playbook whose artifacts and rc handling this lab validates
- [Lab 219c — Comprehensive firewalld Setup (Verify)](../lab-219c-comprehensive-firewalld-setup-verify/) — the same assert-the-evidence discipline for firewall rules

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
