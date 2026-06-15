# Lab 27b: Safely Editing System Databases (Ansible) — `group`, `user` modules

**Series:** linux-ops-mastery — Users & Groups · **Lab 27b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent account management), RHCSA EX200 (the `vipw`/`vigr` work, automated), DevOps (declarative identity)  
**Prerequisite:** [Lab 27a](../lab-27a-vipw-vigr-safe-editing-rhcsa/) completed and a working control node · **root/sudo required**  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | account databases (`getent`) | _Task 1 · Step 2_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | `ansible.builtin.group` | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `ansible.builtin.user` | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N3 | `state: present/absent` accounts | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N4 | `getent` verification in-play | Task 2 · Step 1 | _Task 2 · Step 1_ |

---

## 🎯 Objective

Manage the account databases declaratively. You will create a group with `ansible.builtin.group` and a user in it with `ansible.builtin.user` — both idempotent, both handling the same locking `vipw`/`vigr` use. You'll prove a re-run is `changed=0` and verify with `getent`. This is the production-correct way to do what Lab 27a did by hand.

> **⚠️ System-state lab.** Creates a test group (`labtest99`) and user (`labtest`). The Teardown removes both. Use a practice VM.

---

## 🧠 Concept

`ansible.builtin.group` and `ansible.builtin.user` are the automation equivalents of `vigr`/`vipw`/`useradd`/`groupadd`. They operate on `/etc/passwd`, `/etc/shadow`, `/etc/group`, and `/etc/gshadow` using the same locking primitives, so concurrent safety is handled for you. They're declarative: `state: present` ensures the account exists with the given attributes, `state: absent` removes it, and re-running converges to `changed=0`. You never format a database line by hand — you declare the desired identity and Ansible reconciles it. `getent group/passwd` verifies the result through NSS.

```
RHCSA (27a)                          ANSIBLE (27b)
─────────────────────────────       ──────────────────────────────────────
vigr → add group line                group: name=labtest99 gid=6999 state=present
vipw → add user line                 user: name=labtest group=labtest99 state=present
pwck / grpck                         getent passwd/group + re-run changed=0
```

> **Why this matters:** RHCE expects idempotent identity management. The `user`/`group` modules give you locking, shadow sync, and idempotence in one declarative step — everything Lab 27a did manually, made safe and repeatable.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.group` | Manage a group | `name:`, `gid:`, `state:` |
| `ansible.builtin.user` | Manage a user | `name:`, `group:`, `state:` |
| `state: present/absent` | Ensure/remove | declarative |
| `getent` | Verify via NSS | `group`/`passwd` |
| `register:` + re-run | Prove idempotence | `changed=0` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the playbook folder; the accounts live in the system databases.

> Run this block **once** before Task 1. `LAB_ROOT` is only a marker for Teardown; the real changes are the test accounts, reverted in Teardown.

```bash
export LAB_ROOT=/tmp/lab-27
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-27b/playbooks
echo "setup done"
echo "exit was: $?"
```

**Expected output:**

```
setup done
exit was: 0
```

---

## TASK 1 of 2 — Create a group idempotently

**In plain English:** We declare the test group and prove a re-run changes nothing.

---

### Step 1 of 2 — Write the group playbook

**In plain English:** We create `task1.yml`, which ensures the `labtest99` group exists with a fixed GID.

```yaml
---
- name: "Lab 27b Task 1 — manage a group"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure the labtest99 group exists"
      ansible.builtin.group:
        name: labtest99
        gid: 6999
        state: present
      register: grp_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ grp_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.group: name/gid/state: present` → Declare the group; the module locks and edits `/etc/group` safely — the `vigr` work, automated.
- `become: true` → Account changes need root.

**New words in this step:**

- **`ansible.builtin.group`** — declarative, locked group management.

---

### Step 2 of 2 — Run it twice and watch `changed=0`

**In plain English:** We run the play twice; the group is created once, then already present.

```bash
ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task1.yml
getent group labtest99
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP ********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
labtest99:x:6999:
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: the module converges to the declared state.
- `getent group labtest99` → Confirms the group exists with GID 6999.

**New words in this step:**

- **declarative identity** — declaring an account's desired state rather than editing a line.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `group` module | manage groups | locking handled |
| `gid:` | fixed group id | avoids collisions |
| idempotent | re-run `changed=0` | already-present groups |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| GID in use | Collision | Pick a free GID |
| Permission denied | No `become` | Add `become: true` |

---

## TASK 2 of 2 — Create a user in the group

**In plain English:** We add a user to the group and verify it via `getent`.

---

### Step 1 of 2 — Write the user playbook

**In plain English:** We create `task2.yml`, which ensures a `labtest` user exists in the `labtest99` group, then verifies with `getent`.

```yaml
---
- name: "Lab 27b Task 2 — manage a user"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Ensure the labtest user exists in labtest99"
      ansible.builtin.user:
        name: labtest
        group: labtest99
        shell: /sbin/nologin
        create_home: false
        state: present
      register: usr_result

    - name: "Verify the user via getent (read-only)"
      ansible.builtin.command: "getent passwd labtest"
      register: ent
      changed_when: false

    - name: "Show the account and change status"
      ansible.builtin.debug:
        msg:
          - "changed: {{ usr_result.changed }}"
          - "passwd entry: {{ ent.stdout }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.user: name/group/state: present` → Declare the user in the group — the `vipw`/`useradd` work, automated and locked.
- `shell: /sbin/nologin`, `create_home: false` → A minimal service-style test account.
- `command: getent passwd labtest` (read-only) → Verify the account exists through NSS.

**New words in this step:**

- **`ansible.builtin.user`** — declarative, locked user management.

---

### Step 2 of 2 — Run it twice and verify

**In plain English:** We run the play twice; the user is created once and then unchanged, and `getent` confirms it.

```bash
ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-27b/playbooks/task2.yml
id labtest
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP (run 1) : ok=3  changed=1  ...
PLAY RECAP (run 2) : ok=3  changed=0  ...
uid=NNNN(labtest) gid=6999(labtest99) groups=6999(labtest99)
exit was: 0
```

**Line-by-line breakdown:**

- two runs → `changed=1` then `changed=0`: idempotent user creation.
- `id labtest` → Confirms the user's primary group is `labtest99`.

**New words in this step:**

- **NSS verification** — confirming an account via `getent`/`id` rather than reading files.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `user` module | manage users | shadow sync handled |
| `group:` | primary group | must exist first |
| `getent` check | verify via NSS | not file parsing |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Group not found | Group task not run | Run Task 1 first |
| Home created unexpectedly | `create_home` default | Set `create_home: false` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the group playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0`
- [ ] Task 2 · Step 1 — Write the user playbook
- [ ] Task 2 · Step 2 — Run it twice and verify
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — sandbox + **test user and group removed**

---

## 🧹 Teardown

**In plain English:** Remove the test user and group from the real databases, then delete the sandbox.

> This lab changed system state (added `labtest` and `labtest99`). These commands **reverse** those changes; then `lab_teardown.sh` clears the marker sandbox.

```bash
sudo userdel labtest 2>/dev/null || true
sudo groupdel labtest99 2>/dev/null || true
getent passwd labtest || echo "labtest removed"
getent group labtest99 || echo "labtest99 removed"
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-27
rm -rf /root/rhcsa_journal/lab-27b
```

**Expected output:**

```
labtest removed
labtest99 removed
✅ Removed /tmp/lab-27 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Hand-editing in a play | Non-idempotent, unsafe | Use `user`/`group` modules |
| User before group | "group not found" | Order tasks correctly |
| Forgetting `become` | Permission denied | Add `become: true` |

---

## 📌 Exam Strategy

Use the `group` and `user` modules for all account work — they handle locking, shadow sync, and idempotence that hand-editing can't. Order matters: groups before users. Verify with `getent`/`id`, and re-run to confirm `changed=0`.

- `group` then `user` — dependencies first.
- `state: absent` cleanly removes accounts.
- `getent`/`id` verify through NSS, not file parsing.

---

## 🔗 Related Labs

- [Lab 27a — Safely Editing System Databases (RHCSA)](../lab-27a-vipw-vigr-safe-editing-rhcsa/) — the `vipw`/`vigr` work this automates
- [Lab 27c — Safely Editing System Databases (Verify)](../lab-27c-vipw-vigr-safe-editing-verify/) — prove consistency and cleanup
- [Lab 26b — Editing Files (Ansible)](../lab-26b-vi-editor-ansible/) — declarative file edits

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
