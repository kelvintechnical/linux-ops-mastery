# Lab 19b: Concatenating Files with Ansible (Module-First)

- **Series:** linux-ops-mastery — Text Streams and File Composition
- **Trilogy:** `19a` (RHCSA) → `19b` (Ansible) → `19c` (Verify)
- **Time Estimate:** 30–40 minutes
- **Tasks:** 2
- **Practice Directory (rotation #19):** `/usr`
- **Sandbox (Tier B):** `/tmp/lab19b` with `USER=labuser_19_catjoin`, `GROUP=labgrp_19_catjoin`
- **Playbooks live at:** `/root/rhcsa_journal/lab-19b/playbooks/`
- **Traps rehearsed this lab:** **T19-A** · **T19-B** · **T41** · **T44**

> **This lab's practice directory is: `/usr`** (inspection context only). Writable artifacts are in `/tmp/lab19b`.

---

## LAB HEADER BLOCK

```bash
echo "📦 OS: $(cat /etc/redhat-release 2>/dev/null || grep PRETTY_NAME /etc/os-release)"
echo "🕒 TIME: $(date -Is)"
echo "👤 USER: $(whoami)@$(hostname)"
echo "📁 PRACTICE DIR: /usr"
echo "⚠️ TRAPS: T19-A T19-B T41 T44"
ansible --version | head -n 2
ansible -m ping localhost | tail -n 4
ls -ld /usr
```

---

## Objective

Convert the `cat` join workflow to idempotent Ansible:

1. Merge fragments using `ansible.builtin.assemble` (or controlled `shell: cat` pattern) and copy to final target.
2. Avoid line-management misuse by selecting `lineinfile` vs `blockinfile` correctly.

---

## Lab-Wide Setup — Tier B Sandbox

```bash
sudo -i

export SANDBOX=/tmp/lab19b
export GROUP=labgrp_19_catjoin
export USER=labuser_19_catjoin
export USER_HOME=${SANDBOX}/home_${USER}

mkdir -p "${SANDBOX}" "${USER_HOME}" /root/rhcsa_journal/lab-19b/playbooks
getent group "${GROUP}" >/dev/null || groupadd "${GROUP}"
getent passwd "${USER}" >/dev/null || useradd -d "${USER_HOME}" -M -s /bin/bash -g "${GROUP}" "${USER}"
chown -R "${USER}:${GROUP}" "${SANDBOX}"
```

---

## Task 1 — Idempotent fragment merge (`assemble` preferred)

### Purpose

Use `ansible.builtin.assemble` to merge ordered fragments into one file, then enforce final destination content with `ansible.builtin.copy` so repeated runs are clean and predictable.

### Build fixture fragments

```bash
mkdir -p /tmp/lab19b/fragments
cat > /tmp/lab19b/fragments/01-header <<'EOF'
=== Lab 19 Merge ===
EOF
cat > /tmp/lab19b/fragments/02-os <<'EOF'
OS:
EOF
cat /etc/redhat-release >> /tmp/lab19b/fragments/02-os
cat > /tmp/lab19b/fragments/03-host <<'EOF'
HOST:
EOF
cat /etc/hostname >> /tmp/lab19b/fragments/03-host
```

### Playbook (`/root/rhcsa_journal/lab-19b/playbooks/task1.yml`)

```yaml
---
- name: "Lab 19b Task 1 - assemble fragment files"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    merged_tmp: /tmp/lab19b/assembled.tmp
    merged_final: /tmp/lab19b/assembled-report.txt

  tasks:
    - name: "Merge ordered fragments"
      ansible.builtin.assemble:
        src: /tmp/lab19b/fragments
        dest: "{{ merged_tmp }}"
        delimiter: "\n"
      register: assemble_out

    - name: "Publish merged report idempotently"
      ansible.builtin.copy:
        src: "{{ merged_tmp }}"
        dest: "{{ merged_final }}"
        owner: root
        group: root
        mode: "0644"
        remote_src: true
      register: copy_out

    - name: "Show change summary"
      ansible.builtin.debug:
        msg:
          - "assemble changed={{ assemble_out.changed }}"
          - "copy changed={{ copy_out.changed }}"
```

### Run and verify

```bash
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task1.yml 2>&1 | tee /tmp/lab19b/task1-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task1.yml 2>&1 | tee /tmp/lab19b/task1-apply-2.txt
cat -n /tmp/lab19b/assembled-report.txt
```

> If you choose `shell: cat /tmp/lab19b/fragments/* > ...`, pair it with `copy` or checksum gating; otherwise idempotence reporting is often noisy.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-19b/task1
cp /tmp/lab19b/task1-apply-1.txt /root/rhcsa_journal/lab-19b/task1/apply-1.txt
cp /tmp/lab19b/task1-apply-2.txt /root/rhcsa_journal/lab-19b/task1/apply-2.txt
cp /tmp/lab19b/assembled-report.txt /root/rhcsa_journal/lab-19b/task1/assembled-report.txt
```

---

## Task 2 — `lineinfile` vs `blockinfile` trap

### Purpose

Practice the decision rule:

- Use `lineinfile` for single-line key/value enforcement.
- Use `blockinfile` for multi-line managed blocks.

### Playbook (`/root/rhcsa_journal/lab-19b/playbooks/task2.yml`)

```yaml
---
- name: "Lab 19b Task 2 - line vs block management"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    target: /tmp/lab19b/policy.conf

  tasks:
    - name: "Ensure single setting via lineinfile"
      ansible.builtin.lineinfile:
        path: "{{ target }}"
        create: true
        regexp: '^merge_mode='
        line: 'merge_mode=cat'

    - name: "Ensure multi-line stanza via blockinfile"
      ansible.builtin.blockinfile:
        path: "{{ target }}"
        marker: "# {mark} ANSIBLE MANAGED CAT BLOCK"
        block: |
          [cat_join]
          show_hidden=true
          squeeze_blank=true
```

### Run and inspect

```bash
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task2.yml 2>&1 | tee /tmp/lab19b/task2-apply-1.txt
ansible-playbook /root/rhcsa_journal/lab-19b/playbooks/task2.yml 2>&1 | tee /tmp/lab19b/task2-apply-2.txt
cat -A /tmp/lab19b/policy.conf
```

### Trap callout

- Misusing `lineinfile` to manage multi-line blocks causes brittle, duplicated config.
- Misusing `blockinfile` for one-line key replacement can leave multiple conflicting keys.
- `cat -A` is your T19-B sanity check when strange whitespace appears.

### Journal write

```bash
mkdir -p /root/rhcsa_journal/lab-19b/task2
cp /tmp/lab19b/task2-apply-1.txt /root/rhcsa_journal/lab-19b/task2/apply-1.txt
cp /tmp/lab19b/task2-apply-2.txt /root/rhcsa_journal/lab-19b/task2/apply-2.txt
cp /tmp/lab19b/policy.conf /root/rhcsa_journal/lab-19b/task2/policy.conf
```

---

## Lab Closeout — Bulletproof Teardown (Section 6)

```bash
set +e

if getent passwd "${USER}" >/dev/null 2>&1; then
  userdel -r "${USER}" 2>/dev/null
fi
if getent group "${GROUP}" >/dev/null 2>&1; then
  groupdel "${GROUP}" 2>/dev/null
fi

rm -rf "${SANDBOX}"

echo "── Lab 19b cleanup audit ──"
getent passwd "${USER}" >/dev/null && echo "❌ user remains" || echo "✅ user gone"
getent group "${GROUP}" >/dev/null && echo "❌ group remains" || echo "✅ group gone"
test -d "${SANDBOX}" && echo "❌ sandbox remains" || echo "✅ sandbox gone"
test -d "${USER_HOME}" && echo "❌ home remains" || echo "✅ home gone"

set -e
```

---

## Lab 19b Checklist

- [ ] Task 1 completed (idempotent fragment merge via `assemble` or controlled `shell cat` + `copy`)
- [ ] Task 2 completed (`lineinfile` for single-line + `blockinfile` for stanza)
- [ ] Section 6 closeout audit shows four `✅` lines

---

## Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
