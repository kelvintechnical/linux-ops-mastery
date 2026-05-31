# Lab 26a: Command Mode and Insert Mode in `vi` (RHCSA) — Non-Interactive `ex` Pattern

- **Series:** linux-ops-mastery — Text File Management
- **Trilogy:** **`26a`** (RHCSA hand-typed) → [`26b`](../lab-26b-vi-editor-ansible/) (Ansible boundary) → [`26c`](../lab-26c-vi-editor-verify/) (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (Task 1 = non-interactive `vi -c` substitution + diff verification · Task 2 = numbered view + backup save + privilege-safe write pattern)
- **Practice Directory (rotation #26):** `/opt`
- **Sandbox (Tier B):** `/tmp/lab26a` with `USER=labuser_26_vi`, `GROUP=labgrp_26_vi`
- **Traps rehearsed:** **T26-A** (forget `Esc` before `:wq`, accidentally writing literal `:wq` text) · **T26-B** (editing `/etc/passwd` directly with `vi`; safe tool is `vipw`, covered in Lab 27) · **T41** · **T44**

> This lab demonstrates `vi` behavior using **non-interactive `ex` commands** (`vi -c ...`) because interactive keystrokes cannot be paste-tested reliably.

---

## LAB HEADER BLOCK

```bash
echo "ENV:  ${ENV:-DECLARE_ME}"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "PRACTICE DIR: /opt"
echo "TRAPS THIS LAB: T26-A T26-B T41 T44"
ls -ld /opt
vim --version 2>/dev/null | head -n 2 || vi --version 2>/dev/null | head -n 2 || echo "vi version not printed"
```

> **STOP - Paste header output before setup.**

---

## Objective

Build editor muscle memory for RHCSA-safe text edits:

1. Understand command mode vs insert mode transitions (`i`, `a`, `A`, `o`, `O`, `Esc`).
2. Run deterministic substitutions with `vi -c` and verify with `diff`.
3. Practice save/quit reflexes (`:wq`, `:q!`) and undo/redo (`u`, `Ctrl+r`) conceptually.
4. Use privilege-safe write fallback `:w !sudo tee` when a file was opened without permissions.

---

## Quick Reference

| Token / Command | Meaning |
|---|---|
| `i` / `a` / `A` / `o` / `O` | Enter insert mode at cursor / after cursor / end of line / new line below / new line above |
| `Esc` | Return to command mode |
| `:wq` | Write and quit |
| `:q!` | Quit without saving |
| `:w !sudo tee FILE` | Write buffer through sudo when file is root-owned |
| `/pattern` then `n` / `N` | Search forward, then next/previous match |
| `dd` / `yy` / `p` | Delete line / yank line / paste |
| `u` / `Ctrl+r` | Undo / redo |
| `:%s/foo/bar/g` | Global substitution in whole file |

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=26
export LAB_SLUG=vi
export SANDBOX=/tmp/lab26a
export GROUP=labgrp_26_vi
export USER=labuser_26_vi
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-26a/task1 /root/rhcsa_journal/lab-26a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
getent group "${GROUP}"
getent passwd "${USER}"
echo "setup exit: $?"
```

> **STOP - Paste `id`, `ls -ld`, and both `getent` lines before Task 1.**

---

## Task 1 — Non-interactive substitution with `vi -c` + diff proof

### Purpose

Practice a reproducible exam-safe edit:

- backup file
- run substitution through `vi -c`
- prove the exact change with `diff`

### Main command block

```bash
TASKLOG=/tmp/lab26a/task1.txt
SRC=/tmp/lab26a/app.conf
BAK=/tmp/lab26a/app.conf.bak

cat > "${SRC}" <<'EOF'
mode=old
owner=ops
path=/opt/app
note=old behavior
EOF

cp -a "${SRC}" "${BAK}"

# Required pattern from this lab
vi -c ':1,$s/old/new/g' -c ':wq' "${SRC}"

echo "=== diff against backup ==="                        | tee "${TASKLOG}"
diff -u "${BAK}" "${SRC}"                                | tee -a "${TASKLOG}"
echo "=== final file ==="                                | tee -a "${TASKLOG}"
cat "${SRC}"                                             | tee -a "${TASKLOG}"
grep -n 'new' "${SRC}"                                   | tee -a "${TASKLOG}"
echo "task1 exit: $?"
```

### Trap callout (T26-A)

If you are in insert mode and type `:wq` without pressing `Esc`, those characters become file text instead of a command.

```bash
cat > /tmp/lab26a/t26a-trap-demo.txt <<'EOF'
line1
line2
EOF
echo "Simulated trap marker (what bad save looks like):" | tee -a "${TASKLOG}"
echo ":wq" >> /tmp/lab26a/t26a-trap-demo.txt
tail -n 3 /tmp/lab26a/t26a-trap-demo.txt                 | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26a/task1
mkdir -p "${JDIR}"
cp /tmp/lab26a/task1.txt "${JDIR}/evidence.txt"
cp "${SRC}" "${BAK}" "${JDIR}/"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Task 2 — Numbered view, backup save, and privilege-safe write

### Purpose

Demonstrate supporting editor behaviors:

1. `:set number` and `:sav` from CLI-driven `vi`.
2. privilege-safe save path with `:w !sudo tee`.
3. reinforce Lab 27 boundary: do not use `vi` directly on `/etc/passwd`.

### Main command block

```bash
TASKLOG=/tmp/lab26a/task2.txt
SRC=/tmp/lab26a/notes.txt

cat > "${SRC}" <<'EOF'
alpha
beta
gamma
EOF

# Required pattern from this lab
vi -c ':set number' -c ':sav /tmp/lab26a/notes.txt.bak' -c ':q' "${SRC}"

ls -l /tmp/lab26a/notes.txt*                              | tee "${TASKLOG}"
diff -u "${SRC}" /tmp/lab26a/notes.txt.bak                | tee -a "${TASKLOG}" || true

cat <<'EOF' | tee -a "${TASKLOG}"
Privilege-safe write demo (interactive command to know):
  :w !sudo tee /etc/some-root-file.conf >/dev/null
Then quit with:
  :q!
EOF

# Tier B weave: write as ${USER} and verify ownership
sudo -u "${USER}" bash -c 'echo "vi-task2 by $(whoami) $(date -Is)" > "'"${USER_HOME}"'/task2-asuser.txt"'
stat -c '%U:%G %a %n' "${USER_HOME}/task2-asuser.txt"    | tee -a "${TASKLOG}"
cat "${USER_HOME}/task2-asuser.txt"                      | tee -a "${TASKLOG}"

cat <<'EOF' | tee -a "${TASKLOG}"
T26-B reminder:
  Do NOT edit /etc/passwd with vi directly.
  Use vipw (covered in Lab 27) to avoid database corruption races.
EOF

echo "task2 exit: $?"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-26a/task2
mkdir -p "${JDIR}"
cp /tmp/lab26a/task2.txt "${JDIR}/evidence.txt"
cp /tmp/lab26a/notes.txt /tmp/lab26a/notes.txt.bak "${JDIR}/"
cp "${USER_HOME}/task2-asuser.txt" "${JDIR}/"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
ls -la "${JDIR}"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

rm -f /tmp/lab26a/task1.txt /tmp/lab26a/task2.txt
rm -f /tmp/lab26a/app.conf /tmp/lab26a/app.conf.bak
rm -f /tmp/lab26a/notes.txt /tmp/lab26a/notes.txt.bak
rm -f /tmp/lab26a/t26a-trap-demo.txt
rm -f "${USER_HOME}/task2-asuser.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-26a cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Lab 26a Checklist

- [ ] Task 1 completed (`vi -c ':1,$s/old/new/g' -c ':wq'` + `diff -u` proof)
- [ ] Task 2 completed (`:set number`, `:sav`, and `:w !sudo tee` pattern documented)
- [ ] T26-A and T26-B traps explained
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
