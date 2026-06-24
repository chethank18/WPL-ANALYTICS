# 🏏 WPL Analytics

A Streamlit dashboard for exploring Women's Premier League (WPL) ball-by-ball
data — batting and bowling leaderboards, team win/loss summaries, player
profiles, boundary maps, phase analysis, and match trends.

Data source: [Cricsheet.org](https://cricsheet.org/)

📦 **Repo:** [github.com/chethank18/WPL-ANALYTICS](https://github.com/chethank18/WPL-ANALYTICS)
🔗 **Live demo:** _add your deployed URL here once live_

---

## Features

- **Batting & Bowling leaderboards** — top run scorers, top wicket takers,
  strike rate, economy, average
- **Team summary** — win/loss record, win %, toss impact on results
- **Player Profile** — career stats, runs/economy by phase, dismissal types,
  season-by-season trend
- **Field & Strengths** — boundary map and a strength/weakness radar by
  match phase (Powerplay / Middle / Death)
- **Phase Analysis** — run rate by over, best batters/bowlers per phase
- **Match Trends** — runs and wickets per match over time
- Filters by **season** and **team**, with all stats split correctly by
  batting/bowling side

---

## Project structure

```
WPL-ANALYTICS/
├── app.py                  # Main Streamlit app (UI, tabs, charts)
├── utils/
│   ├── analysis.py         # Data loading + aggregate stats (batters, bowlers, teams, phases)
│   ├── player.py           # Per-player batting/bowling profile builders
│   └── field_viz.py        # Boundary map + strength/weakness radar charts
├── data/
│   └── wpl_combined.csv    # Ball-by-ball match data
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Running locally

```bash
# 1. Clone the repo
git clone https://github.com/chethank18/WPL-ANALYTICS.git
cd WPL-ANALYTICS

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deployment

### ⚠️ Vercel will not work for this app

Vercel hosts static sites and short-lived serverless functions. Streamlit
needs a persistent running Python process, so a plain Vercel deploy will
fail or simply not start the app. Use one of the options below instead.

### Option A — Streamlit Community Cloud (easiest, free)

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **New app**, select this repo, branch (`main`), and main file
   (`app.py`).
3. Click **Deploy**.

You'll get a live URL like `https://your-app-name.streamlit.app`.

### Option B — Render / Railway / Fly.io (Docker-based, more control)

1. Add a `Dockerfile` to the repo:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. Push the change to GitHub.
3. Connect the repo on Render/Railway/Fly.io and let it build from the
   Dockerfile.

---

## Data

`data/wpl_combined.csv` contains one row per ball, with columns including:
`match_id`, `date`, `season`, `venue`, `batting_team`, `bowling_team`,
`batter`, `bowler`, `over`, `runs_batter`, `runs_total`, `extras_type`,
`wicket_type`, `player_dismissed`, `toss_winner`, `toss_decision`, `winner`.

Team names are normalized in `load_data()` (e.g. "Royal Challengers
Bangalore" → "Royal Challengers Bengaluru") so renamed/aliased teams don't
appear twice in filters and charts. To add another alias, edit
`TEAM_NAME_MAP` in `utils/analysis.py`.

---

## Notes on the dashboard logic

- Batting/Bowling tabs and the Player Profile tab use **directional**
  filters (`batting_filtered` / `bowling_filtered`) so selecting a team
  only shows that team's own batters/bowlers, not their opponents'.
- The player dropdowns on the **Player Profile** and **Field & Strengths**
  tabs share selection state, so picking a player on one tab carries over
  to the other.

---

## Built with

[Streamlit](https://streamlit.io/) · [Plotly](https://plotly.com/python/) ·
[Pandas](https://pandas.pydata.org/)
