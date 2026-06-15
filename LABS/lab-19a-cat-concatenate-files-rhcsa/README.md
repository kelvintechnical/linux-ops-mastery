# Lab 19a: Concatenating Files with cat (RHCSA) — `cat`, `cat -n`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 19a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (reading, joining, and creating files with `cat`), RHCE EX294 (the `assemble` analog), SRE/DevOps (log stitching, fragment assembly)  
**Prerequisite:** [Lab 18c](../lab-18c-locate-command-docs-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cat` | _Task 1 · Step 1_ |
| A2 | `>` / `>>` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `cat file1 file2` (concatenate) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `cat -n` / `cat -b` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `cat <<EOF` (heredoc) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `cat -A` (show non-printing) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Use `cat` for what its name means — *concatenate*. You will join multiple files into one, number lines with `-n`/`-b`, build a file inline with a heredoc, and reveal hidden characters (tabs, CRLF, trailing spaces) with `-A`. By the end you can stitch fragments into a config and spot the invisible whitespace bugs that break parsers.

---

## 🧠 Concept

`cat FILE...` prints each file in order to stdout; with one file it just dumps it, with several it concatenates them — the original purpose. Redirect the result with `>`/`>>` to build a combined file. `-n` numbers every line, `-b` numbers only non-blank lines. A **heredoc** (`cat <<EOF ... EOF`) feeds inline text into `cat` (or any command). `-A` makes the invisible visible: `$` marks line ends, `^I` marks tabs, `M-` marks high-bit bytes — essential for debugging "looks fine but won't parse" files.

```
cat a b c > all.txt        → a then b then c, concatenated
cat -n all.txt             → 1  line, 2  line, ...
cat <<EOF > new.txt        → write inline text into a file
  ...
EOF
cat -A file                → see tabs (^I), line ends ($), CRLF (^M$)
```

> **Why this matters:** Config assembly and log stitching are everyday `cat` jobs, and a stray tab or Windows CRLF is the classic invisible cause of a service refusing to start. `cat -A` is how you find it.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `cat` | Print/concatenate files | order of arguments = order of output |
| `cat -n` / `-b` | Number all / non-blank lines | `-b` skips blank-line numbers |
| `cat <<EOF` | Heredoc inline text | quote `'EOF'` to disable expansion |
| `cat -A` | Show non-printing chars | `^I` tab, `$` EOL, `^M` CR |
| `>` / `>>` | Save / append result | one `>` truncates |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a few fragment files to concatenate.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-19
mkdir -p "$LAB_ROOT/parts"
cd "$LAB_ROOT"
printf 'header line\n' > parts/01-header.txt
printf 'body line\n'   > parts/02-body.txt
printf 'footer line\n' > parts/03-footer.txt
ls parts
echo "exit was: $?"
```

**Expected output:**

```
01-header.txt
02-body.txt
03-footer.txt
exit was: 0
```

---

## TASK 1 of 2 — Concatenate and number

**In plain English:** We join the fragments into one file in order, then number the result.

---

### Step 1 of 2 — Concatenate fragments with `cat`

**In plain English:** We print the three parts in order and save them as a single combined file.

```bash
cd "$LAB_ROOT"
cat parts/01-header.txt parts/02-body.txt parts/03-footer.txt
cat parts/*.txt > combined.txt
cat combined.txt
echo "exit was: $?"
```

**Expected output:**

```
header line
body line
footer line
header line
body line
footer line
exit was: 0
```

**Line-by-line breakdown:**

- `cat parts/01... parts/02... parts/03...` → Print the three files in argument order — this is concatenation, `cat`'s namesake.
- `cat parts/*.txt > combined.txt` → The glob expands in sorted order (`01`,`02`,`03`), so the saved file is correctly ordered.

**New words in this step:**

- **concatenate** — join files end-to-end in the order given.

---

### Step 2 of 2 — Number lines with `cat -n` and `-b`

**In plain English:** We number every line, then number only the non-blank ones.

```bash
cd "$LAB_ROOT"
printf 'one\n\nthree\n' > spaced.txt
cat -n spaced.txt
cat -b spaced.txt
echo "exit was: $?"
```

**Expected output:**

```
     1	one
     2	
     3	three
     1	one

     2	three
exit was: 0
```

**Line-by-line breakdown:**

- `cat -n spaced.txt` → Number *every* line, including the blank one (line 2).
- `cat -b spaced.txt` → Number only *non-blank* lines, so the blank line is left unnumbered.

**New words in this step:**

- **`cat -n` / `-b`** — number all lines / number only non-blank lines.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `cat a b` | concatenate in order | argument order = output order |
| `cat *.txt` | glob order | sorted, so prefix files `01-`, `02-` |
| `cat -n` vs `-b` | all vs non-blank | `-b` skips blank-line numbers |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong concatenation order | Glob sorted unexpectedly | Prefix filenames with `01-`, `02-` |
| Numbers on blank lines | Used `-n` | Use `-b` to skip blanks |

---

## TASK 2 of 2 — Build inline and reveal hidden chars

**In plain English:** We create a file with a heredoc, then expose invisible characters with `-A`.

---

### Step 1 of 2 — Create a file with a heredoc

**In plain English:** We write multi-line content directly into a file using `cat <<EOF`.

```bash
cd "$LAB_ROOT"
cat <<'EOF' > motd.txt
Welcome to the lab
Do not feed the daemons
EOF
cat motd.txt
echo "exit was: $?"
```

**Expected output:**

```
Welcome to the lab
Do not feed the daemons
exit was: 0
```

**Line-by-line breakdown:**

- `cat <<'EOF' > motd.txt` → Start a heredoc; everything until the `EOF` marker is fed to `cat` and redirected into the file.
- quoting `'EOF'` → Disables variable/`$` expansion so the text is written literally.

**New words in this step:**

- **heredoc** — inline text block fed to a command, terminated by a marker word like `EOF`.

---

### Step 2 of 2 — Reveal hidden characters with `cat -A`

**In plain English:** We make a file with a tab and a Windows line ending, then show them with `-A`.

```bash
cd "$LAB_ROOT"
printf 'tab\there\r\nplain\n' > hidden.txt
cat -A hidden.txt
echo "exit was: $?"
```

**Expected output:**

```
tab^Ihere^M$
plain$
exit was: 0
```

**Line-by-line breakdown:**

- `printf 'tab\there\r\nplain\n' > hidden.txt` → Write a line containing a tab (`\t`) and a CRLF (`\r\n`).
- `cat -A hidden.txt` → `^I` reveals the tab, `^M` reveals the carriage return, `$` marks each line end — the invisible made visible.

**New words in this step:**

- **`cat -A`** — display non-printing characters: `^I` tab, `$` end-of-line, `^M` carriage return.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `cat <<EOF` | inline file creation | quote `'EOF'` to stop expansion |
| `cat -A` | show hidden chars | `^M$` reveals Windows CRLF |
| tabs vs spaces | `^I` marks tabs | YAML/Makefiles break on the wrong one |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Heredoc expanded variables | Unquoted `EOF` | Quote it: `<<'EOF'` |
| File won't parse | Hidden CRLF/tabs | Find with `cat -A`, fix with `sed`/`dos2unix` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Concatenate fragments with `cat`
- [ ] Task 1 · Step 2 — Number lines with `cat -n` and `-b`
- [ ] Task 2 · Step 1 — Create a file with a heredoc
- [ ] Task 2 · Step 2 — Reveal hidden characters with `cat -A`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-19
```

**Expected output:**

```
✅ Removed /tmp/lab-19 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Relying on glob order | Fragments concatenated wrong | Zero-pad prefixes (`01-`) |
| Unquoted heredoc marker | Variables expanded | Use `<<'EOF'` |
| Ignoring hidden chars | Config won't parse | Inspect with `cat -A` |

---

## 📌 Exam Strategy

Use `cat` to read, join, and build files; reach for `-n` to reference line numbers and `-A` to hunt invisible whitespace that breaks configs. Heredocs are the fastest way to drop multi-line content into a file on the command line.

- Zero-pad fragment names so `cat *` concatenates in order.
- `cat -A` is your first move when "the config looks right but fails."
- Quote `'EOF'` unless you specifically want expansion.

---

## 🔗 Related Labs

- [Lab 19b — Concatenating Files (Ansible)](../lab-19b-cat-concatenate-files-ansible/) — `ansible.builtin.assemble` for fragment concatenation
- [Lab 19c — Concatenating Files (Verify)](../lab-19c-cat-concatenate-files-verify/) — prove order and content integrity
- [Lab 20a — Scrolling Through Large Files (RHCSA)](../lab-20a-less-more-scrolling-rhcsa/) — reading big files `cat` would flood

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
