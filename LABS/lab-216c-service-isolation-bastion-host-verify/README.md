# Lab 216c: Service Isolation Bastion Host (Verify) — `systemctl is-enabled`, `readlink`

**Series:** linux-ops-mastery — Security Administration · **Lab 216c of the Novice → RHCA path**  
**Certifications covered:** RHCSA EX200 (verifying service boot state after `enable`/`disable`/`mask`), RHCE EX294 (proving a playbook converged on the intended state), SRE/Security (post-change verification, attack-surface evidence)  
**Prerequisite:** [Lab 216a](../lab-216a-service-isolation-bastion-host-rhcsa/) and [Lab 216b](../lab-216b-service-isolation-bastion-host-ansible/) completed, on a RHEL 9 / Rocky / Alma sandbox you can `sudo` on  
**Time Estimate:** 20–30 minutes  
**Difficulty:** Beginner → Intermediate

---

## 🎯 Objective

Take the auditor's seat for the isolation work from 216a/216b: instead of *performing* `disable` and `mask`, you *prove* each transition happened with hard, scriptable evidence. You will read `systemctl is-enabled` as a one-word verdict **and** decode its exit code, follow the actual symlink on disk with `readlink -f` to confirm whether a unit points at a real file or at `/dev/null`, and prove that a masked unit genuinely refuses to start. Everything runs against the same harmless `lab216-dummy.service` so the audit is fully reversible.

---

## 🧠 Concept

Verification means asking the system to *prove* a fact rather than trusting that an earlier command worked. For service isolation, three facts matter and three tools answer them. `systemctl is-enabled <unit>` prints `enabled` / `disabled` / `masked` and — the subtlety graders test — returns a **non-zero exit code** for `disabled` and `masked`, which is the state itself, not an error. `readlink -f <path>` resolves a symlink to its final target, so you can see with your own eyes that an enabled unit's boot symlink lands on the real `.service` file while a masked unit's path resolves to `/dev/null`. Finally, `systemctl start` on a masked unit *fails by design*, and capturing that failure exit code is the proof that mask is stronger than disable.

```
systemctl is-enabled dummy   → "enabled"   exit 0
                             → "disabled"  exit 1   (state, NOT an error)
                             → "masked"    exit 1   (state, NOT an error)

readlink -f /etc/systemd/system/multi-user.target.wants/dummy
                             → /etc/systemd/system/lab216-dummy.service   (enabled)
readlink -f /etc/systemd/system/lab216-dummy.service
                             → /dev/null                                   (masked)
```

> **Why this matters:** "I ran `systemctl mask`" is a claim; `readlink -f` resolving to `/dev/null` plus a failed `start` is *proof*. On the exam and on call, the evidence — not your memory — is what closes the ticket, and it is the same evidence a grader script checks.

---

## 📚 Command Reference

| Command | Purpose | Critical flags |
|---|---|---|
| `systemctl is-enabled <unit>` | Print the boot state in one word and signal it via exit code | `enabled`=0; `disabled`/`masked`=non-zero (the state, not a failure) |
| `readlink -f <path>` | Resolve a symlink all the way to its final target | `-f` follows every hop; reveals `/dev/null` for a masked unit |
| `test "$a" = "$b"` / `[ ... ]` | Assert two strings match, turning a check into pass/fail | combine with `&&`/`||` to print `OK`/`FAIL` |
| `systemctl start <unit>; echo $?` | Attempt a start and capture the exit code | a masked unit returns non-zero — the proof of isolation |
| `systemctl show -p <prop> <unit>` | Read one machine-parseable unit property | `-p UnitFileState` / `-p LoadState` give scriptable values |

---

## 🧰 LAB-WIDE SETUP

**In plain English:** We create a single sandbox folder and re-install the harmless `lab216-dummy.service`, then enable it, so there is a known-good "enabled" unit to audit through the disable and mask transitions.

> Run this block **once** before Task 1. It defines a single sandbox root (`LAB_ROOT`) that every file in this lab lives under, so Teardown can wipe it in one safe command.

```bash
export LAB_ROOT=/tmp/lab-216
mkdir -p "$LAB_ROOT"
cd "$LAB_ROOT"

sudo tee /etc/systemd/system/lab216-dummy.service >/dev/null <<'EOF'
[Unit]
Description=Lab 216 harmless dummy service (safe to enable/disable/mask)

[Service]
Type=oneshot
ExecStart=/bin/true
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lab216-dummy.service
systemctl is-enabled lab216-dummy.service
echo "Setup complete at $(date -Is)"
echo "exit was: $?"
```

**Expected output:**

```
Created symlink /etc/systemd/system/multi-user.target.wants/lab216-dummy.service → /etc/systemd/system/lab216-dummy.service.
enabled
Setup complete at 2026-06-15T17:50:03-04:00
exit was: 0
```

---

## TASK 1 of 2 — Verify the enabled → disabled transition

**In plain English:** We assert the unit really is enabled (word + symlink target), then disable it and assert the boot symlink is gone and the state flipped to `disabled` — proving the 216a/216b disable step with evidence.

---

### Step 1 of 2 — Assert the "enabled" state with word and symlink

**In plain English:** We confirm `is-enabled` says `enabled` and that the boot symlink resolves to the real unit file, turning both checks into explicit OK/FAIL lines.

```bash
state=$(systemctl is-enabled lab216-dummy.service)
test "$state" = "enabled" && echo "STATE OK: $state" || echo "STATE FAIL: $state"

link=$(readlink -f /etc/systemd/system/multi-user.target.wants/lab216-dummy.service)
test "$link" = "/etc/systemd/system/lab216-dummy.service" \
  && echo "SYMLINK OK: $link" || echo "SYMLINK FAIL: $link"
```

**Expected output:**

```
STATE OK: enabled
SYMLINK OK: /etc/systemd/system/lab216-dummy.service
```

**Line-by-line breakdown:**

- `state=$(systemctl is-enabled lab216-dummy.service)` → Capture the one-word boot state into a variable so we can compare it instead of eyeballing it.
- `test "$state" = "enabled" && ... || ...` → Assert the word is exactly `enabled`; the `&&`/`||` prints a clear `OK`/`FAIL` verdict, the building block of every check in this lab.
- `link=$(readlink -f .../lab216-dummy.service)` → Resolve the boot symlink to its final target; `-f` follows the link all the way to the real file.
- the second `test ... && ... || ...` → Assert that the resolved target is the actual unit file — concrete proof the unit is wired to start at boot.

**New words in this step:**

- **`readlink -f`** — resolves a symbolic link to its final, fully-canonical target path.
- **assertion** — a check that compares actual to expected and yields a pass/fail, the heart of verification.

---

### Step 2 of 2 — Disable, then assert the symlink is gone

**In plain English:** We disable the unit and prove both that `is-enabled` now reports `disabled` (with its expected non-zero exit) and that the boot symlink no longer exists.

```bash
sudo systemctl disable --now lab216-dummy.service
state=$(systemctl is-enabled lab216-dummy.service); rc=$?
echo "word: $state | is-enabled exit: $rc"
test "$state" = "disabled" && echo "STATE OK: disabled" || echo "STATE FAIL: $state"
test ! -e /etc/systemd/system/multi-user.target.wants/lab216-dummy.service \
  && echo "SYMLINK OK: removed" || echo "SYMLINK FAIL: still present"
```

**Expected output:**

```
Removed "/etc/systemd/system/multi-user.target.wants/lab216-dummy.service".
word: disabled | is-enabled exit: 1
STATE OK: disabled
SYMLINK OK: removed
```

**Line-by-line breakdown:**

- `sudo systemctl disable --now lab216-dummy.service` → Remove the boot symlink and stop the unit, the action we are about to verify.
- `state=$(...); rc=$?` → Capture *both* the printed word and the exit code; `is-enabled` returns `1` for `disabled`, which we record rather than treat as an error.
- `echo "word: $state | is-enabled exit: $rc"` → Show that a non-zero exit accompanies a perfectly normal `disabled` state — the classic exam trap, made visible.
- `test ! -e .../lab216-dummy.service && ... || ...` → Assert the boot symlink path no longer exists (`! -e`), proving the disable removed it.

**New words in this step:**

- **`! -e`** — a `test` expression that is true when a path does **not** exist; used here to prove the symlink was removed.
- **exit code as state** — `is-enabled` encodes the unit's state in its exit code, so non-zero is information, not failure.

---

### Concept card (Task 1)

| Concept | What it does | Exam trap |
|---|---|---|
| `is-enabled` word | the human verdict (`enabled`/`disabled`) | trust the printed word, not just `$?` |
| `is-enabled` exit code | non-zero for `disabled`/`masked` | non-zero here is the state, not an error |
| `readlink -f` | resolves a symlink to its real target | a missing symlink errors — guard with `test -e` first |

---

### Troubleshoot (Task 1)

| Symptom | Likely cause | Fix |
|---|---|---|
| `readlink` prints nothing / errors | The symlink path does not exist yet | Run the enable step first, or guard with `test -e` |
| `STATE FAIL: static` | The unit has no `[Install]` section | Re-run setup so the unit's `WantedBy=` is present |

---

## TASK 2 of 2 — Verify the masked state and that start is blocked

**In plain English:** We mask the unit and prove the strongest isolation with two pieces of evidence — the unit path now resolves to `/dev/null`, and a deliberate `systemctl start` fails — then confirm `unmask` cleanly reverses it.

---

### Step 1 of 2 — Mask and assert the `/dev/null` symlink

**In plain English:** We mask the unit and prove that `is-enabled` reports `masked` and that the unit file path resolves all the way to `/dev/null`.

```bash
sudo systemctl mask lab216-dummy.service
state=$(systemctl is-enabled lab216-dummy.service); rc=$?
echo "word: $state | is-enabled exit: $rc"
target=$(readlink -f /etc/systemd/system/lab216-dummy.service)
test "$target" = "/dev/null" && echo "MASK OK: -> /dev/null" || echo "MASK FAIL: -> $target"
```

**Expected output:**

```
Created symlink /etc/systemd/system/lab216-dummy.service → /dev/null.
word: masked | is-enabled exit: 1
MASK OK: -> /dev/null
```

**Line-by-line breakdown:**

- `sudo systemctl mask lab216-dummy.service` → Symlink the unit to `/dev/null` — the action under audit.
- `state=$(...); rc=$?` → Capture the word (`masked`) and its non-zero exit code together.
- `target=$(readlink -f /etc/systemd/system/lab216-dummy.service)` → Resolve the *unit file path itself*; for a masked unit this canonicalizes to `/dev/null`.
- `test "$target" = "/dev/null" && ... || ...` → Assert the target is exactly `/dev/null`, the definitive on-disk evidence of a mask.

**New words in this step:**

- **bit bucket** — `/dev/null`, the kernel sink a masked unit points at so systemd treats it as nonexistent.

---

### Step 2 of 2 — Prove start is blocked, then reverse with `unmask`

**In plain English:** We attempt to start the masked unit and capture the failure exit code as proof it cannot run, then `unmask` and confirm the state returns to a normal `disabled`.

```bash
sudo systemctl start lab216-dummy.service; rc=$?
test "$rc" -ne 0 && echo "START BLOCKED OK (exit $rc)" || echo "START NOT BLOCKED (FAIL)"
sudo systemctl unmask lab216-dummy.service
state=$(systemctl is-enabled lab216-dummy.service)
echo "after unmask: $state"
echo "exit was: $?"
```

**Expected output:**

```
Failed to start lab216-dummy.service: Unit lab216-dummy.service is masked.
START BLOCKED OK (exit 1)
Removed "/etc/systemd/system/lab216-dummy.service".
after unmask: disabled
exit was: 1
```

**Line-by-line breakdown:**

- `sudo systemctl start lab216-dummy.service; rc=$?` → Try to start the masked unit and capture the exit code; a masked unit refuses, so `rc` is non-zero.
- `test "$rc" -ne 0 && ... || ...` → Assert the start was *blocked* — here a non-zero exit is the success condition we want.
- `sudo systemctl unmask lab216-dummy.service` → Remove the `/dev/null` symlink, restoring the real unit so the change is reversible.
- `state=$(systemctl is-enabled ...)` → Confirm the unit is back to a normal `disabled` state (no longer masked) after unmasking.

**New words in this step:**

- **`unmask`** — removes the `/dev/null` symlink, restoring a masked unit so it can be enabled/started again.
- **negative assertion** — proving something fails as expected (`-ne 0`), the correct way to verify a block.

---

### Concept card (Task 2)

| Concept | What it does | Exam trap |
|---|---|---|
| `readlink -f` to `/dev/null` | hard proof of a mask | only the *unit file* path resolves there, not the wants-symlink |
| `start` exit `!= 0` | proves mask blocks starting | here non-zero is success — invert your usual check |
| `unmask` | restores the real unit | unmask leaves it `disabled`, not `enabled` |

---

### Troubleshoot (Task 2)

| Symptom | Likely cause | Fix |
|---|---|---|
| `START NOT BLOCKED (FAIL)` | The unit was only disabled, not masked | Run `systemctl mask` before the start test |
| `after unmask: masked` | A second mask symlink or stale state | Re-run `systemctl unmask` and `systemctl daemon-reload` |

---

## ✅ Lab Checklist

- [ ] Task 1 · Step 1 — Assert the "enabled" state with word and symlink
- [ ] Task 1 · Step 2 — Disable, then assert the symlink is gone
- [ ] Task 2 · Step 1 — Mask and assert the `/dev/null` symlink
- [ ] Task 2 · Step 2 — Prove start is blocked, then reverse with `unmask`

---

## 🧹 Teardown

**In plain English:** Delete everything this lab created so the box is clean for the next run.

> Run this after you've verified the lab. `lab_teardown.sh` safely removes the single sandbox root — it refuses to touch `/`, `$HOME`, or any protected path.

This lab changed **system state** (it installed, enabled, and masked a unit), and `rm` alone will NOT undo a mask or daemon registration. Run this explicit reversal block **first**, then the sandbox wipe:

```bash
sudo systemctl unmask lab216-dummy.service 2>/dev/null
sudo systemctl disable --now lab216-dummy.service 2>/dev/null
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
| Reading `is-enabled`'s non-zero exit as failure | Verify scripts abort on `disabled`/`masked` | Capture the word; treat non-zero as the state |
| Using `readlink` (no `-f`) on a chained link | You see an intermediate hop, not the real target | Always use `readlink -f` to reach the final target |
| Expecting `start` to succeed after mask | You misread the proof as a bug | A failed start on a masked unit is the expected evidence |

---

## 📌 Exam Strategy

Verification is what turns "I masked it" into "here is the proof it is masked." After any `enable`/`disable`/`mask`, read `is-enabled` for the word, follow the symlink with `readlink -f`, and — for a mask — prove `start` fails. Build the reflex of capturing exit codes deliberately, because `is-enabled` and a masked `start` both return non-zero *as information*, not as errors.

- Quote the rule: "non-zero from `is-enabled` is the state, not a failure."
- `readlink -f` to `/dev/null` is the single strongest piece of mask evidence.
- When verifying a block, invert your test — success is a *non-zero* exit from `start`.

---

## 🔗 Related Labs

- [Lab 216a — Service Isolation Bastion Host (RHCSA)](../lab-216a-service-isolation-bastion-host-rhcsa/) — the hand-typed disable/mask work this lab audits
- [Lab 216b — Service Isolation Bastion Host (Ansible)](../lab-216b-service-isolation-bastion-host-ansible/) — the playbook whose converged state you verify here
- [Lab 218c — Build a Bastion Server (Verify)](../lab-218c-build-bastion-server-verify/) — the same OK/FAIL assertion style applied to a full bastion posture

---

## 👤 Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
