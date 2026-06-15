# Lab 39b: Configure SSH and Key-Based Auth (Ansible) — keys & `authorized_key`

**Series:** linux-ops-mastery — Networking · **Lab 39b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (user/SSH key modules), RHCSA EX200 (the key mechanics underneath), SRE (provisioning access at scale)  
**Prerequisite:** [Lab 39a](../lab-39a-ssh-key-auth-rhcsa/) completed and a working control node  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `command:` + `creates:` (from Lab 10) | _Task 1 · Step 1_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | generate key with `creates:` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible.builtin.slurp` the pubkey | Task 1 · Step 2 | _Task 1 · Step 2_ |
| N3 | `ansible.posix.authorized_key` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `state: absent` key removal | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Provision SSH key access declaratively. You'll generate a key pair idempotently (using `creates:` so it runs once), read the public key with `slurp`, install it into an account with `ansible.posix.authorized_key`, and remove it with `state: absent`. This is how access is granted and revoked at fleet scale — repeatable and reversible.

> **Safety note:** Keys are written to the sandbox `/tmp/lab-39`. The public key is authorized only for *your own* account and removed in Teardown. No remote hosts are modified.

---

## 🧠 Concept

The Ansible way to manage SSH access has two idempotent halves. **Key generation**: wrap `ssh-keygen` in a `command` task with `creates: KEYPATH` so it only runs when the key is absent — or use `community.crypto.openssh_keypair` if the collection is present. **Key installation**: `ansible.posix.authorized_key` declaratively ensures a public key is present (`state: present`) or absent (`state: absent`) in a user's `authorized_keys`, handling permissions and de-duplication for you (far better than appending with `lineinfile`). To feed the key in, read it with `ansible.builtin.slurp` and `b64decode`. The pattern — generate once, authorize declaratively, revoke with `state: absent` — gives clean, auditable access management. Granting access becomes a reviewable change; revoking is one line flip.

```
command: ssh-keygen ... creates: KEY      → generate once (idempotent)
slurp: src=KEY.pub → b64decode             → read the public key
ansible.posix.authorized_key:
  user: "{{ ansible_user_id }}"
  key: "<pubkey>"
  state: present                            → grant access
  state: absent                             → revoke access
```

> **Why this matters:** Manually copying keys to many servers is error-prone and unauditable. `authorized_key` makes access a declarative, idempotent, reviewable change — and revocation as simple as flipping `state` to `absent`.

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `command: ssh-keygen` + `creates:` | Generate once | idempotent |
| `ansible.builtin.slurp` | Read pubkey | `b64decode` |
| `ansible.posix.authorized_key` | Manage authorized key | `user`, `key`, `state` |
| `state: present/absent` | Grant/revoke | declarative |
| `command: ssh -i` | Verify login | `changed_when: false` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, playbook folder, and ensure `~/.ssh` exists.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-39
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-39b/playbooks
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Generate the key idempotently

**In plain English:** We create the key pair once and read the public half.

---

### Step 1 of 2 — Write the key-generation playbook

**In plain English:** We create `task1.yml` that generates the key only if it doesn't exist.

```yaml
---
- name: "Lab 39b Task 1 — generate an SSH key (idempotent)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    key_path: /tmp/lab-39/lab_key
  tasks:
    - name: "Generate the key pair once"
      ansible.builtin.command: "ssh-keygen -t ed25519 -f {{ key_path }} -N '' -C lab-39b"
      args:
        creates: "{{ key_path }}"
      register: gen

    - name: "Read the public key"
      ansible.builtin.slurp:
        src: "{{ key_path }}.pub"
      register: pub

    - name: "Show the public key"
      ansible.builtin.debug:
        msg: "{{ (pub.content | b64decode) | trim }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: ssh-keygen ...` + `args: creates: KEY` → Runs only when the key is missing — idempotent generation.
- `slurp: src: KEY.pub` + `b64decode` → Read the public key content for the next task.

**New words in this step:**

- **`creates:`** — skip the command if the named file already exists.

---

### Step 2 of 2 — Run it twice to prove idempotence

**In plain English:** We apply the play, then re-run to confirm `changed=0` for generation.

```bash
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task1.yml | grep -E 'changed='
```

**Expected output:**

```
localhost                  : ok=3    changed=1    unreachable=0    failed=0
localhost                  : ok=3    changed=0    unreachable=0    failed=0
```

**Line-by-line breakdown:**

- First run `changed=1` (key created); second `changed=0` (`creates:` skips it) — idempotent.

**New words in this step:**

- **run-once generation** — the key is produced a single time, safely re-runnable.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `creates:` | idempotent cmd | skips if file exists |
| `slurp` | read file | base64 |
| `b64decode` | decode | needed after slurp |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Regenerates each run | `creates:` wrong path | Match `key_path` |
| slurp fails | `.pub` missing | Ensure keygen ran |

---

## TASK 2 of 2 — Grant and revoke access

**In plain English:** We authorize the key, then revoke it declaratively.

---

### Step 1 of 2 — Write the authorize/revoke playbook

**In plain English:** We create `task2.yml` that grants the key, then demonstrates revocation.

```yaml
---
- name: "Lab 39b Task 2 — manage authorized_key"
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    key_path: /tmp/lab-39/lab_key
  tasks:
    - name: "Read the public key"
      ansible.builtin.slurp:
        src: "{{ key_path }}.pub"
      register: pub

    - name: "Authorize the key for this account"
      ansible.posix.authorized_key:
        user: "{{ ansible_user_id }}"
        key: "{{ pub.content | b64decode }}"
        state: present
      register: grant

    - name: "Report grant status"
      ansible.builtin.debug:
        msg: "authorized: {{ grant.changed }}"

    - name: "Revoke the key (demonstration)"
      ansible.posix.authorized_key:
        user: "{{ ansible_user_id }}"
        key: "{{ pub.content | b64decode }}"
        state: absent
      register: revoke

    - name: "Report revoke status"
      ansible.builtin.debug:
        msg: "revoked: {{ revoke.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `authorized_key: user: ... key: ... state: present` → Ensures the public key is in the account's `authorized_keys` (handles perms/dedup).
- `state: absent` → Removes the same key — declarative revocation.
- `ansible_user_id` → The current user fact, so we only touch our own account.

**New words in this step:**

- **`ansible.posix.authorized_key`** — module to grant/revoke SSH keys for a user.

---

### Step 2 of 2 — Run it and read grant/revoke

**In plain English:** We run the play and see the key granted then revoked.

```bash
ansible-playbook /root/rhcsa_journal/lab-39b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report grant status] *********************************************
ok: [localhost] => {"msg": "authorized: True"}
TASK [Report revoke status] ********************************************
ok: [localhost] => {"msg": "revoked: True"}
PLAY RECAP **********************************************************
localhost                  : ok=6    changed=2    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → Grants the key (`authorized: True`), then revokes it (`revoked: True`) — full lifecycle in one run.

> In practice you'd keep `state: present` to retain access; the revoke step here is for demonstration and leaves the account clean.

**New words in this step:**

- **access lifecycle** — grant and revoke as declarative state flips.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `state: present` | grant | dedups automatically |
| `state: absent` | revoke | exact key match |
| `ansible_user_id` | current user | needs facts |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Module not found | No `ansible.posix` | `ansible-galaxy collection install ansible.posix` |
| Undefined `ansible_user_id` | `gather_facts: false` | Enable facts |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the key-generation playbook
- [ ] Task 1 · Step 2 — Run it twice to prove idempotence
- [ ] Task 2 · Step 1 — Write the authorize/revoke playbook
- [ ] Task 2 · Step 2 — Run it and read grant/revoke
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — authorized key removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Ensure the key is de-authorized and clear the sandbox.

> Task 2 already revokes the key; this is a safety net plus sandbox cleanup.

```bash
sed -i '/lab-39b/d' ~/.ssh/authorized_keys 2>/dev/null || true
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-39
rm -rf /root/rhcsa_journal/lab-39b
```

**Expected output:**

```
✅ Removed /tmp/lab-39 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `lineinfile` for keys | Dups/permission bugs | Use `authorized_key` |
| No `creates:` | Key regenerated | Add `creates:` |
| Missing collection | Module error | Install `ansible.posix` |

---

## 📌 Exam Strategy

Generate once (`command` + `creates:`), authorize declaratively (`ansible.posix.authorized_key`, `state: present`), revoke with `state: absent`. The module handles permissions and de-duplication — don't hand-roll with `lineinfile`.

- `creates:` makes key generation idempotent.
- `authorized_key` is the right module for granting access.
- Flip `state` to `absent` to revoke cleanly.

---

## 🔗 Related Labs

- [Lab 39a — Configure SSH and Key-Based Auth (RHCSA)](../lab-39a-ssh-key-auth-rhcsa/) — the `ssh-keygen`/`authorized_keys` mechanics
- [Lab 39c — Configure SSH and Key-Based Auth (Verify)](../lab-39c-ssh-key-auth-verify/) — prove key auth and permissions
- [Lab 27b — Safely Editing System Databases (Ansible)](../lab-27b-vipw-vigr-safe-editing-ansible/) — managing the users these keys belong to

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
