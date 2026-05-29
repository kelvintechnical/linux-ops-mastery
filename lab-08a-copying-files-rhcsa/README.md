# Lab 08a: Copying Files & Directories (RHCSA) — `cp`, `cp -R`, `cp -a`, `cp --preserve`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** **`08a` (RHCSA — you are here)** → `08b` (Ansible) → `08c` (Verify)
- **Career arcs covered:** RHCSA EX200 (`cp`, `/etc/skel`, backup/restore), RHCE EX294 (ansible.builtin.copy mental model), SRE (config replication, golden-image staging), DevOps (artifact promotion between environments)
- **Prerequisite:** Lab 07 (timestamps + `stat`, so the mtime preservation story makes sense)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (ADHD spec — Task 1 single-file canonical, Task 2 recursive + preserve-everything contrast)
- **Practice Directory (rotation #08):** `/etc/skel`
- **Sandbox:** `/tmp/copy-lab/`
- **Traps rehearsed this lab:** **T08-A** (`cp DIR DST` without `-R` silently does nothing useful — only the bare error remains) · **T08-B** (`cp -R src/ dst/` with trailing slash on src copies CONTENTS; without the slash copies the DIRECTORY itself) · **T08-C** (`cp` without `--preserve=context` strips SELinux labels — the #1 cause of httpd "permission denied" on copied web content)

> **This lab's practice directory is: `/etc/skel`** — every task references it at least twice. `/etc/skel` is read-only context (the new-user-home template); we write only inside `/tmp/copy-lab/`.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T08-A T08-B T08-C"
echo "📁  PRACTICE DIR: /etc/skel"
echo ""
echo "💡 /etc/skel contents (read-only — this is the new-user-home template):"
ls -laZ /etc/skel
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Copy files and directory trees with **deliberate control over metadata**. By the end of this lab you can:

- Choose between `cp`, `cp -R`, `cp -a`, and `cp --preserve=...` like a senior admin
- Predict whether `cp` will overwrite, prompt, or skip — before you press Enter
- Explain exactly what `cp -a` preserves (mode, ownership, timestamps, symlinks, SELinux context, xattrs)
- Deploy `/etc/skel` into a brand-new user home directory with all metadata intact, RHCSA-grade

---

## 🧠 Concept: `cp -a` vs `cp -R` vs `cp --preserve=...`

Plain `cp` copies bytes. That's all it guarantees. Everything else — mode, owner, mtime, SELinux context — gets **reset to whatever the destination's parent dictates**. That is the source of most "I copied the file but the service still won't read it" incidents.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  cp SRC DST                                                     │
   ├─────────────────────────────────────────────────────────────────┤
   │  data       → copied exactly                                    │
   │  mode       → source's mode (masked by umask for new files)     │
   │  owner      → CALLING USER (not source's owner)                 │
   │  group      → calling user's primary group                      │
   │  mtime      → NOW                                               │
   │  atime      → NOW                                               │
   │  SELinux    → parent directory's default context                │
   │  symlinks   → FOLLOWED (you get the file, not the link)         │
   └─────────────────────────────────────────────────────────────────┘
```

`cp -R` adds recursion but **does not** add preservation. `cp -a` (archive) is shorthand for `cp -dR --preserve=all` — recursion plus full metadata, plus symlinks-as-symlinks. `cp --preserve=ATTRIBUTES` lets you cherry-pick exactly which attributes to keep: `mode`, `ownership`, `timestamps`, `links`, `context`, `xattr`, or `all`. `cp --no-preserve=ATTR` is the negation when you want `-a` *minus* one specific thing.

> **The RHCSA reflex:** when a question says "preserve everything," reach for `cp -a`. When it says "preserve just timestamps and SELinux context," reach for `cp --preserve=timestamps,context`. When it says "make sure the destination is owned by the calling user even though the source is root-owned," reach for `cp -a --no-preserve=ownership`.

---

## 📚 `cp` Reference (everything you need for Tasks 1–2)

| Switch | Meaning | Why it matters |
|---|---|---|
| `cp SRC DST` | Base copy | Data only — metadata reset to defaults |
| `cp -i` | Interactive (prompt before overwrite) | Safer for ad-hoc shell; default in root's aliased shell |
| `cp -n` | No-clobber (skip existing) | Idempotent without prompting |
| `cp -v` | Verbose (`'src' -> 'dst'`) | Audit trail |
| `cp -f` | Force (overwrite without prompt) | Pair carefully with `-i` |
| `cp -R` / `cp -r` | Recursive | Required for directories |
| `cp -a` | Archive = `-dR --preserve=all` | The "preserve everything" answer |
| `cp -p` | Preserve mode + ownership + timestamps | Subset of `-a` |
| `cp -d` | Preserve symlinks as symlinks | Subset of `-a` |
| `cp --preserve=mode,timestamps,context` | Enumerate exact attributes | Fine-grained |
| `cp --preserve=all` | Everything (= `-a`) | Explicit form |
| `cp --no-preserve=ownership` | Drop one attribute from `-a` | "Preserve everything *except* ownership" |
| `ls -lZ` | DAC + SELinux in one row | Auditor's primary view |
| `stat -c '%a %U:%G %y'` | Mode, owner, mtime in one shot | Scriptable metadata check |

> **Rule of `cp`:** Pick the smallest preservation set the task actually requires. `cp` for "just copy bytes." `cp -p` for "keep timestamps + owner." `cp -a` for "make it indistinguishable from the original." `cp --preserve=context` when SELinux is what matters and DAC reset is fine.

---

## 🚦 Lab-Wide Setup — run BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/copy-lab/new-home
mkdir -p /tmp/copy-lab/src
mkdir -p /root/rhcsa_journal/lab-08a

# Confirm /etc/skel exists and capture its baseline (we never write to it)
ls -laZ /etc/skel | tee /tmp/copy-lab/skel-baseline.txt
stat -c 'skel-mtime=%y skel-context=%C' /etc/skel
find /etc/skel -maxdepth 2 | tee -a /tmp/copy-lab/skel-baseline.txt

# Seed a single regular file inside the writable sandbox for Task 1
echo "hello from src"   > /tmp/copy-lab/src/file.txt
echo "secret payload"   > /tmp/copy-lab/src/secret.txt
chmod 600                 /tmp/copy-lab/src/secret.txt
touch -t 202001151200    /tmp/copy-lab/src/file.txt
ls -lZ /tmp/copy-lab/src/

echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

## Task 1 — Single-file `cp`, `cp -i`, `cp -v`, and the directory-vs-file destination semantics

**Practice directory this task:** `/etc/skel` (read), `/tmp/copy-lab/` (write) · `/etc/skel` is the canonical "new-user home template" — every command in Task 1 reads from `/etc/skel` or operates inside `/tmp/copy-lab/`, never the other way around.

### 🔁 Warm-Up — commands woven into Task 1

```bash
ls -laZ /etc/skel                                   2>&1 | tee /tmp/copy-lab/warmup-pre.txt
wc -l /tmp/copy-lab/skel-baseline.txt
test -d /etc/skel && echo "skel template OK"
stat -c '%n mode=%a owner=%U:%G mtime=%y' /etc/skel/.bashrc 2>/dev/null
set -o pipefail
find /tmp/copy-lab -maxdepth 1                       2>/dev/null | wc -l
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Lab 07: `stat -c '%y'` (mtime) and `ls -lZ` (SELinux context) are the two commands you ALWAYS run before AND after a `cp` so you can prove what changed.

### Purpose

Run `cp` in three distinct safety modes (silent, interactive, verbose) against single-file targets. Then demonstrate the **directory-vs-file destination** distinction: `cp SRC DST` where `DST` is a directory copies SRC *into* it; where `DST` is a regular file, it overwrites; where `DST` is a missing path, it creates that path as the new file. Each variant gets a paired before/after metadata snapshot so the trap (T08-A — metadata silently resets) is visible.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -laZ /etc/skel` | Snapshot **before** every `cp` so we can prove what we copied |
| `stat -c '%y %C'` | Reads the **mtime + SELinux context** of source AND destination — pair the two outputs to expose T08-A |
| `test -d /etc/skel` | Guards the `cp /etc/skel/...` calls — only run if the template exists |
| `2>&1 \| tee` | Captures each `cp -v` line into `task1/op.txt` for the journal |
| `set -o pipefail` | Required so a silent `tee` failure can't hide a failed `cp` |
| `$(date -Is)` | Stamps the journal `notes.txt` with completion time |

### Main command block

```bash
cd /tmp/copy-lab
mkdir -p /tmp/copy-lab/task1
mkdir -p /tmp/copy-lab/task1/dst-dir

BEFORE_SRC=$(stat -c 'mtime=%y ctx=%C' /tmp/copy-lab/src/file.txt)

# ── Variant A — cp to a MISSING path (creates the destination file) ──
cp /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/file-copy.txt
ls -lZ /tmp/copy-lab/task1/file-copy.txt             | tee /tmp/copy-lab/task1/op.txt

# ── Variant B — cp to an EXISTING DIRECTORY (becomes DIR/$(basename SRC)) ──
cp /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/dst-dir/
ls -lZ /tmp/copy-lab/task1/dst-dir/                  | tee -a /tmp/copy-lab/task1/op.txt

# ── Variant C — cp -i to an EXISTING FILE (prompts; heredoc answers y) ──
cp -i /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/file-copy.txt <<< "y"
echo "(cp -i answered y from herestring)"            | tee -a /tmp/copy-lab/task1/op.txt

# ── Variant D — cp -v for verbose audit trail ──
cp -v /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/file-copy.v.txt \
                                                     2>&1 | tee -a /tmp/copy-lab/task1/op.txt

# ── Variant E — cp -n no-clobber (skip existing silently) ──
cp -n /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/file-copy.v.txt
echo "(cp -n: silent skip when dst exists)"          | tee -a /tmp/copy-lab/task1/op.txt

# ── T08-A demonstration: copy /etc/skel/.bashrc and watch metadata reset ──
if test -f /etc/skel/.bashrc; then
  cp /etc/skel/.bashrc /tmp/copy-lab/task1/bashrc.copy
  echo "── T08-A: metadata drift after plain cp ──"   | tee -a /tmp/copy-lab/task1/op.txt
  stat -c 'src  mtime=%y ctx=%C' /etc/skel/.bashrc    | tee -a /tmp/copy-lab/task1/op.txt
  stat -c 'dst  mtime=%y ctx=%C' /tmp/copy-lab/task1/bashrc.copy \
                                                      | tee -a /tmp/copy-lab/task1/op.txt
fi

AFTER_SRC=$(stat -c 'mtime=%y ctx=%C' /tmp/copy-lab/src/file.txt)
echo "src before: $BEFORE_SRC"
echo "src after:  $AFTER_SRC  (must match — cp never mutates the source)"
echo "exit was: $?"
```

### Human-readable breakdown

1. Snapshot the source's mtime and SELinux context up front (`BEFORE_SRC`) so we can prove `cp` does not mutate the source.
2. **Variant A** — `cp SRC DST` where `DST` does not exist: creates `DST` as a regular file containing SRC's bytes.
3. **Variant B** — `cp SRC DIR/` where `DIR` already exists as a directory: drops a copy inside as `DIR/$(basename SRC)`.
4. **Variant C** — `cp -i SRC EXISTING_FILE`: prompts `cp: overwrite 'EXISTING_FILE'?`; the heredoc `<<< "y"` feeds the answer.
5. **Variant D** — `cp -v` prints `'src' -> 'dst'` — the canonical audit-friendly form.
6. **Variant E** — `cp -n` silently skips when the destination exists (idempotent, no prompt).
7. **T08-A demonstration** — copy `/etc/skel/.bashrc` to the sandbox and read both `stat -c '%y %C'` outputs side by side. The mtime drift and the SELinux context change are the trap, made visible.

### Reading it left to right

- `cp /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/file-copy.txt` — three tokens: command, source, destination. Destination is **missing**, so it gets created as a file.
- `cp /tmp/copy-lab/src/file.txt /tmp/copy-lab/task1/dst-dir/` — trailing slash on the destination is the visual cue that it must already be a directory. The result is `dst-dir/file.txt`.
- `cp -i SRC DST <<< "y"` — `-i` makes `cp` read from stdin; `<<< "y"` is a herestring that supplies the answer non-interactively.
- `cp -v SRC DST` — verbose; one line per copy in the form `'SRC' -> 'DST'`.
- `cp -n SRC EXISTING_DST` — no-clobber; no output, no error, exit 0 even though nothing happened.
- `stat -c 'mtime=%y ctx=%C' PATH` — custom format: `%y` is human-readable mtime, `%C` is the SELinux context.

### The story

A grader hands you the task: "Copy `/etc/skel/.bashrc` to `/root/backup.bashrc`." The literal answer is `cp /etc/skel/.bashrc /root/backup.bashrc` — RHCSA-correct for the **data** — but the destination's mtime is now NOW (not the source's mtime), the destination's SELinux context is `admin_home_t` (not `etc_t` like the source), and the destination is owned by the calling user (root, here). For most exam questions that's fine. For "preserve the original" it is **wrong**, and Task 2 is where you reach for `cp -a`.

The directory-vs-file destination distinction is the subtle one. `cp SRC DST` where `DST` is a *directory* drops the copy inside it; where `DST` is missing or a regular file, `DST` itself becomes the copy. The trailing slash on `DST` is a self-documenting hint to the reader and a soft signal to the shell ("I expect this to already be a directory"). Build the habit of writing the trailing slash whenever you intend the directory form — future-you will read it correctly in three months.

### Expected output

```text
-rw-r--r--. 1 root root unconfined_u:object_r:user_tmp_t:s0 15 May 28 ... /tmp/copy-lab/task1/file-copy.txt
total 4
-rw-r--r--. 1 root root unconfined_u:object_r:user_tmp_t:s0 15 May 28 ... file.txt
(cp -i answered y from herestring)
'/tmp/copy-lab/src/file.txt' -> '/tmp/copy-lab/task1/file-copy.v.txt'
(cp -n: silent skip when dst exists)
── T08-A: metadata drift after plain cp ──
src  mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
dst  mtime=2026-05-28 20:01:00.000000000 -0400 ctx=unconfined_u:object_r:user_tmp_t:s0
src before: mtime=2020-01-15 12:00:00.000000000 -0500 ctx=unconfined_u:object_r:user_tmp_t:s0
src after:  mtime=2020-01-15 12:00:00.000000000 -0500 ctx=unconfined_u:object_r:user_tmp_t:s0  (must match — cp never mutates the source)
exit was: 0
```

> Notice the **dst** line in the T08-A block: mtime jumped to NOW and the SELinux context changed from `etc_t` to `user_tmp_t`. That is the trap, made visible. Task 2 fixes it with `cp -a`.

### Switches

| Token | Meaning |
|---|---|
| `cp SRC DST` | Copy SRC to DST (DST = file or new path) |
| `cp SRC DIR/` | Copy SRC into existing directory DIR as `DIR/$(basename SRC)` |
| `cp -i SRC DST` | Interactive — prompt before overwrite |
| `cp -n SRC DST` | No-clobber — silent skip if DST exists |
| `cp -v SRC DST` | Verbose — print `'src' -> 'dst'` |
| `cp -f SRC DST` | Force — overwrite without prompt (overrides aliased `-i`) |
| `cp -u SRC DST` | Update — skip if DST is newer than SRC |
| `cp -b SRC DST` | Backup — save existing DST as `DST~` before overwrite |
| `<<< "y"` | Herestring — supplies the next command's stdin from a string |
| `stat -c '%y'` | mtime (human-readable) |
| `stat -c '%C'` | Full SELinux context |
| `ls -lZ` | DAC + SELinux in one row |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `cp SRC DST` base case | Data only — mode/owner/mtime/context reset to defaults |
|   | DST is a directory | SRC dropped inside as `DST/$(basename SRC)` |
|   | DST is a regular file | DST overwritten with SRC's data |
|   | DST is missing | New file created at DST containing SRC's data |
|   | `-i` vs `-n` | Interactive prompt vs silent skip — never both |
|   | `-v` audit | Prints `'src' -> 'dst'` for every copy — the script-debugging form |
|   | mtime drift | Plain `cp` always sets destination mtime to NOW |
|   | SELinux drift | Plain `cp` inherits the parent directory's default context |
| 🪤 | **Trap Risk T08-A** | `cp DIR DST` without `-R` prints `omitting directory` and does nothing — easy to miss in a long script. Always add `-R` (or `-a`) for trees. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Single-file copies present | `ls /tmp/copy-lab/task1/` | Confirms Variants A–E each landed |
| Source untouched | `stat -c '%y' /tmp/copy-lab/src/file.txt` | `cp` must never mutate the source |
| T08-A drift visible | `grep -c 'mtime=' /tmp/copy-lab/task1/op.txt` | Should be `≥2` — proves we captured src AND dst mtimes |
| Journal evidence | `cat /tmp/copy-lab/task1/op.txt` | The op.txt persists until reboot; we'll copy to `/root/` in the journal write |

> **Reboot reasoning:** `/tmp/copy-lab/` is on tmpfs on most RHEL layouts — it evaporates on reboot. The thing that **must** survive is the evidence under `/root/rhcsa_journal/lab-08a/`, not the sandbox itself.

### Journal write — BEFORE cleanup

```bash
LAB=lab-08a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/copy-lab/task1/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Single-file cp + directory-vs-file DST semantics + cp -i / -n / -v
COMMANDS: cp, cp -i, cp -n, cp -v, stat -c '%y %C', ls -lZ
TRAPS:    T08-A rehearsed (we captured mtime + SELinux drift in op.txt)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     task2 — cp -R, cp -a, cp --preserve=context for the /etc/skel tree
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/copy-lab/task1
ls /tmp/copy-lab/
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `cp: cannot create regular file: Permission denied` | Need write on the **parent directory** of DST — `ls -ld $(dirname DST)`; use `sudo` or fix DAC. |
| `cp -i` did not prompt | An alias (`alias cp=cp -i`) was stripped or you are not root. Run `\cp -i ...` or `/usr/bin/cp -i ...`. |
| `cp` "succeeded" but file is empty | Likely a redirection clash (`>` truncated SRC). Re-create SRC and re-run. |
| `cp: omitting directory '/etc/skel'` | T08-A — you copied a directory without `-R`. Add `-R` (or wait for Task 2). |
| Trailing-slash result surprised you | `cp SRC DIR/` requires DIR to exist; without the slash, the missing-path form creates DIR as a regular file. Use `ls -ld DST` to know what DST is *before* the copy. |

> **STOP — paste the T08-A `src/dst mtime + ctx` block from `op.txt` before starting Task 2. The drift must be visible — that's the muscle memory we are building.**

---

## Task 2 — Recursive copy with full attribute preservation: deploy `/etc/skel` into a new user home

**Practice directory this task:** `/etc/skel` (read), `/tmp/copy-lab/new-home/` (write) · This is the realistic RHCSA scenario — `useradd` would normally do this for you, but graders sometimes ask you to do it explicitly with `cp -a` to prove you understand what's preserved.

### 🔁 Warm-Up — commands woven into Task 2

```bash
ls -laZR /etc/skel                                  2>&1 | tee /tmp/copy-lab/warmup-task2.txt
find /etc/skel -mindepth 1                          | wc -l
test -d /etc/skel && echo "skel template OK"
stat -c '%n mode=%a owner=%U:%G mtime=%y ctx=%C' /etc/skel
set -o pipefail
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> Carry from Task 1: every cp must be paired with a before/after `stat`. In Task 2 we extend that — we also pair with `ls -lZ` for the SELinux context and `diff -r` for the recursive content match.

### Purpose

Copy `/etc/skel` (the system-wide new-user-home template) into `/tmp/copy-lab/new-home/` four different ways and **measure what each form preserved**:

1. `cp -R` — recursive, metadata RESET (the trap baseline)
2. `cp -a` — archive: recursive + preserve everything (the canonical RHCSA answer)
3. `cp -R --preserve=context` — recursive, SELinux context only (when DAC reset is fine but labels must survive)
4. `cp -a --no-preserve=ownership` — archive minus ownership (when destination must be owned by the calling user)

Then demonstrate **T08-B** — trailing-slash semantics on the source: `cp -R /etc/skel /tmp/copy-lab/new-home/` creates `new-home/skel/...`, while `cp -R /etc/skel/ /tmp/copy-lab/new-home/` (with trailing slash on the source) copies the **contents** of skel directly into `new-home/`.

### 🧵 WEAVE TRACE — warm-up commands re-used in this task body

| Warm-up command | Role inside Task 2 |
|---|---|
| `ls -laZR /etc/skel` | Snapshot the source tree — every later `diff -r` compares against this baseline |
| `find /etc/skel \| wc -l` | Counts entries — must match the count under each `new-home/<variant>/` after copy |
| `stat -c '%C'` | SELinux context of each source path — paired with the destination's `%C` for the T08-C check |
| `set -o pipefail` | Required so a `tee` failure can't hide a failed `cp -a` |
| `2>&1 \| tee` | Captures every copy + verification step into `task2/op.txt` for the journal |
| `$(date -Is)` | Stamps the journal |

### Main command block

```bash
cd /tmp/copy-lab
mkdir -p /tmp/copy-lab/task2 /tmp/copy-lab/new-home
mkdir -p /tmp/copy-lab/new-home/{cp-R,cp-a,cp-ctx,cp-a-noown}

echo "═══ Variant 1 — cp -R (recursive, metadata RESET) ═══" \
  | tee /tmp/copy-lab/task2/op.txt
cp -R /etc/skel /tmp/copy-lab/new-home/cp-R/skel
ls -lZd /etc/skel /tmp/copy-lab/new-home/cp-R/skel  | tee -a /tmp/copy-lab/task2/op.txt
echo "── mtime + ctx drift on cp -R ──"              | tee -a /tmp/copy-lab/task2/op.txt
stat -c 'src  mtime=%y ctx=%C' /etc/skel/.bashrc    | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null
stat -c 'dst  mtime=%y ctx=%C' /tmp/copy-lab/new-home/cp-R/skel/.bashrc \
                                                     | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null

echo "═══ Variant 2 — cp -a (archive: preserves EVERYTHING) ═══" \
  | tee -a /tmp/copy-lab/task2/op.txt
cp -a /etc/skel /tmp/copy-lab/new-home/cp-a/skel
ls -lZd /etc/skel /tmp/copy-lab/new-home/cp-a/skel  | tee -a /tmp/copy-lab/task2/op.txt
echo "── mtime + ctx PRESERVED on cp -a ──"          | tee -a /tmp/copy-lab/task2/op.txt
stat -c 'src  mtime=%y ctx=%C' /etc/skel/.bashrc    | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null
stat -c 'dst  mtime=%y ctx=%C' /tmp/copy-lab/new-home/cp-a/skel/.bashrc \
                                                     | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null
diff -r /etc/skel /tmp/copy-lab/new-home/cp-a/skel >/dev/null \
  && echo "  ✅ diff -r CLEAN (data byte-identical)" | tee -a /tmp/copy-lab/task2/op.txt

echo "═══ Variant 3 — cp -R --preserve=context (SELinux only) ═══" \
  | tee -a /tmp/copy-lab/task2/op.txt
cp -R --preserve=context /etc/skel /tmp/copy-lab/new-home/cp-ctx/skel
echo "── ctx PRESERVED, mtime RESET ──"              | tee -a /tmp/copy-lab/task2/op.txt
stat -c 'src  mtime=%y ctx=%C' /etc/skel/.bashrc    | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null
stat -c 'dst  mtime=%y ctx=%C' /tmp/copy-lab/new-home/cp-ctx/skel/.bashrc \
                                                     | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null

echo "═══ Variant 4 — cp -a --no-preserve=ownership ═══" \
  | tee -a /tmp/copy-lab/task2/op.txt
cp -a --no-preserve=ownership /etc/skel /tmp/copy-lab/new-home/cp-a-noown/skel
echo "── ownership RESET, everything else PRESERVED ──" | tee -a /tmp/copy-lab/task2/op.txt
stat -c 'src   owner=%U:%G mtime=%y ctx=%C' /etc/skel/.bashrc \
                                                     | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null
stat -c 'dst   owner=%U:%G mtime=%y ctx=%C' /tmp/copy-lab/new-home/cp-a-noown/skel/.bashrc \
                                                     | tee -a /tmp/copy-lab/task2/op.txt 2>/dev/null

echo "═══ T08-B — trailing-slash semantics on SOURCE ═══" \
  | tee -a /tmp/copy-lab/task2/op.txt
mkdir -p /tmp/copy-lab/new-home/no-slash /tmp/copy-lab/new-home/yes-slash
cp -a /etc/skel  /tmp/copy-lab/new-home/no-slash/    # creates no-slash/skel/...
cp -a /etc/skel/ /tmp/copy-lab/new-home/yes-slash/   # contents of skel land directly under yes-slash/
echo "── no trailing slash on src ──"                | tee -a /tmp/copy-lab/task2/op.txt
ls /tmp/copy-lab/new-home/no-slash/                 | tee -a /tmp/copy-lab/task2/op.txt
echo "── yes trailing slash on src ──"               | tee -a /tmp/copy-lab/task2/op.txt
ls -A /tmp/copy-lab/new-home/yes-slash/             | tee -a /tmp/copy-lab/task2/op.txt

echo "exit was: $?"
```

### Human-readable breakdown

1. **Variant 1 (`cp -R`)** — recursion only. Walks subdirectories, but mtime resets to NOW, owner becomes the calling user, SELinux context inherits from the destination parent. This is the trap baseline; you almost never want this for backup or staging.
2. **Variant 2 (`cp -a`)** — archive. Shorthand for `cp -dR --preserve=all`. Preserves mode, ownership, timestamps, symlinks-as-symlinks, SELinux context, and xattrs. This is the canonical RHCSA answer for "deploy this template."
3. **Variant 3 (`cp -R --preserve=context`)** — recursion + SELinux context only. mtime/owner still reset, but the security labels survive. Useful when you intend to take ownership but want the labels intact (e.g., copying a web root that must keep `httpd_sys_content_t`).
4. **Variant 4 (`cp -a --no-preserve=ownership`)** — full archive *minus* ownership. mtime, mode, symlinks, SELinux, xattrs all preserved; ownership becomes the calling user. The RHCSA-grade answer when the question explicitly says "preserve everything except ownership."
5. **T08-B (trailing slash on source)** — `cp -a /etc/skel /tmp/copy-lab/new-home/no-slash/` creates `no-slash/skel/.bashrc`. With the trailing slash on the source — `cp -a /etc/skel/ /tmp/copy-lab/new-home/yes-slash/` — the contents land directly: `yes-slash/.bashrc`. Two characters of typing, two completely different directory layouts.

### Reading it left to right

- `cp -R SRC DST` — recurse into SRC; copy each entry to under DST. Metadata reset.
- `cp -a SRC DST` — `-a` decomposes to `-dR --preserve=all`: `-d` keeps symlinks as symlinks; `-R` recurses; `--preserve=all` keeps mode, ownership, timestamps, links, context, and xattrs.
- `cp -R --preserve=context SRC DST` — recursive, but only the SELinux context attribute is preserved.
- `cp -a --no-preserve=ownership SRC DST` — start from `-a`'s "preserve everything," then subtract `ownership`.
- `cp -a /etc/skel /destdir/` — `/etc/skel` (no trailing slash) is treated as "this directory" — it gets copied as `destdir/skel/`.
- `cp -a /etc/skel/ /destdir/` — `/etc/skel/` (with trailing slash) is treated as "the contents of this directory" — they land directly in `destdir/`.
- `diff -r DIR1 DIR2` — recursive content diff; clean exit = identical bytes for every file in the tree.

### The story

A grader's question: "Deploy `/etc/skel` into `/home/alice/` for a new user `alice`. The contents must be byte-identical, the timestamps must match, and the SELinux contexts must be valid." The textbook answer is `useradd -m alice` and let the kernel do it. The RHCSA-graded answer when you have to do it by hand is:

```bash
sudo cp -a /etc/skel/ /home/alice/
sudo chown -R alice:alice /home/alice/
sudo restorecon -Rv /home/alice/   # because /home/alice has its own SELinux default
```

Note the trailing slash on `/etc/skel/` — without it you would get `/home/alice/skel/.bashrc` instead of `/home/alice/.bashrc`. That single character is the difference between a working login and a broken one. T08-B is the trap that catches almost every RHCSA candidate at least once during practice.

The `--preserve=` and `--no-preserve=` switches matter when the destination has its own SELinux policy (like `/home/alice` does — it requires `user_home_t`, not `etc_t`). In that case `cp -a` is *too much* preservation; you want `cp -a --no-preserve=context` followed by `restorecon -R`. The fine-grained switches are what separates "I memorized `cp -a`" from "I understand what each attribute means."

### Expected output

```text
═══ Variant 1 — cp -R (recursive, metadata RESET) ═══
drwxr-xr-x. 2 root root system_u:object_r:etc_t:s0       62 Jan  1  2025 /etc/skel
drwxr-xr-x. 2 root root unconfined_u:object_r:user_tmp_t:s0  62 May 28 20:01 /tmp/copy-lab/new-home/cp-R/skel
── mtime + ctx drift on cp -R ──
src  mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
dst  mtime=2026-05-28 20:01:00.000000000 -0400 ctx=unconfined_u:object_r:user_tmp_t:s0
═══ Variant 2 — cp -a (archive: preserves EVERYTHING) ═══
drwxr-xr-x. 2 root root system_u:object_r:etc_t:s0       62 Jan  1  2025 /etc/skel
drwxr-xr-x. 2 root root system_u:object_r:etc_t:s0       62 Jan  1  2025 /tmp/copy-lab/new-home/cp-a/skel
── mtime + ctx PRESERVED on cp -a ──
src  mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
dst  mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
  ✅ diff -r CLEAN (data byte-identical)
═══ Variant 3 — cp -R --preserve=context (SELinux only) ═══
── ctx PRESERVED, mtime RESET ──
src  mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
dst  mtime=2026-05-28 20:01:00.000000000 -0400 ctx=system_u:object_r:etc_t:s0
═══ Variant 4 — cp -a --no-preserve=ownership ═══
── ownership RESET, everything else PRESERVED ──
src   owner=root:root mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
dst   owner=root:root mtime=2025-01-01 00:00:00.000000000 -0500 ctx=system_u:object_r:etc_t:s0
═══ T08-B — trailing-slash semantics on SOURCE ═══
── no trailing slash on src ──
skel
── yes trailing slash on src ──
.bash_logout
.bash_profile
.bashrc
exit was: 0
```

> Notice the contrast: in Variant 1 the **dst ctx** is `user_tmp_t` (parent's default). In Variant 2 it stays `etc_t` (source's value). That single difference is why `cp -a` is the answer to "preserve everything."

### Switches

| Token | Meaning |
|---|---|
| `cp -R SRC DST` | Recursive — required for directories |
| `cp -a SRC DST` | Archive = `-dR --preserve=all` |
| `cp -p SRC DST` | Preserve mode + ownership + timestamps (subset of `-a`) |
| `cp -d SRC DST` | Preserve symlinks as symlinks |
| `cp -R --preserve=context` | Recurse + SELinux context only |
| `cp -a --no-preserve=ownership` | Archive minus ownership attribute |
| `--preserve=mode,timestamps,context` | Enumerate exact attributes |
| `--preserve=all` | Everything (= `-a`) |
| `cp -a SRC DST/` | Copy SRC directory as a sub-directory under DST/ |
| `cp -a SRC/ DST/` | Copy contents of SRC directly into DST/ |
| `ls -lZd` | Long listing of the directory itself (not contents), with SELinux |
| `diff -r DIR1 DIR2` | Recursive content diff |
| `restorecon -Rv DST` | Re-apply default SELinux contexts to DST (recursive, verbose) |

### 🧠 Concept Card

|   | Concept | What it does |
|---|---|---|
|   | `cp -R` | Recursive; metadata RESET — not what you want for backup/staging |
|   | `cp -a` | Archive: recursive + preserves mode + owner + mtime + symlinks + SELinux + xattrs |
|   | `cp -a` ≡ | `cp -dR --preserve=all` (memorize the decomposition) |
|   | `--preserve=ATTR` | Enumerate exact attributes — fine-grained control |
|   | `--no-preserve=ATTR` | Start from `-a`, subtract one attribute |
|   | Attribute names | `mode`, `ownership`, `timestamps`, `links`, `context`, `xattr`, `all` |
|   | Trailing slash on SRC | `/etc/skel` copies the dir; `/etc/skel/` copies the CONTENTS |
|   | `restorecon -R` | Re-apply default SELinux contexts when you intentionally did NOT preserve them |
| 🪤 | **Trap Risk T08-B** | One trailing slash on the source = completely different destination layout. Always pre-flight with `ls -ld SRC` and dry-run the path. |
| 🪤 | **Trap Risk T08-C** | Plain `cp -R` of web content into `/var/www/html` → SELinux denies httpd. Use `cp -a` or `restorecon -Rv /var/www/html`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| All four variants present | `ls /tmp/copy-lab/new-home/` | Should list `cp-R cp-a cp-ctx cp-a-noown no-slash yes-slash` |
| `cp -a` is byte-identical | `diff -r /etc/skel /tmp/copy-lab/new-home/cp-a/skel && echo CLEAN` | Tests data preservation |
| `cp -a` preserved mtime | `stat -c '%Y' /etc/skel/.bashrc /tmp/copy-lab/new-home/cp-a/skel/.bashrc` | Both values must match |
| `cp -a` preserved SELinux | `ls -dZ /etc/skel /tmp/copy-lab/new-home/cp-a/skel` | Both contexts must match |
| T08-B contrast captured | `ls /tmp/copy-lab/new-home/no-slash/ /tmp/copy-lab/new-home/yes-slash/` | One contains `skel/`, the other contains `.bashrc` directly |

> **Reboot reasoning:** `/tmp/copy-lab/new-home/` evaporates on reboot. The evidence under `/root/rhcsa_journal/lab-08a/task2/` does not. After a reboot, the only thing that proves Task 2 was done correctly is `evidence.txt` — write it before cleanup.

### Journal write — BEFORE cleanup

```bash
LAB=lab-08a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/copy-lab/task2/op.txt "$JDIR/evidence.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    Recursive copy + cp -a + --preserve=/--no-preserve= + T08-B trailing slash
COMMANDS: cp -R, cp -a, cp --preserve=context, cp --no-preserve=ownership, diff -r, ls -lZ
TRAPS:    T08-A T08-B T08-C rehearsed (drift visible, slash semantics demonstrated, ctx preserved)
MISSED:   (fill in if any ⚠️ flags)
NEXT:     lab-08b — replace cp with ansible.builtin.copy + remote_src + backup
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -rf /tmp/copy-lab
test -d /tmp/copy-lab || echo "sandbox gone — clean exit"
echo "exit was: $?"
```

### Troubleshoot

| Symptom | Fix |
|---|---|
| `cp: -R not specified; omitting directory` | T08-A — you copied a directory without `-R`. Add `-R` or `-a`. |
| `cp -a` "succeeded" but `diff -r` shows differences | A file changed under `/etc/skel` between the two reads (rare). Re-run `cp -a`; verify with `diff -r` again. |
| `cp -a` did not preserve SELinux | SELinux is disabled (`getenforce` → `Disabled`). `--preserve=context` is a no-op when SELinux is off. Enable it and reboot. |
| Symlink in dst became a regular file | You used `cp -R` instead of `cp -a` (or `cp -R -d`). `-R` follows symlinks; `-a` (and `-d`) preserves them. |
| Destination tree has the source dir-name as an extra level | Trailing-slash trap (T08-B). `cp -a /etc/skel /dest/` makes `/dest/skel/`; `cp -a /etc/skel/ /dest/` puts the contents directly in `/dest/`. |
| Web content copied to `/var/www/html` causes httpd 403 | T08-C — context wrong. Either `cp -a` (preserves source's context, may still be wrong) or `cp -R` then `restorecon -Rv /var/www/html`. |

> **STOP — paste the "── mtime + ctx PRESERVED on cp -a ──" block AND the T08-B contrast (no-slash vs yes-slash) from `op.txt` before moving on to Lab 08b. Both must be visible — those are the two muscle-memory moments this lab exists to install.**

---

## Lab 08a Checklist (2 tasks)

- [ ] Task 1 — Single-file `cp`, `cp -i`, `cp -v`, directory-vs-file DST semantics, T08-A drift visible + journal evidence
- [ ] Task 2 — `cp -R` vs `cp -a` vs `cp --preserve=context` vs `cp -a --no-preserve=ownership` + T08-B trailing-slash demo + journal evidence

---

## 🔗 Related Labs in the Trilogy

| Lab | Connection |
|---|---|
| **Lab 08b** — Copying Files via Ansible | `ansible.builtin.copy` with `remote_src:`, `mode:`, `owner:`, `backup:` — the idempotent declarative form of what you just hand-typed |
| **Lab 08c** — Verifying Copies | The auditor seat: `diff -r`, `stat`, `ls -lZ` against a declared baseline + reboot persistence proof |
| Lab 07 — Timestamps and `stat` | The metadata baseline that makes the `cp -a` preservation story legible |
| Lab 09 — Moving and Renaming (`mv`) | The atomic-rename relative; `mv` doesn't have a `--preserve` story because it preserves by default |
| Lab 11a — Safe Deletion | The destructive counterpart — every `cp` you make should be paired with a planned `rm` strategy |

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
