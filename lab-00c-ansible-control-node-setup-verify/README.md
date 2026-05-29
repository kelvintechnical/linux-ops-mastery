# Lab 00c: Ansible Control Node Setup (Verify) — Audit + Persistence Drill

- **Series:** linux-ops-mastery — Foundations
- **Trilogy:** [`00a`](../lab-00a-ansible-control-node-setup-rhcsa/) → [`00b`](../lab-00b-ansible-control-node-setup-ansible/) → **`00c`** (Verify — you are here)
- **Prerequisite:** [`Lab 00a`](../lab-00a-ansible-control-node-setup-rhcsa/) and [`Lab 00b`](../lab-00b-ansible-control-node-setup-ansible/) completed
- **Time Estimate:** 20–30 minutes
- **Tasks:** 2 (Task 1 = audit 00a/00b artifacts · Task 2 = restart-survive simulation + re-ping AS `${USER}` — **T41**, **T42**)
- **Practice Directory:** `/etc` (configs) and `/usr/share/ansible/collections`
- **Sandbox (Tier B):** `/tmp/lab00c` with `USER=labuser_00_verify`, `GROUP=labgrp_00_verify`
- **Traps rehearsed this lab:** **T00-A/B/C/D/E** (audit each) · **T41** (post-reboot the configs must still work) · **T42** (verbalize what survives) · **T44** (Closeout audit)

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T00-A/B/C/D/E T41 T42 T44"
echo ""
echo "📓 00a + 00b journals:"
ls -la /root/rhcsa_journal/lab-00a/task1/ /root/rhcsa_journal/lab-00a/task2/
ls -la /root/rhcsa_journal/lab-00b/task1/ /root/rhcsa_journal/lab-00b/task2/
echo "Shell version: $BASH_VERSION"
```

> **STOP — paste header output. If either journal is empty, return to that lab.**

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=00
export LAB_SLUG=verify
export SANDBOX=/tmp/lab00c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-00c/task1 /root/rhcsa_journal/lab-00c/task2

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Give USER its own .ansible.cfg (mirrors Lab 00a Part D for a fresh user)
cat > "${USER_HOME}/.ansible.cfg" <<'EOF'
[defaults]
inventory       = ~/inventory
host_key_checking = False
stdout_callback = yaml
EOF
echo "localhost ansible_connection=local" > "${USER_HOME}/inventory"
chown "${USER}:${GROUP}" "${USER_HOME}/.ansible.cfg" "${USER_HOME}/inventory"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output before Task 1.**

---

## Task 1 — Audit 00a + 00b artifacts (T00-A through T00-E)

### 🔁 Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-00a/ /root/rhcsa_journal/lab-00b/      2>&1 | tee /tmp/lab00c/warmup.txt
ansible --version | head -n 5
ansible-galaxy collection list | grep -E 'posix|general'
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Main command block

```bash
TASKLOG=/tmp/lab00c/task1.txt

echo "═══ Part A: T00-A — ansible-core present, no legacy ansible ═══" 2>&1 | tee $TASKLOG
rpm -q ansible-core                                                 | tee -a $TASKLOG
rpm -q ansible 2>/dev/null \
    && echo "❌ T00-A FAIL — legacy ansible present" \
    || echo "✅ T00-A clean — no legacy ansible" \
    | tee -a $TASKLOG

echo "═══ Part B: T00-B — both collections present ═══"                | tee -a $TASKLOG
ansible-galaxy collection list 2>/dev/null \
    | grep -E '^(ansible\.posix|community\.general)\s'              | tee -a $TASKLOG
N=$(ansible-galaxy collection list 2>/dev/null \
    | grep -cE '^(ansible\.posix|community\.general)\s')
test "${N}" -ge 2 \
    && echo "✅ T00-B clean — both collections installed" \
    || echo "❌ T00-B FAIL — collections missing" \
    | tee -a $TASKLOG

echo "═══ Part C: T00-C — root + USER configs ═══"                     | tee -a $TASKLOG
test -s /root/.ansible.cfg && echo "✅ root .ansible.cfg present"      | tee -a $TASKLOG
test -s /root/inventory    && echo "✅ root inventory present"         | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c 'test -s ~/.ansible.cfg && echo "✅ ${USER} .ansible.cfg present"' \
                                                                       | tee -a $TASKLOG

echo "═══ Part D: T00-D — playbook journal has --check evidence ═══"   | tee -a $TASKLOG
PB_EVIDENCE=/root/rhcsa_journal/lab-00b/task1/evidence.txt
grep -q '^--- before' "${PB_EVIDENCE}" \
    && echo "✅ T00-D — --check --diff was used (diff hunks present)" \
    || echo "❌ T00-D FAIL — no --check --diff evidence" \
    | tee -a $TASKLOG

echo "═══ Part E: T00-E — idempotence captured ═══"                    | tee -a $TASKLOG
T2_EVIDENCE=/root/rhcsa_journal/lab-00b/task2/evidence.txt
grep -q 'idempotence proven' "${T2_EVIDENCE}" \
    && echo "✅ T00-E — idempotence line present in 00b task2" \
    || echo "❌ T00-E FAIL — re-run 00b Task 2" \
    | tee -a $TASKLOG

echo "═══ Part F: cross-check ping AS 00c USER ═══"                    | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c 'cd ~ && ansible -m ping localhost' \
                                                                      2>&1 | tee -a $TASKLOG \
    | grep -q 'pong' \
    && echo "✅ ping pong from fresh ${USER} works" \
    || echo "❌ fresh user cannot ping localhost" \
    | tee -a $TASKLOG

echo "exit was: $?"
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| Trap-by-trap audit | Each Part verifies one specific failure mode from 00a/00b |
| Fresh-user ping | Tier B audit: a brand-new user (00c's USER) can ping localhost because the `.ansible.cfg` pattern is reproducible |
| **🪤 Trap Risk T44** | Closeout audit must show four `✅` |

### Journal write

```bash
LAB=lab-00c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab00c/task1.txt "$JDIR/evidence.txt"

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
TOPIC:    Audit 00a+00b artifacts; T00-A/B/C/D/E rehearsed; fresh-user ping works
COMMANDS: rpm -q, ansible-galaxy collection list, grep, sudo -u USER -H ansible
TRAPS:    T00-A/B/C/D/E audited
NEXT:     task2 — restart-survive simulation + reboot reasoning (T41/T42)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab00c/warmup.txt /tmp/lab00c/task1.txt
echo "exit was: $?"
```

> **STOP — paste five `✅` lines (Parts A–F) before Task 2.**

---

## Task 2 — Restart-survive simulation + reboot reasoning (T41 / T42)

### 🔁 Warm-Up

```bash
df -h /tmp /root | tail -n 2                                          2>&1 | tee /tmp/lab00c/warmup2.txt
findmnt /tmp 2>/dev/null || echo "/tmp not separately mounted"
sha256sum /root/.ansible.cfg /root/inventory
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. Snapshot `/root/.ansible.cfg` + `/root/inventory` (sha256 + perms).
2. Simulate destruction of the `${USER}`'s sandbox.
3. Re-derive the `${USER}` config from the journal copies and re-ping.
4. Verbalize what survives a reboot vs what does not.

### Main command block

```bash
TASKLOG=/tmp/lab00c/task2.txt

echo "═══ Part A: snapshot system configs ═══"            2>&1 | tee $TASKLOG
sha256sum /root/.ansible.cfg /root/inventory             | tee -a $TASKLOG
stat -c '%U:%G %a %n' /root/.ansible.cfg /root/inventory | tee -a $TASKLOG

echo "═══ Part B: simulate destroy of USER sandbox ═══"   | tee -a $TASKLOG
rm -rf "${USER_HOME}"
test ! -d "${USER_HOME}" \
    && echo "✅ USER home destroyed" \
    || echo "❌ destroy failed" \
    | tee -a $TASKLOG

echo "═══ Part C: rebuild USER config from journal ═══"   | tee -a $TASKLOG
mkdir -p "${USER_HOME}"
# Use the 00a task2 journal as the source of truth
cp /root/rhcsa_journal/lab-00a/task2/user.ansible.cfg "${USER_HOME}/.ansible.cfg" 2>/dev/null \
    || cat > "${USER_HOME}/.ansible.cfg" <<'EOF'
[defaults]
inventory       = ~/inventory
host_key_checking = False
stdout_callback = yaml
EOF
cp /root/rhcsa_journal/lab-00a/task2/user.inventory "${USER_HOME}/inventory" 2>/dev/null \
    || echo "localhost ansible_connection=local" > "${USER_HOME}/inventory"
chown -R "${USER}:${GROUP}" "${USER_HOME}"
ls -la "${USER_HOME}"                                    | tee -a $TASKLOG

echo "═══ Part D: re-ping AS ${USER} after rebuild ═══"   | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c 'cd ~ && ansible -m ping localhost' \
                                                         2>&1 | tee -a $TASKLOG
grep -q 'pong' "$TASKLOG" \
    && echo "✅ T41 — destroy-rebuild-ping cycle worked" \
    || echo "❌ T41 — rebuild did not restore working state" \
    | tee -a $TASKLOG

echo "═══ Part E: reboot-survives reasoning (T42) ═══"    | tee -a $TASKLOG
cat <<'NOTES' | tee -a $TASKLOG
SURVIVES A REBOOT:
  /usr/bin/ansible*               (RPM database, /usr is on root FS)
  /usr/share/ansible/collections/ (system-wide collections, persistent)
  /root/.ansible.cfg              (root home, persistent)
  /root/inventory                 (root home, persistent)
  /root/rhcsa_journal/            (root home, persistent — our evidence)

DOES NOT SURVIVE A REBOOT:
  /tmp/lab00*/                    (tmpfs, cleared on boot)
  /tmp/lab00c/home_${USER}/       (sandbox path under /tmp)

REBUILD ON BOOT:
  - Run Lab 00a Lab-Wide Setup again to rebuild ${USER} + sandbox
  - System-level configs already survived; Tier B configs need re-creation
NOTES

echo "exit was: $?"
```

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| ansible-core | `rpm -q ansible-core` | RPM survives reboot |
| collections | `ansible-galaxy collection list` | Files in `/usr/share/ansible/collections` |
| root config | `test -s /root/.ansible.cfg` | `/root/` survives reboot |
| User config rebuildable | `${USER_HOME}/.ansible.cfg` exists post-rebuild | Tier B reproducible from journal |

### Journal write

```bash
LAB=lab-00c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab00c/task2.txt "$JDIR/evidence.txt"

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
TOPIC:    Destroy-rebuild USER config; re-ping; reboot reasoning
COMMANDS: rm -rf, cp from journal, sudo -u USER -H ansible
TRAPS:    T41 rehearsed; T42 verbalized
PERSISTENCE: ansible-core, collections, root configs survive; /tmp does not
NEXT:     Lab 05a — Directory Navigation
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task)

```bash
rm -f /tmp/lab00c/warmup2.txt /tmp/lab00c/task2.txt
echo "exit was: $?"
```

> **STOP — paste the T41 `✅` line and the T42 reasoning block before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e
awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 00c cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
rpm -q ansible-core >/dev/null      && echo "✅ ansible-core preserved (system)" || echo "❌ ansible-core missing"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste four `✅` lines. Lab 00 trilogy complete; controller is RHCE-ready.**

---

## Lab 00c Checklist (2 tasks + closeout)

- [ ] Task 1 — five `✅` for T00-A/B/C/D/E + fresh-user ping
- [ ] Task 2 — destroy-rebuild restored ping; T42 reasoning recorded
- [ ] Lab Closeout — four `✅`

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
