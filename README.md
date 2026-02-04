# Outbound Engine MVP

A lightweight web app for generating Cursor-specific outbound hypotheses and sequences.

## Features

- **Research Input**: Paste company info, job postings, LinkedIn profiles, and news signals
- **AI Hypothesis Generation**: Get structured analysis of why/when/who to target
- **Sequence Builder**: Generate multi-channel outbound sequences
- **CSV Export**: Export sequences for Outreach.io import

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Project Structure

```
outbound-engine/
├── app.py                 # Main Streamlit app
├── prompts/
│   ├── cursor_context.md  # Cursor value props, use cases, differentiators
│   ├── hypothesis.md      # Prompt template for hypothesis generation
│   └── sequence.md        # Prompt template for sequence generation
├── templates/
│   └── sequence_structure.md  # Sequence template (steps, timing, channels)
├── requirements.txt       # Dependencies
└── README.md
```

## Usage

### Step 1: Input Research
Paste your research into the input fields:
- Company overview (from website, Crunchbase, etc.)
- Relevant job postings (3–5+ recommended for better outputs)
- Target persona LinkedIn profiles (3–5+ recommended for better outputs)
- Recent news or signals

### Step 2: Generate Hypothesis
Click "Generate Hypothesis" to get AI-powered analysis:
- Why this account is a good fit
- Why now is the right time
- Proof points / evidence to cite (with links where possible)
- Tech stack (from research)
- Risks / why we might lose

### Step 3: Build Sequences
Select a persona and generate:
- Draft emails with subject lines
- LinkedIn messages
- Call openers
- Export to CSV for Outreach.io

## Customization

### Cursor Context
Edit `prompts/cursor_context.md` to update:
- Value propositions
- Ideal customer profile
- Competitive positioning
- Stakeholder personas

### Sequence Structure
Edit `templates/sequence_structure.md` to customize:
- Sequence length and timing
- Channel mix
- Touchpoint purposes
