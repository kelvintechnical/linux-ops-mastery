# Lab 17a: Find and Save Config Files (RHCSA) — `find -type f -name -user 2>/dev/null`

- **Series:** linux-ops-mastery — Filesystem Search and Evidence Capture
- **Trilogy:** `17a` (RHCSA hand-typed) → [`17b`](../lab-17b-find-save-config-files-ansible/) (Ansible FQCN) → [`17c`](../lab-17c-find-save-config-files-verify/) (Verify capstone)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 canonical `/etc` search + save · Task 2 noisy `/` search with ownership filter)
- **Practice Directory (rotation #03):** `/lib`
- **Sandbox (Tier B):** `/tmp/lab17a`, `USER=labuser_17_findsave`, `GROUP=labgrp_17_findsave`, `USER_HOME=/tmp/lab17a/home_labuser_17_findsave`
- **Traps rehearsed:** **T14-A** (forgetting `2>/dev/null` on `find /`) · **T14-B** (`-name` vs `-iname`) · **T41** (skip reboot/persistence reasoning) · **T44** (skip cleanup audit)

> **This lab's practice directory is: `/lib`**. It holds shared libraries required by `/bin` and `/sbin`; without it, user and admin binaries cannot run.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T14-A T14-B T41 T44"
echo "📁  PRACTICE DIR: /lib"
ls -ld /lib
```

> **STOP — paste header output before setup.**

---

## Objective

Build exam reflexes for file discovery and safe capture:

1. Use `find /etc -type f -name '*.conf' 2>/dev/null > FILE` correctly.
2. Use ownership filters (`-user root`) while searching broad trees.
3. Treat permission-denied spam as expected noise and redirect stderr.
4. Save clean evidence files for later verification.

---

## Lab-Wide Setup — Tier B Sandbox Stack

```bash
sudo -i

export LAB_NUM=17
export LAB_SLUG=findsave
export SANDBOX=/tmp/lab17a
export GROUP=labgrp_17_findsave
export USER=labuser_17_findsave
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/lib stores shared libraries needed by system binaries in /bin and /sbin.
It exists so executables can stay small and dynamically link required code.
You find .so and loader files here (or under /usr/lib via symlink layouts).
For RHCSA, knowing /lib matters because command execution itself depends on it.
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /lib
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste `id`, `ls -ld`, and `THIS_DIRECTORY.txt` output before Task 1.**

---

## Task 1 — Canonical `/etc` config-file capture

**Practice directory this task:** `/lib` — we still search `/etc`, but we reference `/lib` for rotation discipline and context checks.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 1 -type f 2>/dev/null | head -n 3
echo "warmup-user=$(whoami) time=$(date -Is)" | tee /tmp/lab17a/warmup1.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Run the exact RHCSA-style search for config files under `/etc`, save stdout to a list file, and execute the search as the lab user with `sudo -u` so Tier B user/group mechanics are exercised inside the task.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 1 |
|---|---|
| `ls -ld /lib` | Proves the rotated practice directory is available before work begins |
| `find /lib ...` | Rehearses `find -type f` syntax before target command |
| `tee` | Captures proof output while still showing terminal lines |
| `sudo -u "${USER}"` | Executes the actual `find` as lab user for Tier B repetition |

### Main command block

```bash
LIST1=/tmp/lab17a/etc-conf-list.txt
LOG1=/tmp/lab17a/task1.log

sudo -u "${USER}" bash -c "find /etc -type f -name '*.conf' 2>/dev/null > '${LIST1}'"

wc -l "${LIST1}"                           2>&1 | tee "${LOG1}"
head -n 10 "${LIST1}"                      2>&1 | tee -a "${LOG1}"
test -s "${LIST1}" && echo "list has data" | tee -a "${LOG1}"
stat -c '%U:%G %a %n' "${LIST1}"          | tee -a "${LOG1}"
ls -ld /lib                                | tee -a "${LOG1}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `find /etc -type f -name '*.conf'` narrows results to regular files ending in `.conf`.
- `2>/dev/null` drops permission errors from stderr so only valid paths remain in the list file.
- `sudo -u "${USER}"` forces the command to run as the Tier B lab user.
- `wc -l`, `head`, and `stat` verify count, sample contents, and ownership.

### Reading it left to right

```text
find /etc -type f -name '*.conf' 2>/dev/null > /tmp/lab17a/etc-conf-list.txt
│    │    │       │             │            └─ save stdout list
│    │    │       │             └─ hide permission-noise stderr
│    │    │       └─ filename glob match
│    │    └─ regular files only
│    └─ search root for configs
└─ command
```

### The story

On the exam, "save all matching files" is a speed test of `find` precision. The grader wants clean paths, not pages of permission denials. Redirecting stderr to `/dev/null` keeps evidence deterministic and readable.

### Expected output

```text
N /tmp/lab17a/etc-conf-list.txt
/etc/...
/etc/...
list has data
labuser_17_findsave:labgrp_17_findsave 644 /tmp/lab17a/etc-conf-list.txt
```

### Switches

| Token | Meaning |
|---|---|
| `-type f` | Match regular files only |
| `-name '*.conf'` | Case-sensitive filename glob |
| `2>/dev/null` | Discard stderr (permission noise) |
| `sudo -u USER` | Run command as specific user |
| `wc -l` | Count lines |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | `find` filters | Narrows search by type and name pattern |
| ✅ | stderr redirect | Keeps list file clean from errors |
| ✅ | Tier B `sudo -u` | Makes user/group practice part of real task |
| ✅ | Save then inspect | `> file` capture plus `head`/`wc` validation |
| 🪤 Trap Risk | **T14-A:** forgetting `2>/dev/null` | Always add stderr redirect for broad searches |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Saved list file | `test -s /tmp/lab17a/etc-conf-list.txt` | Confirms capture happened |
| Correct owner/group | `stat -c '%U:%G' /tmp/lab17a/etc-conf-list.txt` | Confirms `sudo -u` was real |
| Search syntax retained | `head -n 3 /tmp/lab17a/etc-conf-list.txt` | Confirms expected file-type output |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-17a/task1
mkdir -p "${JDIR}"
cp "${LIST1}" "${JDIR}/etc-conf-list.txt"
cp "${LOG1}"  "${JDIR}/evidence.txt"
echo "LAB: lab-17a TASK: task1 DATE: $(date -Is) STATUS: COMPLETE" > "${JDIR}/done.txt"
echo "TOPIC: find /etc -type f -name '*.conf' 2>/dev/null with sudo -u ${USER}" > "${JDIR}/notes.txt"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab17a/warmup1.txt /tmp/lab17a/task1.log
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `Permission denied` spam appears | You missed `2>/dev/null`; add it after `find` |
| Empty list file | Verify pattern and quoting: `-name '*.conf'` |
| Wrong owner on list | Run command through `sudo -u "${USER}"` |

> **STOP — paste `wc -l`, `head`, and `stat` output before Task 2.**

---

## Task 2 — Broad root-owned search from `/` with noise control

**Practice directory this task:** `/lib` — use it again for rotation continuity while main search spans `/`.

### Warm-Up

```bash
ls -ld /lib
find /lib -maxdepth 2 -type f -name '*.so*' 2>/dev/null | head -n 5
echo "prep task2 $(date -Is)" | tee /tmp/lab17a/warmup2.txt
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Search from filesystem root for root-owned config-like files while suppressing expected permission errors. Contrast `-name` and `-iname` to avoid case trap T14-B.

### WEAVE TRACE

| Warm-up / setup command | Role inside Task 2 |
|---|---|
| `find /lib ...` | Reuses `find` token order before broad `/` run |
| `head -n` | Samples huge result sets safely |
| `tee` | Captures evidence for verification/journal |
| `ls -ld /lib` | Keeps required practice-dir references in-task |

### Main command block

```bash
LIST2=/tmp/lab17a/root-owned-conf-from-root.txt
LOG2=/tmp/lab17a/task2.log

find / -type f -name '*.conf' -user root 2>/dev/null > "${LIST2}"

echo "case-sensitive count:"                     | tee "${LOG2}"
wc -l "${LIST2}"                                | tee -a "${LOG2}"
head -n 15 "${LIST2}"                           | tee -a "${LOG2}"

echo "case-insensitive sample for trap T14-B:"  | tee -a "${LOG2}"
find /etc -type f -iname '*.conf' 2>/dev/null | head -n 10 | tee -a "${LOG2}"

test -s "${LIST2}" && echo "root-owned list captured" | tee -a "${LOG2}"
ls -ld /lib                                     | tee -a "${LOG2}"
stat -c '%U:%G %a %n' "${LIST2}"               | tee -a "${LOG2}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- `find / ... -user root` performs ownership-filtered discovery across the whole filesystem.
- `2>/dev/null` is mandatory because `/` traversal always touches protected paths.
- `-name` is case-sensitive; `-iname` is case-insensitive and can change result count.
- `head` prevents dumping thousands of lines.

### Reading it left to right

```text
find / -type f -name '*.conf' -user root 2>/dev/null > /tmp/lab17a/root-owned-conf-from-root.txt
│   │  │       │             │          │            └─ clean path list
│   │  │       │             │          └─ hide permission errors
│   │  │       │             └─ owner filter
│   │  │       └─ case-sensitive name match
│   │  └─ files only
│   └─ search from root
└─ command
```

### The story

Real incident triage often starts with "show me all root-owned configs matching this pattern." Running `find /` without stderr control floods output and hides actual results. This task builds the habit of producing clean evidence on the first run.

### Expected output

```text
case-sensitive count:
N /tmp/lab17a/root-owned-conf-from-root.txt
/etc/...
/etc/...
case-insensitive sample for trap T14-B:
/etc/...
root-owned list captured
```

### Switches

| Token | Meaning |
|---|---|
| `-user root` | Match files owned by root |
| `-name` | Case-sensitive pattern match |
| `-iname` | Case-insensitive pattern match |
| `2>/dev/null` | Silence permission-denied stderr |
| `head -n` | Show first N lines |

### Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | Root-scope search | `find /` covers all mounted trees |
| ✅ | Owner filtering | `-user root` limits scope to owned files |
| ✅ | Case sensitivity | `-name` and `-iname` produce different sets |
| ✅ | Output hygiene | `2>/dev/null` keeps evidence useful |
| 🪤 Trap Risk | **T14-B:** wrong case mode | Pick `-name` or `-iname` deliberately |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Saved root-owned list | `test -s /tmp/lab17a/root-owned-conf-from-root.txt` | Confirms broad search succeeded |
| Noise suppressed | `wc -l /tmp/lab17a/task2.log` | Shows readable evidence log exists |
| Case trap rehearsed | `grep -c '\-iname' /tmp/lab17a/task2.log` | Proves contrast was executed |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-17a/task2
mkdir -p "${JDIR}"
cp "${LIST2}" "${JDIR}/root-owned-conf-from-root.txt"
cp "${LOG2}"  "${JDIR}/evidence.txt"
echo "LAB: lab-17a TASK: task2 DATE: $(date -Is) STATUS: COMPLETE" > "${JDIR}/done.txt"
echo "TOPIC: find / -type f -name '*.conf' -user root 2>/dev/null with -name/-iname trap contrast" > "${JDIR}/notes.txt"
```

### 🧹 Cleanup (per-task; final teardown runs in Lab Closeout)

```bash
rm -f /tmp/lab17a/warmup2.txt
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Command hangs visually | It is traversing `/`; wait, then sample with `head` |
| Output polluted with errors | `2>/dev/null` missing or misplaced |
| Too many or too few matches | Check `-name` vs `-iname` and quote glob |

> **STOP — paste `wc -l`, `head`, and trap contrast output before closeout.**

---

## Section 6 Closeout — Bulletproof Teardown Audit

```bash
set +e

# 1) Container layer (guarded no-op here)
podman ps -aq --filter "name=^${CTR}$" 2>/dev/null | xargs -r podman rm -f >/dev/null 2>&1

# 2) Mount layer
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

# 3) LVM layer (guarded no-op here)
if vgs "${VG}" >/dev/null 2>&1; then
    lvremove -fy "${VG}" 2>/dev/null
    vgremove -fy "${VG}" 2>/dev/null
    pvremove -ffy /dev/loop* 2>/dev/null
fi

# 4) Loopback layer
losetup -j "${SANDBOX}/disk.img" 2>/dev/null | cut -d: -f1 | xargs -r losetup -d 2>/dev/null

# 5) User/group
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

# 6) Sandbox
rm -rf "${SANDBOX}"

# 7) Audit
echo "── cleanup audit ──"
getent passwd "${USER}" && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" && echo "❌ group remains" || echo "✅ group gone"
vgs "${VG}" 2>/dev/null && echo "❌ VG remains" || echo "✅ vg gone"
losetup -l | grep -q "${SANDBOX}" && echo "❌ loop remains" || echo "✅ loop gone"
podman ps -a --filter "name=^${CTR}$" --format '{{.Names}}' | grep -q . && echo "❌ ctr remains" || echo "✅ ctr gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

---

## Lab 17a Checklist

- [ ] Tier B setup complete with `/tmp/lab17a/THIS_DIRECTORY.txt`
- [ ] Task 1 captured `/etc` `.conf` list with `2>/dev/null` and `sudo -u ${USER}`
- [ ] Task 2 captured root-owned list from `/` with noise suppression and `-name/-iname` contrast
- [ ] Section 6 closeout shows all ✅ audit lines

---

## Author

**Kelvin R. Tobias**
