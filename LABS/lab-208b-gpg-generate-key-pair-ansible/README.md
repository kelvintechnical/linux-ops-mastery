# Lab 208b: Generate a GPG Key Pair (Ansible) — `ansible.builtin.shell` + `creates:`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 208b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (driving shell-only tools idempotently with `creates:`), RHCSA EX200 (the key-generation behavior underneath), SRE/DevOps (unattended key provisioning in CI and config management)  
**Prerequisite:** [Lab 208a](../lab-208a-gpg-generate-key-pair-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 208a's unattended key generation in Ansible and learn the boundary it exposes: GnuPG has **no `ansible.builtin` module**, so `ansible.builtin.shell` is the only honest way to run `gpg --batch --gen-key` from a play — and a bare `shell:` task reports `changed=1` on every run. You will make it honest with the `creates:` guard (so the second run is `changed=0`), write the batch parameter file declaratively with `ansible.builtin.copy`, and keep read-only listing tasks truthful with `changed_when: false`.

---

## 🧠 Concept

Key generation is a one-time, stateful action that GnuPG performs through its own binary — there is no module that "owns" a keyring the way `ansible.builtin.copy` owns a file's contents. So to generate a key from a play you must shell out. The risk is that `ansible.builtin.shell` is **not idempotent**: Ansible cannot tell whether the key already exists, so it would regenerate (and report `changed=1`) forever. The fix is the **`creates:`** argument — you name a file the command produces (here `pubring.kbx`), and Ansible skips the task once that marker exists. Listing keys, by contrast, changes nothing, so those tasks use `ansible.builtin.command` with `changed_when: false` to keep the PLAY RECAP honest.

```
SHELL (208a)                              ANSIBLE (208b)
────────────────────────────────         ──────────────────────────────────────────
gpg --batch --gen-key keyparams           ansible.builtin.shell: gpg --batch --gen-key ...
                                             args: { creates: <gnupghome>/pubring.kbx }
                                             └─ changed=1 first run, changed=0 after (guarded)

gpg --list-keys                            ansible.builtin.command: gpg --list-keys ...
                                             changed_when: false
                                             └─ changed=0 ALWAYS (pure read)
```

> **Why this matters:** RHCE graders re-run your play and read the recap. A key-generation task that says `changed=1` every time signals you forgot the `creates:` guard; a listing task that says `changed=1` signals a missing `changed_when: false`. Knowing *when* you are forced into `shell:` — and making it idempotent anyway — is exactly the judgment the exam tests.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.shell` | Run `gpg` through `/bin/bash` (no module owns key generation) | not idempotent on its own — pair with `args: creates:` |
| `args: creates: <file>` | Skip the shell task once the named file exists | the idempotence guard for any generative shell command |
| `environment: { GNUPGHOME: ... }` | Point GnuPG at the sandbox keyring per task | keeps keys out of the control node's real `~/.gnupg` |
| `ansible.builtin.copy` with `content:` | Write the batch `keyparams` file declaratively | idempotent — re-run is `changed=0` |
| `ansible.builtin.command` + `changed_when: false` | Run a read-only `gpg --list-keys` honestly | without it, every listing falsely reports `changed=1` |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, then create the durable folder that holds our playbooks and the `/tmp` sandbox they write into; the keyring itself is created by the play inside `/tmp/lab-208/gnupg`, so a single teardown wipes every key.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-208
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-208b/playbooks

ansible --version | head -2
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-208b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root  6 Jun 15 17:40 /tmp/lab-208
drwxr-xr-x. 2 root root  6 Jun 15 17:40 /root/rhcsa_journal/lab-208b/playbooks
Setup complete at 2026-06-15T17:40:05-04:00
exit was: 0
```

---

## TASK 1 of 2 — Generate the key pair idempotently with `shell:` + `creates:`

**In plain English:** We write a playbook that creates the sandbox keyring, drops the batch parameter file with `copy`, then shells out to `gpg --batch --gen-key` guarded by `creates:` — and run it twice to watch `changed=1` become `changed=0`.

---

### Step 1 of 2 — Write the guarded generation playbook

**In plain English:** We create `task1.yml`, which builds the keyring directory, writes `keyparams` declaratively, and generates the key with a `shell:` task that is made idempotent by a `creates:` marker.

```yaml
---
- name: "Lab 208b Task 1 — generate a GPG key pair (shell, guarded)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-208
    gnupghome: /tmp/lab-208/gnupg
    key_email: lab208@example.com
  tasks:
    - name: "Create the sandbox keyring directory (chmod 700)"
      ansible.builtin.file:
        path: "{{ gnupghome }}"
        state: directory
        mode: '0700'

    - name: "Write the batch parameter file (declarative, idempotent)"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/keyparams"
        mode: '0600'
        content: |
          %echo Generating a sandbox GPG key pair
          Key-Type: RSA
          Key-Length: 3072
          Subkey-Type: RSA
          Subkey-Length: 3072
          Name-Real: Lab 208 User
          Name-Email: {{ key_email }}
          Expire-Date: 1y
          Passphrase: labpass208
          %commit
          %echo done

    - name: "Generate the key pair (shell, because no module owns gpg)"
      ansible.builtin.shell: |
        gpg --batch --gen-key "{{ lab_root }}/keyparams"
      environment:
        GNUPGHOME: "{{ gnupghome }}"
      args:
        creates: "{{ gnupghome }}/pubring.kbx"
      register: gen_result

    - name: "Show what the generation task reported"
      ansible.builtin.debug:
        msg:
          - "changed: {{ gen_result.changed }}"
          - "skipped (already created): {{ gen_result.skipped | default(false) }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.file: state=directory mode='0700'` → Create the sandbox keyring with the strict `700` permissions GnuPG requires; idempotent, so it never re-reports a change.
- `ansible.builtin.copy: content: |` → Write the batch `keyparams` file the declarative way — the same parameters as 208a, but state-aware so a re-run is `changed=0`.
- `ansible.builtin.shell: gpg --batch --gen-key ...` → The only honest way to generate a key from a play; `environment: GNUPGHOME` keeps the key inside the sandbox.
- `args: creates: "{{ gnupghome }}/pubring.kbx"` → The idempotence guard — once the public keyring exists, Ansible skips this task instead of regenerating.
- `register: gen_result` + `debug:` → Capture and print whether the task ran or was skipped.

**New words in this step:**

- **`creates:`** — a `shell`/`command` argument naming a file the task produces; if it already exists, Ansible skips the task, giving an otherwise non-idempotent command idempotence.
- **`environment:`** — a per-task (or per-play) map of environment variables; here it scopes `GNUPGHOME` so `gpg` uses the sandbox keyring.

---

### Step 2 of 2 — Run it twice and watch `changed=1` become `changed=0`

**In plain English:** We run the saved playbook two times; the first run generates the key (`changed=1`), and the second sees `pubring.kbx` already exists and skips the shell task (`changed=0`) — idempotence won by the `creates:` guard.

```bash
ansible-playbook /root/rhcsa_journal/lab-208b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-208b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run: the keyring is built, `keyparams` written, and the key generated, so `changed=1`.
- second `ansible-playbook ...` → Second run: `creates:` finds `pubring.kbx`, so the generation task is skipped and the recap reports `changed=0` — the idempotence proof.
- `echo "exit was: $?"` → Confirm the playbook run succeeded (`0`).

**New words in this step:**

- **PLAY RECAP** — the per-host summary Ansible prints at the end, reporting `ok`, `changed`, and `failed` counts.
- **idempotence** — running the play twice leaves the same end state with no extra change reported (`changed=0` on the re-run is the proof).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.shell` for `gpg` | spawns bash to run a tool no module owns | reports `changed=1` every run unless guarded |
| `args: creates:` | skips the task once the file exists | name a file the command actually produces, or it never skips |
| `environment: GNUPGHOME` | scopes the keyring per task | omit it and keys land in the control node's `~/.gnupg` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| Second run still `changed=1` | Missing/incorrect `creates:` path | Point `creates:` at a file the command really makes (`pubring.kbx`) |
| `agent_genkey failed` / hang | No passphrase in the params or no entropy | Keep `Passphrase:` in `keyparams`; install `rng-tools` for entropy |

---

## TASK 2 of 2 — List and inspect the key read-only with `changed_when: false`

**In plain English:** We write a second playbook that lists the public keys and extracts the fingerprint — pure reads — and prove it reports `changed=0` on every run because we mark the read-only tasks honestly.

---

### Step 1 of 2 — Write the read-only listing playbook

**In plain English:** We create `task2.yml`, which runs `gpg --list-keys` with `ansible.builtin.command` and pulls the fingerprint from machine-readable output, marking both tasks `changed_when: false` since they change nothing.

```yaml
---
- name: "Lab 208b Task 2 — list and inspect the key (read-only)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    gnupghome: /tmp/lab-208/gnupg
    key_email: lab208@example.com
  tasks:
    - name: "List public keys with the long key-ID format"
      ansible.builtin.command: gpg --list-keys --keyid-format LONG
      environment:
        GNUPGHOME: "{{ gnupghome }}"
      register: list_result
      changed_when: false

    - name: "Extract the primary key fingerprint from machine-readable output"
      ansible.builtin.shell: |
        gpg --list-keys --with-colons "{{ key_email }}" | awk -F: '/^fpr/ {print $10; exit}'
      environment:
        GNUPGHOME: "{{ gnupghome }}"
      register: fpr_result
      changed_when: false

    - name: "Show the listing and the captured fingerprint"
      ansible.builtin.debug:
        msg:
          - "{{ list_result.stdout_lines }}"
          - "fingerprint: {{ fpr_result.stdout }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.command: gpg --list-keys --keyid-format LONG` → Read the public keyring; `command` (not `shell`) is enough because there is no pipe or redirect here.
- `changed_when: false` → Tell Ansible this task never changes state, so the recap is honest (`changed=0`).
- `ansible.builtin.shell: ... | awk -F: '/^fpr/ {print $10; exit}'` → A pipe needs `shell`; it extracts the 40-hex fingerprint from the first `fpr` record (field 10) of `--with-colons` output.
- `register:` + `debug:` → Capture the listing and the fingerprint and print them for the audit trail.

**New words in this step:**

- **`changed_when: false`** — overrides Ansible's change detection for a task you know is read-only, keeping the PLAY RECAP truthful.
- **`stdout_lines`** — the registered result's stdout already split into a list of lines, convenient for `debug`.

---

### Step 2 of 2 — Run it twice and confirm `changed=0` both times

**In plain English:** We run the listing playbook twice; because every task is a marked read, the recap shows `changed=0` on both runs and prints the same fingerprint each time.

```bash
ansible-playbook /root/rhcsa_journal/lab-208b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-208b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- both `ansible-playbook ...` runs → Each lists keys and extracts the fingerprint without touching state, so `changed=0` is reported every time.
- the `debug` output (between recaps) → Prints the public-key listing and the captured fingerprint so you can read the result.
- `echo "exit was: $?"` → Confirm the run succeeded (`0`).

**New words in this step:**

- **read-only task** — a task that only inspects the system; marked with `changed_when: false` so it never inflates the change count.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.command` | runs a binary with no shell | a pipe/redirect needs `shell`, not `command` |
| `changed_when: false` | declares a task read-only | omit it and a pure read falsely reports `changed=1` |
| `awk -F: '/^fpr/ {print $10}'` | extracts the fingerprint field | the `fpr` record's fingerprint is column 10 |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Listing reports `changed=1` | Forgot `changed_when: false` | Add it to read-only `command`/`shell` tasks |
| `fingerprint:` is empty | Wrong `key_email` or empty keyring | Run Task 1 first; match the `Name-Email` exactly |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the guarded generation playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=1` become `changed=0`
- [ ] Task 2 · Step 1 — Write the read-only listing playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm `changed=0` both times

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Because the keyring lives at `/tmp/lab-208/gnupg` inside `$LAB_ROOT`, wiping the root removes the generated key too; this lab changed **no** persistent system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-208
rm -rf /root/rhcsa_journal/lab-208b
```

**Expected output:**

```
✅ Removed /tmp/lab-208 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `shell:` for key gen without `creates:` | `changed=1` on every run | Add `args: creates: <pubring.kbx>` to guard it |
| Forgetting `environment: GNUPGHOME` | Keys land in the control node's `~/.gnupg` | Set `GNUPGHOME` per task to the sandbox path |
| Listing keys with `command:` but no `changed_when` | Read-only task reports `changed=1` | Add `changed_when: false` to honest reads |

---

## 📌 Exam Strategy

When the task is "generate a key" and no module exists, reach for `ansible.builtin.shell` — but never ship it bare. Add `creates:` so the generation is idempotent, scope `GNUPGHOME` with `environment:`, and mark every listing/inspection task `changed_when: false`. Re-run the play and read the recap: `changed=1` then `changed=0` for generation, `changed=0` always for reads, is the acceptance test.

- Pair any generative `shell:` with `args: creates:` so the second run is a no-op.
- Use `command:` for plain reads and `shell:` only when you need a pipe/redirect.
- Mark read-only tasks `changed_when: false` so the PLAY RECAP stays truthful.

---

## 🔗 Related Labs

- [Lab 208a — Generate a GPG Key Pair (RHCSA)](../lab-208a-gpg-generate-key-pair-rhcsa/) — the hand-typed shell version this play mirrors
- [Lab 208c — Generate a GPG Key Pair (Verify)](../lab-208c-gpg-generate-key-pair-verify/) — prove the pair exists with hard assertions
- [Lab 209b — Encrypt a File with GPG (Ansible)](../lab-209b-gpg-encrypt-file-ansible/) — put this key pair to work encrypting a file in a play

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
