# Lab 17a: Find and Save Config Files (RHCSA) — `find`, `2>/dev/null`

**Series:** linux-ops-mastery — Text Processing & Filters · **Lab 17a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (locating files by name/type/owner and saving the list), RHCE EX294 (the `find` module behind it), SRE/DevOps (config inventory, audits)  
**Prerequisite:** [Lab 16c](../lab-16c-grep-search-save-output-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `find` | _Task 1 · Step 1_ |
| A2 | `>` (save list) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `find -type f` / `-name` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `2>/dev/null` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `find -user` / `-perm` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `find -name '*.conf' -o -name` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Build a clean inventory of config files. You will locate files by name and type with `find`, silence permission-denied noise with `2>/dev/null`, save the list with `>`, then filter by owner and combine name patterns with `-o`. The result is the exact "find all the `.conf` files owned by X and save the paths" task the exam loves.

---

## 🧠 Concept

`find PATH PREDICATE...` walks a tree testing each entry. `-type f` keeps regular files, `-name '*.conf'` matches by glob (quote it so the shell does not expand it first), `-user NAME` filters by owner, `-perm` by mode. When searching system trees as a non-root user you hit "Permission denied" lines on stderr — `2>/dev/null` discards those so your saved list stays clean (this is the one place redirecting stderr is routine). Combine predicates with `-o` (OR) and parentheses for complex filters.

```
find /etc -type f -name '*.conf'        → every .conf file
find / -user alice 2>/dev/null          → alice's files, no noise
find /etc \( -name '*.conf' -o -name '*.cfg' \)  → either extension
find . -type f > list.txt               → save the inventory
```

> **Why this matters:** Auditing "which config files exist / who owns them" is core sysadmin work. `2>/dev/null` is what keeps the saved evidence readable instead of buried in permission errors.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `find` | Walk a tree and test entries | predicates AND by default |
| `-type f` / `-name` | Match regular files / by glob | quote the glob: `-name '*.conf'` |
| `-user` / `-perm` | Filter by owner / mode | `-perm -640` = at least these bits |
| `2>/dev/null` | Discard permission-denied noise | stderr only; stdout still saved |
| `-o` + `\( \)` | OR and grouping | escape parens in the shell |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox tree of mixed config files with different owners and extensions.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-17
mkdir -p "$LAB_ROOT/etc/app" "$LAB_ROOT/etc/svc"
cd "$LAB_ROOT"
echo a > etc/app/app.conf
echo b > etc/svc/svc.conf
echo c > etc/svc/notes.txt
echo d > etc/app/legacy.cfg
ls -R "$LAB_ROOT/etc"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-17/etc:
app
svc

/tmp/lab-17/etc/app:
app.conf
legacy.cfg
...
exit was: 0
```

---

## TASK 1 of 2 — Find by name and type, save the list

**In plain English:** We find regular `.conf` files and save the paths, silencing any permission noise.

---

### Step 1 of 2 — Find `.conf` regular files

**In plain English:** We list every regular file ending in `.conf` under the sandbox.

```bash
cd "$LAB_ROOT"
find etc -type f -name '*.conf'
echo "exit was: $?"
```

**Expected output:**

```
etc/app/app.conf
etc/svc/svc.conf
exit was: 0
```

**Line-by-line breakdown:**

- `find etc -type f -name '*.conf'` → Walk `etc`, keep only regular files (`-type f`) whose name matches `*.conf`; the quotes stop the shell from globbing.

**New words in this step:**

- **predicate** — a `find` test like `-type` or `-name` that an entry must satisfy.

---

### Step 2 of 2 — Silence noise with `2>/dev/null` and save

**In plain English:** We search a broader tree, throw away permission errors, and save the clean list to a file.

```bash
cd "$LAB_ROOT"
find / -type f -name 'svc.conf' 2>/dev/null | tee found.txt
cat found.txt
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-17/etc/svc/svc.conf
/tmp/lab-17/etc/svc/svc.conf
exit was: 0
```

**Line-by-line breakdown:**

- `find / -type f -name 'svc.conf' 2>/dev/null` → Search from `/`; `2>/dev/null` discards the "Permission denied" lines on stderr so only real hits remain.
- `| tee found.txt` → Save the clean list while showing it.

**New words in this step:**

- **`2>/dev/null`** — redirect stderr (file descriptor 2) to the bit bucket, discarding error noise.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `-type f` | regular files only | omitting it includes dirs/links |
| quoted `-name` | glob match | unquoted globs expand in the shell |
| `2>/dev/null` | drop stderr | hides real errors too — use deliberately |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Glob expanded unexpectedly | `-name *.conf` unquoted | Quote it: `-name '*.conf'` |
| List polluted with errors | stderr not redirected | Append `2>/dev/null` |

---

## TASK 2 of 2 — Filter by owner and combine patterns

**In plain English:** We narrow the search by owner, then match multiple extensions with `-o`.

---

### Step 1 of 2 — Filter by owner with `-user`

**In plain English:** We list regular files owned by root under the tree.

```bash
cd "$LAB_ROOT"
find etc -type f -user root
echo "exit was: $?"
```

**Expected output:**

```
etc/app/app.conf
etc/svc/svc.conf
etc/svc/notes.txt
etc/app/legacy.cfg
exit was: 0
```

**Line-by-line breakdown:**

- `find etc -type f -user root` → Keep regular files owned by `root`; predicates AND together, so both `-type f` and `-user root` must hold.

**New words in this step:**

- **`find -user`** — filter entries by owning user (by name or UID).

---

### Step 2 of 2 — Combine extensions with `-o`

**In plain English:** We match files ending in either `.conf` or `.cfg` and save the combined list.

```bash
cd "$LAB_ROOT"
find etc -type f \( -name '*.conf' -o -name '*.cfg' \) > configs.txt
cat configs.txt
echo "exit was: $?"
```

**Expected output:**

```
etc/app/app.conf
etc/svc/svc.conf
etc/app/legacy.cfg
exit was: 0
```

**Line-by-line breakdown:**

- `find etc -type f \( -name '*.conf' -o -name '*.cfg' \)` → Group the OR with escaped parentheses so `-type f` applies to both; matches either extension.
- `> configs.txt` → Save the combined inventory.

**New words in this step:**

- **`-o`** — the OR operator in `find`; group with `\( \)` to control precedence.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `-user` | owner filter | UID vs name both accepted |
| `-o` + `\( \)` | OR with grouping | unescaped parens are shell syntax |
| AND default | predicates combine with AND | order matters for `-o` precedence |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `-o` matches too much | Missing grouping | Wrap in `\( ... \)` |
| `paren` syntax error | Unescaped parentheses | Escape: `\(` `\)` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Find `.conf` regular files
- [ ] Task 1 · Step 2 — Silence noise with `2>/dev/null` and save
- [ ] Task 2 · Step 1 — Filter by owner with `-user`
- [ ] Task 2 · Step 2 — Combine extensions with `-o`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-17
```

**Expected output:**

```
✅ Removed /tmp/lab-17 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Unquoted globs | Shell expands before find | Quote `-name` patterns |
| `2>/dev/null` hiding real errors | Missed a genuine problem | Use it only to drop permission noise |
| Forgetting `-type f` | Directories in the list | Add `-type f` |

---

## 📌 Exam Strategy

"Find all files matching X and save the list to /path" is a stock task. Build it predicate by predicate: `-type f`, `-name`, `-user`, grouping with `\( -o \)`, and `2>/dev/null` to keep the saved list clean. Always quote glob patterns.

- Quote every `-name` glob to avoid shell expansion.
- `2>/dev/null` is the routine way to keep `find` output readable.
- Group OR conditions with escaped parentheses.

---

## 🔗 Related Labs

- [Lab 17b — Find and Save Config Files (Ansible)](../lab-17b-find-save-config-files-ansible/) — `ansible.builtin.find` with patterns/owner
- [Lab 17c — Find and Save Config Files (Verify)](../lab-17c-find-save-config-files-verify/) — prove the saved list is complete and correct
- [Lab 14a — Searching with find (RHCSA)](../lab-14a-searching-with-find-rhcsa/) — more `find` predicates and actions

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
