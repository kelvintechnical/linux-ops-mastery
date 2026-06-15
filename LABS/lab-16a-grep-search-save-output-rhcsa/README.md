# Lab 16a: Search for a String and Save Output (RHCSA) — `grep`, `tee`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 16a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (searching files and saving results), RHCE EX294 (the search-and-capture behind reporting tasks), SRE/DevOps (log triage, evidence capture)  
**Prerequisite:** [Lab 15c](../lab-15c-searching-with-locate-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `>` (redirect) | _Task 1 · Step 1_ |
| A2 | `tee` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `grep -n` / `-i` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `grep -r` / `-l` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `grep -c` / `-o` | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `tee -a` for append-capture | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Find a string and keep the result. You will search files with `grep` (case-insensitive, line-numbered, recursive), save the hits to a file with `>`, then use `tee`/`tee -a` to capture results *and* watch them at once. You will also count matches with `grep -c` and extract just the matched text with `grep -o` — the everyday "search, save, summarize" loop.

---

## 🧠 Concept

`grep PATTERN FILE` prints lines that match. Flags shape the search: `-i` ignores case, `-n` prefixes line numbers, `-r` recurses a directory, `-l` lists only filenames with matches, `-c` counts matches, `-o` prints only the matched substring. To keep results, redirect with `>` (or capture-and-display with `tee`). The pattern is a **basic regular expression** by default; `-E` switches to extended regex.

```
grep -in "error" app.log          → 12:ERROR connection refused
grep -rl "TODO" src/              → src/main.c  (files with matches)
grep -c "GET" access.log          → 42          (match count)
grep -o "[0-9]\+" data.txt        → just the numbers
cmd | tee -a results.txt          → save AND show
```

> **Why this matters:** Half of RHCSA log tasks are "find lines containing X and save them." `grep`'s flags plus `>`/`tee` are the fastest path, and `-c`/`-o` turn a search into a usable summary.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `grep` | Print matching lines | `-i` ignore case, `-n` line numbers |
| `grep -r` / `-l` | Recurse / list filenames only | `-rl` finds which files match |
| `grep -c` / `-o` | Count matches / print only the match | `-c` per-file count |
| `>` / `>>` | Save / append output to a file | one `>` truncates |
| `tee` / `tee -a` | Save and display | `-a` appends instead of truncating |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a couple of sample log/config files containing searchable patterns.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-16
mkdir -p "$LAB_ROOT/conf"
cd "$LAB_ROOT"
printf 'INFO start\nERROR disk full\ninfo retry\nERROR timeout\n' > app.log
printf 'PermitRootLogin no\nPort 22\n#Port 2222\n' > conf/sshd_config
ls -l
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root 41 ... app.log
drwxr-xr-x. 2 root root 24 ... conf
exit was: 0
```

---

## TASK 1 of 2 — Search and save matches

**In plain English:** We find matching lines and write them to a results file, then locate which files contain a pattern.

---

### Step 1 of 2 — Search case-insensitively and save with `>`

**In plain English:** We find every line mentioning "error" regardless of case, number the lines, and save the hits to a file.

```bash
cd "$LAB_ROOT"
grep -in "error" app.log
grep -in "error" app.log > errors.txt
cat errors.txt
echo "exit was: $?"
```

**Expected output:**

```
2:ERROR disk full
4:ERROR timeout
2:ERROR disk full
4:ERROR timeout
exit was: 0
```

**Line-by-line breakdown:**

- `grep -in "error" app.log` → `-i` matches `ERROR` and `error`; `-n` prefixes each hit with its line number.
- `grep -in "error" app.log > errors.txt` → Re-run the search and save the hits with `>` (truncate-then-write).
- `cat errors.txt` → Confirm the saved file holds exactly the matched lines.

**New words in this step:**

- **`grep -i`** — case-insensitive matching.
- **`grep -n`** — prefix each match with its line number.

---

### Step 2 of 2 — Recurse and list matching files with `grep -rl`

**In plain English:** We search a directory tree and list only the filenames that contain the pattern.

```bash
cd "$LAB_ROOT"
grep -rl "Port" conf/
grep -rn "Port" conf/
echo "exit was: $?"
```

**Expected output:**

```
conf/sshd_config
conf/sshd_config:2:Port 22
conf/sshd_config:3:#Port 2222
exit was: 0
```

**Line-by-line breakdown:**

- `grep -rl "Port" conf/` → `-r` recurses the directory, `-l` prints only the *names* of files that match.
- `grep -rn "Port" conf/` → Same recursion but with line numbers and the matching lines for detail.

**New words in this step:**

- **`grep -r`** — recurse into a directory tree.
- **`grep -l`** — print only the filenames containing a match.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `grep -i` | case-insensitive | default grep is case-sensitive |
| `grep -rl` | which files match | `-l` hides the lines themselves |
| `>` save | truncate then write | one `>` wipes prior results |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| No matches but you expected some | Case mismatch | Add `-i` |
| `grep: conf/: Is a directory` | Missing `-r` | Add `-r` for directories |

---

## TASK 2 of 2 — Capture-and-show, then summarize

**In plain English:** We use `tee` to save results while watching them, then count and extract matches.

---

### Step 1 of 2 — Save and display with `tee -a`

**In plain English:** We append search results to a running report file while still seeing them on screen.

```bash
cd "$LAB_ROOT"
grep -i "error" app.log | tee report.txt
grep -i "info" app.log | tee -a report.txt
cat report.txt
echo "exit was: $?"
```

**Expected output:**

```
ERROR disk full
ERROR timeout
INFO start
info retry
ERROR disk full
ERROR timeout
INFO start
info retry
exit was: 0
```

**Line-by-line breakdown:**

- `grep -i "error" app.log | tee report.txt` → Pipe the matches to `tee`, which writes them to `report.txt` AND echoes them.
- `grep -i "info" app.log | tee -a report.txt` → `-a` appends the next batch instead of truncating, building a combined report.
- `cat report.txt` → Confirm both batches landed in the file.

**New words in this step:**

- **`tee -a`** — write stdout to a file (appending) while also displaying it.

---

### Step 2 of 2 — Count and extract with `grep -c` / `-o`

**In plain English:** We count how many lines match and pull out just the matched words.

```bash
cd "$LAB_ROOT"
grep -c "ERROR" app.log
grep -o "ERROR" app.log
echo "exit was: $?"
```

**Expected output:**

```
2
ERROR
ERROR
exit was: 0
```

**Line-by-line breakdown:**

- `grep -c "ERROR" app.log` → `-c` prints the *count* of matching lines (2), not the lines.
- `grep -o "ERROR" app.log` → `-o` prints only the matched text per occurrence, useful for tallying tokens.

**New words in this step:**

- **`grep -c`** — count matching lines.
- **`grep -o`** — print only the matched substring, one per line.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `tee` vs `>` | save AND display | `tee` without `-a` truncates |
| `grep -c` | count lines, not matches | two matches on one line count once |
| `grep -o` | extract substrings | counts every occurrence, even same line |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `tee` overwrote the report | Missing `-a` | Use `tee -a` to append |
| `-c` count seems low | Multiple matches per line | Use `grep -o | wc -l` for occurrences |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Search case-insensitively and save with `>`
- [ ] Task 1 · Step 2 — Recurse and list matching files with `grep -rl`
- [ ] Task 2 · Step 1 — Save and display with `tee -a`
- [ ] Task 2 · Step 2 — Count and extract with `grep -c` / `-o`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-16
```

**Expected output:**

```
✅ Removed /tmp/lab-16 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `tee` without `-a` | Earlier results lost | Use `tee -a` to append |
| Forgetting `-r` on a dir | "Is a directory" error | Add `-r` |
| Confusing `-c` and `-o` counts | Wrong totals | `-c` lines vs `-o`+`wc -l` occurrences |

---

## 📌 Exam Strategy

"Find lines containing X and save them to /path" is a stock task. Reach for `grep -i`/`-n` to search and `>` to save; use `tee -a` when you must both keep and observe. `grep -rl` quickly answers "which file holds this setting?"

- `grep -rl` is the fastest "which config has this?" answer.
- `tee -a` builds reports without losing earlier output.
- `grep -c` gives an instant pass/fail count for assertions.

---

## 🔗 Related Labs

- [Lab 16b — Search and Save Output (Ansible)](../lab-16b-grep-search-save-output-ansible/) — capture matches with `command:`/`lineinfile`
- [Lab 16c — Search and Save Output (Verify)](../lab-16c-grep-search-save-output-verify/) — prove the saved results are correct
- [Lab 22a — Filtering Text with grep and Regex (RHCSA)](../lab-22a-grep-regex-rhcsa/) — deeper regex with `grep -E`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
