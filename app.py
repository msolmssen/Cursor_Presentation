"""
Outbound Engine MVP
A lightweight web app for generating Cursor-specific outbound hypotheses and sequences.
"""

import streamlit as st
import os
import io
import re
import pandas as pd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Optional Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Outbound Engine",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "input"
if "research_data" not in st.session_state:
    st.session_state.research_data = {}
if "hypothesis" not in st.session_state:
    st.session_state.hypothesis = None
if "personas" not in st.session_state:
    st.session_state.personas = []
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None
if "sequence" not in st.session_state:
    st.session_state.sequence = None
if "prospect_info" not in st.session_state:
    st.session_state.prospect_info = {}


def get_openai_client():
    """Get OpenAI client with API key from environment or sidebar."""
    api_key = os.getenv("OPENAI_API_KEY") or st.session_state.get("openai_api_key")
    if api_key:
        return OpenAI(api_key=api_key)
    return None


def list_available_gemini_models():
    """List available Gemini models for debugging."""
    if not GEMINI_AVAILABLE:
        return []
    api_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")
    if not api_key:
        return []
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available.append(model.name)
        return available
    except Exception as e:
        return []


def get_gemini_client():
    """Get Gemini client with API key from environment or sidebar."""
    if not GEMINI_AVAILABLE:
        return None
    api_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")
    if api_key:
        genai.configure(api_key=api_key)
        # Try different model names in order of preference
        model_names = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        # First, try to list available models and use the first one that supports generateContent
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    # Extract model name (remove 'models/' prefix if present)
                    model_name = model.name.replace('models/', '')
                    return genai.GenerativeModel(model_name)
        except:
            pass
        
        # Fallback: try model names directly
        for model_name in model_names:
            try:
                return genai.GenerativeModel(model_name)
            except:
                continue
        
        # If all else fails, try the first one and let it error
        return genai.GenerativeModel('gemini-1.5-flash')
    return None


def get_ai_provider():
    """Get the selected AI provider from session state."""
    return st.session_state.get("ai_provider", "openai")  # Default to OpenAI


def generate_demo_hypothesis(research_data: dict) -> str:
    """Generate a realistic demo hypothesis without API calls."""
    company_info = research_data.get("company_info", "").lower()
    job_postings = research_data.get("job_postings", "").lower()
    news_signals = research_data.get("news_signals", "").lower()
    
    # Extract company name if possible
    company_name = "this company"
    if company_info:
        lines = company_info.split("\n")
        for line in lines[:3]:
            if "company" in line or "inc" in line or "corp" in line or "ltd" in line:
                company_name = line.split()[0] if line.split() else "this company"
                break
    
    # Detect signals
    has_funding = "funding" in news_signals or "raised" in news_signals or "series" in news_signals
    has_hiring = "hiring" in job_postings or "engineer" in job_postings or "developer" in job_postings
    has_devex = "devex" in job_postings or "developer experience" in job_postings or "platform" in job_postings
    
    hypothesis = f"""## Why This Account

{company_name.title()} appears to be a strong fit for Cursor based on several indicators:

**Company Scale & Engineering Focus:**
- Based on the research provided, this organization demonstrates significant engineering investment
- The presence of relevant job postings suggests an active, growing engineering organization
- This indicates the scale necessary to benefit from AI-powered developer productivity tools

**Tech Stack & Digital Maturity:**
- The research suggests a modern, engineering-forward culture
- Active hiring in technical roles indicates ongoing investment in engineering capabilities
- This aligns with Cursor's ideal customer profile of companies prioritizing developer experience

**Budget Indicators:**
{f"- Recent funding activity suggests budget availability for developer tooling investments" if has_funding else "- Growth indicators suggest potential budget for productivity tools"}

---

## Why Now

Several timely signals create urgency for outreach:

**Immediate Triggers:**
{f"- Active hiring in engineering roles - perfect timing to introduce productivity tools as teams scale" if has_hiring else "- Engineering team growth creates opportunity for productivity improvements"}
{f"- Platform/DevEx team formation or expansion indicates focus on developer experience" if has_devex else "- Active engineering investment suggests openness to productivity solutions"}

**Pain Points Likely Experienced:**
- Scaling engineering teams while maintaining velocity
- Onboarding new developers efficiently
- Managing context-switching and productivity bottlenecks
- Justifying engineering headcount growth to leadership

**Connection to Cursor Value Props:**
- Cursor's 2-3x velocity improvement directly addresses scaling challenges
- Codebase understanding accelerates onboarding for new team members
- AI-powered development helps teams ship faster without proportional headcount increases

---

## Who to Target

### 1. VP/Director of Engineering
**Why They Care:**
- Accountable for engineering output and delivery velocity
- Budget authority for developer tools
- Feeling pressure to scale teams efficiently

**Pain Points:**
- Teams not shipping fast enough to meet business demands
- Difficulty justifying headcount growth
- Developer retention and burnout concerns

**Anticipated Objections:**
- "We already have GitHub Copilot" → Position Cursor as codebase-aware upgrade
- "Need to see ROI first" → Offer pilot with measurable metrics
- "Developers should decide" → Enable evaluation while providing structure

### 2. Platform/DevEx Engineering Lead
**Why They Care:**
- Owns developer productivity and tooling
- Tasked with improving developer experience
- Influences tool adoption decisions

**Pain Points:**
- Low adoption of existing developer tools
- Developers complaining about productivity blockers
- Difficulty measuring tooling impact

**Anticipated Objections:**
- "Building our own tools" → Highlight time-to-value and focus on core product
- "How do we measure impact?" → Provide evaluation framework
- "Security review concerns" → Share SOC 2 certs and privacy mode details

### 3. CTO / Chief Technology Officer
**Why They Care:**
- Sets technical strategy and vision
- Accountable for engineering ROI
- Cares about competitive advantage

**Pain Points:**
- Engineering costs growing faster than output
- Competitors shipping faster
- Board pressure on efficiency

**Anticipated Objections:**
- "Is this mature enough for enterprise?" → Share customer references and certifications
- "What's the vendor risk?" → Discuss company stability and roadmap
- "How does this fit our AI strategy?" → Position as strategic AI investment

---

## Multi-Threading Strategy

### Phase 1: Technical Champion (Week 1)
**Start with:** Platform/DevEx Engineering Lead
- They're most likely to understand the value immediately
- Can become internal advocate
- Lower barrier to initial conversation

**Approach:**
- Reference specific job posting or team formation
- Focus on developer experience and productivity metrics
- Offer developer trial access

### Phase 2: Engineering Leadership (Week 2)
**Engage:** VP/Director of Engineering
- Reference technical champion's interest
- Connect to scaling and velocity challenges
- Discuss structured evaluation approach

**Approach:**
- Multi-thread with technical champion's support
- Present ROI framework and pilot structure
- Address budget and procurement questions

### Phase 3: Executive Alignment (Week 3)
**Involve:** CTO (if evaluation is serious)
- Bring in when there's genuine evaluation interest
- Strategic positioning and competitive advantage
- Address enterprise concerns

**Approach:**
- Reference team-level evaluation progress
- Discuss strategic AI investment angle
- Share customer success stories at similar scale

### Recommended Cadence
- **Week 1:** Initial outreach to technical champion (email + LinkedIn)
- **Week 2:** Follow-up with engineering leadership (email + phone)
- **Week 3:** Executive touchpoint if evaluation progressing (email)
- **Ongoing:** Multi-channel touchpoints every 2-3 days within each week

### Key Success Factors
1. **Front-load personalization** - Use specific signals from research
2. **Create internal momentum** - Get technical champion excited first
3. **Structure the evaluation** - Provide framework and metrics
4. **Address security early** - Proactively share compliance info if needed
"""
    
    return hypothesis


def generate_demo_sequence(persona: str, hypothesis: str, prospect_info: dict) -> str:
    """Generate a realistic demo sequence without API calls."""
    first_name = prospect_info.get('first_name', 'John')
    company = prospect_info.get('company', 'Acme Corp')
    
    sequence = f"""# Outbound Sequence for {first_name} - {company}

## Sequence Overview
**Target Persona:** {persona}
**Total Steps:** 8
**Duration:** 14 days
**Channels:** Email, LinkedIn, Phone

---

## Step 1: Initial Email (Day 1)
**Type:** Email
**Subject:** Your DevEx team caught my attention

**Body:**

Hi {first_name},

I noticed {company} is building out your developer experience function - saw the Platform Engineering role you're hiring for.

At similar companies, we've seen DevEx teams struggle with developer tool adoption. Teams try new tools, but they don't stick because they don't understand the full codebase context.

Cursor is different - it's an AI code editor built from the ground up with codebase understanding. When developers ask questions about your authentication system across 50 files, Cursor actually knows the answer.

Quick question: What's your biggest challenge with developer productivity right now?

Best,
[Your Name]

---

## Step 2: LinkedIn Connection (Day 2)
**Type:** LinkedIn
**Message:**

Hi {first_name}, I saw your role at {company} and thought you might be interested in connecting. I work with engineering leaders on developer productivity - would love to share what I'm seeing in the market.

---

## Step 3: Follow-up Email (Day 4)
**Type:** Email
**Subject:** Re: Your DevEx team caught my attention

**Body:**

Hi {first_name},

Following up on my note about developer productivity at {company}.

One thing I didn't mention: Cursor is built on VS Code, so your developers can start using it immediately with zero learning curve. All their extensions, settings, and workflows work exactly the same.

We've seen 90%+ adoption in the first 30 days at companies like yours - developers actually ask for it.

Worth a 15-minute conversation?

Best,
[Your Name]

---

## Step 4: LinkedIn Message (Day 5)
**Type:** LinkedIn
**Message:**

{first_name}, curious - are you evaluating any AI coding tools for your team? Seeing a lot of interest from DevEx leaders right now.

---

## Step 5: Value Email (Day 7)
**Type:** Email
**Subject:** Quick question about {company}'s engineering velocity

**Body:**

Hi {first_name},

I've been thinking about the scaling challenges you're likely facing as you grow the engineering team.

One thing we hear consistently: teams using Cursor report 2-3x faster development velocity. Not just autocomplete - actual codebase understanding that helps with refactoring, debugging, and onboarding.

If you're open to it, I'd love to show you a quick demo on your actual codebase. Takes 15 minutes and you'll see the difference immediately.

Does next week work for a brief call?

Best,
[Your Name]

---

## Step 6: Phone Call Attempt (Day 9)
**Type:** Phone
**Opener:**

Hi {first_name}, this is [Your Name] from Cursor. I've been emailing you about developer productivity tools - do you have 2 minutes?

**If voicemail:**
Hi {first_name}, this is [Your Name] from Cursor. I've been reaching out about AI-powered developer productivity tools. I noticed {company} is investing heavily in engineering, and I thought you'd be interested in what we're seeing - teams using Cursor are shipping 2-3x faster. Would love to connect - my number is [phone]. Talk soon.

---

## Step 7: Final Email (Day 11)
**Type:** Email
**Subject:** Last try - developer productivity at {company}

**Body:**

Hi {first_name},

I know you're busy, so I'll keep this short.

{company} is clearly investing in engineering - the Platform Engineering role you're hiring for is proof of that. The question is: are your developers as productive as they could be?

Cursor helps engineering teams ship faster without adding headcount. It's what GitHub Copilot would be if it understood your entire codebase.

If this isn't the right time, no worries. But if you're curious, I'm happy to show you what it looks like in action.

Best,
[Your Name]

---

## Step 8: Breakup Email (Day 14)
**Type:** Email
**Subject:** Closing the loop

**Body:**

Hi {first_name},

Haven't heard back, so I'll assume this isn't a priority right now. That's totally fine - timing matters.

If that changes, or if you'd like to stay in touch for when it makes sense, just let me know.

Best of luck with the engineering growth at {company}.

Best,
[Your Name]

---

## Personalization Notes
- Reference specific job postings or team formations from research
- Connect to actual pain points mentioned in hypothesis
- Adjust messaging based on persona's likely concerns
- Use company-specific signals throughout sequence
"""
    
    return sequence


def load_file(filepath: str) -> str:
    """Load a file from the project directory."""
    file_path = Path(__file__).parent / filepath
    if file_path.exists():
        return file_path.read_text()
    return ""


def generate_hypothesis_with_ai(prompt: str, provider: str) -> str:
    """Generate text using the specified AI provider."""
    if provider == "gemini":
        model = get_gemini_client()
        if not model:
            raise Exception("Gemini API key not configured")
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Check for rate limit errors
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise Exception("RATE_LIMIT")
            raise e
    else:  # OpenAI
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI API key not configured")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales strategist. Generate actionable, specific outbound hypotheses based on account research."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Check for quota/authentication errors
            if "quota" in error_msg.lower() or "insufficient" in error_msg.lower() or "429" in error_msg:
                raise Exception("QUOTA_EXCEEDED")
            raise e


def generate_hypothesis(research_data: dict, use_demo: bool = False) -> str:
    """Generate outbound hypothesis using AI or demo mode."""
    # Check if demo mode is enabled
    if use_demo or st.session_state.get("demo_mode", False):
        return generate_demo_hypothesis(research_data)
    
    provider = get_ai_provider()
    
    # Load prompts
    cursor_context = load_file("prompts/cursor_context.md")
    hypothesis_template = load_file("prompts/hypothesis.md")
    
    # Build the prompt
    prompt = hypothesis_template.replace("{{company_info}}", research_data.get("company_info", "Not provided"))
    prompt = prompt.replace("{{job_postings}}", research_data.get("job_postings", "Not provided"))
    prompt = prompt.replace("{{linkedin_profiles}}", research_data.get("linkedin_profiles", "Not provided"))
    prompt = prompt.replace("{{news_signals}}", research_data.get("news_signals", "Not provided"))
    prompt = prompt.replace("{{cursor_context}}", cursor_context)
    
    # Add system context for Gemini (which doesn't have separate system messages)
    if provider == "gemini":
        prompt = f"You are an expert B2B sales strategist. Generate actionable, specific outbound hypotheses based on account research.\n\n{prompt}"
    
    try:
        return generate_hypothesis_with_ai(prompt, provider)
    except Exception as e:
        error_msg = str(e)
        # Check for quota/rate limit errors
        if "QUOTA_EXCEEDED" in error_msg or "RATE_LIMIT" in error_msg:
            st.warning(f"⚠️ **API Quota/Rate Limit Exceeded**: Switching to demo mode. You can test the full app flow without an API key.")
            return generate_demo_hypothesis(research_data)
        # Try switching providers if one fails
        if provider == "openai":
            st.info("🔄 OpenAI failed, trying Gemini...")
            try:
                st.session_state.ai_provider = "gemini"
                return generate_hypothesis_with_ai(prompt, "gemini")
            except:
                st.warning("⚠️ Both providers failed. Switching to demo mode.")
                return generate_demo_hypothesis(research_data)
        else:
            st.warning("⚠️ **API Error**: Switching to demo mode.")
            return generate_demo_hypothesis(research_data)


def extract_personas_from_hypothesis(hypothesis: str) -> list:
    """Extract persona recommendations from the hypothesis."""
    # Check for demo mode
    if st.session_state.get("demo_mode", False):
        return ["VP/Director of Engineering", "Platform/DevEx Engineering Lead", "CTO"]
    
    provider = get_ai_provider()
    prompt = f"Extract the recommended target personas from this sales hypothesis. Return ONLY a Python list of job titles, nothing else. Example: [\"VP Engineering\", \"DevEx Lead\", \"CTO\"]\n\n{hypothesis}"
    
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if model:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0,
                        max_output_tokens=200,
                    )
                )
                content = response.text.strip()
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                raise Exception("No API key")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Extract the recommended target personas from this sales hypothesis. Return ONLY a Python list of job titles, nothing else. Example: [\"VP Engineering\", \"DevEx Lead\", \"CTO\"]"},
                    {"role": "user", "content": hypothesis}
                ],
                temperature=0,
                max_tokens=200
            )
            content = response.choices[0].message.content.strip()
        
        # Try to evaluate as a Python list
        import ast
        personas = ast.literal_eval(content)
        if isinstance(personas, list) and len(personas) > 0:
            return personas
    except:
        pass
    
    # Fallback - try to extract from hypothesis text
    personas = []
    if "VP" in hypothesis or "Director" in hypothesis:
        personas.append("VP/Director of Engineering")
    if "Platform" in hypothesis or "DevEx" in hypothesis:
        personas.append("Platform/DevEx Engineering Lead")
    if "CTO" in hypothesis:
        personas.append("CTO")
    
    return personas if personas else ["VP/Director of Engineering", "Platform/DevEx Engineering Lead", "CTO"]


def generate_sequence(persona: str, hypothesis: str, prospect_info: dict, use_demo: bool = False) -> str:
    """Generate outbound sequence for a specific persona."""
    # Check if demo mode is enabled
    if use_demo or st.session_state.get("demo_mode", False):
        return generate_demo_sequence(persona, hypothesis, prospect_info)
    
    provider = get_ai_provider()
    
    # Load templates
    cursor_context = load_file("prompts/cursor_context.md")
    sequence_template = load_file("prompts/sequence.md")
    sequence_structure = load_file("templates/sequence_structure.md")
    
    # Build prospect context
    prospect_context = f"""
Prospect Information:
- Name: {prospect_info.get('first_name', 'Unknown')} {prospect_info.get('last_name', '')}
- Title: {prospect_info.get('title', persona)}
- Company: {prospect_info.get('company', 'Unknown Company')}
- Email: {prospect_info.get('email', 'unknown@company.com')}
"""
    
    # Build the prompt
    prompt = sequence_template.replace("{{persona}}", f"{persona}\n\n{prospect_context}")
    prompt = prompt.replace("{{hypothesis}}", hypothesis)
    prompt = prompt.replace("{{sequence_template}}", sequence_structure)
    prompt = prompt.replace("{{cursor_context}}", cursor_context)
    
    # Add system context for Gemini
    if provider == "gemini":
        prompt = f"You are an expert B2B sales copywriter. Generate compelling, personalized outbound sequences for developer tools.\n\n{prompt}"
    
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if not model:
                raise Exception("Gemini API key not configured")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=3000,
                )
            )
            return response.text
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                raise Exception("OpenAI API key not configured")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales copywriter. Generate compelling, personalized outbound sequences for developer tools."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        # Check for quota/rate limit errors
        if "quota" in error_msg.lower() or "insufficient" in error_msg.lower() or "429" in error_msg or "RATE_LIMIT" in str(e):
            st.warning("⚠️ **API Quota/Rate Limit Exceeded**: Switching to demo mode. You can test the full app flow without an API key.")
            return generate_demo_sequence(persona, hypothesis, prospect_info)
        # Try switching providers if one fails
        if provider == "openai":
            st.info("🔄 OpenAI failed, trying Gemini...")
            try:
                st.session_state.ai_provider = "gemini"
                model = get_gemini_client()
                if model:
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=3000,
                        )
                    )
                    return response.text
            except:
                st.warning("⚠️ Both providers failed. Switching to demo mode.")
                return generate_demo_sequence(persona, hypothesis, prospect_info)
        st.warning("⚠️ **API Error**: Switching to demo mode.")
        return generate_demo_sequence(persona, hypothesis, prospect_info)


def parse_sequence_to_csv(sequence: str, prospect_info: dict) -> pd.DataFrame:
    """Parse the generated sequence into CSV format for Outreach.io."""
    provider = get_ai_provider()
    
    # Count steps in the sequence to validate extraction
    step_count = sequence.count("## Step") or sequence.count("Step ")
    
    csv_prompt = f"""
Convert this outbound sequence into a structured CSV format. Extract EVERY SINGLE STEP and return ONLY valid CSV data with these exact columns:
step_number,step_day,step_type,subject,body

CRITICAL REQUIREMENTS:
- Extract ALL steps from the sequence (there should be multiple steps, typically 6-8)
- Do NOT skip any steps - every step in the sequence must appear in the CSV
- Count the steps in the sequence first to ensure you capture them all

Rules:
- step_number: 1, 2, 3, 4, 5, 6, 7, 8, etc. (numeric only, sequential)
- step_day: Extract the day number from each step (e.g., "Day 1" = 1, "Day 4" = 4)
- step_type: Email, LinkedIn, or Phone (exact values, case-sensitive)
- subject: Email subject line (leave empty for LinkedIn/Phone steps)
- body: The full message content (for phone, include opener and voicemail script)

IMPORTANT CSV FORMATTING RULES:
- Use double quotes to wrap fields that contain commas, newlines, or quotes
- Escape any double quotes inside fields by doubling them ("" becomes "")
- Do NOT include any markdown code blocks (no ```)
- Do NOT include any explanations or text before/after the CSV
- Start immediately with the header row: step_number,step_day,step_type,subject,body
- Each row must be on a single line (use \\n for newlines within body field)
- Ensure all rows have the same number of columns
- Include ALL steps - if the sequence has 8 steps, the CSV must have 8 rows

Return ONLY the raw CSV data, nothing else.

Sequence to convert:
{sequence}
"""
    
    csv_content = None
    try:
        if provider == "gemini":
            model = get_gemini_client()
            if not model:
                st.error("Gemini API key not configured for CSV export")
                return pd.DataFrame()
            response = model.generate_content(
                f"You are a data formatter. Convert sequences to clean CSV format.\n\n{csv_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=4000,  # Increased to handle all 8 steps
                )
            )
            csv_content = response.text.strip()
        else:  # OpenAI
            client = get_openai_client()
            if not client:
                st.error("OpenAI API key not configured for CSV export")
                return pd.DataFrame()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a data formatter. Convert sequences to clean CSV format. Extract ALL steps from the sequence - do not skip any steps."},
                    {"role": "user", "content": csv_prompt}
                ],
                temperature=0,
                max_tokens=4000  # Increased to handle all 8 steps
            )
            csv_content = response.choices[0].message.content.strip()
        
        # Remove any markdown code blocks
        if csv_content.startswith("```"):
            # Extract content from code block
            lines = csv_content.split("\n")
            # Find the first line that's not ``` or language identifier
            start_idx = 1
            if len(lines) > 1 and lines[1].strip() and not lines[1].strip().startswith("```"):
                start_idx = 1
            else:
                start_idx = 2
            # Find the last ```
            end_idx = len(lines) - 1
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            csv_content = "\n".join(lines[start_idx:end_idx])
        
        # Clean up the CSV content
        csv_content = csv_content.strip()
        
        # Remove any leading/trailing non-CSV content (explanations, etc.)
        lines = csv_content.split("\n")
        # Find the header row (should contain step_number, step_day, etc.)
        header_idx = 0
        for i, line in enumerate(lines):
            if "step_number" in line.lower() and "step_day" in line.lower():
                header_idx = i
                break
        csv_content = "\n".join(lines[header_idx:])
        
        # Try to fix common CSV issues
        # Replace smart quotes with regular quotes
        csv_content = csv_content.replace('"', '"').replace('"', '"')
        csv_content = csv_content.replace(''', "'").replace(''', "'")
        
        # Parse CSV with more lenient options
        df = None
        parse_error = None
        try:
            # First try: standard pandas CSV parsing (default settings work best for most cases)
            df = pd.read_csv(io.StringIO(csv_content), on_bad_lines='skip')
        except Exception as e1:
            parse_error = str(e1)
            try:
                # Second try: explicitly set quotechar
                df = pd.read_csv(io.StringIO(csv_content), quotechar='"', on_bad_lines='skip')
            except Exception as e2:
                try:
                    # Third try: use engine='python' which is more lenient with malformed CSV
                    df = pd.read_csv(io.StringIO(csv_content), engine='python', on_bad_lines='skip', quotechar='"')
                except Exception as e3:
                    try:
                        # Fourth try: use QUOTE_ALL (quoting=1) which handles all fields
                        df = pd.read_csv(io.StringIO(csv_content), quoting=1, on_bad_lines='skip')
                    except Exception as e4:
                        # If all parsing attempts fail, raise with context
                        raise Exception(f"CSV parsing failed. Last error: {str(e4)}. Raw CSV content (first 500 chars): {csv_content[:500]}")
        
        if df is None or df.empty:
            raise Exception(f"Failed to parse CSV. Error: {parse_error}. Raw CSV content (first 500 chars): {csv_content[:500]}")
        
        # Validate that we captured all steps
        # Count steps in the original sequence using multiple patterns
        step_patterns = [
            r'## Step \d+',
            r'Step \d+:',
            r'Step \d+ ',
            r'Step \d+\.'  # For "Step 1." format
        ]
        step_matches = []
        for pattern in step_patterns:
            matches = re.findall(pattern, sequence, re.IGNORECASE)
            if matches:
                # Extract step numbers from matches
                step_nums = [int(re.search(r'\d+', m).group()) for m in matches if re.search(r'\d+', m)]
                step_matches.extend(step_nums)
        
        sequence_max_step = max(step_matches) if step_matches else 0
        sequence_step_count = len(set(step_matches)) if step_matches else 0
        
        # Count steps in the parsed CSV
        csv_step_count = len(df)
        
        # Check if step_number column exists and validate sequential steps
        if 'step_number' in df.columns:
            max_step = int(df['step_number'].max()) if not df['step_number'].isna().all() else 0
            min_step = int(df['step_number'].min()) if not df['step_number'].isna().all() else 0
            
            # Check for missing steps
            if max_step > csv_step_count:
                st.warning(f"⚠️ **Warning**: CSV has {csv_step_count} rows but step numbers go up to {max_step}. Some steps may be missing.")
            elif sequence_max_step > 0 and max_step < sequence_max_step:
                st.warning(f"⚠️ **Warning**: Sequence has steps up to {sequence_max_step} but CSV only goes up to step {max_step}. Missing steps: {', '.join([str(i) for i in range(max_step + 1, sequence_max_step + 1)])}")
            elif csv_step_count < sequence_step_count:
                st.warning(f"⚠️ **Warning**: Sequence appears to have {sequence_step_count} steps but CSV only has {csv_step_count} rows. Some steps may be missing.")
            
            # Check for gaps in step numbers
            if max_step > 0:
                expected_steps = set(range(min_step, max_step + 1))
                actual_steps = set(df['step_number'].dropna().astype(int))
                missing_steps = expected_steps - actual_steps
                if missing_steps:
                    st.warning(f"⚠️ **Warning**: Missing step numbers in CSV: {', '.join([str(s) for s in sorted(missing_steps)])}")
        
        # Add prospect info columns
        df['email'] = prospect_info.get('email', '')
        df['first_name'] = prospect_info.get('first_name', '')
        df['last_name'] = prospect_info.get('last_name', '')
        df['title'] = prospect_info.get('title', '')
        df['company'] = prospect_info.get('company', '')
        df['sequence_name'] = f"Cursor Outbound - {prospect_info.get('company', 'Unknown')}"
        
        # Reorder columns
        cols = ['email', 'first_name', 'last_name', 'title', 'company', 'sequence_name', 
                'step_number', 'step_day', 'step_type', 'subject', 'body']
        df = df[[c for c in cols if c in df.columns]]
        
        return df
    except Exception as e:
        error_msg = str(e)
        # If it's a model not found error, show available models
        if "404" in error_msg and "models/" in error_msg:
            available_models = list_available_gemini_models()
            if available_models:
                st.error(f"Error parsing sequence to CSV: {error_msg}")
                st.info(f"**Available Gemini models:** {', '.join(available_models)}")
            else:
                st.error(f"Error parsing sequence to CSV: {error_msg}")
                st.info("💡 **Tip**: Try switching to OpenAI in the sidebar, or check your Gemini API key.")
        else:
            st.error(f"Error parsing sequence to CSV: {error_msg}")
            # Show raw CSV content for debugging if available
            if csv_content:
                with st.expander("🔍 Debug: View raw CSV content from AI"):
                    st.code(csv_content, language="text")
                    st.info("💡 **Tip**: The AI may have generated malformed CSV. Try regenerating the sequence or switch to OpenAI provider.")
        return pd.DataFrame()


def render_sidebar():
    """Render the sidebar with navigation and settings."""
    with st.sidebar:
        st.markdown("### Navigation")
        
        if st.button("1. Research Input", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()
        if st.button("2. Hypothesis", use_container_width=True):
            st.session_state.page = "hypothesis"
            st.rerun()
        if st.button("3. Sequence Builder", use_container_width=True):
            st.session_state.page = "sequence"
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Settings")
        
        # Demo mode toggle
        demo_mode = st.checkbox(
            "Demo Mode (No API Required)",
            value=st.session_state.get("demo_mode", False),
            help="Generate sample outputs without API calls. Perfect for testing!"
        )
        st.session_state.demo_mode = demo_mode
        
        if demo_mode:
            st.info("💡 Demo mode enabled - using sample outputs")
        else:
            # AI Provider selection
            provider_options = ["openai"]
            if GEMINI_AVAILABLE:
                provider_options.append("gemini")
            
            current_provider = st.session_state.get("ai_provider", "openai")
            # If Gemini not available and user had it selected, default to OpenAI
            if current_provider == "gemini" and not GEMINI_AVAILABLE:
                current_provider = "openai"
                st.session_state.ai_provider = "openai"
            
            provider = st.radio(
                "AI Provider",
                provider_options,
                index=0 if current_provider == "openai" else 1 if "gemini" in provider_options else 0,
                format_func=lambda x: "OpenAI (GPT-4o)" if x == "openai" else "Google Gemini (Free Tier)",
                help="Gemini free tier: 1,000 requests/day, 5-15 RPM. No credit card required!" if GEMINI_AVAILABLE else "Install google-generativeai package to use Gemini"
            )
            st.session_state.ai_provider = provider
            
            if not GEMINI_AVAILABLE and provider == "gemini":
                st.error("⚠️ Gemini package not installed. Run: pip3 install google-generativeai")
            
            # API Key inputs
            if provider == "openai":
                if not os.getenv("OPENAI_API_KEY"):
                    api_key = st.text_input(
                        "OpenAI API Key",
                        type="password",
                        value=st.session_state.get("openai_api_key", ""),
                        help="Enter your OpenAI API key (get one at platform.openai.com)",
                        key="openai_key_input"
                    )
                    if api_key:
                        st.session_state.openai_api_key = api_key
                        st.success("✅ OpenAI API key set!")
                else:
                    st.success("✅ OpenAI API key loaded from environment")
            else:  # Gemini
                if not os.getenv("GEMINI_API_KEY"):
                    api_key = st.text_input(
                        "Gemini API Key",
                        type="password",
                        value=st.session_state.get("gemini_api_key", ""),
                        help="Get free API key at aistudio.google.com/app/apikey (no credit card required!)",
                        key="gemini_key_input"
                    )
                    if api_key:
                        st.session_state.gemini_api_key = api_key
                        st.success("✅ Gemini API key set!")
                else:
                    st.success("✅ Gemini API key loaded from environment")
                
                st.info("💡 **Gemini Free Tier**: 1,000 requests/day, 5-15 RPM. Great for personal projects!")
                
                # Debug: Show available models
                if st.button("🔍 List Available Models", help="Check which Gemini models are available with your API key"):
                    with st.spinner("Checking available models..."):
                        models = list_available_gemini_models()
                        if models:
                            st.success(f"**Available models:** {', '.join(models)}")
                        else:
                            st.warning("Could not retrieve model list. Check your API key.")
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("Generate Cursor-specific outbound hypotheses and sequences from your research.")
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Reset All", use_container_width=True, help="Clear all data and return to research input"):
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'prospect_info', 'csv_data']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data'] else []
            st.session_state.page = "input"
            st.rerun()


def render_input_page():
    """Screen 1: Research Input"""
    st.title("🎯 Outbound Engine")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Research Input")
        st.markdown("Paste your research below to generate a Cursor-specific outbound hypothesis.")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'prospect_info', 'csv_data']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info'] else None if key in ['hypothesis', 'selected_persona', 'sequence'] else [] if key == 'personas' else None
            st.session_state.page = "input"
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_info = st.text_area(
            "Company Overview",
            placeholder="Paste company info from website, Crunchbase, etc.\n\nInclude: company name, size, industry, funding, tech stack, recent news...",
            height=200,
            value=st.session_state.research_data.get("company_info", "")
        )
        
        job_postings = st.text_area(
            "Relevant Job Postings",
            placeholder="Paste 1-2 relevant job postings\n\nLook for: DevEx, Platform Engineering, Developer Productivity roles...",
            height=200,
            value=st.session_state.research_data.get("job_postings", "")
        )
    
    with col2:
        linkedin_profiles = st.text_area(
            "Target Persona LinkedIn Profiles",
            placeholder="Paste 1-2 LinkedIn profiles of target personas\n\nInclude: name, title, background, recent posts...",
            height=200,
            value=st.session_state.research_data.get("linkedin_profiles", "")
        )
        
        news_signals = st.text_area(
            "Recent News/Signals",
            placeholder="Paste relevant headlines or summaries\n\nLook for: funding rounds, hiring surges, tech blog posts, conference talks...",
            height=200,
            value=st.session_state.research_data.get("news_signals", "")
        )
    
    # Check if API key is configured or demo mode is enabled
    demo_mode = st.session_state.get("demo_mode", False)
    provider = get_ai_provider()
    if provider == "openai":
        has_api_key = bool(os.getenv("OPENAI_API_KEY") or st.session_state.get("openai_api_key"))
    else:
        has_api_key = bool(os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key"))
    can_generate = demo_mode or has_api_key
    
    if not can_generate:
        provider_name = "OpenAI" if provider == "openai" else "Gemini"
        st.warning(f"💡 Enable 'Demo Mode' in the sidebar to test without an API key, or add your {provider_name} API key.")
    
    if st.button("Generate Hypothesis", type="primary", use_container_width=True, disabled=not can_generate):
        # Validate input
        if not any([company_info, job_postings, linkedin_profiles, news_signals]):
            st.error("Please provide at least some research data.")
            return
        
        # Store research data
        st.session_state.research_data = {
            "company_info": company_info,
            "job_postings": job_postings,
            "linkedin_profiles": linkedin_profiles,
            "news_signals": news_signals
        }
        
        # Generate hypothesis
        demo_mode = st.session_state.get("demo_mode", False)
        with st.spinner("Analyzing research and generating hypothesis..." if not demo_mode else "Generating sample hypothesis..."):
            hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
            st.session_state.hypothesis = hypothesis
            
            # Extract personas
            personas = extract_personas_from_hypothesis(hypothesis)
            st.session_state.personas = personas
        
        st.session_state.page = "hypothesis"
        st.rerun()


def render_hypothesis_page():
    """Screen 2: Hypothesis Output"""
    st.title("🎯 Outbound Engine")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Outbound Hypothesis")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'prospect_info', 'csv_data']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data'] else [] if key == 'personas' else None
            st.session_state.page = "input"
            st.rerun()
    
    if not st.session_state.research_data:
        st.warning("No research data found. Please go back and input your research.")
        if st.button("← Back to Input"):
            st.session_state.page = "input"
            st.rerun()
        return
    
    # Show the hypothesis
    if st.session_state.hypothesis:
        st.markdown(st.session_state.hypothesis)
        
        # Show extracted personas
        if st.session_state.personas:
            st.markdown("---")
            st.markdown("#### Extracted Target Personas")
            for i, persona in enumerate(st.session_state.personas, 1):
                st.markdown(f"{i}. **{persona}**")
    else:
        # Generate if not yet done
        demo_mode = st.session_state.get("demo_mode", False)
        with st.spinner("Generating hypothesis..." if not demo_mode else "Generating sample hypothesis..."):
            hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
            st.session_state.hypothesis = hypothesis
            personas = extract_personas_from_hypothesis(hypothesis)
            st.session_state.personas = personas
            st.rerun()
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Back to Input"):
            st.session_state.page = "input"
            st.rerun()
    
    with col2:
        if st.button("Regenerate", use_container_width=True):
            demo_mode = st.session_state.get("demo_mode", False)
            with st.spinner("Regenerating hypothesis..." if not demo_mode else "Regenerating sample hypothesis..."):
                hypothesis = generate_hypothesis(st.session_state.research_data, use_demo=demo_mode)
                st.session_state.hypothesis = hypothesis
                personas = extract_personas_from_hypothesis(hypothesis)
                st.session_state.personas = personas
                st.rerun()
    
    with col3:
        if st.button("Build Sequence →", type="primary"):
            st.session_state.page = "sequence"
            st.rerun()


def render_sequence_page():
    """Screen 3: Sequence Builder"""
    st.title("🎯 Outbound Engine")
    
    # Refresh button at the top
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown("### Sequence Builder")
    with col_refresh:
        if st.button("🔄 Refresh / Start Over", use_container_width=True, help="Clear all data and start fresh"):
            # Clear all session state
            for key in ['research_data', 'hypothesis', 'personas', 'selected_persona', 'sequence', 'prospect_info', 'csv_data']:
                if key in st.session_state:
                    st.session_state[key] = {} if key in ['research_data', 'prospect_info'] else None if key in ['hypothesis', 'selected_persona', 'sequence', 'csv_data'] else [] if key == 'personas' else None
            st.session_state.page = "input"
            st.rerun()
    
    if not st.session_state.hypothesis:
        st.warning("No hypothesis found. Please generate a hypothesis first.")
        if st.button("← Back to Hypothesis"):
            st.session_state.page = "hypothesis"
            st.rerun()
        return
    
    # Prospect information form
    st.markdown("#### Prospect Information")
    st.markdown("Enter details about your target prospect for personalized sequences.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input(
            "First Name",
            value=st.session_state.prospect_info.get("first_name", ""),
            placeholder="John"
        )
        last_name = st.text_input(
            "Last Name",
            value=st.session_state.prospect_info.get("last_name", ""),
            placeholder="Smith"
        )
        email = st.text_input(
            "Email",
            value=st.session_state.prospect_info.get("email", ""),
            placeholder="john.smith@company.com"
        )
    
    with col2:
        company = st.text_input(
            "Company",
            value=st.session_state.prospect_info.get("company", ""),
            placeholder="Acme Corp"
        )
        
        # Persona selection
        personas = st.session_state.personas if st.session_state.personas else ["VP/Director of Engineering", "Platform/DevEx Engineering Lead", "CTO"]
        selected_persona = st.selectbox(
            "Target Persona",
            personas,
            index=0
        )
        
        title = st.text_input(
            "Job Title (optional - defaults to persona)",
            value=st.session_state.prospect_info.get("title", ""),
            placeholder=selected_persona
        )
    
    # Store prospect info
    st.session_state.prospect_info = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company": company,
        "title": title or selected_persona
    }
    st.session_state.selected_persona = selected_persona
    
    st.markdown("---")
    
    # Generate sequence button
    demo_mode = st.session_state.get("demo_mode", False)
    provider = get_ai_provider()
    if provider == "openai":
        has_api_key = bool(os.getenv("OPENAI_API_KEY") or st.session_state.get("openai_api_key"))
    else:
        has_api_key = bool(os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key"))
    can_generate = demo_mode or has_api_key
    
    if st.button("Generate Sequence", type="primary", use_container_width=True, disabled=not can_generate):
        if not first_name or not company:
            st.error("Please provide at least a first name and company.")
        else:
            with st.spinner("Generating personalized sequence..." if not demo_mode else "Generating sample sequence..."):
                sequence = generate_sequence(
                    selected_persona,
                    st.session_state.hypothesis,
                    st.session_state.prospect_info,
                    use_demo=demo_mode
                )
                st.session_state.sequence = sequence
                st.rerun()
    
    # Display generated sequence
    if st.session_state.sequence:
        st.markdown("---")
        st.markdown("#### Generated Sequence")
        st.markdown(st.session_state.sequence)
        
        # Export section
        st.markdown("---")
        st.markdown("#### Export to Outreach.io")
        
        col1, col2 = st.columns(2)
        
        with col1:
            demo_mode = st.session_state.get("demo_mode", False)
            if st.button("Generate CSV Export", use_container_width=True, disabled=demo_mode):
                with st.spinner("Formatting sequence for export..."):
                    df = parse_sequence_to_csv(
                        st.session_state.sequence,
                        st.session_state.prospect_info
                    )
                    if not df.empty:
                        st.session_state.csv_data = df.to_csv(index=False)
                        step_count = len(df)
                        max_step = int(df['step_number'].max()) if 'step_number' in df.columns and not df['step_number'].isna().all() else step_count
                        st.success(f"✅ CSV generated with {step_count} step(s) (up to step {max_step})!")
                        st.dataframe(df, use_container_width=True)
            elif demo_mode:
                st.info("💡 CSV export requires API access. Enable AI mode in sidebar to export.")
        
        with col2:
            if st.session_state.get("csv_data"):
                st.download_button(
                    "Download CSV",
                    data=st.session_state.csv_data,
                    file_name=f"outreach_sequence_{st.session_state.prospect_info.get('company', 'export').replace(' ', '_').lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Back to Hypothesis"):
            st.session_state.page = "hypothesis"
            st.rerun()
    
    with col2:
        if st.session_state.sequence:
            if st.button("Generate for Another Persona", use_container_width=True):
                st.session_state.sequence = None
                st.session_state.csv_data = None
                st.rerun()


def main():
    """Main application entry point."""
    render_sidebar()
    
    # Render current page
    if st.session_state.page == "input":
        render_input_page()
    elif st.session_state.page == "hypothesis":
        render_hypothesis_page()
    elif st.session_state.page == "sequence":
        render_sequence_page()


if __name__ == "__main__":
    main()
