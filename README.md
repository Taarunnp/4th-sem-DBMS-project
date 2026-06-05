# 🏀 Basketball Players DBMS Mini Project

A DBMS mini project demonstrating **CRUD operations**, **triggers**, **stored
procedures**, **views**, and **JOIN/aggregate** queries using:

- **MySQL** — database (schema, triggers, stored procedures, view, sample data)
- **FastAPI** — Python REST backend
- **HTML/CSS/JS** — single-file dashboard frontend (`frontend/index.html`)

---

## 📁 Folder Structure

```
basketball-dbms/
├── backend/
│   ├── app.py             # FastAPI REST API
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # template for your MySQL password
├── frontend/
│   └── index.html         # the dashboard UI (open in a browser)
├── database/
│   └── schema.sql         # run once to build the database
├── .gitignore
└── README.md
```

---

## 🚀 Run It Locally

### 1. Build the database

Make sure MySQL is running, then load the schema:

```bash
mysql -u root -p < database/schema.sql
```

This creates `basketball_db` with tables, triggers, stored procedures, a view,
and sample data (2 teams, 10 players).

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt

# tell the API your MySQL password (do NOT hardcode it)
export MYSQL_PASSWORD="your_mysql_root_password"     # macOS/Linux
# set MYSQL_PASSWORD=your_mysql_root_password         # Windows CMD

uvicorn app:app --reload
```

The API runs at **http://127.0.0.1:8000** (interactive docs at `/docs`).

### 3. Open the frontend

Open `frontend/index.html` in your browser (double-click it, or right-click →
Open With → your browser). It talks to the backend at `127.0.0.1:8000` and shows
a live dashboard, player/team CRUD, analytics, and the audit log.

> The header shows a green **API Online** dot when the backend is reachable.

---

## 🌐 Hosting on GitHub Pages (data shows with no backend)

GitHub Pages only hosts the **static frontend**, but the page is **never empty**:
`frontend/index.html` ships with an embedded copy of the `schema.sql` sample data
(2 teams, 10 players) and falls back to it automatically when no backend is
reachable. So your GitHub Pages link shows the full dashboard, players, teams,
stats, and audit log out of the box. A gold **"Demo Data"** pill in the header
indicates this offline mode, and Add/Edit/Delete still work in-memory (mirroring
the SQL triggers) for a live demo — changes just reset on refresh.

To run on **real, persistent MySQL data** instead, point the page at a running
backend — no file edit needed, just add a query parameter:

```
index.html?api=https://your-backend-url.com
```

When the backend responds, the pill turns green (**"API Online"**) and every
action is saved to MySQL. See `DEPLOYMENT.md` for a free Aiven + Render setup.

> Tip: add `?demo` to force the embedded demo data even if a backend is running.

---

## 🧠 DBMS Concepts Demonstrated

| Concept | Where |
|---|---|
| Primary / Foreign keys | `teams`, `players` in `database/schema.sql` |
| Trigger | `trg_after_player_insert`, `trg_after_player_delete` (sync `player_count` + write `player_audit`) |
| Stored Procedure | `GetTeamStats`, `GetTopScorers` |
| View | `v_player_roster` |
| JOIN | `/players`, `/stats/team-averages` |
| Aggregate (AVG / COUNT / MAX, GROUP BY) | `/stats/team-averages`, `GetTeamStats` |

---

## 📡 API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/players` | list players (JOIN with team) |
| POST | `/players` | create player |
| PUT | `/players/{id}` | update player |
| DELETE | `/players/{id}` | delete player |
| GET / POST | `/teams` | list / create team |
| DELETE | `/teams/{id}` | delete team |
| GET | `/stats/top-scorers?limit=5` | stored procedure |
| GET | `/stats/team/{team_id}` | stored procedure |
| GET | `/stats/team-averages` | GROUP BY aggregate |
| GET | `/audit` | trigger-populated log |
