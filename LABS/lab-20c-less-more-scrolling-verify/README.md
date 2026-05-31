# Lab 20c: Verifying Scrolling Through Large Files — audit + destroy-restore

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** [`20a`](../lab-20a-less-more-scrolling-rhcsa/) (RHCSA) → [`20b`](../lab-20b-less-more-scrolling-ansible/) (Ansible) → `20c` (Verify)
- **Time Estimate:** 20-30 minutes
- **Tasks:** 2 (Task 1 = audit 20a/20b evidence and search captures, Task 2 = destroy-restore drill)
- **Practice Directory (rotation #20):** `/etc`
- **Sandbox (Tier B):** `/tmp/lab20c` with `USER=labuser_20_pager`, `GROUP=labgrp_20_pager`
- **Traps rehearsed:** **T20-A** · **T20-B** · **T41** · **T44**

---

## LAB HEADER BLOCK

```bash
echo "ENV:  ${ENV:-DECLARE_ME}"
echo "TIME: $(date -Is)"
echo "USER: $(whoami)@$(hostname)"
echo "TRAPS THIS LAB: T20-A T20-B T41 T44"
echo "PRACTICE DIR: /etc"
test -f /root/rhcsa_journal/lab-20a/task1/evidence.txt && echo "20a task1 evidence present"
test -f /root/rhcsa_journal/lab-20b/task1/lab20-less-defaults.sh && echo "20b alias/defaults evidence present"
```

---

## Objective

1. Audit that Lab 20a and 20b produced real, reusable pager evidence.
2. Verify less-defaults profile file exists and contains expected markers/aliases.
3. Run destroy-restore drill (T41) and confirm artifacts can be reconstructed.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export LAB_NUM=20
export LAB_SLUG=pager
export SANDBOX=/tmp/lab20c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-20c/task1 /root/rhcsa_journal/lab-20c/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Audit evidence from 20a and 20b

### Purpose

Confirm that:

- 20a captured search/navigation evidence.
- 20b deployed `/etc/profile.d/lab20-less-defaults.sh`.
- Search hits were captured and auditable.

### Main command block

```bash
TASKLOG=/tmp/lab20c/task1.txt

{
  echo "=== 20a evidence audit ==="
  ls -la /root/rhcsa_journal/lab-20a/task1 /root/rhcsa_journal/lab-20a/task2
  test -f /root/rhcsa_journal/lab-20a/task1/less-nav-demo.sh && echo "OK nav demo present"
  grep -E "error|systemd|/error|\?systemd" /root/rhcsa_journal/lab-20a/task1/evidence.txt | head -n 10 || true

  echo
  echo "=== 20b evidence audit ==="
  ls -la /root/rhcsa_journal/lab-20b/task1 /root/rhcsa_journal/lab-20b/task2
  test -f /root/rhcsa_journal/lab-20b/task1/lab20-less-defaults.sh && echo "OK less defaults file archived"
  grep -c "LAB 20 LESS DEFAULTS" /root/rhcsa_journal/lab-20b/task1/lab20-less-defaults.sh
  grep -E "alias less|export LESS" /root/rhcsa_journal/lab-20b/task1/lab20-less-defaults.sh

  echo
  echo "=== live profile check ==="
  ls -lZ /etc/profile.d/lab20-less-defaults.sh
  cat /etc/profile.d/lab20-less-defaults.sh
  sudo -u "${USER}" bash -c "source /etc/profile.d/lab20-less-defaults.sh; alias less" || true
} 2>&1 | tee "${TASKLOG}"

echo "task1 exit: $?"
```

### Expected output

```text
OK nav demo present
...
OK less defaults file archived
2
alias less='less -N -S'
export LESS='-N -S'
...
```

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20c/task1
mkdir -p "${JDIR}"
cp /tmp/lab20c/task1.txt "${JDIR}/evidence.txt"
echo "TASK1 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
```

---

## Task 2 — Destroy-restore drill (T41)

### Purpose

Delete local working artifacts, restore required profile defaults from journal copy, and prove pager setup is functional again.

### Main command block

```bash
TASKLOG=/tmp/lab20c/task2.txt
SRC=/root/rhcsa_journal/lab-20b/task1/lab20-less-defaults.sh
DST=/etc/profile.d/lab20-less-defaults.sh

{
  echo "=== phase 1: snapshot ==="
  sha256sum "${DST}" 2>/dev/null || echo "no live defaults file yet"
  ls -la /tmp/lab20a /tmp/lab20b /tmp/lab20c 2>/dev/null || true

  echo
  echo "=== phase 2: destroy local temp dirs ==="
  rm -rf /tmp/lab20a /tmp/lab20b /tmp/lab20c
  test ! -d /tmp/lab20a -a ! -d /tmp/lab20b -a ! -d /tmp/lab20c && echo "destroy clean"

  echo
  echo "=== phase 3: restore defaults file from journal ==="
  cp "${SRC}" "${DST}"
  chmod 0644 "${DST}"
  restorecon -v "${DST}" 2>/dev/null || true
  sha256sum "${SRC}" "${DST}"
  diff -u "${SRC}" "${DST}" && echo "restore byte-identical"

  echo
  echo "=== phase 4: functional verification ==="
  mkdir -p "${SANDBOX}" "${USER_HOME}"
  chown -R "${USER}:${GROUP}" "${SANDBOX}"
  sudo -u "${USER}" bash -c "source '${DST}'; alias less; less --version | head -n 1" || true
  awk 'NR<=5{print}' /etc/services > "${USER_HOME}/verify-head.txt"
  stat -c '%U:%G %a %n' "${USER_HOME}/verify-head.txt"
} 2>&1 | tee "${TASKLOG}"

echo "task2 exit: $?"
```

### Concept Card

| Check | Why it matters |
|---|---|
| `diff -u SRC DST` empty | Restore fidelity |
| `alias less` after `source` | Configuration actually loads |
| user-owned verify file | Tier B path and identity still healthy |
| **🪤 T41** | Destroy-restore proves journal can rebuild state |

### Journal write

```bash
JDIR=/root/rhcsa_journal/lab-20c/task2
mkdir -p "${JDIR}"
cp /tmp/lab20c/task2.txt "${JDIR}/evidence.txt"
cp "${USER_HOME}/verify-head.txt" "${JDIR}/verify-head.txt"
echo "TASK2 COMPLETE $(date -Is)" > "${JDIR}/done.txt"
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
rm -f /tmp/lab20c/task1.txt /tmp/lab20c/task2.txt
rm -f "${USER_HOME}/verify-head.txt"

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "---- lab-20c cleanup audit ----"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 20a** | Interactive pager key fluency and follow-mode behavior |
| **Lab 20b** | Ansible-safe pager management and trap handling |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
