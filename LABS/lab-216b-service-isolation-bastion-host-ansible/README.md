# Lab 216b: Service Isolation Bastion Host (Ansible) — `ansible.builtin.systemd_service`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — Security Administration · **Lab 216b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (managing service boot state idempotently with `ansible.builtin.systemd_service`), RHCSA EX200 (the `systemctl enable`/`disable`/`mask` behavior underneath), SRE/Security (fleet-wide attack-surface reduction)  
**Prerequisite:** [Lab 216a](../lab-216a-service-isolation-bastion-host-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 216a's "install a harmless unit, then disable and mask it" as an idempotent Ansible play. You will use `ansible.builtin.copy` to lay down the throwaway `lab216-dummy.service`, then `ansible.builtin.systemd_service` to express boot state declaratively — `enabled: true` to create the boot symlink and `masked: true` to symlink the unit to `/dev/null`. Running each play twice proves the win condition: the second run reports `changed=0` because systemd is already in the desired state.

---

## 🧠 Concept

In the shell you run `systemctl enable`, `disable`, and `mask` as imperative one-shot commands. Ansible turns those into *desired-state* declarations through `ansible.builtin.systemd_service`: `enabled: true/false` controls the boot symlink, `masked: true/false` controls the `/dev/null` symlink, and `state:` controls running/stopped — all state-aware, so re-applying an already-correct state reports `changed=0`. Because masking is just "the unit is symlinked to `/dev/null`," `masked: true` on an already-masked unit is a no-op, which is exactly the idempotence a grader re-running your play looks for.

```
SHELL (216a)                         ANSIBLE (216b)
─────────────────────────────       ──────────────────────────────────────
systemctl enable dummy.service       ansible.builtin.systemd_service:
                                        name: lab216-dummy.service
                                        enabled: true       → changed=1 then 0

systemctl mask dummy.service         ansible.builtin.systemd_service:
                                        name: lab216-dummy.service
                                        masked: true        → changed=1 then 0
                                        state: stopped
```

> **Why this matters:** RHCE graders re-run your play and read the PLAY RECAP. Expressing "this service must be masked" declaratively means the play converges to the right state and stays quiet (`changed=0`) on every subsequent run — across one bastion or a thousand. That convergence is the whole reason to reach for `systemd_service` instead of `ansible.builtin.shell: systemctl mask ...`.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.copy` | Declaratively lay down the unit file's exact contents | `content:` for inline text; `mode:` sets perms; idempotent |
| `ansible.builtin.systemd_service` | Manage a unit's enabled/masked/running state | `enabled:`, `masked:`, `state:`, `daemon_reload:` |
| `daemon_reload: true` | Re-read unit files after writing a new one | needed once after `copy` installs the unit |
| `become: true` | Run the play with root privilege | required for any `systemctl` change |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, then create the durable folder that will hold our playbooks. The playbooks live under `/root` so they survive a reboot; the only thing they touch on the system is the harmless `lab216-dummy.service` unit.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-216
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-216b/playbooks

ansible --version | head -2
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-216b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root  6 Jun 15 17:45 /tmp/lab-216
drwxr-xr-x. 2 root root  6 Jun 15 17:45 /root/rhcsa_journal/lab-216b/playbooks
Setup complete at 2026-06-15T17:45:09-04:00
exit was: 0
```

---

## TASK 1 of 2 — Install the dummy unit and enable it idempotently

**In plain English:** We write a playbook that lays down the harmless unit with `ansible.builtin.copy` and enables it with `ansible.builtin.systemd_service`, then run it twice to watch the second run report `changed=0` — the declarative way to put a service into the boot attack surface.

---

### Step 1 of 2 — Write the install-and-enable playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.copy` to write the dummy unit file and `ansible.builtin.systemd_service` with `enabled: true` to create its boot symlink, capturing both results so the idempotence is readable.

```yaml
---
- name: "Lab 216b Task 1 — install + enable the harmless dummy unit"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    unit_path: /etc/systemd/system/lab216-dummy.service
  tasks:
    - name: "Write the harmless dummy unit file"
      ansible.builtin.copy:
        dest: "{{ unit_path }}"
        mode: '0644'
        content: |
          [Unit]
          Description=Lab 216 harmless dummy service (safe to enable/disable/mask)

          [Service]
          Type=oneshot
          ExecStart=/bin/true
          RemainAfterExit=yes

          [Install]
          WantedBy=multi-user.target
      register: unit_file

    - name: "Enable the dummy unit (create the boot symlink)"
      ansible.builtin.systemd_service:
        name: lab216-dummy.service
        enabled: true
        daemon_reload: true
      register: enable_result

    - name: "Show whether anything changed"
      ansible.builtin.debug:
        msg:
          - "unit file changed: {{ unit_file.changed }}"
          - "enable changed:    {{ enable_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `become: true` → Run with root privilege; writing to `/etc/systemd/system` and changing service state both require it.
- `ansible.builtin.copy: dest/content/mode` → Declaratively write the harmless unit file; `content:` holds the inline unit text and `mode: '0644'` sets its permissions — idempotent, so it only rewrites if the file differs.
- `ansible.builtin.systemd_service: enabled: true` → Create the `WantedBy` boot symlink (the module equivalent of `systemctl enable`); `daemon_reload: true` makes systemd re-read the freshly written unit first.
- `register:` + `ansible.builtin.debug:` → Capture and print each task's `changed` flag so the double-run idempotence is visible.

**New words in this step:**

- **`ansible.builtin.systemd_service`** — the module that manages a unit's enabled, masked, and running state declaratively.
- **idempotence** — running something twice leaves the same end state with no extra change reported (`changed=0` on a re-run is the proof).

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the saved playbook two times; the first run writes the unit and enables it (`changed=1`), and the second sees everything already in the desired state and does nothing (`changed=0`).

```bash
ansible-playbook /root/rhcsa_journal/lab-216b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-216b/playbooks/task1.yml
systemctl is-enabled lab216-dummy.service
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
enabled
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run writes the unit file and creates the boot symlink; `changed=1`.
- second `ansible-playbook ...` → Second run finds the file already correct and the unit already enabled, so it makes no change; `changed=0` — the idempotence proof.
- `systemctl is-enabled lab216-dummy.service` → Confirm out-of-band that the unit really is `enabled`.

**New words in this step:**

- **PLAY RECAP** — the summary line Ansible prints at the end, reporting `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.copy` with `content:` | declaratively writes the unit file | re-run is `changed=0` only if content matches byte-for-byte |
| `enabled: true` | creates the boot symlink | does **not** start the unit (add `state: started`) |
| `daemon_reload: true` | re-reads unit files | omit it after a `copy` and you may get "unit not found" |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not find the requested service` | The unit wasn't reloaded | Add `daemon_reload: true` to the `systemd_service` task |
| Second run still `changed=1` on copy | Content/newline mismatch | Match `content:` exactly, including the final newline |

---

## TASK 2 of 2 — Disable then mask for true isolation

**In plain English:** We rewrite the strongest isolation step — masking — declaratively with `masked: true` plus `state: stopped`, then prove that re-running the play reports `changed=0` because the unit is already symlinked to `/dev/null`.

---

### Step 1 of 2 — Write the mask playbook

**In plain English:** We create `task2.yml`, which uses `ansible.builtin.systemd_service` with `masked: true` and `state: stopped` to symlink the unit to `/dev/null` and ensure it is not running — the declarative equivalent of `systemctl mask`.

```yaml
---
- name: "Lab 216b Task 2 — disable then mask the dummy unit (true isolation)"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  tasks:
    - name: "Mask the dummy unit and ensure it is stopped"
      ansible.builtin.systemd_service:
        name: lab216-dummy.service
        masked: true
        state: stopped
      register: mask_result

    - name: "Show whether the mask changed anything"
      ansible.builtin.debug:
        msg: "mask changed: {{ mask_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `masked: true` → Symlink the unit to `/dev/null` (the module equivalent of `systemctl mask`); a masked unit cannot be started, which is the strongest isolation.
- `state: stopped` → Ensure the unit is not currently running, so masking is paired with an actually-down service.
- `register:` + `ansible.builtin.debug:` → Capture and print the `changed` flag so the second-run `changed=0` is readable.

**New words in this step:**

- **mask** — symlink a unit to `/dev/null` so systemd refuses to load or start it; reversible only with `unmask` (or `masked: false`).
- **declarative** — you describe the desired end state and the tool figures out whether any action is needed.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the mask playbook twice; the first run masks and stops the unit (`changed=1`), and the second sees it already masked at `/dev/null` and does nothing (`changed=0`) — convergence on the strongest isolation state.

```bash
ansible-playbook /root/rhcsa_journal/lab-216b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-216b/playbooks/task2.yml
systemctl is-enabled lab216-dummy.service
ls -l /etc/systemd/system/lab216-dummy.service
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
masked
lrwxrwxrwx. 1 root root 9 Jun 15 17:46 /etc/systemd/system/lab216-dummy.service -> /dev/null
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run symlinks the unit to `/dev/null` and ensures it is stopped; `changed=1`.
- second `ansible-playbook ...` → Second run finds the unit already masked and stopped, so it makes no change; `changed=0` — the idempotence proof for masking.
- `systemctl is-enabled lab216-dummy.service` / `ls -l ...` → Confirm out-of-band that the state is `masked` and the unit path now points at `/dev/null`.

**New words in this step:**

- **convergence** — repeatedly applying a declarative play until the system reaches and holds the desired state, reporting `changed=0` thereafter.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `masked: true` | symlinks the unit to `/dev/null` | a masked unit can't be started until `masked: false` |
| `state: stopped` | ensures the unit is not running | masking does not by itself stop a running unit |
| idempotent mask | re-run is `changed=0` | proves the play converged, not that nothing happened |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Cannot enable/start, unit is masked` later | The unit is still masked | Set `masked: false` (or `enabled: true`) to reverse it |
| Second run still `changed=1` | Another task keeps flipping state | Ensure only one play owns this unit's state |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the install-and-enable playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the mask playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it masked, enabled, and installed a unit file), and `rm` alone will NOT undo a mask or daemon registration. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo systemctl unmask lab216-dummy.service
sudo systemctl disable --now lab216-dummy.service
sudo rm -f /etc/systemd/system/lab216-dummy.service /etc/systemd/system/lab216-dummy.socket
sudo systemctl daemon-reload
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-216
```

**Expected output:**

```
✅ Removed /tmp/lab-216 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `ansible.builtin.shell: systemctl mask` | `changed=1` every run | Use `ansible.builtin.systemd_service` with `masked: true` |
| Forgetting `become: true` | `Permission denied` on `systemctl` | Add `become: true` to the play |
| Skipping `daemon_reload` after `copy` | `Could not find the requested service` | Set `daemon_reload: true` on the enable task |

---

## 📌 Exam Strategy

The RHCE question is "make sure this service is off and stays off," not "type `systemctl mask` once." Express boot state with `ansible.builtin.systemd_service` (`enabled:`, `masked:`, `state:`) so the play converges and re-runs cleanly, and reserve `ansible.builtin.shell` for the rare action no module covers. Always run the play twice and read the PLAY RECAP.

- Use `masked: true` for "must never start," `enabled: false` for "just don't auto-start."
- Run every play twice; `changed=0` on the second run is the acceptance test.
- Pair `masked: true` with `state: stopped` so a currently-running unit is actually brought down.

---

## 🔗 Related Labs

- [Lab 216a — Service Isolation Bastion Host (RHCSA)](../lab-216a-service-isolation-bastion-host-rhcsa/) — the hand-typed `systemctl` version this play mirrors
- [Lab 216c — Service Isolation Bastion Host (Verify)](../lab-216c-service-isolation-bastion-host-verify/) — audit the enabled → disabled → masked transitions with hard evidence
- [Lab 218b — Build a Bastion Host (Ansible)](../lab-218b-build-bastion-host-ansible/) — roll this isolation into a full hardened jump-host playbook

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
