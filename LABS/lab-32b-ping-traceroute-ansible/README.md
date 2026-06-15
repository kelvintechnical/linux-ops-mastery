# Lab 32b: Check Network Connectivity (Ansible) — reachability in plays

**Series:** linux-ops-mastery — Networking · **Lab 32b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (connectivity gates and waits), RHCSA EX200 (the `ping` behavior underneath), SRE (pre-flight reachability checks)  
**Prerequisite:** [Lab 32a](../lab-32a-ping-traceroute-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ping -c` reachability | _Task 1 · Step 1_ |
| A2 | `changed_when: false` for checks | _Task 1 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.ping` (control check) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `command: ping -c` (ICMP check) | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.builtin.wait_for` (port) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `ansible.builtin.uri` (HTTP check) | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Gate plays on connectivity. You'll learn the crucial distinction between `ansible.builtin.ping` (which tests the *Ansible* connection, not ICMP) and a real ICMP `command: ping -c`, then use `wait_for` to block until a TCP port is open and `uri` to confirm an HTTP endpoint answers. These are the reachability checks that make automation robust.

---

## 🧠 Concept

A common trap: `ansible.builtin.ping` does **not** send ICMP — it verifies Ansible can reach and run Python on the host (a connection test). To test actual ICMP reachability of *another* address, shell out: `command: ping -c2 -W2 TARGET` with `changed_when: false` and exit-code handling. For service-level readiness, `ansible.builtin.wait_for` blocks until a TCP `port` is accepting connections (or a timeout), and `ansible.builtin.uri` performs an HTTP request and can assert on `status`. The right tool depends on the layer: connection (`ping` module), ICMP (`command: ping`), TCP (`wait_for`), HTTP (`uri`).

```
ansible.builtin.ping              → "can Ansible run on this host?" (NOT ICMP)
command: ping -c2 -W2 127.0.0.1   → real ICMP reachability (changed_when:false)
wait_for: port=22 timeout=10      → block until TCP port is open
uri: url=http://127.0.0.1 status_code=200 → HTTP endpoint check
```

> **Why this matters:** Plays that assume a host/service is up before configuring it fail messily. The right reachability gate at the right layer — and knowing the `ping` module isn't ICMP — prevents flaky automation.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.ping` | Connection (not ICMP) | reachability of the node |
| `command: ping -c` | ICMP to a target | `changed_when: false` |
| `ansible.builtin.wait_for` | Block on TCP port | `port:`, `timeout:` |
| `ansible.builtin.uri` | HTTP check | `status_code:` |
| `failed_when:` | Handle ping rc | `rc not in [0,1]` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder for connectivity checks.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-32
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-32b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Connection vs ICMP

**In plain English:** We confirm the node is manageable, then test real ICMP reachability.

---

### Step 1 of 2 — Write the connectivity playbook

**In plain English:** We create `task1.yml`, which uses the `ping` module (connection) and a real ICMP `command: ping`.

```yaml
---
- name: "Lab 32b Task 1 — connection vs ICMP"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Connection check (NOT ICMP)"
      ansible.builtin.ping:
      register: conn

    - name: "Real ICMP reachability to loopback"
      ansible.builtin.command: "ping -c2 -W2 127.0.0.1"
      register: icmp
      changed_when: false
      failed_when: icmp.rc != 0

    - name: "Report both checks"
      ansible.builtin.debug:
        msg:
          - "ansible ping: {{ conn.ping | default('n/a') }}"
          - "icmp loss line: {{ icmp.stdout_lines | select('search','packet loss') | first }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.ping:` → Returns `pong` if Ansible can run on the host — a *connection* test, not ICMP.
- `command: ping -c2 -W2 127.0.0.1` → Real ICMP check; `failed_when: rc != 0` makes unreachable a failure.
- `select('search','packet loss') | first` → Pull the loss summary line.

**New words in this step:**

- **`ansible.builtin.ping`** — verifies the Ansible connection (not ICMP).

---

### Step 2 of 2 — Run it and read both checks

**In plain English:** We run the play and confirm connection + ICMP both pass.

```bash
ansible-playbook /root/rhcsa_journal/lab-32b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report both checks] ***********************************************
ok: [localhost] => {
    "msg": ["ansible ping: pong",
            "icmp loss line: 2 packets transmitted, 2 received, 0% packet loss, ..."]
}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → `pong` proves manageability; the loss line proves ICMP works; `changed=0` since both are checks.

**New words in this step:**

- **layered check** — testing connection and ICMP separately.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ping` module | connection test | NOT ICMP |
| `command: ping` | real ICMP | `changed_when: false` |
| `failed_when` | gate on rc | unreachable = fail |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Expected ICMP from module | Misunderstanding | Use `command: ping` |
| Task fails | Target unreachable | Check the address/firewall |

---

## TASK 2 of 2 — Port and HTTP readiness

**In plain English:** We block until a port is open, then check an HTTP endpoint.

---

### Step 1 of 2 — Write the readiness playbook

**In plain English:** We create `task2.yml`, which waits for the SSH port and checks an HTTP URL (gracefully).

```yaml
---
- name: "Lab 32b Task 2 — port and HTTP readiness"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Wait for the SSH port to be open"
      ansible.builtin.wait_for:
        host: 127.0.0.1
        port: 22
        timeout: 5
        state: started
      register: portcheck
      failed_when: false

    - name: "Report the port result"
      ansible.builtin.debug:
        msg: "port 22 reachable: {{ portcheck is succeeded }}"

    - name: "Check an HTTP endpoint (if a server is running)"
      ansible.builtin.uri:
        url: "http://127.0.0.1/"
        status_code: 200
        timeout: 3
      register: web
      failed_when: false

    - name: "Report the HTTP result"
      ansible.builtin.debug:
        msg: "http status: {{ web.status | default('no server') }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `wait_for: port: 22 timeout: 5` → Block up to 5s until TCP port 22 accepts connections.
- `uri: url: ... status_code: 200` → HTTP request; `failed_when: false` keeps the play green whether or not a web server is up.

**New words in this step:**

- **`wait_for`** — block until a TCP port (or file/condition) is ready.
- **`uri`** — make an HTTP request and check the status.

---

### Step 2 of 2 — Run it and read readiness

**In plain English:** We run the play and read the port and HTTP results.

```bash
ansible-playbook /root/rhcsa_journal/lab-32b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report the port result] *******************************************
ok: [localhost] => {"msg": "port 22 reachable: True"}
TASK [Report the HTTP result] *******************************************
ok: [localhost] => {"msg": "http status: no server"}
PLAY RECAP **********************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Reports port reachability and HTTP status; both gracefully handled, `changed=0`.

**New words in this step:**

- **readiness gate** — waiting for a service to be up before proceeding.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `wait_for` | TCP/port wait | set a `timeout:` |
| `uri` | HTTP check | `status_code:` |
| `failed_when: false` | graceful | check, don't abort |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `wait_for` times out | Port closed/firewalled | Open the port / check service |
| `uri` fails | No web server | Expected; `failed_when: false` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the connectivity playbook
- [ ] Task 1 · Step 2 — Run it and read both checks
- [ ] Task 2 · Step 1 — Write the readiness playbook
- [ ] Task 2 · Step 2 — Run it and read readiness
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-32
rm -rf /root/rhcsa_journal/lab-32b
```

**Expected output:**

```
✅ Removed /tmp/lab-32 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Thinking `ping` module = ICMP | Wrong check | Use `command: ping` for ICMP |
| `wait_for` with no timeout | Play hangs | Always set `timeout:` |
| `uri` aborts the play | No server | `failed_when: false` to probe |

---

## 📌 Exam Strategy

Pick the reachability tool by layer: `ping` module for manageability, `command: ping` for ICMP, `wait_for` for TCP ports, `uri` for HTTP. The classic trap is expecting ICMP from `ansible.builtin.ping` — it's a connection test.

- `ansible.builtin.ping` ≠ ICMP.
- `wait_for` to gate on a service port (always with `timeout:`).
- `uri` + `status_code` for HTTP health.

---

## 🔗 Related Labs

- [Lab 32a — Check Network Connectivity (RHCSA)](../lab-32a-ping-traceroute-rhcsa/) — the `ping`/`traceroute` this builds on
- [Lab 32c — Check Network Connectivity (Verify)](../lab-32c-ping-traceroute-verify/) — prove loss/latency thresholds
- [Lab 34b — Inspecting Listening Sockets (Ansible)](../lab-34b-ss-listening-sockets-ansible/) — port-state checks

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
