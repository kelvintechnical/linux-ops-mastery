# Lab 00b: Ansible Control Node (Ansible) — `ansible.builtin.dnf`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — Prerequisite Trilogy · **Lab 00b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (managing packages and config files idempotently), RHCSA EX200 (the `dnf`/file work underneath), DevOps (config-as-code for the automation host itself)  
**Prerequisite:** [Lab 00a](../lab-00a-ansible-control-node-rhcsa/) completed and `ansible --version` succeeds  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ansible.builtin.copy` | _Task 2 · Step 1_ |
| A2 | `ansible-playbook --check --diff` | _Task 2 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.dnf` (package state) | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible.builtin.assert` | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `register:` + idempotence re-run | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N4 | `ansible.builtin.template` vars | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Reproduce Lab 00a's control-node setup as **declarative automation**: a playbook that guarantees `ansible-core` is installed with `ansible.builtin.dnf`, asserts the binary exists, and another that lays down the inventory/config files with `ansible.builtin.copy`. You will run each play twice to watch `changed=1 → changed=0` (the idempotence proof) and dry-run with `--check --diff`, learning to manage the automation host itself the same way you manage everything else.

---

## 🧠 Concept

The control node is just another managed host — so it should be configured by code, not by hand. `ansible.builtin.dnf` declares "package present" and is idempotent: it only acts when the package is missing. `ansible.builtin.copy` declares a file's exact contents and only rewrites on drift. Because both modules compare desired vs actual state, a second run reports `changed=0`. That re-run discipline is the entire point of automation: the same play converges every box to the same state, every time.

```
SHELL (00a)                         ANSIBLE (00b)
─────────────────────────────       ──────────────────────────────────────
dnf install -y ansible-core         ansible.builtin.dnf: name=ansible-core state=present
cat > ansible.cfg <<EOF ...          ansible.builtin.copy: dest=ansible.cfg content="..."
                                       └─ changed=1 first run, changed=0 after
```

> **Why this matters:** Graders re-run your play. A package or file task that reports `changed=0` on the second run proves you used a state-aware module; `changed=1` forever signals you shelled out when a real module existed.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.dnf` | Manage RPM packages idempotently | `state: present/absent/latest`; needs `become: true` |
| `ansible.builtin.assert` | Fail the play unless a condition holds | `that:` takes a list of tests; `fail_msg:` for clarity |
| `ansible.builtin.copy` | Set a file's exact contents | `content:` inline; idempotent on re-run |
| `register:` | Capture a task's result for later use | pair with `debug:` to read `rc`/`changed` |
| `ansible-playbook --check --diff` | Dry-run and show the delta | makes no changes; previews `copy`/`template` writes |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Make the sandbox plus a durable folder for the playbooks, and point Ansible's config at the sandbox so everything is disposable.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
export LAB_ROOT=/tmp/lab-00
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-00b/playbooks

export ANSIBLE_CONFIG="$LAB_ROOT/ansible.cfg"
printf '[defaults]\ninventory = %s/inventory\nhost_key_checking = False\n' "$LAB_ROOT" > "$LAB_ROOT/ansible.cfg"
printf 'localhost ansible_connection=local\n' > "$LAB_ROOT/inventory"

ansible --version | head -1
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.3]
exit was: 0
```

---

## TASK 1 of 2 — Guarantee the engine with `ansible.builtin.dnf`

**In plain English:** We write a play that ensures `ansible-core` is present and asserts the binary exists, then run it twice to prove `dnf` is idempotent.

---

### Step 1 of 2 — Write the package + assert playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.dnf` to require the package and `ansible.builtin.assert` to confirm the engine is usable.

```yaml
---
- name: "Lab 00b Task 1 — ensure ansible-core is present (idempotent)"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure ansible-core is installed"
      ansible.builtin.dnf:
        name: ansible-core
        state: present
      register: pkg_result

    - name: "Assert the ansible binary exists"
      ansible.builtin.assert:
        that:
          - "pkg_result is succeeded"
        success_msg: "ansible-core is present"
        fail_msg: "ansible-core install failed"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `become: true` → Escalate to root because installing packages needs privilege.
- `ansible.builtin.dnf: name/state: present` → Declare the package required; the module installs it only if missing.
- `register: pkg_result` → Save the task's result so the next task can test it.
- `ansible.builtin.assert: that:` → Fail the play unless the package task succeeded, with friendly success/fail messages.

**New words in this step:**

- **`ansible.builtin.dnf`** — the state-aware module for RPM packages on RHEL/Fedora.
- **assert** — a guard task that stops the play unless every condition in `that:` is true.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the play two times; the first may install (or report already-present), and the second always reports `changed=0`, proving `dnf` only acts when needed.

```bash
ansible-playbook /root/rhcsa_journal/lab-00b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-00b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Runs the package + assert tasks; if `ansible-core` was already installed by Lab 00a, `changed=0` immediately.
- second `ansible-playbook ...` → Confirms convergence — the state already matches, so `changed=0` again.

**New words in this step:**

- **convergence** — repeatedly running a play drives the host to the same end state and then stops changing it.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `state: present` | install only if missing | `state: latest` upgrades every run (can flip `changed`) |
| `become: true` | run the task as root | omit it and `dnf` fails with permission denied |
| `assert` | guard with conditions | a bare `assert` without `that:` is a syntax error |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `This command has to be run under the root user` | Missing `become: true` | Add `become: true` to the play |
| `changed=1` every run | Used `state: latest` | Use `state: present` for stable idempotence |

---

## TASK 2 of 2 — Lay down config + inventory with `ansible.builtin.copy`

**In plain English:** We write a play that creates the inventory and config files declaratively, then dry-run it with `--check --diff` to preview the writes.

---

### Step 1 of 2 — Write the config/inventory playbook

**In plain English:** We create `task2.yml`, which uses `ansible.builtin.copy` with `content:` to declare the exact inventory and config files in the sandbox.

```yaml
---
- name: "Lab 00b Task 2 — manage inventory and config (idempotent)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-00
  tasks:
    - name: "Declare the inventory file"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/inventory"
        content: "localhost ansible_connection=local\n"
        mode: '0644'
      register: inv_result

    - name: "Declare the ansible.cfg file"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/ansible.cfg"
        content: |
          [defaults]
          inventory = {{ lab_root }}/inventory
          host_key_checking = False
        mode: '0644'
      register: cfg_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg:
          - "inventory changed: {{ inv_result.changed }}"
          - "config changed:    {{ cfg_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `vars: lab_root` → Define the sandbox path once and reuse it via `{{ lab_root }}`.
- `ansible.builtin.copy: content:` → Declare each file's exact bytes; the module writes only on drift.
- `register:` + `debug:` → Capture and print each file's `changed` flag so idempotence is readable.

**New words in this step:**

- **`vars:`** — playbook-level variables substituted by Jinja `{{ }}` wherever referenced.

---

### Step 2 of 2 — Dry-run with `--check --diff`, then apply

**In plain English:** We preview the changes with `--check --diff`, then run for real twice to confirm `changed=0` on the second pass.

```bash
ansible-playbook --check --diff /root/rhcsa_journal/lab-00b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-00b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-00b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook --check --diff ...` → Preview the file writes without making them; `--diff` prints the would-be content.
- first real run → Writes the files if they differ from the declared content (`changed=2` possible).
- second real run → Content already matches, so `changed=0` — the idempotence proof.

**New words in this step:**

- **drift** — when a file's real contents differ from the declared state; `copy` corrects it and reports `changed=1` only then.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `copy: content:` | sets exact file contents | trailing-newline mismatch keeps `changed=1` |
| `--check` | dry-run, no writes | some modules cannot fully predict in check mode |
| `--diff` | show before/after | only meaningful for file/content modules |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Second run still `changed=1` | Content/newline mismatch | Match `content:` exactly, including final newline |
| `dest is a directory` | `dest` points at a folder | Give `dest` a full file path |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the package + assert playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the config/inventory playbook
- [ ] Task 2 · Step 2 — Dry-run with `--check --diff`, then apply
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + any system state removed

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-00
rm -rf /root/rhcsa_journal/lab-00b
```

**This lab can install a SYSTEM package — reverse it only if you want a fully clean box:**

```bash
# sudo dnf remove -y ansible-core
```

**Expected output:**

```
✅ Removed /tmp/lab-00 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Forgetting `become: true` on `dnf` | Permission denied | Add `become: true` to the play |
| Using `state: latest` for stability | `changed` flips on upgrades | Use `state: present` |
| Shelling out to `dnf` | `changed=1` every run | Use `ansible.builtin.dnf` |

---

## 📌 Exam Strategy

The RHCE wants idempotent package and file management. Reach for `ansible.builtin.dnf` and `ansible.builtin.copy`/`template` instead of `shell:`. Run every play twice and read the PLAY RECAP — `changed=0` on the second run is the acceptance test the grader applies.

- Pair every state-changing task with a re-run check.
- Use `--check --diff` to preview before you apply on a production-like box.
- Keep `ansible.cfg` project-local so the environment is reproducible.

---

## 🔗 Related Labs

- [Lab 00a — Ansible Control Node (RHCSA)](../lab-00a-ansible-control-node-rhcsa/) — the hand-typed setup this play mirrors
- [Lab 00c — Ansible Control Node (Verify)](../lab-00c-ansible-control-node-verify/) — prove the engine, config, and ping all work
- [Lab 01b — Stdout Redirection (Ansible)](../lab-01b-stdout-redirection-ansible/) — `shell:` vs `copy:` idempotence, now that your node is built

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
