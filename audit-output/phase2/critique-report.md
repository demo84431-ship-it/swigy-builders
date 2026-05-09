# FoodDNA Agent — 5-Dimension Design Critique

> **Reviewed artifact**: `static/index.html` + `app.py` (the deployed demo)
> **Reviewer**: Open Design audit framework
> **Date**: 2026-05-09
> **Verdict**: Strong backend, weak UI. The psychology differentiator is real but the presentation doesn't sell it.

---

## Radar Chart

```
Philosophy    ████████░░  5/10
Hierarchy     ██████░░░░  4/10
Detail        ██████░░░░  4/10
Function      ████████░░  7/10
Innovation    ███████░░░  6/10
──────────────────────────
Mean                       5.2/10
```

---

## Dimension 1: Philosophy Consistency — 5/10

**Score: 5 (Functional but drifting)**

The project has a clear *backend* philosophy — psychology-first, Indian-specific, identity-level modeling. But the UI doesn't express this philosophy. It looks like a generic dark chat app that could be for any AI product.

**Evidence:**
- The tagline "Psychology-First Food Intelligence" appears once in the system message and once in the HTML title. It's not explained, not visualized, not felt.
- The 5 profile cards show avatar emoji + name + tagline, but nothing about *why* this is different. "South Indian IT Professional" could be any food app's persona.
- The Food DNA sidebar shows dimensions (dietary, regional, habit strength) but without context. "Habit Strength: 72%" means nothing to a Swiggy reviewer who hasn't read the research.
- The rich card responses are functional but generic — they look like any chatbot's structured responses, not a psychology-driven system.
- Color choice (orange `#f97316`) has no connection to psychology, food, or Indian culture. It's the default "action color" every AI app uses.

**What would make this an 8:**
- A visual language that says "psychology" — maybe warm, human, editorial (think Claude's parchment, not Linear's dark mode)
- Profile cards that show the *psychology* — "Arjun's Food DNA: 72% habitual, Friday biryani loop detected, comfort food = curd rice"
- A clear narrative arc on the landing: Problem → Psychology approach → Live demo → Why it matters

---

## Dimension 2: Visual Hierarchy — 4/10

**Score: 4 (Broken — everything competes)**

A stranger opening the demo sees: a header with a gradient logo, a grid of emoji cards, and no explanation of what to do or why it matters.

**Evidence:**
- **No hero section.** User lands directly on profile selector. No headline, no value prop, no CTA. The `<h1>` is just "🍕 FoodDNA Agent" — not a value statement.
- **Profile cards compete equally.** All 5 cards are the same size, same weight, same treatment. No visual indication of which to try first. No "recommended" or "most popular" signal.
- **Chat area has no hierarchy.** Messages are all the same size. User messages (orange) and agent messages (dark gray) are the only distinction. Rich cards add visual noise without establishing what's important.
- **Sidebar is flat.** All dimensions are listed vertically with equal weight. "Dietary Identity" and "Habit Strength" get the same visual treatment, but one is a hard filter and the other is a soft signal.
- **Suggestions bar is a row of equal pills.** No priority, no grouping. "Order my usual" and "Surprise me" get the same visual weight, but they represent fundamentally different intents (habit vs exploration).

**What would make this an 8:**
- Hero section with clear value prop: "The first AI that understands *why* you eat what you eat"
- Profile cards with hierarchy: show confidence score prominently, highlight the most interesting profile
- Sidebar with visual hierarchy: dietary identity (hard filter) should be visually dominant, habit strength (soft signal) should be secondary
- Suggestions grouped by intent type: habits vs exploration vs planning

---

## Dimension 3: Detail Execution — 4/10

**Score: 4 (Visible tape and string)**

The details reveal an MVP that was shipped without polish.

**Evidence:**
- **Color contrast fails WCAG AA.** `--text-dim: #888` on `--surface: #1a1a1a` = 3.9:1 ratio. Minimum for normal text is 4.5:1. This is a legal accessibility issue.
- **Typography is one font stack.** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` for everything — headings, body, labels, numbers. No display font, no mono for data, no serif for editorial weight.
- **Spacing is inconsistent.** Profile cards have `padding: 24px` but rich cards have `padding: 16px`. Messages have `padding: 14px 18px`. No rhythm.
- **Emoji as icons.** 🍕🎉🌙🥗🎲 are the primary iconography. On a 4K display, these look like placeholder icons that were never replaced.
- **Gradient text on logo.** `background: linear-gradient(135deg, var(--accent), var(--accent2))` — this is the #1 AI-generated design tell. Every Open Design anti-slop rule flags this.
- **No favicon.** Browser tab shows default blank icon.
- **No meta description.** `<title>` is set but no `<meta name="description">` or OG tags.
- **Profile selector subtitle is generic.** "Choose a profile to explore psychology-first food intelligence" — this doesn't explain what FoodDNA *does*.
- **Rich card actions are inconsistent.** Some have 3 buttons, some have 2, some have 1. No design pattern.

**What would make this an 8:**
- Fix color contrast (minimum 4.5:1 for all text)
- Establish a type scale: display font for headings, body font for text, mono for numbers/data
- Consistent spacing rhythm (8px base unit)
- Replace emoji with proper SVG icons
- Remove gradient text, use solid color or subtle treatment
- Add favicon, meta tags, OG image

---

## Dimension 4: Functionality — 7/10

**Score: 7 (Robust through normal use)**

The demo works. Profile selection, chat, rich cards, suggestions, theme toggle, TTS — all functional. This is the strongest dimension.

**Evidence:**
- **Profile selector works.** 5 cards load from `/api/profiles`, selection triggers `/api/select-profile`, sidebar updates.
- **Chat works.** Messages send, typing indicator shows, rich cards render with action buttons.
- **Rich cards are interactive.** "Order Now" buttons trigger new messages. Options are tappable.
- **Context-aware suggestions.** 6 suggestion sets update based on last message. Simple but functional.
- **Dark/light theme.** Toggle works, persists to localStorage.
- **TTS.** Server-proxied Google Translate TTS with browser fallback. Listen button appears on agent messages.
- **Profile switching.** Back button returns to selector. State resets cleanly.

**What docks points:**
- No error handling for API failures (shows raw error text)
- No loading state when selecting a profile (card click → nothing happens for 500ms → sudden switch)
- TTS proxy is fragile (Google Translate endpoint could be blocked)
- WebSocket endpoint exists but isn't used by the frontend (falls back to HTTP POST)
- No keyboard navigation for profile selection (no Enter key support on cards)

**What would make this a 9:**
- Error boundary with retry UI
- Skeleton loader on profile selection
- Keyboard navigation (Enter to select, Escape to go back)
- Use WebSocket for real-time chat instead of HTTP POST
- Graceful TTS fallback messaging

---

## Dimension 5: Innovation — 6/10

**Score: 6 (Competent and memorable in concept, generic in execution)**

The *idea* is innovative — psychology-first food intelligence, cross-server behavioral fusion, Indian-specific modeling. But the *execution* doesn't show this innovation.

**Evidence:**
- **The psychology differentiator is buried.** A Swiggy reviewer opening the demo sees a chat app. They'd need to read the README or try multiple prompts to understand what makes this different.
- **Profile cards show data, not insight.** "67 data points · 82% confidence" is technical metadata. "Arjun orders masala dosa 12 times a month from Saravana Bhavan — his Friday biryani habit is a weekend celebration ritual" is insight. The UI shows the former, not the latter.
- **Rich cards are generic.** The "Order my usual" response shows a food card with emoji, rating, and delivery time. Every food app does this. What would be innovative: "Your usual masala dosa from Saravana Bhavan — 12 orders this month. Your habit strength is 85%. Want to stick with the routine or explore?"
- **The Food DNA sidebar shows dimensions but doesn't explain them.** "Habit Strength: 72%" — what does this mean? Why should I care? A small tooltip or explanation would make this educational.
- **No visualization of the behavioral model.** The 10 dimensions, the learning rates, the EMA updates — this is the technical innovation, but it's invisible to the user.

**What would make this an 8:**
- Hero section that explains the psychology approach in 10 seconds
- Profile cards that show *behavioral insights*, not just metadata
- Rich cards that reference the Food DNA model: "Based on your emotional pattern (stress level: elevated), here's comfort food"
- A "How Food DNA Works" section or tooltip system
- Visual representation of the 10 dimensions as a radar chart or DNA helix

---

## Keep (Don't Touch)

1. **The 5 profile JSONs** — Rich, diverse, culturally authentic. The data model is excellent.
2. **The 10-dimension Food DNA model** — Psychologically grounded, well-implemented in Python.
3. **The nudge engine's ethical boundaries** — Quiet hours, stress suppression, fatigue limits. This is responsible AI.
4. **The scoring weights** — Dietary as hard filter, regional as strong bias, emotional fit for context. Well-calibrated.
5. **The FastAPI backend architecture** — Clean routes, demo mode fallback, session management.

## Fix (P0/P1 — Must Do)

1. **Create a DESIGN.md** — Define color palette, typography, spacing, components. This is the #1 missing piece.
2. **Fix color contrast** — `#888` on `#1a1a1a` fails WCAG AA. Change `--text-dim` to at least `#a0a0a0`.
3. **Add a hero section** — Explain what FoodDNA is in 10 seconds. "The first AI that understands why you eat what you eat."
4. **Replace emoji icons with SVG** — 🍕🎉🌙🥗🎲 look like placeholders.
5. **Remove gradient text** — Replace with solid color or subtle underline. Anti-slop rule.
6. **Add ARIA labels** — All interactive elements need `aria-label` or `aria-labelledby`.
7. **Add loading states** — Profile selection, chat send, API calls all need feedback.
8. **Establish typography hierarchy** — Display font for headings, body font for text, mono for data.

## Quick Wins (15-30 min each)

1. **Change `--text-dim` from `#888` to `#a0a0a0`** — Fixes contrast, one line change.
2. **Add favicon** — 5 min. Use a food DNA helix emoji or simple SVG.
3. **Add meta description** — `<meta name="description" content="...">` — 2 min.
4. **Improve profile selector subtitle** — "See how AI understands food psychology through real Indian personas" > "Choose a profile to explore psychology-first food intelligence".
5. **Add tooltip to Food DNA dimensions** — Hover on "Habit Strength: 72%" shows "How consistent your ordering patterns are. 72% means you have strong routines with some variety."
6. **Group suggestions by intent** — Separate "habits" (Order my usual, It's Friday) from "explore" (Surprise me, Something healthy) from "plan" (Plan my evening).
7. **Add keyboard shortcuts** — Enter to send, Escape to go back, 1-5 to select profile.
8. **Warm up the color palette** — Orange `#f97316` is generic. Consider a warmer, food-adjacent color like terracotta `#c96442` (Claude's accent) or saffron `#e6a817`.

---

## Summary

| Dimension | Score | Band |
|-----------|-------|------|
| Philosophy | 5/10 | Functional |
| Hierarchy | 4/10 | Broken |
| Detail | 4/10 | Broken |
| Function | 7/10 | Strong |
| Innovation | 6/10 | Functional |
| **Mean** | **5.2/10** | **Functional** |

**The project has a world-class backend and a first-draft UI.** The psychology differentiator is real and well-implemented in code, but the presentation doesn't sell it. A Swiggy reviewer opening the demo would see a generic dark chat app, not a groundbreaking behavioral intelligence system.

**The fix is a proper design system + UI rebuild**, not incremental patches. The backend is ready. The profiles are ready. The demo just needs to *look like* what it *is*.
