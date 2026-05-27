# Lab 01a: Standard Output Redirection (RHCSA) — `>`, `>>`, `cat`

- **Series:** linux-ops-mastery — Shells, Terminals & Redirection
- **Trilogy:** `01a` (RHCSA) → `01b` (Ansible, planned) → `01c` (Verify, planned)
- **Career arcs covered:** RHCSA EX200 (every "save the output to..." task), RHCE EX294 (Ansible `command:`/`shell:` `register:` mirrors `>` semantics), SRE (incident-evidence capture without losing prior log lines), DevOps (CI/CD artifact files), AI/MLOps (training-script stdout → experiment log)
- **Prerequisite:** Basic shell familiarity — you can `ls`, `pwd`, `cat`, and you know what a file path is
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 canonical, Task 2 contrast)
- **Practice Directory (rotation #01):** `/bin`
- **Sandbox:** `/tmp/labsandbox_01`
- **Sandbox User/Group:** `labuser_01_stdout` / `labgrp_01_stdout`
- **📌 ANCHOR TYPE:** none (regular lab)
- **📌 TRILOGY POS:** `a` (rhcsa)
- **📌 PREREQ:** —
- **Traps rehearsed this lab:** **T01-A** (`>` truncates BEFORE the command runs — pre-existing content lost) · **T01-B** (`cat file > file` — self-clobber, file ends up empty) · **T44** (cleanup audit — must verify no orphan user/group/sandbox)

> **This lab's practice directory is: `/bin`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T01-A T01-B T44"
echo "📁  PRACTICE DIR: /bin"
echo ""
echo "💡 /bin occupants (read-only context — we never write here):"
ls -ld /bin
ls /bin | wc -l
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Make output redirection a reflex. By the end of this lab you can:

1. Send the stdout of any command to a file with `>` (truncate) or `>>` (append) without losing data you needed.
2. Read it back with `cat` and confirm what landed on disk matches what was on screen.
3. Survive the two redirection traps that cost real RHCSA points: **truncate-before-run** and **self-redirect-clobbers-source**.

Every RHCSA task that says *"save the output of X to /root/Y"* reduces to a `>` or `>>` decision plus a `cat` verification. You will own both decisions.

---

## 🧠 Concept: stdout Is a Stream, Not a Screen

When a command "prints to the screen," what actually happens is the kernel writes bytes to **file descriptor 1** of the process. The terminal happens to be connected to FD 1 by default, but FD 1 is a *handle* — point it at a file and the bytes land in the file instead.

```
   ┌─────────────────────────────────────────────────────┐
   │   Your command (ls, ps, cat, awk, find, ...)        │
   ├─────────────────────────────────────────────────────┤
   │   FD 0  stdin   ← keyboard (default)                │
   │   FD 1  stdout  → terminal screen (default)         │  ← `>`, `>>` retarget THIS
   │   FD 2  stderr  → terminal screen (default)         │      (lab 02 covers FD 2)
   └─────────────────────────────────────────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
            `> file`                       `>> file`
       truncate then write              create if missing, append
       (destroys existing content)      (preserves existing content)
```

The shell sets up the redirection **before** the command starts. That means `cmd > existing.txt` empties `existing.txt` first, then runs `cmd`. If `cmd` fails immediately, you've lost the file's content for nothing. This is **trap T01-A** and it costs exam points every year.

---

## 📚 Redirection Reference (everything used in Tasks 1–2)

| Pattern | What it does | First reach for it when... |
|---|---|---|
| `cmd > file` | Truncate `file` (or create), write stdout | First write of a fresh artifact |
| `cmd >> file` | Append stdout, create if missing | Adding to logs / notes / collected output |
| `cmd > /dev/null` | Discard stdout | Suppress noisy command output |
| `set -o noclobber` | Refuse `>` on existing files | Script safety net |
| `cmd >\| file` | Force overwrite even under noclobber | Explicit "yes, clobber" override |
| `cat FILE` | Stream `FILE` to stdout | Read back what `>` just wrote |
| `cat F1 F2` | Concatenate F1 then F2 to stdout | Combine multiple captures |
| `cat <<'EOF' > file` | Heredoc into a file | Write multi-line content with quoted vars |

> **Rule of `>`:** every `>` is a *destructive write*. Pre-flight with `ls -l FILE` if the file already exists. If you want to keep what's there, use `>>`.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1  (per Section 1.5 of the prompt)

```bash
sudo -i

# Section 1.5 — strict naming so cleanup never collides
export LAB_NUM=01
export LAB_SLUG=stdout
export SANDBOX=/tmp/labsandbox_${LAB_NUM}
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd \
    -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Practice-directory context note
cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/bin — Essential user commands (ls, cp, cat)

Every command a logged-in user needs to survive without any other
filesystem mounted lives here. /bin is on the root partition by
design — if /usr is not mounted yet, /bin still works. On modern
RHEL, /bin is a symlink to /usr/bin.

Why this matters for stdout redirection: /bin is the canonical
read-only source we point commands at (ls /bin, find /bin, etc.)
so the *output* we redirect is real and reproducible without us
needing to invent test data.
EOF

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
cat "${SANDBOX}/THIS_DIRECTORY.txt"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output (id, ls, exit code) before Task 1.**

---

## Task 1 — Canonical: truncate-write with `>`, append with `>>`

### a) Directory context

**Practice directory this task:** `/bin` · Essential user commands — read-only source for our redirected output.

### b) 🔁 Warm-Up — commands woven into Task 1

```bash
ls -ld /bin                                         2>&1 | tee "${SANDBOX}/warmup1.txt"
wc -l < /bin/.. 2>/dev/null; ls /bin | wc -l        # count of /bin entries
getent passwd "${USER}"
id -nG "${USER}"
set -o noclobber 2>/dev/null; set +o noclobber      # cycle the option (Task 2 uses it for real)
test -d "${SANDBOX}" && echo "sandbox OK"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Use `>` to create a fresh capture of `ls /bin`, then use `>>` to append a timestamped footer to the same file. Read it back with `cat`. The capture is owned by the lab user so the Tier-B sandbox stack does real work.

### d) 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -ld /bin` | Pre-flight proof that the source dir exists *before* we redirect from it |
| `ls /bin \| wc -l` | Baseline count — the redirected file must have exactly this many lines |
| `getent passwd "${USER}"` | Confirms the lab user exists before we `chown` the captured file |
| `id -nG "${USER}"` | Verifies the primary group name matches `${GROUP}` (otherwise `chown user:group` would silently fail) |
| `test -d "${SANDBOX}"` | Guards the `> ${SANDBOX}/...` redirection — refuses to redirect into a missing dir |
| `$(date -Is)` | Stamps the footer line appended via `>>` |

### e) Main command block

```bash
cd "${SANDBOX}"

# Pre-flight: prove the source exists and count expected lines
BIN_COUNT=$(ls /bin | wc -l)
echo "expect ${BIN_COUNT} lines in capture"

# 1. Truncate-write — `>` creates ${SANDBOX}/bin-list.txt fresh
ls /bin > "${SANDBOX}/bin-list.txt"

# 2. Read it back and verify line count matches the baseline
CAP_COUNT=$(wc -l < "${SANDBOX}/bin-list.txt")
echo "captured ${CAP_COUNT} lines (baseline was ${BIN_COUNT})"
test "${CAP_COUNT}" -eq "${BIN_COUNT}" && echo "✅ counts match"

# 3. Append-write — `>>` adds a timestamped footer WITHOUT losing content
echo "# captured by $(whoami) at $(date -Is)" >> "${SANDBOX}/bin-list.txt"
echo "# host: $(hostname) kernel: $(uname -r)"   >> "${SANDBOX}/bin-list.txt"

# 4. Hand ownership to the lab user — Tier B requirement
chown "${USER}:${GROUP}" "${SANDBOX}/bin-list.txt"

# 5. Lab user reads it back — prove the user/group/file relationship
sudo -u "${USER}" tail -n 5 "${SANDBOX}/bin-list.txt"

# 6. stat audit — owner, group, mode, line count one more time
stat -c '%n owner=%U:%G mode=%a' "${SANDBOX}/bin-list.txt"
wc -l "${SANDBOX}/bin-list.txt"

echo "exit was: $?"
```

### f) Human-readable breakdown

1. Snapshot how many entries `/bin` has so we have something to verify against.
2. Use `>` to overwrite-create `bin-list.txt` with the directory listing.
3. Count the lines in the captured file and confirm they match.
4. Use `>>` twice to *append* a comment header and a host-info line — without losing the listing.
5. Hand the file over to the lab user via `chown`.
6. Read the last 5 lines **as the lab user** (`sudo -u "${USER}"`) to prove the permissions actually let them read it.
7. Print the final ownership, mode, and line count for the audit.

### g) Reading it left to right

- `ls /bin > "${SANDBOX}/bin-list.txt"` — the shell **opens the file for truncate-write first**, then runs `ls`. If `ls` had failed, the file would already be empty.
- `wc -l < FILE` — `<` is the input-redirection counterpart of `>`. `wc -l` reads stdin instead of opening the file itself, so the printed line has no filename. We use it here to capture the count cleanly into a variable.
- `>>` appends without truncating — same lock-and-write sequence as `>`, but the file pointer starts at the end of file (`O_APPEND`).
- `chown user:group FILE` — changes ownership; quotes around `"${USER}:${GROUP}"` defend against empty-variable expansion (trap-style discipline).
- `sudo -u "${USER}" tail -n 5 FILE` — runs `tail` as the lab user; if file mode or ownership were wrong, `tail` would fail with `Permission denied` and we'd catch it.
- `stat -c '%n owner=%U:%G mode=%a'` — `%n` filename, `%U:%G` owner:group **names** (not numeric IDs), `%a` octal mode.

### h) The story

`>` and `>>` are not "shell tricks." They are the original design of how a Unix program talks to the outside world, dating to 1969 on the PDP-7. Ken Thompson's insight was that every program writes to FD 1 and the **shell** decides what FD 1 is connected to — the terminal, a file, a pipe, another process. That single decision created redirection, pipes, `tee`, and the whole composable-tools philosophy.

The reason RHCSA tests this so heavily is that every grader script reads files, not screens. If your answer scrolled past instead of landing in `/root/answer.txt`, you scored zero on a question you knew. Reflex matters.

### i) Expected output (shape only — your exact line counts will differ)

```
expect 168 lines in capture
captured 168 lines (baseline was 168)
✅ counts match
# captured by root at 2026-05-27T16:35:02-04:00
# host: rhel9.lab kernel: 5.14.0-503.el9.x86_64
/tmp/labsandbox_01/bin-list.txt owner=labuser_01_stdout:labgrp_01_stdout mode=644
170 /tmp/labsandbox_01/bin-list.txt
exit was: 0
```

### j) Switches table

| Token | Meaning |
|---|---|
| `>` | Open file for truncate-write of FD 1 (stdout) |
| `>>` | Open file for append-write of FD 1 (no truncate) |
| `<` | Open file as FD 0 (stdin) — used here with `wc -l` |
| `wc -l` | Count newlines |
| `stat -c '%n %U:%G %a'` | Custom-format stat output: name, owner:group, mode |
| `sudo -u USER CMD` | Run CMD as USER (not via login shell) |
| `chown user:group` | Set owner and primary group |
| `test "$A" -eq "$B"` | Integer equality test for shell `if`/`&&` chains |
| `$(...)` | Command substitution — capture stdout of `...` into the current command line |

### k) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `>` | Truncate-write FD 1 to a file |
|   | `>>` | Append-write FD 1 to a file |
|   | `<` | File becomes FD 0 (stdin) |
|   | Open-before-run | Shell opens/truncates the target *before* the command starts — failed command still empties the file |
|   | Command substitution | `$(...)` captures stdout into the calling command line |
|   | Tier-B weave | The `chown ${USER}:${GROUP}` + `sudo -u ${USER}` pair exercises the sandbox user, group, and file simultaneously |
|   | Pre-flight | `ls /bin \| wc -l` baseline before `>` redirect makes count verification possible |
| 🪤 | **Trap Risk T01-A** | `cmd > existing.txt` empties `existing.txt` BEFORE `cmd` runs. If `cmd` fails (typo, missing file), you've destroyed the original for nothing. **Fix:** `ls -l FILE` first, or use `>>`, or `set -o noclobber`. |

### l) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| File on disk via `>` | `cat "${SANDBOX}/bin-list.txt"` | Confirms data survived past the shell session |
| Append via `>>` | `tail -n 2 "${SANDBOX}/bin-list.txt"` | Confirms `>>` didn't truncate |
| Ownership transfer | `stat -c '%U:%G' "${SANDBOX}/bin-list.txt"` | Confirms `chown` applied |
| Lab user can read | `sudo -u "${USER}" cat "${SANDBOX}/bin-list.txt" \| wc -l` | Confirms group/mode permits the user to read |

> If `/tmp` is `tmpfs` (RAM-backed) on your distro, the file does NOT survive reboot — that's expected. The persistence check above is for **session persistence**, not reboot persistence.

### m) 🧹 Cleanup — bulletproof teardown (Section 6)

Run this BEFORE Task 2 so each task starts from a clean state, then run the same block again at the end of Task 2 with the audit.

```bash
set +e

# Containers — none in this lab, no-op
podman ps -aq --filter "name=^lab_01_stdout$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

# Mounts under sandbox — none in this lab, no-op
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# Sandbox file (Task 1 artifact) — let Task 2 rebuild if needed
rm -f "${SANDBOX}/bin-list.txt"

set -e
echo "Task-1 cleanup at $(date -Is); exit was: $?"
```

> **STOP — paste output before Task 2.**

### n) Troubleshoot

| Symptom | Fix |
|---|---|
| `bash: !${SANDBOX}/bin-list.txt: event not found` | History expansion bit you — `set +H` or escape the `!`, but better: don't put `!` in lab filenames |
| `Permission denied` when `sudo -u "${USER}" tail ...` | The file mode is too restrictive — `chmod 0644 "${SANDBOX}/bin-list.txt"` |
| Captured line count is **0** even though `ls /bin` shows files | You ran `cat file > file` (T01-C) — the shell truncated `file` before `cat` opened it for read |
| `useradd: user "labuser_01_stdout" already exists` | The previous lab didn't clean up — re-run the Section 6 audit, then `userdel -r` manually |

---

## Task 2 — Contrast: `noclobber`, force-overwrite `>|`, discard `/dev/null`

### a) Directory context

**Practice directory this task:** `/bin` (continued) — still our read-only source.

### b) 🔁 Warm-Up — commands woven into Task 2

```bash
ls -la "${SANDBOX}"                                 2>&1 | tee "${SANDBOX}/warmup2.txt"
stat -c '%n owner=%U:%G mode=%a' "${SANDBOX}/warmup2.txt"
getent group "${GROUP}"
sudo -u "${USER}" pwd
set -o noclobber       # leave it ON for this task — the lesson IS the safety net
grep -E '^(bin|sbin)$' /etc/passwd | wc -l    # likely 0 but exercises grep -E + wc
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Show what `>` actually **costs you** when you don't think. Cycle through three safer alternatives:
- `set -o noclobber` — the shell refuses to clobber existing files via `>`.
- `>|` — explicit override that says "yes, I really mean clobber it."
- `> /dev/null` — when the output is what you *don't* want.

The contrast with Task 1: Task 1 was *"capture the output."* Task 2 is *"protect what's already on disk, and discard what doesn't matter."*

### d) 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -la "${SANDBOX}"` | Proves a file already exists before we try to clobber it — required so the noclobber error actually fires |
| `stat -c ... warmup2.txt` | The target of the noclobber-protected `>` attempt — we want to prove mode/owner survived the attempted clobber |
| `getent group "${GROUP}"` | Confirms group still exists (i.e. nothing from Task 1's cleanup over-deleted) |
| `sudo -u "${USER}" pwd` | Proves the lab user can still authenticate / has a shell after Task 1's cleanup |
| `set -o noclobber` | THE feature under test — already turned on so the `>` attempt below triggers `cannot overwrite existing file` |

### e) Main command block

```bash
# 1. Re-create a target file so we have something to "almost clobber"
echo "important data — do not lose me" > "${SANDBOX}/precious.txt"
chown "${USER}:${GROUP}" "${SANDBOX}/precious.txt"
ls -l "${SANDBOX}/precious.txt"

# noclobber is already ON from the warm-up — confirm:
set -o | grep noclobber

# 2. Attempt to clobber — MUST fail under noclobber
ls /bin > "${SANDBOX}/precious.txt" \
    && echo "❌ clobber succeeded (noclobber failed?)" \
    || echo "✅ noclobber blocked the clobber  (exit=$?)"

# Prove the file is intact
cat "${SANDBOX}/precious.txt"

# 3. Explicit force-overwrite — `>|` overrides noclobber
ls /bin >| "${SANDBOX}/precious.txt"
wc -l    "${SANDBOX}/precious.txt"
head -n3 "${SANDBOX}/precious.txt"

# 4. Discard pattern — `> /dev/null` throws stdout away
echo "this never lands in any file" > /dev/null
echo "exit of the discard write: $?"

# 5. Append-with-discard idiom — keep stderr, drop stdout
ls /bin /no/such/dir > /dev/null 2>&1
echo "exit when both streams discarded: $?"

# 6. Reset noclobber so the next lab inherits a normal shell
set +o noclobber
set -o | grep noclobber

echo "exit was: $?"
```

### f) Human-readable breakdown

1. Make a file that holds real data.
2. With `noclobber` already on, **try** to clobber the file using `>` — the shell refuses with `cannot overwrite existing file`.
3. Use `>|` to **explicitly** override noclobber when you mean it.
4. Throw output away with `> /dev/null` — the canonical "I don't care about stdout."
5. Combine `> /dev/null 2>&1` to silence both streams (Lab 04 covers `2>&1` fully).
6. Reset `noclobber` so the next lab in your session isn't surprised.

### g) Reading it left to right

- `ls /bin > "${SANDBOX}/precious.txt"` under noclobber: the shell calls `open(2)` with `O_CREAT|O_WRONLY|O_EXCL`; the existing file makes `open` return `EEXIST`; the shell prints `bash: precious.txt: cannot overwrite existing file` and **`ls` never runs**.
- `&&` vs `||` after the redirect — `||` is reached because the redirect failed (exit 1), so we see the success message.
- `>|` is a single token: pipe is part of the operator, not a separate pipe stage. It means "force overwrite even under noclobber."
- `> /dev/null` opens the kernel's bit-bucket device for write; all bytes are silently accepted and discarded.
- `2>&1` after `>` says "make FD 2 point wherever FD 1 currently points" — but order matters; this is Lab 04's deep dive.
- `set +o noclobber` — `+o` turns options off; `-o` turns them on.

### h) The story

`noclobber` is the seatbelt you put on when you write scripts that touch real production files. It refuses `>` on existing files by default, forcing you to type `>|` when you really mean it. Senior engineers who've lost a config file once *always* turn this on in scripts. The exam doesn't require it — but a senior engineer's instinct does, which is why it appears in real Red Hat training material.

`/dev/null` is a Unix invention: a device file that accepts any write and silently discards it. Pointing FD 1 (or both FD 1 and FD 2) at `/dev/null` is how you call a command for its **side effect** (exit code, file creation, log line elsewhere) without polluting your terminal.

### i) Expected output (shape only)

```
-rw-r--r--. 1 labuser_01_stdout labgrp_01_stdout 33 May 27 16:38 /tmp/labsandbox_01/precious.txt
noclobber       	on
bash: /tmp/labsandbox_01/precious.txt: cannot overwrite existing file
✅ noclobber blocked the clobber  (exit=1)
important data — do not lose me
168 /tmp/labsandbox_01/precious.txt
[
[[
2to3-3.9
exit of the discard write: 0
exit when both streams discarded: 2
noclobber       	off
exit was: 0
```

### j) Switches table

| Token | Meaning |
|---|---|
| `set -o noclobber` | Refuse `>` on existing files |
| `set +o noclobber` | Allow `>` to clobber again |
| `>\|` | Force overwrite even when noclobber is set |
| `> /dev/null` | Discard stdout |
| `2>&1` | Duplicate FD 2 to point at whatever FD 1 currently points at |
| `&&` | Run next command only if previous exit was 0 |
| `\|\|` | Run next command only if previous exit was non-zero |

### k) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `set -o noclobber` | Shell-level safety against accidental `>` overwrite |
|   | `>\|` | Explicit "yes, clobber" override |
|   | `> /dev/null` | Discard stdout when output is unwanted |
|   | `> /dev/null 2>&1` | Discard both streams (Lab 04 detail) |
|   | `&&` / `\|\|` | Short-circuit chain based on previous exit code |
|   | `set +o`/`-o` | Plus turns option OFF, minus turns option ON (counter-intuitive — memorize) |
| 🪤 | **Trap Risk T01-B** | `cat file > file` clobbers `file` to empty BEFORE `cat` opens it for read — you'll lose the file in a script. **Fix:** redirect to a temp, then `mv`: `cat file > file.tmp && mv file.tmp file`. |

### l) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| noclobber state across runs | `set -o \| grep noclobber` | Confirms we left the shell in the state we expected |
| Original file survived | `cat "${SANDBOX}/precious.txt"` (BEFORE step 3) | Confirms `>` refused under noclobber |
| Force-overwrite worked | `wc -l "${SANDBOX}/precious.txt"` (AFTER step 3) | Confirms `>\|` actually overwrote |

### m) 🧹 Cleanup — bulletproof teardown with audit (Section 6)

This is the **full** Section 6 block. Run it at the end of Task 2 to close the lab cleanly.

```bash
set +e

# 1) Container layer — no containers in this lab
podman ps -aq --filter "name=^lab_${LAB_NUM}_${LAB_SLUG}$" 2>/dev/null \
    | xargs -r podman rm -f >/dev/null 2>&1

# 2) Mount layer — no mounts in this lab
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts \
    | tac | xargs -r -n1 umount -l 2>/dev/null

# 3) LVM layer — none
# 4) Loopback — none

# 5) User then group (user owns files inside USER_HOME and SANDBOX)
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

# Reset noclobber if Task 2 left it on
set +o noclobber

set -e
echo "Lab cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the audit block output. Every line must read ✅ before this lab is complete (T44).**

### n) Troubleshoot

| Symptom | Fix |
|---|---|
| `cannot overwrite existing file` after `set +o noclobber` | You toggled wrong — `+o` is OFF, `-o` is ON. Re-run `set +o noclobber`. |
| Audit shows `❌ user remains` | Some process is still running as the user — `pkill -u "${USER}"` then re-run `userdel -r`. |
| Audit shows `❌ sandbox remains` | Something in `${SANDBOX}` is open (open file handle from an editor); close it and `rm -rf` again. |
| `userdel: user labuser_01_stdout is currently used by process N` | Same as above — kill stale processes first. |

---

## 🪤 Trap Rehearsal — summary

| Trap | Description | Rehearsed where |
|---|---|---|
| **T01-A** | `>` truncates BEFORE the command runs — failed command empties the file for nothing | Task 1 Concept Card |
| **T01-B** | `cat file > file` clobbers its own source to empty | Task 2 Concept Card |
| **T44** | Cleanup left an orphan user/group/sandbox — next lab inherits broken state | Task 2 audit block |

If any trap fired during the lab (you typed `>` when you meant `>>`, or the audit showed ❌), log it per Section 12:

```
⚠️ TRAP HIT: [T01-A | T01-B | T44] [what happened]
Repeat this trap in the next 2 labs.
```

---

## ➡️ What's next

- **Lab 01b — Ansible:** declarative version using `ansible.builtin.copy` and `ansible.builtin.shell` with `register:` — same `>`/`>>` semantics expressed as idempotent tasks.
- **Lab 01c — Verify:** audit script that diff-compares a fresh capture against a reference, catching the silent T01-B self-clobber.
- **Lab 02a — stderr (`2>`, `2>/dev/null`):** the second stream, the noisy `find /` problem, exit-code preservation through `2>`.
