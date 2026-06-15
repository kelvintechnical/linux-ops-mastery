# Lab 02b: Stderr Redirection (Ansible) — `register:` `stderr_lines`, `failed_when:`

**Series:** linux-ops-mastery — Shells, Terminals & Redirection · **Lab 02b of the Novice → RHCA path**  
**Certifications covered:** RHCE EX294 (shell tasks expose stdout and stderr via `register:`), DevOps (separating expected errors from real failures in CI), SRE (alerting on unexpected stderr while tolerating known noise)  
**Prerequisite:** [Lab 02a](../lab-02a-stderr-redirection-rhcsa/) completed, and a working Ansible control node (`ansible --version` succeeds)  
**Time Estimate:** 30–40 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Express Lab 02a's `2>` / `2>/dev/null` skills in Ansible. When a play runs a shell command, `ansible.builtin.shell` automatically splits the output into `stdout_lines` (FD 1) and `stderr_lines` (FD 2) on the registered result — no `2>` required. You will capture and inspect both streams, then learn `failed_when:`, the surgical way to tolerate known stderr (like `Permission denied`) while still failing on genuinely unexpected errors — far better than the blunt `ignore_errors: yes`.

---

## 🧠 Concept

In 02a you wrote `2> errors.txt` to split stderr off to its own file. In Ansible you do not have to: `register:` captures the module result, and `result.stdout_lines` / `result.stderr_lines` give you FD 1 and FD 2 already separated. The catch is that a task can finish with `rc=0` yet still produce stderr — invisible unless you explicitly check `stderr_lines`. And for error handling, `ignore_errors: yes` swallows *everything* (including real failures), while `failed_when:` lets you declare exactly which condition counts as failure.

```
SHELL (02a)                       ANSIBLE (02b)
──────────────────────────        ─────────────────────────────────────
find ... 2> errors.txt            ansible.builtin.shell: find ...
                                  register: result
cat log-files.txt   (FD1)         result.stdout_lines  (list, FD1)
cat log-errors.txt  (FD2)         result.stderr_lines  (list, FD2)
echo $?             (exit)        result.rc            (exit code)
```

> **Why this matters:** Teams ship playbooks that print hundreds of warnings every run and never notice, because they only read the PLAY RECAP. Checking `stderr_lines | length` is the Ansible habit that mirrors "capture and read stderr." And `failed_when:` is what lets a play tolerate `Permission denied` without going blind to a real `No such file or directory`.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `register:` | Capture a task's full result (`rc`, `stdout_lines`, `stderr_lines`) | the Ansible equivalent of `> file` + `2> file` + `echo $?` |
| `result.stderr_lines` | The FD 2 stream as a list, auto-split | always check `\| length` — non-zero stderr with `rc=0` is invisible otherwise |
| `failed_when:` | Declare the exact condition that means failure | surgical — tolerate known errors, still catch unexpected ones |
| `ignore_errors: true` | Continue the play even if the task fails | blunt — hides real failures; prefer `failed_when:` |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** Confirm Ansible and `localhost` work, then create the durable playbook folder and the `/tmp` working directory the plays read into. The plays run `find /var/log`, which yields both log paths (stdout) and `Permission denied` (stderr).

> Run this block **once** before Task 1. It builds the clean, private
> workspace that both tasks depend on.

```bash
sudo -i

mkdir -p /tmp/lab02b
mkdir -p /root/rhcsa_journal/lab-02b/playbooks

ansible --version | head -1
ansible localhost -m ping --connection=local 2>/dev/null \
    && echo "localhost reachable" || echo "localhost ping failed"
ls -ld /tmp/lab02b /root/rhcsa_journal/lab-02b/playbooks
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
ansible [core 2.16.x]
localhost reachable
drwxr-xr-x. 2 root root  6 Jun 15 17:40 /tmp/lab02b
drwxr-xr-x. 2 root root  6 Jun 15 17:40 /root/rhcsa_journal/lab-02b/playbooks
Setup complete at 2026-06-15T17:40:00-04:00
exit was: 0
```

---

## TASK 1 of 2 — Capture and inspect `stderr_lines`

**In plain English:** We write a playbook that runs `find /var/log` through `ansible.builtin.shell`, registers the result, and prints the stdout and stderr line counts — proving the module splits the two streams the way `>` and `2>` did by hand.

---

### Step 1 of 2 — Write the capture playbook

**In plain English:** We create `task1.yml`, which runs the `find`, tolerates its non-zero exit with `failed_when: false`, and dumps `rc`, `stdout_lines | length`, and `stderr_lines | length` so both streams are visible.

```yaml
---
- name: "Lab 02b Task 1 — capture stderr_lines from ansible.builtin.shell"
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    output_dir: /tmp/lab02b
  tasks:
    - name: "Find .log files — register splits stdout and stderr automatically"
      ansible.builtin.shell:
        cmd: "find /var/log -name '*.log' -type f"
      register: find_result
      failed_when: false
      changed_when: false

    - name: "Show the split capture"
      ansible.builtin.debug:
        msg:
          - "rc:           {{ find_result.rc }}"
          - "stdout lines: {{ find_result.stdout_lines | length }}"
          - "stderr lines: {{ find_result.stderr_lines | length }}"

    - name: "Save the stderr stream to a file (the 2> equivalent)"
      ansible.builtin.copy:
        dest: "{{ output_dir }}/log-errors.txt"
        content: "{{ find_result.stderr }}\n"
        mode: '0644'
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `ansible.builtin.shell: cmd: "find ..."` → Run the find through a shell; the module captures FD 1 and FD 2 into the registered result separately.
- `failed_when: false` → `find` returns `rc=1` when it hits `Permission denied`; without this the play would abort before we could inspect stderr.
- `changed_when: false` → `find` is read-only, so mark it as never changing — keeps the PLAY RECAP honest.
- `debug: msg:` with `{{ find_result.stderr_lines | length }}` → Print the stderr line count; this explicit check is the whole point — `rc=0` alone would hide non-empty stderr.
- `ansible.builtin.copy: content: "{{ find_result.stderr }}\n"` → Write the captured stderr to a file, the declarative equivalent of `2> log-errors.txt`.

**New words in this step:**

- **`stderr_lines`** — the registered result's FD 2 content as a list, one element per error line.

---

### Step 2 of 2 — Run it and confirm stream separation

**In plain English:** We run the playbook, read the debug output to see non-zero stdout and stderr counts, then check the saved stderr file holds the `Permission denied` lines.

```bash
ansible-playbook /root/rhcsa_journal/lab-02b/playbooks/task1.yml
echo "--- saved stderr file ---"
grep -c 'Permission denied' /tmp/lab02b/log-errors.txt
echo "exit was: $?"
```

**Expected output:**

```
TASK [Show the split capture] **************************************************
ok: [localhost] => {
    "msg": [
        "rc:           1",
        "stdout lines: 21",
        "stderr lines: 3"
    ]
}
PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=1    unreachable=0    failed=0
--- saved stderr file ---
3
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook .../task1.yml` → Run the play; the debug task shows `rc=1` (find hit denied dirs) yet `stdout lines: 21` — proof that `rc` alone is not the whole story.
- `grep -c 'Permission denied' /tmp/lab02b/log-errors.txt` → Count the error lines saved to disk; matches the `stderr lines: 3` from the debug output, confirming the stderr stream was captured.

**New words in this step:**

- **`| length`** — a Jinja2 filter that counts the elements in a list.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `register:` split | `stdout_lines` = FD 1, `stderr_lines` = FD 2 | automatic — no `2>` needed |
| `failed_when: false` | tolerate any `rc` | required when a command legitimately exits non-zero |
| `stderr_lines \| length` | reveal hidden stderr | `rc=0` with non-empty stderr is invisible without this (T02-C) |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `stderr_lines` is empty | Running with full read access to `/var/log` | Target a restricted dir, e.g. `find /var/log/audit` |
| Play aborts on the find task | `failed_when: false` missing | Add it so `rc=1` is tolerated |

---

## TASK 2 of 2 — Selective failure with `failed_when:` vs `ignore_errors:`

**In plain English:** We prove `failed_when:` is a scalpel and `ignore_errors:` is a sledgehammer — one fails only on unexpected stderr while passing known `Permission denied`, the other silently swallows a genuinely broken command.

---

### Step 1 of 2 — Write the comparison playbook

**In plain English:** We create `task2.yml` with three tasks: a `find` that passes because only `Permission denied` appears, a broken path under `ignore_errors:` that fails silently, and the same broken path under `failed_when:` that is correctly caught.

```yaml
---
- name: "Lab 02b Task 2 — failed_when: vs ignore_errors: (T02-D)"
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: "Pass when only Permission denied is in stderr"
      ansible.builtin.shell:
        cmd: "find /var/log -name '*.log' -type f"
      register: selective
      changed_when: false
      failed_when: >
        selective.rc != 0 and
        (selective.stderr_lines | reject('search', 'Permission denied') | list | length) > 0

    - name: "ignore_errors demo — broken path fails SILENTLY"
      ansible.builtin.shell:
        cmd: "find /DOES_NOT_EXIST -type f"
      register: broken
      changed_when: false
      ignore_errors: true

    - name: "Show that ignore_errors hid the real failure"
      ansible.builtin.debug:
        msg: "broken rc={{ broken.rc }} stderr={{ broken.stderr_lines }}"
```

**Expected output:**

```
(this is the saved playbook file — no output until you run it in Step 2)
```

**Line-by-line breakdown:**

- `failed_when: > selective.rc != 0 and (... | reject('search', 'Permission denied') | list | length) > 0` → Fail only if, after discarding `Permission denied` lines, any unexpected stderr remains. Known noise passes; real errors fail.
- `reject('search', 'Permission denied')` → A Jinja2 filter that drops list elements matching the pattern, leaving only unexpected lines.
- `ignore_errors: true` on the broken path → The task fails (the path does not exist) but the play continues — the failure is hidden in plain sight.
- `debug:` printing `broken.rc` and `broken.stderr_lines` → Shows the real error that `ignore_errors:` swallowed.

**New words in this step:**

- **`reject('search', PAT)`** — a Jinja2 filter that removes list items matching a regex, keeping the rest.

---

### Step 2 of 2 — Run it and read the PLAY RECAP

**In plain English:** We run the playbook and read the recap: the selective task passes (only expected errors), and the `ignore_errors:` task shows up as `ignored=1` — a clue that is easy to miss, which is exactly the danger.

```bash
ansible-playbook /root/rhcsa_journal/lab-02b/playbooks/task2.yml
echo "exit was: $?"
```

**Expected output:**

```
TASK [Pass when only Permission denied is in stderr] ***************************
ok: [localhost]
TASK [ignore_errors demo — broken path fails SILENTLY] *************************
fatal: [localhost]: FAILED! => {...} ...ignoring
TASK [Show that ignore_errors hid the real failure] ***************************
ok: [localhost] => {
    "msg": "broken rc=1 stderr=[\"find: '/DOES_NOT_EXIST': No such file or directory\"]"
}
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=0    unreachable=0    failed=0    ignored=1
exit was: 0
```

**Line-by-line breakdown:**

- `ansible-playbook .../task2.yml` → Run the play; the first task is `ok` because only `Permission denied` appeared (tolerated by `failed_when:`).
- the `...ignoring` line → The broken-path task actually failed, but `ignore_errors:` let the play continue — only the small `ignored=1` in the recap hints at it.
- the debug `msg` → Surfaces the real `No such file or directory` error that would otherwise be invisible.
- `PLAY RECAP ... ignored=1` → The one signal that a real failure was swallowed; `failed_when:` would have stopped the play loudly instead.

**New words in this step:**

- **`ignored=N`** in PLAY RECAP — the count of tasks that failed but were allowed to continue via `ignore_errors:`.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `failed_when:` | fail only on YOUR condition | the surgical tool — tolerate known stderr |
| `ignore_errors: true` | continue past any failure | the sledgehammer — hides real failures (T02-D) |
| `reject('search', PAT)` | drop matching list items | leaves only unexpected errors to test |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Selective task fails on expected errors | `reject` pattern typo | Match the exact `Permission denied` string |
| `reject` raises a Jinja2 error | Ansible too old | Upgrade `ansible-core` or use `selectattr` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Write the capture playbook
- [ ] Task 1 · Step 2 — Run it and confirm stream separation
- [ ] Task 2 · Step 1 — Write the comparison playbook
- [ ] Task 2 · Step 2 — Run it and read the PLAY RECAP

---

## ⚠️ Common Pitfalls

| Mistake | Symptom | Fix |
|---|---|---|
| Only checking `rc` | Non-empty stderr goes unnoticed | Log `stderr_lines \| length` in a debug task |
| Reaching for `ignore_errors: yes` | Real failures swallowed silently | Use `failed_when:` to target only known-OK errors |
| Omitting `changed_when: false` | Read-only tasks report `changed=1` | Mark read-only shell tasks honestly |

---

## 📌 Exam Strategy

On the RHCE, error handling is graded on judgment: you are expected to distinguish *expected* output (a `Permission denied` you anticipate) from *real* failures. `failed_when:` with a `reject('search', ...)` filter is the idiom that expresses that judgment; `ignore_errors:` rarely is. Always register shell results and inspect `stderr_lines` so the play's behavior is auditable.

- Default to `failed_when:`; treat `ignore_errors:` as a last resort you can justify out loud.
- Add `changed_when: false` to read-only shell tasks so the recap stays truthful.
- Print `stderr_lines | length` in a debug task — it is the Ansible version of "capture and read stderr."

---

## 🔗 Related Labs

- [Lab 02a — Stderr Redirection (RHCSA)](../lab-02a-stderr-redirection-rhcsa/) — the shell `2>` skills this play mirrors
- [Lab 02c — Stderr Redirection (Verify)](../lab-02c-stderr-redirection-verify/) — audit both 02a and 02b stderr evidence
- [Lab 01b — Stdout Redirection (Ansible)](../lab-01b-stdout-redirection-ansible/) — the previous b-lab: `shell:` vs `copy:` idempotence

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
