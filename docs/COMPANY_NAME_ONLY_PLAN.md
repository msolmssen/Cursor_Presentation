# Company-Name-Only Starting Point — Plan

This doc outlines how we'll tackle the "company name only" starting point (V2.1): user enters a company name (and optionally domain), and the app points them at the right sources—or eventually fetches from them—so research is structured and repeatable instead of fully manual paste.

---

## Step 1: Test current app with updated knowledge base

**Goal:** Validate that the current iteration works end-to-end with the new KB and that outputs match your voice, offers, and sequence structure.

**What to do:**

1. **Run the app**
   - From project root: `streamlit run app.py` (or your usual run command).
   - Ensure API key is set (OpenAI or Gemini) or use Demo Mode for structure-only check.

2. **Run one full flow (research → hypothesis → sequence)**
   - **Research Input:** Paste real research into all four sections (Company Overview, Job Postings, LinkedIn Profiles, News/Signals) for a company you know well—e.g. a prospect or a company you’ve already researched.
   - **Generate Hypothesis:** Click through and review the hypothesis. Check that it uses Cursor-specific angles (from `cursor_encyclopedia`) and personalization-style thinking (from `personalization_playbook`).
   - **Sequence Builder:** Enter a prospect (name, company, persona). Generate sequence. Review:
     - **Voice:** Two-paragraph rule, softeners, POV over pitch, your CTAs, tone constraints (no “revolutionary,” etc.).
     - **Subject lines:** Lowercase, not salesy, map to content (e.g. “coinbase's developer velocity strategy” style).
     - **Structure:** Core sequence (Day 1 email + Day 1 LinkedIn “connect”, Day 3, 5, 8, 11, 15) and LinkedIn-only sequence (Day 1, 3, 5, 9).
     - **Offers:** Persona-to-offer map reflected (VP Eng vs Platform/DX vs CISO vs Architect).
     - **Breakup:** Email breakup sounds like your example (“sounds like timing might not be right… you know where to find me”); LinkedIn “Any thoughts, [Name]?” where relevant.
     - **Placeholders:** Resource slots (Day 5, Day 11) and P.S. called out for manual fill where appropriate.

3. **Note gaps**
   - If anything doesn’t match the KB (voice, structure, subject lines, breakup, offers), write down:
     - What you expected (from which KB file).
     - What the app generated.
   - This list will inform whether we need to tighten prompts or KB wording before changing the input flow.

4. **Optional: second company**
   - Run the same flow for another company to confirm consistency.

**Done when:** You’ve run at least one full flow, confirmed KB is driving outputs, and have a short list of any prompt/KB tweaks (if needed). No code changes required in this step—purely validation.

---

## Step 2: Define source packs and research flow

**Goal:** Decide what “the right sources” means for your workflow and how much is guided manual vs automated.

**What to do:**

1. **List sources you use today**
   - Company: website, Crunchbase, LinkedIn company page, G2/Capterra, etc.
   - Jobs: LinkedIn Jobs, company careers page, Greenhouse/lever, etc.
   - People: LinkedIn (target personas), maybe Apollo/Clay.
   - News/signals: Google News, company blog, Twitter, funding databases, etc.

2. **Define 1–3 “source packs”**
   - Pack A (e.g. “Standard”): Company site + company LinkedIn + 1–2 job postings + recent news (headlines/summaries).
   - Pack B (e.g. “Deep”): Everything in A + G2/reviews + engineering blog + funding round.
   - Pack C (e.g. “Light”): Company site + one job posting + one news headline.
   - Each pack maps to the same four research buckets we have today: company_info, job_postings, linkedin_profiles, news_signals (or we keep that structure so hypothesis/sequence code doesn’t change).

3. **Decide manual vs automated (for later)**
   - **Manual:** User gets a checklist + links (e.g. “Company: [company name] — go to [link], copy overview into Company Overview”).
   - **Automated:** We call APIs (e.g. Clearbit, LinkedIn, job boards) and pre-fill sections where we have keys and rate limits.
   - **Hybrid (recommended):** Start with guided manual (Step 4); add 1–2 automated sources in a later step if useful (e.g. company domain → fetch homepage summary, or job API for “Job Postings”).

**Done when:** You have 1–3 named source packs and a clear “manual first, automate where it’s easy” stance.

---

## Step 3: Design the new input flow (company name first)

**Goal:** One clear path: company name (and optional domain) → research → hypothesis → sequence, with minimal change to existing hypothesis/sequence logic.

**What to do:**

1. **New Step 0: Company**
   - Single required field: **Company name** (e.g. “Stripe”, “Acme Corp”).
   - Optional: **Company domain** (e.g. “stripe.com”) for link-building and future APIs.
   - Optional: **Source pack** choice (e.g. “Standard” / “Deep” / “Light”) if you defined multiple packs.
   - No research text areas on this screen—just company identity + pack choice.

2. **Step 1: Research (guided)**
   - Same four sections as today (Company Overview, Job Postings, LinkedIn Profiles, News/Signals).
   - Add a **guided research panel** (collapsible or sidebar) that shows, for the chosen pack:
     - For each section: “Go here: [link]” and “Copy: [what to copy]” and “Paste below.”
     - Links are built from company name/domain where possible (e.g. “https://www.[domain]”, “https://www.linkedin.com/company/[slug]”, “https://www.google.com/search?q=[company]+news”).
   - User still pastes into the four boxes; we’re just telling them exactly where to look and what to paste.

3. **Keep existing flow**
   - “Generate Hypothesis” still reads the four research fields.
   - Hypothesis → personas → Sequence Builder unchanged.
   - So we’re only changing “how research is gathered” (company-first + guidance), not the downstream app logic.

4. **Optional: “Save research for [company]”**
   - If we add caching later, we’d key it by company name/domain so re-opening that company or adding another prospect there reuses research.

**Done when:** You have a clear spec: “Screen 0 = company + pack; Screen 1 = guided links + same four paste areas; rest unchanged.”

---

## Step 4: Implement guided research (company name + links)

**Goal:** Ship the UX improvement with minimal risk: company name (and optional domain) first, then a guided checklist with links—no new APIs yet.

**What to do:**

1. **Add company step (or fold into input page)**
   - Option A: New “Step 0” page: Company name, optional domain, optional source pack dropdown. “Next” goes to Research Input with these stored in session (and optionally in a `research_context` or `company` object).
   - Option B: Research Input page gets a top section: “Start with company: [text input] [optional domain] [pack dropdown].” When company/domain is set, show the guided panel below.

2. **Build “guided research” panel**
   - For the selected (or default) source pack, render a checklist:
     - **Company Overview:** “1. Open [company website from domain or search]. 2. Copy 2–3 sentences on what they do, size, and tech. 3. Paste in ‘Company Overview’ below.”
     - **Job Postings:** “1. Open [LinkedIn Jobs link for company] or [company careers URL]. 2. Copy 1–2 relevant job posts (DevEx, Platform, Engineering). 3. Paste below.”
     - **LinkedIn Profiles:** “1. Open LinkedIn, search company + title (e.g. VP Engineering). 2. Copy name, title, 1–2 lines from profile or a recent post. 3. Paste below.”
   - Links: use domain when available (e.g. `https://{domain}`); otherwise “Google: [company name]” or a search URL. Keep it simple.

3. **Wire company name/domain through**
   - Store `company_name` and `company_domain` in session so hypothesis/sequence can use them (e.g. in prompts or in “Company” field). No change to `research_data` keys if we keep the same four fields.

4. **Test**
   - Run flow: enter company name (and domain), use guided links to paste research, generate hypothesis, build sequence. Confirm behavior matches current app except for the new entry point and guidance.

**Done when:** User can start from company name (and optional domain), see a clear “go here / copy this / paste here” for each research section, and complete the same hypothesis → sequence flow as today.

---

## Step 5 (Optional): Add one automated source

**Goal:** If it’s quick and reliable, auto-fill one research section (e.g. company overview or job snippets) so the user has less to paste.

**What to do:**

1. **Pick one source**
   - Example: Company domain → fetch homepage or “About” text (e.g. via a simple scraper or an API like Clearbit).
   - Or: Company name → fetch recent headlines (e.g. Google News RSS or a news API) into “News/Signals.”
   - Constraint: Use only APIs/keys you already have or are willing to add; respect rate limits and errors (show “Couldn’t fetch; please paste manually”).

2. **Implement behind a feature flag or optional “Fetch” button**
   - e.g. “Fetch company overview” next to Company Overview that fills the box if we have domain; otherwise show “Add domain to enable.”
   - Don’t remove the manual paste option—automation is an assist.

3. **Handle failures**
   - Timeouts, 403, no key → fall back to “Please paste manually” and keep the guided links.

**Done when:** One section can be auto-filled when conditions are met, with a clear fallback to manual paste and guided links.

---

## Step 6 (Optional): Cache research by company

**Goal:** If the user researches “Stripe” once, the next time they enter “Stripe” (or add another prospect at Stripe), we can offer to reuse the last research so they don’t re-paste.

**What to do:**

1. **Decide storage**
   - In-memory (session): reuse within the same session only.
   - Or simple file/db keyed by company name or domain: e.g. `research_cache/stripe_com.json` with the four fields and a timestamp.

2. **UI**
   - When user enters a company name/domain we’ve seen before: “We have research for [company] from [date]. Use it / Edit it / Start fresh.”

3. **Invalidation**
   - “Start fresh” or “Edit” overwrites cache for that company. Optional: TTL (e.g. reuse only if cached within 7 days).

**Done when:** Re-entering the same company (or adding another prospect there) can reuse cached research, with the option to edit or start over.

---

## Order of work (summary)

| Step | What | Owner |
|------|------|--------|
| **1** | Test current app with updated KB (full flow, check voice/structure/placeholders) | You |
| **2** | Define source packs and manual vs automated | You (+ optional pairing) |
| **3** | Design new input flow (company first, then guided research) | You / dev |
| **4** | Implement guided research (company name + links, same four sections) | Dev |
| **5** | (Optional) Add one automated source | Dev |
| **6** | (Optional) Cache research by company | Dev |

Step 1 is validation only. Steps 2–3 are design. Step 4 is the main UX win. Steps 5–6 are incremental improvements once the new flow is in place.
