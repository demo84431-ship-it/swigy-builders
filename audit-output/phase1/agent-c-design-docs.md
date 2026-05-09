# Agent C: Design, Research & Documentation Audit

## Project Value Proposition
FoodDNA Agent is a **psychology-first AI behavioral intelligence system** for Swiggy's MCP platform. It learns Indian users' food behavior patterns and builds comprehensive "Food DNA" profiles — multi-dimensional psychological fingerprints capturing cultural identity, regional preferences, dietary patterns, temporal rhythms, emotional triggers, and social dynamics.

**Core differentiator**: Built by a Psychology Master's graduate. Treats food as identity, not nutrition.

## Swiggy Application Requirements
- **Track**: Developer
- **MCP Servers needed**: Food, Instamart, Dineout (all 3)
- **Application status**: Pre-submission (needs demo video + client_id)
- **Demo URL**: https://fooddna-agent-01.up.railway.app/
- **GitHub**: https://github.com/demo84431-ship-it/swigy-builders

## Psychology Differentiators (from research)
1. **Food as Identity** — Religious, regional, familial, emotional dimensions (not just taste)
2. **5-Layer Dietary Framework** — Religious → Regional → Family → Temporal → Emotional
3. **6 Behavioral Frameworks** — Habit Loop, SDT, Nudge Theory, Transtheoretical Model, COM-B, Health Belief Model
4. **12 Life-Stage Profiles** — College student to senior citizen, NRI to WFH professional
5. **Indian-Specific Modeling** — Festival calendar, regional cuisine psychology, joint family dynamics
6. **Ethical AI** — Dietary identity never overridden, nudge suppression respects autonomy

## Current Demo Shows
1. Profile selector (5 diverse Indian personas)
2. Chat interface with rich card responses
3. Food DNA sidebar (dietary, regional, habits, emotions)
4. 6 intent types: order usual, Friday biryani, plan evening, healthy, surprise, festival
5. Voice (TTS Listen button)
6. Dark/light theme

## What the Application Form Needs (Not Yet Done)
- ❌ Demo video not recorded
- ❌ Swiggy client_id not obtained
- ❌ Application not submitted
- ✅ Application form answers pre-written (APPLICATION-FORM-ANSWERS.md)

## Documentation Quality

### Strengths
- ✅ Exceptional research foundation (6 research files, 100+ references)
- ✅ Complete taxonomy design (10 dimensions, scoring, profiles)
- ✅ Detailed implementation plan (5 phases, all complete)
- ✅ Pre-written application form answers
- ✅ Comprehensive analysis document

### Weaknesses
- ❌ No DESIGN.md (design system)
- ❌ No style guide or brand identity
- ❌ No UI/UX specifications
- ❌ No component library
- ❌ No accessibility documentation
- ❌ No user testing plan

## Deployment Status
- **Platform**: Railway
- **URL**: https://fooddna-agent-01.up.railway.app/
- **Status**: Live in demo mode
- **Config**: `SWIGGY_CLIENT_ID=YOUR_CLIENT_ID` (demo mode active)
- **When Swiggy approves**: Set real `SWIGGY_CLIENT_ID` in Railway Variables

## Key Gap: No Design System
The project has **world-class research and backend architecture** but **no design system**. The UI was built ad-hoc without:
- Color palette definition
- Typography scale
- Component specifications
- Spacing/layout rules
- Responsive breakpoints
- Accessibility standards
- Brand identity

This is the primary area for improvement.
