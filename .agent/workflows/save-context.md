---
description: Save current working context and progress to a markdown file
---

1. Identify current progress
2. Create context file
// turbo
3. Run `FILE_NAME=.agent/context/context-$(date +%Y%m%d-%H%M).md; echo "# Context Snapshot - $(date)" > $FILE_NAME; echo "## Tasks Completed" >> $FILE_NAME; grep "\[x\]" task.md >> $FILE_NAME; echo "## Current Focus" >> $FILE_NAME; grep "\[/\]" task.md >> $FILE_NAME`
4. Summarize manually in the file if needed
5. Context saved
