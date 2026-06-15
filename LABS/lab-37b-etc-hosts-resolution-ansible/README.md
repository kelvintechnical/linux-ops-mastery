# Lab 37b: Configuring Local Host Resolution (Ansible) — manage `/etc/hosts`

**Series:** linux-ops-mastery — Networking · **Lab 37b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (file/line management), RHCSA EX200 (the `/etc/hosts` underneath), SRE (consistent host maps across a fleet)  
**Prerequisite:** [Lab 37a](../lab-37a-etc-hosts-resolution-rhcsa/) completed and a working control node  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Today's Focus Coverage

> Stay on-subject via the ANCHOR rows; expand vocabulary via the NEW rows. Every row is exercised by a STEP below.

**⚓ Anchor — already learned (on-topic reuse)**

| # | Command / switch | Covered by |
|---|---|---|
| A1 | `ansible.builtin.blockinfile` (from Lab 26) | _Task 1 · Step 1_ |
| A2 | idempotence (`changed=0`) | _Task 1 · Step 2_ |

**🆕 NEW this lab — introduced for the first time** (minimum 3)

| # | Command / switch | First taught in | Covered by |
|---|---|---|---|
| N1 | manage `/etc/hosts` with markers | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N2 | `backup: true` on system file | Task 1 · Step 1 | _Task 1 · Step 1_ |
| N3 | `getent hosts` in a play | Task 2 · Step 1 | _Task 2 · Step 1_ |
| N4 | `assert` on resolution | Task 2 · Step 2 | _Task 2 · Step 2_ |

---

## 🎯 Objective

Manage `/etc/hosts` entries idempotently and prove they resolve. You'll use `ansible.builtin.blockinfile` (with a marker and `backup: true`) to maintain a clearly-delimited group of mappings, then run `getent hosts` in the play and assert the names resolve to the expected IP. This makes static host maps consistent and repeatable across machines.

> **Safety note:** The play edits the real `/etc/hosts` but only inside a labeled marker block, with a backup. Teardown removes the block. Mappings use TEST-NET addresses.

---

## 🧠 Concept

`blockinfile` is the right tool for a *group* of related lines: it wraps them in `# BEGIN/END ANSIBLE MANAGED BLOCK` markers and replaces the whole block as a unit, so the file converges to your declared entries and re-runs report `changed=0`. (`lineinfile` is for a single line.) Always set `backup: true` when touching a system file so a timestamped copy is kept. After managing the block, verify the way the OS resolves: `command: getent hosts NAME` with `changed_when: false`, then `assert` the output contains the expected IP. The pattern — declare the block, then assert the runtime resolution — proves both that the file is right and that resolution actually works.

```
blockinfile: path=/etc/hosts marker="# {mark} LAB37" block=<entries> backup=true
re-run                       → changed=0 (block already matches)
command: getent hosts NAME (changed_when:false) → real resolution
assert that "EXPECTED_IP in stdout" → prove it resolves
```

> **Why this matters:** Hand-editing `/etc/hosts` on each host drifts. A managed marker block keeps every machine's static map identical and reversible, and the `getent` assertion turns "looks right" into "verified resolves".

---

## 📚 Command Reference

| Command | Purpose | Critical detail |
|---|---|---|
| `ansible.builtin.blockinfile` | Manage a group of lines | `marker:`, `block:` |
| `backup: true` | Keep a copy | system-file safety |
| `command: getent hosts` | Resolve via NSS | `changed_when: false` |
| `ansible.builtin.assert` | Pass/fail | `that:` conditions |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Build the sandbox, playbook folder, and back up `/etc/hosts`.

> Run this block **once** before Task 1.

```bash
export LAB_ROOT=/tmp/lab-37
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-37b/playbooks
sudo cp -a /etc/hosts "$LAB_ROOT/hosts.backup"
echo "ready"
echo "exit was: $?"
```

**Expected output:**

```
ready
exit was: 0
```

---

## TASK 1 of 2 — Manage a hosts block

**In plain English:** We declare a marked block of mappings, idempotently.

---

### Step 1 of 2 — Write the blockinfile playbook

**In plain English:** We create `task1.yml` that maintains a labeled block of host entries with a backup.

```yaml
---
- name: "Lab 37b Task 1 — manage /etc/hosts block"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Maintain the lab host entries"
      ansible.builtin.blockinfile:
        path: /etc/hosts
        marker: "# {mark} LAB-37 ANSIBLE"
        backup: true
        block: |
          192.0.2.20   db.lab.local db
          192.0.2.21   cache.lab.local cache
      register: blk

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg: "changed: {{ blk.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `blockinfile ... marker: "# {mark} LAB-37 ANSIBLE"` → Wraps the entries in BEGIN/END markers so the block is managed as a unit.
- `backup: true` → Saves a timestamped copy of `/etc/hosts` before editing.
- `block: |` → The exact set of mappings the file should contain in that block.

**New words in this step:**

- **managed block** — a marker-delimited region Ansible owns and converges.

---

### Step 2 of 2 — Run it twice to prove idempotence

**In plain English:** We apply the play, then re-run to confirm `changed=0`.

```bash
ansible-playbook /root/rhcsa_journal/lab-37b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-37b/playbooks/task1.yml | grep -E 'changed='
grep -A2 'LAB-37 ANSIBLE' /etc/hosts | head -n 4
```

**Expected output:**

```
localhost                  : ok=2    changed=1    unreachable=0    failed=0
localhost                  : ok=2    changed=0    unreachable=0    failed=0
# BEGIN LAB-37 ANSIBLE
192.0.2.20   db.lab.local db
192.0.2.21   cache.lab.local cache
```

**Line-by-line breakdown:**

- First run `changed=1`, second `changed=0` → the block converged, idempotence proven.
- `grep -A2 'LAB-37 ANSIBLE'` → Shows the managed block now present in `/etc/hosts`.

**New words in this step:**

- **convergence** — repeated runs leave the file unchanged once correct.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `blockinfile` | group of lines | `lineinfile` = one line |
| `marker` | delimits block | unique per purpose |
| `backup: true` | safety copy | always on system files |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Permission denied | No `become` | Add `become: true` |
| Duplicate blocks | Different markers | Reuse one marker |

---

## TASK 2 of 2 — Verify resolution in a play

**In plain English:** We resolve the managed names and assert the IP.

---

### Step 1 of 2 — Write the verification playbook

**In plain English:** We create `task2.yml` that runs `getent hosts` and asserts the result.

```yaml
---
- name: "Lab 37b Task 2 — verify resolution"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Resolve the managed name"
      ansible.builtin.command: "getent hosts db.lab.local"
      register: res
      changed_when: false
      failed_when: res.rc != 0

    - name: "Show the resolution"
      ansible.builtin.debug:
        var: res.stdout

    - name: "Assert it maps to the expected IP"
      ansible.builtin.assert:
        that:
          - "'192.0.2.20' in res.stdout"
        success_msg: "db.lab.local resolves to 192.0.2.20"
        fail_msg: "unexpected resolution: {{ res.stdout }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `command: getent hosts db.lab.local` → Resolves the managed name via NSS; `failed_when: res.rc != 0` flags a missing entry.
- `assert ... '192.0.2.20' in res.stdout` → Proves the name maps to the intended IP.

**New words in this step:**

- **resolution assertion** — proving a name resolves to the expected address.

---

### Step 2 of 2 — Run it and confirm the assertion

**In plain English:** We run the play and confirm resolution passes.

```bash
ansible-playbook /root/rhcsa_journal/lab-37b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Assert it maps to the expected IP] *******************************
ok: [localhost] => {"changed": false, "msg": "db.lab.local resolves to 192.0.2.20"}
PLAY RECAP **********************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook ...` → The assertion confirms the managed entry resolves correctly; `changed=0` (read-only).

**New words in this step:**

- **verified map** — the entry is proven to resolve, not just present.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `getent hosts` | NSS resolve | use, not `dig` |
| `failed_when` | missing = fail | rc check |
| `assert` | IP match | substring test |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| rc != 0 | Entry missing | Re-run Task 1 |
| Assert fails | Wrong IP | Fix the block in Task 1 |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the blockinfile playbook
- [ ] Task 1 · Step 2 — Run it twice to prove idempotence
- [ ] Task 2 · Step 1 — Write the verification playbook
- [ ] Task 2 · Step 2 — Run it and confirm the assertion
- [ ] Every 🎯 Focus Coverage row (Anchor + NEW) mapped to a step
- [ ] 🧹 Teardown run — `/etc/hosts` block removed + sandbox cleared

---

## 🧹 Teardown

**In plain English:** Remove the managed block and clear the sandbox.

> This lab edited `/etc/hosts`; the marker block is removed (and a backup exists in the sandbox).

```bash
# Remove the Ansible-managed block precisely:
sudo sed -i '/# BEGIN LAB-37 ANSIBLE/,/# END LAB-37 ANSIBLE/d' /etc/hosts
# ... or restore from the backup if needed:
# sudo cp -a "$LAB_ROOT/hosts.backup" /etc/hosts
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-37
rm -rf /root/rhcsa_journal/lab-37b
```

**Expected output:**

```
✅ Removed /tmp/lab-37 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `lineinfile` for many lines | Messy file | Use `blockinfile` |
| No `backup: true` | No undo | Always back up system files |
| Testing with `dig` | Skips `/etc/hosts` | Use `getent hosts` |

---

## 📌 Exam Strategy

Use `blockinfile` for a group of host entries (with a unique `marker` and `backup: true`), then prove they resolve with `getent hosts` + `assert`. Idempotence (`changed=0` on re-run) confirms the file converged.

- `blockinfile` for groups, `lineinfile` for one line.
- `backup: true` on every system-file edit.
- `getent hosts` (not `dig`) to verify resolution.

---

## 🔗 Related Labs

- [Lab 37a — Configuring Local Host Resolution (RHCSA)](../lab-37a-etc-hosts-resolution-rhcsa/) — the `/etc/hosts` format this manages
- [Lab 37c — Configuring Local Host Resolution (Verify)](../lab-37c-etc-hosts-resolution-verify/) — prove resolution works
- [Lab 26b — Command/Insert Mode in vi (Ansible)](../lab-26b-vi-editor-ansible/) — `blockinfile`/`lineinfile` foundations

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
