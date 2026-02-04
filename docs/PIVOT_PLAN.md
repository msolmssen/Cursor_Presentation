# Pivot Plan: Input Quality + Hypothesis Shape + Sourcing Q&A

This doc captures the pivot away from "company name only" as the next big bet, and toward: (1) refining hypothesis output, (2) better research input, and (3) Q&A about where claims came from. It also spells out why company-name-only can hurt output if we're not careful.

---

## Honest take: Can "company name only" hurt output?

**Short answer: Yes, it can—especially if we dilute or genericize the research that feeds the hypothesis.**

**Why it's risky**

- **Today:** You paste rich, curated research. The model gets exactly what you deemed relevant. Output quality is tightly coupled to that signal.
- **Company-name-only (guided manual):** We'd give links and say "copy 2–3 sentences about the company." If that guidance is generic, you might end up pasting marketing fluff or thin boilerplate instead of engineering/DevEx signals. So we could get *weaker* input and thus weaker hypotheses/sequences unless the prompts for each section are very specific (e.g. "Paste 1–2 sentences on engineering team size or recent eng hiring").
- **Company-name-only (automated):** APIs (Clearbit, job boards, etc.) often return shallow or generic data. Replacing "human chose this paragraph" with "API returned this blob" can easily reduce signal and hurt output. Automation helps only where the source is high-signal and we're confident in the data (e.g. structured job postings).

**Bottom line:** The risk is real. The mitigation is either (a) keep the bar high on what gets pasted (better section prompts/guidance), or (b) only automate where we're confident the source is high-signal. Your pivot toward "better data in research input" (idea 2) is actually the higher-leverage move: improving *input quality* and *what we ask for* beats changing the *entry point* (company name) if the new entry point would lead to noisier or thinner research.

**Recommendation:** Pause company-name-only as the next big feature. Do the three pivots first (hypothesis shape, research input, sourcing Q&A). Revisit company-name-only later—optionally as "company name + much better guided prompts for each section" so we don't dilute signal.

---

## Pivot 1: Refine hypothesis output

**Idea:** The hypothesis structure might not match how you actually use it. Example: "Multi-Threading Strategy" may not be that helpful; other sections might be.

**Current sections (from hypothesis prompt):**

1. Why This Account  
2. Why Now  
3. Who to Target  
4. Multi-Threading Strategy  

**Planning questions**

- Which sections do you *actually* use when you write sequences or decide who to contact?  
- Which do you skim or ignore? (e.g. Multi-Threading)  
- What's missing that you wish you had? (e.g. "One-liner per persona," "Risks / why we might lose," "Key proof points I can reference")

**Options (no implementation yet)**

- **Drop** Multi-Threading (or make it optional) if you don't use it.  
- **Shorten** some sections (e.g. "Who to Target" → bullet one-liners + primary pain + one objection each).  
- **Add** a section you'd use (e.g. "Proof points / evidence to cite" or "Risks").  
- **Reorder** so the most useful section is first (e.g. Why Now before Why This Account if that's how you think).

**Next step:** List "keep / shorten / drop / add" for each current section, then we adjust the hypothesis prompt and any downstream references (e.g. persona extraction) to match.

---

## Pivot 2: Better research input (categories + prompting)

**Idea:** The four buckets (Company Overview, Job Postings, LinkedIn Profiles, News/Signals) are somewhat arbitrary. You want to prompt the app (and yourself) in a way that matches the data you actually use when you build a hypothesis manually.

**Current sections**

- Company Overview  
- Job Postings  
- LinkedIn Profiles (target personas)  
- Recent News/Signals  

**Planning questions**

- When you research a company manually, what do you actually gather? (e.g. "Trigger / why now," "ICP fit," "People/roles," "Proof points I can reference," "Competitive context.")  
- Do the current four map cleanly to that, or would different buckets (or sub-prompts) give the model better signal?  
- For each bucket: what 1–2 sentence instruction would make pasted content higher quality? (e.g. "Paste 1–2 sentences on engineering team size or recent eng hiring" vs "Paste company info.")

**Options (no implementation yet)**

- **Keep four sections** but rename and add very specific sub-prompts per section (so the model gets higher-signal input).  
- **Reshape into different sections** (e.g. "Trigger / Why Now," "Company / ICP Fit," "People / Roles," "Proof Points / Evidence") if that matches your mental model.  
- **Add optional sections** (e.g. "Competitive context" or "Risks") that the hypothesis prompt can use if present.  

**Next step:** You sketch "what I actually use when I research manually" (list or bullets). From that we derive section names + 1–2 sentence prompts per section (and placeholder text for the app). Implementation would then be: update Research Input UI labels + placeholders, and update the hypothesis prompt to reference the new section names/purpose.

---

## Pivot 3: Q&A about hypothesis / sequence (sourcing)

**Idea:** Ask the app where a claim came from. Example: sequence says "aggressive 'platform-ization' strategy" — you want to ask "Where was this sourced from?" and get something you can verify (e.g. "From the Company Overview you pasted: [quote]" or "Inferred from job postings mentioning [X]").

**Why it helps**

- Builds trust: you can check the source.  
- Surfaces hallucination or over-inference: if the model can't point to research, you know to edit or re-paste.  
- Improves iteration: you see which research bits drive which claims, so you can paste better next time.

**Scoping questions**

- **Scope:** Hypothesis only, or sequence too? (Sequence is longer; citing "this line in Email 3" back to research is still doable.)  
- **UX:**  
  - **Option A:** Free-form question box: "Ask about this hypothesis/sequence" and the model answers with citations.  
  - **Option B:** "Cite this" — user selects text (e.g. "aggressive platform-ization") and the app returns "Sourced from: [section] — [quote or 'Inferred from X']".  
  - Option B is more precise; Option A is more flexible.  
- **Context we pass:** Original research (all four sections) + full hypothesis (and sequence if in scope). The model answers using only that context—"where in this research did this claim come from?"—and says "Not in research; inferred" when it's not directly supported.

**Options (no implementation yet)**

- **MVP:** One text area: "Ask about sourcing (e.g. 'Where did the platform-ization claim come from?')" and a button. Response: model gets research + hypothesis (and optionally sequence), returns short answer with section name + quote or "Inferred from X."  
- **Later:** "Cite this" on selection, or multiple questions in one thread.

**Next step:** Decide scope (hypothesis only vs hypothesis + sequence) and UX (free-form vs "Cite this"). Then we can wire one flow: e.g. on Hypothesis page (and optionally Sequence page), add "Ask about sourcing" + endpoint that calls the model with research + hypothesis (and sequence if in scope) and a prompt like "Answer the user's question about where a claim came from. Cite section and quote from the research when possible; otherwise say 'Inferred from [X].'"

---

## Suggested order of work

| Order | Pivot | Why |
|-------|--------|-----|
| 1 | **Pivot 2: Better research input** | Improves signal into the model. Everything downstream (hypothesis, sequence, and eventually sourcing Q&A) benefits. |
| 2 | **Pivot 1: Refine hypothesis output** | Once input is better, shaping the hypothesis (drop/shorten/add sections) makes the output more useful and easier to cite. |
| 3 | **Pivot 3: Sourcing Q&A** | With better input and a refined hypothesis, "where did this come from?" is well-defined and the model has clearer evidence to point to. |

If you'd rather do Pivot 1 before Pivot 2 (hypothesis shape before input categories), that's fine—they're partly independent. Pivot 3 is best after 1 and 2 so citations map to the sections you actually use.

---

## What we're not doing next (for now)

- **Company-name-only** is paused. Revisit after the three pivots, possibly as "company name + much better guided prompts per section" so we don't dilute research quality.

No implementation in this doc—planning only. When you're ready to implement, we can do one pivot at a time and adjust this doc as we go.
