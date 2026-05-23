# 🗺️ Roadmap — linux-ops-mastery

> The full curriculum. Every lab that exists, is in progress, or is planned — organized by certification track and exam objective.
>
> Looking for the day-one starting point? See the **[Suggested Learning Path](README.md#-suggested-learning-path)** in the main README. Looking for what's already built? Jump to **[Currently Built](#-currently-built)** below.

---

## 📊 Counts at a Glance

| Track | ✅ Done | 🚧 In Progress | 📅 Planned | Total |
|---|---:|---:|---:|---:|
| RHCSA EX200 | 5 | 8 | 137 | 150 |
| RHCE EX294 | 0 | 0 | 20 | 20 |
| CKA | 0 | 0 | 20 | 20 |
| CKAD | 0 | 0 | 22 | 22 |
| **Total** | **5** | **8** | **199** | **212** |

> Counts above include the 27+ external companion-repo labs linked from the main README plus the 13 in-repo labs in [`labs/`](labs/). The 183 figure from `future_labs.txt` is preserved as a subset of the 📅 Planned column. See [Summary by Category](#-summary-by-category) at the bottom for per-section breakdowns.

---

## 🔑 Status Legend

| Symbol | Meaning |
|---|---|
| ✅ **Done** | Full lab README in this repo with concept, tasks, troubleshooting, and capstone |
| 🚧 **In Progress** | Placeholder lab page with title + task details checked in; full walkthrough being written |
| 📅 **Planned** | Listed in `future_labs.txt`; task definition is exam-accurate, but no page has been started yet |

---

## 🏷️ ID Prefix System

Each planned lab gets a stable per-category identifier so cross-referencing survives renumbering. The `-F` suffix in every ID below stands for "Future"; once a lab is built and promoted, its `-F` is dropped.

| Prefix | Category |
|---|---|
| `LVM-F##` | LVM (Logical Volume Management) |
| `STOR-F##` | Storage Management (partitions, fstab, mounts) |
| `SEL-F##` | SELinux |
| `NET-F##` | Networking (interfaces, hostname, /etc/hosts) |
| `PKG-F##` | Package Management & Repositories |
| `FW-F##` | Firewall (firewalld) |
| `SSH-F##` | Remote Administration & SSH |
| `WEB-F##` | Web Services (Apache) |
| `USER-F##` | User & Group Management |
| `PERM-F##` | Permissions, Special Bits & ACLs |
| `SUDO-F##` | Sudo & Privilege |
| `NFS-F##` | NFS & AutoFS / Filesystem Mounts |
| `CRON-F##` | Scheduled Tasks (cron, at, systemd timers) |
| `FILES-F##` | Essential Tools & File Operations |
| `TEXT-F##` | Text File Management |
| `ARCH-F##` | Archives & Compression |
| `TIME-F##` | System Time & Locale |
| `BOOT-F##` | Boot Process & GRUB |
| `SYSD-F##` | Systemd & Services |
| `PERF-F##` | System Performance & Tuning |
| `CON-F##` | Containers & Flatpak |
| `SCRIPT-F##` | Shell Scripting & Automation |
| `PROC-F##` | Process Management |
| `DOC-F##` | Documentation Tools |
| `ENV-F##` | Environment & Shell Configuration |
| `RHCE-F##` | RHCE / Ansible |
| `CKA-F##` | CKA (Cluster Administrator) |
| `CKAD-DES-F##` | CKAD — Application Design and Build |
| `CKAD-DEP-F##` | CKAD — Application Deployment |
| `CKAD-OBS-F##` | CKAD — Observability and Maintenance |
| `CKAD-ENV-F##` | CKAD — Environment, Config & Security |
| `CKAD-NET-F##` | CKAD — Services and Networking |

---

## ✨ Currently Built

The labs with full or placeholder content in this repository today, plus links straight to the file.

| Status | Lab | Location |
|---|---|---|
| ✅ | Create LV `lvol1` (ext4, 280 MB) and Mount Persistently | [`labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/) |
| ✅ | Create LV with XFS Filesystem | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) |
| ✅ | Scheduling Jobs with systemd Timers | [`labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/) |
| ✅ | Find Files by Modification Time and Act on Them | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) |
| ✅ | Lock User Account and Capture Regex Evidence | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) |
| 🚧 | Online Extend an LV and Its Filesystem Without Unmounting | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) |
| 🚧 | Create a Swap Partition by UUID | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) |
| 🚧 | Create an Ext4 Partition Mounted by LABEL | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) |
| 🚧 | Apply Recursive SELinux Contexts to a New Directory | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) |
| 🚧 | User-Level Cron Job with `find -exec` | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) |
| 🚧 | Install Development Tools Package Group with Output Capture | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) |
| 🚧 | Bidirectional Bash Script with Argument Logic | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) |
| 🚧 | Rootless Container with Bind Mount and systemd Auto-Start | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) |

> The main [README](README.md) tracks an additional ~27 standalone companion-repo labs (one repo per micro-topic) numbered 01–183+. This roadmap focuses on the in-repo `labs/` directory + future lab planning.

---

## 🎯 RHCSA Track (EX200)

### 🗂 LVM (Logical Volume Management)

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| ✅ | — | Create LV `lvol1` (ext4, 280 MB) | [`labs/lvm-create-lvol1-ext4/`](labs/lvm-create-lvol1-ext4/) — `pvcreate`, `vgcreate`, `lvcreate -L 280M -n lvol1 vgtest`, ext4, persistent UUID mount on `/mnt/mnt1` |
| ✅ | — | Create LV with XFS Filesystem | [`labs/lvm-create-lv1-xfs/`](labs/lvm-create-lv1-xfs/) — `lv1` in `vg1` with 8 MB PE size, 10 LEs, XFS, persistent mount on `/mnt/lvfs1` |
| 🚧 | LVM-F01 | Online Extend an LV and Its Filesystem Without Unmounting | [`labs/lvm-online-extend-xfs/`](labs/lvm-online-extend-xfs/) — `lvextend -L +64M`, then `xfs_growfs` without taking FS offline; verify `lvs` and `df -h` before/after |
| 📅 | LVM-F02 | Create an LVM VDO Volume with Thin Provisioning | Build a Virtual Data Optimizer volume on a 5 GB physical disk: `vdo create --name=vdo1 --device=/dev/sdb --vdoLogicalSize=20G`; mount with ext4 and XFS variants; persistent fstab with `_netdev,x-systemd.requires=vdo.service` |
| 📅 | LVM-F03 | LV by Extent Count in a VG with Custom PE Size (ext4 variant) | `vgcreate -s 8M vgstore /dev/vdb1`, `lvcreate -l 50 -n lvdata vgstore` (= 400 MiB LV), mkfs.ext4, persistent mount on `/mnt/data` — the ext4 sibling of the existing XFS lv1/vg1 lab |
| 📅 | LVM-F04 | LV Sized as a Percentage of the VG with XFS + UUID Mount | `lvcreate -l 50%VG -n mylv myvg`, mkfs.xfs, capture UUID with `blkid`, fstab UUID entry on `/mnt/mylv` — proves the percent-of-VG sizing syntax |
| 📅 | LVM-F05 | LV Sized as a Percentage of Free Space with XFS | `lvcreate -l 75%FREE -n lvstore vgdata`, mkfs.xfs, fstab UUID entry on `/mnt/lvm` — the "use most of what's left" sizing pattern, distinct from `%VG` |
| 📅 | LVM-F06 | LV with Extent Count + Reserved Free Extents Constraint | `vgcreate -s 16M team_vg /dev/sdb1`, `lvcreate -l 40 -n team_lv team_vg` while leaving at least 10 free extents — proves you read the constraint |
| 📅 | LVM-F07 | Online Resize LV to a New Total Extent Count + Grow ext4 | `lvresize -l 85 /dev/vgstore/lvdata && resize2fs ...`; `-l 85` means "exactly 85 extents total," not "add 85" |
| 📅 | LVM-F08 | Add Extents to an Existing LV + Grow XFS Online | `lvextend -l +8 /dev/team_vg/team_lv && xfs_growfs /mnt/team_lv` — "add N extents" expressed instead of "total N extents" |
| 📅 | LVM-F09 | Create Swap from Remaining VG Free Space | `lvcreate -L 500M -n swap_lv team_vg`, `mkswap`, `swapon`, fstab UUID entry `swap swap defaults 0 0` |

---

### 💾 Storage Management (Partitions & fstab)

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 🚧 | STOR-F01 | Create a Swap Partition by UUID | [`labs/storage-swap-partition-uuid/`](labs/storage-swap-partition-uuid/) — `mkswap`, capture UUID, append to `/etc/fstab` with `sw 0 0`, `swapon -a`, verify `swapon --show` |
| 🚧 | STOR-F02 | Create an Ext4 Partition Mounted by LABEL | [`labs/storage-ext4-partition-label/`](labs/storage-ext4-partition-label/) — `mkfs.ext4 -L stdlabel`, fstab entry using `LABEL=` instead of `UUID=`, mount on `/mnt/stdfs1` |
| 📅 | STOR-F03 | Create an MBR Partition with ext4 Mounted by LABEL | `parted /dev/vdb mklabel msdos`, `mkpart primary ext4 1MiB 2GiB`, `mkfs.ext4 -L MYDEV`, fstab `LABEL=MYDEV /mnt/dev ext4 defaults 0 2`, prove persistence after reboot |
| 📅 | STOR-F04 | Create a Companion LVM-Type Partition on the Same Disk | `parted /dev/vdb mkpart primary 2GiB 7GiB`, `set 2 lvm on`, prove with `fdisk -l` showing partition type `Linux LVM` — preps the disk for an LVM lab |

---

### 🛡 SELinux

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 🚧 | SEL-F01 | Apply Recursive SELinux Contexts to a New Directory | [`labs/selinux-recursive-contexts-direct01/`](labs/selinux-recursive-contexts-direct01/) — `mkdir /direct01`, `semanage fcontext -a -e /root /direct01`, `restorecon -Rv`, prove with `ls -Zd` before and after |
| 📅 | SEL-F02 | Add a Custom HTTP Port to the SELinux Policy Database | `semanage port -a -t http_port_t -p tcp 8300`, verify with `semanage port -l \| grep http_port_t`, prove the change survives a relabel |
| 📅 | SEL-F03 | Set SELinux to Permissive Mode Persistently | Edit `/etc/selinux/config: SELINUX=permissive`, `setenforce 0`, prove with `getenforce` and reboot to verify persistence |
| 📅 | SEL-F04 | Apply Recursive SELinux Context from a Reference Directory | `mkdir /dir && mkdir /dir/subdir{1,2}`, `semanage fcontext -a -e /etc /dir`, `restorecon -RFv /dir`, prove with `ls -Zd /dir/subdir1` matching `/etc/skel` exactly |
| 📅 | SEL-F05 | Configure Apache to Serve from a Non-Default Directory | `mkdir /web`, drop `practice.html`, `semanage fcontext -a -t httpd_sys_content_t '/web(/.*)?'`, `restorecon -Rv /web`, prove `ls -Z` and `curl http://localhost/web/practice.html` |
| 📅 | SEL-F06 | Toggle the `httpd_can_network_connect` Boolean Persistently | `setsebool -P httpd_can_network_connect on`, prove `getsebool` shows on, reboot and re-verify — the canonical SELinux boolean lab |

---

### 🌐 Networking

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | NET-F01 | Manual Hostname Configuration by Editing `/etc/hostname` | Set the hostname *without* `hostnamectl`: write the FQDN directly into `/etc/hostname`, refresh the shell prompt, verify after reboot |
| 📅 | NET-F02 | Manual Network Configuration by Editing Connection Files | Configure IP/gateway/DNS without nmcli: hand-edit the keyfile under `/etc/NetworkManager/system-connections/` or `/etc/sysconfig/network-scripts/ifcfg-*`, `nmcli connection reload`, prove persistence |
| 📅 | NET-F03 | Configure Static IPv4 with Specific Host Address | `nmcli con mod ens-XX ipv4.addresses 192.168.50.10/24`, `ipv4.gateway 192.168.50.1`, `ipv4.dns "8.8.8.8 8.8.4.4"`, `ipv4.method manual`, `connection.autoconnect yes`; prove persistence after reboot |
| 📅 | NET-F04 | Configure Static IPv6 Address with DNS Search Domain | `ipv6.addresses fd02::42/64`, `ipv6.gateway fd02::1`, `ipv6.dns fd02::222`, `ipv6.dns-search example.local`, hostname `node1.example.local` |
| 📅 | NET-F05 | Dual-Stack IPv4 + IPv6 with Local Host Resolution | Configure both `192.168.56.25/24` and `fd12:3456:789a:1::25/64` on one interface, set hostname `node1.lab3.example.net`, add `/etc/hosts` entry so short and FQDN both resolve locally |

---

### 📦 Package Management & Repositories

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 🚧 | PKG-F01 | Install Development Tools Package Group with Output Capture | [`labs/dnf-install-dev-tools-capture/`](labs/dnf-install-dev-tools-capture/) — `dnf groupinstall "Development Tools"`, then `dnf group info "Development Tools"` into `/var/tmp/systemtools.out` |
| 📅 | PKG-F02 | Configure Local Repository from Installation ISO Media | Mount RHEL 9 ISO at `/repo` with a persistent loop entry in `/etc/fstab`, create `/etc/yum.repos.d/local-baseos.repo` + `local-appstream.repo` pointing at `file:///repo/BaseOS` and `/repo/AppStream` with `gpgcheck=0` |
| 📅 | PKG-F03 | Configure Two HTTP-Hosted Repositories from a Network Source | Create BaseOS and AppStream `.repo` files pointing at `http://repo.example.com/rhel9/{BaseOS,AppStream}` with `enabled=1` and appropriate `gpgcheck`, prove with `dnf repolist enabled` + `dnf install -y httpd` |

---

### 🔥 Firewall (firewalld)

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | FW-F01 | Open Multiple Services at Once for Web Hosting | `firewall-cmd --permanent --add-service={ssh,http,https}`, reload, verify with `--list-services`, prove external connectivity from a second host |
| 📅 | FW-F02 | Open a Non-Standard SSH Port + Move SSH There | `firewalld --add-port=88/tcp --permanent`, then `sshd_config Port 88`, `semanage port -a -t ssh_port_t -p tcp 88`, restart sshd, prove `ssh -p 88` works while port 22 is closed |

---

### 🔗 Remote Administration & SSH

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | SSH-F01 | Configure SSH to Listen on a Custom Port | `sshd_config Port 88`, SELinux `semanage port -a -t ssh_port_t -p tcp 88`, `firewall-cmd --add-port=88/tcp --permanent`, restart sshd — three-system coordination |
| 📅 | SSH-F02 | Permit Root SSH Login with Authentication-Failure Lockout | `sshd_config PermitRootLogin yes` + `MaxAuthTries 3`, demonstrate the 4th failed attempt is rejected and earlier attempts produce `pam_unix(sshd:auth): authentication failure` lines in `journalctl -u sshd` |
| 📅 | SSH-F03 | Passwordless SSH from Root to Remote Root | `ssh-keygen -t ed25519 -N ""` on Node1, `ssh-copy-id root@Node2`, verify with `ssh root@Node2 hostname` returning remote hostname without password |
| 📅 | SSH-F04 | Key-Based SSH from a User to a Remote Root on a Custom Port | As `marvin` on Node2: `ssh-keygen`, `ssh-copy-id -p 88 root@Node1`, prove `ssh -p 88 root@Node1` succeeds without a password |
| 📅 | SSH-F05 | Configure Local `/etc/hosts` Name Resolution | Add `192.168.56.25 node1.lab3.example.net node1` so `ping node1` resolves locally, persists across reboots, and `ssh node1` works without DNS |
| 📅 | SSH-F06 | Secure File Transfer with `scp` Preserving Attributes | `scp -p /etc/fstab user@host:~/` — `-p` preserves timestamps and mode but NOT ownership across users; for ownership use `rsync -avz --chown` |

---

### 🌍 Web Services (Apache)

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | WEB-F01 | Apache Listening on a Non-Standard TCP Port | `Listen 85` in `/etc/httpd/conf.d/port.conf` drop-in, `semanage port -a -t http_port_t -p tcp 85`, `firewall-cmd --add-port=85/tcp --permanent`, `curl http://localhost:85` returns welcome page |
| 📅 | WEB-F02 | Apache Default Page + Custom Content Directory | Modify `/var/www/html/index.html`, create `/web/practice.html`, `Require all granted`, `semanage fcontext httpd_sys_content_t` for `/web(/.*)?`, `restorecon -Rv /web`, curl both URLs |
| 📅 | WEB-F03 | Apache Subdirectory Routing with SELinux Inheritance | `mkdir /var/www/html/route_station`, drop index.html, confirm new directory inherited `httpd_sys_content_t` from parent, curl `http://Node1/route_station/index.html` |
| 📅 | WEB-F04 | Password-Protected Apache Directory with htpasswd | `htpasswd -c /etc/httpd/.htpasswd alice`, `AuthType Basic` + `AuthUserFile` + `Require valid-user`, prove `curl -u alice:pw http://localhost/protected/` succeeds while anonymous returns HTTP 401 |
| 📅 | WEB-F05 | Apache SSL Virtual Host with Self-Signed Certificate | `openssl req -x509 -newkey rsa:2048 -nodes -keyout ... -out ... -days 365`, ssl.conf `SSLCertificateFile`/`SSLCertificateKeyFile`, `firewall-cmd --add-service=https`, `curl -k https://localhost` |

---

### 👥 User & Group Management

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| ✅ | — | Lock User Account and Capture Regex Evidence | [`labs/user-lock-capture-regex/`](labs/user-lock-capture-regex/) — `passwd -l user70`, `grep -E '^user70:!' /etc/shadow` redirected to evidence file — proves the lock via the leading `!` in the shadow hash field |
| 📅 | USER-F01 | Group with Fixed GID + User with Primary/Secondary Groups | `groupadd -g 3500 admins`, `groupadd users`, `useradd -u 3455 -g admins -G users harry`, prove with `id harry` showing `uid=3455, gid=3500(admins), groups=admins,users` |
| 📅 | USER-F02 | User Without Interactive Shell (`nologin`) That Still Authenticates | `useradd -s /sbin/nologin sarah`, set password, prove SSH login rejected with "This account is currently not available" but PAM-level password auth succeeds for password-only services |
| 📅 | USER-F03 | User With Explicit (Hand-Built) Home Directory | `useradd -M bruce`, `mkdir /home/bruce`, `cp -av /etc/skel/. /home/bruce`, `chown -R bruce:bruce`, `chmod 700` — the "I built the home dir myself" path |
| 📅 | USER-F04 | Force Password Change at Next Login | `passwd --expire liam` (or `chage -d 0 liam`), prove with `chage -l liam` showing "Password must be changed," then ssh in and observe the forced-change prompt |
| 📅 | USER-F05 | Set Hard Account Expiry Date | `chage -E 2029-01-01 lina`, or `chage -E $(date -d '+7 days' +%Y-%m-%d) marvin` for relative expiry, prove with `chage -l USER` |
| 📅 | USER-F06 | Welcome.txt Auto-Created for Every New User via `/etc/skel` | `echo "Welcome Onboard!" > /etc/skel/Welcome.txt`, useradd a new user, verify Welcome.txt appears in their home with right ownership and mode |
| 📅 | USER-F07 | Configure System-Wide Password Aging Policy | Edit `/etc/login.defs`: `PASS_MAX_DAYS 30`, `PASS_MIN_LEN 9`; prove the policy applies only to users created *after* the edit |
| 📅 | USER-F08 | Reset Root Password from GRUB Boot Menu (`rd.break` Path) | Edit GRUB at boot, append `rd.break`, ctrl-x, `mount -o remount,rw /sysroot`, `chroot /sysroot`, `passwd root`, `touch /.autorelabel`, two `exit`s, reboot |

---

### 🔒 Permissions, Special Bits & ACLs

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | PERM-F01 | Collaborative SGID Directory with Multi-User Write Test | `mkdir /sdata`, `chown root:group30`, `chmod 2770`, add `user60` + `user80` to `group30`, prove a file created by `user60` can be edited *and* not deleted by `user80` |
| 📅 | PERM-F02 | File Copy with Combined Ownership + Permissions + ACL + Future-User Safety | `cp /etc/fstab /var/tmp`, `chown root:admins`, `chmod 644`, `setfacl -m u:harry:rw,u:bruce:r,u:natasha:---`, prove "other" still has read so future users automatically get access |
| 📅 | PERM-F03 | ACL with Mixed Read/Write/Read-Only Per User | `cp /etc/hosts /srv/project/hosts_copy`, `setfacl u:emma:rw,u:liam:rw,u:sophie:r,m::rw`, default ACL on parent dir for inheritance, verify with `getfacl` and `sudo -u sophie tee` test |
| 📅 | PERM-F04 | Per-User Default umask via `~/.bashrc` | `echo 'umask 0577' >> /home/bruce/.bashrc` — files become `-r--------`, directories become `dr-x------` for owner only, prove with `touch ~/test && stat -c '%a' ~/test` showing 400 |
| 📅 | PERM-F05 | Collaborative Group Directory with SGID + Sticky Bit | `mkdir /data/engineers`, `chown root:engineers`, `chmod 3770` — SGID for group inheritance, sticky for owner-only delete, prove with two users creating and failing to delete each other's files |
| 📅 | PERM-F06 | Restricted Directory Where Owner Has chmod But No rwx | `mkdir /data/engineers`, `chown tom:engineers`, `chmod g+rwx,o-rwx,u-rwx` — prove tom can still `chmod` because owner even though he cannot read or write |

---

### 🛂 Sudo & Privilege

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | SUDO-F01 | Full Sudo for a User + NOPASSWD for an Entire Group | `visudo`: `john ALL=(ALL) ALL` + `%admins ALL=(ALL) NOPASSWD: ALL`, prove via `sudo -l` per user, password prompt for john but no prompt for an admins member |
| 📅 | SUDO-F02 | Granular Sudo: Allow `passwd` Except Root Password Changes | `visudo`: `brian ALL=(ALL) /usr/bin/passwd [A-Za-z]*, !/usr/bin/passwd root, !/usr/bin/passwd ""` — the classic deny-list pattern preventing root password hijacking |
| 📅 | SUDO-F03 | Privileged User with Account Expiry | `useradd -u 4545 marvin`, `passwd marvin`, add to wheel, `chage -E $(date -d '+7 days' +%F) marvin` so account self-deletes 7 days later |

---

### 📁 NFS & AutoFS / Filesystem Mounts

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | NFS-F01 | NFS Server + AutoFS Direct Map | Export `/rh_share` on server; on client write `/etc/auto.master.d/direct.autofs` + `/etc/auto.direct` map that mounts share on demand at `/mnt/rh_share`, test cross-user file creation honoring NFS permissions |
| 📅 | NFS-F02 | NFS Home-Directory Export with AutoFS Indirect Map on Login | Server exports `/home/user60`; client indirect map under `/nfsdir` mounts the home dir automatically the first time `user60` logs in; prove unmount-on-idle |
| 📅 | NFS-F03 | NFS Static Export with Persistent `/etc/fstab` Mount | `exportfs -rav` on server, `server:/share5 /share6 nfs _netdev,defaults 0 0` in fstab on client, `mount -a`, prove survives reboot |
| 📅 | NFS-F04 | Configure a Node as an NFS Server (companion lab) | `dnf install nfs-utils`, `mkdir /exports/home`, `/etc/exports` `/exports/home *(rw,sync,no_root_squash)`, `exportfs -rav`, `systemctl enable --now nfs-server`, `firewall-cmd --add-service={nfs,mountd,rpc-bind}` |
| 📅 | NFS-F05 | AutoFS Indirect Map for Remote Home Dirs with 60s Timeout | `auto.master.d/homes.autofs` entry `/homes/remote /etc/auto.homes --timeout=60`, `/etc/auto.homes` with `* server.example.com:/exports/home/&`, prove on-demand + unmount after 60s idle |
| 📅 | NFS-F06 | AutoFS Direct Map for `/mnt/shared` with 5-Minute Timeout | `auto.master.d/direct.autofs` `/- /etc/auto.direct --timeout=300`, `/etc/auto.direct` `/mnt/shared -rw server.example.com:/srv/shared`, prove `cd /mnt/shared` triggers mount |

---

### ⏰ Scheduled Tasks (cron, at, systemd timers)

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| ✅ | — | Scheduling Jobs with systemd Timers | [`labs/scheduling-jobs-systemd-timer/`](labs/scheduling-jobs-systemd-timer/) — systemd timer unit + service unit, `OnCalendar=`, `systemctl list-timers` |
| 🚧 | CRON-F01 | User-Level Cron Job with `find -exec` | [`labs/cron-user-find-exec-coredir/`](labs/cron-user-find-exec-coredir/) — as `user70`: `crontab -e` schedules `find /var -name core -exec cp {} /var/tmp/coredir1 \;` Mondays at 01:20 |
| 📅 | CRON-F02 | User Cron Job at 12:45 AM Daily | As `bruce`: `crontab -e` `45 0 * * * /usr/bin/echo "EX200 Practice Test!" >> $HOME/cron.log`, verify with `crontab -l -u bruce` and tail the log |
| 📅 | CRON-F03 | Recurring User Cron Job Every 2 Minutes | As `linda`: `*/2 * * * * logger "RHCSA EX200 Practice Test 2 In Progress!"`, verify with `journalctl --since "5 minutes ago"` |
| 📅 | CRON-F04 | Weekday-Only Cron Job at 5:45 AM | As `emma`: `45 5 * * 1-5 logger "Good morning! Work day about to start."`, verify day-of-week range fires Mon–Fri only |
| 📅 | CRON-F05 | Midnight-Weekend Root Cron Job to Clean Empty Files in `/tmp` | Root crontab: `0 0 * * 6,0 find /tmp -maxdepth 1 -type f -empty -delete`, dry-run first with `-print`, verify fires Sat + Sun |
| 📅 | CRON-F06 | One-Time `at` Job for a Specific Wall-Clock Time | As `russ`: `echo 'echo "EX200 Mock Practice 1 Complete!" >> $HOME/practice.log' \| at 21:30`, verify with `atq` |
| 📅 | CRON-F07 | One-Time `at` Job One Hour from Now Writing to journald | As `alina`: `echo 'logger "Making Progress with EX200!"' \| at now + 1 hour`, verify journal entry under alina's UID |

---

### 🔧 Essential Tools & File Operations

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| ✅ | — | Find Files by Modification Time and Act on Them | [`labs/find-files-by-mtime/`](labs/find-files-by-mtime/) — `find / -mtime -30 -type f` redirected to `/var/tmp/modfiles.txt`, `-exec cp --parents`, `tar --files-from` capstone |
| 📅 | FILES-F01 | Find Files by Size Range and Copy Preserving All Attributes | `find /etc -type f -size +5M -size -10M -exec cp --preserve=ownership,mode,timestamps,context {} /find/largefiles/ \;`, prove with `stat -c '%A %U:%G %y'` |
| 📅 | FILES-F02 | Find Files Owned by a User Within a Size Range | `find / -xdev -user linda -type f -size +3M -size -50M 2>/dev/null -exec cp -a {} /root/linda-files/ \;` — suppresses permission-denied noise |
| 📅 | FILES-F03 | Find Configuration Files by Name and Owner | `find /etc -type f -name '*.conf' -user root > /root/config_files`, verify with `wc -l` and spot-check |
| 📅 | FILES-F04 | Find Files Modified More Than 30 Days Ago and Copy with Hierarchy | `find /etc -type f -mtime +30 -exec cp --parents --preserve=all {} /tmp/etc_backup/ \;` — `--parents` preserves the directory layout |
| 📅 | FILES-F05 | Find Directories with the SUID Bit Set + Copy with Attributes | `find / -xdev -type d -perm -4000 2>/dev/null -exec cp -a {} /security_backup/ \;` — security audits and forensic copies |
| 📅 | FILES-F06 | Find Directories by Size Range and Save Long Listing | `find / -xdev -type d -size +50k -size -100k 2>/dev/null \| xargs ls -ld > /root/moderate_dir_list.txt` — note `find` reports the *directory entry size*, not recursive contents size |
| 📅 | FILES-F07 | Hard and Symbolic Link Lifecycle Demonstration | `touch report.txt`, `ln report.txt report_hard.txt`, `ln -s report.txt report_symlink.txt`, `rm report.txt` — show hard link still has data but symlink is now dangling |

---

### 📄 Text File Management

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | TEXT-F01 | Extract Lines Containing a String Preserving Order | `grep 'bin' /etc/passwd > /root/bin_lines`, prove the line order matches the source with `grep -n` |
| 📅 | TEXT-F02 | Find Exact Word Matches with `grep -w` | `grep -wE 'bin' /etc/passwd > /root/bin_users.txt` — `-w` prevents matches inside longer words like `sbin`, `binary`, `roundbin` |
| 📅 | TEXT-F03 | Search Apache Configuration for Listen Directives | `grep '^Listen' /etc/httpd/conf/httpd.conf > /root/httpd_listen.txt`, the `^` anchor excludes commented-out Listen lines |

---

### 🗜 Archives & Compression

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | ARCH-F01 | Create an xz-Compressed Tar Archive | `tar -cJvf /archives/config_backup.tar.xz /etc`, restore with `tar -xJvf` into `/restore` — highest-compression-ratio option |
| 📅 | ARCH-F02 | Create an Uncompressed Standard Tar Archive | `tar -cvf /root/etc_opt.bak.tar /etc /opt` — the no-compression variant for streaming to other compressors |
| 📅 | ARCH-F03 | Restore a Tar Archive into a Specific Destination Directory | `mkdir -p /root/restored_tmp && tar -xzvf /root/tmp.tgz -C /root/restored_tmp`, prove with `find /root/restored_tmp -maxdepth 2` |

---

### ⏰ System Time & Locale

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | TIME-F01 | Set System Timezone via `timedatectl` | `timedatectl set-timezone Europe/London` — also practice America/New_York and Asia/Tokyo; verify with `timedatectl` and `date` |
| 📅 | TIME-F02 | Configure Chrony with a Specific NTP Server | Edit `/etc/chrony.conf`: comment out default pool, add `server utility.ntp.org iburst`, restart chronyd, `chronyc sources -v` showing `^*` reachability |

---

### 🥾 Boot Process & GRUB

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | BOOT-F01 | Enable Verbose Boot by Removing `quiet` and `rhgb` | Edit `/etc/default/grub`, remove `quiet rhgb` from `GRUB_CMDLINE_LINUX`, `grub2-mkconfig -o /boot/grub2/grub.cfg`, reboot and watch the verbose systemd boot log |

---

### ⚙️ Systemd & Services

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | SYSD-F01 | Set the Default Boot Target to `multi-user.target` | `systemctl set-default multi-user.target`, `systemctl isolate multi-user.target` for immediate effect, prove with `systemctl get-default` + reboot |

---

### ⚡ System Performance & Tuning

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | PERF-F01 | Apply the `virtual-guest` Tuning Profile | `tuned-adm profile virtual-guest` — virtualization-efficiency profile for VMs, verify with `tuned-adm active` |
| 📅 | PERF-F02 | Apply a Power-Saving / Virtualization-Balanced Profile | `tuned-adm profile balanced-battery` or `virtual-guest-powersave`, compare with `tuned-adm recommend`, prove active profile changed |

---

### 🐳 Containers & Flatpak

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 🚧 | CON-F01 | Rootless Container with Bind Mount and systemd Auto-Start | [`labs/podman-rootless-bind-mount-systemd/`](labs/podman-rootless-bind-mount-systemd/) — as `user80`, podman run ubi9 with `-v /data01:/data01`, generate user-level systemd unit, `loginctl enable-linger`, prove auto-start survives reboot without login |
| 📅 | CON-F02 | Build a Custom Container Image with a Containerfile | Write a Containerfile FROM ubi8/ubi9, RUN/COPY a small script printing `ls` + `pwd`, `podman build -t custom:latest`, push to local registry, run as named rootless container under `user60` |
| 📅 | CON-F03 | Rootless Container with Port Mapping + systemd Auto-Start | As `user60`: `podman run -d --name web -p 10000:80 ubi8`, `podman generate systemd --new --files`, copy to `~/.config/systemd/user/`, `loginctl enable-linger`, prove port 10000 reachable after reboot without login |
| 📅 | CON-F04 | Rootless Container with Bind Mount + Env Vars + Port Mapping | Everything-at-once: `podman run` as `user60` with `-v /host_data01:/container_data01`, `-e ENVIRON=Exam`, `-e KERN=$(uname -r)`, `-p 1050:1050`, ubi9; user-level systemd unit with linger |
| 📅 | CON-F05 | Authenticated Pull from `registry.redhat.io` | `podman login registry.redhat.io` with developer credentials, pull `ubi9/ubi`, prove with `podman images` and `podman run --rm ubi9/ubi cat /etc/redhat-release` |
| 📅 | CON-F06 | Build a UBI Image from a Single-Line Containerfile | Containerfile with just `FROM registry.redhat.io/ubi8/ubi-init`, `podman build -t ubigreeter`, podman run --rm — the simplest custom image |
| 📅 | CON-F07 | Rootless HTTP Container with Bind-Mounted DocumentRoot | `podman run -d --name webcon -p 8080:80 -v /var/www/html:/usr/local/apache2/htdocs:Z docker.io/library/httpd`, echo content > index.html, `curl localhost:8080` — `:Z` SELinux relabel is the main lesson |
| 📅 | CON-F08 | Rootless Database Container with Env Vars + Persistent Data | As `ray`: `podman run -d --name inventorydb -p 3308:3306 -e MYSQL_ROOT_PASSWORD=InvPass123 -v /home/ray/inventory_data:/var/lib/mysql:Z registry.redhat.io/rhel9/mariadb-1011` |
| 📅 | CON-F09 | Rootless Nginx with Custom Config + DocumentRoot Mounts | As `david`: `podman run -d --name mynginx -p 8080:80 -v /srv/nginx/html:/usr/share/nginx/html:Z -v /srv/nginx/conf:/etc/nginx/conf.d:Z docker.io/library/nginx`, prove SELinux context shows `container_file_t` |
| 📅 | CON-F10 | Multi-Mount Rootless Container with Two Bind Mounts + Port | `podman run -d --name ubicon -p 8089:8089 -v /opt/out:/opt/in:Z -v /opt/send:/opt/receive:Z registry.redhat.io/ubi9/ubi sleep infinity`, prove both bind mounts work and port is reachable |
| 📅 | CON-F11 | Add Both Flathub and RHEL Flatpak Remotes | `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`, `flatpak remote-add --if-not-exists rhel https://flatpaks.redhat.io/rhel.flatpakrepo`, verify with `flatpak remotes` |
| 📅 | CON-F12 | Install Flatpak Applications (Firefox + VLC + GIMP) | `flatpak search firefox` to find app ID, `flatpak install -y flathub org.mozilla.firefox`, repeat for VLC and GIMP, verify with `flatpak list --app` |
| 📅 | CON-F13 | User-Scoped vs System-Wide Flatpak Installation | Compare `flatpak install --user flathub org.mozilla.firefox` vs root `flatpak install --system`, prove `flatpak list --user` vs `--system` show different inventories |
| 📅 | CON-F14 | Remove Flatpak Apps, Prune Runtimes, Remove Remote | `flatpak uninstall -y org.videolan.VLC org.gimp.GIMP`, `flatpak uninstall --unused -y`, `flatpak remote-delete flathub`, verify with `flatpak list` and `flatpak remotes` |

---

### 📜 Shell Scripting & Automation

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 🚧 | SCRIPT-F01 | Bidirectional Bash Script with Argument Logic | [`labs/bash-bidirectional-arg-script/`](labs/bash-bidirectional-arg-script/) — `script.sh` prints "RHCSA" when given "RHCE" and vice versa; with no argument prints usage and exits 5 |
| 📅 | SCRIPT-F02 | Bash Script: Find Files Matching a Pattern and Print stat | Loop over `/usr/bin/ac*`, `[ -f $f ]` guard to exclude directories, run `stat $f` for each match, redirect to `/var/tmp/acstats.out` |
| 📅 | SCRIPT-F03 | Bash Script: Create a User Whose Name Comes from a Variable | Declare `ENV1=book1`, `useradd "$ENV1"`, set default password from stdin, verify `id "$ENV1"` |
| 📅 | SCRIPT-F04 | Countdown Timer Script with Argument or Interactive Prompt | If `$# -eq 1`, `COUNT=$1`; else `read -p`; `while [ $COUNT -gt 0 ]; do echo "$COUNT seconds remaining..."; sleep 1; ((COUNT--)); done`; install to `/usr/local/bin` |
| 📅 | SCRIPT-F05 | Sum of an Unknown Number of Integer Arguments | `$# -eq 0` → exit 1; else `for n in "$@"; do ((total+=n)); done; echo "Sum is $total"` — teaches `$@` iteration and arithmetic expansion |
| 📅 | SCRIPT-F06 | Find Users by Login Shell and Save the List | `getent passwd \| awk -F: '$7=="/bin/bash" {print $1}' > /root/bash_users.txt`, chmod +x, re-runnable so file is always current |
| 📅 | SCRIPT-F07 | Extract Login Shells of the Last 5 Users in `/etc/passwd` | `tail -5 /etc/passwd \| awk -F: '{printf "User %s has login shell %s\n", $1, $7}'` — teaches awk's printf formatting |
| 📅 | SCRIPT-F08 | Per-User Login Script via `.bash_profile` | As `john`: append `grep bash /etc/passwd > ~/bash-users.txt` to `~/.bash_profile` — every interactive login refreshes the file; user-scoped |
| 📅 | SCRIPT-F09 | Three-Way Argument-Based Script with Multi-Arg Rejection | `team.sh`: `$# > 1` → exit 5; `$1 == "ops"` → message; `$1 == "dev"` → different message; else usage |

---

### 🔄 Process Management

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | PROC-F01 | Start a Background Process with a Specific nice Value | `nice -n 10 sleep 3600 &`, capture `$!` into a variable, verify nice value with `ps -o pid,ni,cmd $!` |
| 📅 | PROC-F02 | Renice a Running Process to a Higher Priority | `renice -n -5 -p $PID` — requires root for negative niceness, prove with `ps -o pid,ni` before and after; teaches "negative is higher priority" counter-intuitive convention |
| 📅 | PROC-F03 | Lowest-Priority Background Task on User Login | As `lina`: in `~/.bash_profile` add `nice -n 19 sleep infinity &`, verify after fresh login that process exists with `ps -o pid,ni -u lina` showing `19` |
| 📅 | PROC-F04 | Clean Termination of a Background Process | `kill $PID` for SIGTERM first, verify exit, fall back to `kill -9` only on hung processes — teaches graceful-shutdown idiom and SIGTERM vs SIGKILL |

---

### 📖 Documentation Tools

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | DOC-F01 | Locate Command Documentation Under `/usr/share/doc` | `find /usr/share/doc -iname '*passwd*'`, display path of one matching file, `less` or `cat` to confirm relevance, prove package owns it with `rpm -qf` |

---

### 🌱 Environment & Shell Configuration

| Status | ID | Lab | Details / Link |
|---|---|---|---|
| 📅 | ENV-F01 | System-Wide Environment Variable via `/etc/profile.d` | `cat > /etc/profile.d/sys_tag.sh <<'EOF' \nexport SYS_TAG="RHCSA v9 EX200 PRACTICE EXAMS COMPLETED!"\nEOF`, chmod +x, prove every new shell has the variable with `printenv SYS_TAG` |

---

## 🎯 RHCE Track (EX294)

> Ansible automation labs. All entries below are 📅 Planned.

### Foundation (Common Tasks across all sample exams)

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F01 | Build an RHCE Ansible Control Project | `/home/ansible`, `ansible.cfg`, static inventory, groups `test/dev/prod/servers`, FQDN + short-name resolution |
| 📅 | RHCE-F02 | Bootstrap Managed Hosts with Ad-Hoc Commands | `setuphosts.sh`: install Python, create `ansible` user, write sudoers drop-in, ping module to verify |
| 📅 | RHCE-F03 | Configure a Repository Server with an Ansible Playbook | `setupreposerver.yml`: loop-mount RHEL ISO to `/var/ftp/repo`, disable firewalld, enable vsftpd with anonymous access |
| 📅 | RHCE-F04 | Configure Managed Repo Clients with Ad-Hoc Commands | Disable existing repos, add BaseOS + AppStream from `control.example.com` via `dnf config-manager` |

### Exam Practice 1 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F05 | HTTP Server and Client Playbooks with `site.yml` | `webserver.yml` installs httpd, `webclient.yml` installs curl, shared `vars/web.yml`, `templates/httpd.j2`, handler restarts httpd, `site.yml` ties them together |
| 📅 | RHCE-F06 | Convert HTTP Playbooks Into an Ansible Role | Refactor webserver tasks into a role with `defaults/main.yml`, `tasks/main.yml`, `templates/`, `handlers/`, then call from a new top-level play |
| 📅 | RHCE-F07 | Ansible Storage Role for `/web` with SELinux Contexts | `parted gpt mkpart 1MiB 100%`, mount `/web`, `semanage fcontext httpd_sys_content_t`, deploy `/web/index.html` with welcome message |

### Exam Practice 2 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F08 | Default Roles Path in `ansible.cfg` | Set `roles_path = /home/ansible/roles` while preserving system role locations as fallbacks |
| 📅 | RHCE-F09 | `setupstorage.yml` — Conditional LVM Playbook | Only on hosts with a second disk: 5GiB partition, `vgdata` with 8MiB PEs, `lvdata` 1GiB, ext3 format, `/data` persistent mount |
| 📅 | RHCE-F10 | `packagefacts.yml` — Package Version Report | Gather package facts, format kernel/bash/glibc as `packagename=version` into `/root/packages.txt` |
| 📅 | RHCE-F11 | Ansible Vault Credentials Workflow | `cloudpass.yml` with `CLOUDID` and `CLOUDPASS` encrypted, vault password file `vaultpass.txt`, `usevault.yml` reads vars and writes `/root/cloudcreds.txt` |
| 📅 | RHCE-F12 | Install Galaxy Roles from `requirements.yml` | `geerlingguy.nginx` + `geerlingguy.docker` into `/home/ansible/roles`, then `start-galaxy-roles.yml` plays both |
| 📅 | RHCE-F13 | Apache Role with Custom Template Showing HOSTNAME/IPADDRESS | Role enables httpd, opens firewall, deploys templated index.html using `ansible_facts.hostname` and `ansible_default_ipv4.address`; `runweb.yml` runs it on `test` group |
| 📅 | RHCE-F14 | Create Users from YAML Input with SHA256 Passwords | Read `users_pass.yml`; on `prod` create only users whose `department=profs`, set department as secondary group, hash passwords with `password_hash('sha512')` |

### Exam Practice 3 specifics

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | RHCE-F15 | Conditional Package Installation by Host Group | perl/php on dev/test/prod, "Virtualization Host" group on prod only, `dnf upgrade` on prod |
| 📅 | RHCE-F16 | Conditional LVM Playbook with Failure Messages | `vgdata` 2GiB only on prod; if missing print "vgprod does not exist"; if <1GiB free print "insufficient disk space available" |
| 📅 | RHCE-F17 | `sysreport.yml` — Hardware Report from a Template | Generate `hwtemplate.txt`, copy to `/root/report.txt` on each managed host, populate `NAME`, `IPADDRESS`, `TOTAL_MEMORY`, `NIC_NAME`, `SECOND_NIC_NAME=NONE` if absent |
| 📅 | RHCE-F18 | Ansible Vault Password Rotation | Create `anspass.txt` with `devpass` + `prodpass` under password `vaultpass`, then rekey to `myvaultpass` and confirm the file is still readable |
| 📅 | RHCE-F19 | RHEL Time Sync System Role (`rhel-system-roles.timesync`) | `settime.yml` uses `control.example.com` as time source with `makestep` enabled; verify `chronyc tracking`; print failure message if not synchronized |
| 📅 | RHCE-F20 | `runwebserver.yml` — Web Content with Symlink and Group Vars | Create `/webcontent/index.html` with welcome message, `USERNAME=anna` sourced from a `group_vars/prod` file, symlink `/var/www/html/index.html` to it, prove remote access |

---

## 🎯 CKA Track (Kubernetes Administrator)

> All entries below are 📅 Planned.

### Cluster Architecture, Installation, Configuration

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F01 | Highly Available Control Plane with kubeadm | Stacked-etcd HA topology with `kubeadm init --control-plane-endpoint`, three control planes behind a VIP/LB, `kubeadm join --control-plane` |
| 📅 | CKA-F02 | Install Cluster Components with Helm | `helm repo add`, `helm install`, `helm upgrade --atomic`, `helm rollback`, inspect `helm history` |
| 📅 | CKA-F03 | Manage Configs with Kustomize | `base/` + `overlays/dev/` + `overlays/prod/`, `kubectl apply -k`, `kustomize edit set image`, `SecretGenerator` and `ConfigMapGenerator` |
| 📅 | CKA-F04 | Container Runtime and Extension Interfaces | CRI: `crictl ps` with containerd; CNI: install Calico or Cilium and inspect `/etc/cni/net.d`; CSI: deploy a CSI driver and validate StorageClass |
| 📅 | CKA-F05 | Install and Configure an Operator with a CRD | Install Operator Lifecycle Manager or a vendor operator, define a CRD, create a custom resource, watch the controller reconcile |

### Workloads and Scheduling

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F06 | Perform a Rolling Update and Rollback | `kubectl set image deployment/web app=v2`, `kubectl rollout status`, `kubectl rollout undo`, control `maxSurge`/`maxUnavailable` |
| 📅 | CKA-F07 | Configure Pods with ConfigMaps | `kubectl create configmap --from-file` and `--from-literal`, project as env vars vs volume mounts, demonstrate hot reload limits |
| 📅 | CKA-F08 | Horizontal Pod Autoscaling | Deploy metrics-server, create HPA targeting CPU, hey/wrk load generator, watch `kubectl get hpa` scale up and back down |
| 📅 | CKA-F09 | ReplicaSet Self-Healing Demonstration | Delete a pod backed by a ReplicaSet, observe recreation; cordon/drain a node and observe reschedule |
| 📅 | CKA-F10 | Resource Limits and LimitRanges | Set requests/limits on a Pod, apply a LimitRange to the namespace, watch admission rejections when exceeded |
| 📅 | CKA-F11 | Resource Quotas at Namespace Scope | ResourceQuota for cpu, memory, pods, pvcs; prove rejection of pods that exceed quota |
| 📅 | CKA-F12 | Node Affinity and Anti-Affinity Scheduling | `requiredDuringSchedulingIgnoredDuringExecution` vs preferred; labels on nodes; podAntiAffinity with `topologyKey=kubernetes.io/hostname` |
| 📅 | CKA-F13 | Taints and Tolerations | `kubectl taint node ... NoSchedule`, matching tolerations on workloads, NoExecute eviction and `tolerationSeconds` |
| 📅 | CKA-F14 | Pod Topology Spread Constraints | Spread pods across zones with `maxSkew`, `topologyKey`, `whenUnsatisfiable=DoNotSchedule` |

### Storage

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F15 | Volume Access Modes and Reclaim Policies | RWO vs RWX vs ROX, `persistentVolumeReclaimPolicy` Retain vs Delete vs Recycle, demonstrate each state transition |

### Servicing and Networking

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F16 | Use Gateway API for Ingress Traffic | Install Gateway API CRDs, define a GatewayClass, Gateway, and HTTPRoute, replace a classic Ingress resource |
| 📅 | CKA-F17 | Use CoreDNS for Service Discovery | Inspect kube-system coredns ConfigMap, add a custom stub-domain, validate DNS resolution from a debug pod with `nslookup` |

### Troubleshooting

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKA-F18 | Monitor Cluster with `kubectl top` and Metrics Server | Deploy metrics-server, `kubectl top nodes`, `kubectl top pods --containers`, identify hot pods |
| 📅 | CKA-F19 | Manage Container Output Streams | `kubectl logs --previous`, `--tail`, `--since`, `-f` to follow, sidecar logging patterns |
| 📅 | CKA-F20 | Troubleshoot Services and Networking | `kubectl get endpoints`, validate Service selectors, debug from within the cluster using netshoot or busybox, trace via `iptables -t nat -L KUBE-SERVICES` |

---

## 🎯 CKAD Track (Kubernetes Application Developer)

> All entries below are 📅 Planned.

### Application Design and Build

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-DES-F01 | Build a Container Image from a Dockerfile/Containerfile | Write a Dockerfile FROM `python:3.12-slim`, COPY app.py, CMD `python app.py`; `podman build -t myapp:1.0`, push to local registry, `kubectl run myapp --image=...`, verify with `kubectl describe pod` |
| 📅 | CKAD-DES-F02 | Run a Kubernetes Job (One-Shot Batch Task) | `kind: Job` spec with `completions: 5`, `parallelism: 2`, `backoffLimit: 4`, container command runs to completion; verify with `kubectl get jobs` and `kubectl logs job/myjob` |
| 📅 | CKAD-DES-F03 | Schedule a Kubernetes CronJob | `kind: CronJob` with `schedule: "*/5 * * * *"`, jobTemplate runs `date` and echoes to stdout, prove with `kubectl get cronjob` and `kubectl get jobs --watch` |
| 📅 | CKAD-DES-F04 | Multi-Container Pod: Sidecar Logging Pattern | Main container writes to `/var/log/app.log`; sidecar `busybox` runs `tail -F /var/log/app.log`; shared emptyDir at `/var/log`; verify with `kubectl logs POD -c sidecar` |
| 📅 | CKAD-DES-F05 | Multi-Container Pod: Init Container for Pre-Start Setup | `initContainers` run `wget` to fetch a config file into a shared emptyDir; main container starts only after init succeeds; verify with `kubectl describe pod` |
| 📅 | CKAD-DES-F06 | Persistent Volume + PVC Workflow End-to-End | StorageClass-backed PV or static hostPath PV, PVC with `ReadWriteOnce` + `1Gi`; Pod consumes the claim; write a file; delete Pod; new Pod with same PVC sees the file |
| 📅 | CKAD-DES-F07 | Ephemeral Volume Shared Between Containers (emptyDir) | Pod with two containers + emptyDir volume mounted at `/shared` in both; one writes, the other reads; verify emptyDir does NOT survive Pod deletion |

### Application Deployment

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-DEP-F01 | Canary Deployment with One Service + Two Deployments | Deployment v1 `replicas: 9` + label `version: v1`, Deployment v2 `replicas: 1` + label `version: v2`, Service selector matches only `app: web` so traffic splits ~90/10 |
| 📅 | CKAD-DEP-F02 | Blue-Green Deployment via Service Selector Switch | Two Deployments labelled `color: blue` and `color: green`, Service starts on `color: blue`, deploy green, smoke-test via debug Pod, `kubectl patch svc` to flip selector |
| 📅 | CKAD-DEP-F03 | Deploy an Application via Helm Chart with Custom Values | `helm repo add bitnami`, `helm install myapp bitnami/nginx --set service.type=NodePort,replicaCount=3`, prove with `helm list` + `kubectl get all -l app.kubernetes.io/instance=myapp`; practice `helm upgrade --atomic` + `helm rollback` |

### Application Observability and Maintenance

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-OBS-F01 | Configure Liveness + Readiness + Startup Probes Together | Deployment with three probe types at `/healthz`: livenessProbe httpGet, readinessProbe tcpSocket, startupProbe with `failureThreshold: 30`; break `/healthz` and watch kubelet restart |
| 📅 | CKAD-OBS-F02 | Identify Deprecated API Versions and Migrate Manifests | Run `kubectl api-resources` and `kubectl api-versions`, identify apps using removed APIs like `extensions/v1beta1`, rewrite to current `apps/v1`, validate with `kubectl apply --dry-run=server` |
| 📅 | CKAD-OBS-F03 | Debug a Failing Pod End-to-End | `kubectl get pods` shows CrashLoopBackOff; `kubectl describe pod` for events; `kubectl logs --previous`; `kubectl exec -it POD -- sh`; ephemeral debug via `kubectl debug` for distroless; `kubectl port-forward` to test |

### Application Environment, Configuration, and Security

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-ENV-F01 | Define a Custom Resource Definition and a Custom Resource | `kind: CustomResourceDefinition` with group, names, versions, openAPIV3Schema validation; create a custom resource of that kind; verify with `kubectl get crd` and `kubectl get <kind>` |
| 📅 | CKAD-ENV-F02 | RBAC: Role + RoleBinding for a ServiceAccount | ServiceAccount `read-only`, Role with verbs `[get, list, watch]` on pods, RoleBinding wiring SA to Role; Pod with `serviceAccountName: read-only` can list pods but not create them via `kubectl auth can-i` |
| 📅 | CKAD-ENV-F03 | Pod Resource Requests and Limits (CPU + Memory) | `resources.requests.cpu: 100m`, `requests.memory: 128Mi`, `limits.cpu: 500m`, `limits.memory: 256Mi`; deploy a stress-test Pod that exceeds memory and watch OOMKilled event in `kubectl describe pod` |
| 📅 | CKAD-ENV-F04 | ConfigMap Injection: env vs envFrom vs Volume Mount | One ConfigMap with three keys; demonstrate `env.valueFrom.configMapKeyRef`, `envFrom.configMapRef`, and `volumes.configMap` + `volumeMounts`; show all three patterns in one Pod manifest |
| 📅 | CKAD-ENV-F05 | Secret Patterns: Env Injection vs Mounted File | `kubectl create secret generic db --from-literal=password=s3cret`, inject via `envFrom.secretRef`, also mount at `/etc/db`; observe base64 is decoded at injection; rotate by re-creating Secret and restarting Pod |
| 📅 | CKAD-ENV-F06 | Custom ServiceAccount with Pod Binding | `kubectl create sa myapp-sa`, `kubectl create token myapp-sa`, Pod spec with `serviceAccountName: myapp-sa`, verify projected token at `/var/run/secrets/kubernetes.io/serviceaccount/token` works against the API |
| 📅 | CKAD-ENV-F07 | SecurityContext: runAsUser, fsGroup, Capabilities, ROFS | Pod-level securityContext with `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 2000`, `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`, `capabilities.add: ["NET_BIND_SERVICE"]`; verify with `kubectl exec POD -- id` |

### Services and Networking

| Status | ID | Lab | Details |
|---|---|---|---|
| 📅 | CKAD-NET-F01 | NetworkPolicy: Default-Deny + Allow Specific Ingress | NetworkPolicy with `podSelector: {}` + `policyTypes: [Ingress]` blocks ALL ingress; second NetworkPolicy allows ingress from pods with `role: frontend`; verify with `kubectl exec` and `curl` — requires Calico or Cilium |
| 📅 | CKAD-NET-F02 | Service Types: ClusterIP vs NodePort vs LoadBalancer vs ExternalName | Deploy same backend, expose via four Service types in turn, verify reachability for each: ClusterIP (in-cluster only), NodePort (any node IP:port), LoadBalancer (cloud or MetalLB), ExternalName (DNS alias) |
| 📅 | CKAD-NET-F03 | Ingress with Path-Based Routing and TLS Termination | Deploy NGINX Ingress Controller or Traefik, Ingress with two backends `/api → backend1`, `/web → backend2`, `host: app.example.com`; provision self-signed cert + Secret `kubernetes.io/tls`, attach via `spec.tls`, verify with `curl -k` |

---

## 📈 Summary by Category

### RHCSA EX200 (150 labs)

| Category | ✅ | 🚧 | 📅 | Total |
|---|---:|---:|---:|---:|
| LVM | 2 | 1 | 8 | 11 |
| Storage Management | 0 | 2 | 2 | 4 |
| SELinux | 0 | 1 | 5 | 6 |
| Networking | 0 | 0 | 5 | 5 |
| Package Management | 0 | 1 | 2 | 3 |
| Firewall | 0 | 0 | 2 | 2 |
| Remote Admin & SSH | 0 | 0 | 6 | 6 |
| Web Services (Apache) | 0 | 0 | 5 | 5 |
| User & Group Management | 1 | 0 | 8 | 9 |
| Permissions, ACLs | 0 | 0 | 6 | 6 |
| Sudo & Privilege | 0 | 0 | 3 | 3 |
| NFS & AutoFS | 0 | 0 | 6 | 6 |
| Scheduled Tasks | 1 | 1 | 6 | 8 |
| Essential Tools & Files | 1 | 0 | 7 | 8 |
| Text File Management | 0 | 0 | 3 | 3 |
| Archives & Compression | 0 | 0 | 3 | 3 |
| System Time & Locale | 0 | 0 | 2 | 2 |
| Boot & GRUB | 0 | 0 | 1 | 1 |
| Systemd & Services | 0 | 0 | 1 | 1 |
| System Performance | 0 | 0 | 2 | 2 |
| Containers & Flatpak | 0 | 1 | 13 | 14 |
| Shell Scripting | 0 | 1 | 8 | 9 |
| Process Management | 0 | 0 | 4 | 4 |
| Documentation Tools | 0 | 0 | 1 | 1 |
| Environment & Shell | 0 | 0 | 1 | 1 |

### RHCE EX294 (20 labs)

| Section | 📅 Planned |
|---|---:|
| Foundation (common tasks) | 4 |
| Exam Practice 1 | 3 |
| Exam Practice 2 | 7 |
| Exam Practice 3 | 6 |

### CKA (20 labs)

| Section | 📅 Planned |
|---|---:|
| Cluster Architecture | 5 |
| Workloads & Scheduling | 9 |
| Storage | 1 |
| Servicing & Networking | 2 |
| Troubleshooting | 3 |

### CKAD (22 labs)

| Section | 📅 Planned |
|---|---:|
| Application Design & Build | 7 |
| Application Deployment | 3 |
| Observability & Maintenance | 3 |
| Environment, Config & Security | 7 |
| Services & Networking | 3 |

---

## 🔄 How This Maps Back to the README

The main [README](README.md) is organized by RHCSA EX200 exam objective with globally numbered labs (01, 02, 03...). This roadmap takes the same content and adds three things the README intentionally omits:

1. **Status visibility** — ✅/🚧/📅 lets a visitor see at a glance what's built vs planned, without scrolling.
2. **Future-lab prefixes** — `LVM-F##`, `NET-F##`, etc. are stable identifiers that survive renumbering when labs get built and slotted into the main README's global sequence.
3. **The non-RHCSA tracks** — the README is RHCSA-first; this roadmap surfaces the parallel RHCE / CKA / CKAD curricula so the whole multi-cert arc is visible in one place.

When a 📅 lab becomes a real lab in `labs/<slug>/`, its row in this roadmap is updated to 🚧 (placeholder shipped) or ✅ (full content shipped), and a new row gets added to the main README with the next free global number (e.g. `184`, `185`...).

---

## 👤 Author

**Kelvin R. Tobias**
[kelvinintech.com](https://kelvinintech.com) · [GitHub](https://github.com/kelvintechnical) · [LinkedIn](https://www.linkedin.com/in/kelvin-r-tobias-211949219)
