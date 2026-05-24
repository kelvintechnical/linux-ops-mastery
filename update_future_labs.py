#!/usr/bin/env python3
"""Add Mastering Ansible chapter sections (ch1, ch2, ch7, ch8, ch13) to future_labs.txt.

Each chapter contributes:
- A section banner identifying source and topic
- A bullet list of proposed labs
- A NAVIGATE-AND-DISCOVER REMINDER comment explaining how the verbatim Q&A
  below it will be transformed when the labs are actually built
- The verbatim multiple-choice questions copied from the chapter

Also updates the source list, adds an Updated timestamp, and rebuilds
SUMMARY COUNTS so the lab total reflects the new bullet count.
All file I/O uses explicit UTF-8 so em-dashes survive.
"""
import re
from pathlib import Path

DEST = Path("future_labs.txt")

NAVIGATE_COMMENT = """
*** NAVIGATE-AND-DISCOVER REMINDER (see INTENT block at top of file) ***
The verbatim multiple-choice questions below are kept here as REFERENCE
ONLY. When the corresponding labs above are actually built, these
questions MUST be rewritten in template.txt-style navigate-and-discover
form (open-ended prompt + hint commands like `ansible-doc`, `man`,
`find`, `grep`, `journalctl`, `<cmd> --help`). The a/b/c/d options below
are the source-of-truth answer key for the lab author, not the final
question format the learner should see.
***********************************************************************
"""


CH1_SECTION = """================================================================
MASTERING ANSIBLE  Ch 1  —  System Architecture & Design (from ch1.txt)
================================================================

----------------------------------------------------------------
🗂  INVENTORY ARCHITECTURE  —  from ch1.txt
----------------------------------------------------------------

- Static INI Inventory with Groups, Children, and Group-Vars
    (mastery-hosts file with [web], [dns], [database],
     [frontend:children]→web, [backend:children]→dns+database,
     plus [web:vars] / [backend:vars] / [all:vars]; prove
     ansible-inventory -i mastery-hosts --graph reflects the
     full hierarchy)

- Behavioral Inventory Variables Cheat-Sheet Playbook
    (one playbook that overrides ansible_host, ansible_port,
     ansible_user, ansible_ssh_private_key_file,
     ansible_connection, ansible_python_interpreter,
     ansible_become_method per host and prints each value back
     with `ansible.builtin.debug var=hostvars[...]`)

- Inventory Ordering: inventory / reverse_inventory / sorted /
  reverse_sorted / shuffle
    (one play, five runs, prove with debug task that
     play-level `order:` keyword controls host processing
     order — include the lexicographical mastery1 / mastery11
     / mastery2 gotcha example)

- AWS EC2 Dynamic Inventory Plugin Bring-Up
    (install amazon.aws collection via ansible-galaxy,
     install python3-boto3/botocore, configure `aws configure`
     default profile, write mastery_aws_ec2.yml with
     plugin: amazon.aws.aws_ec2 + boto_profile: default,
     verify with `ansible-inventory -i mastery_aws_ec2.yml --graph`)

- Runtime Inventory Additions with `ansible.builtin.add_host`
    (one playbook: provision a fake "new cloud node" then
     `add_host name=newmastery.example.name groups=web
     ansible_host=192.168.10.30` and immediately run a task
     against the new host inside the same play)

- Inventory Limiting with `--limit` + Cross-Host hostvars Access
    (run mastery.yaml with `--limit frontend` and prove a task
     can still read `hostvars['backend.example.name']
     ['ansible_port']` even though backend is masked out)

- YAML vs INI Inventory Equivalence Audit
    (convert the same [web]/[dns]/[database]/[frontend:children]
     /[backend:children] INI inventory to a single YAML
     inventory file and diff the `ansible-inventory --list`
     output to prove they parse identically)

- Static + Dynamic Inventory Combined (Directory-Based Inventory)
    (point `-i inventory/` at a directory containing both a
     static `mastery-hosts` file and the `mastery_aws_ec2.yml`
     plugin config; prove both sources merge into one inventory
     with `ansible-inventory -i inventory/ --graph`)

----------------------------------------------------------------
🎬  PLAYBOOK PARSING & EXECUTION ORDER  —  from ch1.txt
----------------------------------------------------------------

- Strict Play Order: pre_tasks → roles → tasks → post_tasks → handlers
    (build the example play from the chapter with all four
     blocks in scrambled YAML order; prove output order
     matches the documented execution order, not file order)

- Handler Flushing with `meta: flush_handlers`
    (config-file change task notifies "restart svc" handler;
     prove that without `meta: flush_handlers`, a later
     "ensure service running" task can start a service that
     the handler then immediately restarts — fix it by
     flushing handlers between the two tasks)

- Relative Path Resolution for vars_files and include
    (recreate the chapter's directory tree:
     a_vars_file.yaml / mastery-hosts / relative.yaml /
     tasks/a.yaml / tasks/b.yaml; prove paths are relative
     to the file that references them, not to the playbook
     root)

- Linear vs Free vs Debug Execution Strategies
    (same play, 3 runs, `strategy: linear` then `free` then
     `debug`; with `serial: 2` and an artificial `pause`
     task on host1, prove free lets host2 race ahead, linear
     forces lockstep, and debug drops into an interactive
     prompt on failure)

- Host Pattern Selection: groups, wildcards, regex, &, !
    (one ad-hoc command per pattern; prove
     `webservers:&dbservers` is intersection,
     `webservers:!dbservers` is exclusion, and
     `~(web|db)\\.example\\.com` is regex matching)

- Play and Task Names with Variables — When Templating Works
    (build the chapter's names.yaml example with `var_name`
     defined in play vars, `task_var_name` defined via
     set_fact, and `runtime_var_name` undefined; prove only
     play-vars render in the visible name, set_fact-defined
     names appear raw in output)

----------------------------------------------------------------
🔢  VARIABLE PRECEDENCE & MAGIC VARIABLES  —  from ch1.txt
----------------------------------------------------------------

- Variable Precedence Pyramid: prove all 21 levels
    (single playbook with the same variable defined in
     extra-vars, set_fact, include_vars, task vars, block
     vars, role vars, vars_files, vars_prompt, host_vars,
     group_vars, role defaults, and inventory; prove
     extra-vars wins, role defaults always lose)

- Magic Variables Tour: inventory_hostname / group_names /
  hostvars / play_hosts / ansible_play_batch
    (one ad-hoc playbook prints each magic variable for
     every host; prove what's defined at parse time vs
     execution time)

- `ansible_group_priority` for Conflict Resolution
    (build the chapter's two-group conflict: host in both
     `web` (http_port=80) and `proxy` (http_port=8080);
     show alphabetical sort makes `web` win, then add
     `ansible_group_priority=10` to `proxy:vars` and prove
     proxy now wins)

- Hash Merge vs Replace via `hash_behavior`
    (set hash_var.fred = {home: Seattle, transport: Bicycle}
     in group_vars, then load `transport: Bus` via
     include_vars; prove default replace mode drops `home`
     but `hash_behavior=merge` in ansible.cfg keeps it)

- Lookup Plugins: file / env / pipe / password / dnstxt
    (one debug task per plugin; prove `lookup('file', ...)`,
     `lookup('env', 'HOME')`, `lookup('pipe', 'date')`,
     `lookup('password', '/tmp/p length=16')`, and
     `lookup('dig', 'example.com')` each return live data
     evaluated at task time)

- vars_prompt for Interactive Variable Capture
    (play prompts for a name + password (private: yes,
     encrypt: sha512), captures the answer into a variable,
     and uses it in a later task)

----------------------------------------------------------------
⚡  MODULE TRANSPORT, PERFORMANCE & SAFETY  —  from ch1.txt
----------------------------------------------------------------

- SSH ControlPersist + Pipelining Performance Benchmark
    (run a 50-task playbook against 5 hosts twice: once
     with default settings, once with `pipelining=true` in
     `[ssh_connection]` and ControlPersist enabled in
     ~/.ssh/config; capture wall-clock time and prove the
     speedup)

- Ansible Forks Tuning
    (run a long playbook across 20 hosts with
     `forks=5` (default) then `forks=20`; capture
     before/after duration with `time`; compare the
     parallelism difference visually with `--forks`)

- Module Discovery Path Order (role library → playbook
  library → ANSIBLE_LIBRARY → /usr/share/ansible)
    (place a custom `debug` module shadow at each level in
     turn and prove which one wins; demonstrate why FQCN
     usage protects you from shadowing accidents)

- Module Blacklisting with plugin_filters.yml
    (set `plugin_filters_cfg=/etc/ansible/plugin_filters.yml`
     in ansible.cfg, write a `module_blacklist: [debug]`
     entry, prove a playbook using `ansible.builtin.debug`
     now fails until the blacklist is removed)

- Module Argument Formats: free-form vs key=value vs YAML hash
    (one playbook with the same `ansible.builtin.user`
     module called three different ways; prove all three
     produce identical results but only the YAML hash
     supports passing complex/nested arguments)
""" + NAVIGATE_COMMENT + """
Verbatim Questions from ch1.txt (Mastering Ansible 4th Ed.):

  1. Why is an inventory important to Ansible?
     a) It forms part of Ansible's configuration management database.
     b) It is used to audit your servers.
     c) It tells Ansible which servers to perform automation tasks on.
     d) None of the above.

  2. When working with frequently changing infrastructures (such as
     public cloud deployments), Ansible users must manually update
     their inventory on a regular basis. Is this true or false?
     a) True – this is the only way to do it.
     b) False – dynamic inventories were invented for precisely this
        purpose.

  3. By default, Ansible processes hosts in an inventory in which
     order?
     a) In alphabetical order
     b) In lexicographical order
     c) In random order
     d) In the order in which they appear in the inventory

  4. By default, Ansible tasks in a simple playbook are executed in
     which order?
     a) In the order in which they are written, but each task must
        be completed on all inventory hosts before the next is
        executed.
     b) In the most optimal order.
     c) In the order in which they are written but only on one
        inventory host at a time.
     d) Something else.

  5. Which variable type takes the highest priority, overriding all
     other variable sources?
     a) Inventory variables
     b) Extra variables (from the command line)
     c) Role defaults
     d) Variables source via vars_prompt

  6. What is the name of the special Ansible variables that only
     exist at runtime?
     a) Special variables
     b) Runtime variables
     c) Magic variables
     d) User variables

  7. If you wanted to access external data from a playbook, what
     would you use?
     a) A lookup plugin
     b) A lookup module
     c) A lookup executable
     d) A lookup role

  8. What is Ansible's preferred default transport mechanism for
     most non-Windows hosts?
     a) The REST API
     b) RabbitMQ
     c) RSH
     d) SSH

  9. What can inventory variables be used to do?
     a) Define unique data for each host or group of hosts in an
        inventory.
     b) Declare your playbook variables.
     c) Define connection parameters for your inventory hosts.
     d) Both (a) and (c).

 10. How can you override the default Ansible configuration on your
     system?
     a) By creating an Ansible configuration file in any location,
        and using the ANSIBLE_CFG environment variable to specify
        this location.
     b) By creating a file called ansible.cfg in the current working
        directory.
     c) By creating a file in your home directory called
        ~/.ansible.cfg.
     d) Any of the above.


"""


CH2_SECTION = """================================================================
MASTERING ANSIBLE  Ch 2  —  Migration / Collections / FQCNs (from ch2.txt)
================================================================

----------------------------------------------------------------
📦  ANSIBLE COLLECTIONS & FQCNs  —  from ch2.txt
----------------------------------------------------------------

- Clean Reinstall: Remove Ansible 2.9 / 3.x, Install Ansible 4.3
    (uninstall via dnf/apt/pip depending on prior install
     method, install 4.3 from pip into a sandbox; prove
     `ansible --version` reports ansible-core 2.11.x)

- Pip + virtualenv: Two Side-by-Side Ansible Versions
    (create `ansible-2.9` and `ansible-4.3` virtualenvs,
     install pinned versions in each via
     `pip install 'ansible>=2.9,<2.10'` etc., switch between
     them with `source <env>/bin/activate`, prove version
     swap with `ansible --version`)

- Build Your First Custom Collection (`masterybook.demo`)
    (`ansible-galaxy collection init masterybook.demo`,
     populate galaxy.yml, drop a custom module into
     plugins/modules/remote_copy.py, run
     `ansible-galaxy collection build` to produce the
     `.tar.gz` artifact)

- Install Your Custom Collection Locally via `collections_paths`
    (create an ansible.cfg in a test dir with
     `collections_paths=./collections:~/.ansible/collections:
     /usr/share/ansible/collections`, install the tarball
     with `ansible-galaxy collection install
     ~/masterybook/demo/masterybook-demo-1.0.0.tar.gz
     -p ./collections`, run a playbook that calls it via
     FQCN)

- FQCN vs Short Module Names — Shadowing Demo
    (write a custom collection containing a module called
     `pause` that does something destructive; prove that
     calling `pause` resolves to `ansible.builtin.pause`
     not your version, then prove that adding
     `collections: [masterybook.demo]` at play level flips
     the priority)

- Collection Installation from Git URL
    (`ansible-galaxy collection install
     git+https://github.com/user/repo.git,branchname`,
     verify with `ansible-galaxy collection list`, run a
     playbook that uses a module from the freshly cloned
     collection)

- Bulk Collection Install via requirements.yml
    (write a `requirements.yml` listing
     `geerlingguy.k8s` (latest) + `geerlingguy.php_roles`
     (pinned to 1.0.0); install all with
     `ansible-galaxy install -r requirements.yml`; prove
     each was installed at the requested version)

- Semantic Versioning Walk-Through for Ansible Packages
    (install 4.0.0 then 4.3.0 then jump to a hypothetical
     5.0.0; document which jumps are backward-compatible
     vs breaking and what the ansible-core dependency
     pinning means for each)

- Discover All Modules in a Collection via `ansible-doc -l`
    (run `ansible-doc -l cisco.ios`, `-l community.aws`,
     `-l amazon.aws`; capture into a markdown table that
     becomes the cheat-sheet for the project)

- Force-Install a Pre-Release / Dev Collection Version
    (`ansible-galaxy collection install
     amazon.aws:==1.4.2-dev9 --force`, prove the dev
     version installs over the released one, then revert
     with another `--force` to the stable channel)

- Publish a Collection to Ansible Galaxy
    (create Galaxy account via GitHub login, copy API key,
     run `ansible-galaxy collection publish
     masterybook-demo-1.0.0.tar.gz --token=<key>`, verify
     it appears at galaxy.ansible.com/masterybook/demo)
""" + NAVIGATE_COMMENT + """
Verbatim Questions from ch2.txt (Mastering Ansible 4th Ed.):

  1. Collections can contain:
     a) Roles
     b) Modules
     c) Plugins
     d) All of the above

  2. Collections mean that Ansible Module versioning is independent
     of the version of the Ansible engine.
     a) True
     b) False

  3. The Ansible 4.3 package:
     a) includes the Ansible automation engine.
     b) has a dependency on the Ansible automation engine.
     c) bears no relation to the Ansible automation engine.

  4. It is possible to upgrade directly from Ansible 2.9 to Ansible
     4.3.
     a) True
     b) False

  5. In Ansible 4.3, module names are guaranteed to be unique
     between different namespaces.
     a) True
     b) False

  6. To ensure that you always access the correct module you intend,
     you should start using which of the following now in your
     tasks?
     a) Fully Qualified Domain Names
     b) Short form module names
     c) Fully Qualified Collection Names
     d) None of the above

  7. Which file can be used to list all the required Collections
     from Ansible Galaxy, ensuring they can easily be installed
     when needed?
     a) site.yml
     b) ansible.cfg
     c) collections.yml
     d) requirements.yml

  8. When you create an account on Ansible Galaxy for the purposes
     of contributing your own Collections, your namespace is:
     a) randomly generated.
     b) chosen by you.
     c) automatically generated based on your GitHub user ID.

  9. Collections are stored in which common file format?
     a) .tar.gz
     b) .zip
     c) .rar
     d) .rpm

 10. How could you list all the Collections installed with your
     Ansible package?
     a) ansible --list-collections
     b) ansible-doc -l
     c) ansible-galaxy --list-collections
     d) ansible-galaxy collections list


"""


CH7_SECTION = """================================================================
MASTERING ANSIBLE  Ch 7  —  Task Conditions, Error Recovery, Loops (from ch7.txt)
================================================================

----------------------------------------------------------------
🎛  TASK CONDITIONS, ERROR RECOVERY & LOOPS  —  from ch7.txt
----------------------------------------------------------------

- `ignore_errors: true` on a Deliberately-Failing URI Task
    (`ansible.builtin.uri` against `http://notahost.nodomain`;
     prove the play normally aborts the host, then add
     `ignore_errors: true` and prove subsequent tasks on
     that host continue to run)

- `failed_when` for iscsiadm Exit Code Tolerance
    (run `/sbin/iscsiadm -m session`, register output, set
     `failed_when: sessions.rc not in (0, 21)`; prove
     `failed_when_result: false` appears in the verbose
     output even when rc=21)

- Multi-Condition `failed_when` as YAML List (Git Branch Delete)
    (`git branch -D badfeature` in /srv/app, register the
     result, fail only when rc != 0 AND stderr doesn't
     match `branch.*not found`; demonstrate that YAML-list
     conditions implicitly AND together)

- `changed_when` to Suppress False-Positive Changes
    (combine `failed_when` + `changed_when: gitout.rc == 0`
     on the git-branch-delete task; prove that a no-op run
     shows `changed: false` and a real delete shows
     `changed: true`)

- `creates` / `removes` for Command-Family Idempotency
    (write a frobitz shell script that creates
     /srv/whiskey/tango; replace the old stat + when
     two-task combo with a single `ansible.builtin.script`
     task using `args: creates: /srv/whiskey/tango`;
     prove second run skips entirely)

- Pure Data-Gathering Tasks with `changed_when: false`
    (iscsiadm session-discovery task with combined
     failed_when + `changed_when: false`; prove the task
     can only be `ok` or `failed`, never `changed`)

- `block` + `rescue` for Graceful Cleanup
    (block runs a `git branch -D badfeature` task that
     fails; rescue logs the failure to /tmp/cleanup.log
     and runs `git reset --hard`; prove the post-block
     "task after block" still executes)

- `block` + `rescue` + `always` (Three-Section Block)
    (rescue runs cleanup tasks, always runs a notification
     task; verify always executes whether or not block
     failed, by running the playbook with the failure
     condition both met and not met)

- `ignore_unreachable: true` Against an Inventory of Dead Hosts
    (inventory with 2 fake hosts that DNS-resolve to
     unreachable IPs; prove the play normally aborts at
     task 1 but with `ignore_unreachable: true` task 2 is
     still attempted)

- Modern `loop:` vs Legacy `with_items:` Equivalence
    (same playbook written both ways to create
     /srv/whiskey/alpha and /srv/whiskey/beta; prove they
     produce identical output and prove `with_items` still
     works but emits a deprecation warning in modern
     Ansible)

- `until` / `retries` / `delay` Loop Waiting for /tmp/flag
    (task uses `ansible.builtin.stat` registered to
     `statresult` with
     `until: statresult.stat.exists`,
     `retries: 5`, `delay: 10`; prove the play polls every
     10s, gives up after 5 attempts, then succeeds when
     the flag is touched mid-loop from another shell)

- Nested Loops with `product` Filter and `loop_control.loop_var`
    (paths=[/tmp, /var/tmp] x files=[test1, test2]; first
     write it inline using
     `loop: "{{ paths | product(files) | list }}"`, then
     refactor to `include_tasks: createfile.yml` with
     `loop_control: loop_var: pathname`; prove both produce
     identical files but show the readability tradeoff)
""" + NAVIGATE_COMMENT + """
Verbatim Questions from ch7.txt (Mastering Ansible 4th Ed.):

  1. By default, Ansible will stop processing further tasks for a
     given host after the first failure occurs:
     a) True
     b) False

  2. The ansible.builtin.command and ansible.builtin.shell modules'
     default behavior is to only ever give a task status of changed
     or failed:
     a) True
     b) False

  3. You can store the results from a task using which Ansible
     keyword?
     a) store:
     b) variable:
     c) register:
     d) save:

  4. Which of the following directives can be used to change the
     failure condition of a task?
     a) error_if:
     b) failed_if:
     c) error_when:
     d) failed_when:

  5. You can combine multiple conditional statements in Ansible
     using which of the following?
     a) and
     b) or
     c) The YAML list format (which works the same as a logical
        AND)
     d) All of the above

  6. Changes can be suppressed with which of the following?
     a) suppress_changed: true
     b) changed_when: false
     c) changed: false
     d) failed_when: false

  7. In a block section, all tasks are executed in order on all
     hosts:
     a) Until the first error occurs
     b) Regardless of any error condition

  8. Which optional section of a block gets run only if an error
     occurs in the block tasks?
     a) recover
     b) rescue
     c) always
     d) on_error

  9. Tasks in the always section of a block are run:
     a) Regardless of what happened in either the block tasks or
        the rescue section
     b) Only if the rescue section did not get run
     c) Only if no errors were encountered
     d) When called manually by the user

 10. The default name of the variable referencing the current
     element of a loop is:
     a) loopvar
     b) loopitem
     c) item
     d) val


"""


CH8_SECTION = """================================================================
MASTERING ANSIBLE  Ch 8  —  Roles, Includes & ansible-galaxy (from ch8.txt)
================================================================

----------------------------------------------------------------
🧱  ROLES, INCLUDES & ANSIBLE-GALAXY  —  from ch8.txt
----------------------------------------------------------------

- Basic Task Inclusion with `ansible.builtin.include`
    (write includer.yaml that runs one inline task then
     includes more-tasks.yaml containing two debug tasks;
     add a third task after the include and prove
     execution order is inline → included-1 → included-2 →
     after)

- Passing Variables Inline to Included Tasks
    (files.yaml takes `path` + `file` variables and runs
     two `ansible.builtin.file` tasks (mkdir + touch);
     include it twice with different vars in the same play
     to create /tmp/foo/herp and /tmp/foo/derp from one
     reusable file)

- Passing Complex Hash Data to Included Tasks via dict2items
    (refactor the above to pass `files: {herp: {path:
     /tmp/foo}, derp: {path: /tmp/foo}}` in a single
     include, loop over `files | dict2items` inside the
     included file; prove one include creates both files)

- Conditional Include with `when: item | bool`
    (more-tasks.yaml iterates over `a_list: [true, false]`;
     include with `when: item | bool` to skip the false
     iteration of every task inside the included file;
     prove every task gets the conditional, not just the
     include itself)

- Tagged Task Includes for Selective Execution
    (include more-tasks.yaml twice, once with `tags: first`
     and `vars: {data: first}`, once with `tags: second`
     and `vars: {data: second}`; run with
     `--tags second` and prove only the second include
     executes)

- Looping Over a Task Include with `loop_control: loop_var`
    (outer loop uses `loop: [one, two]` +
     `loop_control: loop_var: include_item`; inner task
     loops over `[a, b]` using `item`; prove no variable
     collision and 4 total executions per inclusion loop)

- Handler Inclusion with `when` on the Include Statement
    (handler block uses `include: handlers.yaml when: foo
     | default('true') | bool`; trigger with `-e foo=false`
     and prove the handler is skipped entirely)

- `vars_files` Static Inclusion vs `include_vars` Dynamic Inclusion
    (one play with `vars_files: [variables.yaml]` (parsed
     at play parse time) vs another play that calls
     `ansible.builtin.include_vars: "{{ varfile }}"` as a
     task (evaluated at task time); prove the dynamic
     version can use a variable defined by a previous task)

- `include_vars` with `with_first_found` for OS-Specific Vars
    (try `{{ ansible_distribution }}.yaml`,
     `{{ ansible_os_family }}.yaml`, then `variables.yaml`
     as a fallback chain; prove on Ubuntu vs RHEL the right
     distro-specific file is picked first)

- Loading Extra Vars from a File via `-e @file.yaml`
    (run `ansible-playbook -e @variables.yaml` and prove
     that the variables defined in variables.yaml become
     extra-vars even though the file is never referenced
     inside the playbook itself)

- `import_playbook` for Composing Multi-Playbook Workflows
    (master playbook with two `import_playbook` directives
     pulling in installme.yaml + configureme.yaml; prove
     each child playbook is fully run in order, and prove
     `import_playbook` cannot take `vars:` or `when:`)

- Build a Role From Scratch with `ansible-galaxy role init`
    (`ansible-galaxy role init --init-path roles/
     simple`; populate roles/simple/defaults/main.yaml with
     `derp: herp`, roles/simple/tasks/main.yaml with a
     debug task printing `var: derp`; consume from a
     roleplay.yaml that overrides with `derp: newval`)

- Role Dependencies with Variables + Tags + Conditionals
    (roles/apache/meta/main.yaml declares
     `dependencies: [{role: common, simple_var_a: true,
     tags: common_demo}, {role: apache, complex_var:
     {key1: value1}, when: backend_server == 'apache',
     tags: [apache_demo, 8080]}]`; prove dependencies run
     before apache itself)

- pre_tasks / roles / tasks / post_tasks Handler-Flush Ordering
    (single playbook with all four sections, each task
     notifies the same `say hi` handler with `changed_when:
     true`; prove the handler fires exactly 3 times — once
     after pre_tasks, once after roles+tasks, once after
     post_tasks)

- Install Roles from Ansible Galaxy + Git + tarball + requirements.yml
    (`ansible-galaxy role install -p roles/
     angstwad.docker_ubuntu` from Galaxy; then install a
     private role with `git+git@server:repo,v1,renamed`
     syntax; then bulk-install via `ansible-galaxy install
     -r requirements.yml`; verify each with
     `ansible-galaxy role list -p roles/`)
""" + NAVIGATE_COMMENT + """
Verbatim Questions from ch8.txt (Mastering Ansible 4th Ed.):

  1. Which Ansible module can be used to run tasks from a separate
     external task file when a playbook is run?
     a) ansible.builtin.import
     b) ansible.builtin.include
     c) ansible.builtin.tasks_file
     d) ansible.builtin.with_tasks

  2. Variable data can be passed to an external task file when it
     is called:
     a) True
     b) False

  3. The default name of the variable containing the current loop
     value is:
     a) i
     b) loop_var
     c) loop_value
     d) item

  4. When looping over external task files, it is important to
     consider setting which special variable to prevent loop
     variable name collisions?
     a) loop_name
     b) loop_item
     c) loop_var
     d) item

  5. Handlers are generally run:
     a) Once, at the end of the play
     b) Once each, at the end of the pre_tasks, roles/tasks, and
        post_tasks sections of the play
     c) Once each, at the end of the pre_tasks, roles/tasks, and
        post_tasks sections of the play and only when notified
     d) Once each, at the end of the pre_tasks, roles/tasks, and
        post_tasks sections of the play and only when imported

  6. Ansible can load variables from the following external
     sources:
     a) Static vars_files inclusion
     b) Dynamic vars_files inclusion
     c) Through the include_vars statement
     d) Through the extra-vars command-line parameter
     e) All of the above

  7. Roles obtain their name from the role directory name (for
     example, roles/testrole1 has the name testrole1):
     a) True
     b) False

  8. If a role is missing the tasks/main.yml file, Ansible will:
     a) Abort the play with an error
     b) Skip the role entirely
     c) Still reference any other valid parts of the role,
        including metadata, default variables, and handlers
     d) Display a warning

  9. Roles can have dependencies on other roles:
     a) True
     b) False

 10. When you specify a tag for a role, Ansible's behavior is to:
     a) Apply the tag to the entire role
     b) Apply the tag to each task within the role
     c) Skip the role entirely
     d) Only execute tasks from a role with the same tag


"""


CH13_SECTION = """================================================================
MASTERING ANSIBLE  Ch 13  —  Network Automation (from ch13.txt)
================================================================

----------------------------------------------------------------
🌐  NETWORK AUTOMATION — SWITCHES, ROUTERS, JUMP HOSTS  —  from ch13.txt
----------------------------------------------------------------

- Choosing the Right Connection Protocol: local vs network_cli
  vs netconf vs httpapi
    (decision matrix for 4 device types: Cisco IOS,
     Arista EOS, F5 BIG-IP, Cumulus Linux; pick the right
     `ansible_connection` value for each and document why
     `connection: local` is being deprecated)

- Inventory for Cisco IOS via `ansible.netcommon.network_cli`
    (build `[ios_devices]` group with
     `ansible_connection: ansible.netcommon.network_cli`,
     `ansible_network_os: cisco.ios.ios`,
     `ansible_become: yes`,
     `ansible_become_method: enable`; verify with
     `cisco.ios.ios_facts`)

- Save Running Config on Cisco IOS with `cisco.ios.ios_config`
    (playbook task `cisco.ios.ios_config: save_when:
     always` against the ios_devices group; prove it's
     idempotent across multiple runs)

- Bring Up an Arista vEOS Switch from Zero
    (cancel ZeroTouch with `zerotouch cancel`, set admin
     password, configure `interface management 1` with
     IP via `ip address 10.0.50.99/8`, `write` the
     config; prove SSH connectivity from the Ansible
     control node)

- Configure Arista EOS Interfaces with `arista.eos.eos_interfaces`
    (enable Ethernet1, set `description: Managed by
     Ansible`, then `arista.eos.eos_config: save_when:
     modified`; prove second run is fully idempotent
     showing `ok` not `changed`)

- Configure Cumulus Linux Layer-2 Bridge with
  `community.network.nclu`
    (switch-l2-configure.yaml uses inline Jinja2 for-loop
     across swp1..swp3: `add interface swp{i}` +
     `add bridge ports swp{i}` + `commit: true`; verify
     `swp1` joins the default bridge with a follow-up
     `show interface swp1` query)

- Multi-Vendor Inventory with `[switches:children]` Grouping
    (one inventory containing both `[eos]` and `[cumulus]`
     groups under `[switches:children]`; build a single
     playbook that gates Cumulus-only tasks behind
     `when: inventory_hostname in groups['cumulus']`)

- Conditional Fact-Gathering for Different Network OSes
    (one play with two fact tasks:
     `arista.eos.eos_facts` when
     `ansible_network_os is defined and == 'arista.eos.eos'`,
     and `ansible.builtin.setup` when in `groups['cumulus']`;
     prove both fact sets populate cleanly without
     undefined-variable errors)

- Jump Host / Bastion via `ansible_ssh_common_args` ProxyCommand
    (set `ansible_ssh_common_args='-o
     ProxyCommand="ssh -W %h:%p -q
     jfreeman@bastion01.example.com"'` in
     `[cumulus:vars]`, prove the playbook still runs
     unchanged against switches that live behind the
     bastion)

- Raw-Command Fallback for Unsupported Devices via
  `ansible.builtin.raw`
    (TP-Link or other unmanaged switch with only SSH CLI;
     wrap CLI commands in `ansible.builtin.raw` calls,
     accept loss of idempotency, document this as a
     "stepping stone to a proper module" pattern)
""" + NAVIGATE_COMMENT + """
Verbatim Questions from ch13.txt (Mastering Ansible 4th Ed.):

  1. Ansible brings all the benefits of automation from
     infrastructure management to the world of network device
     management.
     a) True
     b) False

  2. When working with a new network device type for the first
     time, you should always do what?
     a) Perform a factory reset of the device.
     b) Consult the Ansible documentation to learn about which
        collections and modules support it, and what the
        requirements for those might be.
     c) Use the ansible.netcommon.network_cli connection protocol.
     d) Use the local connection protocol.

  3. Which execution type is described by Ansible as running its
     automation code on the remote host directly?
     a) Remote execution
     b) Local execution

  4. Which execution type is described by Ansible as running its
     automation code on the control node, and then sending the
     required data over a pre-selected channel (for example, SSH or
     an HTTP-based API)?
     a) Remote execution
     b) Local execution

  5. Which connection protocol has (for the most part) superseded
     the older local connection-based protocol for network devices?
     a) ansible.netcommon.netconf
     b) ansible.netcommon.httpapi
     c) ansible.netcommon.network_cli
     d) local

  6. Can you gather facts for an Arista-based EOS device at the
     beginning of a play?
     a) Yes.
     b) No.
     c) Yes, but only when using the ansible.netcommon.network_cli
        protocol.

  7. All network config on Arista EOS is performed using a single
     module.
     a) True
     b) False

  8. Cumulus Linux does not require the ansible.netcommon.network_cli
     protocol because of which reason?
     a) It is not a network operating system.
     b) It contains a full Linux implementation, including Python.
     c) It uses the SSH protocol for management.
     d) It does not have a CLI.

  9. Good inventory management is especially important when working
     in multi-device-type networks.
     a) True
     b) False

 10. Ansible can support the use of bastion or jump hosts without
     the need for special configuration or software installation.
     a) True
     b) False


"""


NEW_SOURCES = """  - ch1.txt                                (Mastering Ansible, 4th Ed. — Chapter 1:
                                            The System Architecture and Design
                                            of Ansible)
  - ch2.txt                                (Mastering Ansible, 4th Ed. — Chapter 2:
                                            Migrating from Earlier Ansible
                                            Versions / Collections & FQCNs)
  - ch7.txt                                (Mastering Ansible, 4th Ed. — Chapter 7:
                                            Controlling Task Conditions —
                                            failed_when, changed_when, block/
                                            rescue/always, loops)
  - ch8.txt                                (Mastering Ansible, 4th Ed. — Chapter 8:
                                            Composing Reusable Ansible Content
                                            with Roles — includes, role structure,
                                            dependencies, ansible-galaxy)
  - ch13.txt                               (Mastering Ansible, 4th Ed. — Chapter 13:
                                            Network Automation — network_cli,
                                            Arista EOS, Cumulus Linux, jump hosts,
                                            ansible_network_os)
"""


NEW_TIMESTAMP = """Updated:        2026-05-23 (rebuilt Mastering Ansible sections from
                            ch1.txt, ch2.txt, ch7.txt, ch8.txt, ch13.txt;
                            each chapter now contributes labs PLUS the
                            verbatim multiple-choice question block from
                            the chapter, with a NAVIGATE-AND-DISCOVER
                            REMINDER comment between the labs and the
                            questions so any future contributor knows the
                            a/b/c/d format is reference-only and must be
                            rewritten into template.txt-style discovery
                            prompts when the lab is actually built)
"""


def insert_after_marker(text: str, marker: str, insertion: str) -> str:
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit(f"marker not found: {marker!r}")
    insert_at = idx + len(marker)
    return text[:insert_at] + insertion + text[insert_at:]


def main():
    text = DEST.read_text(encoding="utf-8")

    # 1. Add new sources after the PerfectScorerPracticeExams.txt line
    sources_anchor = "                                            mock exams across Node1 + Node2)\n"
    if "  - ch1.txt" not in text:
        text = insert_after_marker(text, sources_anchor, NEW_SOURCES)

    # 2. Add a new Updated timestamp at the end of the timestamps block
    last_ts_marker = "FOR FUTURE LABS appendix)\n"
    if "rebuilt Mastering Ansible sections" not in text:
        text = insert_after_marker(text, last_ts_marker, "\n" + NEW_TIMESTAMP)

    # 3. Insert the five chapter sections immediately before SUMMARY COUNTS
    summary_header = "----------------------------------------------------------------\nSUMMARY COUNTS\n----------------------------------------------------------------"
    chapters_block = (
        "\n\n"
        + CH1_SECTION
        + "\n"
        + CH2_SECTION
        + "\n"
        + CH7_SECTION
        + "\n"
        + CH8_SECTION
        + "\n"
        + CH13_SECTION
        + "\n"
    )
    if "MASTERING ANSIBLE  Ch 1" not in text:
        text = text.replace(summary_header, chapters_block + summary_header, 1)

    # 4. Rebuild SUMMARY COUNTS using authoritative bullet counts
    chapter_counts = {
        "ch1": CH1_SECTION.count("\n- "),
        "ch2": CH2_SECTION.count("\n- "),
        "ch7": CH7_SECTION.count("\n- "),
        "ch8": CH8_SECTION.count("\n- "),
        "ch13": CH13_SECTION.count("\n- "),
    }
    ma_total = sum(chapter_counts.values())

    # Count the surviving non-MA sections by scanning the file BEFORE the
    # first MASTERING ANSIBLE header line.
    pre_ma = text.split("MASTERING ANSIBLE  Ch 1")[0]
    section_patterns = [
        ("RHCSA  (from samplerhcsa2.txt)", "from samplerhcsa2"),
        ("RHCSA  (from samplerhcsa3 + 4.txt)", "from samplerhcsa3"),
        ("RHCE   (from rhcsasample.txt)", "from rhcsasample"),
        ("CKA    (from ckaexamguide.txt)", "from ckaexamguide"),
        ("RHCSA 9 & 10 (PerfectScorerPracticeExams)", "PerfectScorerPracticeExams"),
        ("CKAD   (from ckadstudyguide.txt)", "from ckadstudyguide"),
    ]
    pre_ma_lines = pre_ma.splitlines(keepends=True)

    section_indices = []
    for label, needle in section_patterns:
        for i, line in enumerate(pre_ma_lines):
            # Real section headers contain an em-dash; this excludes the
            # indented source list at the top and the Updated: timestamp
            # lines which also happen to mention the source filenames.
            if needle in line and "\u2014" in line and not line[0].isspace():
                section_indices.append((label, i))
                break

    section_indices.sort(key=lambda x: x[1])
    non_ma_counts = {label: 0 for label, _ in section_patterns}
    for idx, (label, start) in enumerate(section_indices):
        end = section_indices[idx + 1][1] if idx + 1 < len(section_indices) else len(pre_ma_lines)
        non_ma_counts[label] = sum(1 for line in pre_ma_lines[start:end] if line.startswith("- "))

    total = sum(non_ma_counts.values()) + ma_total

    new_summary = f"""----------------------------------------------------------------
SUMMARY COUNTS
----------------------------------------------------------------

  RHCSA  (from samplerhcsa2.txt)             : {non_ma_counts['RHCSA  (from samplerhcsa2.txt)']} future labs
  RHCSA  (from samplerhcsa3 + 4.txt)         : {non_ma_counts['RHCSA  (from samplerhcsa3 + 4.txt)']} future labs
  RHCE   (from rhcsasample.txt)              : {non_ma_counts['RHCE   (from rhcsasample.txt)']} future labs
  CKA    (from ckaexamguide.txt)             : {non_ma_counts['CKA    (from ckaexamguide.txt)']} future labs
  RHCSA 9 & 10 (PerfectScorerPracticeExams)  : {non_ma_counts['RHCSA 9 & 10 (PerfectScorerPracticeExams)']} future labs
  CKAD   (from ckadstudyguide.txt)           : {non_ma_counts['CKAD   (from ckadstudyguide.txt)']} future labs

  Mastering Ansible labs (from ch1, ch2, ch7, ch8, ch13):
    Ch 1  System Architecture & Design       : {chapter_counts['ch1']} labs
    Ch 2  Migration / Collections / FQCNs    : {chapter_counts['ch2']} labs
    Ch 7  Task Conditions / Loops / Rescue   : {chapter_counts['ch7']} labs
    Ch 8  Roles / Includes / ansible-galaxy  : {chapter_counts['ch8']} labs
    Ch 13 Network Automation                 : {chapter_counts['ch13']} labs
    ──────────────────────────────────────────
    Mastering Ansible subtotal               : {ma_total} labs

  -----------------------------------------------------------
  TOTAL                                      : {total} future labs

  (Verified on 2026-05-23 by counting every line that starts
   with `- ` in each section. The template.txt appendix at the
   end of this file contains lab-checklist `- [ ]` bullets that
   are NOT counted toward this total — they belong to the
   reference template, not to the future-lab list.)

  CKAD breakdown by exam domain:
    Application Design and Build .................. 7
    Application Deployment ........................ 3
    Application Observability and Maintenance ..... 3
    Application Environment, Config & Security .... 7
    Services and Networking ....................... 3

  RHCSA 9 & 10 breakdown by README section:
    Networking ................. 3
    Package Management ......... 2
    Firewall ................... 2
    Remote Admin & SSH ......... 6
    Web Services (Apache) ...... 5
    User & Group Management .... 8
    Permissions & ACLs ......... 5
    Sudo & Privilege ........... 3
    NFS & AutoFS ............... 3
    Scheduled Tasks ............ 6
    Essential Tools & Files .... 7
    Text File Management ....... 3
    Archives & Compression ..... 3
    System Time & Locale ....... 2
    Boot Process & GRUB ........ 1
    Storage Management ......... 2
    LVM ........................ 7
    SELinux .................... 4
    Systemd & Services ......... 1
    System Performance ......... 2
    Containers & Flatpak ....... 10
    Shell Scripting ............ 6
    Process Management ......... 4
    Documentation Tools ........ 1
    Environment & Shell ........ 1
"""

    text = re.sub(
        r"----------------------------------------------------------------\nSUMMARY COUNTS\n----------------------------------------------------------------\n.*?(?=\n================================================================\nREFERENCE TEMPLATE FOR FUTURE LABS)",
        new_summary,
        text,
        count=1,
        flags=re.DOTALL,
    )

    DEST.write_text(text, encoding="utf-8", newline="\n")

    final = DEST.read_text(encoding="utf-8")
    em = final.count("\u2014")
    qmark_damage = len(re.findall(r" \? ", final))
    print(f"Wrote {len(final.splitlines())} lines.")
    print(f"Em-dashes preserved: {em}")
    print(f"Space-?-space damage markers: {qmark_damage}")
    print(f"Chapter counts: {chapter_counts}  (sum {ma_total})")
    print(f"Non-MA section counts: {non_ma_counts}")
    print(f"GRAND TOTAL future labs: {total}")


if __name__ == "__main__":
    main()
