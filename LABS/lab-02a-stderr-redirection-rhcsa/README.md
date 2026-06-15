# Lab 02a: Stderr Redirection (RHCSA) — `2>`, `2>/dev/null`

**Series:** linux-ops-mastery — Shells, Terminals & Redirection · **Lab 02a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (every `find /` task that emits `Permission denied`), RHCE EX294 (`result.stderr` is the same stream `2>` captures), SRE/DevOps (post-mortems and CI failures live on stderr)  
**Prerequisite:** [Lab 01a](../lab-01a-stdout-redirection-rhcsa/) and [Lab 01c](../lab-01c-stdout-redirection-verify/) — you understand FD 1, `>`, `>>`, and `wc -l`  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Stop letting error messages scroll off the top of your terminal. Learn to capture the **error stream** (stderr, file descriptor 2) independently of normal output using `2>`, silence noisy `Permission denied` lines with `2>/dev/null`, and understand the order trap where `2>&1`'s position changes everything. By the end you can produce the RHCSA-classic clean answer: real results in a file, errors thrown away — without losing the exit code.

---

## 🧠 Concept

Every process has three streams: stdin (FD 0), stdout (FD 1, the data), and **stderr (FD 2, the diagnostics)**. They both display on your terminal by default, which makes them *look* like one stream — but `>` only redirects FD 1, so errors keep hitting the screen. `2>` redirects FD 2 specifically. The merge operator `2>&1` means "send FD 2 wherever FD 1 currently points," and the shell processes redirections strictly left to right — which is why order matters.

```
   FD 1  stdout  →  terminal (DATA)    ◄─ > file      captures FD 1 only
   FD 2  stderr  →  terminal (ERRORS)  ◄─ 2> file     captures FD 2 only

   > f 2>&1   FD 1→f, then FD 2→(where FD1 points = f)   → BOTH in file   ✅
   2>&1 > f   FD 2→(where FD1 points = terminal!), then FD 1→f → stderr on screen ❌
   2>/dev/null   discard FD 2 — the RHCSA find reflex
```

> **Why this matters:** The bug "my log file is empty even though the screen was full of red" is exactly this: `> file` captured stdout while every error went to the terminal. And `2>/dev/null` hides the message but **not** the exit code — silencing a command never tells you it succeeded.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `2>` | Redirect stderr (FD 2) to a file, truncating it | independent of FD 1 — order vs `>` does not matter for separate files |
| `2>/dev/null` | Discard stderr entirely | hides text, not `$?` — always still check the exit code |
| `> f 2> g` | Split: stdout to `f`, stderr to `g` | two files, one command |
| `2>&1` | Merge FD 2 into wherever FD 1 currently points | order-sensitive — must come *after* `>` to land in the file |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox plus a non-privileged lab user, because the easiest way to generate real `Permission denied` errors is to run `find /var/log` as someone who cannot read every directory.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export SANDBOX=/tmp/lab02a
export GROUP=labgrp_02_stderr
export LAB_USER=labuser_02_stderr
export LAB_USER_HOME=${SANDBOX}/home_${LAB_USER}

mkdir -p "${SANDBOX}" "${LAB_USER_HOME}"
getent group  "${GROUP}"    >/dev/null || groupadd "${GROUP}"
getent passwd "${LAB_USER}" >/dev/null || useradd \
    -d "${LAB_USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${LAB_USER}"
chown -R "${LAB_USER}:${GROUP}" "${SANDBOX}"
id "${LAB_USER}"
ls -ld "${SANDBOX}" /var/log
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
uid=1002(labuser_02_stderr) gid=1002(labgrp_02_stderr) groups=1002(labgrp_02_stderr)
drwxr-xr-x. 3 labuser_02_stderr labgrp_02_stderr 60 Jun 15 17:35 /tmp/lab02a
drwxr-xr-x. 2 root root 4096 Jun 15 17:35 /var/log
Sandbox built by root at 2026-06-15T17:35:09-04:00
exit was: 0
```

---

## TASK 1 of 2 — Capture stderr with `2>` and silence it with `2>/dev/null`

**In plain English:** We run `find /var/log` as the lab user to generate real errors, split the streams into two separate files to prove they are independent, then use the RHCSA clean-answer pattern that keeps the results and discards the noise.

---

### Step 1 of 2 — Split the streams with `> file 2> file`

**In plain English:** We run `find` as the non-privileged lab user and send normal results to one file and errors to another, then count each so the separation is undeniable.

```bash
sudo -u "${LAB_USER}" bash -c \
  'find /var/log -name "*.log" -type f \
      >  '"${LAB_USER_HOME}"'/log-files.txt \
      2> '"${LAB_USER_HOME}"'/log-errors.txt'
echo "stdout lines: $(wc -l < "${LAB_USER_HOME}/log-files.txt")"
echo "stderr lines: $(wc -l < "${LAB_USER_HOME}/log-errors.txt")"
head -1 "${LAB_USER_HOME}/log-errors.txt"
```

**Expected output:**

```
stdout lines: 21
stderr lines: 3
find: '/var/log/audit': Permission denied
```

**Line-by-line breakdown:**

- `sudo -u "${LAB_USER}" bash -c '...'` → Run the whole redirect *as the lab user* so the privilege drop produces real `Permission denied` lines (root would produce none).
- `find /var/log -name "*.log" -type f > .../log-files.txt 2> .../log-errors.txt` → The shell wires FD 1 to `log-files.txt` and FD 2 to `log-errors.txt`; they are independent, so order does not matter here.
- `wc -l < .../log-files.txt` and `< .../log-errors.txt` → Count each stream separately — clean paths on stdout, denied paths on stderr.
- `head -1 .../log-errors.txt` → Show the first error line to confirm stderr holds the `Permission denied` text.

**New words in this step:**

- **stderr** — the error/diagnostic stream, file descriptor 2, separate from the data stream FD 1.
- **file descriptor** — a small integer the kernel uses to track an open stream (0 stdin, 1 stdout, 2 stderr).

---

### Step 2 of 2 — Keep the answer, discard the noise with `2>/dev/null`

**In plain English:** We run the same `find` but throw the errors into the kernel's bit-bucket, keeping only the clean list — and then prove that silencing the error does **not** hide a failing command's exit code.

```bash
sudo -u "${LAB_USER}" bash -c \
  'find /var/log -name "*.log" -type f 2>/dev/null' \
  > "${LAB_USER_HOME}/log-clean.txt"
wc -l < "${LAB_USER_HOME}/log-clean.txt"
find /no/such/path 2>/dev/null
echo "silenced failing find exit code: $?"
```

**Expected output:**

```
21
silenced failing find exit code: 1
```

**Line-by-line breakdown:**

- `find ... 2>/dev/null` → Open the kernel's discard device for FD 2; every error byte is silently accepted and dropped, leaving only the clean results on stdout.
- `> "${LAB_USER_HOME}/log-clean.txt"` → Capture that clean stdout to a file.
- `wc -l < .../log-clean.txt` → Confirm the clean answer has the same count as the stdout file from Step 1.
- `find /no/such/path 2>/dev/null` then `echo "...: $?"` → Even with stderr silenced, the failing `find` still exits `1` — `2>/dev/null` hid the message, not the exit code.

**New words in this step:**

- **`/dev/null`** — a special file that discards everything written to it (the "bit-bucket").

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `2>` | send stderr to a file (truncate) | `>` alone does NOT silence errors (T02-B) |
| `> f 2> g` | split streams to two files | order of `>` and `2>` is irrelevant for separate files |
| `2>/dev/null` | discard stderr | hides text, NOT `$?` — always check the exit code |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `stderr lines: 0` | Running as root (reads everything) | Run via `sudo -u "${LAB_USER}"` as shown |
| Both files hold the same mixed text | You used `2>&1` instead of `2> file2` | Use two separate targets |

---

## TASK 2 of 2 — `2>>` append and the `2>&1` order trap

**In plain English:** We accumulate errors across two runs with `2>>`, then prove the famous order trap: `> file 2>&1` puts both streams in the file, while `2>&1 > file` leaves stderr on the screen — same tokens, different result.

---

### Step 1 of 2 — Accumulate errors with `2>>`

**In plain English:** We run `find` twice, appending each run's errors to the same growing log with `2>>`, the way you build a cumulative error log from a service that keeps failing.

```bash
sudo -u "${LAB_USER}" bash -c '
  find /var/log -name "*.log"  -type f >> '"${LAB_USER_HOME}"'/all.txt 2>> '"${LAB_USER_HOME}"'/errs.txt
  find /var/log -name "*.conf" -type f >> '"${LAB_USER_HOME}"'/all.txt 2>> '"${LAB_USER_HOME}"'/errs.txt
'
echo "combined results: $(wc -l < "${LAB_USER_HOME}/all.txt")"
echo "combined errors:  $(wc -l < "${LAB_USER_HOME}/errs.txt")"
```

**Expected output:**

```
combined results: 46
combined errors:  6
```

**Line-by-line breakdown:**

- two `find` lines with `>>` and `2>>` → Each run appends its stdout to `all.txt` and its stderr to `errs.txt`; `2>>` (like `>>` for FD 1) preserves prior content instead of truncating.
- `wc -l < .../all.txt` and `< .../errs.txt` → Count the accumulated results and errors; both files grew across the two runs rather than being overwritten.

**New words in this step:**

- **`2>>`** — append stderr to a file (the FD-2 version of `>>`).

---

### Step 2 of 2 — Prove the `2>&1` order trap

**In plain English:** We run the same command two ways — correct merge (`> file 2>&1`) and wrong order (`2>&1 > file`) — then grep each captured file for `Permission denied` to prove only the correct form put the errors *in* the file.

```bash
sudo -u "${LAB_USER}" bash -c 'find /var/log -name "*.log" -type f >  '"${LAB_USER_HOME}"'/formA.txt 2>&1'
sudo -u "${LAB_USER}" bash -c 'find /var/log -name "*.log" -type f 2>&1 >  '"${LAB_USER_HOME}"'/formB.txt'
echo "Form A (> file 2>&1) PD in file: $(grep -c 'Permission denied' "${LAB_USER_HOME}/formA.txt")"
echo "Form B (2>&1 > file) PD in file: $(grep -c 'Permission denied' "${LAB_USER_HOME}/formB.txt")"
```

**Expected output:**

```
find: '/var/log/audit': Permission denied
Form A (> file 2>&1) PD in file: 3
Form B (2>&1 > file) PD in file: 0
```

**Line-by-line breakdown:**

- Form A `> formA.txt 2>&1` → FD 1 points at the file *first*, then `2>&1` sends FD 2 to "wherever FD 1 now goes" — the file. Both streams land in `formA.txt`.
- Form B `2>&1 > formB.txt` → `2>&1` runs *first*, when FD 1 still points at the terminal, so FD 2 goes to the screen; only then does `> formB.txt` redirect FD 1. Stderr never reaches the file (you see it printed on screen).
- the two `grep -c 'Permission denied'` lines → Count the error lines captured in each file; Form A has them, Form B has zero — the trap, proven.

**New words in this step:**

- **`2>&1`** — make FD 2 point wherever FD 1 *currently* points; position-sensitive.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `2>>` | append stderr across runs | one `2>` instead truncates each run |
| `> file 2>&1` | correct merge — both streams to file | this is the order you want |
| `2>&1 > file` | FD 2 → screen, FD 1 → file (T02-A) | looks symmetric, behaves differently |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Form A and Form B look identical | Ran as root, so no `Permission denied` anywhere | Run via `sudo -u "${LAB_USER}"` |
| Errors missing from the merged file | You wrote `2>&1 > file` (wrong order) | Put `2>&1` *after* `> file` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Split the streams with `> file 2> file`
- [ ] Task 1 · Step 2 — Keep the answer, discard the noise with `2>/dev/null`
- [ ] Task 2 · Step 1 — Accumulate errors with `2>>`
- [ ] Task 2 · Step 2 — Prove the `2>&1` order trap

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `> file` to silence errors | Errors still print to the screen | Add `2>/dev/null` or `2> errors.txt` |
| Writing `2>&1 > file` | Stderr stays on the terminal | Always `> file 2>&1` — redirect FD 1 first |
| Assuming `2>/dev/null` means success | A failed command looks like it passed | Check `$?` after any silenced command |

---

## 📌 Exam Strategy

The RHCSA `find` task almost always reduces to "find these files, suppress the errors, save the clean list." That is `find ... 2>/dev/null > answer.txt`. Train the reflex to redirect FD 2 deliberately, and to put `2>&1` *after* `>` when you want one combined log. Never let a `2>/dev/null` lull you into ignoring the exit code.

- Memorize the clean-answer pattern: `find / -name '*.conf' 2>/dev/null > /root/conf-files.txt`.
- Say "redirect FD 1 first, then merge FD 2" before typing `2>&1`.
- After silencing stderr, run `echo $?` to confirm the command actually succeeded.

---

## 🔗 Related Labs

- [Lab 02b — Stderr Redirection (Ansible)](../lab-02b-stderr-redirection-ansible/) — `register:` exposes `stderr_lines` automatically
- [Lab 02c — Stderr Redirection (Verify)](../lab-02c-stderr-redirection-verify/) — audit the captured stderr and prove the order trap happened
- [Lab 01a — Stdout Redirection (RHCSA)](../lab-01a-stdout-redirection-rhcsa/) — FD 1, the stream this lab extends with FD 2

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
