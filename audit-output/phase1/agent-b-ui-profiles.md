# Agent B: UI & Profiles Audit

## Part 1: `static/index.html` — Full Audit

### Structure
- Single file: ~700 lines (HTML + CSS + JS inline)
- No external dependencies (no frameworks, no CDN fonts)
- System font stack only: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

### Design System Issues (Open Design Anti-AI-Slop Check)

| Issue | Severity | Details |
|-------|----------|---------|
| **No DESIGN.md** | P0 | No design system. All colors hardcoded in CSS variables. |
| **Gradient text on logo** | P1 | `background: linear-gradient(135deg, var(--accent), var(--accent2))` on logo — classic AI tell |
| **Orange accent (#f97316)** | P1 | Generic orange. No brand identity. Could be any food app. |
| **Emoji as icons** | P2 | 🍕🎉🌙🥗🎲 used as primary iconography. Looks cheap. |
| **Dark mode default** | P2 | Dark mode as default for a food app is unusual. Food = warm, inviting. |
| **No typography hierarchy** | P1 | All text uses same font stack. No display/body/mono distinction. |
| **Card-heavy layout** | P2 | Every response is a "rich card" — monotonous pattern. |

### Accessibility Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **No ARIA labels** | P0 | Buttons, inputs, cards have no ARIA attributes |
| **No focus management** | P0 | Tab order not managed. No focus trap in chat. |
| **Color contrast** | P1 | `--text-dim: #888` on `--surface: #1a1a1a` = 3.9:1 ratio (fails WCAG AA) |
| **No skip-to-content** | P1 | No keyboard shortcut to jump to chat input |
| **No screen reader support** | P1 | Rich cards are not announced properly |
| **Touch targets** | P2 | `.suggestion` buttons are small on mobile |

### Responsive Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **Profile panel hidden on mobile** | P1 | `.profile-panel { display: none }` at 768px — loses context |
| **No mobile nav** | P1 | Header doesn't collapse on mobile |
| **Profile grid** | P2 | 2-column at 768px, 1-column at 480px — works but cards are wide |
| **Chat input** | P2 | Fixed padding, no safe-area-inset for notch phones |

### UI/UX Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **No onboarding** | P0 | User lands on profile selector with no context about what FoodDNA is |
| **No loading state on profile select** | P1 | No feedback when clicking a profile card |
| **No error handling** | P1 | API errors show raw text, no retry UI |
| **No empty state** | P2 | Chat shows "FoodDNA Agent — Psychology-First Food Intelligence" as system message — not helpful |
| **Suggestions don't adapt well** | P2 | 6 suggestion sets, but the logic is simplistic keyword matching |
| **No back navigation in chat** | P2 | Can't undo/go back after sending a message |
| **Theme toggle placement** | P2 | 🌙 button next to "Connect Swiggy" — competing visual weight |

### Code Quality Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **No build step** | Info | Pure static HTML — fine for demo, limits scalability |
| **Inline styles in JS** | P2 | `demo_response()` returns HTML strings with inline classes — fragile |
| **No CSS methodology** | P2 | BEM-like but inconsistent. Some classes are generic (`.message`, `.card`) |
| **No TypeScript** | Info | Plain JS — acceptable for demo |
| **Global state** | P2 | `sessionId`, `connected`, `activeProfileId` are global variables |

### What Works Well
- Profile selector is clean and functional
- Rich cards show structured data (ratings, prices, action buttons)
- Dark/light theme toggle with localStorage persistence
- Context-aware suggestions (6 sets)
- TTS integration (server proxy + browser fallback)
- Typing indicator animation

---

## Part 2: Profile JSONs — Schema Analysis

### Schema Structure
Each profile has:
- **Identity**: id, name, age, city, origin, avatar, tagline
- **Food DNA (10 dimensions)**: Full data with realistic values
- **Meta**: data_points, confidence_score, user_id, version
- **Sample conversations**: 5 example user→agent exchanges (missing from some profiles)

### Profile Diversity (Excellent)

| Profile | Age | City | Diet | Life Stage | Data Points | Confidence |
|---------|-----|------|------|------------|-------------|------------|
| Arjun | 28 | Bengaluru | Vegetarian | Young Professional | 67 | 82% |
| Priya | 45 | Delhi | Non-Veg | Joint Family | 142 | 91% |
| Riya | 21 | Kolkata | Eggetarian | College Student | 89 | 78% |
| Karthik | 32 | SF (NRI) | Vegetarian | NRI Remote | 45 | 68% |
| Mr. Shah | 68 | Ahmedabad | Jain | Senior Citizen | 203 | 95% |

### Coverage
- ✅ All 5 major regions (South, North, East, West, NRI)
- ✅ All major dietary types (veg, non-veg, eggetarian, Jain)
- ✅ All major life stages (student, professional, family, NRI, senior)
- ✅ Wide age range (21-68)
- ✅ Gender diversity (2 male, 2 female, 1 gender-neutral)
- ✅ Financial range (tight → premium)

### Data Quality
- ✅ Realistic values (not random)
- ✅ Culturally specific comfort/celebration foods
- ✅ Region-appropriate cuisine preferences
- ✅ Life-stage-appropriate ordering patterns
- ⚠️ Some profiles missing `sample_conversations` (Karthik has them, Shah has them)
- ⚠️ Habit strength values are well-calibrated but unvalidated

### What's Missing
- No profile photos (using emoji avatars 🧑‍💻👩‍👧‍👦🎓✈️🧓)
- No profile comparison view
- No profile evolution over time visualization
- No "build your own profile" flow for real users
