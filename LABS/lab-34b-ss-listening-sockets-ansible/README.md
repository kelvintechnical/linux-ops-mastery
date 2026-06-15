# Lab 34b: Inspecting Listening Sockets (Ansible) — port-state checks

**Series:** linux-ops-mastery — Networking · **Lab 34b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (service verification), RHCSA EX200 (the `ss` data underneath), SRE (automated port audits)  
**Prerequisite:** [Lab 34a](../lab-34a-ss-listening-sockets-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `command:` + `changed_when: false` | _Task 1 · Step 1_ |
| A2 | `ansible.builtin.assert` | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `command: ss -tuln` (capture) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `select('search', ...)` on sockets | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.builtin.wait_for` (port) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `getent services` / port→name | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Audit listening ports from a play. You'll capture `ss -tuln` output and assert that an expected port (e.g. SSH/22) is listening, then use `ansible.builtin.wait_for` to actively probe a TCP port's state. These checks let automation confirm services are bound before depending on them.

---

## 🧠 Concept

There is no core "socket facts" module, so the idiomatic pattern is `command: ss -tuln` with `changed_when: false` (read-only), then reason over `stdout_lines` with Jinja: `select('search', ':22 ')` to test for a listening port. For an active probe, `ansible.builtin.wait_for` opens a TCP connection to `host`/`port` and either confirms it's `started` or times out — this works even for remote hosts and doesn't depend on parsing `ss`. Use `ss` parsing to inventory what *this* host is listening on; use `wait_for` to confirm reachability/readiness of a specific port. Both belong in pre-flight checks before configuring dependent services.

```
command: ss -tuln            → capture listeners (changed_when:false)
stdout_lines | select('search', ':22 ')  → is SSH listening?
wait_for: port=22 state=started timeout=5 → active TCP probe
```

> **Why this matters:** Automation that assumes a service is up before talking to it is fragile. Asserting the port listens (or actively waiting for it) makes plays reliable and self-documenting.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `command: ss -tuln` | Capture listeners | `changed_when: false` |
| `select('search', ...)` | Filter lines | regex on stdout |
| `wait_for` | Active port probe | `port:`, `timeout:`, `state:` |
| `assert` | Pass/fail | `that:` conditions |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-34
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-34b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Capture and assert a listening port

**In plain English:** We capture `ss` output and assert SSH is listening.

---

### Step 1 of 2 — Write the capture-and-assert playbook

**In plain English:** We create `task1.yml`, capturing `ss -tuln` and asserting port 22 appears.

```yaml
---
- name: "Lab 34b Task 1 — assert a port is listening"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Capture listening sockets"
      ansible.builtin.command: "ss -tuln"
      register: sockets
      changed_when: false

    - name: "Report the listening lines"
      ansible.builtin.debug:
        var: sockets.stdout_lines

    - name: "Assert SSH (port 22) is listening"
      ansible.builtin.assert:
        that:
          - "sockets.stdout_lines | select('search', ':22 ') | list | length > 0"
        success_msg: "port 22 is listening"
        fail_msg: "port 22 not found among listeners"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: ss -tuln` + `changed_when: false` → Capture listeners without reporting a change.
- `select('search', ':22 ')` → Keep only lines containing `:22 ` (the SSH listener).
- `assert ... length > 0` → Pass only if at least one such line exists.

**New words in this step:**

- **socket assertion** — proving a port is listening by filtering `ss` output.

---

### Step 2 of 2 — Run it and confirm

**In plain English:** We run the play and confirm the assertion passes.

```bash
ansible-playbook /root/rhcsa_journal/lab-34b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert SSH (port 22) is listening] *******************************
ok: [localhost] => {"changed": false, "msg": "port 22 is listening"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → The assertion confirms port 22 is listening; `changed=0` (read-only).

> If SSH isn't running on your box, the assert fails by design — start `sshd` or point the filter at a port you do run.

**New words in this step:**

- **read-only audit** — a play that inspects and asserts without changing state.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ss` capture | inventory listeners | `changed_when: false` |
| `select('search')` | filter lines | match `:22 ` exactly |
| `assert` | pass/fail | length test |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Assert fails | Service not running | Start it / change port |
| Matches wrong port | Loose pattern | Anchor the match |

---

## TASK 2 of 2 — Actively probe a port

**In plain English:** We use `wait_for` to actively test a TCP port.

---

### Step 1 of 2 — Write the active-probe playbook

**In plain English:** We create `task2.yml`, which probes port 22 and reports without aborting.

```yaml
---
- name: "Lab 34b Task 2 — active port probe"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Probe TCP port 22"
      ansible.builtin.wait_for:
        host: 127.0.0.1
        port: 22
        state: started
        timeout: 5
      register: probe
      failed_when: false

    - name: "Report the probe result"
      ansible.builtin.debug:
        msg: "port 22 open: {{ probe is succeeded }} (elapsed {{ probe.elapsed | default('n/a') }}s)"

    - name: "Probe a likely-closed port for contrast"
      ansible.builtin.wait_for:
        host: 127.0.0.1
        port: 9
        state: started
        timeout: 2
      register: closed
      failed_when: false

    - name: "Report the closed-port result"
      ansible.builtin.debug:
        msg: "port 9 open: {{ closed is succeeded }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `wait_for: port: 22 state: started timeout: 5` → Actively open a TCP connection; succeeds when the port accepts.
- `failed_when: false` → Turn the probe into a report instead of a hard failure.
- The second probe of port 9 contrasts a closed port (`succeeded` is false).

**New words in this step:**

- **active probe** — opening a real TCP connection to test a port (vs parsing `ss`).

---

### Step 2 of 2 — Run it and compare open vs closed

**In plain English:** We run the play and see one port open and one closed.

```bash
ansible-playbook /root/rhcsa_journal/lab-34b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report the probe result] *****************************************
ok: [localhost] => {"msg": "port 22 open: True (elapsed 0s)"}
TASK [Report the closed-port result] ***********************************
ok: [localhost] => {"msg": "port 9 open: False"}
PLAY RECAP **********************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Port 22 probes open, port 9 closed — `failed_when: false` keeps both as reports.

**New words in this step:**

- **probe contrast** — comparing an open and a closed port to validate the check.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `wait_for` | active TCP probe | always set `timeout:` |
| `state: started` | wait for open | vs `stopped` |
| `failed_when: false` | report mode | probe, don't abort |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Probe hangs | No timeout | Add `timeout:` |
| Always closed | Firewall/service | Check service + firewall |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the capture-and-assert playbook
- [ ] Task 1 · Step 2 — Run it and confirm
- [ ] Task 2 · Step 1 — Write the active-probe playbook
- [ ] Task 2 · Step 2 — Run it and compare open vs closed
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-34
rm -rf /root/rhcsa_journal/lab-34b
```

**Expected output:**

```
✅ Removed /tmp/lab-34 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Parsing without `changed_when` | False "changed" | `changed_when: false` |
| `wait_for` no timeout | Play hangs | Always set `timeout:` |
| Loose port match | Wrong assertion | Anchor `:22 ` pattern |

---

## 📌 Exam Strategy

Two complementary checks: parse `ss -tuln` to inventory local listeners and assert on them, or use `wait_for` to actively probe a port (local or remote). Mark `ss` captures `changed_when: false` and always give `wait_for` a `timeout:`.

- `command: ss -tuln` + `select('search')` + `assert` for local inventory.
- `wait_for` for an active, remote-capable probe.
- `failed_when: false` turns a probe into a graceful report.

---

## 🔗 Related Labs

- [Lab 34a — Inspecting Listening Sockets (RHCSA)](../lab-34a-ss-listening-sockets-rhcsa/) — the `ss` commands behind these checks
- [Lab 34c — Inspecting Listening Sockets (Verify)](../lab-34c-ss-listening-sockets-verify/) — prove a port is (not) listening
- [Lab 32b — Check Network Connectivity (Ansible)](../lab-32b-ping-traceroute-ansible/) — reachability gates that pair with port checks

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
