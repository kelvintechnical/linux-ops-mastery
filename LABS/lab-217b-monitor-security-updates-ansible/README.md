# Lab 217b: Monitor Security Updates (Ansible) — `ansible.builtin.command` rc-100, `ansible.builtin.dnf` `security:`

**Series:** linux-ops-mastery — Security Administration · **Lab 217b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (the `dnf` module, `failed_when`, `check_mode`, register/debug audit trail), RHCSA EX200 (the patch survey underneath), SRE/DevOps (fleet-wide patch reporting)  
**Prerequisite:** [Lab 217a](../lab-217a-monitor-security-updates-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Express Lab 217a's update survey as Ansible, and master the two idioms the exam loves: surviving `dnf check-update`'s **exit code 100** with `failed_when: result.rc not in [0,100]`, and previewing a **security-only** upgrade non-destructively with `ansible.builtin.dnf` (`security: true`, `state: latest`) under `check_mode`. You will run each play twice to confirm it stays safe and reports honestly, capturing every result with `register:` and `ansible.builtin.debug` so a grader can read exactly what happened.

---

## 🧠 Concept

`ansible.builtin.command` runs a program and, by default, **fails the task on any nonzero exit code** — which means `dnf check-update` would *always* fail the play the moment updates exist, since it returns `100`. The fix is `failed_when: result.rc not in [0, 100]`: you redefine "failure" so the rc-100 "updates available" signal is treated as success. The canonical idiom pairs that with `changed_when: false` (a read-only query never "changes" anything) and `register:` + `debug:` to surface the result. For the upgrade itself, the real module `ansible.builtin.dnf` understands security errata directly via `security: true`; run it with `check_mode: true` and it *predicts* the transaction (`changed=1` when patches are pending) without applying anything — the declarative cousin of `dnf upgrade --security --assumeno`.

```
SHELL (217a)                              ANSIBLE (217b)
────────────────────────────────         ───────────────────────────────────────────
dnf check-update ; echo $?  → 100         ansible.builtin.command: dnf check-update
                                            register: r
                                            failed_when: r.rc not in [0, 100]   ← the trap-tamer
                                            changed_when: false

dnf upgrade --security --assumeno         ansible.builtin.dnf:
   (preview, applies nothing)               name: '*'
                                            state: latest
                                            security: true
                                          check_mode: true                       ← safe preview
                                            └─ changed=1 when patches pending, applies NOTHING
```

> **Why this matters:** RHCE graders re-run plays and read the recap. A check-update task with no `failed_when` is a time bomb that fails on every healthy server with pending updates. And a real `dnf:` task left *without* `check_mode` would actually patch the grader's box — knowing how to preview safely is the difference between "reported risk" and "mutated production."

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `dnf update` | The anchor: apply all updates | referenced only — the playbook previews, it does not apply |
| `ansible.builtin.command` + `failed_when` | Run `dnf check-update` and survive rc=100 | `failed_when: r.rc not in [0,100]`, plus `changed_when: false` |
| `ansible.builtin.dnf` (`security: true`) | Module-native security-only upgrade | `state: latest`, `security: true`; pair with `check_mode: true` to preview |
| `check_mode: true` | Make any task a dry run that changes nothing | reports predicted `changed` without acting |
| `register:` / `ansible.builtin.debug` | Capture and print `rc`, `stdout`, `changed` | the audit trail RHCE graders expect |
| `ansible-playbook` | Run a playbook | run it **twice** to confirm non-destructive behavior |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, create the durable folder for our playbooks under `/root`, and create the `/tmp` sandbox the plays will write their reports into.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-217
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-217b/playbooks

ansible --version | head -2
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-217b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /tmp/lab-217
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /root/rhcsa_journal/lab-217b/playbooks
Setup complete at 2026-06-15T17:45:08-04:00
exit was: 0
```

---

## TASK 1 of 2 — Discover updates without failing on rc=100

**In plain English:** We write a playbook that runs `dnf check-update`, teaches Ansible that exit code 100 is *not* a failure, saves the pending list, then run it twice to prove it stays green on a system that has updates.

---

### Step 1 of 2 — Write the rc-100-safe check-update playbook

**In plain English:** We create `task1.yml`, which runs `dnf check-update` via `ansible.builtin.command`, uses `failed_when` so only an rc *other than* 0 or 100 counts as a failure, saves the output, and prints the meaning of the exit code.

```yaml
---
- name: "Lab 217b Task 1 — discover updates without failing on rc=100"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    lab_root: /tmp/lab-217

  tasks:
    - name: "Ensure the sandbox exists for reports"
      ansible.builtin.file:
        path: "{{ lab_root }}"
        state: directory
        mode: '0755'

    - name: "Run dnf check-update (rc 100 = updates available, NOT a failure)"
      ansible.builtin.command: dnf check-update
      register: check_result
      changed_when: false
      failed_when: check_result.rc not in [0, 100]

    - name: "Save the pending list into the sandbox"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/pending.txt"
        content: "{{ check_result.stdout }}\n"
        mode: '0644'

    - name: "Report what the exit code means"
      ansible.builtin.debug:
        msg:
          - "rc: {{ check_result.rc }}"
          - "meaning: {{ 'updates available' if check_result.rc == 100 else 'up to date' if check_result.rc == 0 else 'error' }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `become: true` → `dnf` needs root to read repo metadata caches reliably, so we escalate.
- `ansible.builtin.command: dnf check-update` → Run the query through `command` (no shell needed — there is no redirect or pipe here); `register: check_result` captures its rc and stdout.
- `changed_when: false` → A read-only query never changes the system, so we tell Ansible not to report `changed`.
- `failed_when: check_result.rc not in [0, 100]` → The key idiom: only an exit code that is *neither* 0 nor 100 is a real failure, so the rc-100 "updates available" case passes.
- `ansible.builtin.copy: content: "{{ check_result.stdout }}\n"` → Persist the captured list to `pending.txt` declaratively.

**New words in this step:**

- **`failed_when`** — a per-task override that redefines what counts as task failure, instead of "any nonzero exit."
- **`changed_when: false`** — marks a task as never-changing, the honest label for a read-only query.

---

### Step 2 of 2 — Run it twice and confirm it stays green (rc=100 handled)

**In plain English:** We run the saved playbook two times; both runs succeed (`failed=0`) even though `dnf check-update` returns 100, and `changed=0` because querying changes nothing — the rc-100 trap defused.

```bash
ansible-playbook /root/rhcsa_journal/lab-217b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-217b/playbooks/task1.yml
cat /tmp/lab-217/pending.txt
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report what the exit code means] ****************************************
ok: [localhost] => {
    "msg": [
        "rc: 100",
        "meaning: updates available"
    ]
}
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
openssl.x86_64                  1:3.2.2-6.el9_5             appstream
sudo.x86_64                     1.9.5p2-10.el9_5           baseos
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run: `failed=0` despite rc 100 (the `failed_when` did its job); `changed=1` only because `copy` wrote `pending.txt` for the first time.
- second `ansible-playbook ...` → Second run: `changed=0` because the report file already matches — the query and listing are idempotent.
- `cat /tmp/lab-217/pending.txt` → Read the saved pending list to confirm the report landed in the sandbox.

**New words in this step:**

- **PLAY RECAP** — Ansible's end-of-run summary of `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `failed_when: rc not in [0,100]` | survives DNF's rc-100 "updates available" | omitting it fails the play on every server with updates |
| `changed_when: false` | labels a read-only task honestly | without it, `command` reports `changed=1` every run |
| `register:` + `debug:` | exposes rc/stdout for grading | graders expect the captured audit trail |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Play fails with `non-zero return code` | No `failed_when` on the check-update task | Add `failed_when: result.rc not in [0,100]` |
| Task always shows `changed=1` | Missing `changed_when: false` | Mark read-only commands as never-changing |

---

## TASK 2 of 2 — Preview a security-only upgrade (no changes applied)

**In plain English:** We write a playbook that uses the real `dnf` module to *predict* a security-only upgrade under `check_mode`, lists the security advisories for the report, and run it twice to prove it never actually patches the box.

---

### Step 1 of 2 — Write the `check_mode` security-preview playbook

**In plain English:** We create `task2.yml`, which runs `ansible.builtin.dnf` with `security: true` and `state: latest` under `check_mode: true` so it only forecasts the security upgrade, then saves the advisory list and reports whether it *would* change anything.

```yaml
---
- name: "Lab 217b Task 2 — preview a security-only upgrade (no changes applied)"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    lab_root: /tmp/lab-217

  tasks:
    - name: "Predict the security-only upgrade (check_mode = dry run)"
      ansible.builtin.dnf:
        name: '*'
        state: latest
        security: true
      check_mode: true
      register: sec_preview

    - name: "List pending security advisories for the report"
      ansible.builtin.command: dnf updateinfo list security
      register: sec_list
      changed_when: false
      failed_when: sec_list.rc not in [0, 100]

    - name: "Save the security advisory listing into the sandbox"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/security-advisories.txt"
        content: "{{ sec_list.stdout }}\n"
        mode: '0644'

    - name: "Report the predicted change without applying it"
      ansible.builtin.debug:
        msg:
          - "would change: {{ sec_preview.changed }}"
          - "advisory lines: {{ sec_list.stdout_lines | length }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.dnf: name: '*' state: latest security: true` → Ask the *module* (no shell) to bring all packages to the latest version, but **only those with security errata** — this is the module-native form of `dnf upgrade --security`.
- `check_mode: true` → Force a dry run: the task computes what it *would* do and reports `changed`, but applies nothing — the safe equivalent of `--assumeno`.
- `ansible.builtin.command: dnf updateinfo list security` → Capture the human-readable RHSA listing, again with `changed_when: false` and the rc-100-safe `failed_when`.
- `ansible.builtin.debug: msg: [...]` → Print whether a real run would change the box and how many advisory lines were found.

**New words in this step:**

- **`check_mode`** — Ansible's dry-run flag; a task in check mode predicts changes without making them.
- **`security: true`** — the `dnf` module option that restricts `state: latest` to packages fixing security advisories.

---

### Step 2 of 2 — Run it twice and confirm nothing is patched

**In plain English:** We run the preview playbook two times; the `dnf` task reports `changed=1` (it *would* patch) but `check_mode` means the system is untouched, so re-running gives the same prediction — and the box is never mutated.

```bash
ansible-playbook /root/rhcsa_journal/lab-217b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-217b/playbooks/task2.yml
cat /tmp/lab-217/security-advisories.txt
echo "exit was: $?"
```

**Expected output:**

```
TASK [Report the predicted change without applying it] ***********************
ok: [localhost] => {
    "msg": [
        "would change: True",
        "advisory lines: 2"
    ]
}
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=2    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=1    unreachable=0    failed=0
RHSA-2026:1234 Important/Sec.  openssl-3.2.2-6.el9_5.x86_64
RHSA-2026:1290 Moderate/Sec.   sudo-1.9.5p2-10.el9_5.x86_64
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run: the `dnf` task shows `changed` (it *would* patch) and `copy` writes the advisory file, so the recap shows `changed=2` — yet `check_mode` applied nothing.
- second `ansible-playbook ...` → Second run: the advisory file already matches so `copy` is `changed=0`, but the `dnf` check-mode prediction is still `changed=1` because the (never-applied) updates remain pending.
- `cat /tmp/lab-217/security-advisories.txt` → Confirm the saved RHSA listing; the system itself is still unpatched, exactly as intended.

**New words in this step:**

- **predicted change** — what a `check_mode` task says it *would* do; it counts toward the `changed` recap without altering the host.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.dnf security: true` | upgrades only security-errata packages | without `check_mode` it would actually patch |
| `check_mode: true` | dry-runs the task, applies nothing | `changed=1` here is a *prediction*, not a real change |
| re-run stays `changed` | updates were never applied | non-idempotence here is correct — it is a preview |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Box actually got patched | `check_mode: true` missing on the `dnf` task | Add `check_mode: true` to keep it a preview |
| `updateinfo list security` empty | Repo without errata metadata | Use a repo that publishes RHSA data; `dnf makecache` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the rc-100-safe check-update playbook
- [ ] Task 1 · Step 2 — Run it twice and confirm it stays green (rc=100 handled)
- [ ] Task 2 · Step 1 — Write the `check_mode` security-preview playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm nothing is patched

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-217
```

These plays are **non-destructive**: `check-update` queries and the `dnf` task runs under `check_mode`, so no packages were installed and no system state needs reversing. Optionally remove the playbook folder with `rm -rf /root/rhcsa_journal/lab-217b`, and refresh metadata with `sudo dnf clean all` if you want a clean cache.

**Expected output:**

```
✅ Removed /tmp/lab-217 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `command: dnf check-update` with no `failed_when` | Play fails on every server that has updates | Add `failed_when: r.rc not in [0,100]` |
| Real `dnf: security: true` without `check_mode` | The host gets patched unintentionally | Add `check_mode: true` for a preview |
| Missing `changed_when: false` on queries | Read-only tasks report `changed=1` forever | Label queries with `changed_when: false` |

---

## 📌 Exam Strategy

RHCE patch questions hinge on two reflexes: never let `dnf check-update` fail a play (the rc-100 idiom), and never mutate a box you only meant to inspect (`check_mode`). Reach for the real `ansible.builtin.dnf` module — it speaks `security:` natively — over shelling out, and always attach `register:` + `debug:` so the recap tells the grader exactly what happened.

- Memorize `failed_when: result.rc not in [0, 100]` for any `dnf check-update` task.
- Use `check_mode: true` to preview a security upgrade; drop it (or run `--check` off) only when you truly intend to patch.
- Pair `changed_when: false` with read-only commands so the PLAY RECAP stays honest.

---

## 🔗 Related Labs

- [Lab 217a — Monitor Security Updates (RHCSA)](../lab-217a-monitor-security-updates-rhcsa/) — the hand-typed survey this play mirrors
- [Lab 217b — Monitor Security Updates (Ansible)](../lab-217b-monitor-security-updates-ansible/) — this lab: the rc-100 and check_mode idioms
- [Lab 217c — Monitor Security Updates (Verify)](../lab-217c-monitor-security-updates-verify/) — audit the reports both 217a and 217b produced
- [Lab 218b — Bastion Host Hardening (Ansible)](../lab-218b-bastion-host-ansible/) — the neighbor lab: automate hardening of the jump box you patch from

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
