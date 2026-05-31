# Lab 12a: Creating Nested Directories (RHCSA) — `mkdir`, `mkdir -p`, brace expansion

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** `12a` (RHCSA) → `12b` (Ansible) → `12c` (Verify)
- **Career arcs covered:** RHCSA EX200 ("create the directory tree `/data/X/Y/Z` with mode N" tasks), RHCE EX294 (`ansible.builtin.file: state=directory`), SRE (host bootstrap directory provisioning), DevOps (build artifact layout), AI/MLOps (`mkdir -p runs/$(date +%Y/%m/%d)/exp-$ID` for experiment output paths)
- **Prerequisite:** Lab 11 trilogy complete (`rm` is the inverse of `mkdir -p` — you need to know how to remove what you create)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = `mkdir -p` idempotence, Task 2 = brace expansion + explicit mode)
- **Practice Directory (rotation #12):** `/opt`
- **Sandbox:** `/tmp/mk-lab` (writes happen here; `/opt` is referenced read-only as the "real-world" layout target)
- **Traps rehearsed this lab:** **T12-A** (forgetting `-p` in scripts — errors on re-run) · **T12-B** (forgetting `-m`, mode falls back to umask, ends up `0775` when you wanted `0750`)

> **This lab's practice directory is: `/opt`** — every task references it in at least two commands (read-only inspections).

---

## LAB HEADER BLOCK — run this FIRST

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "💿  DISK:  $(lsblk 2>/dev/null | awk '$NF=="disk"{print "/dev/"$1}' | paste -sd, -)"
echo "🌐  NIC:   $(ip -o addr show 2>/dev/null | awk '$2!="lo"{print $2}' | sort -u | paste -sd, -)"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T12-A T12-B"
echo "📁  PRACTICE DIR: /opt"
echo ""
echo "💡 /opt occupants (we read /opt; we write into /tmp/mk-lab):"
ls -ld /opt 2>/dev/null
ls /opt 2>/dev/null | head -n 5
df -h /opt | head -n 2
```

> **STOP — paste header output before running setup.**

---

## Objective

Build directory trees in a single command — including missing parents, including specific permissions. By the end of this lab you can answer any "create the path `/data/year/month/day/exp-N/`" prompt with a single `mkdir -p` and you understand why that command is **idempotent** (safe to rerun) while bare `mkdir` is not.

---

## Concept: `mkdir -p` Is Not "mkdir With Parents" — It Is "mkdir Made Idempotent"

The bare `mkdir(2)` syscall creates exactly **one** directory and refuses if the parent does not exist. The `-p` flag does two things:

1. Walks the path, creating each missing segment as it goes.
2. **Treats "already exists" as success, not failure.**

```
   $ mkdir /a/b/c
   mkdir: cannot create directory '/a/b/c': No such file or directory
                 ↑
                 └─ parent '/a/b' doesn't exist; kernel refuses

   $ mkdir -p /a/b/c
   (success — creates /a, then /a/b, then /a/b/c, all in one command)

   $ mkdir -p /a/b/c     # second run
   (success — exit 0; nothing changed because target already exists)
```

That second property — "already exists is fine" — is what makes `mkdir -p` **idempotent**. Plain `mkdir` errors on the second run, which breaks scripts in CI loops or on Ansible re-application. Every modern script uses `mkdir -p` unconditionally.

---

## Reference (everything you need for Tasks 1–2)

| Flag | Meaning |
|---|---|
| (default) | Create one directory; error if parent missing or target exists |
| `-p` / `--parents` | Create missing parents; no error if target exists (the idempotence flag) |
| `-m MODE` / `--mode=MODE` | Set explicit mode on creation (bypasses umask) |
| `-v` / `--verbose` | Print each created directory |
| `-Z` | Set SELinux context (policy default) |
| `--context=CTX` | Specific SELinux context |
| `{a,b,c}` | Bash brace expansion — creates three siblings in one command |
| `{01..12}` | Numeric sequence — creates 12 siblings named `01` through `12` |

> **Rule of `mkdir`:** Always `-p` in scripts. Always `-m` when mode matters. The two-second cost is zero compared to the cost of "the directory is mode 775 when I wanted 750" debugging later.

---

## Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/mk-lab
cd /tmp/mk-lab

cat > /tmp/mk-lab/THIS_DIRECTORY.txt <<'EOF'
/opt — Third-party software packages

Software that does not follow the /usr layout installs here as a self-contained
tree: /opt/appname/bin, /opt/appname/lib, /opt/appname/etc. Common examples:
Java runtimes, IBM products, vendor tools, manually-built binaries.

Why it exists: the FHS reserves /opt for software that wants its own namespace
without polluting /usr. Each application becomes one rmable directory.

What lives inside it: typically /opt/<vendor>/<app>/<version>/, with the app's
own bin, lib, share, etc subdirectories underneath. Some shops use /opt for
in-house tooling shipped via tarball rather than RPM.

Why RHCSA cares: creating /opt/<app> trees with correct mode and ownership is
a common admin task. The "create the directory tree with mode 0750 owned by
root:wheel" exam prompt almost always uses /opt as the target.
EOF

cat /tmp/mk-lab/THIS_DIRECTORY.txt
ls -ld /opt
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — `mkdir -p` for deep trees + idempotence proof (T12-A)

**Practice directory this task:** `/opt` · Third-party software packages — we inspect `/opt`'s existing layout to model what a real vendor install looks like, then build a parallel structure in `/tmp/mk-lab` to practice safely.

### Warm-Up — commands woven into Task 1

```bash
ls -ld /opt /tmp/mk-lab                              2>&1 | tee /tmp/mk-lab/warmup-pre.txt
find /opt -maxdepth 2 -type d                        2>/dev/null | head -n 10
test -d /tmp/mk-lab && echo "sandbox OK"
stat -c '%n mode=%a' /opt /tmp/mk-lab
mkdir   # show that bare mkdir errors with no args
echo "exit=$?"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 11: `test -d` guard pattern — only proceed if the target really is a directory. Same guard, different operation.

### Purpose

Build a non-trivial directory tree with a single `mkdir -p` call, then re-run the same command twice more to prove the operation is idempotent. Demonstrate the contrast: bare `mkdir DIR/SUB/SUB` fails when parents are missing, while `mkdir -p DIR/SUB/SUB` succeeds and reports `exit 0` on every subsequent run.

### WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -ld /opt /tmp/mk-lab` | Snapshot **before** and AFTER the `mkdir -p` so we can compare directory counts |
| `find /opt -maxdepth 2 -type d` | Sample real `/opt` vendor layout — we mirror its shape in the sandbox |
| `test -d /tmp/mk-lab` | Guards the loop so we never run `mkdir -p` against a missing sandbox |
| `stat -c '%n mode=%a'` | Captures mode before and after — proves the warm-up's data flowed into the verification |
| `2>&1 \| tee` | Captures every `mkdir -pv` line into `task1/op.txt` for the journal |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /tmp/mk-lab
mkdir -p /tmp/mk-lab/task1

# Snapshot before
BEFORE=$(find /tmp/mk-lab -type d | wc -l)
ls -ld /tmp/mk-lab                                   2>&1 | tee /tmp/mk-lab/task1/op.txt

# Demonstrate the FAILURE without -p
mkdir /tmp/mk-lab/deep/nested/path                   2>&1 | tee -a /tmp/mk-lab/task1/op.txt
echo "exit without -p: $?"                           2>&1 | tee -a /tmp/mk-lab/task1/op.txt

# The right way — -p creates all missing parents
mkdir -pv /tmp/mk-lab/deep/nested/path               2>&1 | tee -a /tmp/mk-lab/task1/op.txt
echo "exit with -p: $?"                              2>&1 | tee -a /tmp/mk-lab/task1/op.txt

# Idempotence — re-run the SAME command twice more
mkdir -pv /tmp/mk-lab/deep/nested/path               2>&1 | tee -a /tmp/mk-lab/task1/op.txt
echo "exit on rerun #1: $?"                          2>&1 | tee -a /tmp/mk-lab/task1/op.txt
mkdir -pv /tmp/mk-lab/deep/nested/path               2>&1 | tee -a /tmp/mk-lab/task1/op.txt
echo "exit on rerun #2: $?"                          2>&1 | tee -a /tmp/mk-lab/task1/op.txt

# Mixed: extend the existing tree
mkdir -pv /tmp/mk-lab/deep/nested/another/branch     2>&1 | tee -a /tmp/mk-lab/task1/op.txt

# Snapshot after
AFTER=$(find /tmp/mk-lab -type d | wc -l)
echo "dirs before=$BEFORE  dirs after=$AFTER  delta=$(( AFTER - BEFORE ))"
ls -lR /tmp/mk-lab/deep                              2>&1 | tee -a /tmp/mk-lab/task1/op.txt
echo "exit was: $?"
```

### Human-readable breakdown

1. Count directories in the sandbox before any `mkdir`.
2. Show bare `mkdir` failing with `cannot create directory: No such file or directory` when parents are missing.
3. Run `mkdir -pv` (verbose) to create the full chain — three directories created in one command.
4. Re-run the **exact same command** twice more. Both reruns succeed silently, exit 0, no errors. That is idempotence.
5. Add a sibling branch to demonstrate `-p` is fine with "some segments exist, some don't" — it only creates the missing ones.
6. Count directories after; the delta confirms how many were actually created.

### Reading it left to right

- `mkdir DIR` — calls `mkdir(2)` once. Errors with `ENOENT` if parent missing or `EEXIST` if target already exists.
- `mkdir -p DIR/SUB/LEAF` — walks `DIR`, `DIR/SUB`, `DIR/SUB/LEAF`; for each segment, `stat` first; if missing, `mkdir`. If it already exists, skip silently. Treat `EEXIST` as success.
- `mkdir -pv` — same as above, but prints `mkdir: created directory 'X'` for each segment that was actually created. Skipped segments produce no output (that's why reruns produce no log lines, just exit 0).
- `find /tmp/mk-lab -type d | wc -l` — counts directories; before/after comparison is the structural proof.
- `ls -lR DIR` — long recursive listing; shows the final tree shape with permissions.

### The story

Idempotence is **the** property scripts rely on. Without it, every retry, every CI re-run, every Ansible re-application errors out on the second attempt and you have to write defensive code: `[ -d "$DIR" ] || mkdir "$DIR"`. With `-p`, that defensive code is gone — the flag does it for you. Every modern script uses `mkdir -p` unconditionally, even when it "knows" the parent exists, because two seconds of "knowing" is exactly when assumptions break.

The most common bug T12-A produces: a setup script that works the first time but fails on every retry. CI catches it. Ansible catches it. Production catches it at 3 a.m. The fix is one character: `-p`.

### Expected output

```text
drwxr-xr-x. 3 root root 41 May 27 ... /tmp/mk-lab
mkdir: cannot create directory '/tmp/mk-lab/deep/nested/path': No such file or directory
exit without -p: 1
mkdir: created directory '/tmp/mk-lab/deep'
mkdir: created directory '/tmp/mk-lab/deep/nested'
mkdir: created directory '/tmp/mk-lab/deep/nested/path'
exit with -p: 0
exit on rerun #1: 0
exit on rerun #2: 0
mkdir: created directory '/tmp/mk-lab/deep/nested/another'
mkdir: created directory '/tmp/mk-lab/deep/nested/another/branch'
dirs before=1  dirs after=6  delta=5
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `mkdir DIR` | Create one directory; errors if parent missing or target exists |
| `mkdir -p A/B/C` | Create missing parents; no error if target exists (idempotent) |
| `mkdir -pv A/B/C` | Same, verbose — prints each created segment |
| `find DIR -type d \| wc -l` | Count directories under DIR |
| `ls -lR DIR` | Long recursive listing |

### Concept Card

| Concept | What it does |
|---|---|
| `mkdir(2)` syscall | Creates one directory entry; errors on missing parent or existing target |
| `-p` idempotence | The "already exists is fine" flag — re-runs become no-ops, exit 0 |
| Verbose `-v` | Prints what was actually created; silence on re-run proves nothing was done |
| `find ... -type d \| wc -l` | Structural counter that doesn't require parsing `ls` output |
| **🪤 Trap Risk T12-A** | Scripts using bare `mkdir` instead of `mkdir -p` — work the first time, fail on retry. Always `-p` in scripts. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Tree built | `find /tmp/mk-lab/deep -type d` | Shows all 5 directories created |
| Idempotence proven | `mkdir -pv /tmp/mk-lab/deep/nested/path; echo $?` | Must print no output and exit 0 |
| Journal evidence | `wc -l /root/rhcsa_journal/lab-12a/task1/op.txt` | Audit trail of the full transcript |

> **Reboot reasoning:** `/tmp/mk-lab` evaporates at reboot (tmpfs). The journal under `/root/` does not. After a reboot, the tree itself is gone, but re-running `mkdir -pv /tmp/mk-lab/deep/nested/path` would rebuild it idempotently — that's the entire point.

### Journal write — BEFORE cleanup

```bash
LAB=lab-12a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mk-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    mkdir -p deep tree + idempotence proof
COMMANDS: mkdir, mkdir -p, mkdir -pv, find -type d, ls -lR
TRAPS:    T12-A rehearsed (demonstrated -p vs no -p; reran -p three times for idempotence)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — brace expansion + explicit mode (T12-B)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-lab/deep /tmp/mk-lab/task1
ls /tmp/mk-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `mkdir: cannot create directory 'X': File exists` | Bare mkdir on existing target. Use `-p` to make it idempotent. |
| `mkdir -p` failed with permission error | No write on the parent. Check `ls -ld $(dirname TARGET)`. |
| Exit 0 but directory not visible | `pwd` likely wrong — recheck the absolute path. |
| Re-run on a tree with mixed mode | `-p` only sets mode on **newly created** segments. Existing parents keep their original mode. |
| `-pv` printed nothing on first run | The tree existed already from a previous run — that IS the idempotence success case. |

> **STOP — paste the "dirs before / after" line and `cat $JDIR/done.txt` before starting Task 2.**

---

## Task 2 — Brace expansion + explicit mode (T12-B trap)

**Practice directory this task:** `/opt` · we model the canonical "deep tree with explicit mode owned root:wheel" RHCSA capstone shape inside `/tmp/mk-lab`, referencing `/opt` to confirm what real vendor mode-0755 layouts look like.

### Warm-Up — commands woven into Task 2

```bash
umask
ls -ld /opt                                          2>&1 | tee /tmp/mk-lab/warmup-task2.txt
find /tmp/mk-lab -type d                             2>/dev/null | wc -l
stat -c '%n mode=%a owner=%U:%G' /opt /tmp/mk-lab
test -d /tmp/mk-lab && echo "sandbox OK"
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: `find ... -type d | wc -l` is still our structural counter. Now we use it to verify a **fan-out**: 3 × 3 = 9 leaves built in one command.

### Purpose

Use bash brace expansion (`{a,b,c}` and `{01..12}`) to create many sibling directories in one `mkdir -p` call, with explicit `-m MODE` so the result does not depend on umask. Demonstrate the contrast: same tree with and without `-m` — one inherits umask, the other has the mode you asked for.

### WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `umask` | Surfaces the **structural reason** Task 2 exists — without `-m`, mode = `0777 & ~umask`, which is usually `0755` not `0750` |
| `stat -c '%n mode=%a owner=%U:%G'` | Verifies the mode **on every created leaf** — drops the trap detection straight into the audit |
| `find ... -type d \| wc -l` | Counts the fan-out: starts at N, must end at N + (3×3) = N+9 |
| `ls -ld /opt` | Real-world reference: vendor `/opt` trees are almost always 0755; our 0750 with explicit `-m` is intentional |
| `2>&1 \| tee` | Captures every step into `task2/op.txt` for the journal |
| `$(date -Is)` | Stamps the journal `notes.txt` |

### Main command block

```bash
cd /tmp/mk-lab
mkdir -p /tmp/mk-lab/task2
BEFORE=$(find /tmp/mk-lab -type d | wc -l)

# ── Part A: the T12-B trap — brace expansion WITHOUT -m ─────────────
mkdir -pv /tmp/mk-lab/projects-bad/{web,api,db}/{logs,configs,backups} \
  2>&1 | tee /tmp/mk-lab/task2/op.txt
echo "── mode of bad/web/logs (umask-derived, NOT what we wanted) ──" \
  | tee -a /tmp/mk-lab/task2/op.txt
stat -c '%n mode=%a' /tmp/mk-lab/projects-bad/web/logs \
  | tee -a /tmp/mk-lab/task2/op.txt

# ── Part B: the right way — brace expansion WITH -m 0750 ────────────
mkdir -pv -m 0750 /tmp/mk-lab/projects-good/{web,api,db}/{logs,configs,backups} \
  2>&1 | tee -a /tmp/mk-lab/task2/op.txt
echo "── mode of good/web/logs (explicit -m 0750) ──" \
  | tee -a /tmp/mk-lab/task2/op.txt
stat -c '%n mode=%a' /tmp/mk-lab/projects-good/web/logs \
  | tee -a /tmp/mk-lab/task2/op.txt

# Show every leaf's mode side-by-side
echo "── all bad leaves ──" | tee -a /tmp/mk-lab/task2/op.txt
find /tmp/mk-lab/projects-bad  -mindepth 2 -type d -exec stat -c '  %n mode=%a' {} + \
  | tee -a /tmp/mk-lab/task2/op.txt
echo "── all good leaves ──" | tee -a /tmp/mk-lab/task2/op.txt
find /tmp/mk-lab/projects-good -mindepth 2 -type d -exec stat -c '  %n mode=%a' {} + \
  | tee -a /tmp/mk-lab/task2/op.txt

# Numeric-sequence fan-out demonstration
mkdir -pv -m 0755 /tmp/mk-lab/runs/2026/{01..12} 2>&1 | tail -n 5 | tee -a /tmp/mk-lab/task2/op.txt
find /tmp/mk-lab/runs -type d | wc -l

AFTER=$(find /tmp/mk-lab -type d | wc -l)
echo "dirs before=$BEFORE  dirs after=$AFTER  delta=$(( AFTER - BEFORE ))"
echo "exit was: $?"
```

### Human-readable breakdown

**Part A — the trap.** Build `projects-bad/{web,api,db}/{logs,configs,backups}` without `-m`. The bash brace expansion creates 3 × 3 = 9 leaf directories. `stat` on one leaf shows mode `0755` (or whatever umask allows) — **not** the `0750` we usually want for app data directories.

**Part B — the fix.** Build the same tree at `projects-good/` with `-m 0750`. Every leaf now has mode `0750` because `-m` overrides the umask calculation entirely.

Compare side-by-side: the bad tree and the good tree have **identical structure** but different mode. The trap is silent — the directories exist, the script "succeeded," but the security posture is wrong. RHCSA graders specifically look for this.

The numeric-sequence demo (`{01..12}`) shows the second brace form, useful for year/month/day fixture builds.

### Reading it left to right

- `{web,api,db}` — bash brace expansion. The shell expands this BEFORE `mkdir` runs into `web api db`.
- `{web,api,db}/{logs,configs,backups}` — Cartesian product. The shell expands into nine pairs: `web/logs web/configs web/backups api/logs ... db/backups`.
- `{01..12}` — numeric sequence with zero-padding (because `01` has a leading zero).
- `-m 0750` — overrides umask; mode applies to ALL newly created segments in the chain. Existing segments are unchanged.
- `find ... -mindepth 2 -type d -exec stat -c ... +` — `-mindepth 2` excludes the top-level container; `-exec ... +` batches matches into one `stat` invocation (much faster than `\;`).
- `umask` — three-octal complement of default mode. `0022` means "remove write for group and other," so new dirs default to `0777 & ~0022 = 0755`.

### The story

`-m` is the difference between "the directories exist" and "the directories exist with the mode the spec asked for." Most candidates lose RHCSA points on `mkdir` tasks because they forget `-m` and accept whatever umask produces. Graders run `stat -c '%a' /path` against the leaves and dock the difference between expected and actual. The fix is one extra flag.

Brace expansion is the other multiplier. `mkdir -p /data/{web,api,db}/{logs,configs,backups}` builds nine directories in one command. The pre-`-p` era required a `for` loop. The pre–brace-expansion era required nine commands. Today both are one line.

### Expected output

```text
0022
drwxr-xr-x. 4 root root 39 ... /opt
1
/opt mode=755 owner=root:root
/tmp/mk-lab mode=755 owner=root:root
sandbox OK
mkdir: created directory '/tmp/mk-lab/projects-bad'
mkdir: created directory '/tmp/mk-lab/projects-bad/web'
mkdir: created directory '/tmp/mk-lab/projects-bad/web/logs'
... (9 lines for projects-bad) ...
── mode of bad/web/logs (umask-derived, NOT what we wanted) ──
/tmp/mk-lab/projects-bad/web/logs mode=755
mkdir: created directory '/tmp/mk-lab/projects-good'
mkdir: created directory '/tmp/mk-lab/projects-good/web'
... (9 lines for projects-good) ...
── mode of good/web/logs (explicit -m 0750) ──
/tmp/mk-lab/projects-good/web/logs mode=750
── all bad leaves ──
  /tmp/mk-lab/projects-bad/web/logs mode=755
  /tmp/mk-lab/projects-bad/web/configs mode=755
  ... (9 entries, all 755) ...
── all good leaves ──
  /tmp/mk-lab/projects-good/web/logs mode=750
  /tmp/mk-lab/projects-good/web/configs mode=750
  ... (9 entries, all 750) ...
mkdir: created directory '/tmp/mk-lab/runs/2026/12'
13
dirs before=1  dirs after=37  delta=36
exit was: 0
```

### Switches

| Token | Meaning |
|---|---|
| `{a,b,c}` | Brace expansion — comma-separated list |
| `{01..12}` | Numeric sequence (compact form, with leading zero) |
| `-m MODE` | Set mode on creation; applies to all newly-created segments |
| `umask` | Show or set the default mode mask |
| `find ... -mindepth N` | Exclude the top N levels from the result |
| `-exec stat -c ... +` | Batched per-match execution (preferred over `\;`) |

### Concept Card

| Concept | What it does |
|---|---|
| Brace expansion `{a,b,c}` | Shell-level fan-out — creates N siblings in one command |
| Numeric sequence `{01..12}` | Compact form for `01 02 03 ... 12`; preserves leading zeros |
| `-m MODE` override | Sets mode at creation, ignoring umask |
| umask | The structural default: `0777 & ~umask` for directories |
| `-mindepth N` filter | Excludes the top N levels from the audit — focuses on leaves |
| **🪤 Trap Risk T12-B** | Forgetting `-m`; the tree is built but the mode silently defaults to umask. Use `stat -c '%a'` on a leaf as a sanity check before moving on. |

### PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| 9 leaves with mode 0750 | `find /tmp/mk-lab/projects-good -mindepth 2 -type d -exec stat -c '%a' {} + \| sort -u` | Must print `750` only (one unique value) |
| 12 month sub-dirs | `find /tmp/mk-lab/runs -mindepth 2 -type d \| wc -l` | Must be `12` |
| Bad tree vs good tree | `diff <(stat -c '%a' /tmp/mk-lab/projects-bad/web/logs) <(stat -c '%a' /tmp/mk-lab/projects-good/web/logs)` | Must show diff (755 vs 750) |
| Journal evidence | `wc -l /root/rhcsa_journal/lab-12a/task2/evidence.txt` | The full transcript |

> **Reboot reasoning:** The trees evaporate (tmpfs), but the journal evidence under `/root/` survives. After a reboot, re-running the exact same `mkdir -p -m 0750 ...` command rebuilds the tree with the same mode — idempotent **and** deterministic.

### Journal write — BEFORE cleanup

```bash
LAB=lab-12a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/mk-lab/task2/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Brace expansion + -m mode override (T12-B contrast)
COMMANDS: mkdir -p -m 0750, {a,b,c}, {01..12}, stat -c '%a', find -mindepth
TRAPS:    T12-B rehearsed (built same tree with and without -m; verified 755 vs 750)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-12b (Ansible) — ansible.builtin.file: state=directory for the same outcome
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### Cleanup

```bash
rm -rf /tmp/mk-lab
test -d /tmp/mk-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| Brace expansion produced literal `{a,b}` directory | Running `sh` instead of `bash`. Switch to bash. |
| Brace expansion was quoted | `'{a,b,c}'` is literal. Remove quotes around braces (quote the path elsewhere if needed). |
| Mode is 0775 instead of 0750 | Forgot `-m`; or umask is 0002 not 0022. `-m` overrides both. |
| `-m` did not affect existing parent | `-m` only applies to newly-created segments. Use `chmod` separately for existing. |
| `{01..31}` produced `1 2 3 ... 31` (no zero-pad) | Older bash, or different shell. Use `{01..31}` explicitly with leading zero. |

> **STOP — paste the "all bad leaves / all good leaves" side-by-side output and `cat $JDIR/notes.txt` before moving to Lab 12b.**

---

## Lab 12a Checklist (2 tasks)

- [ ] Task 1 — `mkdir -p` deep tree + idempotence proof (re-run three times, exit 0 each time)
- [ ] Task 2 — Brace expansion `{web,api,db}/{logs,configs,backups}` with and without `-m 0750` (T12-B contrast)

---

## Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 12b** — Creating Nested Directories via Ansible | `ansible.builtin.file: state=directory  recurse: yes  mode: '0750'` — same outcome, idempotent |
| **Lab 12c** — Verifying Created Directories | The auditor seat: `stat`, `find`, `getfacl` on every leaf |
| Lab 11 — Safe Deletion | The inverse — `mkdir -p` builds, `rm -rf` removes; same `-p` idempotence pattern |
| Lab 13a — Creating Command Aliases | After `mkdir -p` builds `/etc/profile.d/`, that's where system-wide aliases live |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
