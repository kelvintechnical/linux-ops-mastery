# Lab 218b: Build a Bastion Server (Ansible) — `ansible.builtin.systemd_service`, `ansible.builtin.service_facts`

**Series:** linux-ops-mastery — Security Administration · **Lab 218b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (managing units and reading service facts idempotently), RHCSA EX200 (the `systemctl enable`/`disable` behavior underneath), SRE/Security (fleet-wide SSH-only posture enforcement)  
**Prerequisite:** [Lab 218a](../lab-218a-build-bastion-server-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 218a's "add a throwaway listener, then trim it back to SSH-only" as an idempotent Ansible play. You will lay down a disposable socket+service unit with `ansible.builtin.copy`, bring it up declaratively with `ansible.builtin.systemd_service` (`enabled: true`, `state: started`, `daemon_reload: true`), and then *read the system back* with `ansible.builtin.service_facts` to confirm state from Ansible's own inventory rather than by eye. Task 2 reverses it to `enabled: false`, `state: stopped`, and proves `sshd` survived — all converging to `changed=0` on a re-run.

---

## 🧠 Concept

In the shell you `daemon-reload`, `enable --now`, and `disable --now` as imperative steps. Ansible turns those into a single desired-state declaration through `ansible.builtin.systemd_service`: `enabled:` controls the boot symlink, `state: started/stopped` controls whether it runs *now*, and `daemon_reload: true` re-reads freshly written unit files — all state-aware, so re-applying an already-correct state reports `changed=0`. To *verify* without shelling out, `ansible.builtin.service_facts` populates `ansible_facts.services`, a dictionary of every unit's `state`, which you can read in `debug:` to confirm the socket came up and that `sshd` is still running.

```
SHELL (218a)                              ANSIBLE (218b)
─────────────────────────────────        ───────────────────────────────────────
systemctl daemon-reload                   ansible.builtin.systemd_service:
systemctl enable --now extra.socket          name: lab218-extra.socket
                                             enabled: true
                                             state: started
                                             daemon_reload: true      → changed=1 then 0

ss -tlnp / systemctl is-active            ansible.builtin.service_facts:
                                          → ansible_facts.services['lab218-extra.socket'].state
```

> **Why this matters:** A grader re-runs your play and reads the recap; an idempotent `systemd_service` task converges and goes quiet (`changed=0`). And reading posture from `service_facts` — instead of parsing `ss` output by hand — is how you assert state portably across one host or a whole fleet.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.copy` | Declaratively write the socket/service unit files | `content:` inline text; `mode:` perms; idempotent |
| `ansible.builtin.systemd_service` | Manage a unit's enabled/running state | `enabled:`, `state:`, `daemon_reload:` |
| `ansible.builtin.service_facts` | Gather every unit's state into `ansible_facts.services` | no args; read results via `ansible_facts.services['name'].state` |
| `become: true` | Run with root privilege | required for any `systemctl` change |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, then create the durable folder that holds our playbooks under `/root` so they survive a reboot; the only system change the plays make is the harmless `lab218-extra` socket and service.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-218
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-218b/playbooks

ansible --version | head -2
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-218b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /tmp/lab-218
drwxr-xr-x. 2 root root 6 Jun 15 17:45 /root/rhcsa_journal/lab-218b/playbooks
Setup complete at 2026-06-15T17:45:08-04:00
exit was: 0
```

---

## TASK 1 of 2 — Deploy and enable a throwaway listener idempotently

**In plain English:** We write a playbook that lays down the disposable socket+service units, enables and starts the socket declaratively, then reads `service_facts` to confirm it is running — and run it twice to watch the second run report `changed=0`.

---

### Step 1 of 2 — Write the deploy-and-enable playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.copy` for both unit files and `ansible.builtin.systemd_service` to enable+start the socket (with `daemon_reload: true`), then prints the socket's state from gathered facts.

```yaml
---
- name: "Lab 218b Task 1 — deploy and enable a throwaway extra listener"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    socket_unit: /etc/systemd/system/lab218-extra.socket
    service_unit: /etc/systemd/system/lab218-extra.service

  tasks:
    - name: "Install the throwaway socket unit"
      ansible.builtin.copy:
        dest: "{{ socket_unit }}"
        content: |
          [Unit]
          Description=Lab 218 throwaway extra listener (safe to disable)

          [Socket]
          ListenStream=127.0.0.1:2189

          [Install]
          WantedBy=sockets.target
        mode: '0644'

    - name: "Install the paired throwaway service unit"
      ansible.builtin.copy:
        dest: "{{ service_unit }}"
        content: |
          [Unit]
          Description=Lab 218 throwaway service paired with lab218-extra.socket

          [Service]
          ExecStart=/usr/bin/cat
          StandardInput=socket
        mode: '0644'

    - name: "Enable and start the extra socket (daemon_reload picks up new units)"
      ansible.builtin.systemd_service:
        name: lab218-extra.socket
        enabled: true
        state: started
        daemon_reload: true

    - name: "Read current service/socket state into facts"
      ansible.builtin.service_facts:

    - name: "Show the extra socket's reported state"
      ansible.builtin.debug:
        msg: "lab218-extra.socket state: {{ ansible_facts.services['lab218-extra.socket'].state | default('unknown') }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `become: true` → Writing to `/etc/systemd/system` and changing unit state both require root.
- two `ansible.builtin.copy` tasks → Declaratively write the **socket** unit (listens on `127.0.0.1:2189`) and its paired **service** unit; idempotent, so they only rewrite if the content differs.
- `ansible.builtin.systemd_service: enabled: true / state: started / daemon_reload: true` → Create the boot symlink, start it now, and re-read unit files first — the module equivalent of `daemon-reload` + `enable --now`.
- `ansible.builtin.service_facts:` → Populate `ansible_facts.services` so the next task can read the socket's state without shelling out.
- `ansible.builtin.debug: ... ansible_facts.services[...].state` → Print the gathered state; `| default('unknown')` keeps the play from erroring if the key is absent.

**New words in this step:**

- **`ansible.builtin.service_facts`** — a module that gathers every unit's state into `ansible_facts.services` for portable, scriptable checks.
- **socket unit** — a systemd unit that listens on a port/path and launches its paired service on demand (socket activation).

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the saved playbook two times; the first run writes the units and starts the socket (`changed=1`), and the second sees everything already in the desired state (`changed=0`) while reporting the socket as `running`.

```bash
ansible-playbook /root/rhcsa_journal/lab-218b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-218b/playbooks/task1.yml
sudo ss -tlnp | grep 2189
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the extra socket's reported state] *******************************
ok: [localhost] => {
    "msg": "lab218-extra.socket state: running"
}
PLAY RECAP *********************************************************************
localhost                  : ok=5    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=5    changed=0    unreachable=0    failed=0
LISTEN 0      4096       127.0.0.1:2189       0.0.0.0:*    users:(("systemd",pid=1,fd=...))
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run writes both units and enables+starts the socket; `changed=1`.
- second `ansible-playbook ...` → Second run finds the files correct and the socket already running, so it makes no change; `changed=0` — the idempotence proof.
- `sudo ss -tlnp | grep 2189` → Confirm out-of-band that the extra listener really is bound on `127.0.0.1:2189`.

**New words in this step:**

- **PLAY RECAP** — Ansible's end-of-run summary of `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `daemon_reload: true` | re-reads new/edited unit files | omit it after `copy` and the unit may be "not found" |
| `state: started` | ensures the unit runs now | `enabled: true` alone does not start it |
| `service_facts` | reads every unit's state into facts | key access errors if the unit name is wrong — use `default()` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not find the requested service` | Units written but not reloaded | Set `daemon_reload: true` on the `systemd_service` task |
| `state: unknown` in the debug line | Wrong unit key or facts not gathered | Run `service_facts` before the debug; check the exact unit name |

---

## TASK 2 of 2 — Disable the listener and confirm SSH-only

**In plain English:** We rewrite the trim step declaratively with `enabled: false` and `state: stopped`, re-read `service_facts`, and prove `sshd` is still running — the SSH-only posture, converging to `changed=0`.

---

### Step 1 of 2 — Write the disable playbook

**In plain English:** We create `task2.yml`, which sets the throwaway socket to `enabled: false`, `state: stopped`, then gathers facts and prints `sshd`'s state to confirm the one required service survived.

```yaml
---
- name: "Lab 218b Task 2 — disable the extra listener (back to SSH-only)"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Disable and stop the throwaway extra socket"
      ansible.builtin.systemd_service:
        name: lab218-extra.socket
        enabled: false
        state: stopped

    - name: "Re-read service/socket state into facts"
      ansible.builtin.service_facts:

    - name: "Confirm the one required service (sshd) is still running"
      ansible.builtin.debug:
        msg: "sshd state: {{ ansible_facts.services['sshd.service'].state | default('unknown') }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.systemd_service: enabled: false / state: stopped` → Remove the boot symlink and stop the socket now — the declarative `disable --now`.
- `ansible.builtin.service_facts:` → Re-gather unit states so we can read `sshd` after the change.
- `ansible.builtin.debug: ... ['sshd.service'].state` → Print `sshd`'s state to prove we trimmed the *extra* listener, not the service the bastion exists for.

**New words in this step:**

- **convergence** — repeatedly applying a declarative play until the system reaches and holds the desired state, then reporting `changed=0`.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the disable playbook twice; the first run stops and disables the socket (`changed=1`), and the second finds it already stopped+disabled (`changed=0`), with `sshd` reported `running` both times.

```bash
ansible-playbook /root/rhcsa_journal/lab-218b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-218b/playbooks/task2.yml
sudo ss -tlnp | grep 2189 || echo "no extra listener (OK)"
echo "exit was: $?"
```

**Expected output:**

```
TASK [Confirm the one required service (sshd) is still running] *************
ok: [localhost] => {
    "msg": "sshd state: running"
}
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
no extra listener (OK)
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run stops and disables the socket; `changed=1`.
- second `ansible-playbook ...` → Second run finds it already stopped and disabled, so it does nothing; `changed=0` — the idempotence proof.
- `sudo ss -tlnp | grep 2189 || echo "no extra listener (OK)"` → Confirm the `:2189` doorway is closed; `grep` finding nothing fires the `||` branch.

**New words in this step:**

- **SSH-only posture** — a host whose sole listening service is `sshd`; the bastion ideal, now confirmed via facts and `ss`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `enabled: false` + `state: stopped` | the declarative `disable --now` | omitting `state` leaves a running socket disabled-but-up |
| `service_facts` re-read | reflects state *after* the change | gather again post-change, not just once |
| idempotent disable | re-run is `changed=0` | proves convergence, not that nothing happened |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `:2189` still listed after the play | `state: stopped` missing on the task | Add `state: stopped` so the socket is brought down now |
| `sshd state: unknown` | `sshd.service` not present or facts stale | Re-run `service_facts`; confirm `sshd` is installed/enabled |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the deploy-and-enable playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the disable playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it installed and enabled a socket+service), and `rm` alone will NOT undo the daemon registration. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo systemctl disable --now lab218-extra.socket 2>/dev/null
sudo rm -f /etc/systemd/system/lab218-extra.socket /etc/systemd/system/lab218-extra.service
sudo systemctl daemon-reload
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-218
```

**Expected output:**

```
✅ Removed /tmp/lab-218 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `ansible.builtin.shell: systemctl ...` | `changed=1` on every run | Use `ansible.builtin.systemd_service` for state-aware changes |
| Forgetting `become: true` | `Permission denied` on `systemctl` | Add `become: true` to the play |
| Reading posture by parsing `ss` in a play | Brittle string parsing | Use `service_facts` and read `ansible_facts.services` |

---

## 📌 Exam Strategy

The RHCE question is "ensure this service is up/down and stays that way," not "type `systemctl` once." Express boot+run state with `ansible.builtin.systemd_service` so the play converges and re-runs cleanly, and verify with `service_facts` rather than scraping command output. Always run the play twice and read the PLAY RECAP.

- Pair `enabled:` (boot) with `state:` (now) — they answer different questions.
- Set `daemon_reload: true` whenever a task follows a `copy` of a new unit.
- Read posture from `ansible_facts.services` for portable, fleet-wide checks.

---

## 🔗 Related Labs

- [Lab 218a — Build a Bastion Server (RHCSA)](../lab-218a-build-bastion-server-rhcsa/) — the hand-typed `systemctl` version this play mirrors
- [Lab 218c — Build a Bastion Server (Verify)](../lab-218c-build-bastion-server-verify/) — prove the SSH-only posture with scripted OK/FAIL assertions
- [Lab 216b — Service Isolation Bastion Host (Ansible)](../lab-216b-service-isolation-bastion-host-ansible/) — the disable/mask discipline that feeds this hardening

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
