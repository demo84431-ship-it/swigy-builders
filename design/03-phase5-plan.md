# Phase 5: Multi-Profile, Voice Agent & Chat Enhancement

> **Date**: 2026-05-09
> **Status**: ✅ COMPLETE
> **Estimated**: 2-3 days | **Actual**: ~1 hour

---

## What We're Building

### 1. Multi-Profile System (5 Demo Users)

Currently: Only "Arjun, 28, Bengaluru" (South Indian IT professional)

**Add 5 diverse profiles:**

| # | Name | Profile | Region | Dietary | Life Stage | Key Trait |
|---|---|---|---|---|---|---|
| 1 | **Arjun** ✅ | South Indian IT Professional | Tamil Nadu | Vegetarian | Young professional alone | Friday biryani habit |
| 2 | **Priya** | North Indian Joint Family | Delhi | Non-veg (mixed household) | Joint family | Family dinner coordination |
| 3 | **Riya** | Bengali College Student | Kolkata | Eggetarian | College student (hostel) | Budget-conscious, late-night |
| 4 | **Mr. Shah** | Gujarati Senior Citizen | Ahmedabad | Jain | Senior citizen | Voice-first, medical dietary |
| 5 | **Karthik** | NRI Ordering for Parents | US → Chennai | Vegetarian | NRI remote ordering | Cross-timezone care |

**Each profile has:**
- Full 10-dimension Food DNA
- Unique habit patterns
- Different emotional triggers
- Different dietary constraints
- Different price psychology
- Different social dynamics

### 2. Profile Selector UI

**Landing page with profile cards:**

```
┌──────────────────────────────────────────────────────┐
│  🍕 FoodDNA Agent — Choose a Profile to Explore      │
│                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │ 🧑‍💻 Arjun │ │ 👩‍👧‍👦 Priya  │ │ 🎓 Riya   │             │
│  │ 28, BLR  │ │ 45, DEL  │ │ 21, KOL  │             │
│  │ Veg      │ │ Non-veg  │ │ Eggeter. │             │
│  │ Solo     │ │ Family   │ │ Student  │             │
│  │ [Select] │ │ [Select] │ │ [Select] │             │
│  └──────────┘ └──────────┘ └──────────┘             │
│                                                       │
│  ┌──────────┐ ┌──────────┐                           │
│  │ 🧓 Shah   │ │ ✈️ Karthik│                           │
│  │ 68, AMD  │ │ 32, US   │                           │
│  │ Jain     │ │ Veg      │                           │
│  │ Senior   │ │ NRI      │                           │
│  │ [Select] │ │ [Select] │                           │
│  └──────────┘ └──────────┘                           │
│                                                       │
│  Or connect your real Swiggy account → [Connect]     │
└──────────────────────────────────────────────────────┘
```

**When a profile is selected:**
- Chat loads with that profile's Food DNA
- Sidebar shows their specific data
- Responses are personalized to their psychology
- Suggestions adapt to their patterns

### 3. Chat Interface Improvements

| Current | Improved |
|---|---|
| Basic text responses | Rich cards with images, prices, ratings |
| No message history | Persistent chat history |
| No typing indicator | Animated typing dots |
| No timestamps | Message timestamps |
| Static suggestions | Dynamic suggestions based on context |
| No profile indicator | Shows active profile name/avatar |
| No quick actions | "Order Now", "View Menu", "Try Something New" buttons |

**Specific improvements:**
- **Quick action buttons** in agent responses (Order, View Menu, More Options)
- **Context-aware suggestions** — suggestions change based on conversation
- **Profile avatar** in chat (Arjun's messages have his avatar, agent has FoodDNA avatar)
- **Rich cards** for restaurant/food recommendations (image, rating, price, delivery time)
- **Dark/light mode toggle**
- **Mobile responsive** (already is, but polish it)

### 4. Voice Agent Integration

**Two levels:**

#### Level 1: Text-to-Speech (Agent speaks responses)
- Agent responses can be read aloud
- Voice button on each message → "🔊 Listen"
- Uses TTS API (Pollinations.ai free TTS or browser SpeechSynthesis)
- Different voice profiles per user (Arjun = casual, Mr. Shah = respectful)

#### Level 2: Speech-to-Text (User speaks to agent)
- Microphone button in chat input
- Browser Web Speech API (free, built into Chrome)
- Real-time transcription
- "Hold to speak" or "Click to talk" mode
- Voice activity detection

#### Level 3: Full Voice Agent (Advanced)
- WebSocket-based real-time voice
- Interrupt detection (user can barge in)
- Voice personality matching
- Emotional tone detection
- Requires more infrastructure (WebRTC, STT server)

**Recommendation:** Start with Level 1 + Level 2 (browser-native, free, works immediately). Level 3 is a future enhancement.

---

## Implementation Plan

### Phase 5A: Multi-Profile System (Day 1)

| Task | Files | Effort |
|---|---|---|
| Create 5 Food DNA profiles as JSON | `profiles/*.json` | 2h |
| Add profile selector endpoint | `app.py` | 30min |
| Build profile selector UI | `static/index.html` | 2h |
| Wire profile switching in chat | `app.py` | 1h |
| Test all 5 profiles | — | 30min |

**Total: ~6 hours**

### Phase 5B: Chat Enhancement (Day 2)

| Task | Files | Effort |
|---|---|---|
| Rich message cards (restaurant/food) | `static/index.html` | 2h |
| Quick action buttons | `static/index.html` | 1h |
| Context-aware suggestions | `app.py` | 1h |
| Typing indicator polish | `static/index.html` | 30min |
| Profile avatar in messages | `static/index.html` | 30min |
| Mobile responsive polish | `static/index.html` | 1h |

**Total: ~6 hours**

### Phase 5C: Voice Agent (Day 3)

| Task | Files | Effort |
|---|---|---|
| TTS: "Listen" button on messages | `static/index.html` | 1.5h |
| STT: Microphone input | `static/index.html` | 2h |
| Voice personality per profile | `app.py` | 1h |
| Voice UI (mic animation, waveform) | `static/index.html` | 1h |
| Testing + polish | — | 30min |

**Total: ~6 hours**

---

## File Changes Summary

### New Files
```
profiles/
├── arjun.json          # South Indian IT Professional
├── priya.json          # North Indian Joint Family
├── riya.json           # Bengali College Student
├── shah.json           # Gujarati Senior Citizen
└── karthik.json        # NRI Remote Ordering
```

### Modified Files
```
app.py                  # Profile endpoints, voice TTS endpoint, rich responses
static/index.html       # Profile selector, rich cards, voice UI
src/food_dna.py         # Add from_json() class method (already has from_dict)
```

---

## Technical Details

### Profile JSON Structure
```json
{
  "id": "arjun",
  "name": "Arjun",
  "age": 28,
  "city": "Bengaluru",
  "origin": "Chennai",
  "avatar": "🧑‍💻",
  "tagline": "South Indian IT Professional",
  "dna": { ... full Food DNA object ... },
  "sample_conversations": [
    {"user": "Order my usual", "agent": "Your usual masala dosa from Saravana Bhavan?"},
    {"user": "It's Friday", "agent": "Friday vibes! Your usual biryani?"}
  ]
}
```

### Voice Integration (Browser-native)
```javascript
// TTS: Agent speaks
function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = speechSynthesis.getVoices()[0];
  utterance.rate = 0.9;
  speechSynthesis.speak(utterance);
}

// STT: User speaks
function startListening() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('chat-input').value = transcript;
  };
  recognition.start();
}
```

### API Endpoints (New)
```
GET  /api/profiles              → List all available profiles
GET  /api/profiles/{id}         → Get specific profile
POST /api/chat                  → Chat with active profile context
POST /api/tts                   → Convert text to speech (returns audio)
GET  /api/voice/personality     → Get voice settings for active profile
```

---

## Priority Order

1. **Multi-Profile System** — Most impactful for demo, shows diversity
2. **Chat Enhancements** — Polish for Swiggy reviewers
3. **Voice Agent** — Nice-to-have, adds wow factor

---

## Dependencies

| Feature | External Dependency | Cost |
|---|---|---|
| TTS | Browser SpeechSynthesis API | Free (built-in) |
| STT | Browser Web Speech API | Free (built-in, Chrome only) |
| Rich cards | No external dep | Free |
| Profile data | No external dep | Free |

**Everything is free.** No API keys needed for Phase 5.

---

*Plan created 2026-05-09. Ready for next session implementation.*
