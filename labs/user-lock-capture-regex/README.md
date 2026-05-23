# Lab: Lock User Account and Capture Regex Evidence

**Series:** linux-ops-mastery — RHCSA User and Security Administration  
**Subjects covered:** local users, `/etc/shadow`, `passwd -l`, `passwd -S`, `getent`, anchored regular expressions, `grep -E`, `grep -oE`, evidence capture with redirection  
**Career arcs covered:** RHCSA account management, SRE offboarding runbooks, DevOps service-account control, security audit evidence  
**Prerequisite:** Comfort with `useradd`, `passwd`, `grep`, shell redirection  
**Time Estimate:** 35 to 55 minutes  
**Difficulty arc:** Tasks 1-2 baseline user state · 3-4 locking and regex proof · 5 evidence file · 6 exam-style capstone

---

## Objective

Lock a Linux user account and prove the locked state with a regex capture. By the end of this lab you can create a clean test user, lock the account, read the lock from `/etc/shadow`, capture the exact evidence string, and verify the result the way an RHCSA grader or auditor would.

The capstone is: **create user `regexlock`, lock the account, capture proof into `/root/regexlock-evidence.txt`, and verify the lock from a blank slate.**

> **Lab safety note:** This lab uses disposable local users. Do not run the cleanup blocks against real production users unless that is your intended administrative action.

---

## Concept: A Locked Password Is a Shadow-File Prefix

Linux local password state lives in `/etc/shadow`, not `/etc/passwd`. The `/etc/passwd` file usually contains an `x` in the password field, which means "look in shadow." When you lock a user with `passwd -l USER`, Linux places an exclamation mark before the encrypted password hash.

```text
Before lock:
student:$6$salt$hashed-password:19866:0:99999:7:::

After lock:
student:!$6$salt$hashed-password:19866:0:99999:7:::
        ^
        this leading ! makes password authentication fail
```

The important part is that the original hash is still there. Unlocking with `passwd -u USER` removes the `!` prefix and restores the previous password authentication state. That is why locking is reversible and safer than deleting or overwriting the password hash.

---

## Reference: Lock Commands and Proof Commands

| Goal | Command | What to look for |
|---|---|---|
| Lock account password | `passwd -l USER` | `passwd: Success` |
| Unlock account password | `passwd -u USER` | `passwd: Success` |
| Show account password status | `passwd -S USER` | `LK` means locked |
| Read passwd database | `getent passwd USER` | user exists, UID, home, shell |
| Read shadow database | `getent shadow USER` | hash field begins with `!` |
| Regex proof from shadow | `grep -oE '^USER:!+' /etc/shadow` | prints `USER:!` or `USER:!!` |

---

## Task 1 — Create a disposable user and baseline the account

**Purpose:** Create a known test account so later lock and regex checks have a clean starting point.

**Command block:**

```bash
sudo -i
userdel -r locklab 2>/dev/null || true
useradd -m -s /bin/bash locklab
echo 'locklab:RedHat!2026' | chpasswd
id locklab
getent passwd locklab
```

**Human-Readable Breakdown:**  
Become root, remove any old copy of the lab user if it exists, create `locklab` with a home directory and Bash shell, set a known password non-interactively, then prove the account exists through both `id` and the system account database.

**Reading it left to right:**  
`sudo -i` opens a full root shell. `userdel -r locklab 2>/dev/null || true` makes the lab repeatable by deleting stale state without failing if the user does not exist. `useradd -m -s /bin/bash locklab` creates the account, home directory, and shell assignment. `echo 'locklab:RedHat!2026' | chpasswd` feeds `chpasswd` one `user:password` pair. `id locklab` proves the UID and group exist. `getent passwd locklab` proves the name-service database can resolve the user.

**The story:**  
Account labs become confusing when an old test user is left behind from a previous run. The first command after becoming root should reset the state. `chpasswd` is the script-safe cousin of interactive `passwd`; it is what automation tools, kickstart files, and rescue workflows use when there is no terminal prompt. `getent` matters because it asks the name-service switch, not just a single file. On a real system, that means local files, LDAP, SSSD, or whatever the host is configured to use.

**Analogy:**  
You are setting a clean chessboard before teaching a move. If old pieces are still on the board, nobody can tell what the move changed.

**Expected output:**

```text
uid=1001(locklab) gid=1001(locklab) groups=1001(locklab)
locklab:x:1001:1001::/home/locklab:/bin/bash
```

**Switches table:**

| Token | Meaning |
|---|---|
| `sudo -i` | Start an interactive root login shell |
| `userdel -r` | Delete the user plus home directory and mail spool |
| `2>/dev/null` | Hide the expected error if the user is absent |
| `|| true` | Keep the setup block moving even if deletion was unnecessary |
| `useradd -m` | Create the user's home directory |
| `useradd -s /bin/bash` | Set the login shell |
| `chpasswd` | Read `user:password` pairs from standard input |

**Output decoded table:**

| Output | Meaning |
|---|---|
| `uid=1001(locklab)` | The local user exists and has a UID |
| `gid=1001(locklab)` | A matching primary group was created |
| `locklab:x:...` | Password hash is not in `/etc/passwd`; it is in `/etc/shadow` |
| `/home/locklab` | Home directory was created by `-m` |
| `/bin/bash` | Login shell was set correctly |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `useradd: user 'locklab' already exists` | Run `userdel -r locklab` and retry |
| `chpasswd: user 'locklab' does not exist` | The `useradd` step failed; rerun it and read the error |
| `Permission denied` | You are not root; run `sudo -i` |
| `id: locklab: no such user` | Account creation did not complete |

---

## Task 2 — Inspect the unlocked shadow state

**Purpose:** Capture the account's normal, unlocked state before changing it.

**Command block:**

```bash
passwd -S locklab
getent shadow locklab
grep -E '^locklab:' /etc/shadow
```

**Human-Readable Breakdown:**  
Ask `passwd` for the account status, ask `getent` for the shadow record, then directly grep `/etc/shadow` for the same user. This gives you two views of the same truth: a friendly status line and the raw field that will change when the account is locked.

**Reading it left to right:**  
`passwd -S locklab` prints the status summary. `getent shadow locklab` retrieves the user's shadow entry through NSS. `grep -E '^locklab:' /etc/shadow` searches the actual shadow file for a line beginning with `locklab:`. The caret `^` is the anchor that says "the username must start the line."

**The story:**  
The most common beginner mistake is checking `/etc/passwd` for lock state. That file usually stays unchanged because the password field is just `x`. The real lock marker appears in `/etc/shadow`, in the second colon-separated field. The baseline matters because after locking you want to see a specific transformation: the hash field changes from `$6$...` to `!$6$...`, and `passwd -S` changes from `PS` to `LK`.

**Analogy:**  
This is the before photo in a repair job. Without it, you cannot prove what changed.

**Expected output:**

```text
locklab PS 2026-05-23 0 99999 7 -1
locklab:$6$rounds=5000$abc...hash...:20600:0:99999:7:::
locklab:$6$rounds=5000$abc...hash...:20600:0:99999:7:::
```

**Switches table:**

| Token | Meaning |
|---|---|
| `passwd -S USER` | Show password status for one account |
| `getent shadow USER` | Retrieve the shadow entry through NSS |
| `grep -E` | Use extended regular expressions |
| `^locklab:` | Match only a line that starts with `locklab:` |

**Output decoded table:**

| Field | Meaning |
|---|---|
| `PS` | Password is set and not locked |
| `$6$` | SHA-512 password hash marker |
| `20600` or similar | Days since epoch when password was last changed |
| `0 99999 7` | Minimum age, maximum age, warning days |
| Empty trailing fields | No inactive or expiry date configured |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `passwd: Unknown user name` | Recreate the user from Task 1 |
| `getent shadow` prints nothing | You are not root or NSS cannot resolve the user |
| `grep` prints nothing | Check spelling and confirm `/etc/shadow` contains the local account |
| Status is already `LK` | A previous run left the user locked; unlock with `passwd -u locklab` |

---

## Task 3 — Lock the user and confirm the status flag

**Purpose:** Apply the account lock and verify the high-level `LK` status.

**Command block:**

```bash
passwd -l locklab
passwd -S locklab
getent shadow locklab
```

**Human-Readable Breakdown:**  
Run the lock command, then immediately inspect the account with `passwd -S` and `getent shadow`. You are looking for two independent proofs: `LK` in the status line and a leading `!` in the password-hash field.

**Reading it left to right:**  
`passwd -l locklab` means "lock the password for `locklab`." `passwd -S locklab` asks for the compact status line after the change. `getent shadow locklab` prints the raw shadow record so you can see the exact byte that was inserted.

**The story:**  
Locking is intentionally small and reversible. Linux does not delete the account, remove the home directory, or erase the hash. It only makes the stored hash unusable for password authentication by prefixing it with `!`. That is why account locks are perfect for temporary access suspension, exam tasks, security triage, and offboarding checklists where evidence matters.

**Analogy:**  
The key still exists, but you put a cap over the keyhole. Remove the cap and the same key works again.

**Expected output:**

```text
passwd: Success
locklab LK 2026-05-23 0 99999 7 -1
locklab:!$6$rounds=5000$abc...hash...:20600:0:99999:7:::
```

**Switches table:**

| Token | Meaning |
|---|---|
| `passwd -l USER` | Lock the account password |
| `passwd -S USER` | Show password status |
| `LK` | Locked password status |
| `!` in shadow | Hash is intentionally made invalid |

**Output decoded table:**

| Output | Meaning |
|---|---|
| `passwd: Success` | Shadow file was updated |
| `LK` | `passwd` sees the account as locked |
| `!$6$...` | Password hash is preserved but blocked |
| No change to username/home/shell | Locking does not delete or disable the account object itself |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| `passwd: Permission denied` | Run as root |
| Status remains `PS` | Re-run `passwd -l locklab` and inspect stderr |
| `!!` appears instead of `!$6$` | Account may have no usable password hash; still locked |
| SSH key login still works | Password lock does not necessarily disable key-based access; use account expiry for that |

---

## Task 4 — Capture the lock marker with regex

**Purpose:** Use an anchored regex to capture the exact locked prefix from `/etc/shadow`.

**Command block:**

```bash
grep -E '^locklab:!+' /etc/shadow
grep -oE '^locklab:!+' /etc/shadow
passwd -S locklab | grep -E '^locklab[[:space:]]+LK\b'
```

**Human-Readable Breakdown:**  
First match the full shadow line only if it begins with `locklab:` followed by one or more exclamation marks. Then rerun the match with `-o` so only the matched proof string is printed. Finally, use regex on the `passwd -S` status line to prove the account name is followed by the `LK` status.

**Reading it left to right:**  
`grep -E '^locklab:!+' /etc/shadow` uses extended regex. `^` anchors to the beginning of the line. `locklab:` is literal text. `!+` means one or more exclamation marks. `grep -oE` changes the output from "whole line" to "only the matching substring." `[[:space:]]+` matches one or more whitespace characters. `\b` makes `LK` a complete word.

**The story:**  
Evidence should be precise. A loose grep like `grep locklab /etc/shadow` proves only that the username exists somewhere in the file. An anchored regex proves the exact user line has the exact lock prefix. The `-o` form is especially useful for grading and audits because it turns a long sensitive shadow line into a tiny proof string: `locklab:!`.

**Analogy:**  
Instead of photographing the whole warehouse, you zoom in on the sealed lock tag.

**Expected output:**

```text
locklab:!$6$rounds=5000$abc...hash...:20600:0:99999:7:::
locklab:!
locklab LK 2026-05-23 0 99999 7 -1
```

**Switches table:**

| Token | Meaning |
|---|---|
| `grep -E` | Extended regular expressions |
| `grep -o` | Print only the matched substring |
| `^` | Start-of-line anchor |
| `!+` | One or more exclamation marks |
| `[[:space:]]+` | One or more whitespace characters |
| `\b` | Word boundary |

**Output decoded table:**

| Output | Meaning |
|---|---|
| Full shadow line | The account line is locked and still has the old hash after `!` |
| `locklab:!` | Minimal proof that the lock marker exists |
| `locklab LK ...` | `passwd` agrees with the shadow-file regex |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| No regex match | Account is not locked or username is misspelled |
| Match is too broad | Add the `^` anchor and the colon after the username |
| `grep` complains about permissions | You are not root |
| `\b` behaves unexpectedly | Use `(^locklab[[:space:]]+LK([[:space:]]|$))` for pure POSIX matching |

---

## Task 5 — Write the evidence to a file

**Purpose:** Produce a durable proof file that contains timestamp, account status, and regex-captured lock marker.

**Command block:**

```bash
{
  echo "Lock evidence captured at $(date -Is)"
  hostname
  passwd -S locklab
  grep -oE '^locklab:!+' /etc/shadow
  grep -E '^locklab:!+' /etc/shadow
} > /root/locklab-evidence.txt

ls -l /root/locklab-evidence.txt
cat /root/locklab-evidence.txt
```

**Human-Readable Breakdown:**  
Group several proof commands together, redirect their combined output into `/root/locklab-evidence.txt`, then list and read the file. The artifact records when the proof was captured, on which host, what `passwd -S` reported, what the minimal regex found, and what the full shadow line looked like.

**Reading it left to right:**  
`{ ... }` groups commands in the current shell. `echo "Lock evidence captured at $(date -Is)"` writes a timestamped header. `hostname` records the machine. `passwd -S locklab` provides the status proof. `grep -oE '^locklab:!+' /etc/shadow` provides the minimal regex proof. `grep -E '^locklab:!+' /etc/shadow` provides the full context. `> /root/locklab-evidence.txt` writes all output to one file.

**The story:**  
Real operations work does not end when the command succeeds. It ends when you can prove what you did. Evidence files are useful in tickets, audits, handoffs, and exam grading. The command group is cleaner than repeating `>>` five times, and it prevents half-written reports where one line goes to the terminal and another goes to the file.

**Analogy:**  
This is the signed receipt after locking the door: timestamp, location, and proof of the latch.

**Expected output:**

```text
-rw-r--r--. 1 root root 260 May 23 18:52 /root/locklab-evidence.txt
Lock evidence captured at 2026-05-23T18:52:10-04:00
rhel9
locklab LK 2026-05-23 0 99999 7 -1
locklab:!
locklab:!$6$rounds=5000$abc...hash...:20600:0:99999:7:::
```

**Switches table:**

| Token | Meaning |
|---|---|
| `{ ... }` | Group commands and redirect them together |
| `date -Is` | ISO-8601 timestamp with timezone |
| `>` | Write output to a file, replacing existing contents |
| `ls -l` | Show file metadata |
| `cat` | Print file contents |

**Output decoded table:**

| Line | Meaning |
|---|---|
| `Lock evidence captured...` | Time of proof |
| Hostname line | System where the proof was taken |
| `LK` line | Account status proof |
| `locklab:!` | Regex proof |
| Full shadow line | Context proof |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| File is empty | The group ran with no output; rerun each command individually |
| `date: invalid option -- I` | Use `date +%Y-%m-%dT%H:%M:%S%z` on older systems |
| Evidence file contains old runs | Use `>` for fresh evidence instead of `>>` |
| Permission denied writing `/root` | Run as root |

---

## Task 6 — Capstone: lock and prove from a blank slate

**Purpose:** Run the full exam path end-to-end: create the account, lock it, capture regex proof, and verify the result.

**Command block:**

```bash
sudo -i
userdel -r regexlock 2>/dev/null || true
rm -f /root/regexlock-evidence.txt

useradd -m -s /bin/bash regexlock
echo 'regexlock:RedHat!2026' | chpasswd

passwd -S regexlock
passwd -l regexlock

{
  echo "Lock evidence captured at $(date -Is)"
  hostname
  passwd -S regexlock
  grep -oE '^regexlock:!+' /etc/shadow
  grep -E '^regexlock:!+' /etc/shadow
} > /root/regexlock-evidence.txt

passwd -S regexlock
grep -oE '^regexlock:!+' /etc/shadow
cat /root/regexlock-evidence.txt
```

**Human-Readable Breakdown:**  
Start from a clean system state, remove any previous copy of the user and evidence file, create `regexlock`, set a password, confirm the baseline, lock the account, write the proof file, then verify the status, the regex capture, and the file contents. This is the entire exam objective in one repeatable block.

**Reading it left to right:**  
The first three commands reset the lab. `useradd` and `chpasswd` create a valid account. The first `passwd -S` should show `PS`, which proves the account began unlocked. `passwd -l regexlock` applies the lock. The grouped evidence block writes timestamp, host, status, minimal regex, and full regex to `/root/regexlock-evidence.txt`. The final three commands prove the locked state directly and through the saved artifact.

**The story:**  
The capstone is the version you memorize. The minimum viable path is: create or identify the user, lock with `passwd -l`, prove with `passwd -S`, prove with an anchored shadow regex, and save the evidence. If you can run this from a blank slate without looking anything up, account-lock questions become automatic.

**Analogy:**  
It is the complete fire drill: set up the building, pull the alarm, confirm the alarm panel, and file the incident report.

**Expected output:**

```text
regexlock PS 2026-05-23 0 99999 7 -1
passwd: Success
regexlock LK 2026-05-23 0 99999 7 -1
regexlock:!
Lock evidence captured at 2026-05-23T18:58:40-04:00
rhel9
regexlock LK 2026-05-23 0 99999 7 -1
regexlock:!
regexlock:!$6$rounds=5000$abc...hash...:20600:0:99999:7:::
```

**Switches table:**

| Token | Meaning |
|---|---|
| `userdel -r USER 2>/dev/null || true` | Idempotent cleanup |
| `rm -f FILE` | Remove stale evidence without prompting |
| `passwd -l USER` | Lock the user's password |
| `grep -oE '^USER:!+' /etc/shadow` | Print only the lock marker proof |
| `cat FILE` | Display the saved artifact |

**Output decoded table:**

| Proof | Expected result |
|---|---|
| Baseline status | `PS` before lock |
| Lock command | `passwd: Success` |
| Final status | `LK` after lock |
| Regex proof | `regexlock:!` |
| Evidence file | Contains timestamp, host, status, and shadow regex output |

**Troubleshoot table:**

| Symptom | Fix |
|---|---|
| Baseline shows `LK` | Cleanup did not remove old state; rerun `userdel -r regexlock` |
| Evidence regex is empty | Lock failed or username mismatch |
| `cat /root/regexlock-evidence.txt` missing | The grouped redirect did not run as root |
| User can still SSH with a key | Password lock is not the same as account expiry; add `chage -E 0 regexlock` for full session denial |

---

## Lab Checklist

- [ ] Create a clean local test user.
- [ ] Inspect unlocked status with `passwd -S` and `/etc/shadow`.
- [ ] Lock the account with `passwd -l`.
- [ ] Capture the lock marker with anchored regex.
- [ ] Write timestamped evidence to `/root`.
- [ ] Run the blank-slate capstone.

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
