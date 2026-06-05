# 🚀 Deploying the Live Version (Aiven MySQL + Render + GitHub Pages)

This makes the project fully live with working Add/Edit/Delete, reachable from
your GitHub Pages link. Three pieces: **database** (Aiven), **backend**
(Render), **frontend** (GitHub Pages, already deployed).

Do them in this order.

---

## PART 1 — Database on Aiven (MySQL)

1. Go to **https://aiven.io** → Sign up (no credit card needed).
2. Click **Create service** → choose **MySQL**.
3. Pick the **Free** plan, any cloud/region close to you (e.g. an India or
   nearest region), give it a name like `basketball-mysql`, → **Create**.
4. Wait until the service status turns from "Rebuilding" to **Running**
   (a few minutes).
5. Open the service. On the **Overview** tab you'll see connection details.
   Note these down — you'll paste them into Render in Part 2:
   - **Host** (something like `mysql-xxxx.aivencloud.com`)
   - **Port** (a 5-digit number, NOT 3306)
   - **User** (usually `avnadmin`)
   - **Password** (click the eye icon to reveal)
   - **Database name** (usually `defaultdb`)

### Load the schema into Aiven
You need to run `database/schema.sql` against the Aiven database once.

Easiest way — from your Mac terminal (uses the MySQL client you already
installed locally):

```bash
mysql -h YOUR_AIVEN_HOST -P YOUR_AIVEN_PORT -u avnadmin -p \
  --ssl-mode=REQUIRED defaultdb < database/schema.sql
```

It prompts for the Aiven password. One change to make first: the script starts
with `DROP DATABASE / CREATE DATABASE basketball_db; USE basketball_db;`. On
Aiven you typically use the existing `defaultdb`, so either:
  - **Option A (simplest):** edit `schema.sql` — delete the 3 lines
    `DROP DATABASE...`, `CREATE DATABASE...`, and change nothing else; the
    tables will go into `defaultdb`. Then set `MYSQL_DB=defaultdb` in Render.
  - **Option B:** keep the script as-is if your Aiven user is allowed to create
    databases, then set `MYSQL_DB=basketball_db` in Render.

Verify it loaded:
```bash
mysql -h YOUR_AIVEN_HOST -P YOUR_AIVEN_PORT -u avnadmin -p \
  --ssl-mode=REQUIRED defaultdb -e "SELECT COUNT(*) FROM players;"
```
You should see 10.

---

## PART 2 — Backend on Render

1. Make sure this whole project is pushed to your GitHub repo.
2. Go to **https://render.com** → Sign up (connect your GitHub account).
3. Click **New +** → **Web Service** → pick your repo.
4. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. Scroll to **Environment Variables** and add these (values from Aiven Part 1):

   | Key | Value |
   |---|---|
   | `MYSQL_HOST` | your Aiven host |
   | `MYSQL_PORT` | your Aiven port (the 5-digit one) |
   | `MYSQL_USER` | `avnadmin` |
   | `MYSQL_PASSWORD` | your Aiven password |
   | `MYSQL_DB` | `defaultdb` (or `basketball_db` if you used Option B) |
   | `MYSQL_SSL` | `true` |

6. Click **Create Web Service**. Wait for the build + deploy to finish.
7. You'll get a URL like `https://basketball-dbms-api.onrender.com`.
   Open it — you should see:
   `{"message":"Basketball Players API is running. Visit /docs"}`
   Also try `.../players` — you should see JSON player data.

> Note: the free Render service sleeps after ~15 min idle. The first request
> after that takes 30–60 seconds to wake up. Open the URL once a minute before
> your demo so it's warm.

---

## PART 3 — Point the frontend at the live backend

Your frontend reads the backend URL from a `?api=` parameter, so you don't even
need to edit the file. Just visit your GitHub Pages link with the API URL
appended:

```
https://taarunnp.github.io/4TH-SEM-DBMS-PROJECT-/?api=https://basketball-dbms-api.onrender.com
```

The status dot turns green ("API Online") and all data loads — including live
Add/Edit/Delete.

### Optional: bake the URL in so you don't need the ?api= each time
Edit `frontend/index.html`, find this line near the bottom script:

```js
const API = (new URLSearchParams(location.search).get('api')
  || 'http://127.0.0.1:8000').replace(/\/$/, '');
```

Change the fallback `'http://127.0.0.1:8000'` to your Render URL, commit, and
push. Then the plain GitHub Pages link works with no parameter.

---

## Quick troubleshooting

- **Status stays "Connecting…" / data empty:** the backend URL is wrong or the
  service is asleep. Open the Render URL directly first to wake it, check
  `.../players` returns JSON.
- **Backend shows "DB connection failed":** an `MYSQL_*` value is wrong, or
  `MYSQL_SSL` isn't set to `true`. Double-check host/port/password from Aiven.
- **CORS error in browser console:** the backend already allows all origins, so
  this usually means the request never reached the backend — again a URL/sleep
  issue.
- **Aiven powered off:** free Aiven services power off when unused; open the
  Aiven console and power it back on before demoing.
