# Lab 05a: Directory Navigation (RHCSA) — `pwd`, `cd`, `$OLDPWD`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** `05a` (RHCSA hand-typed) → ⛔ no `05b` (Section 18 boundary — `cd` has no honest Ansible module; `chdir:` is task-scoped only) → [`05c`](../lab-05c-directory-nav-verify/) (Verify capstone)
- **Career arcs covered:** RHCSA EX200 (every "navigate to /path and run X" reflex), SRE (rapid context switches between log dirs during incidents), DevOps (script-relative `pwd`-aware paths)
- **Prerequisite:** [`Lab 04c`](../lab-04c-capture-both-output-error-verify/) completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = `cd` / `pwd -L`/`-P` / `cd ..` / `cd ~` · Task 2 = `cd -` / `$OLDPWD` / symlink trap T41)
- **Practice Directory (rotation #05):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab05a` with `USER=labuser_05_nav`, `GROUP=labgrp_05_nav`, `USER_HOME=/tmp/lab05a/home_labuser_05_nav`
- **Traps rehearsed this lab:** **T41** (symlink path vs real path — `pwd -L` vs `pwd -P` reveal which one the shell is "in") · **T42** (assuming `cd ~` goes to `/home/USER` when invoked under sudo — actually goes to root's home) · **T43** (running a script with relative paths after `cd` — script must `cd "$(dirname "$0")"` first) · **T44** (Closeout audit)

> **This lab's practice directory is: `/usr`** — the largest dir on most systems; `/usr/bin`, `/usr/lib`, `/usr/share` are all reachable in one `cd`. Perfect for navigation drills.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T41 T42 T43"
echo "📁  PRACTICE DIR: /usr"
echo ""
echo "💡 /usr context:"
ls -ld /usr /usr/bin /usr/lib /usr/share
ls /usr | head -n 10
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output before setup.**

---

## Lab-Wide Setup — Tier B Sandbox (Section 1.5)

```bash
sudo -i

export LAB_NUM=05
export LAB_SLUG=nav
export SANDBOX=/tmp/lab05a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-05a/task1 /root/rhcsa_journal/lab-05a/task2

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /usr
/usr is the largest directory on most systems. It holds everything
installed by the package manager that is not needed for the initial
boot: compilers, editors, most commands, man pages, and shared data.
Navigation labs use /usr because every subdir we'll cd into is
predictably present on every Linux host.
EOF

# Build a symlink chain inside the sandbox for T41 (real vs symlink path)
mkdir -p "${SANDBOX}/real/deep/path"
ln -s   "${SANDBOX}/real" "${SANDBOX}/sym-to-real"

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /usr "${SANDBOX}/sym-to-real"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste the `id`, four `ls -ld`, and the symlink line before Task 1.**

---

## Task 1 — `cd`, `pwd -L` / `-P`, `cd ..`, `cd ~`

**Practice directory this task:** `/usr` plus the sandbox symlink chain.

### 🔁 Warm-Up

```bash
pwd                                                     2>&1 | tee /tmp/lab05a/warmup.txt
echo "HOME=${HOME}"
ls -ld /usr /usr/bin /usr/share/man
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Walk through `/usr` with `cd`; demonstrate `pwd -L` (logical) vs `pwd -P` (physical, resolves symlinks) using the sandbox symlink; cover `cd ..` and `cd ~`.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `pwd` | Pre-state — we walk away from this dir and `cd -` back later |
| `echo "HOME=${HOME}"` | Pre-state for `cd ~` test |
| `ls -ld /usr/bin` | Confirms target dirs exist before we cd into them |

### Main command block

```bash
TASKLOG=/tmp/lab05a/task1.txt

echo "═══ Part A: cd into /usr/bin and inspect ═══"        2>&1 | tee $TASKLOG
cd /usr/bin
pwd                                                       | tee -a $TASKLOG
ls | head -n 5                                            | tee -a $TASKLOG

echo "═══ Part B: cd .. (parent dir) ═══"                  | tee -a $TASKLOG
cd ..
pwd                                                       | tee -a $TASKLOG

echo "═══ Part C: cd ~ (home) ═══"                         | tee -a $TASKLOG
cd ~
pwd                                                       | tee -a $TASKLOG
test "$(pwd)" = "${HOME}" \
    && echo "✅ cd ~ landed at \$HOME (${HOME})" \
    || echo "❌ cd ~ != \$HOME" \
    | tee -a $TASKLOG

echo "═══ Part D: T41 — pwd -L vs pwd -P via symlink ═══"  | tee -a $TASKLOG
cd "${SANDBOX}/sym-to-real/deep/path"
echo "After cd through symlink:"                          | tee -a $TASKLOG
echo "  pwd       = $(pwd)"                               | tee -a $TASKLOG
echo "  pwd -L    = $(pwd -L)"                            | tee -a $TASKLOG
echo "  pwd -P    = $(pwd -P)"                            | tee -a $TASKLOG

LOGICAL=$(pwd -L)
PHYSICAL=$(pwd -P)
if [ "${LOGICAL}" != "${PHYSICAL}" ]; then
    echo "✅ T41 demonstrated — logical and physical differ"  | tee -a $TASKLOG
else
    echo "❌ T41 not demonstrated"                           | tee -a $TASKLOG
fi

echo "═══ Part E: same walk AS ${USER} (Tier B) ═══"        | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd /usr/share
    echo "as-USER pwd: $(pwd)"
    cd '"${SANDBOX}"'/sym-to-real/deep/path
    echo "as-USER pwd -L: $(pwd -L)"
    echo "as-USER pwd -P: $(pwd -P)"
' > "${USER_HOME}/walk.txt"
cat "${USER_HOME}/walk.txt"                                | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/walk.txt"              | tee -a $TASKLOG

echo "exit was: $?"
```

### Expected output

```text
═══ Part A: cd into /usr/bin and inspect ═══
/usr/bin
[
2to3
2to3-3.9
...
═══ Part B: cd .. (parent dir) ═══
/usr
═══ Part C: cd ~ (home) ═══
/root
✅ cd ~ landed at $HOME (/root)
═══ Part D: T41 — pwd -L vs pwd -P via symlink ═══
After cd through symlink:
  pwd       = /tmp/lab05a/sym-to-real/deep/path
  pwd -L    = /tmp/lab05a/sym-to-real/deep/path
  pwd -P    = /tmp/lab05a/real/deep/path
✅ T41 demonstrated — logical and physical differ
═══ Part E: same walk AS labuser_05_nav (Tier B) ═══
as-USER pwd: /usr/share
as-USER pwd -L: /tmp/lab05a/sym-to-real/deep/path
as-USER pwd -P: /tmp/lab05a/real/deep/path
labuser_05_nav:labgrp_05_nav 644 /tmp/lab05a/home_labuser_05_nav/walk.txt
```

### Switches

| Token | Meaning |
|---|---|
| `cd /path` | Change to absolute path |
| `cd ..` | Parent dir |
| `cd ~` | `$HOME` |
| `pwd` | Print logical (default) working dir |
| `pwd -L` | Logical — what the shell tracks (preserves symlink in path) |
| `pwd -P` | Physical — resolved through symlinks |
| `cd /sym/path && pwd -L` vs `pwd -P` | Diverge when path contains symlink components |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Shell `$PWD` tracking | Bash stores the logical path you typed; `pwd -L` reads `$PWD` |
| Kernel inode tracking | Every dir has an inode; `pwd -P` does `getcwd(2)` from the kernel |
| **🪤 Trap Risk T41** | Confusing logical and physical when scripts compare paths. **Fix:** decide which one your script needs and use the matching flag. |
| **🪤 Trap Risk T42** | `cd ~` under `sudo -i` goes to `/root`, not the original user's home. **Fix:** use `sudo -u USER -H` for user-relative `cd ~`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| sandbox dirs | `test -d "${SANDBOX}/real/deep/path"` | Lab artifacts present |
| symlink chain | `readlink "${SANDBOX}/sym-to-real"` returns `${SANDBOX}/real` | T41 reproducible |
| Tier B walk evidence | `stat -c '%U' "${USER_HOME}/walk.txt"` returns `${USER}` | sudo -u ran |

> **Reboot note:** All sandbox content is under `/tmp` (tmpfs) — re-run Lab-Wide Setup to rebuild after reboot.

### Journal write

```bash
LAB=lab-05a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab05a/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/walk.txt" "$JDIR/walk-asuser.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    cd, cd .., cd ~, pwd -L vs -P; T41 symlink path divergence
COMMANDS: cd, pwd, pwd -L, pwd -P, ls -ld, sudo -u USER -H bash -c
TRAPS:    T41 demonstrated; T42 noted
TIER B:   walk-asuser.txt owned by ${USER}:${GROUP}
NEXT:     task2 — cd - and \$OLDPWD round-trip
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab05a/warmup.txt /tmp/lab05a/task1.txt
rm -f "${USER_HOME}/walk.txt"
ls /tmp/lab05a
echo "exit was: $?"
```

> **STOP — paste the T41 `✅` line and the Tier B `walk-asuser.txt` ownership line before Task 2.**

---

## Task 2 — `cd -` and `$OLDPWD` round-trip (T43)

### 🔁 Warm-Up

```bash
echo "OLDPWD=${OLDPWD:-unset}"
cd /usr/share
echo "OLDPWD now=${OLDPWD}"
cd -
echo "After cd -, pwd=$(pwd)"
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Use `cd -` to bounce between two directories; demonstrate that `$OLDPWD` is the variable behind it; rehearse T43 by running a "broken" relative-path script and the `cd "$(dirname "$0")"` fix.

### Main command block

```bash
TASKLOG=/tmp/lab05a/task2.txt

echo "═══ Part A: cd - round-trip ═══"                     2>&1 | tee $TASKLOG
cd /var/log
echo "PWD=$(pwd)  OLDPWD=${OLDPWD}"                       | tee -a $TASKLOG
cd /etc
echo "PWD=$(pwd)  OLDPWD=${OLDPWD}"                       | tee -a $TASKLOG
cd -                                                       | tee -a $TASKLOG
echo "After cd - PWD=$(pwd)"                              | tee -a $TASKLOG
cd -                                                       | tee -a $TASKLOG
echo "After cd - again PWD=$(pwd)"                        | tee -a $TASKLOG

echo "═══ Part B: T43 — broken relative-path script ═══"   | tee -a $TASKLOG
cat > "${SANDBOX}/broken.sh" <<'EOF'
#!/bin/bash
# Forgets to cd to its own dir — uses unsafe relative path
ls ./data/items.txt 2>&1 | head -n 3 || echo "ls failed (relative path broken)"
EOF
mkdir -p "${SANDBOX}/data"
echo "alpha" > "${SANDBOX}/data/items.txt"
echo "bravo" >> "${SANDBOX}/data/items.txt"
chmod +x "${SANDBOX}/broken.sh"

cd /tmp
"${SANDBOX}/broken.sh"                                    2>&1 | tee -a $TASKLOG

echo "═══ Part C: T43 fix — cd \"\$(dirname \"\$0\")\" ═══" | tee -a $TASKLOG
cat > "${SANDBOX}/fixed.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
ls ./data/items.txt
cat ./data/items.txt
EOF
chmod +x "${SANDBOX}/fixed.sh"

cd /tmp
"${SANDBOX}/fixed.sh"                                     2>&1 | tee -a $TASKLOG

grep -q 'alpha' /tmp/lab05a/task2.txt \
    && echo "✅ T43 fix worked — script is path-independent" \
    || echo "❌ T43 fix did not work" \
    | tee -a $TASKLOG

echo "═══ Part D: round-trip AS ${USER} ═══"               | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    cd /usr
    cd /etc
    cd -
    echo "as-USER PWD after cd -: $(pwd)"
    echo "as-USER OLDPWD: ${OLDPWD}"
' > "${USER_HOME}/round-trip.txt"
cat "${USER_HOME}/round-trip.txt"                          | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/round-trip.txt"        | tee -a $TASKLOG

echo "exit was: $?"
```

### Expected output

```text
═══ Part A: cd - round-trip ═══
PWD=/var/log  OLDPWD=...
PWD=/etc  OLDPWD=/var/log
/var/log
After cd - PWD=/var/log
/etc
After cd - again PWD=/etc
═══ Part B: T43 — broken relative-path script ═══
ls: cannot access './data/items.txt': No such file or directory
ls failed (relative path broken)
═══ Part C: T43 fix — cd "$(dirname "$0")" ═══
./data/items.txt
alpha
bravo
✅ T43 fix worked — script is path-independent
═══ Part D: round-trip AS labuser_05_nav ═══
/etc
as-USER PWD after cd -: /usr
as-USER OLDPWD: /etc
labuser_05_nav:labgrp_05_nav 644 /tmp/lab05a/home_labuser_05_nav/round-trip.txt
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `cd -` | Bounce to `$OLDPWD` and update `$OLDPWD` to the current dir |
| `$OLDPWD` | Bash variable holding the previous directory |
| `cd "$(dirname "$0")"` | Make a script path-independent — `$0` is the script's own path |
| **🪤 Trap Risk T43** | Scripts using relative paths break when invoked from a different dir. **Fix:** `cd "$(dirname "$0")"` at the top. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Round-trip works | output of `cd -` returns expected paths | OLDPWD tracking |
| T43 fix proven | `grep alpha task2.txt` | Path-independent script worked |
| Tier B evidence | `stat -c '%U' round-trip.txt` returns `${USER}` | sudo -u ran |

### Journal write

```bash
LAB=lab-05a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab05a/task2.txt "$JDIR/evidence.txt"
cp "${SANDBOX}/broken.sh" "$JDIR/broken.sh"
cp "${SANDBOX}/fixed.sh" "$JDIR/fixed.sh"
cp "${USER_HOME}/round-trip.txt" "$JDIR/round-trip-asuser.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    cd -, \$OLDPWD round-trip; T43 broken vs fixed relative-path scripts
COMMANDS: cd -, dirname, sudo -u USER -H
TRAPS:    T43 rehearsed
TIER B:   round-trip-asuser.txt owned by ${USER}:${GROUP}
NEXT:     lab-05c — verify capstone (no 05b, Section 18 boundary)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab05a/task2.txt
rm -f "${USER_HOME}/round-trip.txt"
# Keep broken.sh + fixed.sh — 05c uses them
ls /tmp/lab05a
echo "exit was: $?"
```

> **STOP — paste the T43 `✅` line and the Part D Tier B output before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 05a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}"              && echo "❌ home remains"    || echo "✅ home gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste four `✅` lines.**

---

## Lab 05a Checklist (2 tasks + closeout)

- [ ] Lab-Wide Setup — Tier B sandbox + symlink chain
- [ ] Task 1 — pwd -L vs pwd -P diverge (T41); Tier B walk file owned
- [ ] Task 2 — `cd -` round-trip; T43 broken→fixed; Tier B round-trip file owned
- [ ] Lab Closeout — four `✅`

---

## Related Labs

| Lab | Connection |
|---|---|
| ⛔ **No Lab 05b** | Section 18 boundary — `cd` has no honest Ansible module; `chdir:` only changes the working dir for one task |
| **Lab 05c** | Verify capstone — audit walk + round-trip + T43 fix |
| Lab 14a — find | After Lab 05, you can navigate; Lab 14 walks the tree |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
