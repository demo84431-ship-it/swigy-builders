# FoodDNA Agent — Railway Deployment Guide

## Quick Start (5 Steps)

### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. No credit card needed for the free tier ($5/month credit)

### Step 2: Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub Repo"**
3. Choose `demo84431-ship-it/AI-video-editing`
4. Railway auto-detects Python and uses `Procfile`

### Step 3: Set Environment Variables
Go to your project → **Variables** tab → add:

| Variable | Value |
|---|---|
| `SWIGGY_CLIENT_ID` | `YOUR_CLIENT_ID` (from Swiggy after approval) |
| `AUTH_BASE_URL` | `https://auth.swiggy.com` |
| `MCP_FOOD_URL` | `https://mcp.swiggy.com/food` |
| `MCP_INSTAMART_URL` | `https://mcp.swiggy.com/im` |
| `MCP_DINEOUT_URL` | `https://mcp.swiggy.com/dineout` |
| `REDIRECT_URI` | `https://YOUR-APP.up.railway.app/api/auth/callback` |

### Step 4: Set Root Directory
1. Go to **Settings** → **Service**
2. Set **Root Directory** to `swiggy-builders/food-dna-agent`
3. Railway will redeploy automatically

### Step 5: Get Your URL
1. Go to **Settings** → **Networking**
2. Click **"Generate Domain"**
3. You'll get: `https://your-app-name.up.railway.app`
4. Update `REDIRECT_URI` variable with this URL

Done! Your app is live. 🎉

---

## Local Development

```bash
cd swiggy-builders/food-dna-agent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run
python app.py
# Opens at http://localhost:3000
```

---

## Project Structure

```
food-dna-agent/
├── app.py                    ← FastAPI web server (Railway entry point)
├── Procfile                  ← Railway process definition
├── railway.toml              ← Railway config
├── runtime.txt               ← Python version
├── requirements.txt          ← Dependencies
├── .env.example              ← Environment variables template
├── static/
│   └── index.html            ← Chat UI frontend
├── src/
│   ├── agent.py              ← Main agent orchestrator
│   ├── config.py             ← Configuration (OAuth, MCP, rate limits)
│   ├── mcp_client.py         ← MCP client (OAuth, retry, errors)
│   ├── food_dna.py           ← Data model (10 dimensions)
│   ├── feature_extractor.py  ← MCP response → behavioral features
│   ├── food_dna_calculator.py← EMA updates, confidence, habits
│   ├── recommender.py        ← Scoring, recommendations, response shaping
│   └── nudge_engine.py       ← Nudge timing, framing, suppression
├── design/
│   ├── 01-food-dna-taxonomy.md
│   └── 02-demo-and-application.md
├── research/                 ← 6 psychology research files
├── demo.py                   ← Interactive terminal demo
├── generate_video.py         ← Video generator
└── voiceover/                ← Audio clips
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Chat UI |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/auth/login` | Start OAuth flow |
| `GET` | `/api/auth/callback` | OAuth callback |
| `POST` | `/api/chat` | Send message to agent |
| `GET` | `/api/profile` | Get Food DNA profile |
| `WS` | `/ws/chat` | WebSocket chat |

---

## Before Swiggy Approval (Demo Mode)

You can test the UI without Swiggy credentials:

1. The chat UI loads at `/`
2. Click suggestions to see placeholder responses
3. Once you get `SWIGGY_CLIENT_ID`, the real agent activates

---

## After Swiggy Approval

1. Set `SWIGGY_CLIENT_ID` in Railway Variables
2. Update `REDIRECT_URI` to your Railway domain
3. Register the redirect URI with Swiggy
4. Test the OAuth flow
5. Share the URL in your Swiggy application

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Build fails | Check `requirements.txt` has all deps |
| 500 error on `/` | Check `static/index.html` exists |
| OAuth fails | Verify `REDIRECT_URI` matches Railway URL |
| MCP calls fail | Verify `SWIGGY_CLIENT_ID` is set |
| Cold start slow | Railway doesn't cold start (unlike Render) |
