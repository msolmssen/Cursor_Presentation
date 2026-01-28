# Version Management Guide

This project uses a folder-based versioning system for easy presentation and comparison of different versions.

## Project Structure

```
outbound-engine/
├── app.py                    # Current version (V2)
├── versions/
│   └── v1/                   # V1 - Complete snapshot
│       ├── app.py
│       ├── requirements.txt
│       ├── prompts/
│       └── templates/
├── run_version.sh            # Launcher script
└── VERSION_GUIDE.md          # This file
```

## Running Different Versions

### Quick Launch (Recommended)

Use the launcher script:

```bash
# Run V1
./run_version.sh v1

# Run V2 (current)
./run_version.sh v2

# Run V3 (when created)
./run_version.sh v3
```

### Manual Launch

**V1:**
```bash
cd versions/v1
streamlit run app.py
```

**V2 (Current):**
```bash
streamlit run app.py
```

## For Presentations

### Side-by-Side Comparison

1. **Terminal 1:** Run V1
   ```bash
   ./run_version.sh v1
   ```
   Opens at `http://localhost:8501`

2. **Terminal 2:** Run V2
   ```bash
   ./run_version.sh v2
   ```
   Opens at `http://localhost:8502` (Streamlit auto-increments port)

3. **Terminal 3:** Run V3 (if exists)
   ```bash
   ./run_version.sh v3
   ```
   Opens at `http://localhost:8503`

### Single Version Demo

Just run the version you want to show:
```bash
./run_version.sh v1  # or v2, v3, etc.
```

## Creating a New Version

When you're ready to save V2 and start V3:

1. **Copy current version to versions folder:**
   ```bash
   mkdir -p versions/v2
   cp -r app.py requirements.txt README.md prompts templates versions/v2/
   ```

2. **Commit to git:**
   ```bash
   git add versions/v2/
   git commit -m "Save V2 snapshot"
   git tag -a v2.0 -m "Version 2.0"
   ```

3. **Continue working on V3** in the root directory

## Git Integration

- **Tags:** Use git tags for milestone versions (`v1.0`, `v2.0`, etc.)
- **Branches:** Use branches for active development (`v2`, `v3`, etc.)
- **Folders:** Use `versions/` folder for easy access during presentations

This gives you:
- ✅ Easy access to any version for demos
- ✅ Git history for tracking changes
- ✅ Ability to run multiple versions simultaneously
- ✅ Clear separation between versions
