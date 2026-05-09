# Food DNA Agent — Phase 4: Demo & Application

> **Project**: Food DNA Agent (Swiggy Builders Club)
> **Phase**: 4 — Demo & Application
> **Date**: 2026-05-09
> **Status**: In Progress

---

## A. Demo Strategy

### What Makes This Demo Stand Out

Most Swiggy Builders Club applicants will show: "User says X → Agent orders food." That's table stakes.

Our demo shows something different — **the psychology behind the recommendation**. We don't just say "order biryani." We show *why* biryani, *how* the agent knew, and *what psychological framework* drove the decision. This is what a Psychology Master's graduate brings to the table.

### Demo Philosophy

```
Other agents: "Here are 5 restaurants near you."
FoodDNA: "It's Friday evening. You have a Friday biryani habit — 
          this is your weekend celebration ritual. Your usual from 
          Meghana Foods? Or want to try the new Hyderabadi place 
          that just opened in Koramangala?"
```

The difference: **psychological reasoning is visible**.

---

## B. Five Demo Scenarios

### Scenario 1: "Order My Usual" — Behavioral Lookup
**User**: "Order my usual"
**What happens internally**:
1. Agent fetches Food DNA profile
2. Habit profile shows: `overall_habit_strength: 0.72`, top item "Masala Dosa" (12 orders), top restaurant "Saravana Bhavan" (18 orders)
3. Dietary identity: vegetarian (hard filter — never suggests non-veg)
4. Time context: 8:30 AM → breakfast window
5. Decision: High habit strength → suggest "your usual" directly

**Agent response** (voice):
> "Your usual masala dosa from Saravana Bhavan? Want me to order that?"

**Agent response** (chat):
> 🍽️ **Your usual**
>
> **Masala Dosa** from **Saravana Bhavan**
> Based on your ordering pattern — you love this! 12 orders in the past month.
>
> Shall I add it to your cart?

**Psychology shown**: Habit loop reinforcement (Duhigg). The agent identifies the CUE (morning), ROUTINE (masala dosa), and REWARD (familiar taste, energy). It doesn't suggest alternatives because habit strength is high.

---

### Scenario 2: "It's Friday" — Proactive Biryani Suggestion
**User**: "It's Friday"
**What happens internally**:
1. Day = Friday (weekday 4), Hour = 19:00
2. `day_distribution[4]` = 0.22 (>0.15 threshold → heavy Friday orderer)
3. Habit detection: `temporal_habits` includes "friday" with strength 0.8
4. Cuisine check: `north_indian` affinity = 0.35, has "biryani" in `recurring_items`
5. Time check: 7 PM > 5 PM → evening window (biryani time)
6. Decision: Friday biryani habit detected → proactive suggestion

**Agent response** (voice):
> "Friday vibes! Your usual biryani from Meghana Foods? Want me to order?"

**Agent response** (chat):
> 🎉 **It's Friday!**
>
> Your usual **biryani** — because Friday deserves a celebration.
> This is your weekend reward ritual — 4 consecutive Fridays of biryani!
>
> Shall I order from Meghana Foods?

**Psychology shown**: Habit loop theory + cultural psychology. Friday biryani is one of the strongest food habits in Indian culture — it's a weekend celebration ritual. The agent doesn't just suggest food; it acknowledges *why* (reward-seeking, weekend transition).

---

### Scenario 3: "Plan My Evening" — Cross-Server Fusion
**User**: "Plan my evening"
**What happens internally**:
1. Agent checks Dineout server: `search_restaurants_dineout` → finds "Barbeque Nation" with 4.5⭐, 7:30 PM slot available
2. Agent checks Food DNA: `social_dynamics.family_ratio = 0.65` → family dining preferred
3. Agent checks Food server: top restaurant from habit profile for food delivery backup
4. Agent cross-references: Barbeque Nation has both Dineout presence AND delivery
5. Decision: Present both options — dineout experience OR home delivery

**Agent response** (chat):
> 🌙 **Your evening plan:**
>
> **Option 1: Dine out**
> 🍽️ **Barbeque Nation** — 4.5⭐
>    Table for 4 available at 7:30 PM
>    Family dinner buffet — ₹799 per person
>
> **Option 2: Order in**
> 🍕 **Meghana Foods** — Your usual biryani
>    Delivered by 8:15 PM · ₹280
>
> Which sounds better for tonight?

**Psychology shown**: Cross-server intelligence (Food + Dineout fusion). The agent uses social dynamics profiling to detect this is a family context, then offers both dineout and delivery options. No other agent can do this because they don't have access to both servers.

---

### Scenario 4: Restaurant Closed — Error Recovery
**User**: "Order from Paradise Biryani"
**What happens internally**:
1. Agent calls `search_restaurants("Paradise Biryani")` → `availabilityStatus: "CLOSED"`
2. Error recovery triggers
3. Agent checks Food DNA: closed restaurant's cuisine = "north_indian", item = "biryani"
4. Agent searches for similar restaurants: filters by same cuisine + open status
5. Scores alternatives using Food DNA weighted scoring:
   - Regional affinity (0.20): north_indian match
   - Habit reinforcement (0.15): similar to usual
   - Price fit (0.10): within budget range
6. Decision: Suggest top 3 similar alternatives, not random ones

**Agent response** (chat):
> 😔 **Paradise Biryani is closed right now.**
>
> But here are similar options based on your taste:
>
> **1. Meghana Foods** — Biryani, ₹280 · 30-40 min
>    _Similar to Paradise — same Hyderabadi style_
>
> **2. Biryani By Kilo** — Biryani, ₹320 · 35-45 min
>    _Dum biryani, sealed handi — premium experience_
>
> **3. Behrouz Biryani** — Biryani, ₹250 · 25-35 min
>    _Lucknowi style — different but delicious_
>
> Want me to order from one of these?

**Psychology shown**: Error recovery with intelligence. Instead of random alternatives, the agent uses Food DNA to find psychologically similar options — same cuisine, comparable price, familiar comfort. The reasoning is visible ("Similar to Paradise — same Hyderabadi style").

---

### Scenario 5: "Diwali Tomorrow" — Festival Awareness
**User**: "Diwali is tomorrow"
**What happens internally**:
1. Festival calendar match: `FESTIVAL_CALENDAR["diwali"]` → foods: ["mithai", "namkeen", "dry_fruits"]
2. Dietary identity filter: user is vegetarian → all festival foods are compliant
3. Regional identity: south_indian → suggest region-appropriate sweets
4. Price sensitivity adjustment: festival = `price_sensitivity_drop: 0.3` (spending tolerance increases)
5. Social context: `family_ratio = 0.65` → family celebration
6. Decision: Festival-aware suggestion with regional + dietary compliance

**Agent response** (chat):
> 🪔 **Diwali Special!**
>
> Traditional **Mithai**, **Namkeen**, and **Dry Fruits** — perfect for the celebration.
>
> Based on your South Indian background:
> 🍬 **Mysore Pak** from Sri Krishna Sweets — ₹350
> 🍬 **Kaju Katli** from Haldiram's — ₹280
> 🥜 **Dry Fruit Mix** from Instamart — ₹180
>
> Shall I order sweets for the family?

**Psychology shown**: Cultural psychology + festival food calendar. Indian festivals have non-negotiable food associations — Diwali = mithai, Holi = gujiya, Onam = sadya. The agent proactively suggests festival-appropriate food, filtered by dietary identity and regional preference. Price sensitivity drops during festivals (celebration budget).

---

## C. Demo Video Script (3 Minutes)

### Structure

```
[0:00-0:15]  INTRO — What is FoodDNA?
[0:15-0:45]  SCENARIO 1 — "Order my usual" (habit detection)
[0:45-1:15]  SCENARIO 2 — "It's Friday" (proactive biryani)
[1:15-1:50]  SCENARIO 3 — "Plan my evening" (cross-server)
[1:50-2:15]  SCENARIO 4 — Restaurant closed (error recovery)
[2:15-2:45]  SCENARIO 5 — "Diwali tomorrow" (festival)
[2:45-3:00]  OUTRO — Why this matters
```

### Script

**[0:00-0:15] INTRO**
"FoodDNA isn't another food recommendation engine. It's a behavioral intelligence system that understands WHY you eat what you eat. Built by a Psychology Master's graduate, it models Indian food behavior through 10 psychological dimensions — from dietary identity to emotional patterns to cultural rituals."

**[0:15-0:45] SCENARIO 1: "Order my usual"**
"Let's start simple. The user says 'Order my usual.' FoodDNA checks the habit profile — this user has ordered masala dosa from Saravana Bhavan 12 times this month. Habit strength is 0.72 — high. So instead of showing 200 restaurants, it says: 'Your usual masala dosa from Saravana Bhavan?' One tap. Done. This is habit loop reinforcement — a concept from behavioral psychology."

**[0:45-1:15] SCENARIO 2: "It's Friday"**
"Now it gets interesting. The user hasn't said anything — it's just Friday evening. FoodDNA detects a pattern: this user has ordered biryani every Friday for 4 consecutive weeks. This isn't a coincidence — it's a culturally reinforced habit loop. Friday biryani is a weekend celebration ritual in Indian food culture. So FoodDNA proactively suggests: 'Friday vibes! Your usual biryani?' The agent doesn't just know WHAT you order — it knows WHY."

**[1:15-1:50] SCENARIO 3: "Plan my evening"**
"This is where cross-server intelligence kicks in. FoodDNA combines signals from all three Swiggy MCP servers — Food, Instamart, AND Dineout. The user says 'Plan my evening.' FoodDNA checks Dineout for table availability at top-rated restaurants, checks Food for delivery options, and uses the social dynamics profile to detect this is a family context. It presents both: dine-out at Barbeque Nation OR order in from Meghana Foods. No other agent can do this — they only have access to one server."

**[1:50-2:15] SCENARIO 4: Restaurant closed**
"What happens when your favorite restaurant is closed? Most agents just say 'no results.' FoodDNA does something smarter — it cross-references your Food DNA profile to find psychologically similar alternatives. Same cuisine, comparable price, familiar comfort. Not random restaurants — intelligent alternatives that respect your food identity."

**[2:15-2:45] SCENARIO 5: Festival awareness**
"India has 30+ major festivals, each with specific food associations. When the user mentions Diwali, FoodDNA checks the festival calendar, filters by dietary identity — this user is vegetarian, so all suggestions are compliant — and adjusts for regional preference. South Indian user? Mysore Pak from Sri Krishna Sweets. North Indian? Kaju Katli from Haldiram's. The agent understands that festival food is non-negotiable cultural expression, not just a preference."

**[2:45-3:00] OUTRO**
"FoodDNA treats food as identity, not nutrition. It's built on 6 psychological frameworks — habit loop theory, self-determination theory, nudge theory, stages of change, behavioral economics, and cultural psychology. This is what happens when a Psychology Master's graduate builds an AI agent. Thank you."

---

## D. Application Text for Swiggy Builders Club

### Integration Name
**FoodDNA Agent**

### Organization
Individual developer (Psychology Master's graduate)

### Servers Requested
- `food` (14 tools — primary: ordering, restaurants, menus)
- `instamart` (13 tools — grocery patterns, go-to items)
- `dineout` (8 tools — dining out, social patterns)

### Expected Volume
- Development/staging: ~500 requests/day
- Production (post-approval): ~5,000-10,000 requests/day
- Rate budget awareness: targeting 100 req/min per user (20% headroom under 120 limit)

### Use Case Description

**What it does:**
FoodDNA Agent is a psychology-first AI behavioral intelligence system that learns Indian users' food behavior patterns from Swiggy MCP signals and builds a comprehensive "Food DNA" — a multi-dimensional psychological profile that captures cultural identity, regional preferences, dietary patterns, temporal rhythms, emotional triggers, and social dynamics.

**Why it's different:**
Unlike traditional recommendation engines that use collaborative filtering ("users like you ordered X"), FoodDNA models food as **psychology** — applying 6 established behavioral frameworks (Habit Loop Theory, Self-Determination Theory, Nudge Theory, Transtheoretical Model, Behavioral Economics, Cultural Psychology) to understand WHY users eat what they eat.

**Key differentiators:**
1. **Psychology-first architecture** — Built by a Psychology Master's graduate using established behavioral science frameworks, not just statistical patterns
2. **Cross-server behavioral fusion** — Combines signals from Food + Instamart + Dineout to build a unified behavioral profile that no single server provides
3. **Indian-specific modeling** — 12 life-stage profiles, regional food identity, festival food calendar, vegetarian/non-vegetarian as identity (not preference)
4. **10-dimension Food DNA** — Dietary Identity, Regional Identity, Cuisine Preferences, Temporal Patterns, Price Psychology, Health Orientation, Social Dynamics, Emotional Patterns, Life Stage, Habit Profile
5. **Ethical AI design** — Dietary identity is a hard filter (never overridden), nudge suppression rules respect autonomy, health nudges never target stressed users

**Technical approach:**
- MCP Python SDK for Swiggy server communication
- OAuth 2.1 + PKCE authentication
- Per-user behavioral models with exponential moving average updates
- 10 dimensions with individual learning rates (dietary=0.00, emotional=0.50)
- Confidence scoring per dimension based on data point count
- Voice (≤3 options) and chat (≤8 options) response shaping
- Rate limiting at 100 req/min with exponential backoff retry

**What Swiggy gets:**
- Increased Instamart growth through cross-server grocery-to-food intelligence
- Higher Swiggy One retention through personalized, psychologically-aware recommendations
- Demonstration of MCP platform capabilities (cross-server composition, behavioral learning)
- A new category of food agent — behavioral intelligence, not just search

### Primary Technical Contact
- Name: Himansh
- Email: himansh@users.noreply.github.com
- GitHub: demo84431-ship-it/AI-video-editing

### Demo Video Link
[To be recorded and uploaded — Loom/Google Drive/YouTube unlisted]

---

## E. Recording Guide

### Tools Needed
- Screen recorder (OBS Studio / Loom / built-in macOS)
- Terminal with the demo script running
- Browser showing the chat interface (optional)

### Recording Steps

1. **Set up the demo environment**
   ```bash
   cd /root/.openclaw/workspace/swiggy-builders/food-dna-agent
   python demo.py
   ```

2. **Record each scenario as a separate clip** (easier to edit)
   - Clip 1: "Order my usual" — show habit detection, 15 seconds
   - Clip 2: "It's Friday" — show proactive suggestion, 30 seconds
   - Clip 3: "Plan my evening" — show cross-server fusion, 35 seconds
   - Clip 4: Restaurant closed — show error recovery, 25 seconds
   - Clip 5: "Diwali tomorrow" — show festival awareness, 30 seconds

3. **Add voiceover** using the script above
   - Record voiceover separately (better quality)
   - Or use TTS for a clean, professional narration

4. **Edit together** with transitions
   - Intro slide: "FoodDNA Agent — Psychology-First Food Intelligence"
   - Scenario title cards between clips
   - Outro: "Built for Swiggy Builders Club"

5. **Upload** to Loom/Google Drive/YouTube (unlisted)
   - Copy link for application

### Tips for a Great Demo
- Show the Food DNA profile being built (the "brain" of the agent)
- Show the psychological reasoning, not just the output
- Show at least one error case (restaurant closed)
- Keep it under 3 minutes — respect the reviewer's time
- Narrate clearly — explain what's happening and why it matters

---

## F. Go-Live Checklist (Pre-Production)

### Authentication
- [ ] Production `client_id` issued by Swiggy
- [ ] All redirect URIs allowlisted (HTTPS)
- [ ] PKCE flow implemented correctly (already done in `mcp_client.py`)
- [ ] Token stored securely (not in logs, not in URLs)
- [ ] 401 handling triggers re-auth flow (already done)

### Error Handling
- [x] Retry logic with exponential backoff (5 attempts, 500ms→8s)
- [x] Idempotency guards on `place_food_order` (check-then-retry)
- [x] Domain errors surfaced to user (not retried)
- [x] `report_error` called on persistent failures
- [x] 6 error buckets with distinct handling

### UX
- [x] Cart confirmed before order placement
- [x] Restaurant switch warning (Food)
- [x] Address switch clear (Instamart)
- [x] Voice: max 3 options, no raw prices
- [x] Chat: up to 8 results, rich formatting

### Operations
- [x] Session ID logging in place
- [ ] Deprecation monitoring configured
- [ ] Error rate monitoring with alerts
- [ ] Data handling compliant with DPDP Act

### Traffic
- [x] Respectful polling intervals (≥10s for tracking)
- [x] No unnecessary repeated calls
- [x] Local caching where appropriate (5min orders, 10min search)
- [x] Rate limit awareness (100 req/min, 20% headroom)

---

## G. Application Submission Checklist

- [ ] Record demo video (3 min, 5 scenarios)
- [ ] Upload to Loom/Google Drive/YouTube (unlisted)
- [ ] Visit https://mcp.swiggy.com/builders/access/
- [ ] Fill in Developer track application
- [ ] Paste demo video link
- [ ] Submit application
- [ ] Save confirmation/reference number

---

*Phase 4 deliverable. Demo scenarios designed, application text prepared, recording guide ready.*
