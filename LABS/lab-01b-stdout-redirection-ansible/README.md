# Lab 01b: Stdout Redirection (Ansible) — `ansible.builtin.shell` `>`, `ansible.builtin.copy`

**Series:** linux-ops-mastery — Shells, Terminals & Redirection · **Lab 01b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (knowing when `shell:` is required vs when a real module is idempotent), RHCSA EX200 (the shell behavior underneath), DevOps (declarative file content management)  
**Prerequisite:** [Lab 01a](../lab-01a-stdout-redirection-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 25–35 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Reproduce Lab 01a's "write a file from a command's output" in Ansible, and learn the boundary that defines good automation: `>` and `>>` are shell operators with **no honest `ansible.builtin` module**, so `ansible.builtin.shell` is the only literal substitute — and it is **not idempotent**. You will prove that with a double run, then rewrite the same outcome with `ansible.builtin.copy`, which *is* idempotent, and feel the difference.

---

## 🧠 Concept

In the shell, `>` truncates-and-writes and `>>` appends. Ansible has no module that "performs a redirect" — redirection is a shell feature the kernel wires up, not a piece of state Ansible can reason about. So to run `echo ... > file` from a play you must use `ansible.builtin.shell`, which spawns `/bin/bash`. The cost: a `shell:` task reports `changed=1` on **every** run, because Ansible cannot tell whether the file already "should" contain that text. The declarative fix is `ansible.builtin.copy` with `content:` — it compares desired vs actual and only writes when they differ, so a re-run reports `changed=0`.

```
SHELL (01a)                          ANSIBLE (01b)
─────────────────────────────       ──────────────────────────────────────
echo "x" > file.txt                  ansible.builtin.shell: 'echo "x" > file.txt'
                                       └─ changed=1 EVERY run (not idempotent)

(no equivalent — this IS the          ansible.builtin.copy:
 idempotent way to "set contents")      dest: file.txt
                                        content: "x\n"
                                       └─ changed=1 first run, changed=0 after
```

> **Why this matters:** RHCE graders re-run your play and read the PLAY RECAP. A `shell:` redirect that reports `changed=1` forever signals you reached for the wrong tool. Knowing *when* you are forced into `shell:` — and choosing a real module whenever one exists — is the core judgment the exam tests.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ansible.builtin.shell` | Run a command through `/bin/bash` so `>`/`>>` work | not idempotent — `changed=1` every run unless you add `changed_when:` |
| `ansible.builtin.copy` | Declaratively set a file's exact contents | `content:` for inline text; idempotent (`changed=0` on re-run) |
| `register:` / `ansible.builtin.debug` | Capture and print a task's result (`rc`, `stdout`, `changed`) | RHCE graders expect this audit trail |
| `ansible-playbook` | Run a playbook | run it **twice** to test idempotence |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible works, then create the durable folder that will hold our playbooks and the `/tmp` sandbox they write into. The playbooks live under `/root` so they survive a reboot; the file they create lives in volatile `/tmp`.

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

export SANDBOX=/tmp/labsandbox_01
mkdir -p "${SANDBOX}"
mkdir -p /root/rhcsa_journal/lab-01b/playbooks

ansible --version | head -2
ls -ld "${SANDBOX}" /root/rhcsa_journal/lab-01b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
  config file = /etc/ansible/ansible.cfg
drwxr-xr-x. 2 root root  6 Jun 15 17:25 /tmp/labsandbox_01
drwxr-xr-x. 2 root root  6 Jun 15 17:25 /root/rhcsa_journal/lab-01b/playbooks
Setup complete at 2026-06-15T17:25:10-04:00
exit was: 0
```

---

## TASK 1 of 2 — The boundary: `ansible.builtin.shell` `>` is not idempotent

**In plain English:** We write a playbook that does the only honest thing Ansible can do with `>` — shell out — then run it twice to watch it report `changed=1` both times, proving redirection cannot be made idempotent through `shell:`.

---

### Step 1 of 2 — Write the `shell:` redirect playbook

**In plain English:** We create `task1.yml`, which uses `ansible.builtin.shell` to run `echo ... > file`, captures the result with `register:`, and prints it — exactly the shell redirect from 01a, wrapped in a play.

```yaml
---
- name: "Lab 01b Task 1 — stdout redirect via shell (NOT idempotent)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: /tmp/labsandbox_01/notes.txt
  tasks:
    - name: "Write the file with > (shell, because no module owns redirection)"
      ansible.builtin.shell: |
        echo "ansible wrote at $(date -Is)" > "{{ target }}"
      register: write_result

    - name: "Show what the shell task reported"
      ansible.builtin.debug:
        msg:
          - "rc:      {{ write_result.rc }}"
          - "changed: {{ write_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `hosts: localhost` / `connection: local` / `gather_facts: false` → Run on this machine directly, skip SSH, and skip fact-gathering we do not need.
- `ansible.builtin.shell: |` → Use the shell module (which spawns bash) so `>` is interpreted as redirection; the `|` keeps the command as a literal block. `ansible.builtin.command` would NOT work — it has no shell, so `>` would be passed to `echo` as plain text.
- `register: write_result` → Save the task's return code, `changed` flag, and output into a variable.
- `ansible.builtin.debug: msg: [...]` → Print the captured `rc` and `changed` so you can read what happened.

**New words in this step:**

- **idempotence** — running something twice leaves the same end state with no extra change reported (`changed=0` on a re-run is the proof).

---

### Step 2 of 2 — Run it twice and watch `changed=1` both times

**In plain English:** We run the saved playbook two times in a row; a state-aware module would say `changed=0` on the second run, but this `shell:` redirect says `changed=1` every time — the boundary made visible.

```bash
ansible-playbook /root/rhcsa_journal/lab-01b/playbooks/task1.yml
ansible-playbook /root/rhcsa_journal/lab-01b/playbooks/task1.yml
cat /tmp/labsandbox_01/notes.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
ansible wrote at 2026-06-15T17:26:44-04:00
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run; `changed=1` because the file is created/overwritten.
- second `ansible-playbook ...` → Second run; `changed=1` **again** because the timestamp differs every time, so Ansible can never see the state as "already correct."
- `cat /tmp/labsandbox_01/notes.txt` → Read the file; only the latest run's line survives, because each run's `>` truncated the previous content.

**New words in this step:**

- **PLAY RECAP** — the summary line Ansible prints at the end, reporting `ok`, `changed`, and `failed` counts per host.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.shell` | spawns bash so `>` redirects | reports `changed=1` every run — not idempotent |
| `command:` vs `shell:` | `command:` has no shell | `>` becomes a literal echo argument, not a redirect |
| `register:` + `debug:` | capture and read the task result | graders expect the audit trail |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `>` appears literally in the file | You used `ansible.builtin.command` | Switch to `ansible.builtin.shell` |
| Second run shows `changed=0` | Your command is deterministic (no timestamp) | Expected for static text; the boundary still holds for dynamic output |

---

## TASK 2 of 2 — The idempotent fix: `ansible.builtin.copy`

**In plain English:** We rewrite the same "set the file's contents" outcome with `ansible.builtin.copy`, which compares desired versus actual content and only writes when they differ — then prove the re-run reports `changed=0`.

---

### Step 1 of 2 — Write the `copy` playbook

**In plain English:** We create `task2.yml`, which uses `ansible.builtin.copy` with `content:` to declare exactly what the file should contain — the declarative equivalent of `>`, but state-aware.

```yaml
---
- name: "Lab 01b Task 2 — stdout content via copy (idempotent)"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    target: /tmp/labsandbox_01/notes.txt
  tasks:
    - name: "Declare the file's exact contents (the idempotent way to 'write')"
      ansible.builtin.copy:
        dest: "{{ target }}"
        content: |
          first line
          second line
        mode: '0644'
      register: copy_result

    - name: "Show whether copy changed anything"
      ansible.builtin.debug:
        msg: "changed: {{ copy_result.changed }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.copy:` → The declarative module that sets a file to an exact state; no shell, no redirect operator needed.
- `dest: "{{ target }}"` → Where to write the file (the same sandbox path as Task 1).
- `content: |` → Inline text to place in the file; the `|` block keeps the two lines literal. This replaces `echo "..." > file`.
- `mode: '0644'` → Set the file permissions declaratively at the same time.
- `register:` + `debug:` → Capture and print the `changed` flag so the idempotence proof is readable.

**New words in this step:**

- **declarative** — you describe the desired end state and the tool figures out whether any action is needed.

---

### Step 2 of 2 — Run it twice and watch `changed=0` on the re-run

**In plain English:** We run the copy playbook twice; the first run writes the file (`changed=1`), and the second run sees the contents already match and does nothing (`changed=0`) — exactly the idempotence the `shell:` redirect could never give us.

```bash
ansible-playbook /root/rhcsa_journal/lab-01b/playbooks/task2.yml
ansible-playbook /root/rhcsa_journal/lab-01b/playbooks/task2.yml
cat /tmp/labsandbox_01/notes.txt
echo "exit was: $?"
```

**Expected output:**

```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0
first line
second line
exit was: 0
```

**Line-by-line breakdown:**

- first `ansible-playbook ...` → First run writes the file because it does not yet match the declared content; `changed=1`.
- second `ansible-playbook ...` → Second run compares desired vs actual, finds them identical, and makes no change; `changed=0` — the idempotence proof.
- `cat /tmp/labsandbox_01/notes.txt` → Confirm the file holds exactly the two declared lines.

**New words in this step:**

- **content drift** — when a file's actual contents differ from the declared desired state; `copy` corrects it and reports `changed=1` only then.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ansible.builtin.copy` with `content:` | declaratively sets file contents | re-run is `changed=0` — the win condition |
| `mode: '0644'` | sets permissions in the same task | forgetting it leaves default umask perms |
| idempotence | same end state on every run | `shell:` redirects can never achieve it for dynamic data |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Second run still `changed=1` | A trailing-newline or content mismatch | Match `content:` exactly, including the final newline |
| `dest is a directory` error | `dest` points at a folder | Give `dest` a full file path |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the `shell:` redirect playbook
- [ ] Task 1 · Step 2 — Run it twice and watch `changed=1` both times
- [ ] Task 2 · Step 1 — Write the `copy` playbook
- [ ] Task 2 · Step 2 — Run it twice and watch `changed=0` on the re-run

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Using `command:` for a redirect | `>` ends up as literal text in the file | Use `shell:` when you truly need a shell operator |
| Using `shell:` `>` for static content | `changed=1` on every run | Use `ansible.builtin.copy` with `content:` |
| Forgetting to test the re-run | Non-idempotent play ships unnoticed | Always run the playbook twice and read the PLAY RECAP |

---

## 📌 Exam Strategy

The RHCE question is rarely "redirect output" — it is "manage this file's contents idempotently." Reach for a real module (`copy`, `template`, `lineinfile`, `blockinfile`) first; drop to `ansible.builtin.shell` only when no module can express what you need, and mark such tasks honestly with `changed_when:` so the recap stays truthful.

- Run every play twice; `changed=0` on the second run is the acceptance test.
- Prefer `copy: content:` over `shell: echo > file` whenever the content is known and static.
- When you must use `shell:`, add `register:` + `debug:` so the grader can see what happened.

---

## 🔗 Related Labs

- [Lab 01a — Stdout Redirection (RHCSA)](../lab-01a-stdout-redirection-rhcsa/) — the hand-typed shell version this play mirrors
- [Lab 01c — Stdout Redirection (Verify)](../lab-01c-stdout-redirection-verify/) — audit the files both 01a and 01b produced
- [Lab 02b — Stderr Redirection (Ansible)](../lab-02b-stderr-redirection-ansible/) — the stderr analog using `register:` and `stderr_lines`

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
