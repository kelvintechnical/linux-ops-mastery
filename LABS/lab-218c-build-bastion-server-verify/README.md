# Lab 218c: Build a Bastion Server (Verify) — `ss -H -tln`, `systemctl is-active`, assertion scripting

**Series:** linux-ops-mastery — Security Administration · **Lab 218c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (confirming boot target and service posture), RHCE EX294 (validating a hardening playbook's result), SRE/Security (posture attestation, listener inventory)  
**Prerequisite:** [Lab 218a](../lab-218a-build-bastion-server-rhcsa/) and [Lab 218b](../lab-218b-build-bastion-server-ansible/) completed, on a RHEL 9 / Rocky / Alma sandbox you can `sudo` on  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Attest the bastion posture from 218a/218b with hard, scriptable evidence rather than a glance. You will assert the box boots to `multi-user.target`, that `sshd` is both active *and* enabled, and — the heart of the audit — that the **only** non-loopback TCP listener is port 22. To do that you will learn `ss -H -tln` (headerless listener output), filter out loopback, and count the survivors with `wc -l`, turning "is this SSH-only?" into a number you can pass/fail on. A throwaway listener is added and removed so you can watch the count rise and fall.

---

## 🧠 Concept

A bastion attestation is three assertions: the right boot target, the right service running, and nothing extra listening. `systemctl get-default` and `systemctl is-active`/`is-enabled` answer the first two as words and exit codes. The third is the interesting one: `ss -tln` lists listening TCP sockets, and the `-H` flag drops the header line so every remaining line is a real listener — perfect for counting. Filtering out `127.0.0.1` and `::1` leaves only the *externally reachable* listeners; on a true bastion that count should be exactly the number of SSH bindings (IPv4 + IPv6). Comparing that number to an expected value is a precise, repeatable "SSH-only" test.

```
systemctl get-default          → multi-user.target   (assert == expected)
systemctl is-active sshd       → active   (exit 0)
ss -H -tln                     → one line PER listener (no header to skip)
ss -H -tln | grep -Ev '127.0.0.1|::1'   → only externally reachable listeners
            | wc -l            → the number you assert against
```

> **Why this matters:** "Looks SSH-only" is not an attestation; a counted, loopback-filtered listener total is. This is exactly how a security review or a grader script proves a host's surface — and how you catch a stray service that crept back after a reboot.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `ss -H -tln` | List listening TCP sockets with **no** header line | `-H` removes the header so each line is a listener; `-t -l -n` = TCP, listening, numeric |
| `grep -Ev '<pat>'` | Drop lines matching a pattern (here loopback) | `-E` extended regex, `-v` invert (exclude) |
| `wc -l` | Count the surviving lines as a bare number | feed via a pipe; the count is the verdict |
| `systemctl get-default` | Show the boot target to assert against | a bastion must be `multi-user.target` |
| `systemctl is-active <unit>` | Read running state as word + exit code | exit `0` = active; scriptable pass/fail |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We create one sandbox folder for any scratch evidence; the posture checks themselves are read-only, so nothing on the system is altered by setup.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-218
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

echo "Bastion verify workspace ready at $(date -Is)"
ls -ld "$LAB_ROOT"
echo "exit was: $?"
```

**Expected output:**

```
Bastion verify workspace ready at 2026-06-15T17:55:03-04:00
drwxr-xr-x. 2 root root 6 Jun 15 17:55 /tmp/lab-218
exit was: 0
```

---

## TASK 1 of 2 — Assert the boot target and required service

**In plain English:** We prove the box boots to a text target and that `sshd` is both active now and enabled at boot, turning each check into an explicit OK/FAIL verdict.

---

### Step 1 of 2 — Assert the default target is `multi-user.target`

**In plain English:** We capture `systemctl get-default` and assert it equals the bastion-correct text target, flagging a graphical target as a failure.

```bash
target=$(systemctl get-default)
test "$target" = "multi-user.target" \
  && echo "TARGET OK: $target" \
  || echo "TARGET FAIL: $target (expected multi-user.target)"
echo "exit was: $?"
```

**Expected output:**

```
TARGET OK: multi-user.target
exit was: 0
```

**Line-by-line breakdown:**

- `target=$(systemctl get-default)` → Capture the default boot target into a variable so we can compare it.
- `test "$target" = "multi-user.target" && ... || ...` → Assert it is exactly the text-mode target; a `graphical.target` here is a bastion red flag and prints FAIL.
- `echo "exit was: $?"` → Record the exit status of the assertion for a scriptable signal.

**New words in this step:**

- **attestation** — a proven, evidence-backed statement about a system's configuration.
- **boot target** — the systemd unit that defines the system state reached at boot (`multi-user.target` = text, multi-user).

---

### Step 2 of 2 — Assert `sshd` is active *and* enabled

**In plain English:** We check both that `sshd` is running now (`is-active`) and that it will start at boot (`is-enabled`), since a bastion needs both to be true.

```bash
a=$(systemctl is-active sshd); ra=$?
e=$(systemctl is-enabled sshd); re=$?
echo "is-active: $a (exit $ra) | is-enabled: $e (exit $re)"
test "$a" = "active" -a "$e" = "enabled" \
  && echo "SSHD OK: active and enabled" \
  || echo "SSHD FAIL: active=$a enabled=$e"
```

**Expected output:**

```
is-active: active (exit 0) | is-enabled: enabled (exit 0)
SSHD OK: active and enabled
```

**Line-by-line breakdown:**

- `a=$(systemctl is-active sshd); ra=$?` → Capture the running state word and its exit code (`0` when active).
- `e=$(systemctl is-enabled sshd); re=$?` → Capture the boot state word and its exit code (`0` when enabled).
- `echo "is-active: ... is-enabled: ..."` → Surface both words and codes for the record.
- `test "$a" = "active" -a "$e" = "enabled" && ... || ...` → Assert *both* conditions with `-a` (logical AND); a bastion that is active-but-disabled would lock you out after reboot.

**New words in this step:**

- **`test -a`** — the logical AND operator inside `test`, true only when both expressions are true.
- **active vs enabled** — running *now* versus configured to start *at boot*; a bastion needs both.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `get-default` | the boot target verdict | `graphical.target` on a server wastes surface |
| `is-active` + `is-enabled` | now vs at-boot, together | active-but-disabled dies on reboot |
| `test -a` | AND two assertions | a single failing side flips the whole verdict |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `TARGET FAIL: graphical.target` | Box installed with a GUI | `sudo systemctl set-default multi-user.target` |
| `SSHD FAIL: ... enabled=disabled` | `sshd` not set to start at boot | `sudo systemctl enable --now sshd` |

---

## TASK 2 of 2 — Count the listeners and prove SSH-only

**In plain English:** We count externally reachable TCP listeners with `ss -H -tln` filtered of loopback, add a throwaway listener to watch the count rise, then remove it and assert the count returns to SSH-only.

---

### Step 1 of 2 — Count externally reachable listeners (baseline)

**In plain English:** We list listeners headerless, drop the loopback addresses, count what remains, and record it as the SSH-only baseline.

```bash
ss -H -tln | grep -Ev '127\.0\.0\.1|\[::1\]' | tee "$LAB_ROOT/listeners-before.txt"
base=$(ss -H -tln | grep -Ev '127\.0\.0\.1|\[::1\]' | wc -l)
echo "external listeners (baseline): $base"
```

**Expected output:**

```
LISTEN 0      128      0.0.0.0:22      0.0.0.0:*
LISTEN 0      128         [::]:22         [::]:*
external listeners (baseline): 2
```

**Line-by-line breakdown:**

- `ss -H -tln | grep -Ev '127\.0\.0\.1|\[::1\]'` → List listening TCP sockets without the header (`-H`), then exclude the IPv4 and IPv6 loopback addresses so only externally reachable listeners remain; `tee` saves the snapshot.
- `base=$(... | wc -l)` → Count those listeners; on a clean bastion this is `2` (SSH on IPv4 `0.0.0.0:22` and IPv6 `[::]:22`).
- `echo "external listeners (baseline): $base"` → Record the baseline count for the comparison in Step 2.

**New words in this step:**

- **`ss -H`** — suppresses the header row so every output line is a real socket entry, ideal for counting.
- **loopback** — the `127.0.0.1` / `::1` addresses reachable only from the host itself; excluded from the external surface.

---

### Step 2 of 2 — Add an extra listener, watch the count, then prove it returns

**In plain English:** We open a throwaway port to make the count rise above baseline, assert the rise, then close it and assert the count drops back to the SSH-only baseline.

```bash
sudo tee /etc/systemd/system/lab218-verify.socket >/dev/null <<'EOF'
[Unit]
Description=Lab 218c throwaway verify listener
[Socket]
ListenStream=0.0.0.0:2189
[Install]
WantedBy=sockets.target
EOF
sudo tee /etc/systemd/system/lab218-verify.service >/dev/null <<'EOF'
[Service]
ExecStart=/usr/bin/cat
StandardInput=socket
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now lab218-verify.socket

now=$(ss -H -tln | grep -Ev '127\.0\.0\.1|\[::1\]' | wc -l)
test "$now" -gt "$base" && echo "RISE OK: $now > baseline $base" || echo "RISE FAIL"

sudo systemctl disable --now lab218-verify.socket
after=$(ss -H -tln | grep -Ev '127\.0\.0\.1|\[::1\]' | wc -l)
test "$after" = "$base" && echo "SSH-ONLY OK: back to $after" || echo "SSH-ONLY FAIL: $after"
```

**Expected output:**

```
Created symlink /etc/systemd/system/sockets.target.wants/lab218-verify.socket → /etc/systemd/system/lab218-verify.socket.
RISE OK: 3 > baseline 2
Removed "/etc/systemd/system/sockets.target.wants/lab218-verify.socket".
SSH-ONLY OK: back to 2
```

**Line-by-line breakdown:**

- the two `tee` heredocs + `daemon-reload` + `enable --now` → Add a throwaway externally-bound listener on `0.0.0.0:2189` so the external count rises by one.
- `now=$(... | wc -l)` and `test "$now" -gt "$base"` → Recount and assert the number *increased* — proof the new doorway registered.
- `sudo systemctl disable --now lab218-verify.socket` → Close the throwaway listener.
- `after=$(... | wc -l)` and `test "$after" = "$base"` → Recount and assert we are back to the SSH-only baseline — the attestation that the surface is restored.

**New words in this step:**

- **baseline** — the known-good count you compare future measurements against.
- **delta** — the change in a measured value (here, the listener count rising by one then returning).

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `ss -H -tln \| wc -l` | counts listeners precisely | without `-H` you'd count the header line too |
| loopback filter | isolates the external surface | forgetting it inflates the count with local-only sockets |
| baseline compare | turns posture into pass/fail | compare to a number, not a vibe |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| Count includes a header line | You omitted `-H` | Use `ss -H -tln` so only listeners are counted |
| `SSH-ONLY FAIL` after cleanup | The throwaway socket wasn't disabled with `--now` | Run `sudo systemctl disable --now lab218-verify.socket` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the default target is `multi-user.target`
- [ ] Task 1 · Step 2 — Assert `sshd` is active *and* enabled
- [ ] Task 2 · Step 1 — Count externally reachable listeners (baseline)
- [ ] Task 2 · Step 2 — Add an extra listener, watch the count, then prove it returns

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it added a throwaway verify socket+service), and `rm` alone will NOT undo the daemon registration. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo systemctl disable --now lab218-verify.socket 2>/dev/null
sudo rm -f /etc/systemd/system/lab218-verify.socket /etc/systemd/system/lab218-verify.service
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
| Counting `ss` output with the header | Listener count is off by one | Always use `-H` when counting |
| Forgetting the loopback filter | Local-only sockets inflate the surface | Exclude `127.0.0.1` and `[::1]` before counting |
| Eyeballing "SSH-only" | A stray listener slips past | Assert against a numeric baseline |

---

## 📌 Exam Strategy

Posture verification is counting, not glancing. Capture `get-default` and `is-active`/`is-enabled` as words+codes, then count loopback-filtered listeners with `ss -H -tln | wc -l` and compare to a baseline. The habit of expressing "SSH-only" as a number you assert against is what makes your attestation reproducible — and is exactly what a grader script checks.

- `ss -H -tln` is your countable listener feed — remember `-H` drops the header.
- Filter loopback first so you count only the externally reachable surface.
- Assert `get-default == multi-user.target` and `sshd` active **and** enabled together.

---

## 🔗 Related Labs

- [Lab 218a — Build a Bastion Server (RHCSA)](../lab-218a-build-bastion-server-rhcsa/) — the hand-typed posture work this lab attests
- [Lab 218b — Build a Bastion Server (Ansible)](../lab-218b-build-bastion-server-ansible/) — the playbook whose result you verify with counts
- [Lab 216c — Service Isolation Bastion Host (Verify)](../lab-216c-service-isolation-bastion-host-verify/) — the same assertion discipline applied to disable/mask

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
