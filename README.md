<div align="center">

# 🐧 Linux Ops Mastery

### A Hands-On Linux Operations Study Guide
**RHCSA → RHCE → CKA → Production AI/MLOps Infrastructure**

![RHCSA](https://img.shields.io/badge/RHCSA-EX200-EE0000?style=flat&logo=redhat&logoColor=white)
![RHCE](https://img.shields.io/badge/RHCE-EX294-EE0000?style=flat&logo=redhat&logoColor=white)
![CKA](https://img.shields.io/badge/CKA-Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![CompTIA Linux+](https://img.shields.io/badge/Linux%2B-FF0000?style=flat&logo=comptia&logoColor=white)
![CompTIA Security+](https://img.shields.io/badge/Security%2B-FF0000?style=flat&logo=comptia&logoColor=white)
![AWS CCP](https://img.shields.io/badge/AWS_Cloud_Practitioner-232F3E?style=flat&logo=amazonaws&logoColor=white)

[![Stars](https://img.shields.io/github/stars/kelvintechnical/linux-ops-mastery?style=social)](https://github.com/kelvintechnical/linux-ops-mastery)

</div>

---

## 📚 Table of Contents

- [About](#-about)
- [Who This Is For](#-who-this-is-for)
- [Companion Repos](#-companion-repos)
- [Certification Path](#-certification-path)
- [RHCSA Labs](#-rhcsa-ex200-labs)
- [RHCE Labs](#-rhce-ex294-labs)
- [CKA Labs](#-cka-labs)
- [How to Use This Repo](#-how-to-use-this-repo)
- [Author & Connect](#-author--connect)

---

## 📖 About

A complete, hands-on Linux operations study guide built for engineers preparing for **RHCSA (EX200)**, **RHCE (EX294)**, and **CKA** — and anyone building production-grade Linux and Kubernetes skills for cloud, DevOps, or AI/MLOps infrastructure roles.

All commands tested on **RHEL 9** / **Rocky Linux** / **AWS RHEL AMI**.

---

## 🎯 Who This Is For

- Engineers preparing for **RHCSA**, **RHCE**, or **CKA**
- DevOps / SRE / Platform engineers building Linux and Kubernetes skills
- AI/MLOps practitioners deploying on Linux infrastructure
- Self-learners working through Red Hat and CNCF certification objectives

> No prior Red Hat experience required. CompTIA Linux+ or equivalent familiarity recommended.

---

## 🔗 Companion Repos

Foundational Linux skills broken into focused, standalone learning resources:

| Repo | Topic |
|------|-------|
| 🌐 [accessing-your-linux-system](https://github.com/kelvintechnical/accessing-your-linux-system) | Console access, SSH, PuTTY, AWS EC2 |
| 🗂 [managing-linux-files-cli](https://github.com/kelvintechnical/managing-linux-files-cli) | File system, file management, links, I/O redirection, pipes |

> 💡 **Start here if you're new to Linux** — these repos build the foundation before diving into RHCSA-level material.

---

## 🗺️ Certification Path

| Phase | Certification | Exam | Status |
|-------|--------------|------|--------|
| Foundation | CompTIA Linux+ | XK0-005 | ✅ Complete |
| Intermediate | RHCSA | EX200 | 🔄 In Progress |
| Advanced | RHCE (Ansible) | EX294 | 🔜 Planned |
| Cloud Native | CKA (Kubernetes) | CKA | 🔜 Planned |

---

## 🧪 RHCSA EX200 Labs

Labs organized by official RHCSA EX200 exam objectives.

---

### 🖥️ Shells, Terminals & Redirection

> Understand stdout, stderr, pipes, and how to control where command output goes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | [Standard Output Redirection](https://github.com/kelvintechnical/stdout-redirection) | `>`, `>>`, `cat` |
| 02 | [Standard Error Redirection](https://github.com/kelvintechnical/stderr-redirection) | `2>`, `2>/dev/null`, `&>` |
| 03 | [Pipe Text Streams](https://github.com/kelvintechnical/pipe-text-streams) | `\|`, `less`, `grep`, `tee`, `wc -l` |

---

### 🌐 Networking

> Configure and manage network interfaces, static IPs, hostnames, and DNS.

| # | Lab | Key Commands |
|---|-----|-------------|
| 04 | [Configure a Static IP Address](./01-system-management/README.md#lab-01--configure-a-static-ip-address) | `nmcli con mod`, `ip addr`, `ip route` |
| 05 | Configure SSH & Key-Based Authentication *(coming soon)* | `ssh-keygen`, `authorized_keys`, `sshd_config` |

---

### 📦 Package Management & Repositories

> Configure DNF repositories, install packages, and manage software sources.

| # | Lab | Key Commands |
|---|-----|-------------|
| 06 | [Configure Repository Access](https://github.com/kelvintechnical/Configure-Repository-Access-) | `dnf`, `tee`, `/etc/yum.repos.d/` |
| 07 | [Install Package Groups](https://github.com/kelvintechnical/install-package-group) | `dnf group list`, `dnf groupinstall`, `dnf groupremove` |

---

### ⏰ System Time & Locale

> Set timezone, configure NTP, and ensure time synchronization persists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 07 | [Configure Timezone and Time Synchronization](https://github.com/kelvintechnical/Configure-Timezone-and-Time-Synchronization) | `timedatectl`, `systemctl enable --now chronyd` |
| 08 | [Configure NTP Time Source](https://github.com/kelvintechnical/configure-ntp) | `/etc/chrony.conf`, `chronyc sources`, `iburst` |

---

### 🔧 Essential Tools & File Operations

> Search, filter, redirect, and manage files from the command line.

| # | Lab | Key Commands |
|---|-----|-------------|
| 09 | [Search for a String and Save Output](https://github.com/kelvintechnical/search-string-save-output) | `grep`, `tee`, `>` |
| 10 | [Find and Save Config Files](https://github.com/kelvintechnical/find-save-config-files) | `find -type f -name -user`, `2>/dev/null` |
| 11 | [Locate Command Documentation](https://github.com/kelvintechnical/locate-command-docs) | `find /usr/share/doc`, `rpm -qf`, `rpm -qd` |
| 12 | [Standard File Compression with gzip](https://github.com/kelvintechnical/standard-file-compression) | `gzip`, `gunzip`, `zcat`, `gzip -k`, `gzip -v` |
| 13 | [High-Ratio Compression with bzip2](https://github.com/kelvintechnical/high-ratio-compression) | `bzip2`, `bunzip2`, `bzcat`, `bzip2 -k`, `bzip2 -v` |
| 14 | [Create Standard Archives with tar](https://github.com/kelvintechnical/create-standard-archives) | `tar -cvf`, `tar -tvf`, `tar -xvf` |
| 15 | Create Compressed Archives *(coming soon)* | `tar -czf`, `tar -cjf`, `tar -cJf`, `xz` |

---

### 👥 User & Group Management

> Create and manage users and groups, control login access, and enforce account policies.

| # | Lab | Key Commands |
|---|-----|-------------|
| 16 | [User & Group Management / Permissions](https://github.com/kelvintechnical/User-Group-Management-Permissions) | `useradd`, `groupadd`, `chown`, `chmod`, `id`, `getent` |
| 17 | [Disable User Login Without Removing the Account](https://github.com/kelvintechnical/disable-user-login) | `usermod -s /sbin/nologin`, `getent passwd` |

---

### 🔒 Permissions, Special Bits & ACLs

> Configure standard permissions, special bits, and access control lists.

| # | Lab | Key Commands |
|---|-----|-------------|
| 18 | [Configure SGID and Sticky Bit](https://github.com/kelvintechnical/sgid-sticky-bit) | `chmod g+s`, `chmod +t`, `ls -ld` |
| 19 | Configure ACLs *(coming soon)* | `getfacl`, `setfacl`, default ACLs |

---

### 💾 Storage Management

> Create and manage partitions, filesystems, and disk devices.

| # | Lab | Key Commands |
|---|-----|-------------|
| 20 | Create and Format Partitions *(coming soon)* | `fdisk`, `parted`, `mkfs`, `lsblk` |
| 21 | Mount Filesystems & Configure fstab *(coming soon)* | `mount`, `umount`, `/etc/fstab`, `UUID` |
| 22 | Create and Activate Swap Space *(coming soon)* | `mkswap`, `swapon`, `swapoff`, `/etc/fstab` |

---

### 🗂 LVM (Logical Volume Management)

> Create, extend, and manage logical volumes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 23 | Create LVM Volumes *(coming soon)* | `pvcreate`, `vgcreate`, `lvcreate` |
| 24 | Extend and Reduce LVM Volumes *(coming soon)* | `lvextend`, `lvreduce`, `resize2fs`, `xfs_growfs` |

---

### 🛡️ SELinux

> Manage SELinux modes, contexts, booleans, and troubleshoot denials.

| # | Lab | Key Commands |
|---|-----|-------------|
| 25 | Manage SELinux Modes and Contexts *(coming soon)* | `getenforce`, `setenforce`, `semanage`, `restorecon` |
| 26 | Manage SELinux Booleans and Troubleshoot Denials *(coming soon)* | `getsebool`, `setsebool`, `audit2allow`, `ausearch` |

---

### 🔥 Firewall (firewalld)

> Manage firewall rules, zones, ports, and services.

| # | Lab | Key Commands |
|---|-----|-------------|
| 27 | Configure firewalld Rules *(coming soon)* | `firewall-cmd`, `--add-service`, `--add-port`, `--permanent` |
| 28 | Manage firewalld Zones *(coming soon)* | `--zone`, `--list-all`, `--change-interface` |

---

### ⚙️ Systemd & Services

> Manage system services, unit files, and boot targets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 29 | Manage Services with systemctl *(coming soon)* | `systemctl start/stop/enable/disable/status` |
| 30 | Create and Manage systemd Unit Files *(coming soon)* | Unit file syntax, `systemctl daemon-reload` |
| 31 | Manage Boot Targets *(coming soon)* | `systemctl get-default`, `systemctl set-default`, `rescue.target` |

---

### 🥾 Boot Process & GRUB

> Understand the boot process, reset root passwords, and configure GRUB.

| # | Lab | Key Commands |
|---|-----|-------------|
| 32 | Reset Root Password via Boot *(coming soon)* | GRUB interrupt, `rd.break`, `chroot`, `passwd` |
| 33 | Configure GRUB Boot Loader *(coming soon)* | `grub2-mkconfig`, `/etc/default/grub` |

---

### 🕐 Scheduled Tasks

> Automate recurring and one-time tasks using cron and at.

| # | Lab | Key Commands |
|---|-----|-------------|
| 34 | Schedule Tasks with cron *(coming soon)* | `crontab -e`, `/etc/cron.d/`, cron syntax |
| 35 | Schedule One-Time Tasks with at *(coming soon)* | `at`, `atq`, `atrm` |

---

### 🔄 Process Management

> Monitor, control, and prioritize running processes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 36 | Monitor and Manage Processes *(coming soon)* | `ps aux`, `top`, `kill`, `pkill` |
| 37 | Manage Process Priority *(coming soon)* | `nice`, `renice`, `jobs`, `bg`, `fg` |

---

### 📋 Log Management

> Query and manage system logs using journalctl and rsyslog.

| # | Lab | Key Commands |
|---|-----|-------------|
| 38 | Query Logs with journalctl *(coming soon)* | `journalctl -u`, `-p`, `--since`, `--until` |
| 39 | Configure rsyslog *(coming soon)* | `/etc/rsyslog.conf`, log facilities, log rotation |

---

### 🌍 Web Services (Apache)

> Install, configure, and verify the Apache web server.

| # | Lab | Key Commands |
|---|-----|-------------|
| 40 | [Configure Apache to Serve Default and Custom Web Content](https://github.com/kelvintechnical/apache-custom-content) | `httpd`, `semanage fcontext`, `restorecon`, `curl` |

---

### ⚡ System Performance & Tuning

> Identify and apply system tuning profiles using tuned.

| # | Lab | Key Commands |
|---|-----|-------------|
| 41 | [Enable Recommended Tuning Profile](https://github.com/kelvintechnical/tuning-profile) | `tuned-adm recommend`, `tuned-adm profile`, `tuned-adm active` |

---

### 📜 Shell Scripting & Automation

> Write conditional bash scripts that handle arguments, validate input, and return exit codes.

| # | Lab | Key Commands |
|---|-----|-------------|
| 42 | [Argument-Based Conditional Script](https://github.com/kelvintechnical/argument-script) | `$1`, `$#`, `if/elif/else`, `exit 5`, `chmod +x` |

---

### 🔗 Remote Administration & Network Tools

> Remotely administer systems, transfer files, test ports, and verify network services.

| # | Lab | Key Commands |
|---|-----|-------------|
| 43 | [Command-Line Web and FTP Testing](https://github.com/kelvintechnical/elinks-iftp) | `elinks -dump`, `lftp`, `get`, `mget`, `put` |
| 44 | [Command-Line Email Testing](https://github.com/kelvintechnical/mutt-mail-smtp) | `mail -s`, `mutt -f`, `postfix`, `/var/mail/` |

---

### 🐳 Containers & Runtime Management

> Build and run containerized Linux environments using Docker/Podman, including port mapping, named containers, and interactive shells.

| # | Lab | Key Commands |
|---|-----|-------------|
| 45 | [Launch Named Root Container with Port Mapping](https://github.com/kelvintechnical/Launch-Named-Root-Container-with-Port-Mapping) | `podman run`, `docker run`, `-p`, `--name`, `-it` |

---

## 🤖 RHCE EX294 Labs

Labs organized by official RHCE EX294 exam objectives. Requires RHCSA as a prerequisite.

---

### 📡 Ansible Fundamentals

> Install Ansible, configure inventory, and run ad-hoc commands.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | Ansible Installation and Inventory *(coming soon)* | `ansible`, `ansible.cfg`, `inventory` |
| 02 | Ansible Ad-Hoc Commands *(coming soon)* | `ansible -m`, `ping`, `command`, `shell` |

---

### 📝 Ansible Playbooks

> Write and execute YAML playbooks with tasks, handlers, and variables.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | Write Your First Playbook *(coming soon)* | YAML syntax, `hosts`, `tasks`, `become` |
| 04 | Playbook Variables and Handlers *(coming soon)* | `vars`, `notify`, `handlers`, `register` |

---

### 🎭 Ansible Roles

> Structure reusable Ansible content using roles.

| # | Lab | Key Commands |
|---|-----|-------------|
| 05 | Create and Use Ansible Roles *(coming soon)* | `ansible-galaxy init`, role directory structure |
| 06 | Use Roles from Ansible Galaxy *(coming soon)* | `ansible-galaxy install`, `requirements.yml` |

---

### 🧩 Jinja2 Templates

> Generate dynamic config files using Ansible templates.

| # | Lab | Key Commands |
|---|-----|-------------|
| 07 | Create and Deploy Jinja2 Templates *(coming soon)* | `template` module, `{{ variable }}`, `{% for %}` |

---

### 🔒 Ansible Vault

> Encrypt and manage sensitive data in playbooks.

| # | Lab | Key Commands |
|---|-----|-------------|
| 08 | Encrypt Secrets with Ansible Vault *(coming soon)* | `ansible-vault create`, `encrypt`, `decrypt`, `--ask-vault-pass` |

---

## ☸️ CKA Labs

Labs organized by official CKA exam objectives.

---

### 🏗️ Cluster Architecture

> Understand Kubernetes components and cluster setup.

| # | Lab | Key Commands |
|---|-----|-------------|
| 01 | Explore Cluster Components *(coming soon)* | `kubectl get nodes`, `kubectl cluster-info` |
| 02 | Install a Cluster with kubeadm *(coming soon)* | `kubeadm init`, `kubeadm join` |

---

### 📦 Workloads

> Deploy and manage Pods, Deployments, and ReplicaSets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 03 | Deploy and Manage Pods *(coming soon)* | `kubectl run`, `kubectl get pods`, `kubectl describe` |
| 04 | Create and Scale Deployments *(coming soon)* | `kubectl create deployment`, `kubectl scale` |
| 05 | Configure DaemonSets and Jobs *(coming soon)* | `kubectl apply -f`, DaemonSet/Job YAML |

---

### 🌐 Kubernetes Networking

> Configure Services, Ingress, and NetworkPolicy.

| # | Lab | Key Commands |
|---|-----|-------------|
| 06 | Expose Applications with Services *(coming soon)* | `kubectl expose`, ClusterIP, NodePort, LoadBalancer |
| 07 | Configure Ingress *(coming soon)* | Ingress YAML, `kubectl get ingress` |
| 08 | Apply NetworkPolicy *(coming soon)* | NetworkPolicy YAML, ingress/egress rules |

---

### 💾 Kubernetes Storage

> Manage persistent storage with PVs, PVCs, and StorageClasses.

| # | Lab | Key Commands |
|---|-----|-------------|
| 09 | Create PersistentVolumes and PVCs *(coming soon)* | PV/PVC YAML, `kubectl get pv` |
| 10 | Configure StorageClasses *(coming soon)* | StorageClass YAML, dynamic provisioning |

---

### 🔐 Kubernetes Security

> Manage RBAC, ServiceAccounts, and Secrets.

| # | Lab | Key Commands |
|---|-----|-------------|
| 11 | Configure RBAC *(coming soon)* | `Role`, `ClusterRole`, `RoleBinding`, `kubectl auth can-i` |
| 12 | Manage Secrets and ServiceAccounts *(coming soon)* | `kubectl create secret`, ServiceAccount YAML |

---

### 🔧 Cluster Maintenance

> Upgrade clusters, manage nodes, and back up etcd.

| # | Lab | Key Commands |
|---|-----|-------------|
| 13 | Upgrade a Kubernetes Cluster *(coming soon)* | `kubeadm upgrade`, `apt-get`, `kubectl drain` |
| 14 | Back Up and Restore etcd *(coming soon)* | `etcdctl snapshot save`, `snapshot restore` |

---

### 🔍 Kubernetes Troubleshooting

> Diagnose and fix failing pods, nodes, and cluster components.

| # | Lab | Key Commands |
|---|-----|-------------|
| 15 | Troubleshoot Pods and Deployments *(coming soon)* | `kubectl logs`, `kubectl describe`, `kubectl exec` |
| 16 | Troubleshoot Node and Cluster Failures *(coming soon)* | `kubectl get nodes`, `systemctl status kubelet` |

---

## 🧭 How to Use This Repo

1. **New to Linux?** Start with the [companion repos](#-companion-repos) above
2. **RHCSA prep?** Work through the [RHCSA labs](#-rhcsa-ex200-labs) in domain order
3. **RHCE prep?** Complete RHCSA first, then move to [RHCE labs](#-rhce-ex294-labs)
4. **CKA prep?** Tackle [CKA labs](#-cka-labs) after solid Linux fundamentals
5. **Practice on a RHEL AMI** — all RHCSA/RHCE labs tested on AWS RHEL 9 AMI

---

## 👤 Author & Connect

**Kelvin R. Tobias** — Software Engineer | AI Engineering Candidate | Consultant
📍 Kinston, NC

- B.S. Software Engineering, WGU (2026) — 3× Excellence Award
- M.S. AI Engineering, WGU (in progress)
- Certs: CompTIA Security+, Linux+, AWS Cloud Practitioner, ITIL 4 Foundation
- ✍️ Blog: [PyTorch Zero to One](https://hashnode.com/@kelvintechnical) — 32+ articles

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Kelvin%20Tobias-0A66C2?logo=linkedin)](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
[![GitHub](https://img.shields.io/badge/GitHub-kelvintechnical-181717?logo=github)](https://github.com/kelvintechnical)
[![Website](https://img.shields.io/badge/Web-kelvinintech.com-808000?logo=google-chrome)](https://kelvinintech.com)
[![Hashnode](https://img.shields.io/badge/Blog-PyTorch%20Zero%20to%20One-2962FF?logo=hashnode)](https://hashnode.com/@kelvintechnical)

---

<div align="center">

**⭐ Star this repo if it helped you on your Linux journey.**

*Part of a larger engineering stack — from Linux ops to AI infrastructure to computational biology research.*

</div>
