# Lab 220b: PAM and SELinux with FTP (Ansible) — `ansible.posix.seboolean`, `ansible.builtin.lineinfile`

**Series:** linux-ops-mastery — Security Administration · **Lab 220b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (`ansible.posix.seboolean`, `ansible.builtin.dnf`/`systemd_service`/`lineinfile`), RHCSA EX200 (the `setsebool -P` and `ftpusers` behavior underneath), Security+/SRE (declarative defense-in-depth)  
**Prerequisite:** [Lab 220a](../lab-220a-pam-selinux-ftp-rhcsa/) completed, a working Ansible control node, and the `ansible.posix` collection (`ansible-galaxy collection install ansible.posix`)  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Intermediate

---

## 🎯 Objective

Express Lab 220a's FTP hardening as an idempotent Ansible play. You will install and enable `vsftpd` with real modules, flip the `ftp_home_dir` SELinux boolean persistently with `ansible.posix.seboolean` (`persistent: true` is the module's `setsebool -P`), and manage the `/etc/vsftpd/ftpusers` PAM deny list with `ansible.builtin.lineinfile` so exactly one matching line is guaranteed present. Running each play twice proves the win condition: the second run reports `changed=0` because the service, the boolean, and the deny-list line are already in the desired state.

---

## 🧠 Concept

The three layers from 220a map cleanly onto three idempotent modules. `ansible.builtin.dnf` (`state: present`) ensures the package; `ansible.builtin.systemd_service` (`enabled: true`, `state: started`) ensures the service is up and persistent. SELinux is the subtle one: `ansible.posix.seboolean` with `persistent: true` is the declarative `setsebool -P` — it sets the boolean in policy so it survives a reboot, and reports `changed=0` once it is already on. For PAM access control, `ansible.builtin.lineinfile` ensures a username is present in `/etc/vsftpd/ftpusers` exactly once — re-running never adds a duplicate, which is the whole point of a *desired-state* edit versus a blind `echo >>`.

```
SHELL (220a)                          ANSIBLE (220b)
─────────────────────────────        ──────────────────────────────────────────
dnf install -y vsftpd                 ansible.builtin.dnf: { name: vsftpd, state: present }
systemctl enable --now vsftpd         ansible.builtin.systemd_service:
                                         name: vsftpd, enabled: true, state: started
setsebool -P ftp_home_dir on          ansible.posix.seboolean:
                                         name: ftp_home_dir, state: true, persistent: true
echo labghost220 >> .../ftpusers      ansible.builtin.lineinfile:
   (adds a DUPLICATE every run)          path: /etc/vsftpd/ftpusers, line: labghost220
                                         └─ exactly one line, changed=0 on re-run
```

> **Why this matters:** A grader re-runs your play; `echo >>` would pile up duplicate `ftpusers` lines and a non-`-P` boolean would silently revert on reboot. `seboolean persistent: true` and `lineinfile` are how you express "this must be true and stay true" instead of "do this action again."

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.dnf` | Ensure the `vsftpd` package is installed | `state: present` (or `latest`) |
| `ansible.builtin.systemd_service` | Enable + start the service declaratively | `enabled: true`, `state: started` |
| `ansible.posix.seboolean` | Set an SELinux boolean idempotently | `state: true`, `persistent: true` (= `setsebool -P`) |
| `ansible.builtin.lineinfile` | Guarantee exactly one matching line in a file | `path:`, `line:`, `state: present` |
| `ansible.builtin.copy` (`remote_src`, `force: false`) | Back up a file once, never overwriting it | `force: false` keeps the first backup |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible and the `ansible.posix` collection are present, create the durable playbook folder under `/root`, and define the `/tmp` sandbox root; the plays themselves install `vsftpd` and edit FTP security files, all reversed in Teardown.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-220
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-220b/playbooks

ansible --version | head -2
ansible-galaxy collection list ansible.posix | grep ansible.posix \
  || ansible-galaxy collection install ansible.posix
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-220b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
ansible.posix 1.5.4
drwxr-xr-x. 2 root root 6 Jun 15 18:00 /tmp/lab-220
drwxr-xr-x. 2 root root 6 Jun 15 18:00 /root/rhcsa_journal/lab-220b/playbooks
Setup complete at 2026-06-15T18:00:08-04:00
exit was: 0
```

---

## TASK 1 of 2 — Install vsftpd and set the SELinux boolean idempotently

**In plain English:** We write a playbook that installs `vsftpd`, enables+starts it, and turns `ftp_home_dir` on persistently, then run it twice to watch the second run report `changed=0`.

---

### Step 1 of 2 — Write the install-enable-seboolean playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.dnf`, `ansible.builtin.systemd_service`, and `ansible.posix.seboolean` (`persistent: true`) to converge the FTP service and the SELinux boolean on the desired state.

```yaml
---
- name: "Lab 220b Task 1 — vsftpd up + ftp_home_dir boolean on"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true

  tasks:
    - name: "Install the vsftpd package"
      ansible.builtin.dnf:
        name: vsftpd
        state: present

    - name: "Enable and start vsftpd (now and at boot)"
      ansible.builtin.systemd_service:
        name: vsftpd
        enabled: true
        state: started

    - name: "Turn the ftp_home_dir SELinux boolean ON, persistently"
      ansible.posix.seboolean:
        name: ftp_home_dir
        state: true
        persistent: true
      register: sebool_result

    - name: "Show whether the boolean changed"
      ansible.builtin.debug:
        msg: "ftp_home_dir changed: {{ sebool_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.dnf: name: vsftpd state: present` → Ensure the package is installed; `present` is idempotent (no change if it is already there).
- `ansible.builtin.systemd_service: enabled: true state: started` → The declarative `systemctl enable --now vsftpd`: running now and at boot.
- `ansible.posix.seboolean: name: ftp_home_dir state: true persistent: true` → Set the boolean on in policy; `persistent: true` is the module's `setsebool -P`, so it survives a reboot — and reports `changed=0` once already on.
- `register:` + `ansible.builtin.debug:` → Capture and print the boolean task's `changed` flag so the idempotence is visible.

**New words in this step:**

- **`ansible.posix.seboolean`** — the module that sets SELinux booleans declaratively; `persistent: true` writes the change to policy.
- **idempotence** — running something twice leaves the same end state with no extra change reported.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the saved playbook two times; the first run installs/enables/sets (`changed>=1`), and the second finds everything already in the desired state (`changed=0`), confirmed by `getsebool`.

```bash
ansible-playbook /root/rhcsa_journal/lab-220b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-220b/playbooks/task1.yml
getsebool ftp_home_dir
systemctl is-active vsftpd
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=2    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=0    unreachable=0    failed=0
ftp_home_dir --> on
active
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run installs/enables vsftpd and turns the boolean on; the recap shows `changed`.
- second `ansible-playbook ...` → Second run finds the package present, the service running, and the boolean already on, so it makes no change; `changed=0` — the idempotence proof.
- `getsebool ftp_home_dir` / `systemctl is-active vsftpd` → Confirm out-of-band that the boolean is `on` and the service is `active`.

**New words in this step:**

- **PLAY RECAP** — Ansible's end-of-run summary of `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `seboolean persistent: true` | the declarative `setsebool -P` | `persistent: false` reverts on reboot |
| `systemd_service` enabled+started | runs now and at boot | `enabled` alone does not start it |
| `dnf state: present` | ensures the package | `latest` would also upgrade it — different intent |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `seboolean` module not found | `ansible.posix` collection missing | `ansible-galaxy collection install ansible.posix` |
| Boolean reverts after reboot | `persistent: true` omitted | Add `persistent: true` to the `seboolean` task |

---

## TASK 2 of 2 — Manage the ftpusers deny list idempotently

**In plain English:** We rewrite the deny-list edit with `ansible.builtin.lineinfile` so exactly one matching line is guaranteed present, back the file up once, then prove the re-run reports `changed=0` — no duplicate lines ever.

---

### Step 1 of 2 — Write the lineinfile deny-list playbook

**In plain English:** We create `task2.yml`, which backs up `ftpusers` once with `copy` (`force: false`), then uses `ansible.builtin.lineinfile` to ensure the denied username is present exactly once.

```yaml
---
- name: "Lab 220b Task 2 — add an account to the ftpusers deny list"
  hosts: localhost
  connection: local
  gather_facts: false
  become: true
  vars:
    denied_user: labghost220

  tasks:
    - name: "Back up ftpusers once before editing (idempotent via creates:)"
      ansible.builtin.copy:
        src: /etc/vsftpd/ftpusers
        dest: /etc/vsftpd/ftpusers.lab220.bak
        remote_src: true
        force: false

    - name: "Ensure the account is present in the ftpusers deny list"
      ansible.builtin.lineinfile:
        path: /etc/vsftpd/ftpusers
        line: "{{ denied_user }}"
        state: present
      register: deny_result

    - name: "Show whether the deny list changed"
      ansible.builtin.debug:
        msg: "ftpusers changed: {{ deny_result.changed }} (denied: {{ denied_user }})"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.copy: ... force: false` → Make a one-time backup of `ftpusers`; `remote_src: true` copies a file already on the target, and `force: false` means "do not overwrite if the backup already exists," so re-runs never clobber the original snapshot.
- `ansible.builtin.lineinfile: path/line/state: present` → Guarantee `labghost220` appears in the file exactly once; if it is already there, nothing changes — unlike `echo >>`, which would append a duplicate every run.
- `register:` + `ansible.builtin.debug:` → Capture and print whether the deny list changed.

**New words in this step:**

- **`ansible.builtin.lineinfile`** — ensures a single line is present (or absent) in a file, idempotently.
- **`force: false`** — tells `copy` not to overwrite an existing destination, preserving the first backup.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the deny-list playbook twice; the first run adds the line (`changed=1`), and the second sees it already present and does nothing (`changed=0`), with no duplicate line in the file.

```bash
ansible-playbook /root/rhcsa_journal/lab-220b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-220b/playbooks/task2.yml
grep -c '^labghost220$' /etc/vsftpd/ftpusers
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
1
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run backs up the file and adds the deny line; `changed=2` (backup created + line added).
- second `ansible-playbook ...` → Second run: the backup already exists (`force: false` skips it) and the line is already present, so `changed=0` — the idempotence proof.
- `grep -c '^labghost220$' /etc/vsftpd/ftpusers` → Count exact matches; the answer is `1`, proving `lineinfile` did **not** create a duplicate (an `echo >>` loop would print `2`).

**New words in this step:**

- **duplicate-safety** — `lineinfile` guarantees one matching line, so re-runs cannot pile up repeats.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `lineinfile state: present` | exactly one matching line | `echo >>` appends a duplicate every run |
| `copy force: false` | one-time backup | default `force: true` would re-copy each run |
| deny semantics | listed = blocked from FTP | adding a line *removes* access, not grants it |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `grep -c` returns `2` | A prior `echo >>` added a duplicate | Remove dupes; let `lineinfile` own the line |
| Backup keeps getting overwritten | `force:` left at default `true` | Set `force: false` to keep the first backup |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the install-enable-seboolean playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=0` on the re-run
- [ ] Task 2 · Step 1 — Write the lineinfile deny-list playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (installed/enabled a service, set a persistent SELinux boolean, edited a PAM-controlled file), and `rm` will NOT undo those. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo setsebool -P ftp_home_dir off
sudo systemctl disable --now vsftpd
# Restore the original ftpusers from the playbook's one-time backup:
sudo cp -a /etc/vsftpd/ftpusers.lab220.bak /etc/vsftpd/ftpusers && sudo rm -f /etc/vsftpd/ftpusers.lab220.bak
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-220
```

> Optional: `sudo dnf remove -y vsftpd` if it was not already required by the system.

**Expected output:**

```
✅ Removed /tmp/lab-220 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| `seboolean` without `persistent: true` | Boolean reverts on reboot | Always set `persistent: true` for durable policy |
| Using `shell: echo >> ftpusers` | Duplicate lines accumulate each run | Use `ansible.builtin.lineinfile` for a single managed line |
| Forgetting `become: true` | `Permission denied` editing `/etc/vsftpd` | Add `become: true` to the play |

---

## 📌 Exam Strategy

The RHCE question is "ensure FTP is configured and stays configured," not "run these commands once." Use real modules — `dnf`, `systemd_service`, `seboolean` (`persistent: true`), and `lineinfile` — so the play converges and re-runs cleanly. Reserve `ansible.builtin.shell` for what no module covers, and always run the play twice and read the recap.

- `seboolean persistent: true` is the only way to make a boolean survive reboot in a play.
- `lineinfile` beats `shell: echo >>` because it cannot create duplicates.
- Back up config with `copy force: false` so the first snapshot is never clobbered.

---

## 🔗 Related Labs

- [Lab 220a — PAM and SELinux with FTP (RHCSA)](../lab-220a-pam-selinux-ftp-rhcsa/) — the hand-typed `setsebool`/`ftpusers` work this play mirrors
- [Lab 220c — PAM and SELinux with FTP (Verify)](../lab-220c-pam-selinux-ftp-verify/) — prove the boolean, service, and deny list with hard assertions
- [Lab 219b — Comprehensive firewalld Setup (Ansible)](../lab-219b-comprehensive-firewalld-setup-ansible/) — the network-layer guard that complements these host-layer controls

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
