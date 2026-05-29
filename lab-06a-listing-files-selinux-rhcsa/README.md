# Lab 06a: Listing Files & SELinux Contexts (RHCSA) — `ls -l/-lZ/-dZ`, `matchpathcon`, `restorecon`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `06a` (RHCSA) → `06b` (Ansible) → `06c` (Verify)
- **Career arcs covered:** RHCSA EX200 (SELinux labels, `ls -lZ`, `semanage fcontext`, `restorecon`), RHCE EX294 (`community.general.sefcontext`, `ansible.posix.selinux`), SRE (postmortem-driven SELinux fixes — 403 with rwx, AVC denials), RHCA RH415 (SELinux audit and remediation)
- **Prerequisite:** Lab 05 (navigation, `pwd`, `cd`, `ls`)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical, Task 2 contrast)
- **Practice Directory (rotation #06):** `/etc`
- **Sandbox:** `/tmp/listing-lab/` + `/srv/www-lab-06/`
- **Traps rehearsed this lab:** **T01** (using `chcon` when a permanent fix is needed — survives until `restorecon -R /` runs) · **T02** (forgetting the `'PATH(/.*)?'` regex when adding fcontext for a directory tree) · **T03** (forgetting `restorecon` after `semanage fcontext -a`)

> **This lab's practice directory is: `/etc`** — every task references it in at least two commands. `/srv/www-lab-06/` is the sandbox where we deliberately mislabel and fix.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T01 T02 T03"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 SELinux quick-look on /etc:"
ls -dZ /etc
sestatus | head -3
```

> **STOP — confirm `getenforce` prints `Enforcing` before continuing. Permissive mode will lie to you about labels.**

---

## 🎯 Objective

Read the 10 fields of an `ls -l` listing fluently, read the 4 fields of an `ls -lZ` SELinux context fluently, and fix a mislabeled web file using the **permanent** RHCSA path (`semanage fcontext` → `restorecon`). By the end you can glance at any `ls -lZ` line and decode both DAC (mode, owner, group) and MAC (user:role:type:level) in one pass — and you know exactly why `chcon` is the wrong tool for a permanent fix.

---

## 🧠 Concept: `ls -l` vs `ls -lZ` — DAC and MAC on One Line

`ls -l` shows **Discretionary Access Control (DAC)**: mode, owner, group, size, mtime. `ls -lZ` adds **Mandatory Access Control (MAC)**: the SELinux context column that sits between the group and the size.

```
   ┌──────────────────────────────────────────────────────────────────────────┐
   │  ls -lZ /etc/passwd                                                      │
   ├──────────────────────────────────────────────────────────────────────────┤
   │  -rw-r--r--. 1 root root system_u:object_r:passwd_file_t:s0 2456 ...     │
   │  │           │ │    │    │                                  │            │
   │  │           │ │    │    └─ SELinux context (4 fields)      │            │
   │  │           │ │    └─ group (DAC)                          │            │
   │  │           │ └─ owner (DAC)                                │            │
   │  │           └─ link count                                    │            │
   │  └─ mode (type char + rwx triplets)                            │            │
   │                                                                └─ mtime    │
   └──────────────────────────────────────────────────────────────────────────┘
```

The **type** field inside the context (e.g. `passwd_file_t`, `httpd_sys_content_t`) is what matters 95% of the time. A process running with type `httpd_t` can read files of type `httpd_sys_content_t` — that's the policy match. A mislabeled web file (type `var_t` instead of `httpd_sys_content_t`) gets Permission denied **EVEN IF** the DAC mode says rwx for everyone. SELinux is independent of DAC.

The single biggest invisible bug in SELinux troubleshooting is running plain `ls -l` and never seeing the context column. The fix is one habit: **always add `-Z`** when a service won't start, a file isn't readable, or an AVC denial appears in the logs.

---

## 📚 Listing & SELinux Reference (everything you need for Tasks 1–2)

| Task | Command | Notes |
|---|---|---|
| Long listing (DAC) | `ls -l PATH` | 10 fields: mode, links, owner, group, size, mtime, name |
| Long + SELinux (MAC) | `ls -lZ PATH` | Adds context column before size |
| Directory itself | `ls -ldZ /etc/` | `-d` lists the dir, not its contents |
| Policy prediction | `matchpathcon PATH` | "What context SHOULD this path have?" |
| Declare permanent rule | `semanage fcontext -a -t TYPE '/path(/.*)?'` | Survives reboot |
| Apply policy (dry-run) | `restorecon -nv PATH` | `-n` = no changes, `-v` = verbose |
| Apply policy (for real) | `restorecon -Rv PATH` | `-R` = recursive, `-v` = verbose |
| Temporary label | `chcon -t TYPE PATH` | Lost on relabel — NOT permanent |
| SELinux mode | `getenforce` | `Enforcing` / `Permissive` / `Disabled` |
| Full status | `sestatus` | Mode + policy + loaded modules |

> **Rule of SELinux listing:** Pick `ls -lZ` whenever a service won't start, a file isn't readable, or an AVC denial appears. Plain `ls -l` hides the MAC column entirely.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i

# 0) Confirm policycoreutils-python-utils is installed (semanage lives here)
rpm -q policycoreutils-python-utils || sudo dnf install -y policycoreutils-python-utils

# 1) Create the web sandbox with a deliberately wrong label
sudo mkdir -p /srv/www-lab-06
echo "lab06a content" | sudo tee /srv/www-lab-06/index.html

# 2) Create the /tmp scratch sandbox
mkdir -p /tmp/listing-lab
cd /tmp/listing-lab

cat > /tmp/listing-lab/THIS_DIRECTORY.txt <<'EOF'
/etc — System configuration directory

/etc holds persistent configuration for every service and system policy.
Unlike /tmp, nothing here is cleared on reboot. SELinux assigns distinct
types to /etc files — passwd_file_t for /etc/passwd, shadow_t for
/etc/shadow, etc_t for the directory itself.

Why RHCSA cares: every "inspect the label on /etc/X" task lives here.
Reading ls -lZ output on /etc files is the foundation of SELinux
troubleshooting on the EX200 exam.
EOF

cat /tmp/listing-lab/THIS_DIRECTORY.txt
ls -lZ /srv/www-lab-06/
echo "exit was: $?"
```

You should see something like `unconfined_u:object_r:var_t:s0` on `/srv/www-lab-06/index.html`. That's the **wrong** label if we wanted this to serve as a web root — Apache expects `httpd_sys_content_t`. We'll deliberately use that mismatch as the lab's running example.

> **STOP — paste output before Task 1.**

---

## Task 1 — Read `ls -l`, `ls -lZ`, and `ls -dZ`: decode DAC and MAC columns

**Practice directory this task:** `/etc` · System configuration directory — every command in this task targets `/etc` so you build the muscle memory of reading real system file labels, not sandbox placeholders.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -la /etc/passwd /etc/shadow                    2>&1 | tee /tmp/listing-lab/warmup-pre.txt
getenforce | tee -a /tmp/listing-lab/warmup-pre.txt
ls -dZ /etc/                                      2>&1 | tee -a /tmp/listing-lab/warmup-pre.txt
test -f /etc/passwd && echo "passwd OK"
stat -c '%n mode=%a' /etc/passwd /etc/shadow
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 05: `ls` without flags is the quick glance; `ls -l` is the audit form. We add `-Z` here because SELinux context is the column that separates a passing EX200 answer from a silent failure.

### Purpose

Decode the 10-column `ls -l` output, read the 4-field SELinux context from `ls -lZ`, compare the contexts on `/etc/passwd` vs `/etc/shadow`, and capture the listing to the journal.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -la /etc/passwd /etc/shadow` | Snapshot **before** the `-Z` pass so we can see DAC-only vs DAC+MAC side by side |
| `getenforce` | Pre-flight — Permissive mode hides real enforcement behavior |
| `ls -dZ /etc/` | Inspects the **directory itself** (not contents) — the `-d` flag in action |
| `test -f /etc/passwd` | Guards the capture block — only runs if the target exists |
| `2>&1 \| tee` | Captures each listing into `task1/op.txt` for the journal |
| `$(date -Is)` | Stamps the journal `notes.txt` with the completion time |

### Main command block

```bash
cd /tmp/listing-lab
mkdir -p /tmp/listing-lab/task1

# ── Part A: DAC — the 10 fields of ls -l ─────────────────────────
ls -l /etc/passwd /etc/shadow /etc/hostname
ls -ld /etc/
ls -l /etc | head -10

# ── Part B: MAC — add the SELinux context column ───────────────────
ls -lZ /etc/passwd /etc/shadow /etc/hostname
ls -dZ /etc/
ls -lZ /etc | head -10

# Capture everything
{
  echo "=== ls -l /etc/passwd ===";      ls -l /etc/passwd
  echo "=== ls -lZ /etc/passwd ===";     ls -lZ /etc/passwd
  echo "=== ls -lZ /etc/shadow ===";     ls -lZ /etc/shadow
  echo "=== ls -dZ /etc/ ===";           ls -dZ /etc/
  echo "=== ls -lZ sandbox ===";         ls -lZ /srv/www-lab-06/index.html
} 2>&1 | tee /tmp/listing-lab/task1/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. Run `ls -l` on three `/etc` files to decode the 10 DAC fields (mode, links, owner, group, size, mtime, name).
2. Run `ls -ld /etc/` to inspect the **directory itself** — the `-d` flag prevents listing every file inside `/etc`.
3. Run `ls -lZ` on the same targets to add the SELinux context column.
4. Compare `/etc/passwd` (`passwd_file_t`) vs `/etc/shadow` (`shadow_t`) — same owner/group, different SELinux types.
5. Capture all output to `task1/op.txt` for the journal.

### Reading it left to right

- `ls -l /etc/passwd` — long format (DAC only); `ls -lZ` adds the context column between group and size.
- `ls -dZ /etc/` — `-d` lists the directory entry itself; `-Z` adds its context (`etc_t`).
- `system_u:object_r:passwd_file_t:s0` — user:role:**type**:level; the **type** is what policy enforces.

A single `ls -lZ` row has these fields, in order:

| # | Field | Example | Meaning |
|---|---|---|---|
| 1 | Mode | `-rw-r--r--.` | Type (1 char) + DAC mode (9 chars) + SELinux dot |
| 2 | Link count | `1` | Number of hard links |
| 3 | Owner | `root` | DAC owner |
| 4 | Group | `root` | DAC group |
| 5 | Context | `system_u:object_r:passwd_file_t:s0` | SELinux user:role:type:level |
| 6 | Size | `2456` | Bytes |
| 7–9 | mtime | `May 27 14:03` | Month, day, year/time |
| 10 | Name | `/etc/passwd` | Path |

Field 1 character meanings: `-` regular file, `d` directory, `l` symlink, `c` character device, `b` block device, `s` socket, `p` named pipe.

### The story

A grader points at one line of `ls -lZ` and asks "what is this?" Your answer is the full decode: DAC mode, owner, group, **and** the four SELinux context fields. `/etc/passwd` (`passwd_file_t`) and `/etc/shadow` (`shadow_t`) share the same owner but carry **different types** because policy restricts which processes may access each — reading both in one `ls -lZ` line is the skill the EX200 expects.

### Expected output

```text
$ ls -lZ /etc/passwd
-rw-r--r--. 1 root root system_u:object_r:passwd_file_t:s0 2456 May 27 14:03 /etc/passwd

$ ls -lZ /etc/shadow
----------. 1 root root system_u:object_r:shadow_t:s0 1234 May 27 14:03 /etc/shadow

$ ls -dZ /etc/
drwxr-xr-x. 90 root root system_u:object_r:etc_t:s0 8192 May 27 14:03 /etc

$ ls -lZ /srv/www-lab-06/index.html
-rw-r--r--. 1 root root unconfined_u:object_r:var_t:s0 15 May 27 14:05 /srv/www-lab-06/index.html
exit was: 0
```

Notice `/etc/shadow` is mode `000` — readable only via group/setuid. And the sandbox file is `var_t` — wrong for a web root. Both facts are invisible without `-Z`.

### Switches

| Token | Meaning |
|---|---|
| `ls -l FILE` | Long format — 10 DAC fields |
| `ls -lZ FILE` | Long format + SELinux context column |
| `ls -ld DIR` | List the directory itself, not its contents |
| `ls -dZ DIR` | Directory itself + SELinux context |
| `getenforce` | Current SELinux mode (`Enforcing`/`Permissive`/`Disabled`) |
| `sestatus` | Full SELinux status (mode + policy + loaded modules) |
| `set -o pipefail` | Pipeline exit = first non-zero stage |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | DAC | Discretionary Access Control — mode, owner, group |
|   | MAC | Mandatory Access Control — SELinux context (type enforcement) |
|   | Context field: user | SELinux user (`system_u`, `unconfined_u`) — not the Linux user |
|   | Context field: role | `object_r` for files, `system_r` for processes |
|   | Context field: type | **THE KEY FIELD** — `passwd_file_t`, `shadow_t`, `httpd_sys_content_t` |
|   | Context field: level | MLS/MCS sensitivity (`s0` on most RHEL servers) |
|   | `ls -ld DIR` | Inspect the directory itself, not its contents |
| 🪤 | **Trap Risk T01** | Running plain `ls -l` and missing SELinux mismatches — always add `-Z` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Transcript captured | `test -f /tmp/listing-lab/task1/op.txt && echo ok` | Evidence of the listing session |
| passwd context present | `grep -c 'passwd_file_t' /tmp/listing-lab/task1/op.txt` | Confirms `-Z` was used on `/etc/passwd` |
| shadow context present | `grep -c 'shadow_t' /tmp/listing-lab/task1/op.txt` | Confirms `-Z` was used on `/etc/shadow` |
| Journal evidence | `ls /root/rhcsa_journal/lab-06a/task1/` | The op.txt copy persists under `/root/` |

> **Reboot reasoning:** `/etc` labels survive reboot — they are on disk and loaded from policy at boot. The thing that **must** survive is the **evidence** of your listing session — that goes in the journal under `/root/`, not `/tmp/`.

### Journal write — BEFORE cleanup

```bash
LAB=lab-06a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/listing-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ls -l, ls -lZ, ls -dZ — DAC and MAC column decode
COMMANDS: ls -l, ls -lZ, ls -ld, ls -dZ, getenforce, sestatus
TRAPS:    T01 (rehearsed: used -Z on every listing)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — semanage fcontext + restorecon permanent fix
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/listing-lab/task1
ls /tmp/listing-lab
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `ls -lZ` has no context column | SELinux is disabled — check `getenforce`; re-enable via `/etc/selinux/config` and reboot |
| `getenforce` prints `Permissive` | `sudo setenforce 1` (temporary) or edit `/etc/selinux/config` and reboot |
| `ls -lZ /etc/shadow` shows `Permission denied` | Run with `sudo` — shadow is mode `000` |
| Context column shows `?` | SELinux policy not loaded — run `sestatus` |

> **STOP — paste the output of `cat $JDIR/done.txt` and the final `grep -c 'shadow_t' $JDIR/evidence.txt` before starting Task 2.**

---

## Task 2 — Permanent label fix: `semanage fcontext`, `restorecon`, and the `chcon` contrast (T02 T03)

**Practice directory this task:** `/etc` · (`/etc/selinux/targeted/contexts/files/file_contexts.local` is where rules persist) — and `/srv/www-lab-06/` is the sandbox where we deliberately mislabel and fix.

### 🔁 Warm-Up — commands woven into Task 2

```bash
pwd
ls -lZ /srv/www-lab-06/                           2>&1 | tee /tmp/listing-lab/warmup-task2.txt
matchpathcon /srv/www-lab-06/index.html            2>&1 | tee -a /tmp/listing-lab/warmup-task2.txt
test -d /srv/www-lab-06 && echo "sandbox OK"
rpm -q policycoreutils-python-utils
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `matchpathcon PATH` asks the policy "what context SHOULD this path have?" That's the diagnostic for "is my file labeled correctly?" — we use it before and after every label fix.

### Purpose

Mark `/srv/www-lab-06` as web content with `semanage fcontext -a -t httpd_sys_content_t`, dry-run with `restorecon -nv`, apply with `restorecon -Rv`, then **contrast** with a temporary `chcon` fix on a parallel test file to demonstrate T03. Verify with `ls -lZ` and `matchpathcon`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -lZ /srv/www-lab-06/` | Snapshot **before** the fix — confirms `var_t` (wrong label) |
| `matchpathcon /srv/www-lab-06/index.html` | Shows what policy **currently** expects (still `var_t` until we add the rule) |
| `test -d /srv/www-lab-06` | Guards every `restorecon` call — only runs if sandbox exists |
| `rpm -q policycoreutils-python-utils` | Confirms `semanage` is available before we need it |
| `2>&1 \| tee` | Captures every step into `task2/op.txt` for the journal |

### Main command block

```bash
cd /tmp/listing-lab
mkdir -p /tmp/listing-lab/task2

# ── Part A: confirm the wrong label (before) ───────────────────────
ls -lZ /srv/www-lab-06/
matchpathcon /srv/www-lab-06/index.html

# ── Part B: declare the permanent policy rule ────────────────────
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www-lab-06(/.*)?'
sudo semanage fcontext -l | grep '/srv/www-lab-06'

# ── Part C: dry-run first (T02 rehearsal — see what WOULD change) ─
sudo restorecon -nv /srv/www-lab-06/

# ── Part D: apply for real ─────────────────────────────────────────
sudo restorecon -Rv /srv/www-lab-06/

# ── Part E: verify the permanent fix ───────────────────────────────
ls -lZ /srv/www-lab-06/
matchpathcon /srv/www-lab-06/index.html

# ── Part F: chcon contrast — temporary fix on a parallel test file ──
echo "chcon test" | sudo tee /srv/www-lab-06/chcon-test.html
sudo chcon -t httpd_sys_content_t /srv/www-lab-06/chcon-test.html
ls -lZ /srv/www-lab-06/chcon-test.html
echo "Now run restorecon — chcon label will be overwritten (T03):"
sudo restorecon -v /srv/www-lab-06/chcon-test.html
ls -lZ /srv/www-lab-06/chcon-test.html

# Capture everything
{
  echo "=== before ls -lZ ===";          ls -lZ /srv/www-lab-06/
  echo "=== rule stored ===";            sudo semanage fcontext -l | grep '/srv/www-lab-06'
  echo "=== restorecon dry-run ===";     sudo restorecon -nv /srv/www-lab-06/
  echo "=== restorecon apply ===";       sudo restorecon -Rv /srv/www-lab-06/
  echo "=== after ls -lZ ===";           ls -lZ /srv/www-lab-06/
  echo "=== matchpathcon ===";           matchpathcon /srv/www-lab-06/index.html
  echo "=== chcon contrast ===";         ls -lZ /srv/www-lab-06/chcon-test.html
} 2>&1 | tee /tmp/listing-lab/task2/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

**Part A — wrong label.** Confirm `index.html` is `var_t`; `matchpathcon` agrees until we add the rule.

**Part B — declare the rule.** `semanage fcontext -a -t httpd_sys_content_t '/srv/www-lab-06(/.*)?'` stores a permanent rule in `file_contexts.local`. The regex `(/.*)?` covers the directory AND everything under it.

**Part C — dry-run then apply.** `restorecon -nv` shows what would change (T02); `restorecon -Rv` applies recursively with verbose output.

**Part D — verify and chcon contrast (T03).** `ls -lZ` and `matchpathcon` should show `httpd_sys_content_t`. Then label a parallel file with `chcon` and watch `restorecon -v` overwrite it with the permanent policy rule.

### Reading it left to right

- `semanage fcontext -a -t httpd_sys_content_t '/srv/www-lab-06(/.*)?'` — `semanage` (SELinux policy tool), `fcontext` (file-context sub-command), `-a` (add rule), `-t TYPE` (set type), quoted regex path.
- `restorecon -nv /srv/www-lab-06/` — `-n` = dry-run (no changes), `-v` = verbose (print what would change).
- `restorecon -Rv /srv/www-lab-06/` — `-R` = recursive, `-v` = verbose (print every relabel).
- `chcon -t httpd_sys_content_t FILE` — sets type on one file; **temporary** — lost on next `restorecon` or relabel.
- `matchpathcon PATH` — asks policy "what context SHOULD this path have?" — the diagnostic for label correctness.

The regex `(/.*)?` is the convention: match the directory itself OR the directory followed by any path. Use it on every `semanage fcontext -a` of a directory tree.

### The story

A grader's question: "Apache returns 403 on `/srv/www-lab-06/`. Fix it without changing DAC." The path is `ls -lZ` (see `var_t`) → `semanage fcontext -a` → `restorecon -Rv`. The page works; you haven't touched chmod.

The `chcon` contrast demonstrates T03: a junior admin runs `chcon`, the page works, they declare victory — then the next `restorecon` or relabel reverts the label. The permanent fix is always `semanage fcontext` + `restorecon`.

### Expected output

```text
$ ls -lZ /srv/www-lab-06/index.html
-rw-r--r--. 1 root root unconfined_u:object_r:var_t:s0 15 May 27 14:05 /srv/www-lab-06/index.html

$ sudo restorecon -nv /srv/www-lab-06/
Would relabel /srv/www-lab-06/index.html from unconfined_u:object_r:var_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0

$ sudo restorecon -Rv /srv/www-lab-06/
Relabeled /srv/www-lab-06/index.html from unconfined_u:object_r:var_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0

$ ls -lZ /srv/www-lab-06/
total 4
-rw-r--r--. 1 root root unconfined_u:object_r:httpd_sys_content_t:s0 15 May 27 14:05 index.html

$ matchpathcon /srv/www-lab-06/index.html
/srv/www-lab-06/index.html  system_u:object_r:httpd_sys_content_t:s0
exit was: 0
```

> Notice: after Part F, `chcon-test.html` keeps `httpd_sys_content_t` because the **permanent rule** from Part B now governs that path. The `chcon` label was overwritten by `restorecon` applying the policy rule — that's T03 in action.

### Switches

| Token | Meaning |
|---|---|
| `semanage fcontext -a -t TYPE PATH` | Add a permanent fcontext rule |
| `semanage fcontext -l` | List all fcontext rules |
| `semanage fcontext -d PATH` | Delete a rule |
| `restorecon -nv PATH` | Dry-run: show what would change, no changes |
| `restorecon -Rv PATH` | Apply policy recursively, verbose |
| `chcon -t TYPE PATH` | Set type on a file — TEMPORARY |
| `matchpathcon PATH` | "What context SHOULD this path have?" |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | Permanent fix | `semanage fcontext -a` + `restorecon -Rv` |
|   | Temporary fix | `chcon -t TYPE PATH` (lost on relabel) |
|   | Path regex convention | `'/path(/.*)?'` covers dir + everything under it |
|   | `file_contexts.local` | Where custom rules persist on disk |
|   | Dry-run discipline | `restorecon -nv` before `restorecon -Rv` — see before you apply |
|   | 403 with rwx | Classic SELinux symptom — DAC is fine, MAC says no |
| 🪤 | **Trap Risk T02** | `restorecon` without `-R` only fixes the leaf — always use `-Rv` on a tree |
| 🪤 | **Trap Risk T03** | `chcon` is reset on next `restorecon` or relabel — use `semanage fcontext` |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| fcontext rule stored | `sudo semanage fcontext -l \| grep -c '/srv/www-lab-06'` | Must return `1` |
| Label applied | `ls -Z /srv/www-lab-06/index.html \| grep -c 'httpd_sys_content_t'` | Must return `1` |
| matchpathcon agrees | `matchpathcon /srv/www-lab-06/index.html \| grep -c 'httpd_sys_content_t'` | Must return `1` |
| Rule on disk | `sudo grep -c '/srv/www-lab-06' /etc/selinux/targeted/contexts/files/file_contexts.local` | Survives reboot |
| Journal transcript | `wc -l /root/rhcsa_journal/lab-06a/task2/evidence.txt` | Audit trail (must be > 0) |

> **Reboot reasoning:** `/etc/selinux/targeted/contexts/files/file_contexts.local` survives reboot — it's on disk. On boot, SELinux loads the policy + local customizations; the rule is back in effect. If a full relabel ever runs, `restorecon` walks the tree and re-applies `httpd_sys_content_t`. The thing that **must** persist is the journal `evidence.txt` under `/root/`.

### Journal write — BEFORE cleanup

```bash
LAB=lab-06a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/listing-lab/task2/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    semanage fcontext + restorecon permanent fix + chcon contrast (T02 T03)
COMMANDS: semanage fcontext, restorecon -nv, restorecon -Rv, chcon, matchpathcon, ls -lZ
TRAPS:    T02 rehearsed (dry-run before apply); T03 rehearsed (chcon overwritten by restorecon)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-06b (Ansible) — community.general.sefcontext for the same outcome
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
sudo semanage fcontext -d '/srv/www-lab-06(/.*)?' 2>/dev/null || true
sudo restorecon -Rv /srv/www-lab-06/
sudo rm -rf /srv/www-lab-06
rm -rf /tmp/listing-lab
test -d /srv/www-lab-06 || echo "sandbox gone — clean exit"
test -d /tmp/listing-lab || echo "tmp sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `semanage: command not found` | `sudo dnf install -y policycoreutils-python-utils` |
| `restorecon` says no changes | Rule isn't stored or files already match — check `semanage fcontext -l` |
| `chcon` label survives `restorecon` | No fcontext rule governs that path — T03 in action |

> **STOP — paste the output of `cat $JDIR/notes.txt` and the final `sudo semanage fcontext -l -C | grep -c '/srv/www-lab-06'` (should be 0 after cleanup) before moving on to Lab 06b.**

---

## Lab 06a Checklist (2 tasks)

- [ ] Task 1 — `ls -l`, `ls -lZ`, `ls -dZ` on `/etc` with passwd vs shadow context compare + journal evidence
- [ ] Task 2 — `semanage fcontext` + `restorecon -nv/-Rv` permanent fix **and** the `chcon` contrast (T02 T03) + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 06b** — SELinux Labels via Ansible | `community.general.sefcontext` — same fcontext rule, idempotent, via the module |
| **Lab 06c** — Verifying SELinux Labels | The auditor seat: `ls -lZ`, `matchpathcon`, `semanage fcontext -l -C`, journal evidence verification |
| Lab 05 — Directory Navigation (`pwd`, `cd`, `ls`) | `ls` without flags is the quick glance; this lab adds `-lZ` for SELinux context |
| Lab 11a — Safe Deletion (`rm`, `rmdir`) | Different file-ops trilogy — deletion discipline vs listing discipline |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
