# Lab 01a: Stdout Redirection (RHCSA) — `>`, `>>`

**Series:** linux-ops-mastery — Shells, Terminals & Redirection · **Lab 01a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (every "save the output to a file" task), RHCE EX294 (the shell muscle memory behind `ansible.builtin.shell`), SRE/DevOps (log capture, build artifacts)  
**Prerequisite:** A RHEL/Rocky/Alma sandbox you can `sudo` on — no prior lab required (this is the first lab)  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Objective

Learn to direct a command's normal text output (stdout) into a file instead of the screen, using the two operators you will type more than any other on the exam: `>` to write a **new** file (truncate-then-write) and `>>` to **append** to an existing one. By the end you can write, append, count, and log text safely — and you will have felt the silent data-loss trap that catches everyone exactly once.

---

## 🧠 Concept

Every command prints its results to **stdout** (*standard output*), which by default lands on your terminal. Redirection re-points that stream into a file. `>` opens the target, **truncates** it to zero bytes, and writes — so it destroys whatever was there. `>>` opens the target and **appends**, preserving the existing contents. The single missing `>` is the difference between adding a line and wiping a file with no warning and no undo.

```
echo "hi" >  file.txt     FD 1 ─▶ [ truncate file to 0 bytes ] ─▶ write "hi"
echo "hi" >> file.txt     FD 1 ─▶ [ keep contents, seek to end ] ─▶ append "hi"
wc -l     <  file.txt     file.txt ─▶ FD 0 (stdin)   → prints bare line count
echo x | tee -a file.txt  FD 1 ─▶ tee ─┬─▶ screen
                                       └─▶ file (append)
```

> **Why this matters:** On a real system, typing one `>` when you meant two is how admins erase log files, configs, and `~/.ssh/authorized_keys` instantly. The habit you build here — "`>` first to start fresh, then `>>` to add" — is the single most repeated reflex in Linux operations.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `>` | Redirect stdout to a file, truncating it first (creates if missing) | one `>` truncates — never use it when you meant to append |
| `>>` | Redirect stdout to a file, appending to the end (creates if missing) | two `>` preserve existing content |
| `tee -a` | Write stdout to a file **and** echo it to the screen | `-a` appends; without it, `tee` truncates |
| `wc -l` | Count lines | `wc -l < file` prints just the number, no filename |
| `<` | Redirect a file into stdin | feeds the file as input, so output has no filename attached |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Before any task we build a private, throwaway workspace under `/tmp` — a sandbox folder plus a disposable group and user account that own it — so nothing we do touches the real system. We save the names in variables first so we never have to retype them.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

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
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
uid=1001(labuser_01_stdout-redirection) gid=1001(labgrp_01_stdout-redirection) groups=1001(labgrp_01_stdout-redirection)
drwxr-xr-x. 3 labuser_01_stdout-redirection labgrp_01_stdout-redirection 60 Jun 15 17:20 /tmp/labsandbox_01
drwxr-xr-x. 2 labuser_01_stdout-redirection labgrp_01_stdout-redirection  6 Jun 15 17:20 /tmp/labsandbox_01/home_labuser_01_stdout-redirection
Sandbox built by root at 2026-06-15T17:20:01-04:00
exit was: 0
```

---

## TASK 1 of 2 — Canonical stdout redirection (`>`, `>>`, `wc -l`, `tee -a`)

**In plain English:** This task teaches the four safe, everyday moves — write a file, add to it, count its lines, and log a line while still seeing it on screen. Nothing here destroys data.

---

### Step 1 of 2 — Write a file with `>`, then append with `>>`

**In plain English:** We create a brand-new file with one line, then add a second line to the bottom of it, then read the whole thing back to prove both lines are there — the single most common thing you will ever do with redirection.

```bash
echo "first line"  >  "${SANDBOX}/notes.txt"
echo "second line" >> "${SANDBOX}/notes.txt"
cat                   "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

**Expected output:**

```
first line
second line
exit was: 0
```

**Line-by-line breakdown:**

- `echo "first line" > "${SANDBOX}/notes.txt"` → Print `first line`, but send it into the file; the single `>` truncates the file (empties it to zero bytes) and then writes, creating it fresh if it did not exist.
- `echo "second line" >> "${SANDBOX}/notes.txt"` → Print `second line` and append it to the bottom; `>>` (two of them) means "append without erasing what is already there."
- `cat "${SANDBOX}/notes.txt"` → Read the whole file to the screen so we can see both lines, then `echo "exit was: $?"` prints `cat`'s exit status (`0` = success).

**New words in this step:**

- **stdout** — the normal text output a command prints to the screen (file descriptor 1).
- **truncate** — to instantly empty a file down to zero bytes (what a single `>` does before it writes).

---

### Step 2 of 2 — Count lines with `wc -l`, then log-and-show with `tee -a`

**In plain English:** First we count how many lines the file has using a trick that prints just the number, then we add a third line in a way that writes it to the file *and* shows it on screen at the same time — the standard "log this but let me watch it too" move.

```bash
wc -l < "${SANDBOX}/notes.txt"
echo "third line" | tee -a "${SANDBOX}/notes.txt"
echo "exit was: $?"
```

**Expected output:**

```
2
third line
exit was: 0
```

**Line-by-line breakdown:**

- `wc -l < "${SANDBOX}/notes.txt"` → Count lines; `wc` is "word count," `-l` says "lines only," and `<` feeds the file in as stdin so the output is just the bare number with no filename attached.
- `echo "third line" | tee -a "${SANDBOX}/notes.txt"` → Print `third line`, then `|` (the pipe) hands it to `tee`, which writes it to the file AND echoes it to your screen; `-a` means "append" (without `-a`, `tee` truncates the file first — the same trap as `>` vs `>>`).
- `echo "exit was: $?"` → Print the exit status of the `tee` pipeline.

**New words in this step:**

- **pipe (`|`)** — a connector that feeds the output of the command on the left into the command on the right.
- **`tee`** — a tool that splits output two ways: into a file and onto the screen at once (named after a T-shaped pipe fitting).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `>` | truncate-then-write stdout to a file | silently destroys prior contents |
| `>>` | append stdout to a file | one `>` instead of two = data loss |
| `wc -l < f` | count lines without printing the filename | unterminated final line is not counted |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| File only has the last line | You used `>` where you meant `>>` | Rebuild with `>` for line 1, `>>` for the rest |
| `wc -l` prints `2 filename` | You wrote `wc -l file` instead of `wc -l < file` | Use `< file` so only the number prints |

---

## TASK 2 of 2 — The contrast: silent-overwrite trap, `noclobber`, and the `sudo` gotcha

**In plain English:** This is the "feel the pain" half — we build a file correctly, deliberately destroy it with a single `>`, then turn on a safety net (`noclobber`) and learn the one `sudo` redirection gotcha that fools everybody once.

---

### Step 1 of 2 — Build it right, then break it on purpose

**In plain English:** First we build a clean three-line file the correct way, then run a single `>` against it and read it back to watch two of the three lines vanish without any warning — the trap demonstrated live.

```bash
echo "alpha"   >  "${SANDBOX}/notes.txt"
echo "bravo"   >> "${SANDBOX}/notes.txt"
echo "charlie" >> "${SANDBOX}/notes.txt"
echo "newest"  >  "${SANDBOX}/notes.txt"
cat               "${SANDBOX}/notes.txt"
```

**Expected output:**

```
newest
```

**Line-by-line breakdown:**

- `echo "alpha" > ...` → Start the file fresh with `alpha`; the first line MUST use `>` so no stale leftovers from an old run survive.
- `echo "bravo" >> ...` / `echo "charlie" >> ...` → Append the next two lines without erasing, giving a correct three-line file.
- `echo "newest" > ...` → A single `>` truncates the file to empty and writes only `newest`; `alpha`, `bravo`, and `charlie` are gone instantly, with no warning and no recycle bin.
- `cat "${SANDBOX}/notes.txt"` → Read it back — you see ONLY `newest`, the canonical "I meant `>>` and typed `>`" data-loss event.

**New words in this step:**

- **clobber** — to overwrite a file's contents (the thing `noclobber`, next step, prevents).

---

### Step 2 of 2 — Protect with `noclobber`, then the `sudo` ownership gotcha

**In plain English:** We switch on a safety net called `noclobber` that makes the shell refuse to overwrite an existing file with `>`, then meet the famous `sudo` redirection gotcha where a file ends up root-owned even though you ran the command "as" another user — and fix it with the `| sudo tee` trick.

```bash
set -o noclobber
echo "blocked?" > "${SANDBOX}/notes.txt"
echo "exit was: $?"
set +o noclobber
echo "owned by labuser" | sudo -u "${LAB_USER}" tee "${SANDBOX}/labuser_note.txt" >/dev/null
stat -c '%U:%G %a %n' "${SANDBOX}/labuser_note.txt"
```

**Expected output:**

```
bash: /tmp/labsandbox_01/notes.txt: cannot overwrite existing file
exit was: 1
labuser_01_stdout-redirection:labgrp_01_stdout-redirection 644 /tmp/labsandbox_01/labuser_note.txt
```

**Line-by-line breakdown:**

- `set -o noclobber` → Turn on the shell setting that refuses to let `>` overwrite a file that already exists; the next line is blocked and `$?` is non-zero (`1`).
- `set +o noclobber` → Turn the protection back off (`+o` undoes `-o`) so normal work continues.
- `echo "owned by labuser" | sudo -u "${LAB_USER}" tee ... >/dev/null` → Pipe the text to `tee` running **as the lab user**, so `tee` opens the file with the lab user's identity and the lab user owns the bytes; `>/dev/null` discards tee's screen echo. (If you had written `sudo -u "${LAB_USER}" echo ... > file`, the shell would open `file` as root *before* sudo runs, leaving it root-owned — the gotcha.)
- `stat -c '%U:%G %a %n' ...` → Audit the file's owner, group, octal mode, and name; it correctly shows the lab user, not root.

**New words in this step:**

- **noclobber** — a shell setting that blocks `>` from overwriting an existing file.
- **`stat`** — a tool that prints a file's metadata (owner, group, permissions, name).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `set -o noclobber` | refuse `>` on existing files | OFF by default — must be enabled per shell |
| `sudo -u USER cmd > file` | redirection runs in the OUTER (root) shell | file ends up root-owned, not USER-owned |
| `\| sudo -u USER tee file` | the write runs as USER | file ends up USER-owned (the correct fix) |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `cannot overwrite existing file` when you meant to | `noclobber` is on | Use `>\|` to force, or `set +o noclobber` |
| File is `root`-owned after `sudo -u user ... > file` | The shell opened the file before `sudo` ran | Use `... \| sudo -u user tee file` instead |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write a file with `>`, then append with `>>`
- [ ] Task 1 · Step 2 — Count lines with `wc -l`, then log-and-show with `tee -a`
- [ ] Task 2 · Step 1 — Build it right, then break it on purpose
- [ ] Task 2 · Step 2 — Protect with `noclobber`, then the `sudo` ownership gotcha

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `>` when you meant `>>` | File suddenly contains only the newest line | Build with `>` once, then always `>>` to add |
| `wc -l file` instead of `wc -l < file` | Output includes the filename | Feed via `<` so only the number prints |
| `sudo -u user cmd > file` | File is owned by root | Pipe to `sudo -u user tee file` so the write happens as the user |

---

## 📌 Exam Strategy

On the RHCSA, redirection shows up inside almost every task that asks you to "save the output." Reach for `>` only when you intend to create or replace, and `>>` whenever you are adding to something that must survive. When ownership matters (a file a service or another user must read), build it with `sudo -u USER tee`, not a root-shell `>`.

- Say "`>` overwrites, `>>` appends" out loud before you type the arrow — it prevents the one-character data-loss slip.
- Use `wc -l < file` to verify line counts cleanly; the bare number is easy to compare against an expected value.
- After any `2>/dev/null`-style silencing in later labs, still check `$?` — redirection hides text, not exit codes.

---

## 🔗 Related Labs

- [Lab 01b — Stdout Redirection (Ansible)](../lab-01b-stdout-redirection-ansible/) — the same outcome expressed (and bounded) in an Ansible playbook
- [Lab 01c — Stdout Redirection (Verify)](../lab-01c-stdout-redirection-verify/) — prove `>` truncates and `>>` preserves with hard evidence
- [Lab 02a — Stderr Redirection (RHCSA)](../lab-02a-stderr-redirection-rhcsa/) — the next stream: capturing errors with `2>`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
