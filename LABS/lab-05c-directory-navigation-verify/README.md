# Lab 05c: Verifying Directory Navigation (Capstone) — Audit + Destroy/Restore Drill

- **Series:** linux-ops-mastery — File Operations & Shell Fundamentals
- **Trilogy:** [`05a`](../lab-05a-directory-navigation-rhcsa/) → [`05b`](../lab-05b-directory-navigation-ansible/) → **`05c`** (Verify)
- **Tasks:** 2 (Task 1 = audit 05a evidence; Task 2 = destroy/restore navigation state drill)
- **Practice Directory (rotation #05):** `/usr`
- **Traps rehearsed:** **T41** (state reset assumptions) · **T42** (persistent evidence mismatch) · **T43** (stalling without explicit audit)

> **This lab's practice directory is: `/usr`**.

---

## LAB HEADER BLOCK

```bash
echo "verify-start=$(date -Is)"
ls -ld /usr
ls -la /root/rhcsa_journal/lab-05a/task1 /root/rhcsa_journal/lab-05a/task2 2>/dev/null
echo "⚠️ TRAPS: T41 T42 T43"
echo "exit was: $?"
```

> **STOP — paste header output before setup.**

---

## Objective

1. Validate that 05a task evidence is complete and internally consistent.
2. Rebuild navigation evidence after a controlled `/tmp` wipe.
3. Prove what survives reboot (`/root/rhcsa_journal`) vs what does not (`/tmp` state).

---

## Lab-Wide Setup

```bash
sudo -i

export LAB_NUM=05
export LAB_SLUG=dirnav_verify
export SANDBOX=/tmp/labsandbox_${LAB_NUM}_c
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-05c/task1 /root/rhcsa_journal/lab-05c/task2
getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
/usr is our reference navigation target.
This verify lab checks whether previous navigation evidence remains trustworthy and recoverable.
EOF

id "${USER}"
echo "exit was: $?"
```

---

## Task 1 — Audit Lab 05a evidence

**Practice directory this task:** `/usr`  
Audit the RHCSA creator-seat outputs before destructive testing.

### 🔁 Warm-Up

```bash
ls -la /root/rhcsa_journal/lab-05a/task1 /root/rhcsa_journal/lab-05a/task2
grep -n "^TOPIC:" /root/rhcsa_journal/lab-05a/task*/notes.txt 2>/dev/null
pwd
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Confirm 05a captured valid navigation evidence for both tasks.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside task |
|---|---|
| `ls -la ...` | checks files exist before deeper assertions |
| `grep -n "^TOPIC:" ...` | verifies notes metadata completeness |
| `pwd` | baseline for local verification sequence |

### Main Command Block

```bash
TASKLOG=/tmp/labsandbox_05_c/task1.txt

{
  echo "=== file existence audit ==="
  for f in \
    /root/rhcsa_journal/lab-05a/task1/evidence.txt \
    /root/rhcsa_journal/lab-05a/task1/task1-asuser-pwd.txt \
    /root/rhcsa_journal/lab-05a/task2/evidence.txt \
    /root/rhcsa_journal/lab-05a/task2/task2-asuser-cdminus.txt; do
      test -s "$f" && echo "✅ $f" || echo "❌ $f"
  done

  echo "=== content sanity ==="
  grep -c '/usr' /root/rhcsa_journal/lab-05a/task1/task1-asuser-pwd.txt
  grep -c '/usr' /root/rhcsa_journal/lab-05a/task2/task2-asuser-cdminus.txt
  grep -E 'OLDPWD|PWD' /root/rhcsa_journal/lab-05a/task2/evidence.txt | head -n 5

  echo "=== ownership checks ==="
  stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-05a/task1/task1-asuser-pwd.txt
  stat -c '%U:%G %a %n' /root/rhcsa_journal/lab-05a/task2/task2-asuser-cdminus.txt
} 2>&1 | tee "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- First block validates required artifacts exist.
- Second block checks semantic content (`/usr`, `PWD`, `OLDPWD`) instead of file presence only.
- Third block confirms ownership context from Tier B runs.

### Reading it left to right

`test -s "$f" && echo "✅" || echo "❌"`

- `test -s` checks file exists and non-empty
- `&&` prints success marker on true
- `||` prints failure marker on false

### The story

Audit before destroy is the only way to distinguish "restore bug" from "source evidence was already wrong."

### Expected output

```text
✅ /root/rhcsa_journal/lab-05a/task1/evidence.txt
✅ /root/rhcsa_journal/lab-05a/task2/evidence.txt
```

### Switches table

| Token | Meaning |
|---|---|
| `test -s` | file exists and non-empty |
| `grep -c` | count matching lines |
| `stat -c` | compact ownership/mode output |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | pre-destroy audit | establishes trusted baseline |
| ✅ | semantic verification | validates meaning, not just presence |
| ✅ | ownership audit | confirms user-context evidence |
| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T43 | skipping structured checks | run fixed checklist before mutation |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| task evidence exists | `find /root/rhcsa_journal/lab-05a -name '*.txt' | wc -l` | confirms journal baseline |
| navigation semantics present | `grep -c '/usr' ...` | confirms topic-specific content |
| audit transcript | `test -s "${TASKLOG}"` | keeps verifier-seat trail |

### Journal write

```bash
LAB=lab-05c
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp "${TASKLOG}" "${JDIR}/evidence.txt"
```

### 🧹 Cleanup

```bash
rm -f /tmp/labsandbox_05_c/task1.txt
echo "exit was: $?"
```

### Troubleshoot table

| Symptom | Fix |
|---|---|
| missing 05a files | complete/re-run 05a journal write blocks |
| grep count zero | inspect source files for expected tokens |
| ownership unexpected | review how files were created in 05a |

> **STOP — paste audit outputs before Task 2.**

---

## Task 2 — Destroy/restore navigation state drill

**Practice directory this task:** `/usr`  
Wipe volatile state, restore from journal, and prove continuity.

### 🔁 Warm-Up

```bash
wc -l /root/rhcsa_journal/lab-05a/task1/evidence.txt /root/rhcsa_journal/lab-05a/task2/evidence.txt
ls -ld /tmp/labsandbox_05 /tmp/labsandbox_05_c 2>/dev/null
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Destroy `/tmp` navigation artifacts, restore core evidence to a fresh sandbox, and append new verified navigation state.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside task |
|---|---|
| `wc -l ...` | baseline evidence size before restore |
| `ls -ld /tmp/...` | confirms target directories pre-destroy |

### Main Command Block

```bash
TASKLOG=/tmp/labsandbox_05_c/task2.txt
RESTORE_DIR=/tmp/labsandbox_05_c/restore

{
  echo "=== destroy volatile dirs ==="
  rm -rf /tmp/labsandbox_05 /tmp/labsandbox_05_c
  test ! -d /tmp/labsandbox_05 -a ! -d /tmp/labsandbox_05_c && echo "✅ destroy clean" || echo "❌ destroy incomplete"

  echo "=== rebuild verifier sandbox ==="
  mkdir -p "${SANDBOX}" "${USER_HOME}" "${RESTORE_DIR}"
  chown -R "${USER}:${GROUP}" "${SANDBOX}"

  echo "=== restore 05a evidence ==="
  cp /root/rhcsa_journal/lab-05a/task1/task1-asuser-pwd.txt "${RESTORE_DIR}/"
  cp /root/rhcsa_journal/lab-05a/task2/task2-asuser-cdminus.txt "${RESTORE_DIR}/"
  ls -la "${RESTORE_DIR}"

  echo "=== append new nav proof as verify user ==="
  sudo -u "${USER}" bash -c 'cd /usr; pwd > "'"${USER_HOME}"'/task2-restore-proof.txt"; cd /etc; cd - >> "'"${USER_HOME}"'/task2-restore-proof.txt"; echo "OLDPWD=$OLDPWD" >> "'"${USER_HOME}"'/task2-restore-proof.txt"'
  stat -c '%U:%G %a %n' "${USER_HOME}/task2-restore-proof.txt"
  cat "${USER_HOME}/task2-restore-proof.txt"
} 2>&1 | tee "${TASKLOG}"

echo "exit was: $?"
```

### Human-Readable Breakdown

- Removes old `/tmp` lab state to simulate reboot/ephemeral loss.
- Restores only durable journal artifacts.
- Creates fresh as-user navigation proof to demonstrate continued operability.

### Reading it left to right

`sudo -u "${USER}" bash -c 'cd /usr; pwd > file; cd /etc; cd - >> file'`

- user-context shell executes all navigation
- first write creates proof file
- second write appends toggle result

### The story

Real persistence is not "my shell still remembers"; it is "I can reconstruct state from durable evidence and keep working."

### Expected output

```text
✅ destroy clean
labuser_05_dirnav_verify:labgrp_05_dirnav_verify 644 /tmp/labsandbox_05_c/home_labuser_05_dirnav_verify/task2-restore-proof.txt
/usr
/usr
OLDPWD=/etc
```

### Switches table

| Token | Meaning |
|---|---|
| `rm -rf` | recursive force remove |
| `test ! -d` | assert directory absent |
| `cp` | restore durable file copies |
| `>>` | append output to existing file |

### 🧠 Concept Card

| ✅ | Concept | What it does |
|---|---|---|
| ✅ | destroy/restore drill | rehearses volatile-state loss recovery |
| ✅ | durable journal source | `/root/rhcsa_journal` becomes recovery anchor |
| ✅ | post-restore continuation | proves resumed navigation workflow |
| 🪤 Trap Risk | What goes wrong | How to avoid |
|---|---|---|
| T41 | assuming `/tmp` survives reboot | always copy critical evidence to `/root/rhcsa_journal` |
| T42 | restoring files but not validating behavior | run fresh command sequence after restore |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| restored artifacts | `test -s "${RESTORE_DIR}/task1-asuser-pwd.txt"` | proves journal recovery worked |
| new post-restore proof | `test -s "${USER_HOME}/task2-restore-proof.txt"` | proves workflow resumed |
| ownership correctness | `stat -c '%U:%G' "${USER_HOME}/task2-restore-proof.txt"` | confirms user-context persistence |

### Journal write

```bash
LAB=lab-05c
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "${JDIR}"
cp "${TASKLOG}" "${JDIR}/evidence.txt"
cp "${USER_HOME}/task2-restore-proof.txt" "${JDIR}/task2-restore-proof.txt"
```

### 🧹 Cleanup

```bash
rm -f /tmp/labsandbox_05_c/task2.txt
echo "exit was: $?"
```

### Troubleshoot table

| Symptom | Fix |
|---|---|
| destroy incomplete | find open handles/processes and retry |
| restore copy fails | verify 05a journal paths exist |
| proof file empty | inspect quoted `bash -c` command sequence |

> **STOP — paste outputs before Lab Closeout.**

---

## Lab Closeout

```bash
set +e
if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"
set -e
```

## Lab 05c Checklist

- [ ] Task 1 audited 05a evidence
- [ ] Task 2 completed destroy/restore drill
- [ ] Post-restore user proof captured
- [ ] Closeout audit shows four `✅`
