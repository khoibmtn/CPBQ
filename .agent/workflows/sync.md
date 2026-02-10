---
description: Sync changes to main, push, rename branch, and create tag
---

1. Commit current changes
// turbo
2. Run `git add . && git commit -m "sync: $(date +%Y%m%d) update"`
3. Switch to main and merge
// turbo
4. Run `git checkout main && git merge -`
5. Push to origin
// turbo
6. Run `git push origin main`
7. Return to previous branch and rename
// turbo
8. Run `PREV_BRANCH=$(git reflog | grep "checkout: moving from" | head -n 1 | awk '{print $6}'); git checkout $PREV_BRANCH`
// turbo
9. Run `NEW_NAME=$(date +%Y%m%d)-temp-update; git branch -m $NEW_NAME`
10. Create tag
// turbo
11. Run `git tag -a v$(date +%Y%m%d)-$(date +%H%M) -m "Snapshot before sync"`
12. Done
