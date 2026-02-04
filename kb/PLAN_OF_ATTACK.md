# Knowledge Base Upgrade - Plan of Attack

## Overview

This plan outlines the implementation of knowledge base upgrades to improve sequence quality by making outputs sound like YOU, not generic AI.

## What Was Built

### 1. Knowledge Base Directory Structure
Created `kb/` directory with 4 template files:
- **`voice.md`** - Your writing DNA (tone, style, vocabulary, examples)
- **`offers.md`** - Your offer library (what you offer, when to use it)
- **`sequence_patterns.md`** - Sequence structure and progression rules
- **`personalization_playbook.md`** - What personalization is allowed/off-limits

### 2. Code Integration
Updated `app.py` to:
- Load KB files automatically (if they exist)
- Inject KB content into sequence generation prompts
- Inject personalization guidance into hypothesis generation
- Gracefully handle missing KB files (won't break if not filled in yet)

### 3. Documentation
- **`kb/README.md`** - Overview of KB files and how they work
- **`kb/MANUAL_WORK_GUIDE.md`** - Step-by-step guide for filling in KB files

## How It Works

1. **You fill in the KB files** with your voice, style, and patterns
2. **App loads KB files** when generating sequences
3. **AI uses your KB content** to match your voice and style
4. **Outputs sound like you** instead of generic AI

## Manual Work Required

### Time Estimate
- **First pass**: 2-3 hours
- **Ongoing**: 15-30 minutes/week

### What You Need to Do

1. **Collect your best emails** (10-20 examples that got responses)
2. **Extract patterns** (what works, what doesn't)
3. **Fill in the template files** (replace placeholders with your content)
4. **Add real examples** (paste your best emails, CTAs, subject lines)

### Start Here
1. Read `kb/MANUAL_WORK_GUIDE.md` for detailed instructions
2. Start with `kb/voice.md` (biggest impact)
3. Fill in other files as you have time
4. Test by generating a sequence and see if it sounds like you

## Implementation Details

### File Loading
- KB files are loaded from `kb/` directory
- If files don't exist or are empty, app works normally (no errors)
- Files are loaded fresh on each generation (no caching)

### Prompt Injection
- KB content is appended to sequence generation prompts
- Personalization playbook is added to hypothesis generation
- KB content comes AFTER template content (so it overrides/refines)

### Priority Order
1. **Voice & Style** (`voice.md`) - Highest impact
2. **Offers** (`offers.md`) - High impact
3. **Sequence Patterns** (`sequence_patterns.md`) - Medium impact
4. **Personalization** (`personalization_playbook.md`) - Medium impact

## Next Steps

1. ✅ **Code is ready** - KB files will be loaded automatically
2. ⏳ **You fill in KB files** - Follow `MANUAL_WORK_GUIDE.md`
3. ✅ **Test** - Generate a sequence and see if it matches your voice
4. ✅ **Iterate** - Update KB files as you learn what works

## Success Criteria

You'll know it's working when:
- ✅ Generated sequences sound recognizably like you
- ✅ CTAs match your style
- ✅ Tone matches your voice
- ✅ Personalization follows your patterns
- ✅ Sequences use your proven offers

## Questions?

- **"Do I need to fill in everything?"** - No, start with `voice.md` and add others as you have time
- **"What if I don't have examples?"** - Start with what you know works, add examples later
- **"Can I update later?"** - Yes! Update KB files anytime, changes take effect immediately
- **"Will this break if KB files are empty?"** - No, app works normally without KB files

## Files Created

```
kb/
├── README.md                    # Overview of KB system
├── PLAN_OF_ATTACK.md           # This file
├── MANUAL_WORK_GUIDE.md        # Step-by-step guide for you
├── voice.md                    # Template for your writing voice
├── offers.md                   # Template for your offer library
├── sequence_patterns.md        # Template for sequence structure
└── personalization_playbook.md # Template for personalization rules
```

## Code Changes

- `app.py`: Added `load_kb_files()` function and KB injection into prompts
- No breaking changes - app works with or without KB files
