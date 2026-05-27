# Lab 08: Copying Files and Directories — `cp`, `cp -R`, `cp -a`, `cp --preserve`

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Career arcs covered:** RHCSA EX200 (backup/restore, /etc/skel, config staging), RHCE EX294 (Ansible `copy:` module), CKA (kubectl cp + ConfigMap staging), RHCA — RH358 (preserving SELinux on copies)
- **Prerequisite:** Lab 07 (`touch`, `stat`, timestamp manipulation)
- **Time Estimate:** 35–50 minutes
- **Tasks:** 3 (ADHD spec)
- **Practice Directory (lab-wide rotation #08):** `/home`
- **Sandbox:** `/tmp/cp-lab`
- **Traps rehearsed this lab:** **T32** (setfacl default ACL on directories is a separate command — `-m d:`) · **T31** (usermod -G without -a replaces all supplementary groups)

> **This lab's practice directory is: `/home`** — every task references it in at least two commands.

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
echo "⚠️  TRAP REMINDERS THIS LAB: T32 T31"
echo "📁  PRACTICE DIR: /home"
echo ""
echo "💡 /home occupants (read-only inspection):"
ls -ld /home /home/*/ 2>/dev/null | head -n 10
```

> **STOP — paste header output before running setup.**

---

## 🎯 Objective

Copy single files, copy entire directory trees, and **preserve everything that matters** — timestamps, owner, group, SELinux context, ACLs, and links. By the end you will choose between `cp`, `cp -R`, `cp -a`, and `cp --preserve=` like a senior admin, and you will know exactly which one to use when staging files into `/home/<user>/` or `/etc/skel/`.

---

## 🧠 Concept: A Copy Is Not a Copy

Every `cp` is a decision. Each flag controls a different attribute:

| Flag | Preserves | Loses if missing |
|---|---|---|
| `cp` (plain) | contents | mtime, owner, group, mode (partly), context, ACLs, links |
| `cp -p` | + mtime, owner, group, mode | context, ACLs, hardlinks |
| `cp -R` (or `-r`) | + recursion into dirs | (still loses metadata unless paired with `-p`) |
| `cp -a` | **everything `cp` can preserve** — `-dpR --preserve=all` | (rarely loses anything — this is the "be safe" flag) |
| `cp --preserve=context` | + SELinux context (subset of `-a`) | ACLs, links |
| `cp --preserve=all` | mode + ownership + timestamps + links + context + xattr | — |
| `cp --reflink=auto` | uses FS-level copy-on-write when supported (XFS, Btrfs) | — |

```
cp src dst                  # bare copy — new mtime, new owner (you), default context
cp -p src dst               # preserve mtime/owner/group/mode
cp -R srcdir/ dstdir/       # recurse (no metadata preservation)
cp -a srcdir/ dstdir/       # recursive + preserve everything (THE production move)
cp --preserve=context f d   # only SELinux ctx
```

> **The single most important rule:** when copying into a directory that a daemon serves (Apache, NFS, systemd unit dir, /etc), use **`cp -a`** or **`cp --preserve=context`** + `restorecon -Rv`. A bare `cp` produces files that the daemon literally cannot read because SELinux contexts default to your shell's context (`user_tmp_t`, `user_home_t`).

---

## 🚦 Lab-Wide Setup — Run This BEFORE Task 1

```bash
sudo -i
mkdir -p /tmp/cp-lab/src /tmp/cp-lab/dst
cd /tmp/cp-lab

cat > /tmp/cp-lab/THIS_DIRECTORY.txt <<'EOF'
/home — Personal directories for standard users

/home holds one subdirectory per user account, named after the login.
It exists to separate user data from system files so /home can live on
its own disk, its own LV, or even be NFS-mounted, without affecting
the bootability of the host.

Why it exists: predictable per-user paths (~ resolves to /home/<user>),
quota management on a per-user basis, and isolation of personal data
from system upgrades.

What lives inside it: one directory per user (/home/alice, /home/bob),
with each containing dotfiles (.bashrc, .ssh/, .bash_history) and the
user's working files.

Why RHCSA cares: /etc/skel populates new /home/<user> on useradd. SELinux
context for /home/<user> is user_home_dir_t (and files inside are
user_home_t). Copying files INTO /home/<user>/.ssh/ without preserving
context can break SSH key auth — this is one of the most common
real-world cp gotchas.
EOF

cat /tmp/cp-lab/THIS_DIRECTORY.txt
echo ""
echo "Build the source fixture:"
echo "hello from src" > src/file1.txt
echo "secret line"    > src/secret.txt
chmod 600 src/secret.txt
mkdir -p src/subdir
echo "nested"  > src/subdir/nested.txt
ln -s file1.txt src/symlink-to-file1

ls -lR src/
echo ""
echo "SELinux contexts of source:"
ls -Z src/ src/subdir/
echo "exit was: $?"
```

> **STOP — paste output before Task 1.**

---

# The 3 Tasks

---

## Task 1 — `cp` vs `cp -p`: When Metadata Matters

### a) Directory Context

**Practice directory this task:** `/home` (read-only reference) and `/tmp/cp-lab` (sandbox).
We will copy our `src/secret.txt` (mode 600) two ways and prove that bare `cp` loses metadata you usually want to keep.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/cp-lab
date -Is | tee task01-warmup.log
ls -ld /home 2>&1 | tee -a task01-warmup.log
ls -ld /home/*/ 2>/dev/null | head -n 3 | tee -a task01-warmup.log
echo "warmup lines: $(wc -l < task01-warmup.log)"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Copy a file two ways — `cp` (bare) and `cp -p` (preserve) — and use `stat` to diff the results.

### d) Main Command Block

```bash
cd /tmp/cp-lab

cp src/secret.txt dst/secret-bare.txt
cp -p src/secret.txt dst/secret-preserved.txt

echo "=== source ==="
stat --format='Mode:%a Owner:%U:%G MTime:%y Ctx:%C' src/secret.txt

echo "=== bare cp ==="
stat --format='Mode:%a Owner:%U:%G MTime:%y Ctx:%C' dst/secret-bare.txt

echo "=== cp -p ==="
stat --format='Mode:%a Owner:%U:%G MTime:%y Ctx:%C' dst/secret-preserved.txt

echo ""
echo "ls -lZ comparison:"
ls -lZ src/secret.txt dst/secret-bare.txt dst/secret-preserved.txt

echo ""
echo "Try a /home destination (this is where bare cp bites you):"
mkdir -p /home/cp-lab-demo
chown root:root /home/cp-lab-demo
chmod 755 /home/cp-lab-demo
cp    src/secret.txt /home/cp-lab-demo/secret-bare-home.txt
cp -p src/secret.txt /home/cp-lab-demo/secret-preserved-home.txt
ls -lZ /home/cp-lab-demo/
```

### e) Human-Readable Breakdown

- `cp src/secret.txt dst/secret-bare.txt` — copy contents. mtime becomes "now," owner becomes you, mode is inherited from the destination's umask in some cases.
- `cp -p src/secret.txt dst/secret-preserved.txt` — preserve mode, owner, group, mtime.
- `stat --format='Mode:%a Owner:%U:%G MTime:%y Ctx:%C'` — print just the fields we care about; `%C` is the SELinux context.
- The `/home` portion shows the most common production gotcha: copying into a user's home with bare `cp` gives the files **your** ownership and a different SELinux context.

### f) Reading It Left to Right

`stat --format='Mode:%a Owner:%U:%G MTime:%y Ctx:%C' src/secret.txt`

1. `stat` — file metadata.
2. `--format='...'` — custom output, no default block.
3. `%a` — mode in octal (e.g. `600`).
4. `%U:%G` — owner user / group.
5. `%y` — modification time (human-readable).
6. `%C` — SELinux security context.
7. `src/secret.txt` — target path.

### g) The Story

Bare `cp` is fine for "throw a temp file somewhere I'll delete in 5 minutes." Every other case wants `cp -p` at minimum. The classic disaster: an admin copies `~/.ssh/authorized_keys` from a working host to a new host with bare `cp`. New owner is whoever ran the scp, new mode might be 644 (others readable!), and on RHEL the SELinux context is wrong. SSH refuses to use the key — sometimes silently — and you spend an hour debugging.

### h) Expected Output

```text
=== source ===
Mode:600 Owner:root:root MTime:2026-05-27 14:30:00.xxx -0400 Ctx:unconfined_u:object_r:user_tmp_t:s0

=== bare cp ===
Mode:600 Owner:root:root MTime:2026-05-27 14:30:01.xxx -0400 Ctx:unconfined_u:object_r:user_tmp_t:s0

=== cp -p ===
Mode:600 Owner:root:root MTime:2026-05-27 14:30:00.xxx -0400 Ctx:unconfined_u:object_r:user_tmp_t:s0

-rw------- ... unconfined_u:object_r:user_tmp_t:s0 src/secret.txt
-rw------- ... unconfined_u:object_r:user_tmp_t:s0 dst/secret-bare.txt
-rw------- ... unconfined_u:object_r:user_tmp_t:s0 dst/secret-preserved.txt

(Inside /home/cp-lab-demo/ — note the context type changes if SELinux is enforcing:)
-rw------- ... unconfined_u:object_r:user_home_t:s0  secret-bare-home.txt
-rw------- ... unconfined_u:object_r:user_home_t:s0  secret-preserved-home.txt
```

Two key observations:

1. **Within /tmp/cp-lab**, contexts look identical — both files inherit `user_tmp_t` because they live in `/tmp`. The mtime is the only visible difference between `cp` and `cp -p`.
2. **Inside /home/cp-lab-demo/**, contexts become `user_home_t` automatically because the destination directory has `user_home_dir_t` context and the policy assigns child types. **This is policy-driven re-labeling on `cp`** — it works because the SELinux policy has a `type_transition` rule. Without that policy magic (e.g. when copying into a non-standard dir), you'd be stuck with `user_tmp_t` everywhere.

### i) Switches Table

| Token | Meaning |
|---|---|
| `cp SRC DST` | Copy contents only |
| `cp -p SRC DST` | Preserve mode + owner + group + mtime |
| `cp -i SRC DST` | Interactive (prompt before overwrite) |
| `cp -n SRC DST` | No-clobber (skip existing) |
| `cp -v SRC DST` | Verbose |
| `stat --format='%a'` | Mode in octal |
| `stat --format='%U:%G'` | Owner user:group |
| `stat --format='%y'` | mtime (human) |
| `stat --format='%C'` | SELinux context |
| `chown root:root` | Set owner + group |
| `chmod 755` | rwxr-xr-x |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | Bare `cp` | New mtime, possibly new owner, default context |
|   | `cp -p` | Preserves mode + owner + group + mtime |
|   | `%C` in stat | SELinux context |
|   | Type transition | SELinux auto-relabels on copy when destination dir has policy |
|   | `/home/<user>/` | Has `user_home_dir_t` context — children become `user_home_t` |
|   | `/tmp/...` | Has `tmp_t`/`user_tmp_t` context |
| 🪤 **Trap Risk (T32)** | setfacl default ACL on directories is a separate command (`-m d:`) | `cp -p` does NOT copy ACLs. If the source dir has a default ACL, a bare `cp -p` of files into it inherits the dir's ACL, but copying FROM an ACL-tagged dir to a plain dir loses them. Use `cp --preserve=all` |

### k) 🧹 Cleanup

```bash
LAB=lab08
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
TOPIC:    cp vs cp -p; stat metadata diffing
COMMANDS: cp, cp -p, stat --format='%a %U:%G %y %C'
TRAPS:    T32 (ACLs not preserved by -p; need --preserve=all)
MISSED:   —
NEXT:     task2 — cp -R / cp -a recursive copies
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/cp-lab
rm -f task01-warmup.log dst/secret-bare.txt dst/secret-preserved.txt
rm -rf /home/cp-lab-demo
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cp -p` shows different owner | You are not root; `sudo -i` to copy with `-p` faithfully |
| `%C` empty in stat | SELinux disabled — `getenforce` |
| `cp` says `omitting directory` | Use `-R` for recursion (Task 2) |
| `/home/cp-lab-demo` won't delete | `cd` out of it first; check `lsof +D /home/cp-lab-demo` |

### m) STOP

> **STOP — paste output before Task 2.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `/home/cp-lab-demo` cleaned | `test -d /home/cp-lab-demo \|\| echo CLEAN` | No test debris in `/home` |
| Journal task1 | `cat /root/rhcsa_journal/lab08/task1/done.txt` | Reboot-proof |

---

## Task 2 — `cp -R` vs `cp -a`: Recursive Copies + Symlinks

### a) Directory Context

**Practice directory this task:** `/home` (target of full-tree copy) and `/tmp/cp-lab` (sandbox).
We will replicate `src/` (which contains a subdir AND a symlink) into a destination twice — once with `-R` and once with `-a` — and diff the results.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/cp-lab
date -Is | tee task02-warmup.log
ls -lR src/ 2>&1 | head -n 15 | tee -a task02-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Copy `src/` recursively two ways, prove `-a` preserves more than `-R`, and observe how symlinks are handled differently.

### d) Main Command Block

```bash
cd /tmp/cp-lab
rm -rf dst/copy-R dst/copy-a
cp -R src dst/copy-R
cp -a src dst/copy-a

echo "=== source tree ==="
ls -lR src/ | head -n 15
echo ""
echo "=== cp -R result ==="
ls -lR dst/copy-R/ | head -n 15
echo ""
echo "=== cp -a result ==="
ls -lR dst/copy-a/ | head -n 15

echo ""
echo "Symlink handling:"
ls -l src/symlink-to-file1 dst/copy-R/symlink-to-file1 dst/copy-a/symlink-to-file1

echo ""
echo "mtime diff (source first file vs each copy):"
stat --format='%n %y' src/file1.txt dst/copy-R/file1.txt dst/copy-a/file1.txt

echo ""
echo "Context diff:"
ls -Z src/file1.txt dst/copy-R/file1.txt dst/copy-a/file1.txt

echo ""
echo "Stage to /home/cp-lab-staging (the production pattern):"
mkdir -p /home/cp-lab-staging
cp -a src/. /home/cp-lab-staging/
ls -lZ /home/cp-lab-staging/
```

### e) Human-Readable Breakdown

- `cp -R src dst/copy-R` — recurse but do NOT preserve metadata.
- `cp -a src dst/copy-a` — recurse AND preserve everything (`-a` = `-dpR --preserve=all`).
- The symlink test shows: `-R` by default **dereferences** symlinks (or treats them inconsistently across versions), while `-a` preserves them as symlinks.
- `cp -a src/. /home/cp-lab-staging/` — the `/.` idiom copies the **contents** of `src` into the destination (not `src` itself as a new subdirectory).

### f) Reading It Left to Right

`cp -a src/. /home/cp-lab-staging/`

1. `cp` — copy command.
2. `-a` — archive mode (recursive + preserve all).
3. `src/.` — source: the `.` (current dir from src's perspective) means "all contents of `src/`, including hidden files."
4. `/home/cp-lab-staging/` — destination directory; contents are placed INSIDE it.

Contrast: `cp -a src /home/cp-lab-staging/` would create `/home/cp-lab-staging/src/...` (one level deeper).

### g) The Story

`cp -R` exists for compatibility. `cp -a` is what you actually want 99% of the time when copying directory trees on Linux. The `-a` flag is equivalent to typing `-dpR --preserve=all` (preserve mode/owner/group/timestamps/links/context/xattr AND recurse AND don't follow symlinks). Memorize: **archive mode**.

The `/.` trick (or `/*` for shells that expand it, but `/.` survives hidden files better) is how you copy "contents of dir A into dir B" without creating an extra layer. RHCSA exam: "Copy the contents of `/etc/skel` into `/home/newuser/`." → `cp -a /etc/skel/. /home/newuser/`.

### h) Expected Output

```text
=== source tree ===
total 12
-rw-r--r--. ... file1.txt
-rw-------. ... secret.txt
lrwxrwxrwx. ... symlink-to-file1 -> file1.txt
drwxr-xr-x. ... subdir
src/subdir:
-rw-r--r--. ... nested.txt

=== cp -R result ===
(similar tree, but mtimes are "now")

=== cp -a result ===
(similar tree, mtimes preserved from source)

Symlink handling:
lrwxrwxrwx. ... src/symlink-to-file1 -> file1.txt
lrwxrwxrwx. ... dst/copy-R/symlink-to-file1 -> file1.txt   (modern coreutils preserve)
lrwxrwxrwx. ... dst/copy-a/symlink-to-file1 -> file1.txt

mtime diff:
src/file1.txt          2026-05-27 14:25:00.xxx -0400
dst/copy-R/file1.txt   2026-05-27 14:35:00.xxx -0400   (NEW — -R didn't preserve)
dst/copy-a/file1.txt   2026-05-27 14:25:00.xxx -0400   (preserved by -a)

Context diff:
unconfined_u:object_r:user_tmp_t:s0    src/file1.txt
unconfined_u:object_r:user_tmp_t:s0    dst/copy-R/file1.txt
unconfined_u:object_r:user_tmp_t:s0    dst/copy-a/file1.txt

(After staging to /home/cp-lab-staging/ with cp -a:)
unconfined_u:object_r:user_home_t:s0   file1.txt
unconfined_u:object_r:user_home_t:s0   secret.txt
...
```

Within `/tmp` the contexts look identical. The `/home/cp-lab-staging` copy shows `user_home_t` because of type_transition policy. If you had used `cp` (no flag) into `/home/cp-lab-staging`, contexts would still re-label correctly because of policy — BUT mtimes would be "now," ACLs would be lost, and ownership would be the running user. **`cp -a` is the only way to preserve everything AND let policy re-label.**

### i) Switches Table

| Token | Meaning |
|---|---|
| `cp -R` | Recursive, no metadata preservation |
| `cp -r` | Same as `-R` |
| `cp -a` | Archive mode (`-dpR --preserve=all`) |
| `cp -d` | Don't follow symlinks; preserve them |
| `cp --preserve=mode` | Just mode |
| `cp --preserve=context` | Just SELinux context |
| `cp --preserve=all` | Mode + owner + group + mtime + ACLs + xattr + context + links |
| `cp -v` | Verbose |
| `src/.` | "Contents of src, including hidden" |
| `src/*` | Shell-expanded contents (no hidden by default) |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `cp -R` | Recurse; metadata lost |
|   | `cp -a` | Recurse + preserve all |
|   | `src/.` idiom | Copy contents, not the dir itself |
|   | Symlinks | `-a` preserves; `-R` varies by version |
|   | Type transition | SELinux relabels children based on dest dir policy |
|   | `--preserve=context` | Override transition; force source context |
| 🪤 **Trap Risk (T32)** | Default ACL on directories | If `src` has a default ACL set via `setfacl -m d:u:alice:rwx src`, `cp -a` copies the ACL. But if you ran `setfacl -m u:alice:rwx src` (without `d:`), only the dir gets the ACL — new files inside do NOT inherit. Use `setfacl -m d:u:alice:rwx` for the default |
| 🪤 **Trap Risk (T31)** | `usermod -G` without `-a` replaces all supplementary groups | Not directly cp, but if you `useradd alice; useradd bob; chown bob:engineers src/`, then `usermod -G web alice` removes alice from ALL groups except web. ALWAYS `usermod -aG` |

### k) 🧹 Cleanup

```bash
LAB=lab08
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
TOPIC:    cp -R vs cp -a; src/. idiom; symlink preservation
COMMANDS: cp -R, cp -a, cp -d, cp --preserve=, src/.
TRAPS:    T32 (default ACL d:); T31 (usermod -aG)
MISSED:   —
NEXT:     task3 — cp --preserve=context + restorecon capstone
EOF
echo "Journal written: $(ls -la $JDIR)"

cd /tmp/cp-lab
rm -rf dst/copy-R dst/copy-a task02-warmup.log
rm -rf /home/cp-lab-staging
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `cp -R` says "omitting directory" | Spell is wrong; `cp -R src dst` (need `-R`, not nothing) |
| Symlink became a regular file | You used `-L` (dereference); switch to `-a` or `-d` |
| Hidden files not copied with `src/*` | Shell didn't expand `.*`; use `src/.` instead |
| `/home/cp-lab-staging` files have wrong owner | Use `cp -a` AND verify with `ls -lZ` |

### m) STOP

> **STOP — paste output before Task 3.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| `/home/cp-lab-staging` cleaned | `test -d /home/cp-lab-staging \|\| echo CLEAN` | No leftover test data in /home |
| Source tree intact | `find src -mindepth 1 \| wc -l` (expect 4) | Confirms we didn't accidentally `mv` instead of `cp` |
| Journal task2 | `cat /root/rhcsa_journal/lab08/task2/done.txt` | Reboot-proof |

---

## Task 3 — `cp --preserve=context` + `restorecon` Capstone (the /home/.ssh Story)

### a) Directory Context

**Practice directory this task:** `/home` (we will create a fake user and copy SSH-like files into their home).
This is the most production-realistic `cp` scenario on the exam.

### b) 🔁 Warm-Up — Commands from Previous Labs

```bash
cd /tmp/cp-lab
date -Is | tee task03-warmup.log
ls -ldZ /home 2>&1 | tee -a task03-warmup.log
ls -lZ src/ 2>&1 | tee -a task03-warmup.log
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### c) Purpose

Build a fake user, copy a "key file" three ways (bare `cp`, `cp -a`, `cp --preserve=context`), and verify with `ls -lZ` + `restorecon -Rv` which method ends up with the **correct** `ssh_home_t` context.

### d) Main Command Block

```bash
cd /tmp/cp-lab

useradd -m cplab 2>/dev/null || echo "cplab already exists"
USER_HOME=$(getent passwd cplab | awk -F: '{print $6}')
echo "USER_HOME=$USER_HOME"

mkdir -p $USER_HOME/.ssh
chmod 700 $USER_HOME/.ssh

cat > /tmp/cp-lab/src/fake_authorized_keys <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKeyForLabUse cplab@localhost
EOF
chmod 600 /tmp/cp-lab/src/fake_authorized_keys

echo ""
echo "=== Method 1: bare cp (the DISASTER) ==="
cp /tmp/cp-lab/src/fake_authorized_keys $USER_HOME/.ssh/authorized_keys.bare
ls -lZ $USER_HOME/.ssh/authorized_keys.bare

echo ""
echo "=== Method 2: cp -a (preserve source context) ==="
cp -a /tmp/cp-lab/src/fake_authorized_keys $USER_HOME/.ssh/authorized_keys.cpa
ls -lZ $USER_HOME/.ssh/authorized_keys.cpa

echo ""
echo "=== Method 3: cp + restorecon (the RHCSA pattern) ==="
cp /tmp/cp-lab/src/fake_authorized_keys $USER_HOME/.ssh/authorized_keys.fixed
restorecon -Rv $USER_HOME/.ssh
ls -lZ $USER_HOME/.ssh/authorized_keys.fixed

echo ""
echo "=== Fix ownership too (sshd won't accept root-owned files in alice's .ssh) ==="
chown -R cplab:cplab $USER_HOME/.ssh
ls -lZ $USER_HOME/.ssh/

echo ""
echo "=== What does policy SAY the right context is? ==="
matchpathcon $USER_HOME/.ssh/authorized_keys 2>/dev/null || \
  matchpathcon /home/cplab/.ssh/authorized_keys 2>/dev/null || \
  echo "matchpathcon not available — install policycoreutils-python-utils"
```

### e) Human-Readable Breakdown

- `useradd -m cplab` — create a user and their home dir.
- `getent passwd cplab | awk -F:` — pull the home path from `/etc/passwd` (don't hardcode).
- Three copy methods of the same file:
  1. **Bare `cp`** — usually OK on RHEL because of type_transition, but mode might shift if source mode and dest dir don't agree.
  2. **`cp -a`** — preserves the SOURCE context (`user_tmp_t` in this case) — which is **wrong** for `.ssh/authorized_keys`. Surprise: `-a` is not always right!
  3. **`cp` then `restorecon -Rv`** — restorecon reads policy and assigns the correct type. **This is the RHCSA-correct pattern.**
- `chown -R cplab:cplab` — sshd refuses to read keys that root owns in another user's `.ssh`.
- `matchpathcon` — confirms policy expects `ssh_home_t`.

### f) Reading It Left to Right

`cp -a /tmp/cp-lab/src/fake_authorized_keys $USER_HOME/.ssh/authorized_keys.cpa`

1. `cp` — copy.
2. `-a` — archive mode.
3. Source path.
4. Destination: `$USER_HOME` was set above via `getent`. `.ssh/authorized_keys.cpa` is inside the destination dir.

The critical insight: `-a` preserves **what is in the source**, NOT what is in policy. Source was `user_tmp_t` → destination becomes `user_tmp_t`. sshd won't read it. **Use `restorecon` to align with policy when copying into a policy-managed location.**

### g) The Story

This is the single most common SELinux-related real-world disaster. An admin generates a key locally (`ssh-keygen` → `~/.ssh/id_ed25519.pub`), then copies it to a server with `scp` or `cp` and asks "why doesn't SSH key auth work?" The mode is right (600), the owner is right, but the SELinux type is wrong. `sshd` (running as `sshd_t`) is not allowed to read files with type `user_tmp_t` — the policy denies it.

The fix is one of:
- `restorecon -Rv /home/<user>/.ssh` (preferred — uses policy)
- `chcon -t ssh_home_t /home/<user>/.ssh/authorized_keys` (non-persistent; lost on a relabel)

`ssh-copy-id` does both copy + restorecon for you. That's why it exists.

### h) Expected Output

```text
USER_HOME=/home/cplab

=== Method 1: bare cp ===
-rw-------. 1 root root unconfined_u:object_r:user_home_t:s0  authorized_keys.bare

=== Method 2: cp -a ===
-rw-------. 1 root root unconfined_u:object_r:user_tmp_t:s0   authorized_keys.cpa
   ↑ NOTICE: type is wrong — cp -a preserved the source's /tmp context

=== Method 3: cp + restorecon ===
-rw-------. 1 root root unconfined_u:object_r:ssh_home_t:s0   authorized_keys.fixed
   ↑ CORRECT — restorecon applied policy

=== Fix ownership ===
-rw-------. 1 cplab cplab unconfined_u:object_r:ssh_home_t:s0    authorized_keys.bare
-rw-------. 1 cplab cplab unconfined_u:object_r:user_tmp_t:s0    authorized_keys.cpa
-rw-------. 1 cplab cplab unconfined_u:object_r:ssh_home_t:s0    authorized_keys.fixed

=== Policy says ===
/home/cplab/.ssh/authorized_keys  system_u:object_r:ssh_home_t:s0
```

`authorized_keys.cpa` still has the wrong type even after `chown`. **The only fix is `restorecon`.** That is exactly why we run `restorecon -Rv ~/.ssh` after any manual key copy.

### i) Switches Table

| Token | Meaning |
|---|---|
| `cp --preserve=context` | Preserve only SELinux ctx (subset of `-a`) |
| `cp --no-preserve=context` | Force destination policy (let type_transition fire) |
| `useradd -m USER` | Create user + home dir |
| `getent passwd USER` | Look up user in NSS (works for LDAP too) |
| `awk -F: '{print $6}'` | Pull field 6 (home dir) from colon-delimited passwd |
| `restorecon -Rv PATH` | Recursive, verbose policy apply |
| `matchpathcon PATH` | Show policy's expected context |
| `chown -R user:group PATH` | Recursive owner change |

### j) 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
|   | `cp` (default) | Lets type_transition assign new context |
|   | `cp -a` | Preserves SOURCE context (sometimes wrong!) |
|   | `cp --preserve=context` | Force source ctx |
|   | `cp --no-preserve=context` | Force destination policy |
|   | `restorecon -Rv` | Authoritative — applies current policy |
|   | `matchpathcon` | "What does policy say?" lookup |
|   | `getent passwd USER` | Resolve home dir via NSS |
|   | `ssh-copy-id` | Does the full copy+restorecon dance for you |
| 🪤 **Trap Risk (T32)** | Default ACL on directories (`-m d:`) | `cp -a` into a directory with a default ACL inherits the ACL on new files. Without `d:`, the ACL applies only to the dir itself — child copies don't get it. Verify with `getfacl` |
| 🪤 **Trap Risk (T31)** | usermod -G without -a | If you did `useradd -m cplab; usermod -G web cplab` (forgetting `-a`), you would have wiped cplab from its primary group's supplementary list. Always `usermod -aG` |

### k) 🧹 Cleanup

```bash
LAB=lab08
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
TOPIC:    cp + restorecon capstone for /home/<user>/.ssh
COMMANDS: cp, cp -a, cp --preserve=context, restorecon -Rv, matchpathcon, getent
TRAPS:    T32 + T31 (both rehearsed)
MISSED:   —
NEXT:     Lab 09 — hard and soft links (/root practice dir)
EOF
echo "Journal written: $(ls -la $JDIR)"

userdel -r cplab 2>/dev/null
rm -rf /home/cplab
rm -rf /tmp/cp-lab
echo "exit was: $?"
```

### l) Troubleshoot Table

| Symptom | Fix |
|---|---|
| `useradd: user already exists` | Run `userdel -r cplab` and retry, OR continue (the `\|\| echo` keeps us going) |
| `restorecon` says nothing | Already correct; that's success. Add `-v` for diagnostic chatter |
| `authorized_keys.cpa` STILL wrong context after restorecon | Verify path matches the policy regex with `matchpathcon` |
| `chown: invalid user 'cplab'` | useradd silently failed; check `id cplab` |

### m) STOP

> **STOP — paste output before declaring Lab 08 complete.**

### n) 🔁 Persistence Check

| What was configured | Verification command | Why it matters |
|---|---|---|
| User `cplab` removed | `id cplab 2>&1 \| grep "no such user"` | Confirms userdel worked |
| `/home/cplab` gone | `test -d /home/cplab \|\| echo CLEAN` | userdel -r should remove the home |
| `/tmp/cp-lab` removed | `test -d /tmp/cp-lab \|\| echo CLEAN` | Sandbox cleanup |
| All 3 journal entries | `find /root/rhcsa_journal/lab08 -name done.txt \| wc -l` (expect 3) | Reboot-proof |

> **Reboot question:** "If we rebooted after copying a key but before restorecon, would the wrong context survive?" — Answer: yes, until either (a) you run `restorecon`, (b) `/.autorelabel` triggers (only at full system relabel), or (c) the file is `cp -a`-replaced from a correctly-labeled source. Wrong context **persists**.

---

## 🪤 Trap Registry Update — End of Lab 08

| Trap ID | Category | Rehearsed? | If hit, repeat in |
|---|---|---|---|
| T32 | Users / Groups / Permissions | ✅ | — |
| T31 | Users / Groups / Permissions | ✅ | — |

3-lab trap window (06+07+08): **T01, T02, T07, T43, T32, T31** = **6 unique traps** ✓

Next lab (09) traps: **T17** (mask vs disable confusion — mask = symlink to /dev/null!) · **T16** (Editing unit file without daemon-reload).

---

## 🎓 What You Now Own

1. `cp` (bare) — when "throw it somewhere temporary" is enough.
2. `cp -p` — preserve mode, owner, group, mtime (the "no surprises" copy).
3. `cp -R` / `-r` — recursion only.
4. `cp -a` — archive mode (recursive + everything preserved).
5. `cp --preserve=context` / `--no-preserve=context` — fine-grained SELinux control.
6. `cp -i` / `-n` — interactive / no-clobber safety.
7. The `src/.` idiom for "copy contents, not the dir itself."
8. The full `cp + restorecon -Rv + chown -R` pattern for staging into `/home/<user>/.ssh`.
9. `matchpathcon` to ask "what context SHOULD this be?"
10. The trap muscle memory: `cp -a` is NOT always right — when copying into a policy-managed dir, follow with `restorecon`.
