# Lab 05a: Directory Navigation (RHCSA) — `pwd`, `cd`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 05a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (every "go to /path and run X" task), RHCE EX294 (the `chdir:` reflex behind shell tasks), SRE/DevOps (script-relative paths and safe context switching)  
**Prerequisite:** [Lab 04c](../lab-04c-capture-both-output-error-verify/) completed  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `cd` | _Task 1 · Step 1_ |
| A2 | `pwd` | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `pwd -L` / `pwd -P` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `cd -` and `$OLDPWD` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `cd ~` (HOME expansion) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `cd ..` (parent traversal) | Task 1 · Step 1 | _Task 1 · Step 1_ |

---

## 🎯 Objective

Move through the filesystem with intent: print where you are, jump to a parent, home, or a previous directory, and — the trap that catches everyone — tell the difference between the *symlinked* path you typed and the *real* path you are physically standing in. By the end you can navigate fluently and prove which path the shell thinks is current using `pwd -L` versus `pwd -P`.

---

## 🧠 Concept

The shell keeps a "current working directory" (CWD) and a single memory slot, `$OLDPWD`, holding the last place you were. `cd` changes the CWD; `cd -` swaps to `$OLDPWD` (a toggle); `cd ~` goes home; `cd ..` climbs one level. The subtlety is symlinks: if you `cd` into a symlinked directory, the shell *remembers the symlink path* (logical view) but the files actually live at the real path (physical view). `pwd -L` prints the logical path; `pwd -P` resolves every symlink to the real one. Confusing the two breaks scripts that compute paths.

```
cd /usr/lib   (symlink? no)          pwd -L → /usr/lib      pwd -P → /usr/lib
cd $LAB_ROOT/link → real dir         pwd -L → .../link      pwd -P → .../real
cd -          (toggle)               returns to $OLDPWD
```

> **Why this matters:** RHCSA tasks say "in /etc/…" and a wrong CWD silently sends your output to the wrong place. Knowing `pwd -P` lets you prove where you really are before you write a file.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `pwd` | Print the current working directory | defaults to `-L` (logical) |
| `pwd -L` | Print the logical path (keeps symlinks) | shows the path you typed |
| `pwd -P` | Print the physical path (resolves symlinks) | shows where files truly live |
| `cd -` | Switch to the previous directory (`$OLDPWD`) | prints the directory it jumps to |
| `cd ~` | Go to `$HOME` | under `sudo -i`, `~` is root's home, not yours |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a real subdirectory and a symlink that points at it, so we can demonstrate the logical-vs-physical path difference safely.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-05
mkdir -p "$LAB_ROOT/real_dir/sub"
ln -s "$LAB_ROOT/real_dir" "$LAB_ROOT/link_dir"
ls -l "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 3 root root 17 Jun 15 18:10 real_dir
lrwxrwxrwx. 1 root root 18 Jun 15 18:10 link_dir -> /tmp/lab-05/real_dir
exit was: 0
```

---

## TASK 1 of 2 — Move and locate with `cd` and `pwd`

**In plain English:** We practice the everyday jumps — into a subdir, up to the parent, home — then expose the symlink trap with `pwd -L` versus `pwd -P`.

---

### Step 1 of 2 — Jump in, up, and home

**In plain English:** We change into a subdirectory, climb back to its parent, and bounce home, printing the working directory at each stop.

```bash
cd "$LAB_ROOT/real_dir/sub"
pwd
cd ..
pwd
cd ~
pwd
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-05/real_dir/sub
/tmp/lab-05/real_dir
/root
exit was: 0
```

**Line-by-line breakdown:**

- `cd "$LAB_ROOT/real_dir/sub"` → Change into the deepest folder; `pwd` confirms the CWD.
- `cd ..` → Climb one level to the parent; `..` always means "the directory above this one."
- `cd ~` → Jump to `$HOME` (`/root` when you are root); `~` expands to your home directory.

**New words in this step:**

- **CWD (current working directory)** — the folder the shell treats as "here" for relative paths.
- **`~` (tilde)** — shorthand for the current user's home directory.

---

### Step 2 of 2 — Expose the symlink trap with `pwd -L` vs `pwd -P`

**In plain English:** We `cd` into the symlink, then print both the logical path we typed and the physical path the files really live at.

```bash
cd "$LAB_ROOT/link_dir"
pwd -L
pwd -P
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-05/link_dir
/tmp/lab-05/real_dir
exit was: 0
```

**Line-by-line breakdown:**

- `cd "$LAB_ROOT/link_dir"` → Enter the symlinked directory; the shell remembers the symlink path.
- `pwd -L` → Print the *logical* path — the symlink name you typed (`link_dir`).
- `pwd -P` → Print the *physical* path — symlinks resolved to where files truly are (`real_dir`).

**New words in this step:**

- **logical path** — the path including symlink names, as the shell remembers it.
- **physical path** — the canonical path with all symlinks resolved.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `cd ..` | climb to parent | from `/` it stays at `/`, not an error |
| `cd ~` | go to `$HOME` | under `sudo -i`, `~` is root's home |
| `pwd -L` vs `-P` | logical vs physical | a script using `-L` can write to the wrong real dir |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `cd ~` lands in `/root` unexpectedly | You are root via `sudo -i` | Use the explicit path, not `~` |
| `pwd` shows the symlink, files elsewhere | You `cd`'d via a symlink | Use `pwd -P` to see the real location |

---

## TASK 2 of 2 — Toggle directories with `cd -` and `$OLDPWD`

**In plain English:** We learn the fast two-place toggle every admin uses, then prove `$OLDPWD` holds the previous directory.

---

### Step 1 of 2 — Toggle with `cd -`

**In plain English:** We bounce between two directories using `cd -`, which jumps back to wherever we just were.

```bash
cd "$LAB_ROOT/real_dir"
cd /usr
cd -
pwd
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-05/real_dir
/tmp/lab-05/real_dir
exit was: 0
```

**Line-by-line breakdown:**

- `cd "$LAB_ROOT/real_dir"` then `cd /usr` → Visit two directories so the shell stores the first in `$OLDPWD`.
- `cd -` → Toggle back to `$OLDPWD`; it also prints the directory it lands in.
- `pwd` → Confirm we are back in `real_dir`.

**New words in this step:**

- **`cd -`** — jump to the previous directory; running it twice returns you where you started.

---

### Step 2 of 2 — Read the `$OLDPWD` memory slot directly

**In plain English:** We inspect the `$OLDPWD` variable to prove the shell tracks the previous directory in plain text.

```bash
cd "$LAB_ROOT/real_dir/sub"
cd "$LAB_ROOT"
echo "OLDPWD is: $OLDPWD"
echo "exit was: $?"
```

**Expected output:**

```
OLDPWD is: /tmp/lab-05/real_dir/sub
exit was: 0
```

**Line-by-line breakdown:**

- `cd ".../sub"` then `cd "$LAB_ROOT"` → Move twice so `$OLDPWD` is set to the `sub` directory.
- `echo "OLDPWD is: $OLDPWD"` → Print the variable; it holds exactly the previous CWD that `cd -` would jump to.

**New words in this step:**

- **`$OLDPWD`** — the environment variable holding the previous working directory; `cd -` is just a jump to it.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `cd -` | toggle to `$OLDPWD` | only remembers ONE previous dir, not a stack |
| `$OLDPWD` | stores the last CWD | a fresh shell has it unset |
| `cd` (no arg) | goes to `$HOME` | easy to confuse with `cd -` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `cd -` errors `OLDPWD not set` | First `cd` in a new shell | `cd` somewhere once to populate `$OLDPWD` |
| `cd -` goes somewhere unexpected | You changed dirs in between | Remember it tracks only the single last dir |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Jump in, up, and home
- [ ] Task 1 · Step 2 — Expose the symlink trap with `pwd -L` vs `pwd -P`
- [ ] Task 2 · Step 1 — Toggle with `cd -`
- [ ] Task 2 · Step 2 — Read the `$OLDPWD` memory slot directly
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-05
```

**Expected output:**

```
✅ Removed /tmp/lab-05 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting `pwd` inside a symlink | Files land in the real dir, not where you expect | Use `pwd -P` to confirm |
| Assuming `cd -` keeps a history | It only remembers one previous dir | Use `pushd`/`popd` for a stack |
| Running teardown from inside `$LAB_ROOT` | "Device or resource busy" | `cd /tmp` first, then teardown |

---

## 📌 Exam Strategy

Navigation is invisible until it bites: a wrong CWD sends your redirected output into the wrong file. Before any "create a file in /path" task, `cd` there and `pwd -P` to confirm you are physically in the right place. Use `cd -` to bounce between a config dir and a log dir without retyping long paths.

- `pwd -P` is your "am I really here?" check before writing files.
- `cd -` saves seconds on every back-and-forth — build the reflex.
- Remember `~` follows the *effective* user, so it changes under `sudo -i`.

---

## 🔗 Related Labs

- [Lab 05b — Directory Navigation (Ansible)](../lab-05b-directory-navigation-ansible/) — why there is no `cd` module and how `chdir:` replaces it
- [Lab 05c — Directory Navigation (Verify)](../lab-05c-directory-navigation-verify/) — prove logical vs physical paths with hard evidence
- [Lab 09a — Hard and Soft Links (RHCSA)](../lab-09a-hard-and-soft-links-rhcsa/) — the symlinks behind the `pwd -L`/`-P` trap

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
