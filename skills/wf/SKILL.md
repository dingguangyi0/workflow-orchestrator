---
name: wf
description: >-
  ⚡ Shortcut for /workflow. All arguments are forwarded directly.
  Use /wf <goal> exactly like /workflow <goal>.
  Supports: /wf <goal>, /wf status, /wf report, /wf resume,
  /wf template, /wf use <template> <goal>, /wf save <name>.
---

# /wf — Workflow Shortcut

You are being invoked via the `/wf` shortcut. This is identical to `/workflow`.

**Forward ALL arguments to the workflow skill.** Read the full protocol from
`~/.claude/skills/workflow/SKILL.md` and follow it exactly with the user's input.

The user's input after `/wf` is: <user's arguments>

If the user typed just `/wf` with no arguments, show usage:
```
/wf <goal>                  Start workflow
/wf status                  Show current status
/wf report                  Generate report
/wf resume                  Resume interrupted workflow
/wf template                List templates
/wf use <template> <goal>   Use template
/wf save <name>             Save as template
```
