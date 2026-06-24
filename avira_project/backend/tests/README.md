# AVIRA Backend — Test Scripts

These scripts are manual integration/smoke tests used during development.
Run them from the `backend/` directory with the virtual environment activated.

| Script | What it tests | How to run |
|--------|--------------|------------|
| `test_api_retry.py` | Full API pipeline via HTTP — waits for server, sends 6 real command payloads | `python tests/test_api_retry.py` (server must be running) |
| `test_emotion.py` | BERT emotion classifier — 10 sample sentences | `python tests/test_emotion.py` |
| `test_smart_home_emotion.py` | Command processor — device commands vs chitchat routing | `python tests/test_smart_home_emotion.py` |
| `verify_emotion.py` | Emotion model accuracy — 6 labelled sentences with pass/fail output | `python tests/verify_emotion.py` |

## Quick Run

```bash
# Activate virtual environment first
cd avira_project/backend

# Test emotion model (no server needed)
python tests/verify_emotion.py

# Test full API (start server first in another terminal)
python server.py &
python tests/test_api_retry.py
```
