# Lab 60a: Inspect Active Firewall Zones (RHCSA) — `firewall-cmd` active/runtime/permanent

- **Series:** linux-ops-mastery — Network Security and Service Access
- **Trilogy:** `60a` (RHCSA hand-typed) -> [`60b`](../lab-60b-firewalld-active-zones-ansible/) (Ansible) -> [`60c`](../lab-60c-firewalld-active-zones-verify/) (Verify)
- **Topic:** Active-zone inspection with interface context and runtime/permanent contrast
- **Distinct from Lab 56:** Lab 56 focused broad zone inspection; Lab 60 centers on **active zones with interfaces** and proving **runtime vs permanent divergence** before reload.
- **Time Estimate:** 25-35 minutes
- **Tasks:** 2 (ADHD format)
- **Practice Directory:** `/usr` (inspection context)
- **Sandbox (Tier B):** `/tmp/lab60a`, `USER=labuser_60_fwactive`, `GROUP=labgrp_60_fwactive`
- **Traps rehearsed this lab:** **T60-A** (`--list-all-zones` is huge; always scope output with `less`, `head`, or `--info-zone`) · **T60-B** (runtime can differ from permanent until `--reload`; capture both) · **T41** · **T44**

> Read-only inspection only. This lab does not change firewalld rules, zones, or service access.

---

## LAB HEADER BLOCK

```bash
echo "OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "TIME:  $(date -Is)"
echo "USER:  $(whoami)@$(hostname)"
echo "PRACTICE DIR: /usr"
echo "TRAPS: T60-A T60-B T41 T44"
systemctl is-active firewalld 2>/dev/null || echo "firewalld inactive"
firewall-cmd --state 2>/dev/null || true
ls -ld /usr
```

> STOP - paste header output before setup.

---

## Objective

1. Read active zones and interface bindings with `--get-active-zones`.
2. Compare runtime and permanent zone metadata for the same zone.
3. Safely sample all zones output without flooding terminal context.
4. Build reflex for audit-first firewall diagnostics without mutation.

---

## Lab-Wide Setup (Tier B)

```bash
sudo -i

export SANDBOX=/tmp/lab60a
export GROUP=labgrp_60_fwactive
export USER=labuser_60_fwactive
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-60a/task1 /root/rhcsa_journal/lab-60a/task2
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}"
```

> STOP - paste `id` and both `ls -ld` lines before Task 1.

---

## Task 1 - Inspect active zones and compare runtime/permanent (`public`)

### Purpose

Capture active-zone interface state, then compare `public` zone runtime vs permanent view to expose T60-B safely.

### Main command block

```bash
TASKLOG=/tmp/lab60a/task1.txt

echo "== active zones (runtime) ==" | tee "${TASKLOG}"
sudo firewall-cmd --get-active-zones | tee -a "${TASKLOG}"

echo "== public zone runtime info ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --info-zone=public | tee -a "${TASKLOG}"

echo "== public zone permanent info ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --info-zone=public | tee -a "${TASKLOG}"

echo "== default zone ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --get-default-zone | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Expected verification

- `--get-active-zones` shows zone names and attached interfaces.
- Runtime and permanent `public` output may match or may differ (both outcomes are valid; evidence matters).
- Journal evidence contains both runtime and permanent snapshots for compare.

### Journal write

```bash
cp /tmp/lab60a/task1.txt /root/rhcsa_journal/lab-60a/task1/evidence.txt
cat > /root/rhcsa_journal/lab-60a/task1/done.txt <<EOF
LAB: lab-60a
TASK: task1
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Task 2 - Scope large zone output (`--list-all-zones`) and contrast runtime/permanent

### Purpose

Practice safe output scoping for huge zone listings (T60-A) while capturing runtime/permanent contrast for all zones (T60-B).

### Main command block

```bash
TASKLOG=/tmp/lab60a/task2.txt

echo "== scoped all-zones runtime (first lines only) ==" | tee "${TASKLOG}"
sudo firewall-cmd --list-all-zones | head -n 40 | tee -a "${TASKLOG}"

echo "== scoped all-zones permanent (first lines only) ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --list-all-zones | head -n 40 | tee -a "${TASKLOG}"

echo "== focused runtime view for default zone ==" | tee -a "${TASKLOG}"
DEF_ZONE="$(sudo firewall-cmd --get-default-zone)"
sudo firewall-cmd --info-zone="${DEF_ZONE}" | tee -a "${TASKLOG}"

echo "== focused permanent view for default zone ==" | tee -a "${TASKLOG}"
sudo firewall-cmd --permanent --info-zone="${DEF_ZONE}" | tee -a "${TASKLOG}"

echo "exit was: $?"
```

### Trap callouts

- **T60-A:** Never dump full `--list-all-zones` blindly; use `head`, `less`, or zone-specific info.
- **T60-B:** Runtime and permanent may diverge until `firewall-cmd --reload` (do not reload in this lab; audit only).

### Journal write

```bash
cp /tmp/lab60a/task2.txt /root/rhcsa_journal/lab-60a/task2/evidence.txt
cat > /root/rhcsa_journal/lab-60a/task2/done.txt <<EOF
LAB: lab-60a
TASK: task2
DATE: $(date -Is)
STATUS: COMPLETE
EOF
```

---

## Lab Closeout - Section 6 Teardown

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi
rm -rf "${SANDBOX}"

echo "-- lab-60a cleanup audit --"
getent passwd "${USER}" >/dev/null && echo "FAIL user remains" || echo "OK user gone"
getent group  "${GROUP}" >/dev/null && echo "FAIL group remains" || echo "OK group gone"
test -d "${SANDBOX}" && echo "FAIL sandbox remains" || echo "OK sandbox gone"
test -d "${USER_HOME}" && echo "FAIL home remains" || echo "OK home gone"

set -e
```

---

## Checklist

- [ ] Task 1: captured `--get-active-zones`, runtime `--info-zone=public`, permanent `--permanent --info-zone=public`
- [ ] Task 2: captured scoped runtime/permanent `--list-all-zones` and focused default-zone runtime/permanent info
- [ ] T60-A and T60-B behavior documented in evidence
- [ ] Section 6 closeout audit returned all `OK`

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
