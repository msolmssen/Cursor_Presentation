# Sequence Workflow

## Core Sequence (Email + LinkedIn + Call)

Use this as the primary outbound flow. If at any point they accept the LinkedIn connection, continue the core sequence **and** add them to the "LinkedIn only" sequence in parallel.

| Day | Step | Channel | Content |
| :--- | :--- | :--- | :--- |
| **Day 1** | Email | Email | Highly personal technical email. Lead with a POV on their current stack/launch. |
| **Day 1** | LinkedIn connection | LinkedIn | Click "Connect" (no message from GPT). If they accept → add to "LinkedIn only" sequence. |
| **Day 1** | Call attempt | Phone | Opener + voicemail if no answer. |
| **Day 3** | Light bump | Email | Same thread. Light bump. |
| **Day 3** | Call attempt | Phone | Opener + voicemail if no answer. |
| **Day 5** | Slightly more robust | Email | Same thread. Still light but slightly more robust. **[Resource / mixed media – add manually]** |
| **Day 5** | Call attempt | Phone | Opener + voicemail if no answer. |
| **Day 8** | New thread, value | Email | **New email thread.** Pick up on a new or nuanced topic aimed at providing value. |
| **Day 9** | Call attempt | Phone | Opener + voicemail if no answer. |
| **Day 11** | Lighter + resource | Email | Same thread as Day 8. Lighter email. Direct toward website or **[resource – add manually, not same as Day 5]** |
| **Day 12** | Call attempt | Phone | Opener + voicemail if no answer. |
| **Day 15** | Breakup | Email | Kind breakup. See Breakup Rules in voice.md (e.g. "Sounds like timing might not be right… you know where to find me! Hope we connect down the line."). |

### Core sequence rules
- **Same thread** for Day 1 → Day 5; **new thread** for Day 8 onward.
- **Call steps** on Day 1, 3, 5, 9, 12. For each: opener + voicemail if no answer. No long scripts—user uses prior emails as reference.
- **Every email and LinkedIn message must end with a CTA**—question preferred (e.g. "Worth a 15-min call?"), or a soft statement CTA. No step without a CTA; bumps (Day 3, etc.) are no exception.
- **Vary openers**: Do not repeat the same opener phrase in one sequence (e.g. not multiple "I was thinking about..."). Lead with a specific signal or observation from the research.
- Day 5 and Day 11: **placeholder for resource/mixed media**—add manually; Day 11 resource must be different from Day 5. Evolve resource types as you go.
- Breakup: short and sweet, warm, door open. Use voice.md breakup example.

---

## LinkedIn Only Sequence

Use when they have **accepted** the LinkedIn connection. Run in parallel with core sequence if they accept mid-flow. No call steps in LinkedIn-only.

| Day | Step | Content |
| :--- | :--- | :--- |
| **Day 1** | Core message | "Hey [Name], great to be connected! Noticed/reaching out because..." |
| **Day 3** | Bump + CTA | Similar content to Day 1 but slightly nuanced. Include CTA. |
| **Day 5** | Super light bump | "Circling back here..." |
| **Day 9** | Super light touch | Another super light touch. More of a statement than a question. **LinkedIn breakup option**: "Any thoughts, [Name]?" |

### LinkedIn-only rules
- Keep tone conversational and light.
- **Every message must have a CTA**—Day 3 = bump + CTA; Day 5 and 9 = light touch but still end with a question or soft CTA (e.g. "Any thoughts?" "Worth a quick look?").
- Day 1 = core message ("Hey [Name], great to be connected! Noticed/reaching out because..."); Day 3 = bump + CTA; Day 5 and 9 = very light, low pressure.
- Final touch (Day 9) can be simple sign-off: "Any thoughts, [Name]?"

---

## Flow logic

- **Core sequence**: Always run. Day 1 = email + LinkedIn "Connect" (no connection request copy from GPT—just click connect). Call steps on Day 1, 3, 5, 9, 12.
- **LinkedIn only sequence**: **Generate by default** alongside the core sequence. No call steps. Use when they've accepted (or will accept). If they accept mid-flow, run LinkedIn-only in parallel from that point.
- When generating a sequence, **always output both**: (1) core email + call sequence, (2) LinkedIn-only sequence. User adds connection manually; no GPT copy needed for the connect button.
