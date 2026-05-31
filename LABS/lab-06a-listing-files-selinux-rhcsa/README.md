# Lab 06a: Listing Files and SELinux Contexts (RHCSA) — `ls -lZ`, `matchpathcon`, `restorecon`

- **Series:** linux-ops-mastery — Essential Tools & File Operations
- **Trilogy:** `06a` (RHCSA hand-typed) → [`06b`](../lab-06b-listing-files-selinux-ansible/) (Ansible — `community.general.sefcontext`) → [`06c`](../lab-06c-listing-files-selinux-verify/) (Verify capstone)
- **Career arcs covered:** RHCSA EX200 (every "verify the SELinux context" question), RHCE EX294 (`community.general.sefcontext` is the permanent fcontext module)
- **Prerequisite:** [`Lab 05c`](../lab-05c-directory-nav-verify/) completed
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2 (Task 1 = `ls -l`, `ls -lZ`, `ls -dZ`, `stat -Z`, `matchpathcon` · Task 2 = wrong context proof + `semanage fcontext -a` + `restorecon -Rv` — **T01**, **T02**, **T03**)
- **Practice Directory (rotation #06):** `/etc`
- **Sandbox (Tier B):** `/tmp/lab06a` with `USER=labuser_06_ls`, `GROUP=labgrp_06_ls`
- **Traps rehearsed this lab:** **T01** (setting permissive instead of fixing the real context) · **T02** (`semanage fcontext` without `restorecon -Rv` afterwards — config recorded but not applied) · **T03** (`setsebool` without `-P` — not persistent across reboot — noted but not the focus)

> **This lab's practice directory is: `/etc`** — every system-wide config file lives here with a specific SELinux context. RHCSA exams constantly test fcontext on `/etc/<service>/...`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "🔐  SE:    $(getenforce 2>/dev/null || echo n/a)"
test "$(getenforce)" = "Disabled" && echo "⚠️  ENV WARN: SELinux Disabled — Lab 06 needs Enforcing or Permissive"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T01 T02 T03"
echo "📁  PRACTICE DIR: /etc"
echo ""
echo "💡 /etc context (our SELinux source):"
ls -ldZ /etc /etc/ssh /etc/httpd 2>/dev/null
```

> **STOP — paste header. If `getenforce` says `Disabled`, switch to baremetal/Rocky AMI; this lab won't demonstrate fcontext on Disabled.**

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export LAB_NUM=06
export LAB_SLUG=ls
export SANDBOX=/tmp/lab06a
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}"
mkdir -p /root/rhcsa_journal/lab-06a/task1 /root/rhcsa_journal/lab-06a/task2

# Install policycoreutils-python-utils if missing — semanage lives there
rpm -q policycoreutils-python-utils >/dev/null 2>&1 || \
    dnf install -y policycoreutils-python-utils >/dev/null 2>&1

cat > "${SANDBOX}/THIS_DIRECTORY.txt" <<'EOF'
Practice directory: /etc
/etc holds every system-wide config file. Each subdirectory has a
specific SELinux file context. /etc/ssh has sshd_t types, /etc/httpd
has httpd_config_t, /etc/postfix has postfix_etc_t. RHCSA expects
you to verify, fix, and persist these contexts.
EOF

getent group  "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}"  >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"

id "${USER}"
ls -ld "${SANDBOX}" "${USER_HOME}" /etc
echo "Sandbox built by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — paste setup output before Task 1.**

---

## Task 1 — `ls -l`, `ls -lZ`, `ls -dZ`, `stat -Z`, `matchpathcon`

### 🔁 Warm-Up

```bash
ls -ld /etc                                              2>&1 | tee /tmp/lab06a/warmup.txt
ls -ldZ /etc
stat -c '%U:%G %a %n' /etc
which semanage matchpathcon restorecon
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

Build the listing-with-context reflex: `ls -l` for owner/group/mode, `ls -lZ` adds SELinux label, `ls -dZ` for the dir itself; `matchpathcon` predicts what the *correct* context should be.

### 🧵 WEAVE TRACE

| Warm-up command | Role inside Task 1 |
|---|---|
| `ls -ld /etc` | Baseline mode + ownership |
| `ls -ldZ /etc` | Same plus SELinux context — main subject |
| `stat -c '%U:%G %a %n' /etc` | Numeric mode + owner — reused for compare-on-disk |
| `which semanage matchpathcon` | Confirms tools available before Part D |

### Main command block

```bash
TASKLOG=/tmp/lab06a/task1.txt

echo "═══ Part A: ls -l vs ls -lZ ═══"                    2>&1 | tee $TASKLOG
ls -ld /etc/passwd /etc/shadow /etc/ssh                  | tee -a $TASKLOG
echo "----- with -Z -----"                              | tee -a $TASKLOG
ls -ldZ /etc/passwd /etc/shadow /etc/ssh                 | tee -a $TASKLOG

echo "═══ Part B: stat -Z on /etc files ═══"              | tee -a $TASKLOG
stat -c '%C %n' /etc/passwd /etc/ssh/sshd_config         | tee -a $TASKLOG

echo "═══ Part C: ls -dZ on a directory ═══"              | tee -a $TASKLOG
ls -dZ /etc /etc/ssh /etc/postfix 2>/dev/null            | tee -a $TASKLOG

echo "═══ Part D: matchpathcon — predicted context ═══"   | tee -a $TASKLOG
matchpathcon /etc/passwd                                 | tee -a $TASKLOG
matchpathcon /etc/ssh/sshd_config                        | tee -a $TASKLOG
matchpathcon "${SANDBOX}/test.txt"                       | tee -a $TASKLOG

echo "═══ Part E: AS ${USER} (Tier B) ═══"                | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    ls -lZ /etc/passwd /etc/shadow 2>&1
    matchpathcon /etc/passwd
    stat -c "%C %n" /etc/passwd
' > "${USER_HOME}/listing.txt"
cat "${USER_HOME}/listing.txt"                            | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/listing.txt"          | tee -a $TASKLOG

echo "exit was: $?"
```

### Expected output

```text
═══ Part A: ls -l vs ls -lZ ═══
-rw-r--r--. 1 root root ... /etc/passwd
-rw-r-----. 1 root root ... /etc/shadow
drwxr-xr-x. 5 root root ... /etc/ssh
----- with -Z -----
-rw-r--r--. 1 root root system_u:object_r:passwd_file_t:s0       /etc/passwd
-rw-r-----. 1 root root system_u:object_r:shadow_t:s0            /etc/shadow
drwxr-xr-x. 5 root root system_u:object_r:etc_t:s0               /etc/ssh
═══ Part B: stat -Z on /etc files ═══
system_u:object_r:passwd_file_t:s0 /etc/passwd
system_u:object_r:etc_t:s0 /etc/ssh/sshd_config
═══ Part D: matchpathcon — predicted context ═══
/etc/passwd	system_u:object_r:passwd_file_t:s0
/etc/ssh/sshd_config	system_u:object_r:etc_t:s0
/tmp/lab06a/test.txt	system_u:object_r:user_tmp_t:s0
═══ Part E: AS labuser_06_ls (Tier B) ═══
-rw-r--r--. 1 root root system_u:object_r:passwd_file_t:s0 /etc/passwd
...
labuser_06_ls:labgrp_06_ls 644 /tmp/lab06a/home_labuser_06_ls/listing.txt
```

### Switches

| Token | Meaning |
|---|---|
| `ls -l` | long listing (mode, links, owner, group, size, date, name) |
| `ls -Z` | add SELinux context column |
| `ls -d PATH` | list the dir itself (not its contents) |
| `stat -c '%C %n'` | print SELinux context + file name |
| `matchpathcon PATH` | predict correct context per `file_contexts` rules |

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `ls -lZ` | Show full ACL-less context — first reflex on every "what's wrong with X?" question |
| `matchpathcon` | The expected context — diff against `ls -Z` to find drift |
| `policycoreutils-python-utils` | RPM that ships `semanage`; install before exam day |
| **🪤 Trap Risk T01** | Switching SELinux to permissive instead of fixing the real context. **Fix:** keep `getenforce` = `Enforcing`; fix the label. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Listing tools work | `ls -lZ /etc/passwd` returns context | Foundation reflex |
| matchpathcon works | `matchpathcon /etc/passwd` returns predicted | semanage installed |
| Tier B file owned | `stat -c '%U' "${USER_HOME}/listing.txt"` returns `${USER}` | sudo -u ran |

### Journal write

```bash
LAB=lab-06a
TASK=task1
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06a/task1.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/listing.txt" "$JDIR/listing-asuser.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    ls -l/-lZ/-dZ; stat -Z; matchpathcon predicted contexts
COMMANDS: ls -lZ, ls -dZ, stat -c '%C %n', matchpathcon
TRAPS:    T01 noted; T02 deferred to Task 2
TIER B:   listing-asuser.txt owned by ${USER}
NEXT:     task2 — chcon vs semanage fcontext + restorecon (T02 proof)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup

```bash
rm -f /tmp/lab06a/warmup.txt /tmp/lab06a/task1.txt
ls /tmp/lab06a
echo "exit was: $?"
```

> **STOP — paste Part D `matchpathcon` lines and Part E `Tier B ownership` line before Task 2.**

---

## Task 2 — `chcon` (temporary) vs `semanage fcontext -a` + `restorecon -Rv` (permanent — T02)

### 🔁 Warm-Up

```bash
ls -lZ "${SANDBOX}" 2>/dev/null                          2>&1 | tee /tmp/lab06a/warmup2.txt
matchpathcon "${SANDBOX}/web/index.html"
semanage fcontext -l | grep '/var/www' | head -n 3
echo "Warm-up done by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

### Purpose

1. Create a fake web doc-root in the sandbox; observe its default context (`user_tmp_t`).
2. Use `chcon` to TEMPORARILY label it `httpd_sys_content_t` — works until `restorecon`.
3. Add a permanent `semanage fcontext` rule mapping the path to `httpd_sys_content_t`.
4. Run `restorecon -Rv` — same label, but now it's persistent across reboots and `restorecon` runs.

### Main command block

```bash
TASKLOG=/tmp/lab06a/task2.txt
WEBROOT="${SANDBOX}/web"

echo "═══ Part A: create fake webroot ═══"               2>&1 | tee $TASKLOG
mkdir -p "${WEBROOT}"
echo "<h1>Lab 06a</h1>" > "${WEBROOT}/index.html"
ls -ldZ "${WEBROOT}"                                    | tee -a $TASKLOG
ls -lZ  "${WEBROOT}/index.html"                          | tee -a $TASKLOG

echo "═══ Part B: chcon (temporary label) ═══"           | tee -a $TASKLOG
chcon -R -t httpd_sys_content_t "${WEBROOT}"
ls -ldZ "${WEBROOT}"                                    | tee -a $TASKLOG
ls -lZ  "${WEBROOT}/index.html"                          | tee -a $TASKLOG

echo "═══ Part C: T02 demo — restorecon wipes chcon ═══" | tee -a $TASKLOG
restorecon -Rv "${WEBROOT}"                              | tee -a $TASKLOG
ls -lZ "${WEBROOT}/index.html"                           | tee -a $TASKLOG
echo "Note: label reverted to user_tmp_t — chcon was not persistent" | tee -a $TASKLOG

echo "═══ Part D: semanage fcontext + restorecon (permanent) ═══" | tee -a $TASKLOG
semanage fcontext -a -t httpd_sys_content_t "${WEBROOT}(/.*)?"   2>&1 | tee -a $TASKLOG
semanage fcontext -l | grep "${WEBROOT}"                | tee -a $TASKLOG
restorecon -Rv "${WEBROOT}"                              | tee -a $TASKLOG
ls -lZ "${WEBROOT}/index.html"                           | tee -a $TASKLOG

echo "═══ Part E: verify persistence (run restorecon again) ═══" | tee -a $TASKLOG
restorecon -Rv "${WEBROOT}"                              | tee -a $TASKLOG
ls -lZ "${WEBROOT}/index.html"                           | tee -a $TASKLOG

CTX=$(stat -c '%C' "${WEBROOT}/index.html")
echo "${CTX}" | grep -q 'httpd_sys_content_t' \
    && echo "✅ T02 fix worked — context persistent (httpd_sys_content_t)" \
    || echo "❌ context not persistent" \
    | tee -a $TASKLOG

echo "═══ Part F: AS ${USER} — read but not relabel ═══"  | tee -a $TASKLOG
sudo -u "${USER}" -H bash -c '
    ls -lZ '"${WEBROOT}"'/index.html
    cat '"${WEBROOT}"'/index.html
' > "${USER_HOME}/webread.txt" 2>&1
cat "${USER_HOME}/webread.txt"                           | tee -a $TASKLOG
stat -c '%U:%G %a %n' "${USER_HOME}/webread.txt"          | tee -a $TASKLOG

echo "exit was: $?"
```

### Expected output

```text
═══ Part A: create fake webroot ═══
drwxr-xr-x. ... unconfined_u:object_r:user_tmp_t:s0 /tmp/lab06a/web
-rw-r--r--. ... unconfined_u:object_r:user_tmp_t:s0 /tmp/lab06a/web/index.html
═══ Part B: chcon (temporary label) ═══
drwxr-xr-x. ... unconfined_u:object_r:httpd_sys_content_t:s0 /tmp/lab06a/web
═══ Part C: T02 demo — restorecon wipes chcon ═══
Relabeled /tmp/lab06a/web ... user_tmp_t:s0
-rw-r--r--. ... unconfined_u:object_r:user_tmp_t:s0 ... index.html
Note: label reverted to user_tmp_t — chcon was not persistent
═══ Part D: semanage fcontext + restorecon (permanent) ═══
/tmp/lab06a/web(/.*)?    all files          system_u:object_r:httpd_sys_content_t:s0
Relabeled /tmp/lab06a/web ... httpd_sys_content_t:s0
-rw-r--r--. ... httpd_sys_content_t ... index.html
═══ Part E: verify persistence (run restorecon again) ═══
-rw-r--r--. ... httpd_sys_content_t ... index.html
✅ T02 fix worked — context persistent (httpd_sys_content_t)
```

### 🧠 Concept Card

| Concept | What it does |
|---|---|
| `chcon` | TEMPORARY relabel — wiped by `restorecon` |
| `semanage fcontext -a -t TYPE 'PATTERN'` | Add a permanent rule — survives reboot |
| `restorecon -Rv PATH` | Apply the recorded fcontext rules to the actual files |
| **🪤 Trap Risk T02** | Running `semanage fcontext -a` and stopping there. **Fix:** ALWAYS follow with `restorecon -Rv`. |

### 🔁 PERSISTENCE CHECK

| What was configured | Verification command | Why it matters |
|---|---|---|
| Permanent fcontext rule | `semanage fcontext -l \| grep "${WEBROOT}"` | Survives reboot |
| Label applied | `ls -lZ "${WEBROOT}/index.html"` shows `httpd_sys_content_t` | restorecon ran |
| restorecon idempotent | second `restorecon -Rv` makes no changes | Truly persistent |

### Journal write

```bash
LAB=lab-06a
TASK=task2
JDIR="/root/rhcsa_journal/${LAB}/${TASK}"
mkdir -p "$JDIR"
cp /tmp/lab06a/task2.txt "$JDIR/evidence.txt"
cp "${USER_HOME}/webread.txt" "$JDIR/webread-asuser.txt"
semanage fcontext -l | grep "${WEBROOT}" > "$JDIR/fcontext-rule.txt"

cat > "$JDIR/done.txt" <<EOF
LAB:    ${LAB}
TASK:   ${TASK}
DATE:   $(date -Is)
USER:   $(whoami)@$(hostname)
LAB_USER: ${USER}
LAB_GROUP: ${GROUP}
STATUS: COMPLETE
EOF

cat > "$JDIR/notes.txt" <<EOF
TOPIC:    chcon vs semanage fcontext + restorecon; T02 demonstrated
COMMANDS: chcon -R -t, semanage fcontext -a -t TYPE 'PATTERN', restorecon -Rv
TRAPS:    T02 rehearsed (chcon wiped by restorecon; semanage rule survives)
TIER B:   webread-asuser.txt owned by ${USER}
NEXT:     lab-06b — community.general.sefcontext (RHCE permanent fcontext)
EOF

ls -la "$JDIR"
echo "exit was: $?"
```

### 🧹 Cleanup (per-task — undo semanage rule so 06b/06c start clean)

```bash
semanage fcontext -d "${WEBROOT}(/.*)?" 2>/dev/null
rm -f /tmp/lab06a/warmup2.txt /tmp/lab06a/task2.txt
rm -f "${USER_HOME}/webread.txt" "${USER_HOME}/listing.txt"
# Keep ${WEBROOT} for 06b/06c
ls /tmp/lab06a
echo "exit was: $?"
```

> **STOP — paste Part D `httpd_sys_content_t` line and Part E `✅ T02 fix worked` line before Lab Closeout.**

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

# Remove any lingering semanage rule from this lab
semanage fcontext -d "${SANDBOX}/web(/.*)?" 2>/dev/null

awk -v s="${SANDBOX}" '$2 ~ s {print $2}' /proc/mounts | tac | xargs -r -n1 umount -l 2>/dev/null

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi
rm -rf "${SANDBOX}"

echo "── Lab 06a cleanup audit ──"
getent passwd "${USER}"  >/dev/null && echo "❌ user remains"    || echo "✅ user gone"
getent group  "${GROUP}" >/dev/null && echo "❌ group remains"   || echo "✅ group gone"
test -d "${SANDBOX}"                && echo "❌ sandbox remains" || echo "✅ sandbox gone"
semanage fcontext -l | grep -q "${SANDBOX}" && echo "❌ fcontext rule remains" || echo "✅ fcontext rule gone"

set -e
echo "Cleanup complete by $(whoami) at $(date -Is)"
echo "exit was: $?"
```

> **STOP — four `✅` audit lines before Lab 06b.**

---

## Lab 06a Checklist

- [ ] Lab-Wide Setup — `policycoreutils-python-utils` installed; Tier B sandbox built
- [ ] Task 1 — `ls -lZ`/`stat -Z`/`matchpathcon` all return contexts; Tier B file owned
- [ ] Task 2 — chcon temporary; restorecon wipes chcon; semanage rule survives second restorecon (T02)
- [ ] Lab Closeout — four `✅` (including fcontext rule cleaned)

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 06b** — Ansible | `community.general.sefcontext` is the declarative version of `semanage fcontext -a` |
| **Lab 06c** — Verify | Audit the rule + the restorecon idempotence |
| Lab 02a / 02c — stderr | restorecon's `-Rv` produces stderr noise that is captured with `2>&1` |

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
