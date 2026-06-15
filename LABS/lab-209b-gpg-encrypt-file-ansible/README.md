# Lab 209b: Encrypt a File with GPG (Ansible) — `ansible.builtin.shell` + `creates:`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 209b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (idempotent shell-outs for tools without a module), RHCSA EX200 (the encryption behavior underneath), Security+/SRE (encrypting artifacts and secrets in automation)  
**Prerequisite:** [Lab 209a](../lab-209a-gpg-encrypt-file-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 209a's two encryption models in Ansible — **asymmetric** (`gpg -e -r recipient`) and **symmetric** (`gpg --symmetric`) — and learn how to make a tool with no module behave idempotently. Since nothing in `ansible.builtin` performs GPG encryption, you will use `ansible.builtin.shell` guarded by `creates:` so the ciphertext is produced once and re-runs report `changed=0`, while writing the plaintext declaratively with `ansible.builtin.copy`.

---

## 🧠 Concept

Encryption produces a *new file* (the ciphertext), which makes it a perfect fit for the `creates:` idempotence guard: name the output file, and Ansible skips the `shell:` task once it exists. Both models go through the same shell module — `ansible.builtin.shell` — because GnuPG has no `ansible.builtin` equivalent. The difference is in the gpg flags: asymmetric needs a `--recipient` whose public key is in the keyring; symmetric needs only `--passphrase` (with loopback pinentry) and no key at all. Writing the plaintext input with `ansible.builtin.copy` keeps that half declarative and state-aware.

```
ASYMMETRIC (task1.yml)                        SYMMETRIC (task2.yml)
──────────────────────────────────────       ────────────────────────────────────────────
shell: gpg -e -r recipient -o out.gpg in      shell: gpg --symmetric --passphrase X -o out in
  creates: out.gpg                              creates: out
  needs the recipient PUBLIC key in keyring     needs no keyring — just the passphrase
  └─ changed=1 first, changed=0 after           └─ changed=1 first, changed=0 after
```

> **Why this matters:** A `shell:` task that re-encrypts on every run looks "changed" forever and wastes work; graders read that as a missing idempotence guard. `creates:` is the one-line fix that turns an unavoidable shell-out into well-behaved automation.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.shell` | Run `gpg` encryption (no module owns it) | pair with `args: creates:` for idempotence |
| `args: creates: <ciphertext>` | Skip the encrypt task once the output exists | name the exact output file gpg writes |
| `environment: { GNUPGHOME: ... }` | Use the sandbox keyring for recipient lookups | set at play level so every task inherits it |
| `ansible.builtin.copy` with `content:` | Write the plaintext input declaratively | idempotent — re-run is `changed=0` |
| `gpg --batch --yes` | Run gpg unattended and overwrite without prompting | required so a play never stalls on a prompt |
| `gpg --pinentry-mode loopback --passphrase` | Supply a symmetric passphrase non-interactively | only honored with `--pinentry-mode loopback` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, build the playbook folder and `/tmp` sandbox, point GnuPG at a sandbox keyring, and generate a throwaway **recipient** key so the asymmetric play has someone to encrypt to.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-209
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-209b/playbooks

export GNUPGHOME="$LAB_ROOT/gnupg"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

cat > "$LAB_ROOT/keyparams" <<'EOF'
%echo Generating throwaway Lab 209 recipient key
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: Lab 209 Recipient
Name-Email: recipient@lab209.local
Expire-Date: 0
Passphrase: labpass209
%commit
%echo done
EOF

gpg --batch --pinentry-mode loopback --gen-key "$LAB_ROOT/keyparams"
ansible --version | head -2
gpg --list-keys recipient@lab209.local >/dev/null && echo "recipient key ready (OK)"
echo "exit was: $?"
```

**Expected output:**

```
gpg: key A1B2C3D4E5F6A7B8 marked as ultimately trusted
gpg: done
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
recipient key ready (OK)
exit was: 0
```

---

## TASK 1 of 2 — Asymmetric encryption to a recipient, guarded by `creates:`

**In plain English:** We write a playbook that drops a plaintext with `copy`, encrypts it to the recipient's public key with a `shell:` gpg task guarded by `creates:`, and run it twice to watch `changed=1` become `changed=0`.

---

### Step 1 of 2 — Write the asymmetric encryption playbook

**In plain English:** We create `task1.yml`, which writes the plaintext declaratively, then shells out to `gpg --encrypt --recipient` with a `creates:` marker so the ciphertext is produced exactly once.

```yaml
---
- name: "Lab 209b Task 1 — asymmetric encrypt to a recipient (shell + creates)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-209
    recipient: recipient@lab209.local
  environment:
    GNUPGHOME: "{{ lab_root }}/gnupg"
  tasks:
    - name: "Write the plaintext we will encrypt (idempotent copy)"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/secret.txt"
        content: |
          top secret ansible payload
        mode: '0644'

    - name: "Encrypt to the recipient's public key (binary OpenPGP)"
      ansible.builtin.shell: |
        gpg --batch --yes --recipient "{{ recipient }}" \
            --encrypt --output "{{ lab_root }}/secret.txt.gpg" \
            "{{ lab_root }}/secret.txt"
      args:
        creates: "{{ lab_root }}/secret.txt.gpg"
      register: enc_result

    - name: "Show the encryption result"
      ansible.builtin.debug:
        msg:
          - "changed:    {{ enc_result.changed }}"
          - "ciphertext: {{ lab_root }}/secret.txt.gpg"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `environment: GNUPGHOME:` at play level → Every task in the play uses the sandbox keyring, so the recipient lookup finds the key from SETUP.
- `ansible.builtin.copy: content: |` → Write the plaintext input declaratively; a re-run is `changed=0` because the content already matches.
- `ansible.builtin.shell: gpg --batch --yes --recipient ... --encrypt --output ...` → The shell-out that performs asymmetric encryption; `--batch --yes` keeps it unattended.
- `args: creates: "{{ lab_root }}/secret.txt.gpg"` → The idempotence guard — once the ciphertext exists, the task is skipped.
- `register:` + `debug:` → Capture and print whether encryption ran.

**New words in this step:**

- **`creates:`** — names a file the task produces; if present, Ansible skips the task, giving a non-idempotent shell command idempotence.
- **play-level `environment:`** — environment variables applied to every task in the play, not just one.

---

### Step 2 of 2 — Run it twice and watch `changed=1` become `changed=0`

**In plain English:** We run the playbook two times; the first encrypts the file (`changed=1`) and the second finds the ciphertext already present and skips the encrypt task (`changed=0`).

```bash
ansible-playbook /root/rhcsa_journal/lab-209b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-209b/playbooks/task1.yml
file /tmp/lab-209/secret.txt.gpg
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=2    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
/tmp/lab-209/secret.txt.gpg: PGP RSA encrypted session key - keyid: ... RSA (Encrypt or Sign) 2048b .
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run writes the plaintext and encrypts it, so `changed=2` (copy + encrypt).
- second `ansible-playbook ...` → Second run: the plaintext already matches and `creates:` skips the encrypt, so `changed=0` — the idempotence proof.
- `file /tmp/lab-209/secret.txt.gpg` → Confirm the output is real binary OpenPGP ciphertext, not plaintext.

**New words in this step:**

- **PLAY RECAP** — the per-host summary of `ok`/`changed`/`failed` counts printed at the end of a run.
- **idempotence** — the re-run leaves the same state and reports no change (`changed=0`).

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `shell:` gpg encrypt | runs a tool no module owns | bare, it re-encrypts every run (`changed=1`) |
| `args: creates:` | skips once the ciphertext exists | must name the exact `--output` path |
| play-level `environment:` | scopes `GNUPGHOME` for all tasks | omit it and recipient lookup fails on the control node |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No public key` for the recipient | SETUP key missing or wrong `GNUPGHOME` | Re-run SETUP; confirm `gpg --list-keys recipient@lab209.local` |
| Second run still `changed=1` | `creates:` path differs from `--output` | Make them identical so the guard fires |

---

## TASK 2 of 2 — Symmetric encryption with a passphrase (no keyring)

**In plain English:** We write a second playbook that encrypts the same file with only a shared passphrase and AES-256, again guarded by `creates:`, and prove the re-run is `changed=0`.

---

### Step 1 of 2 — Write the symmetric encryption playbook

**In plain English:** We create `task2.yml`, which runs `gpg --symmetric` with loopback pinentry so the passphrase is supplied non-interactively — no recipient key needed at all.

```yaml
---
- name: "Lab 209b Task 2 — symmetric (passphrase-only) encrypt (shell + creates)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-209
    passphrase: labpass209
  environment:
    GNUPGHOME: "{{ lab_root }}/gnupg"
  tasks:
    - name: "Symmetrically encrypt with AES256 (no keys, just a passphrase)"
      ansible.builtin.shell: |
        gpg --batch --yes --pinentry-mode loopback \
            --passphrase "{{ passphrase }}" \
            --symmetric --cipher-algo AES256 \
            --output "{{ lab_root }}/secret.sym.gpg" \
            "{{ lab_root }}/secret.txt"
      args:
        creates: "{{ lab_root }}/secret.sym.gpg"
      register: sym_result

    - name: "Show the symmetric encryption result"
      ansible.builtin.debug:
        msg:
          - "changed:    {{ sym_result.changed }}"
          - "ciphertext: {{ lab_root }}/secret.sym.gpg"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.shell: gpg ... --symmetric --cipher-algo AES256 ...` → Encrypt with a shared passphrase, pinning AES-256; no `--recipient`, no key lookup.
- `--pinentry-mode loopback --passphrase "{{ passphrase }}"` → Supply the passphrase on the command line so the play never waits on a prompt.
- `args: creates: "{{ lab_root }}/secret.sym.gpg"` → Skip the task once the symmetric ciphertext exists.
- `register:` + `debug:` → Surface the `changed` flag for the idempotence proof.

**New words in this step:**

- **symmetric encryption** — one shared passphrase both locks and unlocks the data; no public/private keypair involved.
- **`--cipher-algo AES256`** — pins a strong cipher instead of relying on gpg's default.

---

### Step 2 of 2 — Run it twice and confirm `changed=0` on the re-run

**In plain English:** We run the symmetric playbook twice; the first run creates the AES-256 ciphertext (`changed=1`) and the second skips it (`changed=0`), then we confirm `file` sees a symmetric blob.

```bash
ansible-playbook /root/rhcsa_journal/lab-209b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-209b/playbooks/task2.yml
file /tmp/lab-209/secret.sym.gpg
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=1    changed=0    unreachable=0    failed=0
/tmp/lab-209/secret.sym.gpg: GPG symmetrically encrypted data (AES256 cipher)
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Creates `secret.sym.gpg`, so `changed=1`.
- second `ansible-playbook ...` → `creates:` finds it and skips, so `changed=0`.
- `file /tmp/lab-209/secret.sym.gpg` → Confirms it is "GPG symmetrically encrypted data (AES256 cipher)" — the passphrase model, not a public key.

**New words in this step:**

- **session key** — the per-message key that actually encrypts the data; symmetric mode protects it with the passphrase, not a public key.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `gpg --symmetric` | passphrase-only encryption, no keyring | distribution of the passphrase is the weak point |
| `--pinentry-mode loopback` | lets `--passphrase` work unattended | omit it and the play hangs on a hidden prompt |
| `creates:` on the `.sym.gpg` | idempotence for the symmetric output | the marker must equal the `--output` path |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Task hangs / `Inappropriate ioctl for device` | Missing loopback pinentry | Add `--pinentry-mode loopback --passphrase '...'` |
| `secret.txt` not found | Ran Task 2 before Task 1 wrote the plaintext | Run `task1.yml` first (or add a `copy` of the plaintext) |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the asymmetric encryption playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=1` become `changed=0`
- [ ] Task 2 · Step 1 — Write the symmetric encryption playbook
- [ ] Task 2 · Step 2 — Run it twice and confirm `changed=0` on the re-run

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. The keyring and all ciphertext live under `$LAB_ROOT`, so one wipe removes the throwaway recipient key too — this lab changed **no** persistent system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-209
rm -rf /root/rhcsa_journal/lab-209b
```

**Expected output:**

```
✅ Removed /tmp/lab-209 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Encrypting in `shell:` without `creates:` | `changed=1` on every run | Add `args: creates: <ciphertext>` |
| Forgetting play-level `environment:` | Recipient key not found | Scope `GNUPGHOME` for all tasks |
| Omitting loopback pinentry on symmetric | Play stalls on a passphrase prompt | Use `--pinentry-mode loopback --passphrase` |

---

## 📌 Exam Strategy

When automation must encrypt a file and no module exists, use `ansible.builtin.shell` — but guard it with `creates:` so it runs once. Choose the model by the prompt: "encrypt for *recipient*" is asymmetric (`-e -r`, key must be in the keyring); "protect with a passphrase" is symmetric (`--symmetric` + loopback). Re-run and read the recap to prove idempotence.

- Always pair an encrypting `shell:` with `args: creates: <output>`.
- Scope `GNUPGHOME` at play level so recipient lookups succeed.
- Use `--batch --yes` (and loopback pinentry for symmetric) so the play never prompts.

---

## 🔗 Related Labs

- [Lab 209a — Encrypt a File with GPG (RHCSA)](../lab-209a-gpg-encrypt-file-rhcsa/) — the hand-typed version this play mirrors
- [Lab 209c — Encrypt a File with GPG (Verify)](../lab-209c-gpg-encrypt-file-verify/) — prove the `.gpg`/`.sym.gpg` outputs are real and packet-correct
- [Lab 210b — Decrypt a GPG File (Ansible)](../lab-210b-gpg-decrypt-file-ansible/) — the reverse trip in a play

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
