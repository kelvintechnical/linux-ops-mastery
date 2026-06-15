# Lab 220a: PAM and SELinux with FTP (RHCSA) — `setsebool -P ftp_home_dir`, `/etc/pam.d/vsftpd`

**Series:** linux-ops-mastery — Security Administration · **Lab 220a of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (manage SELinux booleans, control services, configure FTP access), RHCE EX294 (the manual behavior behind `ansible.posix.seboolean`/`lineinfile`), Security+/SRE (defense-in-depth: SELinux + PAM together)  
**Prerequisite:** A RHEL 9 / Rocky / Alma sandbox you can `sudo` on with SELinux in **Enforcing** mode (`getenforce`) and package access to install `vsftpd`; the SELinux-boolean labs (e.g. [Lab 82a](../lab-82a-selinux-booleans-rhcsa/)) are a useful warm-up  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

---

## 🎯 Objective

Stand up the `vsftpd` FTP server and secure it with the two independent guards RHEL layers on top of file permissions: an **SELinux boolean** that decides whether FTP may even touch users' home directories, and a **PAM access list** that decides which accounts may log in at all. You will install and enable `vsftpd`, flip `ftp_home_dir` on *persistently* with `setsebool -P`, then read `/etc/pam.d/vsftpd` to see how `pam_listfile` turns `/etc/vsftpd/ftpusers` into a deny list — and add an account to that list to block it. Every config file you change is backed up into the sandbox so Teardown can restore the box exactly.

---

## 🧠 Concept

On RHEL, "can this FTP user read their home directory?" is answered by **three** layers, and all three must agree. Standard Unix permissions are first. Then **SELinux**: even with perfect permissions, the `vsftpd` process runs in a confined domain that is *denied* home-directory access unless the `ftp_home_dir` boolean is on — and a boolean change only survives a reboot when you set it with `-P` (persistent). Finally **PAM**: before authentication even completes, `/etc/pam.d/vsftpd` runs `pam_listfile.so` against `/etc/vsftpd/ftpusers`, and any account listed there is *denied* (that is why `root` is denied FTP out of the box). Permissions, SELinux booleans, and PAM lists are three separate locks on the same door.

```
FTP login attempt for user "alice"
        │
        ▼
PAM (/etc/pam.d/vsftpd) ── pam_listfile ─▶ is "alice" in /etc/vsftpd/ftpusers?
        │  yes → DENY (login rejected)        no ↓
        ▼
SELinux ── is ftp_home_dir boolean ON? ── no → AVC denial, home dir unreadable
        │  yes ↓
        ▼
Unix permissions on ~alice  ──▶ normal rwx checks ──▶ access granted
```

> **Why this matters:** Beginners "fix" an FTP problem by loosening file permissions and get nowhere, because the real block is an SELinux boolean or a PAM deny list they never looked at. Knowing the three layers — and that `setsebool` needs `-P` to persist — is exactly the RHCSA troubleshooting muscle this lab builds.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `dnf install -y vsftpd` | Install the Very Secure FTP daemon | provides `/etc/vsftpd/` and the `vsftpd.service` unit |
| `systemctl enable --now vsftpd` | Start the FTP service now *and* at boot | `--now` = start immediately in addition to enabling |
| `getsebool ftp_home_dir` | Read the current value of an SELinux boolean | prints `ftp_home_dir --> on/off` |
| `setsebool -P ftp_home_dir on` | Set an SELinux boolean **persistently** | `-P` writes policy so it survives reboot; without it, runtime-only |
| `/etc/pam.d/vsftpd` | PAM stack for FTP; runs `pam_listfile` against `ftpusers` | the `file=/etc/vsftpd/ftpusers sense=deny` line is the access gate |
| `/etc/vsftpd/ftpusers` | List of accounts **denied** FTP login | one username per line; `root` is present by default |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We make one sandbox folder under `/tmp`, confirm SELinux is enforcing, and back up the two files we will change (`/etc/vsftpd/ftpusers` and the live `ftp_home_dir` value) so Teardown can restore the system exactly.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-220
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

getenforce
sudo dnf install -y vsftpd >/dev/null && echo "vsftpd installed"

# Back up state we will modify so Teardown can restore it.
sudo cp -a /etc/vsftpd/ftpusers "$LAB_ROOT/ftpusers.bak" 2>/dev/null || true
getsebool ftp_home_dir | tee "$LAB_ROOT/ftp_home_dir.before"

ls -l "$LAB_ROOT"
echo "Sandbox ready at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
Enforcing
vsftpd installed
ftp_home_dir --> off
-rw-r--r--. 1 root root  21 Jun 15 18:00 ftp_home_dir.before
-rw-------. 1 root root 152 Jun 15 18:00 ftpusers.bak
Sandbox ready at 2026-06-15T18:00:03-04:00
exit was: 0
```

---

## TASK 1 of 2 — Bring up vsftpd and open the SELinux home-dir boolean

**In plain English:** We start and enable the FTP service, confirm it is listening, then read and persistently flip the `ftp_home_dir` SELinux boolean so authenticated users can actually reach their home directories.

---

### Step 1 of 2 — Install, enable, and confirm vsftpd is listening

**In plain English:** We enable `vsftpd` to run now and at boot, confirm it is active, and prove it is listening on the FTP control port 21.

```bash
sudo systemctl enable --now vsftpd
systemctl is-active vsftpd
sudo ss -tlnp | grep ':21 '
echo "exit was: $?"
```

**Expected output:**

```
Created symlink /etc/systemd/system/multi-user.target.wants/vsftpd.service → /usr/lib/systemd/system/vsftpd.service.
active
LISTEN 0      32           *:21          *:*    users:(("vsftpd",pid=2310,fd=3))
exit was: 0
```

**Line-by-line breakdown:**

- `sudo systemctl enable --now vsftpd` → Create the boot symlink *and* start the daemon immediately; `--now` saves the separate `start` step, so FTP is both running and persistent.
- `systemctl is-active vsftpd` → Read-only confirm the service is `active` right now.
- `sudo ss -tlnp | grep ':21 '` → Prove `vsftpd` is bound to TCP port 21 (the FTP control channel); seeing the `vsftpd` process owning `:21` confirms the service is truly serving, not just "started."
- `echo "exit was: $?"` → Print the exit status as a scriptable signal.

**New words in this step:**

- **vsftpd** — the "Very Secure FTP Daemon," RHEL's default FTP server; its config lives under `/etc/vsftpd/`.
- **control port 21** — the TCP port FTP uses for commands; data transfers use a separate port negotiated per connection.

---

### Step 2 of 2 — Read and persistently set the `ftp_home_dir` boolean

**In plain English:** We check the current `ftp_home_dir` value, turn it on with `-P` so the change persists across reboots, and confirm SELinux now permits FTP to access home directories.

```bash
getsebool ftp_home_dir
sudo setsebool -P ftp_home_dir on
getsebool ftp_home_dir
echo "exit was: $?"
```

**Expected output:**

```
ftp_home_dir --> off
ftp_home_dir --> on
exit was: 0
```

**Line-by-line breakdown:**

- `getsebool ftp_home_dir` (first) → Read the boolean's current value; it ships `off`, so SELinux is *blocking* FTP from touching home directories regardless of file permissions.
- `sudo setsebool -P ftp_home_dir on` → Turn the boolean on **persistently**; the `-P` flag writes the change into the policy store so it survives a reboot. Without `-P` the change is runtime-only and lost on the next boot — a classic exam trap.
- `getsebool ftp_home_dir` (second) → Confirm the value is now `on`, so SELinux permits the access the FTP users need.

**New words in this step:**

- **SELinux boolean** — a named on/off switch that toggles a chunk of SELinux policy without writing custom rules.
- **`-P` (persistent)** — the `setsebool` flag that makes a boolean change permanent across reboots, not just for the current session.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `enable --now vsftpd` | starts now AND at boot | plain `start` is lost on reboot |
| `setsebool -P` | persists a boolean change | dropping `-P` makes it runtime-only |
| `ftp_home_dir` | lets FTP reach home dirs | perfect file perms still fail if this is `off` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| FTP login works but home dir is "permission denied" | `ftp_home_dir` boolean is `off` | `sudo setsebool -P ftp_home_dir on` |
| Boolean reverts after reboot | You set it without `-P` | Re-run with `setsebool -P` to persist it |

---

## TASK 2 of 2 — Control logins with PAM and the ftpusers deny list

**In plain English:** We read `/etc/pam.d/vsftpd` to see how PAM enforces a deny list, confirm `root` is already denied, then add another account to `/etc/vsftpd/ftpusers` to block it — pure access control, no permissions changed.

---

### Step 1 of 2 — Inspect the PAM stack and the existing deny list

**In plain English:** We look at the `pam_listfile` line in `/etc/pam.d/vsftpd` that wires FTP to the deny file, then confirm `root` is in `/etc/vsftpd/ftpusers` and therefore blocked.

```bash
grep -n 'pam_listfile' /etc/pam.d/vsftpd
grep -nx 'root' /etc/vsftpd/ftpusers && echo "root is DENIED FTP (as shipped)"
echo "exit was: $?"
```

**Expected output:**

```
2:auth    required     pam_listfile.so item=user sense=deny file=/etc/vsftpd/ftpusers onerr=succeed
1:root
root is DENIED FTP (as shipped)
```

**Line-by-line breakdown:**

- `grep -n 'pam_listfile' /etc/pam.d/vsftpd` → Show the PAM line that does access control; `pam_listfile.so item=user sense=deny file=/etc/vsftpd/ftpusers` reads as "for the *user* item, **deny** anyone whose name appears in `ftpusers`." `onerr=succeed` means a missing file does not lock everyone out.
- `grep -nx 'root' /etc/vsftpd/ftpusers` → Confirm `root` is listed (`-x` matches the whole line exactly); because PAM denies listed users, `root` cannot log in over FTP by default — a deliberate hardening default.
- `&& echo "root is DENIED FTP (as shipped)"` → Make the meaning explicit when the match is found.

**New words in this step:**

- **PAM** — Pluggable Authentication Modules, the stack RHEL consults to decide *whether and how* an account may authenticate to a service.
- **`pam_listfile`** — a PAM module that allows or denies based on whether a name appears in a given file (here, deny by `ftpusers`).

---

### Step 2 of 2 — Add an account to the deny list and confirm

**In plain English:** We append a demonstration username to `/etc/vsftpd/ftpusers` (backed up in setup), confirm it is now listed, and explain that PAM will reject its FTP logins — all without touching file permissions or SELinux.

```bash
echo 'labghost220' | sudo tee -a /etc/vsftpd/ftpusers
grep -nx 'labghost220' /etc/vsftpd/ftpusers && echo "labghost220 is now DENIED FTP"
sudo diff "$LAB_ROOT/ftpusers.bak" /etc/vsftpd/ftpusers
echo "exit was: $?"
```

**Expected output:**

```
labghost220
4:labghost220
labghost220 is now DENIED FTP
4a5
> labghost220
exit was: 1
```

**Line-by-line breakdown:**

- `echo 'labghost220' | sudo tee -a /etc/vsftpd/ftpusers` → Append a username to the deny file; `tee -a` adds a line without truncating the file. Any FTP login attempt for this account will now be rejected by PAM *before* a password is even checked.
- `grep -nx 'labghost220' /etc/vsftpd/ftpusers` → Confirm the exact line is present, with its line number.
- `sudo diff "$LAB_ROOT/ftpusers.bak" /etc/vsftpd/ftpusers` → Compare against the backup taken in setup; the single `> labghost220` add line is the only difference, and `diff`'s exit code `1` means "files differ" (expected, not an error) — proof our change is surgical and reversible.

**New words in this step:**

- **deny list** — a file of names that are *blocked*; `ftpusers` denies FTP login to every account it contains.
- **`tee -a`** → append text to a file (instead of overwriting), useful with `sudo` for editing root-owned config.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `pam_listfile sense=deny` | denies users listed in `ftpusers` | `sense=allow` would invert it to an allow list |
| `/etc/vsftpd/ftpusers` | the FTP deny list | being *in* it means blocked, not allowed |
| `onerr=succeed` | missing file ⇒ don't block everyone | deleting `ftpusers` opens the gate, not closes it |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| A user can still FTP in despite editing a file | You edited `user_list`, not `ftpusers`, or wrong semantics | Confirm `/etc/pam.d/vsftpd` points at `ftpusers` with `sense=deny` |
| Everyone is suddenly blocked | `ftpusers` syntax/whitespace error | Restore from `$LAB_ROOT/ftpusers.bak` and re-edit carefully |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Install, enable, and confirm vsftpd is listening
- [ ] Task 1 · Step 2 — Read and persistently set the `ftp_home_dir` boolean
- [ ] Task 2 · Step 1 — Inspect the PAM stack and the existing deny list
- [ ] Task 2 · Step 2 — Add an account to the deny list and confirm

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it enabled a service, set a persistent SELinux boolean, and edited a PAM-controlled file), and `rm` will NOT undo those. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo setsebool -P ftp_home_dir off
sudo systemctl disable --now vsftpd
# Restore the original ftpusers from the setup backup (removes labghost220):
sudo cp -a "$LAB_ROOT/ftpusers.bak" /etc/vsftpd/ftpusers
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-220
```

> Optional: if you want the box exactly as it was before, `sudo dnf remove -y vsftpd` — but only if `vsftpd` was not already required by the system.

**Expected output:**

```
✅ Removed /tmp/lab-220 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Setting `ftp_home_dir` without `-P` | Works now, broken after reboot | Always use `setsebool -P` for persistence |
| Loosening file permissions to "fix" FTP | Access still denied | Check the SELinux boolean and PAM list first |
| Confusing `ftpusers` with `user_list` | Wrong users blocked/allowed | `ftpusers` is the PAM deny list; verify via `/etc/pam.d/vsftpd` |

---

## 📌 Exam Strategy

When an FTP task "doesn't work," resist touching `chmod`. Walk the three layers in order: is the account on a PAM deny list (`/etc/vsftpd/ftpusers`)? Is the relevant SELinux boolean on (`getsebool ftp_home_dir`, fix with `setsebool -P`)? Only then look at Unix permissions. The RHCSA loves the `-P` distinction and the SELinux-boolean-as-root-cause scenario.

- Say "minus P or it won't persist" every time you run `setsebool`.
- Use `getsebool`/`setsebool -P` before reaching for `chmod` on FTP problems.
- Remember `ftpusers` is a *deny* list — being listed blocks the account.

---

## 🔗 Related Labs

- [Lab 220b — PAM and SELinux with FTP (Ansible)](../lab-220b-pam-selinux-ftp-ansible/) — the same setup expressed idempotently with `seboolean` and `lineinfile`
- [Lab 220c — PAM and SELinux with FTP (Verify)](../lab-220c-pam-selinux-ftp-verify/) — prove the boolean, service, and deny list with hard assertions
- [Lab 82a — Toggling SELinux Booleans (RHCSA)](../lab-82a-selinux-booleans-rhcsa/) — the boolean fundamentals this lab applies to FTP

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
