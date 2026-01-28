# Testing Guide for Outbound Engine

## Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** - Get one from https://platform.openai.com/api-keys

## Step 1: Install Dependencies

```bash
cd /Users/maxsolmssen/Cursor/outbound-engine
pip install -r requirements.txt
```

If you prefer using a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Set Up API Key

**Option A: Environment Variable (Recommended)**

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Option B: Enter in App**
You can also enter your API key directly in the app's sidebar after launching.

## Step 3: Launch the App

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

If it doesn't open automatically, you'll see a URL in the terminal - click it or copy/paste into your browser.

## Step 4: Test with Sample Data

### Test Case 1: Basic Hypothesis Generation

1. **Navigate to "Research Input"** (should be default)

2. **Fill in sample data:**

   **Company Overview:**
   ```
   Stripe
   - Payment processing platform
   - 7,000+ employees
   - Engineering-heavy organization
   - Series H funding, valued at $65B
   - Tech stack: Ruby, Go, JavaScript, microservices architecture
   - Known for high engineering standards and developer-focused culture
   ```

   **Relevant Job Postings:**
   ```
   Senior Platform Engineer - Developer Experience
   - Building internal developer tools and platforms
   - Focus on improving developer productivity
   - Experience with VS Code extensions and developer tooling
   - Location: San Francisco
   ```

   **Target Persona LinkedIn Profiles:**
   ```
   Sarah Chen - VP of Engineering at Stripe
   - 10+ years in engineering leadership
   - Previously at Google, led platform teams
   - Recent post: "Investing heavily in developer experience this year"
   - Background: Infrastructure and developer tooling
   ```

   **Recent News/Signals:**
   ```
   - Announced $1B investment in engineering infrastructure
   - Hiring surge: 200+ engineering roles posted
   - Tech blog post: "Scaling our engineering organization"
   - Mentioned developer productivity as key priority in recent all-hands
   ```

3. **Click "Generate Hypothesis"**

4. **Expected Results:**
   - Loading spinner appears
   - Hypothesis page displays with structured analysis:
     - Why This Account (company fit)
     - Why Now (timing signals)
     - Who to Target (2-3 personas)
     - Multi-Threading Strategy

### Test Case 2: Sequence Generation

1. **After generating hypothesis, click "Build Sequence →"**

2. **Fill in Prospect Information:**
   - First Name: `Sarah`
   - Last Name: `Chen`
   - Email: `sarah.chen@stripe.com`
   - Company: `Stripe`
   - Select Persona: Choose from the extracted personas
   - Job Title: `VP of Engineering` (or leave blank to use persona default)

3. **Click "Generate Sequence"**

4. **Expected Results:**
   - Loading spinner appears
   - Full sequence displays with:
     - 8 touchpoints (emails, LinkedIn, calls)
     - Subject lines for emails
     - Full message content
     - Timing for each step

5. **Test CSV Export:**
   - Click "Generate CSV Export"
   - Review the dataframe preview
   - Click "Download CSV"
   - Verify the CSV file downloads with proper format

### Test Case 3: Error Handling

1. **Test without API key:**
   - Remove API key from `.env` (or don't enter in sidebar)
   - Try to generate hypothesis
   - Should show warning message

2. **Test with empty inputs:**
   - Leave all fields blank
   - Click "Generate Hypothesis"
   - Should show error: "Please provide at least some research data"

3. **Test navigation:**
   - Use sidebar buttons to navigate between pages
   - Use back buttons on each page
   - Verify session state persists (data doesn't disappear)

## Step 5: Verify Output Quality

### Hypothesis Should Include:
- ✅ Specific references to your input data (not generic)
- ✅ Clear "Why This Account" with company fit analysis
- ✅ "Why Now" tied to actual signals you provided
- ✅ 2-3 specific personas with reasoning
- ✅ Multi-threading strategy that makes sense

### Sequence Should Include:
- ✅ 8 touchpoints matching the template structure
- ✅ Personalized content referencing the prospect/company
- ✅ Mix of channels (Email, LinkedIn, Phone)
- ✅ Subject lines under 50 characters
- ✅ Concise email bodies (under 150 words)
- ✅ Clear CTAs

### CSV Export Should Have:
- ✅ All required columns: email, first_name, last_name, title, company, sequence_name, step_number, step_day, step_type, subject, body
- ✅ 8 rows (one per step)
- ✅ Proper formatting (no extra quotes, clean text)

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "OpenAI API key not configured"
- Check `.env` file exists and has `OPENAI_API_KEY=sk-...`
- Or enter API key in sidebar
- Verify key is valid at https://platform.openai.com/api-keys

### App won't start
- Check Python version: `python3 --version` (needs 3.8+)
- Try: `python3 -m streamlit run app.py`

### API errors / Rate limits
- Check your OpenAI account has credits
- Verify API key permissions
- Check OpenAI status page

### CSV export not working
- Make sure you've generated a sequence first
- Check that prospect info (name, company) is filled in
- Try regenerating the sequence

## Next Steps After Testing

1. **Refine Prompts**: If outputs aren't quite right, edit:
   - `prompts/hypothesis.md` - Adjust hypothesis structure
   - `prompts/sequence.md` - Adjust sequence style
   - `prompts/cursor_context.md` - Update value props/messaging

2. **Customize Sequence Template**: Edit `templates/sequence_structure.md` to match your preferred cadence

3. **Test with Real Account**: Use actual research for your interview exercise

## Quick Test Checklist

- [ ] Dependencies installed
- [ ] API key configured
- [ ] App launches successfully
- [ ] Can input research data
- [ ] Hypothesis generates with structured output
- [ ] Personas are extracted correctly
- [ ] Sequence generates with all touchpoints
- [ ] CSV exports successfully
- [ ] CSV format matches Outreach.io requirements
- [ ] Navigation works between all pages
- [ ] Error handling works (empty inputs, no API key)
