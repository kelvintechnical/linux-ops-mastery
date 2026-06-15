# Lab 211b: Share and Verify Public Keys (Ansible) — `ansible.builtin.shell`, `environment: GNUPGHOME`

**Series:** linux-ops-mastery — GPG Encryption · **Lab 211b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (multi-environment gpg shell-outs, idempotent export/import), RHCSA EX200 (the key-sharing behavior underneath), Security+/SRE (signed-release automation)  
**Prerequisite:** [Lab 211a](../lab-211a-gpg-share-verify-public-keys-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 211a's two-party key handoff and signature verification in Ansible. You will manage **two separate keyrings** (`gnupg-a` and `gnupg-b`) by scoping `GNUPGHOME` per task with `environment:`, export and import public keys through guarded `ansible.builtin.shell` tasks, transfer the armored key with `ansible.builtin.copy`, detach-sign a message, and verify the signature — proving idempotence with `creates:` and `changed_when: false` on read-only checks.

---

## 🧠 Concept

Key sharing in Ansible has one extra dimension: **which keyring** each `gpg` call uses. Unlike a single-user shell session, a play must set `environment: GNUPGHOME` on every gpg task so Party A's private key never bleeds into Party B's ring. Export and sign are generative shell-outs — guard them with `creates:`. Import is trickier (re-import may say "not changed"); use `changed_when:` parsing gpg's "imported: 1" message. Verification is read-only — mark it `changed_when: false` and use `failed_when: rc != 0` so a BAD signature fails the play honestly.

```
TASK 1                              TASK 2
──────────────────────────────    ──────────────────────────────────────
GNUPGHOME=A → export -a            GNUPGHOME=A → --detach-sign
copy: transfer pubkey.asc            creates: message.txt.sig
GNUPGHOME=B → import                 GNUPGHOME=B → --verify
compare fingerprints (read-only)     failed_when: rc != 0
```

> **Why this matters:** A play that forgets to scope `GNUPGHOME` imports into the wrong ring or signs with the wrong identity — silent, dangerous misconfiguration. Per-task `environment:` is the Ansible equivalent of `export GNUPGHOME=...` before every shell command in 211a.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `environment: { GNUPGHOME: ... }` | Scope each gpg task to the correct keyring | set per task when A and B differ |
| `ansible.builtin.shell` + `creates:` | Export/sign/import via gpg with idempotence | name the output file the command produces |
| `ansible.builtin.copy` | Transfer the armored pubkey / write the message | `remote_src: true` to copy within the host |
| `changed_when:` on import | Detect whether gpg actually imported a new key | parse "imported: 1" in stderr/stdout |
| `changed_when: false` | Mark verify/fingerprint tasks read-only | keeps the PLAY RECAP honest |
| `failed_when: verify_result.rc != 0` | Fail the play on BAD signature | surfaces verification failure to the grader |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works and create the durable playbook folder plus the `/tmp/lab-211` sandbox; the two keyrings (`gnupg-a`, `gnupg-b`) are created by the plays themselves.

> Run this block **once** before Task 1. It builds the clean, private workspace that both tasks depend on.

```bash
sudo -i

export LAB_ROOT=/tmp/lab-211
mkdir -p "$LAB_ROOT"
mkdir -p /root/rhcsa_journal/lab-211b/playbooks

ansible --version | head -2
ls -ld "$LAB_ROOT" /root/rhcsa_journal/lab-211b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root  6 Jun 15 17:45 /tmp/lab-211
drwxr-xr-x. 2 root root  6 Jun 15 17:45 /root/rhcsa_journal/lab-211b/playbooks
Setup complete at 2026-06-15T17:45:05-04:00
exit was: 0
```

---

## TASK 1 of 2 — Export, transfer, and import across two keyrings

**In plain English:** We write a playbook that generates Party A's key (if needed), exports the armored public key, copies it to a receive path, imports it into Party B's ring, and compares fingerprints — all with scoped `GNUPGHOME`.

---

### Step 1 of 2 — Write the export/import playbook

**In plain English:** We create `task1.yml`, which builds both keyrings, generates A's key guarded by `creates:`, exports armored public key, transfers it with `copy`, and imports into B's ring.

```yaml
---
- name: "Lab 211b Task 1 — export, transfer, import public key"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-211
    gnupg_a: /tmp/lab-211/gnupg-a
    gnupg_b: /tmp/lab-211/gnupg-b
    key_email: alice@lab211.local
    pubkey: /tmp/lab-211/pubkey.asc
    received: /tmp/lab-211/pubkey-received.asc
  tasks:
    - name: "Ensure both sandbox keyrings exist (chmod 700)"
      ansible.builtin.file:
        path: "{{ item }}"
        state: directory
        mode: '0700'
      loop:
        - "{{ gnupg_a }}"
        - "{{ gnupg_b }}"

    - name: "Write Party A batch params (idempotent copy)"
      ansible.builtin.copy:
        dest: "{{ lab_root }}/keyparams-a"
        mode: '0600'
        content: |
          %echo Generating Party A key for Lab 211
          Key-Type: RSA
          Key-Length: 3072
          Subkey-Type: RSA
          Subkey-Length: 3072
          Name-Real: Lab 211 Alice
          Name-Email: {{ key_email }}
          Expire-Date: 1y
          Passphrase: labpass211
          %commit
          %echo done

    - name: "Generate Party A key if not present (guarded shell)"
      ansible.builtin.shell: |
        gpg --batch --gen-key "{{ lab_root }}/keyparams-a"
      environment:
        GNUPGHOME: "{{ gnupg_a }}"
      args:
        creates: "{{ gnupg_a }}/pubring.kbx"
      register: gen_result

    - name: "Export the armored public key from Party A"
      ansible.builtin.shell: |
        gpg --export -a "{{ key_email }}" > "{{ pubkey }}"
      environment:
        GNUPGHOME: "{{ gnupg_a }}"
      args:
        creates: "{{ pubkey }}"
      register: export_result

    - name: "Transfer the key (local copy simulating scp handoff)"
      ansible.builtin.copy:
        src: "{{ pubkey }}"
        dest: "{{ received }}"
        remote_src: true
        mode: '0644'

    - name: "Import the public key into Party B's keyring"
      ansible.builtin.shell: |
        gpg --import "{{ received }}"
      environment:
        GNUPGHOME: "{{ gnupg_b }}"
      register: import_result
      changed_when: "'imported: 1' in import_result.stderr or 'imported: 1' in import_result.stdout"

    - name: "Compare fingerprints between A and B"
      ansible.builtin.shell: |
        fpr_a=$(gpg --list-keys --with-colons "{{ key_email }}" | awk -F: '/^fpr/ {print $10; exit}')
        fpr_b=$(GNUPGHOME="{{ gnupg_b }}" gpg --list-keys --with-colons "{{ key_email }}" | awk -F: '/^fpr/ {print $10; exit}')
        test "$fpr_a" = "$fpr_b" && echo "FINGERPRINT MATCH" || echo "FINGERPRINT MISMATCH"
      environment:
        GNUPGHOME: "{{ gnupg_a }}"
      register: fpr_result
      changed_when: false

    - name: "Show export/import and fingerprint result"
      ansible.builtin.debug:
        msg:
          - "gen changed:    {{ gen_result.changed }}"
          - "export changed: {{ export_result.changed }}"
          - "import changed: {{ import_result.changed }}"
          - "{{ fpr_result.stdout }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.file` loop → Create both `gnupg-a` and `gnupg-b` with mode `700`.
- `environment: GNUPGHOME: "{{ gnupg_a }}"` on generate/export → Party A's ring only.
- `args: creates:` on generate and export → Idempotence guards for generative shell tasks.
- `ansible.builtin.copy: remote_src: true` → Copy `pubkey.asc` to `pubkey-received.asc` on the same host (simulating `scp` handoff).
- `environment: GNUPGHOME: "{{ gnupg_b }}"` on import → Party B's ring only.
- `changed_when: "'imported: 1' in ..."` → Report change only when gpg actually imported a new key.
- fingerprint task with `changed_when: false` → Read-only comparison.

**New words in this step:**

- **per-task `environment:`** — scopes `GNUPGHOME` differently for A vs B tasks in the same play.
- **`remote_src: true`** — tells `copy` the source is already on the target host (not from the control node).

---

### Step 2 of 2 — Run it twice and confirm fingerprint match

**In plain English:** We run the playbook two times; the first creates keys and imports (`changed=1`), the second skips guarded tasks (`changed=0`), and the debug output shows `FINGERPRINT MATCH`.

```bash
ansible-playbook /root/rhcsa_journal/lab-211b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-211b/playbooks/task1.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=7    changed=3    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=6    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Generates A's key, exports, imports to B; `changed` reflects the generative steps.
- second `ansible-playbook ...` → `creates:` skips generate/export; import reports no new key; `changed=0`.
- debug output between runs → Should print `FINGERPRINT MATCH`.

**New words in this step:**

- **idempotence** — the re-run leaves the same state with no extra change reported.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| per-task `GNUPGHOME` | keeps A and B keyrings separate | one global env var mixes identities |
| `creates:` on export | skips re-export once `pubkey.asc` exists | path must match the shell redirect target |
| `changed_when` on import | honest change detection for re-import | bare import always says `changed=1` |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `FINGERPRINT MISMATCH` in debug | Import used wrong `GNUPGHOME` | Confirm import task sets `GNUPGHOME` to `gnupg_b` |
| Second run still `changed=1` on export | `creates:` path wrong | Point `creates:` at the exact `pubkey.asc` path |

---

## TASK 2 of 2 — Detach-sign and verify in automation

**In plain English:** We write a second playbook that signs the message from A's ring, verifies from B's ring, and fails the play honestly if verification would fail.

---

### Step 1 of 2 — Write the sign/verify playbook

**In plain English:** We create `task2.yml`, which writes the message, detach-signs it from A's ring guarded by `creates:`, and verifies from B's ring with `failed_when: rc != 0`.

```yaml
---
- name: "Lab 211b Task 2 — detach-sign and verify"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    lab_root: /tmp/lab-211
    gnupg_a: /tmp/lab-211/gnupg-a
    gnupg_b: /tmp/lab-211/gnupg-b
    key_email: alice@lab211.local
    message: /tmp/lab-211/message.txt
    sig: /tmp/lab-211/message.txt.sig
    passphrase: labpass211
  tasks:
    - name: "Write the message to sign (idempotent copy)"
      ansible.builtin.copy:
        dest: "{{ message }}"
        content: |
          release artifact v1.0 — checksum: deadbeef
        mode: '0644'

    - name: "Create a detached signature from Party A"
      ansible.builtin.shell: |
        gpg --batch --pinentry-mode loopback --passphrase '{{ passphrase }}' \
            --detach-sign -o '{{ sig }}' '{{ message }}'
      environment:
        GNUPGHOME: "{{ gnupg_a }}"
      args:
        creates: "{{ sig }}"
      register: sign_result

    - name: "Verify the signature from Party B's keyring"
      ansible.builtin.shell: |
        gpg --verify '{{ sig }}' '{{ message }}'
      environment:
        GNUPGHOME: "{{ gnupg_b }}"
      register: verify_result
      changed_when: false
      failed_when: verify_result.rc != 0

    - name: "Show sign and verify results"
      ansible.builtin.debug:
        msg:
          - "sign changed:   {{ sign_result.changed }}"
          - "verify rc:     {{ verify_result.rc }}"
          - "verify stderr: {{ verify_result.stderr }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.copy` → Write the message declaratively.
- `environment: GNUPGHOME: "{{ gnupg_a }}"` on sign → Alice's private key signs the file.
- `args: creates: "{{ sig }}"` → Skip re-signing once the `.sig` exists.
- `environment: GNUPGHOME: "{{ gnupg_b }}"` on verify → B's ring holds Alice's imported public key.
- `changed_when: false` + `failed_when: rc != 0` → Read-only verify that fails the play on BAD signature.

**New words in this step:**

- **`failed_when:`** — overrides Ansible's default failure detection; here, any non-zero verify `rc` fails the play.
- **`verify_result.stderr`** — gpg prints "Good signature" to stderr, not stdout.

---

### Step 2 of 2 — Run it twice and read the Good signature

**In plain English:** We run the sign/verify playbook twice; the first creates the signature (`changed=1`), the second skips sign (`changed=0`), and debug shows verify `rc: 0` with "Good signature" in stderr.

```bash
ansible-playbook /root/rhcsa_journal/lab-211b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-211b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=4    changed=2    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → Writes message and creates `.sig`; verify passes with `rc: 0`.
- second `ansible-playbook ...` → `creates:` skips sign; verify still runs read-only (`changed=0`).
- debug → `verify stderr` contains `Good signature from "Lab 211 Alice <alice@lab211.local>"`.

**New words in this step:**

- **Good signature** — gpg's confirmation that the detached `.sig` matches the data file and a trusted public key.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `GNUPGHOME=A` for sign | uses the private key | signing from B's ring fails — no secret key |
| `GNUPGHOME=B` for verify | uses the imported public key | verify before import → `No public key` |
| `failed_when: rc != 0` | fails play on BAD signature | without it, a tampered file might pass silently |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `No public key` on verify | Task 1 import not run first | Run `task1.yml` before `task2.yml` |
| Play fails on verify | Message tampered or wrong sig | Re-sign from the original message |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the export/import playbook
- [ ] Task 1 · Step 2 — Run it twice and confirm fingerprint match
- [ ] Task 2 · Step 1 — Write the sign/verify playbook
- [ ] Task 2 · Step 2 — Run it twice and read the Good signature

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path. Both keyrings live inside `$LAB_ROOT`, so one wipe removes every key — this lab changed **no** persistent system state.

```bash
bash lab_teardown.sh "$LAB_ROOT"     # = /tmp/lab-211
rm -rf /root/rhcsa_journal/lab-211b
```

**Expected output:**

```
✅ Removed /tmp/lab-211 — lab workspace is clean.
```

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| One `GNUPGHOME` for both parties | Import/sign hits the wrong ring | Set `environment:` per task for A vs B |
| Verify task without `failed_when` | BAD signature does not fail the play | Add `failed_when: verify_result.rc != 0` |
| Running task2 before task1 | `No public key` on verify | Run export/import play first |

---

## 📌 Exam Strategy

Multi-party gpg in Ansible is all about scoping `GNUPGHOME` per task. Export and sign are generative — guard with `creates:`. Import needs honest `changed_when:`. Verify is read-only — `changed_when: false` and `failed_when: rc != 0`. Re-run both plays and read the recap plus the debug output for `FINGERPRINT MATCH` and `Good signature`.

- Scope `GNUPGHOME` differently for Party A (sign/export) and Party B (import/verify).
- Run Task 1 before Task 2 so B holds Alice's public key.
- Read gpg's "Good signature" from `stderr`, not `stdout`.

---

## 🔗 Related Labs

- [Lab 211a — Share and Verify Public Keys (RHCSA)](../lab-211a-gpg-share-verify-public-keys-rhcsa/) — the hand-typed shell version this play mirrors
- [Lab 211c — Share and Verify Public Keys (Verify)](../lab-211c-gpg-share-verify-public-keys-verify/) — hard assertions on fingerprints and signatures
- [Lab 208b — Generate a GPG Key Pair (Ansible)](../lab-208b-gpg-generate-key-pair-ansible/) — the key-generation play that precedes sharing

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
