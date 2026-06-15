# Lab 210b: Decrypt a GPG File (Ansible) — `ansible.builtin.shell` + `creates:`, `register`/`rc`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 210b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent shell-outs and reading task `rc`), RHCSA EX200 (the decrypt behavior underneath), SRE/DevOps (recovering secrets in headless pipelines)  
**Prerequisite:** [Lab 210a](../lab-210a-gpg-decrypt-file-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 210a's non-interactive decryption in Ansible for both an **asymmetric** file (private key + passphrase) and a **symmetric** file (passphrase only). Because GnuPG has no `ansible.builtin` module, you will run `gpg --decrypt` through `ansible.builtin.shell`, make it idempotent with `creates:` (the recovered file is the marker), supply the passphrase non-interactively with loopback pinentry, and surface the task's return code (`rc`) so a wrong passphrase is detectable in automation.

---

## 🧠 Concept

Decryption writes a *recovered plaintext file*, which is the natural `creates:` marker: once it exists, Ansible skips the shell task and the re-run is `changed=0`. Both decrypts go through `ansible.builtin.shell` (no module owns gpg). The asymmetric file needs the matching private key in `GNUPGHOME` plus its passphrase; the symmetric file needs only the shared passphrase. On a control node there is no terminal for a pinentry prompt, so `--pinentry-mode loopback --passphrase` is mandatory. Capturing the result with `register:` exposes `rc`, the return code that an automation can test — a wrong passphrase exits non-zero even though gpg may leave a stub output file behind.

```
ASYMMETRIC (task1.yml)                          SYMMETRIC (task2.yml)
──────────────────────────────────────────     ──────────────────────────────────────────
shell: gpg ... --decrypt secret.txt.gpg         shell: gpg ... -d secret.sym.gpg
  -o recovered.txt   creates: recovered.txt        -o recovered.sym.txt  creates: recovered.sym.txt
  needs PRIVATE key + passphrase                   needs only the shared passphrase
  register → rc (0 = ok, non-zero = bad pass)      register → rc (detect failure in automation)
```

> **Why this matters:** A decrypt that hangs on a hidden pinentry prompt freezes a pipeline; one that "succeeds" with a wrong passphrase and a 0-byte file corrupts downstream steps. The loopback/`--passphrase` pattern plus reading `rc` is how automation recovers secrets safely.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.shell` | Run `gpg --decrypt` (no module owns it) | pair with `args: creates:` for idempotence |
| `args: creates: <recovered>` | Skip the decrypt once the plaintext exists | name the exact `-o` output path |
| `environment: { GNUPGHOME: ... }` | Use the sandbox keyring for the private key | set at play or task level |
| `--pinentry-mode loopback --passphrase` | Supply the passphrase without a terminal | required on a headless control node |
| `register:` + `.rc` | Capture the task's return code | `rc != 0` flags a wrong passphrase or failure |
| `gpg --batch --yes` | Run unattended and overwrite without prompting | lets a re-decrypt complete non-interactively |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, build the playbook folder and `/tmp` sandbox, point GnuPG at a sandbox keyring, generate a disposable keypair, and seal one plaintext two ways so the plays have real ciphertext to recover.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-210
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-210b/playbooks

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

gpg --batch --pinentry-mode loopback --passphrase 'LabPass210!' \
    --quick-generate-key 'Lab 210 <lab210@example.com>' default default never

echo "top secret: the vault code is 4815-1623-4208" > "$LAB_ROOT/secret.txt"
gpg --batch --yes -e -r 'lab210@example.com' -o "$LAB_ROOT/secret.txt.gpg" "$LAB_ROOT/secret.txt"
gpg --batch --yes --pinentry-mode loopback --passphrase 'LabPass210!' \
    --symmetric -o "$LAB_ROOT/secret.sym.gpg" "$LAB_ROOT/secret.txt"

ansible --version | head -2
ls -1 "$LAB_ROOT"/secret.*
echo "exit was: $?"
```

**Expected output:**

```
gpg: key A1B2C3D4E5F6 marked as ultimately trusted
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
/tmp/lab-210/secret.sym.gpg
/tmp/lab-210/secret.txt
/tmp/lab-210/secret.txt.gpg
exit was: 0
```

---

## TASK 1 of 2 — Decrypt the asymmetric file idempotently

**In plain English:** We write a playbook that decrypts `secret.txt.gpg` with the private key's passphrase via loopback pinentry, guarded by `creates:`, then run it twice to watch `changed=1` become `changed=0`.

---

### Step 1 of 2 — Write the asymmetric decrypt playbook

**In plain English:** We create `task1.yml`, which shells out to `gpg --decrypt` with loopback pinentry, names the recovered file as the `creates:` marker, and registers the result so we can read its return code.

```yaml
---
- name: "Lab 210b Task 1 — decrypt an asymmetric GPG file (idempotent via creates:)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-210
    gnupg_home: /tmp/lab-210/gnupg
    passphrase: "LabPass210!"
    cipher: /tmp/lab-210/secret.txt.gpg
    recovered: /tmp/lab-210/recovered.txt
  tasks:
    - name: "Decrypt the asymmetric file with loopback pinentry (no module owns gpg)"
      ansible.builtin.shell: |
        gpg --batch --pinentry-mode loopback --passphrase '{{ passphrase }}' \
            -o '{{ recovered }}' --decrypt '{{ cipher }}'
      environment:
        GNUPGHOME: "{{ gnupg_home }}"
      args:
        creates: "{{ recovered }}"
      register: decrypt_result

    - name: "Show what the decrypt task reported"
      ansible.builtin.debug:
        msg:
          - "rc:      {{ decrypt_result.rc | default('skipped') }}"
          - "changed: {{ decrypt_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.shell: gpg ... --decrypt '{{ cipher }}'` → The only honest way to decrypt from a play; `-o` writes the recovered plaintext to a file.
- `--pinentry-mode loopback --passphrase '{{ passphrase }}'` → Supply the private key's passphrase without a terminal, so the play never hangs.
- `environment: GNUPGHOME:` → Point gpg at the sandbox keyring that holds the private key.
- `args: creates: "{{ recovered }}"` → Skip the decrypt once `recovered.txt` exists — the idempotence guard.
- `register: decrypt_result` + `debug:` → Capture `rc` (use `| default('skipped')` because a skipped task has no `rc`) and the `changed` flag.

**New words in this step:**

- **`rc`** — the return code field of a registered command/shell result; `0` is success, non-zero flags failure.
- **`| default('skipped')`** — a Jinja filter giving a fallback value when a field (like `rc` on a skipped task) is undefined.

---

### Step 2 of 2 — Run it twice and verify the recovered plaintext

**In plain English:** We run the playbook two times; the first decrypts (`changed=1`), the second is skipped by `creates:` (`changed=0`), and we confirm the recovered text matches the original.

```bash
ansible-playbook /root/rhcsa_journal/lab-210b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-210b/playbooks/task1.yml
diff /tmp/lab-210/secret.txt /tmp/lab-210/recovered.txt && echo "RECOVERY MATCH (OK)"
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=0    unreachable=0    failed=0
RECOVERY MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Decrypts the file, creating `recovered.txt`, so `changed=1`.
- second `ansible-playbook ...` → `creates:` finds `recovered.txt` and skips the decrypt, so `changed=0`.
- `diff ... && echo "RECOVERY MATCH (OK)"` → Prove the recovered plaintext equals the original byte-for-byte.

**New words in this step:**

- **idempotence** — the re-run leaves the same state with no extra change reported.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `shell:` gpg decrypt | runs a tool no module owns | bare, it re-decrypts every run |
| `args: creates:` | skips once the recovered file exists | must equal the `-o` output path |
| `--pinentry-mode loopback` | answers the passphrase prompt headlessly | omit it and the task hangs |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No secret key` | Wrong `GNUPGHOME` or key not generated | Re-run SETUP; point `GNUPGHOME` at the sandbox |
| Task hangs | Missing loopback pinentry | Add `--pinentry-mode loopback --passphrase '...'` |

---

## TASK 2 of 2 — Decrypt the symmetric file and read the return code

**In plain English:** We write a second playbook that decrypts the passphrase-only file (no private key involved), guarded by `creates:`, and surface `rc` so a wrong passphrase would be detectable in automation.

---

### Step 1 of 2 — Write the symmetric decrypt playbook

**In plain English:** We create `task2.yml`, which decrypts `secret.sym.gpg` with only the shared passphrase, names the recovered file as the `creates:` marker, and registers the result to report `rc`.

```yaml
---
- name: "Lab 210b Task 2 — decrypt a symmetric GPG file (passphrase only, report rc)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-210
    gnupg_home: /tmp/lab-210/gnupg
    passphrase: "LabPass210!"
    cipher: /tmp/lab-210/secret.sym.gpg
    recovered: /tmp/lab-210/recovered.sym.txt
  tasks:
    - name: "Decrypt the symmetric file with only the shared passphrase"
      ansible.builtin.shell: |
        gpg --batch --yes --pinentry-mode loopback --passphrase '{{ passphrase }}' \
            -o '{{ recovered }}' -d '{{ cipher }}'
      environment:
        GNUPGHOME: "{{ gnupg_home }}"
      args:
        creates: "{{ recovered }}"
      register: sym_result

    - name: "Show the return code so a wrong passphrase would be detectable"
      ansible.builtin.debug:
        msg:
          - "rc:      {{ sym_result.rc | default('skipped') }}"
          - "changed: {{ sym_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.shell: gpg ... -d '{{ cipher }}'` → Decrypt the symmetric file; no private key is consulted, only the passphrase.
- `--batch --yes` → Run unattended and overwrite an existing output without prompting.
- `args: creates: "{{ recovered }}"` → Idempotence guard on the recovered symmetric plaintext.
- `register: sym_result` + `debug:` → Expose `rc` so automation can branch on success/failure.

**New words in this step:**

- **symmetric decrypt** — recovering plaintext using only the shared passphrase, with no keypair involved.

---

### Step 2 of 2 — Run it twice and confirm the recovery

**In plain English:** We run the symmetric playbook twice; the first decrypts (`changed=1`), the second is skipped (`changed=0`), and we confirm the recovered file matches the original.

```bash
ansible-playbook /root/rhcsa_journal/lab-210b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-210b/playbooks/task2.yml
diff /tmp/lab-210/secret.txt /tmp/lab-210/recovered.sym.txt && echo "SYMMETRIC MATCH (OK)"
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=0    unreachable=0    failed=0
SYMMETRIC MATCH (OK)
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Decrypts `secret.sym.gpg` to `recovered.sym.txt`, so `changed=1`.
- second `ansible-playbook ...` → `creates:` finds it and skips, so `changed=0`.
- `diff ... && echo "SYMMETRIC MATCH (OK)"` → Prove the symmetric recovery is byte-identical to the original.

**New words in this step:**

- **return code branching** — using a task's `rc` to decide success/failure in later automation steps.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| symmetric `-d` | opens passphrase-only ciphertext | a missing private key is irrelevant here |
| `register` → `rc` | exposes success/failure to automation | a wrong passphrase can still leave a stub file |
| `creates:` on recovered file | idempotence for the decrypt | the marker must equal the `-o` path |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `rc` is non-zero | Wrong passphrase or corrupt ciphertext | Re-check the passphrase; re-run SETUP |
| Second run still `changed=1` | `creates:` path differs from `-o` | Make them identical |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the asymmetric decrypt playbook
- [ ] Task 1 · Step 2 — Run it twice and verify the recovered plaintext
- [ ] Task 2 · Step 1 — Write the symmetric decrypt playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm the recovery

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. The keyring, ciphertext, and recovered files all live under `$LAB_ROOT`, so one wipe is enough — this lab changed **no** persistent system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-210
rm -rf /root/rhcsa_journal/lab-210b
```

**Expected output:**

```
✅ Removed /tmp/lab-210 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Decrypting in `shell:` without `creates:` | `changed=1` on every run | Add `args: creates: <recovered>` |
| No loopback pinentry on a control node | Task hangs waiting for a prompt | Add `--pinentry-mode loopback --passphrase` |
| Ignoring `rc` | A wrong passphrase passes unnoticed | Register the result and test `rc` |

---

## 📌 Exam Strategy

When a play must decrypt, shell out to `gpg --decrypt`, guard it with `creates:`, and always supply the passphrase via loopback so it never stalls. Register the result and read `rc` so a bad passphrase fails loudly. Re-run to prove `changed=0`, and verify the recovered bytes with `diff`/`sha256sum`.

- Pair every decrypting `shell:` with `args: creates: <recovered>`.
- Use loopback pinentry on headless hosts — `--passphrase` is ignored without it.
- Register the task and branch on `rc` to detect a wrong passphrase.

---

## 🔗 Related Labs

- [Lab 210a — Decrypt a GPG File (RHCSA)](../lab-210a-gpg-decrypt-file-rhcsa/) — the hand-typed version this play mirrors
- [Lab 210c — Decrypt a GPG File (Verify)](../lab-210c-gpg-decrypt-file-verify/) — prove recovery is byte-identical and a wrong passphrase fails
- [Lab 209b — Encrypt a File with GPG (Ansible)](../lab-209b-gpg-encrypt-file-ansible/) — the encryption play that produced this ciphertext

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
