# Lab 24a: Stream Editing with sed (RHCSA) — `sed s///`, addresses, `-i`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 24a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (non-interactive text editing), RHCE EX294 (the engine behind `replace`), SRE/DevOps (bulk config edits)  
**Prerequisite:** [Lab 23c](../lab-23c-diff-comparing-files-verify/) completed  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | regex (`-E` patterns) | _Task 1 · Step 1_ |
| A2 | `cp` / backups | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `sed 's/old/new/'` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `sed` addresses (line / `/re/`) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `sed -i.bak` (in-place + backup) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `sed -n 'p'` / `d` (print/delete) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Edit text without opening an editor. You will substitute with `sed 's///'` (including flags `g` and `I`), target edits with line and regex *addresses*, edit files in place with a safety backup (`-i.bak`), and print or delete selected lines (`-n p`, `d`). By the end you can transform configs and logs reproducibly from the command line or a script.

---

## 🧠 Concept

`sed` (stream editor) reads input line by line, applies commands, and emits the result — non-interactive editing built for pipes and scripts. The workhorse is substitution: `s/regex/replacement/flags`, where `g` replaces all occurrences on a line (not just the first) and `I` is case-insensitive. **Addresses** restrict which lines a command touches: a line number (`3s/.../.../`), a range (`2,5d`), or a regex (`/^Port/s/22/2222/`). `-i` edits the file in place; always use `-i.bak` so a timestamped/`.bak` backup is kept. `-n` suppresses auto-print so `p` prints only what you select; `d` deletes lines.

```
sed 's/foo/bar/' f        → replace first foo per line
sed 's/foo/bar/g' f       → replace all foo per line
sed '/^#/d' f             → delete comment lines
sed -n '10,20p' f         → print only lines 10-20
sed -i.bak 's/22/2222/' f → edit in place, keep f.bak
```

> **Why this matters:** `sed` is the non-interactive editor of choice for scripts and one-off bulk fixes, and it's the engine behind Ansible's `replace`. `-i.bak` is the seatbelt that makes in-place edits safe.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `sed 's///'` | Substitute | `g` all, `I` ignore case |
| address `Ns` `/re/` | Restrict edits | line, range, or regex |
| `sed -i.bak` | In-place + backup | never bare `-i` blindly |
| `sed -n 'p'` | Print selected | `-n` suppresses auto-print |
| `sed 'd'` | Delete lines | with an address |
| `sed -E` | Extended regex | groups, `+ ? |` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a config to stream-edit.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-24
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"
cat > sshd.conf <<'EOF'
# main config
Port 22
Port 22
LogLevel INFO
# PermitRootLogin yes
MaxAuthTries 6
EOF
cat sshd.conf
echo "exit was: $?"
```

**Expected output:**

```
# main config
Port 22
Port 22
LogLevel INFO
# PermitRootLogin yes
MaxAuthTries 6
exit was: 0
```

---

## TASK 1 of 2 — Substitute and address

**In plain English:** We replace text, then target specific lines with addresses.

---

### Step 1 of 2 — Substitute with `s///` and `g`

**In plain English:** We change INFO to DEBUG, and show how `g` affects multiple matches on a line.

```bash
cd "$LAB_ROOT"
sed 's/INFO/DEBUG/' sshd.conf | grep LogLevel
echo "a a a" | sed 's/a/b/'
echo "a a a" | sed 's/a/b/g'
echo "exit was: $?"
```

**Expected output:**

```
LogLevel DEBUG
b a a
b b b
exit was: 0
```

**Line-by-line breakdown:**

- `sed 's/INFO/DEBUG/'` → Replace the first `INFO` on each line — here LogLevel becomes DEBUG.
- `s/a/b/` vs `s/a/b/g` → Without `g` only the first match changes; with `g` every match on the line changes.

**New words in this step:**

- **`sed 's/old/new/'`** — substitute command; `g` flag replaces all per line.

---

### Step 2 of 2 — Target lines with addresses

**In plain English:** We delete comment lines and edit only the line matching a regex.

```bash
cd "$LAB_ROOT"
sed '/^#/d' sshd.conf
echo "---"
sed '/^Port/s/22/2222/' sshd.conf | grep Port
echo "exit was: $?"
```

**Expected output:**

```
Port 22
Port 22
LogLevel INFO
MaxAuthTries 6
---
Port 2222
Port 2222
exit was: 0
```

**Line-by-line breakdown:**

- `sed '/^#/d'` → Address `/^#/` selects comment lines; `d` deletes them from the stream.
- `sed '/^Port/s/22/2222/'` → Only on lines matching `/^Port/`, substitute 22→2222.

**New words in this step:**

- **address** — a line number, range, or `/regex/` that restricts where a command applies.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `s///` | substitute | first match unless `g` |
| `/re/cmd` | regex address | applies only to matches |
| `d` | delete line | needs an address |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Only first match changed | Missing `g` | Add `g` flag |
| Edited wrong lines | No/loose address | Anchor the address regex |

---

## TASK 2 of 2 — In-place edits and selection

**In plain English:** We edit the file in place with a backup, then print and delete selectively.

---

### Step 1 of 2 — Edit in place with `-i.bak`

**In plain English:** We change the Port to 2222 directly in the file, keeping a backup.

```bash
cd "$LAB_ROOT"
sed -i.bak 's/^Port 22$/Port 2222/' sshd.conf
grep Port sshd.conf
echo "--- backup ---"
grep Port sshd.conf.bak
echo "exit was: $?"
```

**Expected output:**

```
Port 2222
Port 2222
--- backup ---
Port 22
Port 22
exit was: 0
```

**Line-by-line breakdown:**

- `sed -i.bak 's/^Port 22$/Port 2222/'` → Edit the file in place; `.bak` keeps the original as `sshd.conf.bak`.
- `grep Port sshd.conf.bak` → The backup still shows the original `Port 22`.

**New words in this step:**

- **`-i.bak`** — in-place edit that first saves a `.bak` backup.

---

### Step 2 of 2 — Print and delete selected lines

**In plain English:** We print only a line range, then produce a comment-free version.

```bash
cd "$LAB_ROOT"
sed -n '1,2p' sshd.conf
echo "---"
sed '/^#/d' sshd.conf | sed '/^$/d' > sshd.clean
cat sshd.clean
echo "exit was: $?"
```

**Expected output:**

```
# main config
Port 2222
---
Port 2222
Port 2222
LogLevel INFO
MaxAuthTries 6
exit was: 0
```

**Line-by-line breakdown:**

- `sed -n '1,2p'` → `-n` suppresses auto-print; `1,2p` prints only lines 1–2.
- `sed '/^#/d' | sed '/^$/d'` → Delete comment lines, then blank lines, producing a clean config.

**New words in this step:**

- **`-n` + `p`** — print only explicitly selected lines.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-i.bak` | safe in-place | bare `-i` has no undo |
| `-n 'Np'` | selective print | `-n` required |
| chained `sed` | pipe filters | order matters |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Lost original | Bare `-i` | Always `-i.bak` |
| `p` prints everything twice | Forgot `-n` | Add `-n` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Substitute with `s///` and `g`
- [ ] Task 1 · Step 2 — Target lines with addresses
- [ ] Task 2 · Step 1 — Edit in place with `-i.bak`
- [ ] Task 2 · Step 2 — Print and delete selected lines
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-24
```

**Expected output:**

```
✅ Removed /tmp/lab-24 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Bare `sed -i` | No backup, no undo | Use `-i.bak` |
| Missing `g` | Only first match changed | Add `g` |
| Unanchored address | Wrong lines edited | Anchor with `^`/`$` |

---

## 📌 Exam Strategy

`sed` is your non-interactive editor: substitute with `s///g`, restrict with addresses, and always edit in place with `-i.bak`. Use `-n p` to extract and `d` to remove — and remember `sed -E` for readable regex.

- `-i.bak` every in-place edit.
- Anchor addresses to hit exactly the right lines.
- `sed -E` for grouped/quantified patterns.

---

## 🔗 Related Labs

- [Lab 24b — Stream Editing with sed (Ansible)](../lab-24b-sed-stream-editor-ansible/) — `replace`/`lineinfile` instead of `sed -i`
- [Lab 24c — Stream Editing with sed (Verify)](../lab-24c-sed-stream-editor-verify/) — prove edits and backups
- [Lab 25a — Extracting Columns with awk (RHCSA)](../lab-25a-awk-columns-rhcsa/) — field-oriented text processing

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
