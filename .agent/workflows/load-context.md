---
description: Restore project state from Source of Truth and session logs
---

1. Read latest Source of Truth
// turbo
2. Run `cat .agent/context/latest_context.md`
3. List recent session logs
// turbo
4. Run `ls -lt .agent/context/context-*.md | head -n 5`
5. Read most recent session log if needed
6. Start the Streamlit dev server
// turbo
7. Run `PYTHONPATH=/Users/buiminhkhoi/Documents/Antigravity/CPBQ/.pylibs:$PYTHONPATH python3 -m streamlit run app.py --server.port 8501`
8. Wait a few seconds, check the command output for errors. If there are import errors, install missing packages to `.pylibs` via `pip3 install --target=.pylibs <package>` then restart.
9. Confirm the app is running at http://localhost:8501 and report to user.
