# Lab 220c: PAM and SELinux with FTP (Verify) — `getsebool`, `systemctl is-active`, `grep -nx`

**Series:** linux-ops-mastery — Security Administration · **Lab 220c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (confirming SELinux booleans, services, and PAM deny lists), RHCE EX294 (validating `seboolean`/`lineinfile` playbook results), Security+/SRE (FTP hardening attestation)  
**Prerequisite:** [Lab 220a](../lab-220a-pam-selinux-ftp-rhcsa/) and [Lab 220b](../lab-220b-pam-selinux-ftp-ansible/) completed, on a RHEL 9 / Rocky / Alma sandbox you can `sudo` on with SELinux **Enforcing**  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Attest the FTP hardening from 220a/220b without changing policy yourself. You will assert `vsftpd` is active, the `ftp_home_dir` boolean is **on**, the PAM stack still points at `/etc/vsftpd/ftpusers` with `sense=deny`, and both `root` and the lab demonstration account `labghost220` appear on the deny list — printing an explicit OK/FAIL line for each check so a grader (or future you) can read the verdict at a glance.

---

## 🧠 Concept

Verifying FTP security is a three-layer checklist, and each layer has a dedicated read-only tool. **Service state:** `systemctl is-active vsftpd` and `ss -tlnp | grep ':21 '` prove the daemon is running and listening. **SELinux:** `getsebool ftp_home_dir` must read `on` — without it, home-directory access fails no matter what file permissions say. **PAM:** grep `/etc/pam.d/vsftpd` for `pam_listfile` to confirm the deny file path, then `grep -nx` in `/etc/vsftpd/ftpusers` to confirm blocked accounts. Verification never loosens permissions; it only reads and asserts.

```
systemctl is-active vsftpd     → active   (service up)
getsebool ftp_home_dir         → on       (SELinux allows home dirs)
grep pam_listfile vsftpd       → file=/etc/vsftpd/ftpusers sense=deny
grep -nx root ftpusers         → present  (root blocked by default)
grep -nx labghost220 ftpusers   → present  (lab deny entry from 220a/220b)
```

> **Why this matters:** The RHCSA loves "it still fails after chmod 777" scenarios where the real block is a boolean or PAM list. A verify lab trains you to *prove* each layer before you declare the task done — the same discipline a grader uses.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `systemctl is-active vsftpd` | Read-only service state | prints `active`/`inactive`; exit 0 only when active |
| `ss -tlnp \| grep ':21 '` | Prove FTP control port is listening | shows the `vsftpd` process owning `:21` |
| `getsebool ftp_home_dir` | Read an SELinux boolean | must show `on` after 220a/220b |
| `grep pam_listfile /etc/pam.d/vsftpd` | Confirm PAM deny wiring | look for `sense=deny` and `file=/etc/vsftpd/ftpusers` |
| `grep -nx <user> /etc/vsftpd/ftpusers` | Assert a user is on the deny list | `-x` = whole-line match; `-n` = line number |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We point at the same `/tmp/lab-220` sandbox and, if 220a/220b were torn down, rebuild the minimum FTP hardening state this verify lab expects to audit — then save a snapshot file listing the checks we will run.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-220
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

getenforce | tee "$LAB_ROOT/selinux-mode.txt"

# Rebuild expected state if prior labs were cleaned up:
if ! systemctl is-active --quiet vsftpd; then
  sudo dnf install -y vsftpd >/dev/null
  sudo systemctl enable --now vsftpd
fi
sudo setsebool -P ftp_home_dir on
grep -qx 'labghost220' /etc/vsftpd/ftpusers 2>/dev/null \
  || echo 'labghost220' | sudo tee -a /etc/vsftpd/ftpusers >/dev/null

{
  echo "# Lab 220c attestation snapshot $(date -Is)"
  systemctl is-active vsftpd
  getsebool ftp_home_dir
  grep 'pam_listfile' /etc/pam.d/vsftpd
} | tee "$LAB_ROOT/attest-baseline.txt"

echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
Enforcing
# Lab 220c attestation snapshot 2026-06-15T18:15:02-04:00
active
ftp_home_dir --> on
auth    required     pam_listfile.so item=user sense=deny file=/etc/vsftpd/ftpusers onerr=succeed
Sandbox ready at 2026-06-15T18:15:02-04:00
exit was: 0
```

---

## TASK 1 of 2 — Assert service and SELinux layers

**In plain English:** We confirm `vsftpd` is active, listening on port 21, and the `ftp_home_dir` boolean is on — the two layers that must pass before PAM even matters for home-directory reads.

---

### Step 1 of 2 — Check service state and the listening port

**In plain English:** We read `systemctl is-active` and inspect port 21 with `ss`, printing OK/FAIL for each.

```bash
if systemctl is-active --quiet vsftpd; then
  echo "SERVICE OK: vsftpd is active"
else
  echo "SERVICE FAIL: vsftpd is not active"
fi

if sudo ss -tlnp | grep -q ':21 '; then
  echo "PORT OK: something is listening on TCP 21"
  sudo ss -tlnp | grep ':21 '
else
  echo "PORT FAIL: nothing listening on TCP 21"
fi
echo "exit was: $?"
```

**Expected output:**

```
SERVICE OK: vsftpd is active
PORT OK: something is listening on TCP 21
LISTEN 0      32           *:21          *:*    users:(("vsftpd",pid=2310,fd=3))
exit was: 0
```

**Line-by-line breakdown:**

- `systemctl is-active --quiet vsftpd` → Exit 0 only when the unit is `active`; `--quiet` suppresses text so the `if` tests the exit code alone.
- `ss -tlnp | grep ':21 '` → List TCP listeners (`-tln`) with processes (`-p`) and match the FTP control port.
- OK/FAIL echoes → Turn each check into an explicit verdict a script (or grader) can scan.

**New words in this step:**

- **control port 21** — FTP's command channel; data uses separate ports negotiated per session.

---

### Step 2 of 2 — Assert the `ftp_home_dir` boolean is on

**In plain English:** We read `getsebool ftp_home_dir` and fail the check if it is not `on`.

```bash
if getsebool ftp_home_dir | grep -q '--> on'; then
  echo "SELINUX OK: ftp_home_dir is on"
else
  echo "SELINUX FAIL: ftp_home_dir is off (home dirs blocked for FTP)"
  getsebool ftp_home_dir
fi
echo "exit was: $?"
```

**Expected output:**

```
SELINUX OK: ftp_home_dir is on
exit was: 0
```

**Line-by-line breakdown:**

- `getsebool ftp_home_dir` → Print the boolean in `name --> on/off` form.
- `grep -q '--> on'` → Treat only the `on` state as PASS; `off` means SELinux still blocks FTP home access regardless of Unix permissions.

**New words in this step:**

- **attestation** — proving a configuration is in the expected state without modifying it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `is-active --quiet` | scriptable service check | reading `status` output is harder to automate |
| `ss -tlnp` | prove a port is owned by the right daemon | `systemctl start` without listening = misconfig |
| `ftp_home_dir --> on` | SELinux allows FTP home access | chmod 777 still fails when boolean is off |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| SERVICE FAIL | unit not enabled/started | `sudo systemctl enable --now vsftpd` |
| SELINUX FAIL | boolean off or not persistent | `sudo setsebool -P ftp_home_dir on` |

---

## TASK 2 of 2 — Assert PAM wiring and deny-list entries

**In plain English:** We confirm PAM still denies users listed in `ftpusers`, and assert both `root` and `labghost220` are on that list.

---

### Step 1 of 2 — Confirm the PAM stack points at the deny file

**In plain English:** We grep `/etc/pam.d/vsftpd` for the `pam_listfile` line and verify it uses `sense=deny` and the expected file path.

```bash
PAM_LINE=$(grep 'pam_listfile' /etc/pam.d/vsftpd)
echo "$PAM_LINE"
if echo "$PAM_LINE" | grep -q 'sense=deny' \
   && echo "$PAM_LINE" | grep -q 'file=/etc/vsftpd/ftpusers'; then
  echo "PAM OK: ftpusers deny list is wired"
else
  echo "PAM FAIL: unexpected pam_listfile configuration"
fi
echo "exit was: $?"
```

**Expected output:**

```
auth    required     pam_listfile.so item=user sense=deny file=/etc/vsftpd/ftpusers onerr=succeed
PAM OK: ftpusers deny list is wired
exit was: 0
```

**Line-by-line breakdown:**

- `grep 'pam_listfile' /etc/pam.d/vsftpd` → Extract the single PAM line that enforces the deny list.
- `sense=deny` check → Confirms listed users are **blocked**, not allowed.
- `file=/etc/vsftpd/ftpusers` check → Confirms we are auditing the same file 220a/220b edited.

**New words in this step:**

- **`sense=deny`** — PAM rejects accounts whose names appear in the referenced file.

---

### Step 2 of 2 — Assert `root` and `labghost220` are denied

**In plain English:** We use `grep -nx` to prove both accounts appear as whole lines in `ftpusers`, printing OK/FAIL for each.

```bash
for u in root labghost220; do
  if grep -qx "$u" /etc/vsftpd/ftpusers; then
    echo "DENY OK: $u is listed (line $(grep -nx "$u" /etc/vsftpd/ftpusers | cut -d: -f1))"
  else
    echo "DENY FAIL: $u is NOT on the deny list"
  fi
done
echo "exit was: $?"
```

**Expected output:**

```
DENY OK: root is listed (line 1)
DENY OK: labghost220 is listed (line 4)
exit was: 0
```

**Line-by-line breakdown:**

- `grep -qx "$u" /etc/vsftpd/ftpusers` → `-x` requires a whole-line match so `rooty` does not falsely pass as `root`.
- `grep -nx` + `cut -d: -f1` → Print the line number for audit logs.
- Loop over `root` and `labghost220` → Covers the shipped default **and** the lab-added demonstration deny entry.

**New words in this step:**

- **`-qx`** — quiet whole-line grep; ideal for "is this exact username present?" checks.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `pam_listfile sense=deny` | listed names blocked at login | confusing with `user_list` allow semantics |
| `grep -qx user ftpusers` | exact deny-list membership test | substring grep gives false positives |
| `root` on deny list | root FTP blocked by default | "fixing" with chmod does not remove PAM deny |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| labghost220 DENY FAIL | 220b not applied or teardown ran | re-run 220b Task 2 or append the line manually |
| PAM FAIL | edited wrong PAM file | restore `/etc/pam.d/vsftpd` from vendor package |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Check service state and the listening port
- [ ] Task 1 · Step 2 — Assert the `ftp_home_dir` boolean is on
- [ ] Task 2 · Step 1 — Confirm the PAM stack points at the deny file
- [ ] Task 2 · Step 2 — Assert `root` and `labghost220` are denied
- [ ] 🧹 Teardown run — reverse system state + sandbox wipe

---

## 🧹 Teardown

**In plain English:** Reverse the FTP hardening this trilogy applied, then remove the sandbox.

```bash
sudo setsebool -P ftp_home_dir off
sudo systemctl disable --now vsftpd
sudo sed -i '/^labghost220$/d' /etc/vsftpd/ftpusers
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-220
```

**Expected output:**

```
✅ Removed /tmp/lab-220 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Checking `user_list` instead of `ftpusers` | false PASS/FAIL | follow `/etc/pam.d/vsftpd`'s `file=` path |
| Substring grep for usernames | `rooty` matches `root` | always use `grep -x` for account names |
| Skipping SELinux check | service up but uploads fail | `getsebool ftp_home_dir` first |

---

## 📌 Exam Strategy

Walk the same three layers in order on every FTP troubleshooting task: PAM deny list → SELinux boolean (`-P` for persistence) → Unix permissions. This verify lab is the checklist; memorize the OK/FAIL pattern.

---

## 🔗 Related Labs

- [Lab 220a — PAM and SELinux with FTP (RHCSA)](../lab-220a-pam-selinux-ftp-rhcsa/) — hands-on setup this lab attests
- [Lab 220b — PAM and SELinux with FTP (Ansible)](../lab-220b-pam-selinux-ftp-ansible/) — idempotent declarative version
- [Lab 82a — Toggling SELinux Booleans (RHCSA)](../lab-82a-selinux-booleans-rhcsa/) — boolean fundamentals

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
