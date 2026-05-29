# Lab 30a: Navigating `info` Pages (RHCSA)

- **Series:** linux-ops-mastery — Documentation Navigation and Discovery
- **Trilogy:** `30a` (RHCSA hand-typed) -> `30b` (Ansible mirror) -> `30c` (Verify capstone)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (rotation #30):** `/sys` (read-only orientation path)
- **Sandbox (Tier B):** `/tmp/lab30a` with `USER=labuser_30_info`, `GROUP=labgrp_30_info`
- **Traps rehearsed this lab:** **T30-A** (`info` is Texinfo docs, not `man` roff pages) · **T30-B** (minimal install may not include `info` package) · **T41** · **T44**

> **This lab's topic:** navigating GNU info pages with `info`, the `info` command, `n/p/u` movement keys, `/search`, and `q` to quit.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "📁  PRACTICE DIR: /sys"
echo "⚠️  TRAP REMINDERS THIS LAB: T30-A T30-B T41 T44"
ls -ld /sys /usr/share/info 2>/dev/null || true
command -v info >/dev/null && info --version | head -n 1 || echo "info command missing"
```

> **STOP — paste header output before setup.**

---

## Objective

Build exam-safe reflexes for GNU documentation lookup:

1. Export and inspect the `coreutils` node for **ls invocation** using non-interactive `info ... -o`.
2. Explain interactive movement keys (`n`, `p`, `u`, `/`, `q`) in evidence notes because automated tests cannot press TTY keys.
3. Install and verify the `info` package pathing (`/usr/share/info`) to avoid minimal-install surprises (T30-B).

---

## Core Reference

| Command | Meaning |
|---|---|
| `info` | Launch interactive info browser |
| `info coreutils` | Open top node of the coreutils manual |
| `info coreutils 'ls invocation'` | Jump directly to the `ls` node |
| `info coreutils -o FILE` | Write rendered output to file (non-interactive evidence path) |
| `n` / `p` / `u` | Next node / previous node / up node |
| `/pattern` | Search within the current info document |
| `q` | Quit info browser |
| `rpm -ql info` | List files shipped by the `info` package |
| `install-info` | Maintains directory entries for info docs |

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=30
export LAB_SLUG=info
export SANDBOX=/tmp/lab30a
export GROUP=labgrp_30_info
export USER=labuser_30_info
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-30a/task1 /root/rhcsa_journal/lab-30a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> **STOP — paste `id` and `ls -ld` outputs before Task 1.**

---

## Task 1 — Export `coreutils` info node for `ls invocation`

### Purpose

Execute the required non-interactive pattern:

- `info coreutils 'ls invocation'`
- `info coreutils -o /tmp/.../ls.txt`
- `cat` the exported file for evidence

Also record the interactive key map (`n/p/u`, `/`, `q`) in notes since keypresses are not directly testable in automation.

### Main command block

```bash
TASKLOG=/tmp/lab30a/task1.txt
OUT=/tmp/lab30a/ls.txt

# Required non-interactive evidence flow
info coreutils 'ls invocation' -o "${OUT}"          2>&1 | tee "${TASKLOG}"
test -s "${OUT}" && echo "✅ ls.txt populated"      | tee -a "${TASKLOG}"
cat "${OUT}"                                        | tee -a "${TASKLOG}"

# Interactive key documentation (TTY behavior note)
cat >> "${TASKLOG}" <<'EOF'
KEY_NAV_NOTES:
- n = next node
- p = previous node
- u = up node
- /pattern = search within info document
- q = quit info browser
EOF

echo "exit was: $?"                                 | tee -a "${TASKLOG}"
```

### Trap callout

- **T30-A:** `info` and `man` are different formats and ecosystems (`Texinfo` vs `roff`).
- Do not claim "man output proves info navigation"; they are related references, not the same document tree.

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-30a/task1
cp /tmp/lab30a/task1.txt "${JDIR}/evidence.txt"
cp /tmp/lab30a/ls.txt "${JDIR}/ls.txt"
```

---

## Task 2 — Install and verify `info` docs tree

### Purpose

Rehearse minimal-install recovery flow for T30-B:

1. Install `info` package with `dnf`.
2. Validate shipped files contain `share` paths.
3. Confirm `/usr/share/info` exists and is populated.

### Main command block

```bash
TASKLOG=/tmp/lab30a/task2.txt

dnf install -y info                                 2>&1 | tee "${TASKLOG}"
rpm -q info                                         2>&1 | tee -a "${TASKLOG}"
rpm -ql info | grep share                           2>&1 | tee -a "${TASKLOG}"
ls -la /usr/share/info                              2>&1 | tee -a "${TASKLOG}"

command -v install-info >/dev/null \
  && echo "✅ install-info present"                 | tee -a "${TASKLOG}" \
  || echo "❌ install-info missing"                 | tee -a "${TASKLOG}"

echo "exit was: $?"                                 | tee -a "${TASKLOG}"
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-30a/task2
cp /tmp/lab30a/task2.txt "${JDIR}/evidence.txt"
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

echo "── Lab 30a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 30a Checklist

- [ ] Task 1 completed (`info coreutils 'ls invocation'` exported to `/tmp/lab30a/ls.txt` and key-map notes recorded)
- [ ] Task 2 completed (`dnf install info`, `rpm -ql info | grep share`, `ls /usr/share/info`)
- [ ] T30-A and T30-B trap notes recorded in evidence
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
