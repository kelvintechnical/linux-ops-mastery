# Lab 02a: Standard Error Redirection (RHCSA) — `2>`, `2>>`, `2>/dev/null`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `02a` (RHCSA) → `02b` (Ansible, planned) → `02c` (Verify, planned)
- **Career arcs covered:** RHCSA EX200 (every `find /` task that emits `Permission denied`), RHCE EX294 (Ansible `result.stderr` is the same stream `2>` captures), SRE (post-mortems read stderr, not stdout — that's where the actual error message is), DevOps (CI/CD failed-build alerts), AI/MLOps (Python tracebacks land on stderr by default)
- **Prerequisite:** Lab 01a — you understand FD 1, `>`, `>>`, and `noclobber`
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical, Task 2 contrast)
- **Practice Directory (rotation #02):** `/sbin`
- **Sandbox:** `/tmp/labsandbox_02`
- **Sandbox User/Group:** `labuser_02_stderr` / `labgrp_02_stderr`
- **📌 ANCHOR TYPE:** none (regular lab)
- **📌 TRILOGY POS:** `a` (rhcsa)
- **📌 PREREQ:** Lab 01a complete and cleaned up
- **Traps rehearsed this lab:** **T02-A** (using `>` thinking it captures errors — it only captures FD 1) · **T02-B** (`cmd 2>&1 > file` vs `cmd > file 2>&1` — order is everything) · **T02-C** (`2>/dev/null` hides the exit code you needed) · **T44** (cleanup audit)

> **This lab's practice directory is: `/sbin`** — admin-only commands, mostly unreadable by non-root, so `find /sbin` as the lab user is the perfect natural source of `Permission denied` messages on FD 2.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T02-A T02-B T02-C T44"
echo "📁  PRACTICE DIR: /sbin"
echo ""
echo "💡 /sbin occupants (admin commands — most rooted-only):"
ls -ld /sbin
ls /sbin | wc -l
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Stop letting errors disappear off the top of your terminal scrollback. By the end of this lab you can:

1. Send the stderr of any command to a file with `2>` or `2>>` — independently from stdout.
2. Silence noisy `Permission denied` lines with `2>/dev/null` while still capturing the legitimate results.
3. Survive the three stderr traps that cost real RHCSA points: **wrong-stream redirection** (T02-A), **wrong-order combined redirect** (T02-B), **suppressed exit code** (T02-C).

The capstone is the RHCSA-realistic pattern: *"Find every file owned by USER under /etc whose name ends in .conf, suppress all errors, save the clean list to /root/conf-files.txt."* — every exam cycle has at least one task that reduces to this.

---

## 🧠 Concept: stderr Is a Second, Independent Stream

Every Linux process has three FDs by default. Lab 01a covered FD 0 (stdin) and FD 1 (stdout). **FD 2 is stderr.** It exists for one reason: so that error messages do not get tangled into the program's data output.

```
   ┌─────────────────────────────────────────────────────┐
   │   Your command (find, ls, grep, awk, ...)           │
   ├─────────────────────────────────────────────────────┤
   │   FD 0  stdin   ← keyboard                          │
   │   FD 1  stdout  → terminal (DATA)         ← `>`     │
   │   FD 2  stderr  → terminal (ERRORS)       ← `2>`    │
   └─────────────────────────────────────────────────────┘

   `> file`    captures FD 1 only — errors STILL hit the screen.   ← T02-A trap
   `2> file`   captures FD 2 only — data still hits the screen.
   `&> file`   captures both (Lab 04 — bash shorthand for `> file 2>&1`).
```

Both streams happen to display on the same terminal by default, which makes them *look* like one stream. They are not. `>` only redirects FD 1; FD 2 keeps going to the screen. That is the source of the bug *"my log file is empty even though the screen was full of red."*

---

## 📚 stderr Reference (everything used in Tasks 1–2)

| Pattern | Direction | Notes |
|---|---|---|
| `cmd 2> file` | stderr → file (truncate) | Captures errors, leaves stdout on screen |
| `cmd 2>> file` | stderr → file (append) | Adds to an existing error log |
| `cmd 2> /dev/null` | stderr → bit-bucket | The "silence the noise" idiom for `find /` |
| `cmd 2>&1` | stderr → wherever FD 1 currently goes | Merges error into data — **order matters** |
| `cmd 1>&2` | stdout → wherever FD 2 currently goes | Used in scripts to print errors deliberately |
| `cmd > out 2> err` | Split streams to two files | Capture both separately |
| `cmd > /dev/null 2>&1` | Discard both | Run for side effects only |

> **Rule of `2>`:** stderr is "everything that is not the answer." Status, progress, warnings, `Permission denied` — all of it. If you want a clean answer file, redirect FD 1 to the file *and* FD 2 to `/dev/null`.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1  (Section 1.5 sandbox stack)

```bash
sudo -i

export LAB_NUM=02
export LAB_SLUG=stderr
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/sbin — Admin-only commands (fdisk, reboot, iptables)

/sbin holds commands the system needs to boot, recover, and be
administered. Regular users cannot run most of these without sudo.
On modern RHEL, /sbin is a symlink to /usr/sbin.

Why this matters for stderr redirection: most of /sbin's contents
are readable but the BINARIES inside it (when executed by a non-
root user) often write diagnostics to FD 2. We exploit /etc instead
for the canonical `Permission denied`-while-finding lesson, because
/etc has subdirectories root can read but our lab user cannot. The
core fact: stderr-on-find is the most common RHCSA pattern.
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
cat "${SANDBOX}/THIS_DIRECTORY.txt"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output (id, ls, exit code) before Task 1.**

---

## Task 1 — Canonical: `2>` capture and `2>/dev/null` silence

### a) Directory context

**Practice directory this task:** `/sbin` (lookup) and `/etc` (the actual source of stderr) — `/sbin` is the FHS rotation slot we're studying; `/etc` is where the realistic `Permission denied` traffic lives.

### b) 🔁 Warm-Up — commands woven into Task 1

```bash
ls -ld /sbin /etc                                   2>&1 | tee "${SANDBOX}/warmup1.txt"
ls /sbin | wc -l
getent passwd "${USER}"
id -nG "${USER}"
sudo -u "${USER}" pwd
test -d "${SANDBOX}" && echo "sandbox OK"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Run `find /etc -name '*.conf'` **as the lab user** (who can't read every subdir) so it emits real `Permission denied` messages. Capture stderr to one file, stdout to another, then re-run with `2>/dev/null` to prove the silencing pattern. The lab user owns the captured files so the Tier-B sandbox stack does real work.

### d) 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -ld /sbin /etc` | Pre-flight: both source dirs must exist before `find` runs |
| `getent passwd "${USER}"` | Confirms the lab user exists before `sudo -u "${USER}"` |
| `id -nG "${USER}"` | Confirms primary group matches — needed because we'll `chown user:group` the captures |
| `sudo -u "${USER}" pwd` | Smoke-test that `sudo -u` works at all (catches bad sudoers entries early) |
| `test -d "${SANDBOX}"` | Guards the redirects — refuses to write into a missing dir |

### e) Main command block

```bash
cd "${SANDBOX}"

# 1. Naive run — both streams hit screen, mixed together
echo "── run #1: no redirect (errors and data tangled) ──"
sudo -u "${USER}" find /etc -name '*.conf' -type f | head -n 3
echo "── (errors were lost above the head -n3 cut)"

# 2. Capture-everything — stdout to one file, stderr to another
sudo -u "${USER}" find /etc -name '*.conf' -type f \
    >  "${SANDBOX}/conf-files.txt" \
    2> "${SANDBOX}/conf-errors.txt"

STDOUT_LINES=$(wc -l < "${SANDBOX}/conf-files.txt")
STDERR_LINES=$(wc -l < "${SANDBOX}/conf-errors.txt")
echo "── run #2: split capture ──"
echo "stdout lines (real results): ${STDOUT_LINES}"
echo "stderr lines (denied paths): ${STDERR_LINES}"

# 3. Inspect the two captures so we KNOW they're different streams
echo "── first 3 stdout lines (clean .conf paths) ──"
head -n 3 "${SANDBOX}/conf-files.txt"
echo "── first 3 stderr lines (the noise that ruined run #1) ──"
head -n 3 "${SANDBOX}/conf-errors.txt"

# 4. The RHCSA reflex: clean answer file, silence the noise
sudo -u "${USER}" find /etc -name '*.conf' -type f \
    >  "${SANDBOX}/conf-clean.txt" \
    2> /dev/null

echo "── run #3: clean answer (stderr discarded) ──"
wc -l "${SANDBOX}/conf-clean.txt"

# 5. Tier-B weave — chown all captures to lab user, prove they can read them
chown "${USER}:${GROUP}" "${SANDBOX}"/conf-*.txt
sudo -u "${USER}" wc -l "${SANDBOX}"/conf-*.txt
stat -c '%n owner=%U:%G mode=%a' "${SANDBOX}"/conf-*.txt

echo "exit was: $?"
```

### f) Human-readable breakdown

1. Run `find` with **no** redirection so you see how stderr and stdout mix on screen — and notice you've effectively lost the errors after `head -n 3` cuts them.
2. Run `find` again, this time splitting stdout to `conf-files.txt` and stderr to `conf-errors.txt`. Both files now hold separate, complete content.
3. Show the first 3 lines of each so the difference is undeniable: clean paths on stdout, `Permission denied` on stderr.
4. Run the RHCSA pattern: keep stdout in a file, throw stderr at `/dev/null`. This is the muscle memory you want.
5. Hand the files to the lab user via `chown` and verify the user can read them (Tier-B sandbox stack work).

### g) Reading it left to right

- `sudo -u "${USER}" find ...` — `find` runs as the lab user, so subdirectories of `/etc` that are mode `0700` and owned by root will emit `find: '/etc/PRIVATE': Permission denied` to FD 2.
- `> "${SANDBOX}/conf-files.txt"` — FD 1 redirect (same as Lab 01a). Truncate-write.
- `2> "${SANDBOX}/conf-errors.txt"` — FD 2 redirect. Identical syntax to `>` but prefixed with the FD number. Truncate-write.
- Order of `>` and `2>` does NOT matter when targeting **different files** (they're independent dup2 calls). It matters CRITICALLY when one of them uses `&` to alias the other — Task 2 covers that.
- `wc -l < FILE` — re-using the Lab 01a `<` pattern to count lines without a filename in the output.
- `2> /dev/null` — FD 2 opens `/dev/null` for write; every error byte is silently accepted and discarded.

### h) The story

In 1971, the first version of Unix had only stdin and stdout. Errors went to stdout, mixed with data. Then somebody piped `cc` (the C compiler) into another tool and discovered that the next tool was choking on `cc: warning: unused variable` lines that looked exactly like real code output.

So in **Version 5 Unix (1974)**, Dennis Ritchie and Ken Thompson split stderr off into a separate file descriptor. The rule from that day forward:

- **stdout (FD 1):** the program's actual answer — what you would pipe into the next command.
- **stderr (FD 2):** diagnostics — warnings, errors, progress bars, "could not open" messages. **Not** the program's answer.

Every well-behaved command since 1974 obeys this rule. `find /etc -name '*.conf'` writes file paths to FD 1 and writes `find: '/etc/secret': Permission denied` to FD 2. You can keep the paths and drop the errors, keep the errors and drop the paths, drop both, or save both to different files. RHCSA tests every one of these patterns.

### i) Expected output (shape only — your exact counts will differ)

```
── run #1: no redirect (errors and data tangled) ──
find: '/etc/grub2.cfg': Permission denied
/etc/dnf/dnf.conf
/etc/yum.conf
── (errors were lost above the head -n3 cut)
── run #2: split capture ──
stdout lines (real results): 142
stderr lines (denied paths): 18
── first 3 stdout lines (clean .conf paths) ──
/etc/dnf/dnf.conf
/etc/yum.conf
/etc/dnf/plugins/copr.conf
── first 3 stderr lines (the noise that ruined run #1) ──
find: '/etc/grub2.cfg': Permission denied
find: '/etc/sudoers': Permission denied
find: '/etc/audit': Permission denied
── run #3: clean answer (stderr discarded) ──
142 /tmp/labsandbox_02/conf-clean.txt
142 /tmp/labsandbox_02/conf-clean.txt
142 /tmp/labsandbox_02/conf-files.txt
142 /tmp/labsandbox_02/conf-files.txt
  0 /tmp/labsandbox_02/conf-errors.txt    ← stderr only file when read by user
/tmp/labsandbox_02/conf-clean.txt owner=labuser_02_stderr:labgrp_02_stderr mode=644
/tmp/labsandbox_02/conf-errors.txt owner=labuser_02_stderr:labgrp_02_stderr mode=644
/tmp/labsandbox_02/conf-files.txt  owner=labuser_02_stderr:labgrp_02_stderr mode=644
exit was: 0
```

### j) Switches table

| Token | Meaning |
|---|---|
| `2>` | Open file for truncate-write of FD 2 (stderr) |
| `2>>` | Open file for append-write of FD 2 |
| `2> /dev/null` | Discard stderr |
| `> file 2> file2` | Split streams to two different files |
| `sudo -u USER CMD` | Run CMD as USER without a login shell |
| `find DIR -name PATTERN -type f` | Walk DIR, match name PATTERN, only regular files |
| `wc -l < FILE` | Line-count via stdin (output has no filename) |
| `head -n N` | First N lines |
| `stat -c '%n %U:%G %a'` | Custom-format owner/group/mode |

### k) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | FD 1 vs FD 2 | Two independent kernel-managed file descriptors; redirecting one does NOT touch the other |
|   | `2>` | Send stderr to a file (truncate) |
|   | `2>>` | Append stderr to a file |
|   | `2> /dev/null` | Discard stderr — the RHCSA `find` reflex |
|   | Split capture | `> out 2> err` writes to two different files in one command |
|   | Tier-B weave | `sudo -u "${USER}" find ...` exercises the lab user, group, and captured files together |
| 🪤 | **Trap Risk T02-A** | `find / > /root/answer.txt` does NOT silence `Permission denied`. It captures only FD 1; FD 2 keeps hitting the screen. **Fix:** add `2>/dev/null` for the clean-answer-file pattern. |

### l) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Stdout captured | `wc -l "${SANDBOX}/conf-files.txt"` | Confirms FD 1 redirect worked |
| Stderr captured | `wc -l "${SANDBOX}/conf-errors.txt"` | Confirms FD 2 redirect worked — count should be > 0 if user really lacks perms |
| Stderr silenced | `wc -l "${SANDBOX}/conf-clean.txt"` matches stdout count | Confirms `2>/dev/null` didn't accidentally also drop stdout |
| Lab user owns files | `stat -c '%U:%G' "${SANDBOX}"/conf-*.txt` | Confirms `chown` applied |

### m) 🧹 Cleanup between tasks

```bash
set +e
podman ps -aq --filter "name=^lab_02_stderr$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null
rm -f "${SANDBOX}/conf-files.txt" "${SANDBOX}/conf-errors.txt" "${SANDBOX}/conf-clean.txt"
set -e
echo "Task-1 cleanup at $(date -Is); exit was: $?"
```

> **STOP — paste output before Task 2.**

### n) Troubleshoot

| Symptom | Fix |
|---|---|
| `stderr lines: 0` (no `Permission denied`) | Your distro / `/etc` perms let the lab user read everything — pick a harder dir (`find /var/log/...`) or run as a more restricted user |
| `stdout lines: 0` and `stderr lines: 0` | The `sudo -u` didn't actually run — check `getent passwd "${USER}"` and the user's shell (`/bin/bash`, not `/sbin/nologin`) |
| Both files have everything mixed | You wrote `2>&1` instead of `2> file2` — re-read Task 1 step 2 |
| `bash: ${SANDBOX}/conf-files.txt: cannot overwrite existing file` | noclobber leaked in from Lab 01a — `set +o noclobber` |

---

## Task 2 — Contrast: `2>>` append, order-sensitive `2>&1`, exit-code preservation

### a) Directory context

**Practice directory this task:** `/sbin` lookup + `/etc` source (same as Task 1).

### b) 🔁 Warm-Up — commands woven into Task 2

```bash
ls -la "${SANDBOX}"                                 2>&1 | tee "${SANDBOX}/warmup2.txt"
sudo -u "${USER}" ls -d "${USER_HOME}"
getent group "${GROUP}"
stat -c '%n %U:%G %a' "${SANDBOX}/THIS_DIRECTORY.txt"
grep -c 'conf' /etc/services 2>/dev/null            # warm up grep -c
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Show the three follow-on stderr patterns that turn a beginner into a senior:

1. **`2>>` append** — collect errors across multiple invocations into one growing log.
2. **`2>&1` order trap** — `cmd 2>&1 > file` and `cmd > file 2>&1` produce **different** results. Memorize which one merges.
3. **Exit code preservation** — `2>/dev/null` does NOT mask `$?`; the redirect operator returns whatever the command itself returned.

The contrast with Task 1: Task 1 was *"capture or silence."* Task 2 is *"merge correctly and never lose the exit code."*

### d) 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -la "${SANDBOX}"` | Proves Task 1 cleanup ran (`conf-*.txt` should be gone) |
| `sudo -u "${USER}" ls -d "${USER_HOME}"` | Lab user still functional and can `ls` their own home |
| `getent group "${GROUP}"` | Group survives between tasks |
| `stat ... THIS_DIRECTORY.txt` | The one file that should still exist in `${SANDBOX}` after Task 1 cleanup |
| `grep -c 'conf' /etc/services` | Exercises `-c` count flag we use below in the exit-code section |

### e) Main command block

```bash
cd "${SANDBOX}"

# 1. `2>>` append — run find twice with different patterns, both error logs land in ONE file
sudo -u "${USER}" find /etc -name '*.conf' -type f >> "${SANDBOX}/all-results.txt"  2>> "${SANDBOX}/all-errors.txt"
sudo -u "${USER}" find /etc -name '*.cfg'  -type f >> "${SANDBOX}/all-results.txt"  2>> "${SANDBOX}/all-errors.txt"
chown "${USER}:${GROUP}" "${SANDBOX}/all-results.txt" "${SANDBOX}/all-errors.txt"

R_LINES=$(wc -l < "${SANDBOX}/all-results.txt")
E_LINES=$(wc -l < "${SANDBOX}/all-errors.txt")
echo "── merged across 2 find runs ──"
echo "results lines: ${R_LINES}"
echo "errors  lines: ${E_LINES}"

# 2. Order trap — these two look identical but behave differently
echo "── order trap (T02-B) ──"

# Form A: `cmd > file 2>&1`
#   step 1: FD 1 → file
#   step 2: FD 2 → wherever FD 1 NOW goes (the file)
#   → BOTH end up in the file. The classic merge.
sudo -u "${USER}" find /etc -name '*.conf' -type f > "${SANDBOX}/formA.txt" 2>&1
A_LINES=$(wc -l < "${SANDBOX}/formA.txt")

# Form B: `cmd 2>&1 > file`
#   step 1: FD 2 → wherever FD 1 NOW goes (still the terminal!)
#   step 2: FD 1 → file
#   → stderr STILL on screen, stdout in file. Easy mistake.
sudo -u "${USER}" find /etc -name '*.conf' -type f 2>&1 > "${SANDBOX}/formB.txt"
B_LINES=$(wc -l < "${SANDBOX}/formB.txt")

echo "Form A (correct merge)  lines in file: ${A_LINES}   (should equal stdout+stderr)"
echo "Form B (wrong order)    lines in file: ${B_LINES}   (only stdout — errors went to screen)"

# 3. Exit code preservation — 2>/dev/null does NOT touch $?
echo "── exit code preservation (T02-C) ──"
sudo -u "${USER}" find /no/such/path 2>/dev/null
echo "exit after silenced failing find: $?"   # should be 1, NOT 0

sudo -u "${USER}" find /etc -name '*.conf' -type f >/dev/null 2>/dev/null
echo "exit after silenced succeeding find: $?" # should be 0

# Common idiom for "I want to know if it found anything"
if sudo -u "${USER}" grep -q 'root' /etc/passwd 2>/dev/null; then
    echo "✅ grep -q found 'root' in /etc/passwd"
else
    echo "❌ grep -q did not find — but the redirect did NOT cause the no-match"
fi

# 4. `1>&2` — deliberate stderr write from a script
echo "this message is an ERROR by design" 1>&2

echo "exit was: $?"
```

### f) Human-readable breakdown

1. `2>>` appends stderr across two `find` runs into one cumulative error log — the same data pattern as a service that's been failing intermittently.
2. Run the same command two ways: `> file 2>&1` (correct merge) vs `2>&1 > file` (wrong order). Count lines in each captured file — Form A has **everything**, Form B has only stdout.
3. Prove `2>/dev/null` does NOT affect `$?`. A failing command still exits non-zero even with its stderr silenced — this is the foundation of every `if cmd 2>/dev/null; then ...` check.
4. Use `1>&2` to deliberately write to stderr from your own script — useful for error messages in helper scripts.

### g) Reading it left to right (the order trap in detail)

The shell processes redirections **left to right**. Each redirection is one `dup2(2)` syscall.

**Form A — `cmd > file 2>&1`:**

```
Initial state:  FD 1 → terminal,  FD 2 → terminal

Step 1 (> file): open(file); dup2(opened_fd, 1);    // FD 1 → file
Step 2 (2>&1) :  dup2(1, 2);                        // FD 2 → file (because FD 1 IS file now)

Final state:    FD 1 → file,  FD 2 → file       ← BOTH go to file ✅
```

**Form B — `cmd 2>&1 > file`:**

```
Initial state:  FD 1 → terminal,  FD 2 → terminal

Step 1 (2>&1):   dup2(1, 2);                        // FD 2 → terminal (FD 1 is still terminal!)
Step 2 (> file): open(file); dup2(opened_fd, 1);    // FD 1 → file

Final state:    FD 1 → file,  FD 2 → terminal   ← stderr stays on screen ❌
```

> **The rule:** if you want both streams in one file, put the `2>&1` **after** the `>`. Or use the bash shorthand `&>` (Lab 04).

### h) The story

The order trap (T02-B) is the most "tricked an entire senior engineer in production" stderr bug in Unix history. It looks symmetric — both forms have a `>` and a `2>&1`, so it feels like order can't matter. It does. The reason is that `2>&1` copies *the current target of FD 1 at the moment the redirect is parsed*, not "whatever FD 1 will eventually be." Once you've seen the dup2 picture above, you'll never write Form B again.

Exit-code preservation (T02-C) is the other quiet killer. People silence noisy commands with `2>/dev/null` and assume the command "succeeded." It didn't — only its complaining was hidden. Always check `$?` immediately, and never trust a silenced command without it.

### i) Expected output (shape only)

```
── merged across 2 find runs ──
results lines: 284
errors  lines: 36
── order trap (T02-B) ──
Form A (correct merge)  lines in file: 160   (should equal stdout+stderr)
Form B (wrong order)    lines in file: 142   (only stdout — errors went to screen)
find: '/etc/grub2.cfg': Permission denied      ← this line appeared on YOUR SCREEN during Form B
── exit code preservation (T02-C) ──
exit after silenced failing find: 1
exit after silenced succeeding find: 0
✅ grep -q found 'root' in /etc/passwd
this message is an ERROR by design
exit was: 0
```

### j) Switches table

| Token | Meaning |
|---|---|
| `2>>` | Append-write to FD 2 target file |
| `2>&1` | Make FD 2 point wherever FD 1 currently points |
| `1>&2` | Make FD 1 point wherever FD 2 currently points (script idiom for "print to stderr") |
| `> file 2>&1` | Correct order — both streams to file |
| `2>&1 > file` | Wrong order — only stdout to file, stderr stays on screen |
| `grep -q` | Quiet mode — exit 0 if any match, 1 if none |
| `grep -c` | Count matching lines |
| `find /path` | Walk filesystem; if path doesn't exist, exit 1 with stderr message |

### k) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `2>>` append | Accumulate errors across runs into one growing file |
|   | dup2 mental model | Each redirect is one `dup2` syscall against the *current* state of the FDs |
|   | `2>&1` after `>` | Both streams merged into the file |
|   | `&>` shorthand | Bash combined-redirect (Lab 04) — equivalent to `> file 2>&1` |
|   | `1>&2` | Script idiom for "this echo is an error message" |
|   | Exit-code preservation | `2>/dev/null` hides stderr text, NOT `$?` |
|   | `grep -q` | The exit-code-only matcher; pairs perfectly with silenced stderr |
| 🪤 | **Trap Risk T02-B** | `cmd 2>&1 > file` leaves stderr on screen. **Fix:** always `> file 2>&1` (redirect FD 1 FIRST, then merge FD 2 into it). |
| 🪤 | **Trap Risk T02-C** | After `cmd 2>/dev/null` always check `$?` — silenced does not mean succeeded. **Fix:** `cmd 2>/dev/null; echo "exit was: $?"`. |

### l) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| Cumulative error log | `wc -l "${SANDBOX}/all-errors.txt"` (should be sum of two runs' errors) | Proves `2>>` didn't truncate between runs |
| Form A merge worked | `grep -c 'Permission denied' "${SANDBOX}/formA.txt"` (should be > 0) | Errors made it INTO the file |
| Form B did NOT merge | `grep -c 'Permission denied' "${SANDBOX}/formB.txt"` (should be 0) | Confirms the order trap really happened |
| Exit code is honest | `find /no/such/path 2>/dev/null; echo $?` returns 1 | `2>/dev/null` doesn't mask `$?` |

### m) 🧹 Cleanup — bulletproof teardown with audit (Section 6)

```bash
set +e

# 1) Container layer — none in this lab
podman ps -aq --filter "name=^lab_${LAB_NUM}_${LAB_SLUG}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

# 2) Mount layer — none in this lab
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 3) LVM — none
# 4) Loopback — none

# 5) User then group
if getent passwd "${USER}" >/dev/null 2>&1; then
    userdel -r "${USER}" 2>/dev/null || userdel "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
    groupdel "${GROUP}" 2>/dev/null
fi

# 6) Sandbox dir
rm -rf "${SANDBOX}"

# 7) Audit — every row MUST print ✅
echo "── cleanup audit ──"
getent passwd "${USER}"  >/dev/null 2>&1 && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null 2>&1 && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                       && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
echo "Lab cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the audit block output. Every line must read ✅ before this lab is complete (T44).**

### n) Troubleshoot

| Symptom | Fix |
|---|---|
| Form A and Form B both look the same on disk | You're running as root — `sudo -u "${USER}"` is missing or the user has full read perms |
| Form B shows `Permission denied` IN the file (not on screen) | You typed `> file 2>&1` by accident — re-read Task 2 step 2 |
| `exit after silenced failing find: 0` | Your shell collapsed the pipeline; check that `find /no/such/path` is the LAST command in its statement |
| Audit `❌ user remains` | A stale process still owns the user — `pkill -u "${USER}"`, then `userdel -r "${USER}"` |
| Audit `❌ sandbox remains` | Something holds an open FD inside `${SANDBOX}` — `lsof +D "${SANDBOX}"` to find it |

---

## 🪤 Trap Rehearsal — summary

| Trap | Description | Rehearsed where |
|---|---|---|
| **T02-A** | `>` captures FD 1 only — errors still hit the screen | Task 1 Concept Card |
| **T02-B** | `cmd 2>&1 > file` puts errors on screen, NOT in the file (order matters) | Task 2 Concept Card + dup2 explainer |
| **T02-C** | `2>/dev/null` hides the message, NOT the exit code — always check `$?` | Task 2 Concept Card + step 3 |
| **T44** | Cleanup left an orphan user/group/sandbox | Task 2 audit block |

If any trap fired (you typed `>` thinking it would silence errors, or audit showed ❌), log it per Section 12:

```
⚠️ TRAP HIT: [T02-A | T02-B | T02-C | T44] [what happened]
Repeat this trap in the next 2 labs.
```

---

## ➡️ What's next

- **Lab 02b — Ansible:** declarative version using `register: result` plus `result.stdout` / `result.stderr` — same two-stream model in YAML.
- **Lab 02c — Verify:** audit script that fails if a captured "answer file" contains any `Permission denied` line (proves the `2>/dev/null` discipline held).
- **Lab 03 — Pipes (`|`, `tee`):** what happens when you connect FD 1 of one command to FD 0 of another, and the `tee` "wye fitting" that lets you save AND pass.
- **Lab 04 — Combined (`&>`, `2>&1`):** the deep dive on stream merging, including the order trap's bash shorthand workaround.
