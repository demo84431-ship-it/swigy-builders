# Technical Tools, GitHub Repos & Implementation Resources

> **For**: Food DNA Agent (Swiggy Builders Club)
> **Date**: 2026-05-09
> **Purpose**: Technical foundation for building the behavioral learning agent

---

## 1. Indian Food Datasets

### 1.1 Indian Food Composition Tables (IFCT 2017) — CRITICAL
**Repo**: https://github.com/ifct2017/compositions (npm: `@nodef/ifct2017`)
**What**: Detailed nutritional values for 542 key foods in India, based on direct measurements across six regions
**Source**: National Institute of Nutrition, Hyderabad (ICMR)
**Key features**:
- 20 food groups (Cereals, Legumes, Green Leafy Vegetables, Fruits, etc.)
- Names in multiple Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, etc.)
- 38+ nutrient values per food (energy, protein, fat, carbs, vitamins, minerals)
- Regional sampling across 6 regions of India
- Yield factors for raw-to-edible conversion
- Recommended daily intakes

**Why it's critical for Food DNA Agent**:
- Enables nutritional profiling of any Indian dish
- Multi-language food names → vernacular agent support
- Regional categorization → maps to user's regional identity
- Can calculate daily nutrient intake from order history

**Data structure**:
```javascript
ifct2017.compositions('pineapple')
// → { code: 'E053', name: 'Pineapple', scie: 'Ananas comosus',
//     lang: 'A. Ahnaros; B. Anarasa; G. Anenas; H. Ananas; Kan. Ananas;
//     Kash. Punchitipul; Kh. Soh trun; Kon. Anas; Mal. Kayirha chakka;
//     M. Kihom Ananas; O. Sapuri; P. Ananas; Tam. Annasi pazham;
//     Tel. Anasa pandu; U. Ananas.' }
```

### 1.2 Indian Nutrient Databank (INDB)
**Repo**: https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB-
**What**: Nutrient values for recipes commonly consumed in India
**Source**: ICMR-NIN IFCT 2017 + UK McCance & Widdowson + USDA FoodData Central
**Key features**:
- 1,016 recipes (490 from "Art & Science of Cooking" + 378 from "Basic Food Preparation" + 148 from web)
- Recipe ingredients with amounts and units
- Nutrient retention factors for Indian cooking methods
- Serving sizes for Indian recipes
- Common names in multiple languages

**Why it's critical for Food DNA Agent**:
- Recipe-level nutrition (not just ingredient-level)
- Cooking method nutrient retention (boiling, frying, baking affect nutrients differently)
- Can estimate nutritional content of restaurant orders by matching dish names

### 1.3 Kaggle: Food Ordering Behavior India (50K Orders)
**URL**: https://www.kaggle.com/datasets/rhythmghai/food-ordering-behavior-india-50k-orders
**What**: User habits, preferences, and context-rich food delivery data from Indian platforms
**Key features**:
- 50,000+ orders from Indian food delivery platforms
- User behavior patterns, ordering times, preferences
- Contextual data (weather, day of week, etc.)

**Why it's critical for Food DNA Agent**:
- Real Indian food ordering behavior data
- Can validate behavioral models against real patterns
- Training data for prediction models

### 1.4 Kaggle: Indian Food and Its Recipes Dataset
**URL**: https://www.kaggle.com/datasets/kishanpahadiya/indian-food-and-its-recipes-dataset-with-images
**What**: Indian food dishes with recipes and images
**Key features**:
- Regional dish categorization
- Recipe ingredients and instructions
- Images for visual recognition

### 1.5 Indian Food Data Analysis
**Repo**: https://github.com/sanju6890/Indian-food-Data-Analysis
**What**: Regional analysis of Indian dishes, state-wise analysis
**Key features**:
- Vegetarian vs non-vegetarian distribution by region
- State-wise cuisine analysis
- Regional food patterns

---

## 2. Recommendation System Repos

### 2.1 Hybrid Food Recommendation System — BEST REFERENCE
**Repo**: https://github.com/zyna-b/Food-Recommendation-System
**What**: Hybrid ML recipe recommendation using collaborative filtering + content-based filtering
**Key features**:
- SVD for collaborative filtering
- TF-IDF for content-based filtering
- User profile management (dietary preferences, cuisine choices, cooking time)
- Smart categorization with clustering
- Rating system for feedback loop
- Complete data pipeline

**Why it's relevant**:
- Hybrid approach = behavioral (collaborative) + content (food attributes)
- User profiling system can be adapted for Food DNA
- Clustering approach can group users by food personality
- Rating feedback loop → agent learning loop

**Architecture**:
```
data/Scripts/
├── recommender_app.py              # Main recommendation app
├── preprocess_recipes_and_build_initial_models.py  # Data pipeline
├── preprocess_interactions.py      # Interaction preprocessing
└── retrain_models.py              # Model retraining
```

### 2.2 Hybrid Restaurant Recommender
**Repo**: https://github.com/poolkit/Hybrid-Restaurant-Recommender
**What**: Restaurant recommendation using collaborative + content-based filtering
**Key features**:
- Restaurant-level recommendations (not just dish-level)
- User sign-in and preference tracking
- Hybrid filtering approach

### 2.3 Online Food Order Prediction
**Repo**: https://github.com/Shivmalge/Online-Food-Order-Prediction
**What**: ML model predicting whether users will order again based on demographics
**Key features**:
- Age, marital status, occupation, income, family size as features
- Latitude/longitude location data
- Feedback analysis (positive/negative)
- Reorder prediction
**Why it's relevant**: Feature engineering approach for user profiling from Indian food delivery data

### 2.4 Zomato Sales Data Analysis
**Repo**: https://github.com/MinakshiDhhote/Zomato-sales-data-snalysis
**What**: Exploratory Data Analysis on Zomato dataset (restaurants, ratings, customers)
**Why it's relevant**: EDA patterns for Indian food delivery data

### 2.5 Customer Segmentation & Behavior Analysis (GitHub Topic)
**URL**: https://github.com/topics/customer-behavior-analysis
**What**: 80+ repos on customer behavior analysis using Python, SQL, Power BI
**Notable patterns**:
- RFM analysis (Recency, Frequency, Monetary) for customer segmentation
- K-means clustering for behavioral grouping
- Process mining for customer journey analysis
- Purchase pattern analysis
**Why it's relevant**: Behavioral clustering techniques applicable to food user segmentation

### 2.6 Recipe Recommendation Topics (GitHub)
**URL**: https://github.com/topics/recipe-recommendation?o=asc&s=stars
**What**: Collection of recipe recommendation projects on GitHub
**Notable repos**: Multiple implementations of collaborative filtering, content-based, and hybrid approaches for food recommendation

---

## 3. Behavioral Modeling & User Profiling

### 3.1 User Modeling and User Profiling Survey (arXiv)
**URL**: https://arxiv.org/html/2402.09660v1
**What**: Comprehensive survey of user modeling techniques for recommendation systems
**Key concepts**:
- Multi-view deep learning for cross-domain user modeling
- User profiling from behavioral data
- Dynamic user preference modeling
- Cross-domain recommendation techniques

**Why it's relevant**:
- Academic foundation for building user profiles from behavioral signals
- Cross-domain techniques = using Food + Instamart + Dineout data together
- Dynamic modeling = user preferences change over time

### 3.2 Darts (Time Series Forecasting)
**Repo**: https://github.com/unit8co/darts
**What**: Python library for user-friendly forecasting and anomaly detection in time series
**Key features**:
- Multiple forecasting models (ARIMA, Prophet, Neural Networks)
- Pattern recognition in time series
- Anomaly detection

**Why it's relevant**:
- Order frequency prediction (when will user order next?)
- Consumption pattern detection (milk every 3 days)
- Seasonal pattern recognition (festival ordering spikes)

### 3.3 Customer Behavior Analysis (GitHub Topic)
**URL**: https://github.com/topics/customer-behavior-analysis
**What**: Collection of customer behavior analysis projects
**Notable patterns**:
- Purchase pattern analysis
- Customer segmentation
- Behavioral clustering
- Churn prediction

---

## 4. NLP & Indian Language Tools

### 4.1 Indic NLP Library
**Repo**: https://github.com/anoopkunchukuttan/indic_nlp_library
**What**: NLP library for Indian languages
**Key features**:
- Tokenization, sentence splitting for 10+ Indian languages
- Transliteration between scripts
- Morphological analysis

**Why it's relevant**: Vernacular food names → standardize for matching

### 4.2 AI4Bharat IndicBERT
**Repo**: https://github.com/AI4Bharat/IndicBERT
**What**: BERT model trained on Indian languages
**Why it's relevant**: Understanding food names and descriptions in Indian languages

### 4.3 Google IndicTrans
**Repo**: https://github.com/AI4Bharat/IndicTrans2
**What**: Translation model for Indian languages
**Why it's relevant**: Multi-language food name matching

---

## 5. MCP Implementation Resources

### 5.1 ML System Design Case Studies
**Repo**: https://github.com/Engineer1999/A-Curated-List-of-ML-System-Design-Case-Studies
**What**: Curated list of ML system design case studies including DoorDash food recommendation
**Key case studies**:
- DoorDash: Ensemble Learning for Time Series food delivery
- Personalizing Recommendations for food items
- Recommendation system architectures
**Why it's relevant**: Production ML system design patterns for food recommendation

### 5.2 MCP Python SDK
**Repo**: https://github.com/modelcontextprotocol/python-sdk
**What**: Official Python SDK for MCP servers and clients
**Why it's relevant**: Building the Food DNA agent that connects to Swiggy MCP

### 5.2 MCP Reference Servers
**Repo**: https://github.com/modelcontextprotocol/servers
**What**: Reference implementations of MCP servers
**Why it's relevant**: Understanding MCP patterns, testing, and development

### 5.3 MCP Example Servers
**URL**: https://modelcontextprotocol.io/examples
**What**: List of MCP server examples (Git, filesystem, database, etc.)
**Why it's relevant**: Pattern reference for building MCP-compatible agents

---

## 6. AI Nutrition & Food Intelligence

### 6.1 AI Nutrition Recommendation (Nature)
**URL**: https://www.nature.com/articles/s41598-024-65438-x
**What**: Deep generative model for nutrition recommendation
**Key concepts**:
- Explainable food recommendation
- Dynamic user behavior handling
- Nutrition-aware recommendations

### 6.2 Health-Aware Food Recommendation
**URL**: https://www.sciencedirect.com/science/article/pii/S0010482523013471
**What**: Food recommendation with dual attention mechanism
**Key concepts**:
- User preferences + nutrition data integration
- Deep learning for food recommendation
- Health-aware filtering

### 6.3 Intelligent Food Recommendation Framework
**URL**: https://dl.acm.org/doi/fullHtml/10.1145/3660853.3660883
**What**: Framework combining behavioral data, image classification, and food analysis
**Key concepts**:
- Multi-modal food recommendation
- Behavioral data integration
- Deep learning for food analysis

---

## 7. Implementation Architecture

### 7.1 Recommended Tech Stack for Food DNA Agent

```
Layer 1: Data Sources
├── Swiggy MCP (your_go_to_items, get_food_orders, get_booking_status)
├── IFCT 2017 (Indian food nutrition database)
├── INDB (Indian recipe nutrition databank)
└── External (weather API, calendar API, festival calendar)

Layer 2: Behavioral Processing
├── User Profile Builder (from MCP signals)
├── Pattern Recognition (time-series analysis)
├── Habit Loop Detector (cue-routine-reward)
└── Cultural Context Engine (region, religion, family)

Layer 3: Intelligence Layer
├── Food DNA Classifier (personality type)
├── Predictive Ordering (what/when/where)
├── Recommendation Engine (hybrid filtering)
└── Nudge Engine (behavioral interventions)

Layer 4: MCP Integration
├── Swiggy MCP Client (3 servers, 35 tools)
├── Voice Response Shaping (3-item lists, natural prices)
├── Error Recovery (cart expired, item unavailable)
└── Widget Integration (restaurant cards, menu items)
```

### 7.2 Data Flow: How Food DNA Gets Built

```
Step 1: Gather Signals (MCP)
├── your_go_to_items → frequently ordered groceries
├── get_food_orders → restaurant order history
├── get_booking_status → dining out patterns
└── get_addresses → location patterns (home, work, travel)

Step 2: Extract Features
├── Cuisine preferences (South Indian, North Indian, Chinese, etc.)
├── Dietary identity (vegetarian, non-veg, Jain, vegan)
├── Temporal patterns (breakfast person, late-night snacker)
├── Price sensitivity (budget range, coupon usage)
├── Health orientation (healthy vs indulgent)
├── Social patterns (solo vs family vs group)
└── Regional identity (based on food choices)

Step 3: Build Food DNA Profile
├── Primary Identity: "South Indian vegetarian, breakfast-focused"
├── Behavioral Patterns: "Orders biryani every Friday, groceries every 3 days"
├── Temporal Rhythm: "Breakfast at 8 AM, lunch at 1 PM, dinner at 9 PM"
├── Price Profile: "Moderate spender, coupon-aware"
├── Health Profile: "Indulgent weekends, healthier weekdays"
├── Social Profile: "Family orders on weekends, solo on weekdays"
└── Emotional Profile: "Comfort food when stressed, celebration food on festivals"

Step 4: Apply Intelligence
├── Proactive suggestions: "It's Friday, your usual biryani?"
├── Predictive ordering: "Running low on milk, shall I order?"
├── Contextual awareness: "It's raining, want pakora?"
├── Festival awareness: "Diwali is tomorrow, order sweets?"
├── Health gentle nudge: "You've ordered heavy food 3 days in a row, lighter option today?"
└── Social awareness: "Ordering for the family? Here's a combo that works for everyone."
```

### 7.3 Key Algorithms Needed

| Algorithm | Purpose | Data Source |
|-----------|---------|-------------|
| **Collaborative Filtering (SVD)** | "Users like you also ordered..." | Order history |
| **Content-Based Filtering (TF-IDF)** | Match food attributes to preferences | Menu items + IFCT data |
| **Time Series Forecasting** | Predict next order time | Order timestamps |
| **Clustering (K-Means)** | Group users by food personality | Behavioral features |
| **Sequence Pattern Mining** | Find ordering sequences (A→B→C) | Order history |
| **Anomaly Detection** | Detect unusual orders (dietary change?) | Order patterns |
| **NLP (Embeddings)** | Match food names across languages | IFCT multilingual data |

---

## 8. Key References

### Academic Papers
1. Hungund, S. (2025). "The Role of Food Delivery Apps in Transforming Urban Eating Patterns." medRxiv.
2. "User Modeling and User Profiling: A Comprehensive Survey." arXiv (2024).
3. "AI nutrition recommendation using a deep generative model." Nature (2024).
4. "Health-aware food recommendation system with dual attention." ScienceDirect (2023).
5. "Intelligent Food Recommendation Framework." ACM (2024).

### Datasets
1. IFCT 2017 — 542 Indian foods, 38+ nutrients, 6 regions, multilingual
2. INDB — 1,016 Indian recipes with nutrition data
3. Kaggle Food Ordering Behavior India — 50K orders
4. Food.com Recipes — 180K recipes, 700K interactions

### GitHub Repos
1. ifct2017/compositions — Indian food nutrition database
2. lindsayjaacks/Indian-Nutrient-Databank-INDB — Indian recipe nutrition
3. zyna-b/Food-Recommendation-System — Hybrid recommendation engine
4. unit8co/darts — Time series forecasting
5. modelcontextprotocol/python-sdk — MCP Python SDK
6. Shivmalge/Online-Food-Order-Prediction — Indian food delivery prediction
7. MinakshiDhhote/Zomato-sales-data-snalysis — Zomato EDA
8. Engineer1999/A-Curated-List-of-ML-System-Design-Case-Studies — ML system design (includes DoorDash)
9. poolkit/Hybrid-Restaurant-Recommender — Restaurant recommendation
10. github.com/topics/customer-behavior-analysis — 80+ customer behavior repos
11. github.com/topics/recipe-recommendation — Recipe recommendation collection
12. github.com/topics/user-profiling — User profiling projects
13. github.com/topics/personality-analysis — Personality analysis projects
