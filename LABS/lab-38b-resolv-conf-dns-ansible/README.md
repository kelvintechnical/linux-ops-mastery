# Lab 38b: Configuring DNS Servers (Ansible) — declarative resolver config

**Series:** linux-ops-mastery — Networking · **Lab 38b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (network module, DNS), RHCSA EX200 (the resolv.conf underneath), SRE (consistent resolver config fleet-wide)  
**Prerequisite:** [Lab 38a](../lab-38a-resolv-conf-dns-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `community.general.nmcli` (from Lab 36) | _Task 1 · Step 1_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `dns4` list via module | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `dns_search` via module | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | verify generated resolv.conf | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `assert` on nameserver | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Configure DNS declaratively and prove it lands in `/etc/resolv.conf`. You'll set `dns4` and `dns_search` on a dummy connection via `community.general.nmcli`, then verify that NetworkManager regenerated `/etc/resolv.conf` with the expected `nameserver`/`search` lines and assert on them. This is fleet-consistent resolver config with built-in verification.

> **Safety note:** All work targets the throwaway **dummy** profile `lab-dns` (on `dummy0`). Teardown removes it; your real resolver returns automatically.

---

## 🧠 Concept

Since NetworkManager generates `/etc/resolv.conf`, the Ansible-correct way to set DNS is the same as the CLI-correct way: configure the *connection*, not the file. `community.general.nmcli` exposes `dns4` (a list of servers) and `dns_search` (a list of search domains). Declaring them with `state: present` and activating makes NM rewrite `/etc/resolv.conf`. You then verify by reading the generated file (`command: cat /etc/resolv.conf`, `changed_when: false`) and asserting the expected `nameserver` appears. The mental model: **module sets the connection → NM regenerates resolv.conf → assert the file**. Idempotence applies — re-running yields `changed=0`. Never template `/etc/resolv.conf` directly on an NM-managed host; it will be overwritten.

```
community.general.nmcli:
  dns4: [10.88.88.53, 10.88.88.54]
  dns_search: [lab.local]
  state: present
→ NM regenerates /etc/resolv.conf
command: cat /etc/resolv.conf (changed_when: false) → verify
assert "'10.88.88.53' in resolv_contents"
```

> **Why this matters:** Templating `/etc/resolv.conf` directly is a common mistake that breaks on the next network event. Setting DNS on the connection via the module is durable, idempotent, and verifiable — the production-grade approach.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `community.general.nmcli` | Manage connection DNS | `dns4`, `dns_search` |
| `dns4` | DNS servers | YAML list |
| `dns_search` | Search domains | YAML list |
| `command: cat /etc/resolv.conf` | Verify output | `changed_when: false` |
| `ansible.builtin.assert` | Pass/fail | `that:` conditions |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, playbook folder, dummy module, and base profile.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-38
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-38b/playbooks
sudo modprobe dummy 2>/dev/null || true
sudo nmcli con add type dummy ifname dummy0 con-name lab-dns ipv4.method manual \
  ipv4.addresses 10.88.88.2/24 2>/dev/null
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Declare DNS on the connection

**In plain English:** We set DNS servers and a search domain declaratively.

---

### Step 1 of 2 — Write the DNS playbook

**In plain English:** We create `task1.yml` that sets `dns4` and `dns_search` on the dummy profile.

```yaml
---
- name: "Lab 38b Task 1 — declarative DNS config"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Set DNS servers and search domain on lab-dns"
      community.general.nmcli:
        conn_name: lab-dns
        ifname: dummy0
        type: dummy
        method4: manual
        ip4: 10.88.88.2/24
        dns4:
          - 10.88.88.53
          - 10.88.88.54
        dns_search:
          - lab.local
        state: present
      register: nm

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ nm.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `dns4: [...]` → The DNS server list, set exactly (declarative).
- `dns_search: [lab.local]` → The search domain(s) written to resolv.conf's `search` line.
- `state: present` → Reconcile the profile to this desired state.

**New words in this step:**

- **`dns4` / `dns_search`** — module parameters for resolver servers and search domains.

---

### Step 2 of 2 — Run, activate, and prove idempotence

**In plain English:** We apply the play, activate, and re-run for `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-38b/playbooks/task1.yml
sudo nmcli con up lab-dns >/dev/null
ansible-playbook /root/rhcsa_journal/lab-38b/playbooks/task1.yml | grep -E 'changed='
```

**Expected output:**

```
localhost                  : ok=2    changed=1    unreachable=0    failed=0
localhost                  : ok=2    changed=0    unreachable=0    failed=0
```

**Line-by-line breakdown:**

- First run `changed=1`, second `changed=0` → idempotent DNS configuration.
- `nmcli con up lab-dns` → Activate so NM regenerates `/etc/resolv.conf`.

**New words in this step:**

- **declarative resolver** — DNS described as desired state, not file edits.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `dns4` list | exact servers | replaces list |
| `dns_search` | search domains | list form |
| `state: present` | reconcile | idempotent |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Module missing | No collection | Install `community.general` |
| resolv.conf unchanged | Not activated | `nmcli con up` |

---

## TASK 2 of 2 — Verify the generated resolv.conf

**In plain English:** We read the generated file and assert the nameserver.

---

### Step 1 of 2 — Write the verification playbook

**In plain English:** We create `task2.yml` that reads `/etc/resolv.conf` and asserts the expected `nameserver`.

```yaml
---
- name: "Lab 38b Task 2 — verify generated resolv.conf"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Read the generated resolver config"
      ansible.builtin.command: "cat /etc/resolv.conf"
      register: rc
      changed_when: false

    - name: "Show the resolver config"
      ansible.builtin.debug:
        var: rc.stdout_lines

    - name: "Assert our DNS server is present"
      ansible.builtin.assert:
        that:
          - "rc.stdout_lines | select('search', 'nameserver 10.88.88.53') | list | length > 0"
        success_msg: "nameserver 10.88.88.53 present in resolv.conf"
        fail_msg: "expected nameserver missing — did NM regenerate the file?"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: cat /etc/resolv.conf` + `changed_when: false` → Read the generated file without marking a change.
- `select('search', 'nameserver 10.88.88.53')` → Keep matching lines; `length > 0` asserts presence.

**New words in this step:**

- **generated-file assertion** — proving NM wrote the expected resolver entry.

---

### Step 2 of 2 — Run it and confirm

**In plain English:** We run the play and confirm the nameserver is present.

```bash
ansible-playbook /root/rhcsa_journal/lab-38b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert our DNS server is present] ********************************
ok: [localhost] => {"changed": false, "msg": "nameserver 10.88.88.53 present in resolv.conf"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → The assertion confirms NM regenerated `/etc/resolv.conf` with our server; `changed=0`.

> If the assert fails, the profile wasn't activated — run `nmcli con up lab-dns` and re-test.

**New words in this step:**

- **end-to-end check** — module config proven all the way to the output file.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| read resolv.conf | verify output | `changed_when: false` |
| `select('search')` | match line | nameserver present |
| activation needed | NM regenerates | `con up` first |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Assert fails | Not activated | `nmcli con up lab-dns` |
| Wrong server | Profile drift | Re-run Task 1 |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the DNS playbook
- [ ] Task 1 · Step 2 — Run, activate, and prove idempotence
- [ ] Task 2 · Step 1 — Write the verification playbook
- [ ] Task 2 · Step 2 — Run it and confirm
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — dummy profile removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the dummy DNS profile and clear the sandbox.

> Removing the profile lets NM restore resolv.conf from your real connection.

```bash
sudo nmcli con down lab-dns 2>/dev/null || true
sudo nmcli con delete lab-dns 2>/dev/null || true
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-38
rm -rf /root/rhcsa_journal/lab-38b
```

**Expected output:**

```
Connection 'lab-dns' (...) successfully deleted.
✅ Removed /tmp/lab-38 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Templating resolv.conf | Overwritten by NM | Use `dns4`/`dns_search` |
| Skipping activation | File not regenerated | `nmcli con up` |
| Read task marks changed | Noisy runs | `changed_when: false` |

---

## 📌 Exam Strategy

Set DNS on the connection via `community.general.nmcli` (`dns4`, `dns_search`), activate, then assert the generated `/etc/resolv.conf`. Never template resolv.conf on an NM host — it reverts.

- `dns4`/`dns_search` are lists, set exactly.
- Activate so NM regenerates the file.
- Verify end-to-end by asserting the `nameserver` line.

---

## 🔗 Related Labs

- [Lab 38a — Configuring DNS Servers (RHCSA)](../lab-38a-resolv-conf-dns-rhcsa/) — the `nmcli`/`resolv.conf` basics
- [Lab 38c — Configuring DNS Servers (Verify)](../lab-38c-resolv-conf-dns-verify/) — prove the resolver config
- [Lab 36b — Command-Line Network Config (Ansible)](../lab-36b-nmcli-cli-config-ansible/) — the nmcli module fundamentals

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
