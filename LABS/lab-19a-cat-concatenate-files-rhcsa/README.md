# Lab 19a: Concatenating Files with `cat` (RHCSA)

- **Series:** linux-ops-mastery — Text Streams and File Composition
- **Trilogy:** `19a` (RHCSA hand-typed) → `19b` (Ansible) → `19c` (Verify)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2
- **Practice Directory (rotation #19):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab19a` with `USER=labuser_19_catjoin`, `GROUP=labgrp_19_catjoin`
- **Traps rehearsed this lab:** **T19-A** (`cat > file` truncates target when you meant `>>`) · **T19-B** (`cat -A` reveals hidden chars) · **T41** · **T44**

> **This lab's practice directory is: `/usr`** (read-only inspection context) while all writes happen in `/tmp/lab19a`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T19-A T19-B T41 T44"
echo "📁  PRACTICE DIR: /usr"
ls -ld /usr
```

> **STOP — paste header output before setup.**

---

## Objective

Build file-joining reflexes with `cat`:

1. Concatenate multiple files in ordered output streams.
2. Inspect numbered lines and hidden characters with `cat -n` and `cat -A`.
3. Collapse repeated blank lines with `cat -s`.
4. Use heredocs with `cat <<'EOF'` safely, including quoted vs unquoted delimiter behavior.

---

## Core Reference

| Command | Meaning |
|---|---|
| `cat f1 f2 f3` | Print files in order to stdout |
| `cat f1 f2 > out` | Merge into one output file (truncate/create) |
| `cat -n FILE` | Number output lines |
| `cat -A FILE` | Show tabs/endings/non-printing chars |
| `cat -s FILE` | Squeeze consecutive blank lines |
| `cat <<'EOF'` | Literal heredoc (no variable expansion) |
| `cat <<EOF` | Expanding heredoc (variables expand) |

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=19
export LAB_SLUG=catjoin
export SANDBOX=/tmp/lab19a
export GROUP=labgrp_19_catjoin
export USER=labuser_19_catjoin
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-19a/task1 /root/rhcsa_journal/lab-19a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> **STOP — paste `id` and `ls -ld` outputs before Task 1.**

---

## Task 1 — Concatenate system outputs and build a joined report

### Purpose

Execute the exact RHCSA-style pattern:

- `cat /etc/redhat-release /etc/hostname`
- `cat -n /etc/passwd | head`
- Build a joined report with `cat f1 f2 > out`

### Main command block

```bash
TASKLOG=/tmp/lab19a/task1.txt
mkdir -p /tmp/lab19a/parts

# Required system-view commands
cat /etc/redhat-release /etc/hostname              2>&1 | tee "$TASKLOG"
cat -n /etc/passwd | head                          2>&1 | tee -a "$TASKLOG"

# Build source fragments
cat /etc/redhat-release > /tmp/lab19a/parts/f1.txt
cat /etc/hostname       > /tmp/lab19a/parts/f2.txt

# Required merge pattern
cat /tmp/lab19a/parts/f1.txt /tmp/lab19a/parts/f2.txt > /tmp/lab19a/joined-report.txt

# T19-B: hidden characters and squeezes
printf "A\tB\n\n\nC\n" > /tmp/lab19a/parts/hidden.txt
cat -A /tmp/lab19a/parts/hidden.txt                2>&1 | tee -a "$TASKLOG"
cat -s /tmp/lab19a/parts/hidden.txt                2>&1 | tee -a "$TASKLOG"

wc -l /tmp/lab19a/joined-report.txt                2>&1 | tee -a "$TASKLOG"
cat -n /tmp/lab19a/joined-report.txt               2>&1 | tee -a "$TASKLOG"
echo "exit was: $?"
```

### Trap Drill (T19-A)

```bash
echo "base-line" > /tmp/lab19a/trap.txt
echo "append-ok" >> /tmp/lab19a/trap.txt
cat /tmp/lab19a/trap.txt
echo "oops-overwrite" > /tmp/lab19a/trap.txt   # this destroys prior content
cat /tmp/lab19a/trap.txt
```

> **Checkpoint:** explain why the final file has only one line (`>` truncates first).

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-19a/task1
cp /tmp/lab19a/task1.txt "$JDIR/evidence.txt"
cp /tmp/lab19a/joined-report.txt "$JDIR/joined-report.txt"
```

---

## Task 2 — Heredoc script creation as `${USER}`

### Purpose

Write a script with `cat <<'EOF'` as the Tier B lab user, then contrast quoted vs unquoted EOF behavior.

### Main command block

```bash
TASKLOG=/tmp/lab19a/task2.txt

# Literal heredoc (quoted EOF) as lab user
sudo -u "${USER}" bash -c "cat <<'EOF' > '${USER_HOME}/literal-script.sh'
#!/usr/bin/env bash
echo \"user=\$USER\"
echo \"home=\$HOME\"
EOF"

# Expanding heredoc (unquoted EOF) as root
cat <<EOF > /tmp/lab19a/expanded-script.sh
#!/usr/bin/env bash
echo "user=$USER"
echo "home=$HOME"
EOF

chmod +x "${USER_HOME}/literal-script.sh" /tmp/lab19a/expanded-script.sh
stat -c '%U:%G %a %n' "${USER_HOME}/literal-script.sh" /tmp/lab19a/expanded-script.sh | tee "$TASKLOG"
cat -n "${USER_HOME}/literal-script.sh" /tmp/lab19a/expanded-script.sh                | tee -a "$TASKLOG"
echo "exit was: $?"
```

### What to observe

- In `literal-script.sh`, `$USER` and `$HOME` remain literal text.
- In `expanded-script.sh`, variables are expanded at write time.
- Ownership on the first file is `${USER}:${GROUP}` because the write happened through `sudo -u`.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-19a/task2
cp /tmp/lab19a/task2.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/literal-script.sh" "$JDIR/literal-script.sh"
cp /tmp/lab19a/expanded-script.sh "$JDIR/expanded-script.sh"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 19a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 19a Checklist

- [ ] Task 1 completed (`cat /etc/redhat-release /etc/hostname`, `cat -n /etc/passwd | head`, joined report with `cat f1 f2 > out`)
- [ ] Task 2 completed (heredoc script as `${USER}` + quoted vs unquoted EOF contrast)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
