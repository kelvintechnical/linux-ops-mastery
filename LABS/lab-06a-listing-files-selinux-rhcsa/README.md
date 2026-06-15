# Lab 06a: Listing Files and SELinux (RHCSA) — `ls -lZ`, `restorecon`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 06a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (reading and fixing SELinux contexts — a guaranteed objective), RHCE EX294 (the `sefcontext` module behind this), SRE/DevOps (debugging "permission denied" that is really SELinux)  
**Prerequisite:** [Lab 05c](../lab-05c-directory-navigation-verify/) completed; SELinux in `Enforcing` or `Permissive`  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ls -l` | _Task 1 · Step 1_ |
| A2 | `ls -d` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ls -lZ` / `ls -dZ` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `semanage fcontext -a` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `restorecon -Rv` | Task 2 · Step 2 | _Task 2 · Step 2_ |
| N4 | `matchpathcon` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Read every column of a long listing, then add the one column that decides whether a service can open a file at all: the SELinux context shown by `-Z`. You will list files and directories with `ls -lZ`/`ls -dZ`, define a persistent file-context rule with `semanage fcontext`, apply it with `restorecon`, and confirm the result matches policy with `matchpathcon` — the full "set, apply, verify" loop the exam expects.

---

## 🧠 Concept

Every file carries an SELinux **context**: `user:role:type:level`, and the **type** is what the policy uses to allow or deny access (e.g. `httpd_sys_content_t` for web content). `ls -Z` reveals it. Changing a label has two layers: `chcon` changes it *now but not persistently*, while `semanage fcontext -a` records a **rule** in policy and `restorecon` then relabels the file to match that rule — surviving relabels and reboots. `matchpathcon` answers "what context *should* this path have?" so you can prove the file now matches the rule.

```
ls -lZ file        → unconfined_u:object_r:tmp_t:s0  file
semanage fcontext -a -t httpd_sys_content_t '/path(/.*)?'   (record the rule)
restorecon -Rv /path                                        (apply the rule)
matchpathcon /path/file → /path/file  httpd_sys_content_t   (policy says so)
```

> **Why this matters:** "It works with SELinux off" is not a fix. The RHCSA tests whether you can make a service-readable file *persistently* correct with `semanage` + `restorecon`, not the throwaway `chcon`.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ls -lZ` | Long listing including SELinux context | `-Z` adds the context column |
| `ls -dZ` | Show a directory's own context, not its contents | `-d` stops recursion |
| `semanage fcontext -a` | Add a persistent file-context rule | `-t TYPE`; `-l` lists rules; `-d` deletes |
| `restorecon -Rv` | Relabel files to match policy | `-R` recursive, `-v` verbose |
| `matchpathcon` | Show the context policy expects for a path | compares actual vs expected |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build a sandbox with a content directory and a file inside it so we have something to label and relabel.

> Run this block **once** before Task 1. It defines a single sandbox root
> (`LAB_ROOT`) that every file in this lab lives under, so the Teardown
> section can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-06
mkdir -p "$LAB_ROOT/webroot"
echo "<h1>lab 06</h1>" > "$LAB_ROOT/webroot/index.html"
ls -ldZ "$LAB_ROOT/webroot"
echo "exit was: $?"
```

**Expected output:**

```
drwxr-xr-x. 2 root root unconfined_u:object_r:tmp_t:s0 24 Jun 15 18:25 /tmp/lab-06/webroot
exit was: 0
```

---

## TASK 1 of 2 — Read contexts with `ls -Z`

**In plain English:** We read the SELinux context column for both files and the directory itself, learning where the label lives.

---

### Step 1 of 2 — List files with `ls -lZ`

**In plain English:** We show the long listing plus the SELinux context for the files inside our content directory.

```bash
cd "$LAB_ROOT/webroot"
ls -lZ
echo "exit was: $?"
```

**Expected output:**

```
-rw-r--r--. 1 root root unconfined_u:object_r:tmp_t:s0 16 Jun 15 18:25 index.html
exit was: 0
```

**Line-by-line breakdown:**

- `cd "$LAB_ROOT/webroot"` → Enter the content directory.
- `ls -lZ` → Long listing with the SELinux context column; the `tmp_t` type shows files under `/tmp` inherit the temp type.

**New words in this step:**

- **SELinux context** — the `user:role:type:level` label every file carries; the **type** drives access decisions.
- **`-Z`** — the `ls` flag that adds the SELinux context to the output.

---

### Step 2 of 2 — Show the directory's own context with `ls -dZ`

**In plain English:** We print the directory's own label instead of its contents, so we can target the folder for relabeling.

```bash
ls -dZ "$LAB_ROOT/webroot"
echo "exit was: $?"
```

**Expected output:**

```
unconfined_u:object_r:tmp_t:s0 /tmp/lab-06/webroot
exit was: 0
```

**Line-by-line breakdown:**

- `ls -dZ "$LAB_ROOT/webroot"` → `-d` shows the directory entry itself (its label), not the files inside; `-Z` adds the context.

**New words in this step:**

- **`-d`** — list a directory's own entry rather than descending into it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ls -Z` | shows the context column | type, not user/role, drives access |
| `ls -dZ` | directory's own label | without `-d`, you see contents' labels |
| `tmp_t` | the temp file type | services often cannot read `tmp_t` content |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| No context column | SELinux disabled | Check `getenforce`; enable Permissive/Enforcing |
| `-Z` shows `?` | Filesystem without xattrs | Use a normal ext4/xfs path |

---

## TASK 2 of 2 — Set, apply, and verify a context rule

**In plain English:** We record a persistent file-context rule, apply it with `restorecon`, and confirm the file now matches policy with `matchpathcon`.

---

### Step 1 of 2 — Record the rule with `semanage fcontext -a`

**In plain English:** We add a policy rule that says everything under our webroot should be web content, without changing any file yet.

```bash
sudo semanage fcontext -a -t httpd_sys_content_t "${LAB_ROOT}/webroot(/.*)?"
sudo semanage fcontext -l | grep "${LAB_ROOT}/webroot"
echo "exit was: $?"
```

**Expected output:**

```
/tmp/lab-06/webroot(/.*)?    all files    system_u:object_r:httpd_sys_content_t:s0
exit was: 0
```

**Line-by-line breakdown:**

- `semanage fcontext -a -t httpd_sys_content_t "...(/.*)?"` → Add a rule mapping the path (and everything under it, via the `(/.*)?` regex) to the web-content type. This records policy; files are not touched yet.
- `semanage fcontext -l | grep ...` → List local rules and confirm ours is present.

**New words in this step:**

- **`semanage fcontext`** — manages persistent file-context rules in the SELinux policy database.
- **`(/.*)?`** — the standard regex suffix meaning "this path and everything beneath it."

---

### Step 2 of 2 — Apply with `restorecon` and verify with `matchpathcon`

**In plain English:** We relabel the directory to match the new rule, then prove both that the file carries the new type and that policy expects exactly that.

```bash
sudo restorecon -Rv "${LAB_ROOT}/webroot"
ls -lZ "${LAB_ROOT}/webroot/index.html"
matchpathcon "${LAB_ROOT}/webroot/index.html"
echo "exit was: $?"
```

**Expected output:**

```
Relabeled /tmp/lab-06/webroot from unconfined_u:object_r:tmp_t:s0 to system_u:object_r:httpd_sys_content_t:s0
Relabeled /tmp/lab-06/webroot/index.html from ... to system_u:object_r:httpd_sys_content_t:s0
-rw-r--r--. 1 root root system_u:object_r:httpd_sys_content_t:s0 16 Jun 15 18:26 index.html
/tmp/lab-06/webroot/index.html	system_u:object_r:httpd_sys_content_t:s0
exit was: 0
```

**Line-by-line breakdown:**

- `restorecon -Rv "...webroot"` → Apply the policy rule by relabeling recursively (`-R`) and verbosely (`-v`); each relabel is printed.
- `ls -lZ ...index.html` → Confirm the file now carries `httpd_sys_content_t`.
- `matchpathcon ...index.html` → Print the context policy expects; it matches the file, proving the rule and the label agree.

**New words in this step:**

- **`restorecon`** — relabels files to whatever the current policy rules say they should be.
- **`matchpathcon`** — reports the expected context for a path, the "what should it be?" oracle.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `semanage fcontext -a` | persistent rule | `chcon` alone is wiped by relabel/reboot |
| `restorecon -R` | apply policy to files | without the rule, it reverts to default type |
| `matchpathcon` | expected context | mismatch means rule not applied yet |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `restorecon` changes nothing | No rule recorded for the path | Add it with `semanage fcontext -a` first |
| Label reverts after reboot | Used `chcon`, not `semanage` | Use the `semanage` + `restorecon` pair |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — List files with `ls -lZ`
- [ ] Task 1 · Step 2 — Show the directory's own context with `ls -dZ`
- [ ] Task 2 · Step 1 — Record the rule with `semanage fcontext -a`
- [ ] Task 2 · Step 2 — Apply with `restorecon` and verify with `matchpathcon`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-06
```

**This lab created SYSTEM state (an SELinux fcontext rule) — reverse it explicitly** (`rm` will not):

```bash
sudo semanage fcontext -d "${LAB_ROOT}/webroot(/.*)?"   # remove the policy rule
```

**Expected output:**

```
✅ Removed /tmp/lab-06 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `chcon` for a "permanent" fix | Label reverts on relabel/reboot | Use `semanage fcontext` + `restorecon` |
| Forgetting `(/.*)?` in the rule | Files inside stay unlabeled | Add the regex suffix to cover contents |
| Leaving the fcontext rule behind | Policy DB clutter | Delete with `semanage fcontext -d` in teardown |

---

## 📌 Exam Strategy

SELinux context tasks are near-guaranteed on the RHCSA. The pattern never changes: `semanage fcontext -a -t TYPE 'PATH(/.*)?'` then `restorecon -Rv PATH`, then prove it with `ls -Z`. Never settle for `chcon` — graders relabel and your change vanishes.

- Memorize the `(/.*)?` regex — it is in almost every fcontext rule.
- `restorecon -Rv` shows you exactly what it relabeled; read the output.
- `matchpathcon` confirms expected vs actual before you move on.

---

## 🔗 Related Labs

- [Lab 06b — Listing Files and SELinux (Ansible)](../lab-06b-listing-files-selinux-ansible/) — the `community.general.sefcontext` module version
- [Lab 06c — Listing Files and SELinux (Verify)](../lab-06c-listing-files-selinux-verify/) — prove the label matches policy with hard evidence
- [Lab 05a — Directory Navigation (RHCSA)](../lab-05a-directory-navigation-rhcsa/) — the listing skills this builds on

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
