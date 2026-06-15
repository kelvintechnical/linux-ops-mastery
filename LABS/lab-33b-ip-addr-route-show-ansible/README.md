# Lab 33b: Display IP and Routing Info (Ansible) — network facts

**Series:** linux-ops-mastery — Networking · **Lab 33b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (facts & conditionals), RHCSA EX200 (the `ip` data underneath), SRE (inventory of network state)  
**Prerequisite:** [Lab 33a](../lab-33a-ip-addr-route-show-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `gather_facts` | _Task 1 · Step 1_ |
| A2 | `command: ip` (read-only) | _Task 2 · Step 1_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible_default_ipv4` fact | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible_interfaces` / `hostvars` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `command: ip -j` (JSON) | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `from_json` parsing | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Read network state the Ansible way. You'll use gathered facts (`ansible_default_ipv4`, `ansible_interfaces`) to discover addresses and the gateway without parsing text, then capture `ip -j` JSON and parse it with `from_json` for fine-grained data. Facts first, raw `ip` only when facts don't cover what you need.

---

## 🧠 Concept

When Ansible gathers facts it inspects the network and exposes structured data: `ansible_default_ipv4.address` (primary IP), `ansible_default_ipv4.gateway` (default gateway), `ansible_default_ipv4.interface` (egress device), and `ansible_interfaces` (list of NICs). Per-interface details live in `ansible_<name>` (e.g. `ansible_lo`). This beats scraping `ip` output. When you need something facts don't expose, modern `ip` supports `-j` for **JSON** output — capture it with `command` (`changed_when: false`) and parse with the `from_json` filter into real data structures. Principle: prefer facts; fall back to `ip -j | from_json`; avoid brittle text scraping.

```
gather_facts: true              → populates ansible_* network facts
ansible_default_ipv4.address    → primary IPv4
ansible_default_ipv4.gateway    → default gateway
ip -j addr show lo | from_json  → structured per-interface data
```

> **Why this matters:** Reliable automation keys off structured data, not fragile regexes against `ip` text. Facts and `-j` JSON give you stable fields you can assert on.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `gather_facts: true` | Populate facts | network facts included |
| `ansible_default_ipv4` | Primary IP/gw | `.address`, `.gateway` |
| `ansible_interfaces` | NIC list | array of names |
| `command: ip -j` | JSON output | `changed_when: false` |
| `from_json` | Parse JSON | text → data |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox and playbook folder.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-33
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-33b/playbooks
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Read network facts

**In plain English:** We gather facts and report the primary address, gateway, and interfaces.

---

### Step 1 of 2 — Write the facts playbook

**In plain English:** We create `task1.yml`, which gathers facts and prints the default IPv4 details.

```yaml
---
- name: "Lab 33b Task 1 — network facts"
  hosts: localhost
  connection: local
  gather_facts: true
  tasks:
    - name: "Report the default IPv4 details"
      ansible.builtin.debug:
        msg:
          - "address: {{ ansible_default_ipv4.address | default('none') }}"
          - "gateway: {{ ansible_default_ipv4.gateway | default('none') }}"
          - "interface: {{ ansible_default_ipv4.interface | default('none') }}"

    - name: "List all interfaces"
      ansible.builtin.debug:
        var: ansible_interfaces
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `gather_facts: true` → Populates the `ansible_*` network facts before tasks run.
- `ansible_default_ipv4.address/.gateway` → The primary IP and gateway, no text parsing needed.
- `default('none')` → Safe fallback on hosts without a default route.

**New words in this step:**

- **`ansible_default_ipv4`** — fact holding the primary IPv4 address, gateway, and egress interface.

---

### Step 2 of 2 — Run it and read the facts

**In plain English:** We run the play and confirm the facts populate.

```bash
ansible-playbook /root/rhcsa_journal/lab-33b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report the default IPv4 details] **********************************
ok: [localhost] => {"msg": ["address: 192.168.x.x", "gateway: 192.168.x.1", "interface: eth0"]}
TASK [List all interfaces] *********************************************
ok: [localhost] => {"ansible_interfaces": ["lo", "eth0"]}
PLAY RECAP **********************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Facts report the address/gateway/interface and the NIC list; `changed=0` (read-only).

**New words in this step:**

- **`ansible_interfaces`** — the list of network interface names on the host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| facts | structured network data | needs `gather_facts` |
| `default_ipv4` | primary IP/gw | `.address`/`.gateway` |
| `default()` | safe fallback | no default route |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Undefined fact | `gather_facts: false` | Enable fact gathering |
| Empty `default_ipv4` | No default route | Expected on isolated hosts |

---

## TASK 2 of 2 — Parse `ip -j` JSON

**In plain English:** We capture `ip` JSON and parse it into real data.

---

### Step 1 of 2 — Write the JSON-parsing playbook

**In plain English:** We create `task2.yml`, capturing `ip -j addr show lo` and parsing it with `from_json`.

```yaml
---
- name: "Lab 33b Task 2 — parse ip JSON"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Capture loopback addressing as JSON"
      ansible.builtin.command: "ip -j addr show dev lo"
      register: ipjson
      changed_when: false

    - name: "Parse the JSON into a fact"
      ansible.builtin.set_fact:
        lo_data: "{{ ipjson.stdout | from_json }}"

    - name: "Extract the IPv4 address from the structure"
      ansible.builtin.set_fact:
        lo_v4: "{{ lo_data[0].addr_info | selectattr('family','equalto','inet') | map(attribute='local') | first }}"

    - name: "Report and assert loopback is 127.0.0.1"
      ansible.builtin.assert:
        that:
          - "lo_v4 == '127.0.0.1'"
        success_msg: "loopback IPv4 is {{ lo_v4 }}"
        fail_msg: "unexpected loopback address: {{ lo_v4 }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ip -j addr show dev lo` → Machine-readable JSON instead of human text; `changed_when: false` (read-only).
- `from_json` → Turns the JSON string into a list/dict you can index.
- `selectattr('family','equalto','inet') | map(attribute='local')` → Pick the IPv4 entry and its address.

**New words in this step:**

- **`ip -j`** — emit JSON; **`from_json`** — parse it into Ansible data.

---

### Step 2 of 2 — Run it and confirm the assertion

**In plain English:** We run the play and confirm the parsed address asserts true.

```bash
ansible-playbook /root/rhcsa_journal/lab-33b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report and assert loopback is 127.0.0.1] *************************
ok: [localhost] => {"changed": false, "msg": "loopback IPv4 is 127.0.0.1"}
PLAY RECAP **********************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → The assertion passes, proving the JSON parse produced the expected address.

**New words in this step:**

- **structured parse** — extracting a field from JSON rather than scraping text.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ip -j` | JSON output | `changed_when: false` |
| `from_json` | parse | needs valid JSON |
| `selectattr` | filter list | match exact family |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `from_json` error | Non-JSON output | Ensure `-j` flag |
| Empty `lo_v4` | Wrong filter | Check `family`/`local` keys |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the facts playbook
- [ ] Task 1 · Step 2 — Run it and read the facts
- [ ] Task 2 · Step 1 — Write the JSON-parsing playbook
- [ ] Task 2 · Step 2 — Run it and confirm the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. This lab changed **no** system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-33
rm -rf /root/rhcsa_journal/lab-33b
```

**Expected output:**

```
✅ Removed /tmp/lab-33 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Scraping `ip` text | Brittle | Use facts or `ip -j` |
| Forgetting `gather_facts` | Undefined facts | Enable it |
| Missing `changed_when` | False "changed" | `changed_when: false` |

---

## 📌 Exam Strategy

Prefer facts (`ansible_default_ipv4`, `ansible_interfaces`) for network state; drop to `ip -j | from_json` for details facts don't expose. Always mark read-only `command` tasks `changed_when: false`.

- Facts give address, gateway, interface for free.
- `ip -j` + `from_json` = reliable structured parse.
- Never scrape human `ip` text in production plays.

---

## 🔗 Related Labs

- [Lab 33a — Display IP and Routing Info (RHCSA)](../lab-33a-ip-addr-route-show-rhcsa/) — the `ip` commands these facts mirror
- [Lab 33c — Display IP and Routing Info (Verify)](../lab-33c-ip-addr-route-show-verify/) — prove addresses and routes
- [Lab 31b — Configure a Static IP (Ansible)](../lab-31b-static-ip-nmcli-ansible/) — setting the state you read here

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
