# Lab 08c: Copying Files and Directories (Verify) — `diff -r`, `sha256sum`, `stat`

**Series:** linux-ops-mastery — Essential Tools & File Operations · **Lab 08c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving a copy is faithful), SRE (backup integrity checks), DevOps (deployment verification)  
**Prerequisite:** [Lab 08a](../lab-08a-copying-files-rhcsa/) and [Lab 08b](../lab-08b-copying-files-ansible/) completed  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `sha256sum` | _Task 1 · Step 1_ |
| A2 | `stat -c` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `diff -r` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N2 | `sha256sum -c` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `find ... -printf '%m'` (mode audit) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `cmp` | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Take the auditor's seat: prove a copy is faithful in both content and metadata. You will fingerprint files with `sha256sum` and re-check with `sha256sum -c`, compare whole trees with `diff -r`, and assert mode/context match between source and copy. The verdict is binary — identical or not — exactly what a grader needs to award the point.

---

## 🧠 Concept

A faithful copy is verified on two layers. **Content**: `sha256sum` produces a fingerprint, and `diff -r` walks two trees reporting any file that differs or is missing; identical content yields a clean exit and no output. **Metadata**: `stat -c '%a %C'` (or `find -printf '%m'`) proves mode and SELinux context carried over. Content equality without metadata equality is a *partial* copy — both must pass for "faithful."

```
sha256sum src copy           → same hash = identical bytes
diff -r srcdir copydir       → (no output) = trees identical
stat -c '%a %C' src copy     → same mode + context = metadata preserved
cmp -s a b                   → silent exit 0 = byte-identical
```

> **Why this matters:** A copy that matches content but lost its SELinux context still breaks the service. Auditing both layers is the only way to certify a copy as truly faithful.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `sha256sum` | Content fingerprint | pipe to `awk '{print $1}'` for the bare hash |
| `sha256sum -c` | Verify files against a checksum list | reports `OK`/`FAILED` per file |
| `diff -r` | Recursively compare two trees | no output = identical |
| `stat -c '%a %C'` | Compare mode + context | source vs copy |
| `cmp -s` | Silent byte comparison | exit 0 = identical |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Rebuild a source tree and a faithful `cp -a` copy so there is a matched pair to audit.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-08
mkdir -p "$LAB_ROOT/src/conf"
cd "$LAB_ROOT"
echo "key=value" > src/conf/app.conf
chmod 640 src/conf/app.conf
cp -a src copy
ls -lR "$LAB_ROOT" | head -n 12
echo "exit was: $?"
```

**Expected output:**

```
-rw-r-----. 1 root root 10 ... app.conf
exit was: 0
```

---

## TASK 1 of 2 — Prove content is identical

**In plain English:** We fingerprint the files and compare the whole tree to prove the bytes match.

---

### Step 1 of 2 — Fingerprint and verify with `sha256sum`

**In plain English:** We hash the source, record it, and verify the copy against that recorded hash.

```bash
cd "$LAB_ROOT"
sha256sum src/conf/app.conf | sed 's| .*|  copy/conf/app.conf|' > expected.sha256
sha256sum -c expected.sha256
echo "exit was: $?"
```

**Expected output:**

```
copy/conf/app.conf: OK
exit was: 0
```

**Line-by-line breakdown:**

- `sha256sum src/conf/app.conf | sed ...` → Compute the source hash and rewrite the filename to the copy's path, building a checklist entry.
- `sha256sum -c expected.sha256` → Verify the copy's bytes against that hash; `OK` proves identical content.

**New words in this step:**

- **`sha256sum -c`** — verify files listed in a checksum file, printing `OK` or `FAILED`.

---

### Step 2 of 2 — Compare whole trees with `diff -r`

**In plain English:** We recursively diff the source and copy directories; no output means every file matches.

```bash
cd "$LAB_ROOT"
diff -r src copy && echo "TREES IDENTICAL (OK)" || echo "TREES DIFFER (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
TREES IDENTICAL (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `diff -r src copy` → Walk both trees comparing every file; identical content produces no output and exit 0.
- `&& echo OK || echo FAIL` → Turn the exit code into a verdict.

**New words in this step:**

- **`diff -r`** — recursively compares two directory trees file by file.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `sha256sum -c` | hash verification | filename in the list must match the target |
| `diff -r` | tree comparison | reports files present in only one side |
| clean diff | identical content | exit 1 means "differ," not an error |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `FAILED` from `-c` | Content differs | Re-copy with `cp -a` |
| `Only in ...` lines | Missing/extra files | Ensure recursive copy completed |

---

## TASK 2 of 2 — Prove metadata is faithful

**In plain English:** We compare mode and SELinux context between source and copy, then confirm byte-identity with `cmp`.

---

### Step 1 of 2 — Audit mode and context with `stat`

**In plain English:** We print mode and context for source and copy and assert they match.

```bash
cd "$LAB_ROOT"
stat -c '%a %C %n' src/conf/app.conf copy/conf/app.conf
SM=$(stat -c '%a' src/conf/app.conf); CM=$(stat -c '%a' copy/conf/app.conf)
[ "$SM" = "$CM" ] && echo "MODE MATCH (OK)" || echo "MODE DIFFERS (FAIL)"
```

**Expected output:**

```
640 unconfined_u:object_r:user_tmp_t:s0 src/conf/app.conf
640 unconfined_u:object_r:user_tmp_t:s0 copy/conf/app.conf
MODE MATCH (OK)
```

**Line-by-line breakdown:**

- `stat -c '%a %C %n' ...` → Print mode and context for both files side by side.
- `[ "$SM" = "$CM" ]` → Assert the mode strings are equal, proving permissions were preserved.

**New words in this step:**

- **`%m`/`%a` mode field** — the octal permission bits, the metadata a faithful copy keeps.

---

### Step 2 of 2 — Confirm byte-identity with `cmp`

**In plain English:** We do a final silent byte comparison; success means the files are truly identical.

```bash
cd "$LAB_ROOT"
cmp -s src/conf/app.conf copy/conf/app.conf && echo "BYTE IDENTICAL (OK)" || echo "BYTES DIFFER (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
BYTE IDENTICAL (OK)
exit was: 0
```

**Line-by-line breakdown:**

- `cmp -s src/conf/app.conf copy/conf/app.conf` → Byte-compare the two files silently; exit 0 means identical.
- `&& echo OK || echo FAIL` → Turn the comparison into a final verdict.

**New words in this step:**

- **`cmp -s`** — silent byte-for-byte comparison; exit 0 identical, non-zero differ.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `stat -c %a` | mode audit | content match alone is not "faithful" |
| `stat -c %C` | context audit | the field that keeps services working |
| `cmp -s` | byte verdict | catches differences a quick `cat` misses |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `MODE DIFFERS` | Copy without `-a`/`--preserve=mode` | Re-copy faithfully |
| Context differs | Plain `cp` reset it | Use `cp -a` or `--preserve=context` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Fingerprint and verify with `sha256sum`
- [ ] Task 1 · Step 2 — Compare whole trees with `diff -r`
- [ ] Task 2 · Step 1 — Audit mode and context with `stat`
- [ ] Task 2 · Step 2 — Confirm byte-identity with `cmp`
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This verify lab changed **no** system state.

```bash
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-08
```

**Expected output:**

```
✅ Removed /tmp/lab-08 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking content only | Lost context ships unnoticed | Audit mode and context too |
| Trusting `ls` over a hash | A subtle difference slips by | Use `sha256sum`/`cmp` |
| Ignoring `diff -r` "Only in" lines | Missing files unnoticed | Treat them as failures |

---

## 📌 Exam Strategy

Certify a copy on both axes: `diff -r`/`sha256sum` for content and `stat -c '%a %C'` for metadata. A faithful copy passes all of them. Make this two-layer audit your habit after every backup or deployment.

- A clean `diff -r` is the fastest "trees match" proof.
- Never call a copy faithful without checking mode and context.
- `sha256sum -c` scales to many files at once.

---

## 🔗 Related Labs

- [Lab 08a — Copying Files (RHCSA)](../lab-08a-copying-files-rhcsa/) — the copies this audits
- [Lab 08b — Copying Files (Ansible)](../lab-08b-copying-files-ansible/) — the playbook whose output you verify
- [Lab 10c — Moving and Renaming Files (Verify)](../lab-10c-moving-renaming-files-verify/) — the move counterpart audit

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
