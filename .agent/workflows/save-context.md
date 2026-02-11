---
description: Save session context, update Source of Truth, and cleanup old logs
---

1. Update Source of Truth (`latest_context.md`)
2. Capture Session Log
// turbo
3. Run `TS=$(date +%Y%m%d-%H%M); FILE_NAME=.agent/context/context-$TS.md; echo "# Session Log - $TS" > $FILE_NAME; echo "## Tasks Completed" >> $FILE_NAME; grep "\[x\]" /Users/buiminhkhoi/.gemini/antigravity/brain/63ca1a18-70c5-4389-bf51-0b8fcab486cc/task.md >> $FILE_NAME; echo "## Changes Made" >> $FILE_NAME; git log -n 5 --oneline >> $FILE_NAME`
4. Auto-cleanup old logs (Keep 10 latest)
// turbo
5. Run `ls -t .agent/context/context-*.md | tail -n +11 | xargs rm -f 2>/dev/null || true`
6. Sync to Git
// turbo
7. Run `git add .agent/context/ && git commit -m "context: snapshot $TS"`
8. Done
