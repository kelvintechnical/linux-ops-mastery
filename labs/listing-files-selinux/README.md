# Lab 06: Listing Files and SELinux Contexts — `ls -l`, `ls -Z`, `ps -eZ`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (SELinux objectives, file permissions), RHCE EX294 (Ansible file/copy with `setype:`), CKA (pod SELinux contexts), RHCA — RH362 (Identity Mgmt + SELinux audit)
- **Prerequisite:** Lab 05 (`pwd`, `cd`, `ls -l`)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 3 (ADHD spec — exactly 3 dense tasks per `readmetemplate/cursor-adhd-lab-prompt.txt`)
- **Practice Directory (lab-wide rotation #06):** `/etc`
- **Sandbox:** `/tmp/lsZ-lab`
- **Traps rehearsed this lab:** **T01** (Setting permissive instead of fixing the real context) · **T02** (semanage fcontext without restorecon -Rv afterward)

> **This lab's practice directory is: `/etc`** — every task references it in at least two commands.

---

## 🖥️ LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T01 T02"
echo "📁  PRACTICE DIR: /etc"
```

> **STOP — paste header output before running setup.**
>
> ⚠️ **ENV WARN — AMI users:** if `getenforce` returns `Disabled` or `Permissive`, run `sudo setenforce 1` if possible. If SELinux is fully disabled in `/etc/selinux/config`, flag this lab as ⚠️ **partially blocked** and plan to redo Task 3 on a baremetal or Rocky/RHEL AMI.

---

## 🎯 Objective

Read a Linux long listing column-by-column, then layer SELinux context awareness on top. By the end of this lab you can identify the owner, group, permissions, link count, SELinux user, role, type, and MLS level of any file — and you can connect a running process's context to the file context it can access.

---

## 🧠 Concept: Two Permission Models on Top of Each Other

| Layer | Tool | Question it answers |
|---|---|---|
| **DAC** (Discretionary Access Control) | `ls -l`, `chmod`, `chown` | "Does the file's mode allow the user/group to read/write/execute?" |
| **MAC** (Mandatory Access Control) | `ls -Z`, `semanage`, `chcon`, `restorecon` | "Does SELinux policy allow this *process context* to touch this *file context*?" |

A process must pass **both** checks. SELinux only matters when DAC says "yes" — but SELinux can still block what DAC permits.

### Reading `ls -l` left to right

```
-rw-r--r--. 1 root root  1234 May 27 13:45 /etc/hostname
└┬┘└──┬───┘ │ └─┬┘ └─┬┘   │      │            │
type   mode  │   │     │     size   mtime         path
            link  user group
            count
```

### Reading `ls -Z` left to right

```
system_u:object_r:net_conf_t:s0 /etc/hostname
   │        │         │       │
  user     role      type    level (MLS / MCS)
```

The **type** (`net_conf_t`, `etc_t`, `httpd_sys_content_t`, ...) is the one that matters 95% of the time on RHCSA.

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/lsZ-lab
cd /tmp/lsZ-lab

cat > /tmp/lsZ-lab/THIS_DIRECTORY.txt <<'EOF'
/etc — System-wide configuration files

Every daemon, service, and subsystem reads its configuration from /etc. No
binaries live here — only text files and scripts. Backing up /etc is
effectively backing up the system's identity.

Why it exists: separating mutable configuration from immutable binaries
makes upgrades, audits, and recoveries straightforward. /usr/bin/sshd
never changes between minor releases, but /etc/ssh/sshd_config does.

What lives inside it: networking (/etc/hosts, /etc/resolv.conf), users
(/etc/passwd, /etc/shadow), services (/etc/systemd, /etc/httpd), security
(/etc/selinux, /etc/pam.d), and hundreds of per-package config trees.

Why RHCSA cares: nearly every exam objective touches /etc. Every SELinux
context type you will encounter on the exam (etc_t, net_conf_t,
shadow_t, ssh_home_t, httpd_config_t) is anchored here.
EOF

cat /tmp/lsZ-lab/THIS_DIRECTORY.txt
sestatus 2>/dev/null || echo "SELinux tooling not available — install policycoreutils-python-utils"
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — Decode the Long Listing on `/etc`

### a) Directory Context

**Practice directory this task:** `/etc`
`/etc` has every type of entry you will see on RHCSA: regular files, directories, symlinks, files owned by different users, files with restrictive modes, and files with various SELinux types.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/lsZ-lab
pwd
ls -ld /etc /tmp/lsZ-lab > task01-warmup.log 2>&1
cat task01-warmup.log
echo "etc entries: $(ls /etc 2>/dev/null | wc -l)"
ls /etc | head -n 5 | tee task01-etc-head.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Read every column of `ls -l` output on real `/etc` files and prove you understand each piece.

### d) Main Command Block

```bash
cd /tmp/lsZ-lab
ls -l /etc/hostname /etc/hosts /etc/passwd /etc/shadow /etc/resolv.conf 2>&1 | tee task01-etc-long.txt
ls -la /etc/ssh > task01-ssh.txt 2>&1
ls -ld /etc /etc/ssh /etc/systemd > task01-dirs.txt 2>&1
cat task01-etc-long.txt
echo "---"
head -n 5 task01-ssh.txt
echo "---"
cat task01-dirs.txt
echo "line counts: $(wc -l task01-*.txt)"
```

### e) Human-Readable Breakdown

- `ls -l /etc/hostname /etc/hosts ...` — long listing for 5 critical files.
- `2>&1 | tee FILE` — capture both stdout and stderr to the file AND the screen (e.g. `/etc/shadow` may not be readable for non-root; the error goes into the same file as the success lines).
- `ls -la /etc/ssh` — long listing including hidden entries (none in `/etc/ssh` normally, but the pattern matters).
- `ls -ld /etc /etc/ssh /etc/systemd` — metadata for the directories themselves.

### f) Reading It Left to Right

`ls -l /etc/hostname /etc/hosts /etc/passwd /etc/shadow /etc/resolv.conf 2>&1 | tee task01-etc-long.txt`

1. `ls -l` — long format.
2. Five `/etc/*` files as targets.
3. `2>&1` — merge stderr into stdout (capture permission-denied errors in the same stream).
4. `| tee FILE` — print to screen AND write to file.

A single line of output:

```
-rw-r--r--. 1 root root 9 May 27 13:45 /etc/hostname
```

| Column | Meaning |
|---|---|
| `-` | Regular file (vs `d` for dir, `l` for symlink, `c` for char device) |
| `rw-r--r--` | Owner read+write, group read, other read |
| `.` | SELinux context exists (would be `+` for ACL, blank for neither) |
| `1` | Hard link count |
| `root` | Owner user |
| `root` | Owner group |
| `9` | Size in bytes |
| `May 27 13:45` | Last modification time |
| `/etc/hostname` | Path |

### g) The Story

`ls -l` is the universal Linux "X-ray." Before you `chmod`, `chown`, `chcon`, or `restorecon` anything, you read `ls -l` and `ls -Z` first. RHCSA grading scripts read these same fields — if your `chmod 640` produces `-rw-r-----` your task passes; if it produces `-rw-r--r--` it fails.

### h) Expected Output

```text
-rw-r--r--. 1 root root    9 ... /etc/hostname
-rw-r--r--. 1 root root  158 ... /etc/hosts
-rw-r--r--. 1 root root 2987 ... /etc/passwd
ls: cannot open '/etc/shadow': Permission denied   (or, if root, ----------. 1 root root ...)
-rw-r--r--. 1 root root   90 ... /etc/resolv.conf
total ...
-rw-r--r--. 1 root root ... ssh_config
-rw-------. 1 root root ... ssh_host_ed25519_key
...
drwxr-xr-x. ... /etc
drwxr-xr-x. ... /etc/ssh
drwxr-xr-x. ... /etc/systemd
line counts: ...
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `ls -l` | Long listing |
| `ls -la` | Long + hidden |
| `ls -ld` | Directory entry, not contents |
| `2>&1` | Stderr → stdout's destination |
| `\| tee FILE` | Print and save |
| `head -n N` | First N lines |
| `wc -l` | Line count |
| `.` (after mode) | SELinux context present |
| `+` (after mode) | ACL present |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | File type char | `-` file, `d` dir, `l` link, `c`/`b` device, `p` pipe, `s` socket |
|   | rwx triplets | Owner / group / other |
|   | Link count | How many hard links point to this inode |
|   | Owner / group | Two separate identities |
|   | `.` after mode | SELinux context present (modern RHEL default) |
|   | `+` after mode | ACL present (we'll cover ACLs in a later lab) |
|   | `2>&1 \| tee` | Capture stdout+stderr AND show on screen |
| 🪤 **Trap Risk (T01)** | Setting permissive instead of fixing context | When `ls -l` shows correct mode but app fails, the next instinct is `setenforce 0` — wrong. Run `ls -Z` instead and fix the *type* with `semanage fcontext` + `restorecon` |

### k) 🧹 Cleanup

```bash
LAB=lab06
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    Reading ls -l columns on /etc
COMMANDS: ls -l, ls -la, ls -ld, 2>&1, tee
TRAPS:    T01 (permissive ≠ fix)
MISSED:   —
NEXT:     task2 — ls -Z and SELinux context reading
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/lsZ-lab
rm -f task01-warmup.log task01-etc-head.txt task01-etc-long.txt task01-ssh.txt task01-dirs.txt
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `Permission denied` on `/etc/shadow` | Expected for non-root; rerun with `sudo` |
| No `.` after the mode | SELinux is disabled or filesystem is FAT/exfat — confirm with `sestatus` |
| Times shown as `2025` instead of `13:45` | Files older than 6 months show year instead of time — normal |
| `tee` shows duplicate output | That is the design — `tee` writes to file AND stdout |

### m) STOP

> **STOP — paste output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Journal entry | `cat /root/rhcsa_journal/lab06/task1/done.txt` | Survives reboot |
| `/etc` integrity | `ls -ld /etc \| head -1` | Practice dir still mounted |
| Sandbox cleaned | `ls /tmp/lsZ-lab` | Should be empty or `THIS_DIRECTORY.txt` only |

---

## Task 2 — `ls -Z`: Read SELinux File Contexts

### a) Directory Context

**Practice directory this task:** `/etc`
`/etc` files have a wide variety of SELinux types — `etc_t`, `net_conf_t`, `shadow_t`, `passwd_file_t`, `ssh_home_t`, `httpd_config_t`. Reading these is the foundational SELinux skill.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/lsZ-lab
ls -l /etc/hosts /etc/hostname 2>&1 | tee task02-warmup.log
grep -c "root root" task02-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Use `ls -Z` to display SELinux contexts for files and directories in `/etc`, then confirm the **type** field by querying `semanage fcontext`.

### d) Main Command Block

```bash
cd /tmp/lsZ-lab
ls -Z /etc/hostname /etc/hosts /etc/resolv.conf /etc/shadow 2>&1 | tee task02-contexts.txt
ls -Zd /etc /etc/ssh /etc/systemd >> task02-contexts.txt 2>&1
cat task02-contexts.txt

echo "---"
semanage fcontext -l 2>/dev/null | grep -E "^/etc/hostname|^/etc/hosts|^/etc/shadow" | tee task02-semanage.txt
echo "---"

mkdir -p task02-target
echo "fake web content" > task02-target/index.html
ls -Z task02-target task02-target/index.html
matchpathcon /var/www/html/index.html 2>/dev/null || echo "matchpathcon: not installed"

echo "context types found: $(awk '{print $1}' task02-contexts.txt | awk -F: '{print $3}' | sort -u | tr '\n' ' ')"
```

### e) Human-Readable Breakdown

- `ls -Z FILE` — show the SELinux context (`user:role:type:level`).
- `ls -Zd DIR` — context for the directory itself.
- `semanage fcontext -l | grep PATH` — show the **policy rule** that defines the type for a path pattern. This is the "should be" lookup.
- `matchpathcon PATH` — show what context **policy says** the path should have, even if the path does not yet exist.
- `awk '{print $1}' | awk -F:` — extract the type field by splitting the context string on `:`.

### f) Reading It Left to Right

`ls -Z /etc/hostname /etc/hosts /etc/resolv.conf /etc/shadow 2>&1 | tee task02-contexts.txt`

A line of output:

```
system_u:object_r:net_conf_t:s0 /etc/hostname
   │         │         │      │       │
   user     role      type   level   path
```

| Field | Common values on RHEL |
|---|---|
| `user` | `system_u`, `unconfined_u`, `staff_u` |
| `role` | `object_r` (for files), `system_r` (for processes) |
| `type` | `etc_t`, `net_conf_t`, `shadow_t`, `httpd_config_t` — **this is the one you fix** |
| `level` | `s0` (default), `s0-s0:c0.c1023` (MLS systems) |

### g) The Story

SELinux has a reputation for being scary, but 95% of RHCSA SELinux work is "read the type, compare to what the policy expects, fix it with `semanage fcontext` + `restorecon`." `ls -Z` is the **first** command you run when an app can't read its own config or a web server returns 403 on a file you just copied.

### h) Expected Output

```text
system_u:object_r:net_conf_t:s0   /etc/hostname
system_u:object_r:net_conf_t:s0   /etc/hosts
system_u:object_r:net_conf_t:s0   /etc/resolv.conf
system_u:object_r:shadow_t:s0     /etc/shadow
system_u:object_r:etc_t:s0        /etc
system_u:object_r:etc_t:s0        /etc/ssh
system_u:object_r:systemd_unit_file_t:s0  /etc/systemd
---
/etc/hostname    system_u:object_r:net_conf_t:s0
/etc/hosts       system_u:object_r:net_conf_t:s0
/etc/shadow      system_u:object_r:shadow_t:s0
---
unconfined_u:object_r:user_tmp_t:s0  task02-target/
unconfined_u:object_r:user_tmp_t:s0  task02-target/index.html
/var/www/html/index.html  system_u:object_r:httpd_sys_content_t:s0
context types found: etc_t net_conf_t shadow_t systemd_unit_file_t user_tmp_t
```

Notice: the `task02-target/index.html` file inside `/tmp` has type `user_tmp_t`. If you copied it to `/var/www/html`, Apache (running as `httpd_t`) would be **denied** read access until you `restorecon -Rv /var/www/html`. This is the most common RHCSA SELinux trap.

### i) Switches Table

| Token | Meaning |
|---|---|
| `ls -Z` | Show SELinux context |
| `ls -Zd` | Context of directory itself |
| `semanage fcontext -l` | List all path → type policy rules |
| `matchpathcon PATH` | Show what type policy expects for path |
| `awk '{print $1}'` | First whitespace-separated field |
| `awk -F: '{print $3}'` | Field 3 with `:` as separator |
| `sort -u` | Unique sorted lines |
| `tr '\n' ' '` | Join with spaces |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | SELinux context | `user:role:type:level` |
|   | The "type" | `etc_t`, `net_conf_t`, `httpd_sys_content_t` — the field that matters |
|   | `ls -Z` | Reads the file's current context |
|   | `matchpathcon` | Reads policy's expected context for a path |
|   | `semanage fcontext -l` | Lists all policy rules |
|   | `unconfined_u` | Default user context for files you create as a regular user |
|   | `system_u` | Default user context for system files |
|   | `user_tmp_t` | Default type for files in `/tmp` (limited reach) |
| 🪤 **Trap Risk (T01)** | Setting permissive instead of fixing context | If an app fails on a `/var/www/html` file just copied from `/tmp`, the file is still `user_tmp_t`. Fix: `restorecon -Rv /var/www/html`. Do NOT `setenforce 0` |

### k) 🧹 Cleanup

```bash
LAB=lab06
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    Reading SELinux file contexts with ls -Z
COMMANDS: ls -Z, ls -Zd, semanage fcontext -l, matchpathcon
TRAPS:    T01 (permissive ≠ fix)
MISSED:   —
NEXT:     task3 — ps -eZ + semanage/restorecon (T02)
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/lsZ-lab
rm -rf task02-target
rm -f task02-warmup.log task02-contexts.txt task02-semanage.txt
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `ls -Z` shows `?` for context | SELinux disabled or context lost — run `sestatus` |
| `semanage: command not found` | `sudo dnf install policycoreutils-python-utils` |
| `matchpathcon` shows wrong type | Your local policy may be stale — `restorecon -Rv` rebuilds |
| Context has `unconfined_u` everywhere | Normal for files created by a logged-in user; RHEL defaults |

### m) STOP

> **STOP — paste output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| SELinux still enforcing | `getenforce` | Should say `Enforcing` (or note Permissive/Disabled in journal) |
| File contexts unchanged on `/etc` | `ls -Z /etc/hostname` | Should still be `net_conf_t` |
| Journal task2 | `cat /root/rhcsa_journal/lab06/task2/done.txt` | Reboot-proof |

---

## Task 3 — Tie It Together: `ps -eZ` + `semanage fcontext` + `restorecon`

### a) Directory Context

**Practice directory this task:** `/etc`
We will create a fake `/etc/` config file under our sandbox, register a persistent context rule for the sandbox path, and prove `restorecon` applies it. This is the exact RHCSA muscle memory.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/lsZ-lab
ls -Z /etc/hostname /etc/hosts /etc/resolv.conf | tee task03-warmup.log
grep -c "net_conf_t" task03-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Connect three SELinux artifacts: **process contexts** (`ps -eZ`), **file contexts** (`ls -Z`), and **policy rules** (`semanage fcontext` + `restorecon`).

### d) Main Command Block

```bash
cd /tmp/lsZ-lab
ps -eZ | head -n 10 | tee task03-procs.txt
echo "---"
ps -eZ | grep -E "sshd|systemd" | head -n 5

mkdir -p /tmp/lsZ-lab/fake-etc
echo "ServerName fake.example.com" > /tmp/lsZ-lab/fake-etc/httpd.conf
ls -Z /tmp/lsZ-lab/fake-etc/httpd.conf

semanage fcontext -a -t httpd_config_t "/tmp/lsZ-lab/fake-etc(/.*)?" 2>&1 | tee task03-semanage.txt
echo "registered exit: ${PIPESTATUS[0]}"

restorecon -Rv /tmp/lsZ-lab/fake-etc 2>&1 | tee task03-restorecon.txt
echo "restorecon exit: ${PIPESTATUS[0]}"

ls -Z /tmp/lsZ-lab/fake-etc/httpd.conf
matchpathcon /tmp/lsZ-lab/fake-etc/httpd.conf

semanage fcontext -d "/tmp/lsZ-lab/fake-etc(/.*)?"
restorecon -Rv /tmp/lsZ-lab/fake-etc
ls -Z /tmp/lsZ-lab/fake-etc/httpd.conf
```

### e) Human-Readable Breakdown

- `ps -eZ` — list every process with its SELinux context (`system_u:system_r:sshd_t:s0-s0:c0.c1023`).
- `mkdir -p fake-etc; echo ... > httpd.conf` — create a fake config file.
- `ls -Z` initially shows `user_tmp_t` (because `/tmp` defaults).
- `semanage fcontext -a -t httpd_config_t "PATH(/.*)?"` — register a **persistent** policy rule that says "this path and everything inside should be type `httpd_config_t`." The `(/.*)?` regex covers the directory and all descendants.
- `restorecon -Rv PATH` — actually **apply** the policy rule, relabeling existing files. **This is the half people forget (T02).**
- `ls -Z` after — confirm the type changed to `httpd_config_t`.
- `semanage fcontext -d "PATH(/.*)?"` + `restorecon -Rv` — remove the rule and relabel back, leaving no policy debris.

### f) Reading It Left to Right

`semanage fcontext -a -t httpd_config_t "/tmp/lsZ-lab/fake-etc(/.*)?"`

1. `semanage` — SELinux management CLI.
2. `fcontext` — manage **file context** rules (vs `port`, `login`, `boolean`).
3. `-a` — **add** a rule (vs `-d` delete, `-m` modify, `-l` list).
4. `-t httpd_config_t` — assign this type.
5. `"/tmp/lsZ-lab/fake-etc(/.*)?"` — path **regex**. `(/.*)?` = "optionally followed by `/anything`." Covers the dir and all contents.

### g) The Story

The full RHCSA SELinux flow is exactly this three-line dance:

```
semanage fcontext -a -t TYPE "PATH(/.*)?"   # tell policy
restorecon -Rv PATH                          # apply policy
ls -Z PATH                                   # verify
```

The catastrophic bug (T02) is running the `semanage` line, walking away, and never running `restorecon`. The policy rule is registered in `/etc/selinux/targeted/contexts/files/file_contexts.local` but **nothing on disk has been relabeled**. A reboot eventually relabels, but the exam grader runs in seconds, not after a reboot.

### h) Expected Output

```text
LABEL                              PID TTY          TIME CMD
system_u:system_r:init_t:s0          1 ?        00:00:01 systemd
system_u:system_r:kernel_t:s0        2 ?        00:00:00 kthreadd
...
---
system_u:system_r:sshd_t:s0-s0:c0.c1023  ...
system_u:system_r:init_t:s0              ...

unconfined_u:object_r:user_tmp_t:s0  /tmp/lsZ-lab/fake-etc/httpd.conf
   ↑ before semanage

Restorecon reset /tmp/lsZ-lab/fake-etc context unconfined_u:object_r:user_tmp_t:s0->unconfined_u:object_r:httpd_config_t:s0
Restorecon reset /tmp/lsZ-lab/fake-etc/httpd.conf context unconfined_u:object_r:user_tmp_t:s0->unconfined_u:object_r:httpd_config_t:s0
restorecon exit: 0

unconfined_u:object_r:httpd_config_t:s0  /tmp/lsZ-lab/fake-etc/httpd.conf
   ↑ after semanage + restorecon — policy now matches reality

/tmp/lsZ-lab/fake-etc/httpd.conf  system_u:object_r:httpd_config_t:s0

unconfined_u:object_r:user_tmp_t:s0  /tmp/lsZ-lab/fake-etc/httpd.conf
   ↑ after deletion + restorecon — back to default
```

### i) Switches Table

| Token | Meaning |
|---|---|
| `ps -eZ` | All processes with SELinux contexts |
| `semanage fcontext -a -t TYPE PATH` | Add policy rule |
| `semanage fcontext -d PATH` | Delete policy rule |
| `semanage fcontext -l` | List rules |
| `semanage fcontext -m -t TYPE PATH` | Modify existing rule |
| `restorecon -R` | Recursive |
| `restorecon -v` | Verbose (show what was changed) |
| `restorecon -Rv PATH` | Apply policy, recursive + verbose |
| `matchpathcon PATH` | Show expected context for path |
| `(/.*)?` | Optional `/` + anything (regex covering descendants) |
| `${PIPESTATUS[0]}` | Exit status of first pipeline stage |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `ps -eZ` | Process contexts (`system_r` role) |
|   | `ls -Z` | File contexts (`object_r` role) |
|   | Type enforcement | Process type + file type pair must be allowed by policy |
|   | `semanage fcontext -a` | Persistent policy rule |
|   | `restorecon -Rv` | Apply policy to disk |
|   | Three-step flow | semanage → restorecon → verify |
|   | `(/.*)?` regex | Covers a directory and all descendants |
| 🪤 **Trap Risk (T02)** | semanage fcontext without restorecon -Rv afterward | Rule is registered but files are still mislabeled. Always pair the two commands — make it muscle memory |
| 🪤 **Trap Risk (T01)** | Setting permissive instead of fixing context | If `restorecon` did not fix it, *read the actual AVC denial* with `ausearch -m avc -ts recent`. Do not reach for `setenforce 0` |

### k) 🧹 Cleanup

```bash
LAB=lab06
TASK=task3
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF
cat > "$JDIR/notes.txt" <<'EOF'
TOPIC:    ps -eZ, semanage fcontext -a/-d, restorecon -Rv
COMMANDS: ps -eZ, semanage fcontext, restorecon, matchpathcon
TRAPS:    T01 + T02 (both rehearsed)
MISSED:   —
NEXT:     Lab 07 — touch + timestamps (/boot practice dir)
EOF
echo "Journal written: $(ls -la $JDIR)"

semanage fcontext -d "/tmp/lsZ-lab/fake-etc(/.*)?" 2>/dev/null
rm -rf /tmp/lsZ-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `semanage fcontext -a` says "already defined" | Use `-m` to modify instead of `-a` |
| `restorecon` does not change anything | Verify the path regex with `semanage fcontext -l \| grep PATH` |
| `ls -Z` still shows old type after `restorecon` | The semanage rule is wrong; check `matchpathcon` says the expected type |
| `ausearch: not found` | `sudo dnf install audit` |
| App still denied after fix | Read the AVC: `ausearch -m avc -ts recent`; the type may need different perms |

### m) STOP

> **STOP — paste output before declaring Lab 06 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Policy rule REMOVED | `semanage fcontext -l \| grep fake-etc` (empty) | Confirms no leftover policy debris |
| Sandbox removed | `test -d /tmp/lsZ-lab \|\| echo CLEAN` | Confirms `rm -rf` worked |
| All 3 journal entries | `find /root/rhcsa_journal/lab06 -name done.txt \| wc -l` (expect 3) | Reboot-proof study record |
| SELinux still enforcing | `getenforce` | Confirms we did NOT fall for T01 |

> **Reboot question:** "If we rebooted now, would the `httpd_config_t` change on `fake-etc` have survived?" — Answer: yes, **as long as the semanage rule still existed**. That is the whole point of `semanage fcontext` (vs `chcon`, which is non-persistent). Since we deleted the rule, the next `restorecon` reverts the labels. Boot or no boot.

---

## 🪤 Trap Registry Update — End of Lab 06

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T01 | SELinux | ✅ | — |
| T02 | SELinux | ✅ | — |

Next lab (07) traps: **T07** (Wrong UUID in fstab — always copy-paste from blkid) · **T43** (Getting stuck >10 min on one task).

3-lab trap window (05+06+07 once complete): T41, T43, T01, T02, T07 = **5 traps minimum** ✓

---

## 🎓 What You Now Own

After this lab you can:

1. Read every column of `ls -l` on autopilot.
2. Identify SELinux contexts with `ls -Z` and `ls -Zd`.
3. Connect process contexts (`ps -eZ`) to file contexts (`ls -Z`).
4. Add a persistent context with `semanage fcontext -a -t TYPE "PATH(/.*)?"`.
5. **Always** pair `semanage fcontext` with `restorecon -Rv` (T02 lifesaver).
6. Refuse the trap of `setenforce 0` as a "fix" (T01 lifesaver).
7. Roll back a context with `semanage -d` + `restorecon -Rv`.
8. Diagnose denials with `matchpathcon` and `ausearch -m avc -ts recent`.
