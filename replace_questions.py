#!/usr/bin/env python3
"""Replace each 'Verbatim Questions from chN.txt' block in future_labs.txt
with the paraphrased question-stems-only version.

This drops the verbatim a/b/c/d multiple-choice text and keeps only
short, paraphrased question stems that align with the navigate-and-
discover learning intent documented at the top of the file.
"""
import re
from pathlib import Path

DEST = Path("future_labs.txt")

STEMS = {
    "ch1": [
        "Why is an inventory important to Ansible?",
        "Do Ansible users need to manually update inventory for frequently changing infrastructure?",
        "By default, in what order does Ansible process hosts in an inventory?",
        "By default, in what order are Ansible tasks in a simple playbook executed?",
        "Which variable type has the highest priority?",
        "What are Ansible's special runtime variables called?",
        "What would you use to access external data from a playbook?",
        "What is Ansible's preferred default transport for most non-Windows hosts?",
        "What can inventory variables be used for?",
        "How can you override the default Ansible configuration?",
    ],
    "ch2": [
        "What can Ansible Collections contain?",
        "Do Collections make module versioning independent of the Ansible engine version?",
        "What is the relationship between the Ansible package and the automation engine?",
        "Can you upgrade directly from Ansible 2.9 to Ansible 4.3?",
        "Are module names guaranteed to be unique across namespaces in Ansible 4.3?",
        "What naming format helps ensure you call the correct module?",
        "Which file lists required Collections for easy installation?",
        "How is your Ansible Galaxy namespace created?",
        "What archive format are Collections stored in?",
        "How can you list installed Collections?",
    ],
    "ch7": [
        "Does Ansible stop processing further tasks for a host after the first failure by default?",
        "What default statuses do `command` and `shell` usually return?",
        "Which keyword stores task results?",
        "Which directive changes a task's failure condition?",
        "How can multiple conditional statements be combined?",
        "How can changed status be suppressed?",
        "How do tasks behave inside a `block` when an error occurs?",
        "Which block section runs only after an error?",
        "When does the `always` section of a block run?",
        "What is the default variable name for the current loop item?",
    ],
    "ch8": [
        "Which module runs tasks from an external task file?",
        "Can variable data be passed to an external task file?",
        "What is the default variable name for the current loop value?",
        "Which loop control prevents loop variable name collisions?",
        "When are handlers generally run?",
        "From which external sources can Ansible load variables?",
        "How do roles get their names?",
        "What happens if a role is missing `tasks/main.yml`?",
        "Can roles depend on other roles?",
        "What happens when you specify a tag for a role?",
    ],
    "ch13": [
        "Does Ansible bring infrastructure automation benefits to network device management?",
        "What should you do first when working with a new network device type?",
        "What is remote execution?",
        "What is local execution?",
        "Which protocol mostly superseded older local connection-based network automation?",
        "Can facts be gathered for an Arista EOS device at the start of a play?",
        "Is all Arista EOS network configuration performed with one module?",
        "Why does Cumulus Linux not require `ansible.netcommon.network_cli`?",
        "Why is inventory management important in multi-device networks?",
        "Can Ansible support bastion or jump hosts without special proxy software?",
    ],
}


def build_block(chapter: str) -> str:
    stems = STEMS[chapter]
    lines = [f"Question Stems from {chapter}.txt (paraphrased — use as lab prompts):", ""]
    for i, stem in enumerate(stems, start=1):
        lines.append(f"  {i:2d}. {stem}")
    lines.append("")
    return "\n".join(lines)


def replace_block(text: str, chapter: str, end_anchor: str) -> str:
    start_marker = f"Verbatim Questions from {chapter}.txt"
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"missing start marker for {chapter}")
    end = text.find(end_anchor, start)
    if end < 0:
        raise SystemExit(f"missing end anchor for {chapter}")
    return text[:start] + build_block(chapter) + "\n\n" + text[end:]


def main():
    text = DEST.read_text(encoding="utf-8")

    text = replace_block(text, "ch1",  "================================================================\nMASTERING ANSIBLE  Ch 2")
    text = replace_block(text, "ch2",  "================================================================\nMASTERING ANSIBLE  Ch 7")
    text = replace_block(text, "ch7",  "================================================================\nMASTERING ANSIBLE  Ch 8")
    text = replace_block(text, "ch8",  "================================================================\nMASTERING ANSIBLE  Ch 13")
    text = replace_block(text, "ch13", "----------------------------------------------------------------\nSUMMARY COUNTS")

    text = re.sub(
        r"\*\*\* NAVIGATE-AND-DISCOVER REMINDER \(see INTENT block at top of file\) \*\*\*\nThe verbatim multiple-choice questions below are kept here as REFERENCE\nONLY\. When the corresponding labs above are actually built, these\nquestions MUST be rewritten in template\.txt-style navigate-and-discover\nform \(open-ended prompt \+ hint commands like `ansible-doc`, `man`,\n`find`, `grep`, `journalctl`, `<cmd> --help`\)\. The a/b/c/d options below\nare the source-of-truth answer key for the lab author, not the final\nquestion format the learner should see\.\n\*{71}",
        (
            "*** NAVIGATE-AND-DISCOVER REMINDER (see INTENT block at top of file) ***\n"
            "The question stems below are paraphrased prompts only. When the\n"
            "corresponding labs above are actually built, each stem should be\n"
            "expanded into a template.txt-style navigate-and-discover lab:\n"
            "an open-ended prompt plus hint commands like `ansible-doc`, `man`,\n"
            "`find`, `grep`, `journalctl`, or `<cmd> --help` so the learner\n"
            "answers by exploring Linux, not by picking a/b/c/d.\n"
            "***********************************************************************"
        ),
        text,
    )

    DEST.write_text(text, encoding="utf-8", newline="\n")

    final = DEST.read_text(encoding="utf-8")
    print(f"Lines: {len(final.splitlines())}")
    print(f"Em-dashes: {final.count(chr(0x2014))}")
    print(f"Verbatim blocks remaining: {final.count('Verbatim Questions from')}")
    print(f"Stem blocks present: {final.count('Question Stems from')}")
    print(f"a/b/c/d option lines remaining: {len(re.findall(r'^\\s+[a-d]\\)', final, flags=re.MULTILINE))}")


if __name__ == "__main__":
    main()
