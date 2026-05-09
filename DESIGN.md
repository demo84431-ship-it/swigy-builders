# FoodDNA Agent — Design System

> Category: AI & Food Intelligence
> Psychology-first behavioral intelligence for Indian food. Warm, human, clear.

## 1. Visual Theme & Atmosphere

FoodDNA is about understanding *why* people eat what they eat — identity, emotion, culture, habit. The visual language must feel warm and human, not cold and technical. This is not a dashboard. It's a conversation about food psychology.

**Key Characteristics:**
- Warm canvas (`#FAF8F5`) evoking quality paper, not screens
- Terracotta accent (`#C4654A`) — earthy, food-adjacent, deliberately un-tech
- Serif display font (Playfair Display) for headlines — editorial gravitas
- Sans body font (Inter) for UI — clean, readable, modern
- Mono font (JetBrains Mono) for data/numbers — precision without coldness
- Warm-toned neutrals — every gray has a yellow-brown undertone
- Generous whitespace — let the content breathe
- Single accent, used sparingly — at most 2x per screen
- No gradients, no glassmorphism, no dark mode by default

**What this is NOT:**
- Not a dark-mode chat app (food is warm, not cold)
- Not a generic AI interface (this has a specific personality)
- Not a dashboard with 15 charts (this is a conversation)
- Not Indian-flag-saffron (subtle, not cliché)

## 2. Color Palette & Roles

### Primary
- **Canvas** (`#FAF8F5`): Page background. Warm off-white with yellow undertone. Like quality paper.
- **Ink** (`#1A1714`): Primary text. Warm near-black, not pure black.
- **Terracotta** (`#C4654A`): Brand accent. Primary CTAs, active states, emphasis. Earthy, warm, food-adjacent.
- **Terracotta Light** (`#E8A898`): Hover states, subtle highlights, progress bars.

### Surface
- **Surface** (`#FFFFFF`): Cards, modals, elevated containers.
- **Surface Warm** (`#F5F2EE`): Secondary surfaces, sidebar background, input backgrounds.
- **Surface Hover** (`#EDE9E3`): Hover states on cards and interactive elements.

### Text
- **Text Primary** (`#1A1714`): Headings, body text, strong labels.
- **Text Secondary** (`#6B6560`): Descriptions, captions, muted labels.
- **Text Tertiary** (`#9B9590`): Placeholders, disabled states, metadata.
- **Text On Accent** (`#FFFFFF`): Text on terracotta backgrounds.

### Borders
- **Border** (`#E8E4DF`): Standard borders, dividers.
- **Border Subtle** (`#F0EDE8`): Hairline borders, card outlines.

### Semantic
- **Success** (`#2D8A56`): Positive states, "live" indicators.
- **Warning** (`#D4880F`): Caution, "stale" indicators.
- **Error** (`#C44040`): Errors, destructive actions.
- **Info** (`#4A7FB5`): Informational, links.

### Psychology-Specific Colors (for Food DNA dimensions)
- **Dietary** (`#2D8A56`): Green — identity, non-negotiable.
- **Regional** (`#C4654A`): Terracotta — cultural roots.
- **Temporal** (`#4A7FB5`): Blue — time, rhythm.
- **Emotional** (`#D4880F`): Amber — warmth, feeling.
- **Habit** (`#7B61A8`): Purple — patterns, repetition.

## 3. Typography Rules

### Font Families
- **Display**: `'Playfair Display', Georgia, 'Times New Roman', serif`
- **Body**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif`
- **Mono**: `'JetBrains Mono', 'SF Mono', 'Menlo', monospace`

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing | Usage |
|------|------|------|--------|-------------|----------------|-------|
| Hero Title | Playfair Display | 48px (desktop) / 32px (mobile) | 700 | 1.10 | -0.02em | Main headline |
| Section Title | Playfair Display | 32px / 24px | 700 | 1.20 | -0.01em | Section headings |
| Card Title | Inter | 20px | 600 | 1.30 | normal | Card headings |
| Body Large | Inter | 18px | 400 | 1.60 | normal | Intro paragraphs |
| Body | Inter | 16px | 400 | 1.50 | normal | Standard text |
| Body Small | Inter | 14px | 400 | 1.50 | normal | Secondary text |
| Caption | Inter | 12px | 500 | 1.40 | 0.02em | Labels, metadata |
| Data | JetBrains Mono | 14px | 500 | 1.40 | normal | Numbers, metrics |
| Kicker | Inter | 12px | 600 | 1.40 | 0.08em | Overlines, categories |

### Principles
- **Serif for personality, sans for utility.** Playfair Display carries the editorial weight. Inter handles everything functional.
- **Mono for data.** Numbers, percentages, metrics always use JetBrains Mono with `font-variant-numeric: tabular-nums`.
- **No italic.** Emphasis uses terracotta color or weight change, not italic.
- **ALL CAPS only for kickers.** 12px, 600 weight, 0.08em letter-spacing. Never for body text.

## 4. Component Stylings

### Buttons
- **Primary**: Terracotta (`#C4654A`) background, white text, 8px radius, 12px 24px padding. Hover: `#A8503A`.
- **Secondary**: Transparent background, 1px border (`#E8E4DF`), ink text, 8px radius. Hover: border terracotta.
- **Ghost**: No background, no border, terracotta text. Hover: underline.
- **Pill**: 9999px radius, used for suggestion chips and tags.

### Cards
- White background, 1px border (`#E8E4DF`), 12px radius, 24px internal padding.
- No shadow by default. Hover: subtle shadow `0 2px 8px rgba(26,23,20,0.06)`.
- Accent card: Left border 3px terracotta (used for active/selected states).

### Inputs
- Surface Warm (`#F5F2EE`) background, 1px border (`#E8E4DF`), 8px radius.
- Focus: border terracotta, no box-shadow.
- Placeholder: Text Tertiary (`#9B9590`).

### Chat Messages
- User: Terracotta background, white text, 16px radius, bottom-right 4px.
- Agent: Surface background, 1px border, 16px radius, bottom-left 4px.
- System: No background, centered, Text Secondary color, 13px.

### Profile Cards
- White background, 1px border, 16px radius, 24px padding.
- Hover: border terracotta, translateY(-2px), subtle shadow.
- Active: 3px left border terracotta.

### Rich Cards (Food Recommendations)
- White background, 1px border, 12px radius.
- Header: food emoji (large) + title + subtitle.
- Meta: pill badges with Surface Warm background.
- Actions: Primary + Secondary buttons in a flex row.

### Food DNA Dimensions
- Label: 12px Inter 500, uppercase, 0.05em tracking, Text Secondary.
- Value: 16px Inter 600, Text Primary.
- Bar: 6px height, Surface Warm background, terracotta fill.
- Tooltip: On hover, shows explanation text.

## 5. Layout Principles

### Spacing System
- Base unit: 8px
- Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96
- Section spacing: 96px (desktop), 64px (tablet), 48px (mobile)

### Grid
- Max width: 1200px centered
- 12-column grid on desktop, 8 on tablet, 4 on mobile
- Gutter: 24px

### Page Structure (New UI)
```
┌─────────────────────────────────────────────┐
│ Header: Logo + Nav + Theme Toggle           │ 64px
├─────────────────────────────────────────────┤
│ Hero: Value prop + CTA + Visual             │ 80vh
├─────────────────────────────────────────────┤
│ How It Works: 3 steps with icons            │ auto
├─────────────────────────────────────────────┤
│ Live Demo: Profile selector + Chat + DNA    │ 100vh
├─────────────────────────────────────────────┤
│ Profiles: 5 cards with behavioral insights  │ auto
├─────────────────────────────────────────────┤
│ Why Different: Psychology frameworks        │ auto
├─────────────────────────────────────────────┤
│ CTA: Apply / Connect                        │ auto
├─────────────────────────────────────────────┤
│ Footer                                      │ 80px
└─────────────────────────────────────────────┘
```

### Whitespace Philosophy
- Sections separated by generous padding, not dividers.
- Cards have breathing room (24px gap minimum).
- The canvas color (#FAF8F5) provides natural separation between white cards.

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (0) | No shadow, canvas background | Page background |
| Surface (1) | White background + 1px border | Cards, inputs |
| Hover (2) | `0 2px 8px rgba(26,23,20,0.06)` | Interactive hover |
| Elevated (3) | `0 4px 16px rgba(26,23,20,0.08)` | Dropdowns, modals |
| Floating (4) | `0 8px 32px rgba(26,23,20,0.12)` | Tooltips, popovers |

No glassmorphism. No neumorphism. Depth comes from borders and subtle shadows.

## 7. Do's and Don'ts

### Do
- ✅ Use terracotta sparingly — at most 2 elements per screen
- ✅ Let whitespace do the work — don't fill every pixel
- ✅ Use serif for headlines, sans for body — clear hierarchy
- ✅ Use mono for all numbers and data
- ✅ Write copy that explains the psychology, not just the features
- ✅ Warm neutrals everywhere — no cool grays
- ✅ `font-variant-numeric: tabular-nums` on all number displays

### Don't
- ❌ No gradient text (anti-slop rule #1)
- ❌ No emoji as primary iconography — use SVG or text
- ❌ No dark mode as default — food is warm
- ❌ No cyan-on-dark, no purple-to-blue gradients (anti-AI tells)
- ❌ No "10× faster" / "infinite" / "revolutionary" copy
- ❌ No more than 2 accent elements per screen
- ❌ No cool blue-grays — every neutral must be warm-shifted

## 8. Responsive Behavior

| Breakpoint | Width | Changes |
|------------|-------|---------|
| Desktop | ≥1024px | 12-col grid, sidebar visible, 2-col layouts |
| Tablet | 640–1023px | 8-col grid, sidebar hidden, stacked layouts |
| Mobile | <640px | 4-col grid, single column, compact spacing |

- Hero title: 48px → 36px → 28px
- Section padding: 96px → 64px → 48px
- Profile grid: 3-col → 2-col → 1-col
- Chat: full width on all breakpoints
- Sidebar: hidden on tablet/mobile (accessible via toggle)

## 9. Agent Prompt Guide

### Quick Color Reference
- Canvas: `#FAF8F5`
- Ink: `#1A1714`
- Accent: `#C4654A` (terracotta)
- Surface: `#FFFFFF`
- Surface Warm: `#F5F2EE`
- Border: `#E8E4DF`
- Text Primary: `#1A1714`
- Text Secondary: `#6B6560`
- Text Tertiary: `#9B9590`

### Example Component Prompts
- "Design a hero section on `#FAF8F5` canvas. Headline in Playfair Display 48px weight 700, line-height 1.10, color `#1A1714`. Subtitle in Inter 18px weight 400, color `#6B6560`. Primary CTA button: `#C4654A` background, white text, 8px radius."
- "Build a profile card: white background, 1px `#E8E4DF` border, 16px radius, 24px padding. Name in Inter 20px weight 600. Tagline in Inter 14px, `#6B6560`. Hover: border shifts to `#C4654A`."
- "Create a Food DNA dimension bar: label in Inter 12px weight 500 uppercase, 0.05em tracking, `#6B6560`. Value in JetBrains Mono 14px weight 500. Bar: 6px height, `#F5F2EE` background, `#C4654A` fill."

### Iteration Guide
1. Start with canvas (#FAF8F5) and ink (#1A1714) — these never change
2. Use terracotta (#C4654A) only for CTAs and active states — don't flood
3. All neutrals must be warm-shifted — no `#gray` values with blue undertone
4. Serif for personality (headlines), sans for utility (body), mono for data
5. Spacing rhythm: 8px base, 24px for cards, 48px for sections, 96px for page sections
