# Behavioral Change Models for Food DNA Agent

> **For**: Food DNA Agent (Swiggy Builders Club)
> **Researcher**: Psychology Master's graduate
> **Date**: 2026-05-09
> **Purpose**: Behavioral change frameworks for designing intelligent food interventions

---

## 1. The Habit Loop (Charles Duhigg, 2012)

### Core Model
Every habit follows a three-step loop:

```
CUE → ROUTINE → REWARD
```

- **Cue**: The trigger that initiates the behavior (time, location, emotional state, preceding action, other people)
- **Routine**: The behavior itself (ordering food, cooking, snacking)
- **Reward**: The positive outcome that reinforces the loop (taste, convenience, social bonding, comfort)

### Application to Indian Food Ordering

**Identified Habit Loops from Indian Food Behavior:**

| Cue Type | Specific Cue | Routine | Reward | Frequency |
|----------|-------------|---------|--------|-----------|
| **Temporal** | 7 AM alarm | Order breakfast (idli/dosa) | Familiar taste, energy | Daily |
| **Temporal** | Friday 7 PM | Order biryani | Weekend celebration | Weekly |
| **Environmental** | Rain starts | Order pakora + chai | Warmth, nostalgia | Seasonal |
| **Social** | Friends visiting | Order extra food | Hospitality satisfaction | Occasional |
| **Emotional** | Work stress | Order comfort food | Emotional regulation | Variable |
| **Cultural** | Festival day | Order sweets | Cultural participation | Annual |
| **Location** | Arriving home | Order dinner | Convenience after commute | Daily |

### How the Agent Detects Habit Loops

**From MCP Signals:**

| Signal | What It Reveals | Habit Loop Component |
|--------|----------------|---------------------|
| `your_go_to_items` (order dates) | Regular purchase intervals | Routine identification |
| `get_food_orders` (timestamps) | Ordering time patterns | Cue identification |
| `get_food_orders` (items) | What they order | Routine identification |
| `get_food_orders` (frequency) | How often they order | Habit strength |
| `get_addresses` | Where they order from | Context/cue |
| `fetch_food_coupons` (usage) | Price-seeking behavior | Reward type |

**Detection Algorithm:**
```
For each user:
1. Extract order timestamps → identify temporal clusters (same time, same day)
2. Extract order items → identify recurring items (same dish, same restaurant)
3. Cross-reference: same item + same time = habit loop candidate
4. Calculate habit strength: frequency × consistency
5. Identify cue: what triggers this habit? (time, day, context)
6. Identify reward: what need does this satisfy? (convenience, comfort, celebration)
```

### How the Agent Uses Habit Loops

**Respect existing habits:**
- "It's Friday evening, your usual biryani from Paradise?" (acknowledges the habit)
- Don't over-recommend alternatives to established habits (status quo bias)

**Strengthen positive habits:**
- "You've ordered healthy lunch 5 days in a row! Great streak." (positive reinforcement)
- "Your usual breakfast is ready to order. 2 taps and done." (reduce friction)

**Gently redirect negative habits:**
- "You've ordered heavy food 3 days in a row. How about a lighter option today?" (gentle nudge, not force)
- Use the Transtheoretical Model to gauge readiness for change

---

## 2. Tiny Habits Framework (B.J. Fogg, 2020)

### Core Model
Behavior = Motivation × Ability × Prompt (B=MAP)

**Three rules for creating new habits:**
1. **Make it tiny** — Start with behavior so small it requires no motivation
2. **Find an anchor** — Attach the new behavior to an existing habit
3. **Celebrate immediately** — Create a positive emotion right after the behavior

### Application to Food DNA Agent

**Making healthy food ordering a tiny habit:**

| Anchor (Existing Habit) | Tiny Behavior (New) | Celebration |
|------------------------|--------------------| ------------|
| Opening Swiggy app | Add one healthy item to cart | "Great choice! 🌱" |
| Morning coffee time | Order fruit from Instamart | "Starting the day right! ☀️" |
| Friday biryani order | Add a salad as side | "Balance is key! 💪" |
| Weekend grocery order | Add one new vegetable | "Trying something new! 🎉" |

**Agent Implementation:**
```
Instead of: "You should eat healthier" (high motivation required)
Do: "Want to add a fruit to your order? Just one tap." (low motivation, tiny action)

Instead of: "Change your entire diet" (overwhelming)
Do: "Your usual biryani + a side salad today?" (tiny addition to existing habit)
```

### Key Insight for Food DNA Agent
**Don't fight habits — stack on top of them.** The agent should identify existing habit loops and attach small, positive behaviors to them rather than trying to replace habits entirely.

---

## 3. Nudge Theory (Thaler & Sunstein, 2008)

### Core Model
A nudge is any aspect of the choice architecture that alters people's behavior in a predictable way without forbidding any options or significantly changing their economic incentives.

**Key nudge types:**

| Nudge Type | Definition | Food Application |
|-----------|-----------|-----------------|
| **Default** | Pre-selected option | "Your usual" as default suggestion |
| **Social proof** | What others do | "Most popular in your area" |
| **Salience** | What stands out | Highlight healthy options visually |
| **Framing** | How options are presented | "Light and fresh" vs "low calorie" |
| **Simplification** | Reduce complexity | One-tap reorder |
| **Timely prompts** | Right moment | "Lunchtime! Order your usual?" |

### Ethical Nudging for Food DNA Agent

**Principles:**
1. **Transparent** — User knows they're being nudged ("Based on your patterns...")
2. **Easy to resist** — Always show alternatives, never hide options
3. **Aligned with user goals** — Nudge toward what the user wants, not what we want
4. **Respect autonomy** — Never force, always suggest
5. **Culturally appropriate** — Use Indian framing, not Western diet culture

**Nudge Design for Indian Context:**

| Situation | Nudge | Framing | Why It Works |
|-----------|-------|---------|-------------|
| User orders heavy food 3+ days | "Lighter option today?" | Health + variety | Loss aversion (don't lose health) |
| User hasn't ordered vegetables | "Add some greens?" | Simplicity | Default effect (easy addition) |
| Festival approaching | "Order [festival] sweets?" | Cultural identity | Social proof + identity |
| Rainy weather | "Perfect for hot pakora!" | Contextual relevance | Environmental cue alignment |
| User has Swiggy One | "Free delivery on this order!" | Savings framing | Loss aversion (don't waste benefit) |

### What NOT to Do (Ethical Boundaries)
- Never guilt-trip ("You're eating too much junk")
- Never hide unhealthy options (respect autonomy)
- Never use shame as motivation
- Never push Western diet standards on Indian users
- Never override cultural/religious food choices

---

## 4. Self-Determination Theory (Deci & Ryan, 2000)

### Core Model
Three innate psychological needs drive motivation:

1. **Autonomy** — Feeling of choice and control
2. **Competence** — Feeling effective and capable
3. **Relatedness** — Feeling connected to others

### Application to Food DNA Agent

**Autonomy:**
- "Here are 3 options based on your preferences. Which one?" (choice, not command)
- "Your usual is available. Or try something new?" (options, not mandates)
- Never auto-order without confirmation (user must feel in control)

**Competence:**
- "You've saved ₹4,200 this year with smart ordering!" (competence feedback)
- "Great choice — this is one of the healthiest options available." (competence affirmation)
- Show nutrition information so users feel informed

**Relatedness:**
- "Your family usually orders from this place on Sundays." (family connection)
- "People in your area love this restaurant." (social connection)
- "Perfect for your dinner party tonight." (social occasion)

---

## 5. Transtheoretical Model (Stages of Change) — Prochaska & DiClemente

### Core Model
Behavior change occurs in 5 stages:

| Stage | User State | Food Behavior | Agent Strategy |
|-------|-----------|---------------|----------------|
| **Pre-contemplation** | "I eat whatever" | No intention to change | Don't push health, serve well |
| **Contemplation** | "Maybe I should eat better" | Thinking about change | Gentle information, no pressure |
| **Preparation** | "I want to change" | Planning to act | Help find healthy options |
| **Action** | "I'm changing now" | Actively changing | Track progress, celebrate wins |
| **Maintenance** | "This is my new norm" | Sustained change | Reinforce, prevent relapse |

### How the Agent Detects Stage

| Signal | Likely Stage | Agent Response |
|--------|-------------|----------------|
| Always orders same comfort food | Pre-contemplation | Serve well, don't nudge |
| Occasionally browses healthy options | Contemplation | "Want to try this healthy option?" |
| Orders healthy food sometimes | Preparation | "Here are more healthy options near you" |
| Orders healthy food frequently | Action | "Great streak! 5 healthy meals this week" |
| Consistently orders healthy | Maintenance | "You've made healthy eating a habit!" |

### Key Insight
**Match intervention intensity to change stage.** Pushing healthy food on someone in pre-contemplation will annoy them and reduce trust. The agent must DETECT the stage and adjust accordingly.

---

## 6. COM-B Model (Michie et al., 2011)

### Core Model
Behavior (B) occurs when three conditions are met:

- **Capability (C)** — Physical and psychological ability to perform the behavior
- **Opportunity (O)** — Environmental and social factors that enable the behavior
- **Motivation (M)** — Reflective and automatic processes that drive behavior

### Application to Food DNA Agent

| Component | Food Context | Agent Role |
|-----------|-------------|------------|
| **Capability** | Can they order? (app literacy, language) | Simplify UI, voice-first, vernacular |
| **Opportunity** | Is food available? (restaurant coverage, time) | Show available options, manage timing |
| **Motivation** | Do they want to? (taste, health, price) | Personalized recommendations, incentives |

**Diagnosing why someone doesn't order healthy food:**

| Barrier | Component | Intervention |
|---------|-----------|-------------|
| "I don't know what's healthy" | Capability | Show nutrition info, suggest options |
| "Healthy restaurants don't deliver here" | Opportunity | Show Instamart cooking ingredients |
| "Healthy food doesn't taste good" | Motivation | Show highly-rated healthy options |
| "Healthy food is too expensive" | Motivation | Show budget-friendly healthy options, coupons |
| "I don't have time to choose" | Capability | One-tap healthy reorder |

---

## 7. Indian-Specific Behavioral Patterns (Pew Research Data)

### Vegetarian Distribution by Region (Pew Research, 2021)

| Region | % Vegetarian (Hindus) | Dietary Pattern |
|--------|----------------------|-----------------|
| **North India** | 71% | Strong vegetarian, wheat-based |
| **Central India** | 61% | Strong vegetarian |
| **West India** | 57% | Mixed, vegetarian dominant |
| **South India** | 30% | More non-veg, rice-based |
| **East India** | 18% | Fish-heavy, less vegetarian |
| **Northeast India** | 19% | Meat-heavy, minimal vegetarian |

### Religious Dietary Patterns

| Religion | % Vegetarian | Key Restrictions |
|----------|-------------|-----------------|
| **Jain** | 92% | No meat, no root vegetables (onion, garlic), no eating after sunset |
| **Sikh** | 59% | Vegetarian dominant |
| **Hindu** | 44% | Varies by region, no beef for most |
| **Buddhist** | 25% | Vegetarian lean |
| **Muslim** | 8% | Halal, no pork |
| **Christian** | 10% | Fewer restrictions |

### Additional Findings
- **81% of Indians** limit meat consumption in some way (vegetarian, certain meats, certain days)
- **21% of Hindu vegetarians** also avoid root vegetables (onion, garlic)
- **51% of Hindus** would not eat in a home with different food rules
- **72% of Jains** would not eat in a home with different food rules
- **Highly religious Hindus** are more likely to be vegetarian (46% vs 33%)
- **BJP-favoring Hindus** are more likely to be vegetarian (49% vs 35%)

### Implication for Food DNA Agent
The agent must model dietary identity as a **core, non-negotiable dimension** — not a preference to be overridden. A Jain user who avoids root vegetables will NEVER want onion/garlic suggestions. A Muslim user will NEVER want non-halal food. These are identity-level constraints, not optimization targets.

---

## 8. Integrated Behavioral Model for Food DNA

### Combining All Frameworks

```
Food DNA Behavioral Model
├── Layer 1: Identity (Non-negotiable)
│   ├── Religious/Moral: Vegetarian, Jain, Halal, etc.
│   ├── Regional: South Indian, North Indian, Bengali, etc.
│   └── Cultural: Festival food, family traditions
│
├── Layer 2: Habits (Automatic)
│   ├── Habit Loops: Cue → Routine → Reward
│   ├── Temporal Patterns: When they order
│   ├── Restaurant Loyalty: Where they order
│   └── Item Preferences: What they order
│
├── Layer 3: Context (Situational)
│   ├── Weather: Rain → comfort food
│   ├── Time: Morning → breakfast, Evening → dinner
│   ├── Social: Alone vs family vs friends
│   └── Emotional: Stressed → comfort, celebrating → treats
│
├── Layer 4: Motivation (Changeable)
│   ├── Health Orientation: How health-conscious
│   ├── Price Sensitivity: Budget constraints
│   ├── Variety Seeking: Open to new things
│   └── Convenience Priority: Speed vs quality
│
└── Layer 5: Interventions (Agent Actions)
    ├── Nudges: Gentle suggestions
    ├── Habit Stacking: Attach new behaviors to existing habits
    ├── Stage-Matched: Match intervention to change readiness
    └── Ethical: Transparent, respectful, culturally appropriate
```

### Decision Tree for Agent Behavior

```
1. Is this a dietary identity issue? (Religion, region, culture)
   → YES: Never override. Respect absolutely.
   → NO: Continue.

2. Is this an established habit? (Regular pattern detected)
   → YES: Respect the habit. Only suggest if user is in contemplation+ stage.
   → NO: Continue.

3. Is there a contextual trigger? (Weather, time, social, emotional)
   → YES: Use context for relevant suggestion.
   → NO: Continue.

4. Is the user open to change? (Stage of change assessment)
   → Pre-contemplation: Don't nudge. Serve well.
   → Contemplation: Gentle information.
   → Preparation: Active suggestions.
   → Action: Track and celebrate.
   → Maintenance: Reinforce.

5. What type of nudge is appropriate?
   → Default: "Your usual" as first option
   → Social proof: "Popular in your area"
   → Framing: Use Indian health framing, not Western
   → Simplification: One-tap options
   → Timely: Right moment, right context
```

---

## References

1. Duhigg, C. (2012). "The Power of Habit: Why We Do What We Do in Life and Business."
2. Fogg, B.J. (2020). "Tiny Habits: The Small Changes That Change Everything."
3. Thaler, R.H. & Sunstein, C.R. (2008). "Nudge: Improving Decisions About Health, Wealth, and Happiness."
4. Deci, E.L. & Ryan, R.M. (2000). "The 'What' and 'Why' of Goal Pursuits."
5. Prochaska, J.O. & DiClemente, C.C. (1983). "Stages and Processes of Self-Change of Smoking."
6. Michie, S. et al. (2011). "The Behaviour Change Technique Taxonomy (v1)."
7. Pew Research Center (2021). "Views of religion and food in India."
8. Neal, D.T. et al. (2006). "Habits — A Repeat Performance."
9. Wood, W. et al. (2002). "Habits in Everyday Life."
10. Hungund, S. (2025). "The Role of Food Delivery Apps in Transforming Urban Eating Patterns." medRxiv.
