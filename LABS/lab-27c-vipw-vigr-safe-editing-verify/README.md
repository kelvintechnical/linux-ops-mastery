# Lab 27c: Safely Editing System Databases (Verify) — `pwck`, `grpck`, `getent`

**Series:** linux-ops-mastery — Users & Groups · **Lab 27c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (proving account databases are consistent), SRE (identity validation), DevOps (account-state verification)  
**Prerequisite:** [Lab 27a](../lab-27a-vipw-vigr-safe-editing-rhcsa/) and [Lab 27b](../lab-27b-vipw-vigr-safe-editing-ansible/) completed · **root/sudo required**  
**Time Estimate:** 15–25 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `getent` lookups | _Task 1 · Step 1_ |
| A2 | `pwck -r` / `grpck -r` | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `getent` exit-code test | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `id` group membership proof | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `pwck`/`grpck` rc gating | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | lock-file presence (`/etc/.pwd.lock`) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Prove the account changes are present, correct, and consistent — and that the editing was safe. You will confirm the test group/user exist via `getent` exit codes, prove group membership with `id`, gate on `pwck`/`grpck` returning clean, and confirm the lock infrastructure (`/etc/.pwd.lock`) is in place. These are the checks that certify a safe database edit.

> **⚠️ System-state lab.** Assumes `labtest99`/`labtest` from Lab 27b exist. Teardown removal is repeated here so this lab is self-contained.

---

## 🧠 Concept

Verifying account edits means confirming three things. **Existence/correctness**: `getent group labtest99` and `getent passwd labtest` return the entry (exit 0) with the expected fields, and `id labtest` proves the user's group membership resolved correctly through NSS. **Consistency**: `pwck -r` and `grpck -r` scan for structural problems (wrong field counts, orphaned shadow entries, duplicate names) and return non-zero if anything is wrong — gate on rc 0. **Safety infrastructure**: the lock file `/etc/.pwd.lock` exists on a healthy system, evidence that the `vipw`/module locking mechanism is present. Together: the change is there, the database is sound, and edits are serialized.

```
getent passwd labtest; echo $?   → 0 means present
id labtest                       → gid=...(labtest99) membership proof
pwck -r; grpck -r                → rc 0 = consistent
ls -l /etc/.pwd.lock             → locking infrastructure present
```

> **Why this matters:** A user can appear in `/etc/passwd` yet be broken (missing shadow entry, bad GID). `getent`/`id`/`pwck`/`grpck` prove the account actually *works* and the database is sound — the real definition of a successful safe edit.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `getent passwd/group` | Resolve via NSS | exit 0 = found |
| `id USER` | Show UID/GID/groups | membership proof |
| `pwck -r` | Check passwd/shadow | rc 0 = clean |
| `grpck -r` | Check group/gshadow | rc 0 = clean |
| `ls /etc/.pwd.lock` | Lock infrastructure | safety check |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Ensure the test accounts exist so there is something to verify.

> Run this block **once** before Task 1. It recreates the test group/user (idempotently) if Lab 27b's Teardown already removed them, so this verify lab stands alone.

```bash
export LAB_ROOT=/tmp/lab-27
mkdir -p "$LAB_ROOT"
getent group labtest99 >/dev/null || sudo groupadd -g 6999 labtest99
getent passwd labtest  >/dev/null || sudo useradd -g labtest99 -s /sbin/nologin -M labtest
getent group labtest99; getent passwd labtest
echo "exit was: $?"
```

**Expected output:**

```
labtest99:x:6999:
labtest:x:NNNN:6999::/home/labtest:/sbin/nologin
exit was: 0
```

---

## TASK 1 of 2 — Prove existence and membership

**In plain English:** We confirm the accounts resolve and the user is in the right group.

---

### Step 1 of 2 — Existence via `getent` exit codes

**In plain English:** We test that both the group and user resolve through NSS.

```bash
getent group labtest99 >/dev/null && echo "GROUP OK" || echo "GROUP MISSING (FAIL)"
getent passwd labtest  >/dev/null && echo "USER OK"  || echo "USER MISSING (FAIL)"
echo "exit was: $?"
```

**Expected output:**

```
GROUP OK
USER OK
exit was: 0
```

**Line-by-line breakdown:**

- `getent group labtest99 >/dev/null && ...` → Exit 0 (found) triggers the OK branch; output discarded since we only need the code.
- `getent passwd labtest >/dev/null && ...` → Same existence test for the user.

**New words in this step:**

- **`getent` exit code** — 0 when the entry resolves, 2 when not found.

---

### Step 2 of 2 — Membership via `id`

**In plain English:** We confirm the user's primary group is `labtest99`.

```bash
id labtest
id -gn labtest
[ "$(id -gn labtest)" = "labtest99" ] && echo "MEMBERSHIP OK" || echo "WRONG GROUP (FAIL)"
```

**Expected output:**

```
uid=NNNN(labtest) gid=6999(labtest99) groups=6999(labtest99)
labtest99
MEMBERSHIP OK
```

**Line-by-line breakdown:**

- `id labtest` → Full identity: UID, primary GID, supplementary groups.
- `id -gn labtest` → Just the primary group *name*.
- `[ ... = "labtest99" ]` → Assert the user landed in the intended group.

**New words in this step:**

- **`id -gn`** — print the user's primary group name.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `getent` rc | existence | 0 found, 2 missing |
| `id` | membership | resolves via NSS |
| `-gn` | primary group name | not supplementary |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `getent` rc 2 | Account missing | Re-run setup/27b |
| Wrong primary group | Created without `-g` | Recreate with group |

---

## TASK 2 of 2 — Prove consistency and safety

**In plain English:** We confirm the databases are sound and the lock infrastructure exists.

---

### Step 1 of 2 — Database consistency with `pwck`/`grpck`

**In plain English:** We run read-only consistency checks and require a clean result.

```bash
sudo pwck -r; PW=$?
sudo grpck -r; GR=$?
echo "pwck rc: $PW  grpck rc: $GR"
[ "$PW" -eq 0 ] && [ "$GR" -eq 0 ] && echo "DATABASES CONSISTENT (OK)" || echo "INCONSISTENT (FAIL)"
```

**Expected output:**

```
pwck rc: 0  grpck rc: 0
DATABASES CONSISTENT (OK)
```

**Line-by-line breakdown:**

- `sudo pwck -r; PW=$?` → Read-only check of passwd/shadow; capture the return code.
- `sudo grpck -r; GR=$?` → Read-only check of group/gshadow.
- `[ "$PW" -eq 0 ] && [ "$GR" -eq 0 ]` → Both clean means the databases are structurally sound.

**New words in this step:**

- **consistency gating** — requiring `pwck`/`grpck` rc 0 before trusting the databases.

---

### Step 2 of 2 — Lock infrastructure present

**In plain English:** We confirm the password lock file exists, evidence the safe-editing mechanism is in place.

```bash
ls -l /etc/.pwd.lock 2>/dev/null && echo "LOCK INFRA PRESENT (OK)" || echo "NO LOCK FILE (info)"
echo "exit was: $?"
```

**Expected output:**

```
-rw------- 1 root root 0 ... /etc/.pwd.lock
LOCK INFRA PRESENT (OK)
```

**Line-by-line breakdown:**

- `ls -l /etc/.pwd.lock` → The lock file `vipw`/`vigr`/`useradd` use to serialize edits; its presence shows the locking mechanism is established.

**New words in this step:**

- **`/etc/.pwd.lock`** — the account-database lock file used to serialize edits.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `pwck -r` | passwd check | rc 0 required |
| `grpck -r` | group check | rc 0 required |
| `.pwd.lock` | serialization | created on demand |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `pwck` rc non-zero | Orphan/format issue | Fix with `vipw`/`vipw -s` |
| No lock file | Never edited yet | Created by next locked edit |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Existence via `getent` exit codes
- [ ] Task 1 · Step 2 — Membership via `id`
- [ ] Task 2 · Step 1 — Database consistency with `pwck`/`grpck`
- [ ] Task 2 · Step 2 — Lock infrastructure present
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **test user and group removed**

---

## 🧹 Teardown

**In plain English:** Remove the test user and group from the real databases, then delete the sandbox.

> This lab (and its setup) changed system state. These commands **reverse** those changes; then `lab_teardown.sh` clears the marker sandbox.

```bash
sudo userdel labtest 2>/dev/null || true
sudo groupdel labtest99 2>/dev/null || true
getent passwd labtest || echo "labtest removed"
getent group labtest99 || echo "labtest99 removed"
cd /tmp
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-27
```

**Expected output:**

```
labtest removed
labtest99 removed
✅ Removed /tmp/lab-27 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Trusting `/etc/passwd` grep | Account may be broken | Verify with `getent`/`id` |
| Skipping `pwck`/`grpck` | Latent corruption | Always check after edits |
| Leaving test accounts | Drift | Run Teardown |

---

## 📌 Exam Strategy

Certify account work with `getent`/`id` for existence and membership, `pwck`/`grpck` for consistency, and remember the `/etc/.pwd.lock` mechanism that keeps concurrent edits safe. An account isn't "created" until it resolves and the databases check clean.

- `getent`/`id` prove the account actually resolves.
- `pwck -r`/`grpck -r` must return 0.
- Always remove test accounts in Teardown.

---

## 🔗 Related Labs

- [Lab 27a — Safely Editing System Databases (RHCSA)](../lab-27a-vipw-vigr-safe-editing-rhcsa/) — the `vipw`/`vigr` edits this audits
- [Lab 27b — Safely Editing System Databases (Ansible)](../lab-27b-vipw-vigr-safe-editing-ansible/) — the `user`/`group` plays you verify
- [Lab 28a — Exploring Manual Pages (RHCSA)](../lab-28a-man-pages-rhcsa/) — documentation for these account tools

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
