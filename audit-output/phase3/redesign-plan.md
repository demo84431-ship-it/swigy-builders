# FoodDNA Agent — UI Redesign Plan

## Current State → Target State

| Aspect | Current | Target |
|--------|---------|--------|
| Structure | Profile selector → Chat | Hero → How It Works → Live Demo → Profiles → Why Different → CTA |
| Design system | None | Full DESIGN.md (warm, human, editorial) |
| Typography | One font stack | Playfair Display (serif) + Inter (sans) + JetBrains Mono |
| Colors | Orange `#f97316` on dark | Terracotta `#C4654A` on warm canvas `#FAF8F5` |
| Iconography | Emoji 🍕🎉🌙 | Text labels + subtle SVG where needed |
| Accessibility | No ARIA, contrast fails | WCAG AA compliant, ARIA labels, keyboard nav |
| First impression | "What is this?" | "Psychology-first food intelligence — I get it in 10 seconds" |

---

## New Page Structure

### Section 1: Header (64px)
- Left: "FoodDNA" in Playfair Display + terracotta dot
- Right: "How it works" · "Profiles" · "Try Demo" (pill button) · Theme toggle
- Sticky on scroll, white background, bottom border

### Section 2: Hero (80vh)
**Goal**: Explain what FoodDNA is in 10 seconds.

- Kicker: `PSYCHOLOGY-FIRST FOOD INTELLIGENCE` (12px, uppercase, terracotta)
- Headline: `The AI that understands why you eat what you eat` (Playfair Display, 48px)
- Subtitle: `FoodDNA builds behavioral profiles from Swiggy signals — cultural identity, emotional patterns, habit loops, life stage. Not just "what you like" — but "why you eat it, when, and how it connects to who you are."` (Inter, 18px, Text Secondary)
- CTA: "Try the Live Demo" (primary button) · "Read the Research" (ghost button)
- Visual: A stylized "DNA helix" made of food-related words (identity, habit, emotion, culture, region, time, social, health, price, variety) — CSS animation, not image
- Stats strip below: "10 Dimensions · 5 Profiles · 3 MCP Servers · 6 Behavioral Frameworks"

### Section 3: How It Works (auto height)
**Goal**: Show the 3-step pipeline.

3 cards in a row:
1. **Signal** — "Swiggy's 3 MCP servers send behavioral signals — orders, groceries, dining, addresses"
2. **Analyze** — "FoodDNA extracts 10 psychological dimensions using behavioral science frameworks"
3. **Recommend** — "Personalized suggestions that respect your identity, habits, and emotional state"

Each card: number (large, mono, terracotta) + title (Inter 20px 600) + body (Inter 16px)

### Section 4: Live Demo (100vh)
**Goal**: Interactive demo that showcases the psychology differentiator.

Split layout:
- **Left (60%)**: Chat interface (current chat UI, restyled with DESIGN.md)
  - Profile selector integrated as a horizontal strip at top (not a separate screen)
  - 5 profile pills: Arjun · Priya · Riya · Karthik · Mr. Shah
  - Active profile highlighted with terracotta border
  - Chat area below with rich cards
  - Suggestions bar at bottom
- **Right (40%)**: Food DNA sidebar (current sidebar, restyled)
  - Profile avatar + name + tagline
  - 10 dimensions with bars and tooltips
  - Top cuisines, habits, emotional foods
  - "How this profile was built" explanation

Mobile: Stacked (chat on top, DNA below with toggle)

### Section 5: The Profiles (auto height)
**Goal**: Show the diversity of Indian food psychology.

5 profile cards in a grid:
- Each card: avatar (large emoji or SVG) + name + age + city + tagline
- Below: 3 behavioral insights specific to that profile
  - Arjun: "Friday biryani habit · 72% habitual · Comfort food = curd rice"
  - Priya: "Family orders for 5 · Sunday lunch ritual · Mixed dietary household"
  - Riya: "Late-night study fuel · Budget hunter · Egg roll = hostel comfort"
  - Karthik: "Orders for parents in Chennai · Festival sweets · 12,000 km away"
  - Shah: "Jain strict · Diabetic wife · Morning thepla ritual"
- Click to load profile in demo

### Section 6: Why Different (auto height)
**Goal**: Explain the psychology differentiator.

Left: Heading — "Built by a Psychology Master's graduate"
Right: 6 framework cards in 2x3 grid:
1. **Habit Loop** — "Cue → Routine → Reward. We detect your food habits."
2. **Stages of Change** — "Never push health on someone not ready."
3. **Self-Determination** — "Autonomy, not commands. Nudge, not force."
4. **Identity Theory** — "Dietary identity is non-negotiable. A Jain stays Jain."
5. **Behavioral Economics** — "Show savings, not discounts. Frame value, not cheap."
6. **Cultural Psychology** — "Friday biryani. Rain pakora. Festival sweets."

### Section 7: CTA (auto height)
**Goal**: Drive action.

- Headline: "Ready to see your Food DNA?"
- Subtitle: "Connect your Swiggy account or explore with demo profiles."
- Primary CTA: "Try Live Demo" (scrolls to demo section)
- Secondary CTA: "Apply on Swiggy Builders Club" (external link)
- Stats: "5 demo profiles · 10 dimensions · 3 MCP servers"

### Section 8: Footer (80px)
- Left: "FoodDNA Agent · Built for Swiggy Builders Club"
- Right: "GitHub" · "Research" · "Apply"
- Bottom: "Psychology-first. Indian-specific. Identity-respecting."

---

## Technical Implementation

### File Structure (new)
```
food-dna-agent/
├── DESIGN.md              ← NEW (design system)
├── static/
│   └── index.html         ← REBUILT (new page structure)
├── app.py                 ← UPDATED (new API endpoints for sections)
└── profiles/              ← UNCHANGED
```

### CSS Architecture (in index.html)
```
<style>
  /* Design tokens (from DESIGN.md) */
  :root { --canvas: #FAF8F5; --ink: #1A1714; --accent: #C4654A; ... }
  
  /* Reset + base */
  /* Typography (Playfair + Inter + JetBrains Mono via Google Fonts) */
  /* Layout (grid, sections, containers) */
  /* Components (cards, buttons, inputs, badges) */
  /* Chat (messages, rich cards, suggestions) */
  /* Profile sidebar (dimensions, bars, tooltips) */
  /* Responsive (1024, 640 breakpoints) */
</style>
```

### JavaScript Architecture
```
<script>
  // State management (profile, theme, chat history)
  // Profile selector (horizontal pills, not separate screen)
  // Chat (send, receive, rich cards, suggestions)
  // Food DNA sidebar (dimensions, bars, tooltips)
  // Scroll behavior (smooth scroll to sections)
  // Theme toggle (light default, dark optional)
  // Keyboard shortcuts (Enter send, Escape back, 1-5 profile)
</script>
```

### External Dependencies
- Google Fonts: Playfair Display (700), Inter (400/500/600), JetBrains Mono (500)
- No frameworks, no build step, no CDN icons

---

## Success Criteria

- [ ] Swiggy reviewer understands what FoodDNA is within 10 seconds of landing
- [ ] All text passes WCAG AA contrast (4.5:1 minimum)
- [ ] Responsive at 1440w, 768w, 375w
- [ ] Profile selector shows behavioral insights, not just metadata
- [ ] Chat demo works with all 5 profiles
- [ ] Food DNA sidebar explains dimensions with tooltips
- [ ] "How It Works" section shows the 3-step pipeline
- [ ] "Why Different" section shows the 6 psychology frameworks
- [ ] No gradient text, no emoji icons, no AI-slop patterns
- [ ] Warm, human, editorial feel — not a generic dark chat app
