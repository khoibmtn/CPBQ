---
description: Sync changes to main, push to GitHub, and create snapshot tag
---

1. Ensure we are on main branch
// turbo
2. Run `git checkout main`
3. Commit and push
// turbo
4. Run `git add . && git commit -m "sync: update $(date +%Y%m%d)" && git push origin main`
5. Create snapshot tag
// turbo
6. Run `TAG_NAME=v$(date +%Y%m%d-%H%M); git tag -a $TAG_NAME -m "Snapshot Sync"; git push origin $TAG_NAME`
7. Done
