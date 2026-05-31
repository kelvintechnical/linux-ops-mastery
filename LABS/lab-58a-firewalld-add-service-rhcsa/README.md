# Lab 58a: Adding Services to firewalld Zones (RHCSA) - `--add-service`, `--remove-service`, `--permanent`, `--reload`

- **Series:** linux-ops-mastery - Security Administration (firewalld)
- **Trilogy:** `58a` (RHCSA hand-typed) -> [`58b`](../lab-58b-firewalld-add-service-ansible/) (Ansible) -> [`58c`](../lab-58c-firewalld-add-service-verify/) (Verify)
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2
- **Practice Directory (objective context):** `/lib` (inspection context), `/tmp/lab58a` (write target)
- **Sandbox (Tier B):** `/tmp/lab58a` with `USER=labuser_58_fwsvc`, `GROUP=labgrp_58_fwsvc`
- **Traps rehearsed:** **T58-A** (no `--permanent` means runtime-only, lost on reload) · **T58-B** (`--reload` syncs runtime to permanent) · **T41** (destroy-restore belongs in verify) · **T44** (cleanup audit)

> **Service definition source:** predefined services live in `/usr/lib/firewalld/services/` as XML profiles.

---

## LAB HEADER BLOCK

```bash
echo "📁 PRACTICE DIR: /lib (inspect), /tmp/lab58a (write)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "🕒 TIME: $(date -Is)"
echo "⚠️ TRAPS: T58-A T58-B T41 T44"
command -v firewall-cmd
systemctl is-active firewalld
ls -ld /lib /tmp
ls /usr/lib/firewalld/services | head -n 10
```

---

## Objective

1. Add and remove a predefined service (`http`) from a firewalld zone correctly.
2. Use `--permanent` with `--reload` so changes persist.
3. Demonstrate and explain runtime-only loss on reload (T58-A).

---

## Lab-Wide Setup - Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab58a
export GROUP=labgrp_58_fwsvc
export USER=labuser_58_fwsvc
export USER_HOME=${SANDBOX}/home_${USER}
export ZONE=public

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-58a/task1
mkdir -p /root/rhcsa_journal/lab-58a/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

# Capture original services once for restore and audits.
sudo firewall-cmd --zone="${ZONE}" --list-services | xargs > "${SANDBOX}/original-services.txt"
cat "${SANDBOX}/original-services.txt"
```

---

## Task 1 - Capture baseline, add `http` permanently, reload, verify

### Purpose

Perform the production-safe sequence for service addition: baseline capture -> permanent change -> reload -> verify.

### Main command block

```bash
TASKLOG=/tmp/lab58a/task1.txt

echo "== original services (${ZONE}) ==" | tee "${TASKLOG}"
cat /tmp/lab58a/original-services.txt | tee -a "${TASKLOG}"

echo "== add http permanently ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --zone="${ZONE}" --add-service=http | tee -a "${TASKLOG}"

echo "== reload (T58-B sync runtime<-permanent) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --reload | tee -a "${TASKLOG}"

echo "== verify list-services ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Journal write

```bash
cp /tmp/lab58a/task1.txt /root/rhcsa_journal/lab-58a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-58a/task1/done.txt <<EOF
LAB: lab-58a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Revert with `--remove-service`, then prove T58-A runtime loss

### Purpose

Revert the permanent change cleanly, then intentionally trigger the runtime-only trap and prove reload removes it.

### Main command block

```bash
TASKLOG=/tmp/lab58a/task2.txt

echo "== remove http permanently and reload (revert) ==" | tee "${TASKLOG}"
sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service=http | tee -a "${TASKLOG}" || true
sudo firewall-cmd --reload | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services | tee -a "${TASKLOG}"

echo "== T58-A demo: add without --permanent ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --add-service=http | tee -a "${TASKLOG}"
echo "runtime after add (contains http):" | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services | tee -a "${TASKLOG}"

echo "reload now (runtime reverts to permanent):" | tee -a "${TASKLOG}"
sudo firewall-cmd --reload | tee -a "${TASKLOG}"
echo "after reload (http is gone unless permanent had it):" | tee -a "${TASKLOG}"
sudo firewall-cmd --zone="${ZONE}" --list-services | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callout

- **T58-A:** `--add-service=http` without `--permanent` edits runtime only.
- **T58-B:** `--reload` discards runtime deltas and reloads permanent config.

### Journal write

```bash
cp /tmp/lab58a/task2.txt /root/rhcsa_journal/lab-58a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-58a/task2/done.txt <<EOF
LAB: lab-58a
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Section 6 Teardown (restore original services first)

```bash
set +e

# 1) Restore permanent services in zone back to setup baseline.
ORIG="$(cat "${SANDBOX}/original-services.txt" 2>/dev/null)"
CURR="$(sudo firewall-cmd --permanent --zone="${ZONE}" --list-services 2>/dev/null)"

for svc in ${CURR}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --remove-service="${svc}" >/dev/null 2>&1 || true
done
for svc in ${ORIG}; do
  sudo firewall-cmd --permanent --zone="${ZONE}" --add-service="${svc}" >/dev/null 2>&1 || true
done
sudo firewall-cmd --reload >/dev/null 2>&1 || true

# 2) Tier B teardown.
userdel -r "${USER}" 2>/dev/null
groupdel "${GROUP}" 2>/dev/null
rm -rf "${SANDBOX}"

# 3) Audits.
echo "── Lab 58a cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
echo "firewalld ${ZONE} services after restore:"
sudo firewall-cmd --zone="${ZONE}" --list-services

set -e
```

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
