# Lab 50b: Denying Access via ACLs (Ansible) — `ansible.posix.acl` zero-perm pattern

- **Series:** linux-ops-mastery — Permissions, Ownership, and ACL Control
- **Trilogy:** [`50a`](../lab-50a-setfacl-deny-rhcsa/) (RHCSA hand-typed) → `50b` (Ansible) → [`50c`](../lab-50c-setfacl-deny-verify/) (Verify)
- **Time Estimate:** 25–35 minutes
- **Tasks:** 2 (Task 1 = implement deny-by-zero via Ansible; Task 2 = trap T50-A explanation and contrast notes)
- **Practice Directory (rotation #50):** `/proc` (inspection only; writes stay in sandbox)
- **Sandbox (Tier B):** `/tmp/lab50b` with `USER=labuser_50_aclden`, `USER_B=labuser_50_aclden_b`, `GROUP=labgrp_50_aclden`
- **Traps rehearsed this lab:** **T50-A** (no true deny in POSIX ACL) · **T50-B** (explicit `---` differs from absent entry) · **T41** (destroy-restore drill deferred to 50c) · **T44** (identity cleanup proof required)

> **This lab's practice directory is: `/proc`**. `/proc` gives read-only context. All ACL state changes happen in `/tmp/lab50b`.

---

## LAB HEADER BLOCK

```bash
echo "🖥️  ENV:   ${ENV:-DECLARE_ME}"
echo "📦  OS:    $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒  TIME:  $(date -Is)"
echo "👤  USER:  $(whoami)@$(hostname)"
echo "⚠️  TRAP REMINDERS THIS LAB: T50-A T50-B T41 T44"
echo "📁  PRACTICE DIR: /proc"
echo ""
mount | grep " on /proc "
ansible --version | head -n 1
```

> **STOP — paste header output before setup.**

---

## Objective

Use Ansible to apply the same ACL denial pattern you hand-typed in 50a:

1. Build a mode `0644` file.
2. Apply named-user ACL deny using `ansible.posix.acl` with empty permissions (`permissions: ''`).
3. Verify denied access for `USER_B`.
4. Document why this is a simulation pattern (not a true deny keyword in Linux POSIX ACL).

---

## Concept: `permissions: ''` maps to explicit zero ACL entry

In `ansible.posix.acl`, setting:

- `etype: user`
- `entity: labuser_50_aclden_b`
- `permissions: ''`
- `state: present`

produces a named-user ACL entry equivalent to `u:labuser_50_aclden_b:---`.

This is not a true deny primitive; it is an explicit zero-permission grant line that wins over fallback for that named principal.

---

## Lab-Wide Setup — Tier B Sandbox Stack (Section 1.5)

```bash
sudo -i

export LAB_NUM=50
export LAB_SLUG=aclden
export SANDBOX=/tmp/lab50b
export GROUP=labgrp_${LAB_NUM}_${LAB_SLUG}
export USER=labuser_${LAB_NUM}_${LAB_SLUG}
export USER_B=labuser_${LAB_NUM}_${LAB_SLUG}_b
export USER_HOME=${SANDBOX}/home_${USER}
export USER_B_HOME=${SANDBOX}/home_${USER_B}

mkdir -p "${SANDBOX}" "${USER_HOME}" "${USER_B_HOME}"
mkdir -p /root/rhcsa_journal/lab-50b/task1
mkdir -p /root/rhcsa_journal/lab-50b/task2

getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
getent passwd "${USER_B}" >/dev/null || useradd -d "${USER_B_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER_B}"

chown -R "${USER}:${GROUP}" "${USER_HOME}"
chown -R "${USER_B}:${GROUP}" "${USER_B_HOME}"
chown root:root "${SANDBOX}"
chmod 0755 "${SANDBOX}"

ansible-galaxy collection install ansible.posix
```

> **STOP — confirm both users and group exist, and `ansible.posix` is installed, before Task 1.**

---

## Task 1 — Apply explicit zero ACL deny with Ansible

### Purpose

Automate the deny-by-explicit-zero pattern using `ansible.posix.acl`.

### Main command block

```bash
cat > /tmp/lab50b/inventory.ini <<'EOF'
[local]
localhost ansible_connection=local
EOF

cat > /tmp/lab50b/task1.yml <<'EOF'
- name: Lab 50b Task 1 ACL deny
  hosts: local
  become: true
  gather_facts: false
  vars:
    acl_file: /tmp/lab50b/public.txt
    owner_user: labuser_50_aclden
    deny_user: labuser_50_aclden_b
  tasks:
    - name: Create world-readable file as owner user
      ansible.builtin.copy:
        dest: "{{ acl_file }}"
        content: "lab50b ACL deny demo\n"
        owner: "{{ owner_user }}"
        group: labgrp_50_aclden
        mode: "0644"

    - name: Apply deny-by-zero ACL entry for deny user
      ansible.posix.acl:
        path: "{{ acl_file }}"
        etype: user
        entity: "{{ deny_user }}"
        permissions: ''
        state: present
EOF

ansible-playbook -i /tmp/lab50b/inventory.ini /tmp/lab50b/task1.yml | tee /tmp/lab50b/task1.txt
getfacl /tmp/lab50b/public.txt                                       | tee -a /tmp/lab50b/task1.txt
sudo -u "${USER_B}" cat /tmp/lab50b/public.txt 2>&1                  | tee -a /tmp/lab50b/task1.txt
```

### Expected signal

- `getfacl` contains `user:labuser_50_aclden_b:---`
- access as `USER_B` fails even though file mode is still `0644`

---

## Task 2 — Trap T50-A documentation and workaround contrast

### Purpose

Capture the exact model answer for exam/troubleshooting context: Linux ACL deny-by-zero is a workaround, not a native deny entry.

### Main command block

```bash
cat > /tmp/lab50b/task2-notes.txt <<'EOF'
T50-A NOTE:
Linux POSIX ACL does not implement true deny ACEs like NFSv4 ACL.
Workaround pattern:
  setfacl -m u:USER:---
or in Ansible:
  ansible.posix.acl permissions: '' state: present

T50-B NOTE:
Explicit zero entry (u:USER:---) is different from absent entry.
If entry is absent, permissions fall through to group::/other:: and base mode bits.
Group variant: g:GROUP:--- explicitly blocks that group ACL path; absent group ACL entry can fall through.
EOF

# Optional contrast: remove entry and observe fallback access restored
setfacl -x u:"${USER_B}" /tmp/lab50b/public.txt
sudo -u "${USER_B}" cat /tmp/lab50b/public.txt | tee /tmp/lab50b/task2.txt
cat /tmp/lab50b/task2-notes.txt               | tee -a /tmp/lab50b/task2.txt
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then userdel -r "${USER}" 2>/dev/null; fi
if getent passwd "${USER_B}" >/dev/null 2>&1; then userdel -r "${USER_B}" 2>/dev/null; fi
if getent group "${GROUP}" >/dev/null 2>&1; then groupdel "${GROUP}" 2>/dev/null; fi

rm -rf "${SANDBOX}"

echo "── Lab 50b cleanup audit ──"
getent passwd "${USER}"   >/dev/null && echo "❌ ${USER} remains"   || echo "✅ ${USER} gone"
getent passwd "${USER_B}" >/dev/null && echo "❌ ${USER_B} remains" || echo "✅ ${USER_B} gone"
getent group  "${GROUP}"  >/dev/null && echo "❌ ${GROUP} remains"  || echo "✅ ${GROUP} gone"
test -d "${SANDBOX}"                    && echo "❌ sandbox remains" || echo "✅ sandbox gone"

set -e
```

> **STOP — paste the four cleanup audit lines before marking Lab 50b complete.**

---

## Lab 50b Checklist (2 tasks + closeout)

- [ ] Setup created `${USER}`, `${USER_B}`, and `${GROUP}` under `/tmp/lab50b`
- [ ] Task 1 applied deny-by-zero using `ansible.posix.acl permissions: ''`
- [ ] Task 2 documented T50-A/T50-B and contrasted absent-entry fallback
- [ ] Closeout removed both users, group, and sandbox

---

## Related Labs

| Lab | Connection |
|---|---|
| **Lab 50a** — RHCSA ACL deny | Manual CLI form of same pattern |
| **Lab 50c** — Verify ACL deny | Audit + destroy-restore drill for ACL state |

---

## Author

**Kelvin R. Tobias**  
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
