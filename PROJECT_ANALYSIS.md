# 📦 RPSU Complaint Box — Project Analysis

> A Flask-based anonymous complaint submission system for R. P. Shaha University.

---

## 📋 Table of Contents
1. [Location System](#1-location-system)
2. [Database Schema](#2-database-schema)
3. [One-Person One-Vote](#3-one-person-one-vote)
4. [Pages & Connections](#4-pages--connections)
5. [Future Improvements](#5-future-improvements)
6. [Worst Part](#6-worst-part)
7. [Code Summary](#7-code-summary)
8. [Dark Mode](#8-dark-mode)

---

## 1. 📍 Location System

A **geo-fence gate** — only users physically on campus can submit complaints anonymously.

### How it flows

```
Page loads
  └─► DOMContentLoaded fires getUserLocation()          [getlocation.js:72]
        └─► browser asks for GPS permission
              ├─► DENIED  → showLocationError()          [getlocation.js:55]
              └─► GRANTED → POST /location {lat, lon}    [getlocation.js:8]
                              └─► haversine() calculates distance from RPSU
                                    ├─► distance ≤ 2km → showForm()     ✅
                                    └─► distance > 2km → showWarning()  ❌
```

### Key details

| What | Where | Value |
|---|---|---|
| RPSU base coordinates | `app.py:26–27` | `23.601004, 90.498348` |
| Allowed radius | `app.py:52` | **2 km** |
| Distance formula | `app.py:30–35` | Haversine (great-circle distance) |
| Retake button | `getlocation.js:44` | Re-runs full flow from scratch |

### ⚠️ What it does NOT do
- No re-check on form submission — user can move away after passing
- Logged-in users skip the index entirely → bypass the geo-fence (`app.py:148`)
- **No server-side enforcement** — anyone can `curl /submit` directly

---

## 2. 🗄️ Database Schema

**SQLite** at `instance/complaints.db` · **4 tables**

### `user` — Student accounts (`app.py:63`)
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String(100) | Full name |
| `student_id` | String(50) UNIQUE | University ID |
| `email` | String(120) UNIQUE | Must be `@rpsu.edu.bd` |
| `password_hash` | String(128) | Werkzeug `pbkdf2:sha256` |
| `created_at` | DateTime | UTC timestamp |

### `complaint` — Anonymous submissions (`app.py:75`)
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | — |
| `reference_id` | String UNIQUE | Format: `RPSU-<uuid4>` |
| `department` | String(50) | e.g. `administration`, `library` |
| `category` | String(50) | e.g. `harassment`, `infrastructure` |
| `subject` | String(200) | Short title |
| `complaint` | Text | Full body |
| `priority` | String(20) | `low` / `medium` / `high` |
| `status` | String(20) | `pending` / `in_progress` / `resolved` |
| `image_path` | String nullable | `uploads/<uuid>_<filename>` |
| `agree_count` | Integer | Denormalized counter |
| `disagree_count` | Integer | Denormalized counter |
| `created_at` | DateTime | UTC timestamp |
| `flagged_at` | DateTime nullable | Set when disagree ≥ 65% |

> No FK to `user` — complaints are **fully anonymous by design**

### `vote` — Voting records (`app.py:105`)
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | — |
| `user_id` | FK → `user.id` | Who voted |
| `complaint_id` | FK → `complaint.id` | What they voted on |
| `vote_type` | String(10) | `'agree'` or `'disagree'` |
| `created_at` | DateTime | UTC timestamp |

> **Unique constraint** on `(user_id, complaint_id)` — DB-level one-vote enforcement

### `admin` — Admin accounts (`app.py:115`)
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | — |
| `username` | String(100) UNIQUE | Default: `admin` |
| `password_hash` | String(128) | Default: `admin123` (seeded on startup) |

### Relationships
```
user (1) ────────── (many) vote (many) ────────── (1) complaint
user ──── no direct link ──── complaint   ← anonymity by design
```

---

## 3. ✅ One-Person One-Vote

Enforced at **4 layers**:

| Layer | Where | How |
|---|---|---|
| **DB constraint** | `app.py:113` | `UniqueConstraint('user_id', 'complaint_id')` — DB rejects duplicate inserts |
| **App logic** | `app.py:218–275` | Checks for existing vote before inserting |
| **Route guard** | `app.py:216,244` | `@login_required` — anonymous users can't vote |
| **UI state** | `feed.html:26`, `feed.js:40` | Server pre-marks voted buttons; JS updates after each call |

### Vote behavior matrix

| Had voted | Clicks | Result |
|---|---|---|
| Nothing | Agree | ➕ New agree vote |
| Agree | Agree | 🔄 Toggle off (vote removed) |
| Disagree | Agree | 🔀 Switch to agree |
| Nothing | Disagree | ➕ New disagree vote |
| Disagree | Disagree | 🔄 Toggle off (vote removed) |
| Agree | Disagree | 🔀 Switch to disagree |

---

## 4. 🗺️ Pages & Connections

**7 pages total**

```
/  (index.html)
├── location denied  ──► /login  ──► /feed
│                    ──► /register ──► /feed
└── location allowed ──► [complaint form] ──► POST /submit ──► success

/feed  [login required]
└── vote buttons ──► POST /api/complaint/<id>/agree|disagree

/admin/login
└── success ──► /admin
      ├── card click ──► /admin/complaint/<id>
      │     └── status dropdown ──► POST /admin/update_status/<id>
      └── settings modal ──► POST /admin/settings

/logout ──► /
/admin/logout ──► /admin/login
```

### Pages at a glance

| # | Route | Template | Auth | Purpose |
|---|---|---|---|---|
| 1 | `/` | `index.html` | Public | Geo-fenced complaint form |
| 2 | `/login` | `login.html` | Public | Student login |
| 3 | `/register` | `register.html` | Public | Student registration |
| 4 | `/feed` | `feed.html` | 🔒 Student | Complaint feed + voting |
| 5 | `/admin/login` | `admin_login.html` | Public | Admin login |
| 6 | `/admin` | `admin.html` | 🔒 Admin | Dashboard + filters |
| 7 | `/admin/complaint/<id>` | `view_complaint.html` | 🔒 Admin | Detail + status update |

### API endpoints

| Route | Method | Purpose |
|---|---|---|
| `/location` | POST | Geo-fence check |
| `/submit` | POST | Submit anonymous complaint |
| `/api/complaint/<id>/agree` | POST | Vote agree |
| `/api/complaint/<id>/disagree` | POST | Vote disagree |
| `/api/complaints` | GET | All complaints as JSON |
| `/api/stats` | GET | Counts by status |
| `/admin/update_status/<id>` | POST | Change complaint status |
| `/admin/settings` | POST | Update admin credentials |

---

## 5. 🔧 Future Improvements

### 🔴 High Priority (Security)

| # | Issue | Fix |
|---|---|---|
| 1 | **Location bypassable** — `/submit` has zero location check | Issue signed token from `/location`, validate in `/submit` |
| 2 | **Hardcoded secret key** — `app.py:13` committed to source control | Move to `.env` with `python-dotenv` |
| 3 | **Default `admin/admin123`** — seeded on every fresh install | Force password change on first login |
| 4 | **No CSRF protection** — all AJAX forms unprotected | Add `flask-wtf` CSRF tokens |
| 5 | **Denormalized vote counts** — can drift if votes deleted externally | Compute from `Vote` table or add reconciliation |

### 🟡 Medium Priority

| # | Issue | Fix |
|---|---|---|
| 6 | No email verification | Add confirmation email via Flask-Mail |
| 7 | No pagination — `.all()` on every load | Use SQLAlchemy `.paginate()` |
| 8 | No rate limiting | Add `flask-limiter` |
| 9 | Feed has no search/filter | Add department/category filters |
| 10 | Auto-delete job is silent | Add logging for audit trail |

### 🟢 Low Priority

| # | Issue | Fix |
|---|---|---|
| 11 | ~~`register.js` was empty~~ | ✅ Fixed — register logic moved to `register.js`, `login.js` now login-only |
| 12 | No complaint tracking page | Add `/track/<reference_id>` route |
| 13 | No admin notifications | Add email alerts or dashboard badge |
| 14 | Orphaned images on manual DB delete | Add cleanup on delete |

---

## 6. 💀 Worst Part

> **The geo-fence is client-side only — it's security theater.**

`app.py:40–57` has a perfectly working Haversine check on the server. But `/submit` (`app.py:152`) has **zero location validation**. Anyone can run:

```bash
curl -X POST http://localhost:5500/submit \
  -d "department=it&category=other&subject=test&complaint=test&priority=low"
```

...and the complaint is accepted from anywhere in the world.

Since complaints are **fully anonymous** (no user account linked), the location check was the only gate. It's trivially bypassed.

**The fix:** when `/location` returns `allowed: true`, generate a short-lived signed token (`itsdangerous.URLSafeTimedSerializer`). Client includes it in `/submit`. Server validates before accepting.

---

## 7. 📝 Code Summary

### Architecture
**Flask monolith** · SQLite via SQLAlchemy · Flask-Login (students) · custom session admin · Jinja2 templates · vanilla JS AJAX

### `app.py` — Section by Section

| Lines | What it does |
|---|---|
| 1–11 | Imports: Flask, SQLAlchemy, Flask-Login, Werkzeug, uuid, APScheduler |
| 13–20 | App config: secret key, DB path, upload folder, 16MB limit |
| 22–24 | `allowed_file()` — validates image extensions |
| 26–35 | RPSU coordinates + `haversine()` distance formula |
| 37–57 | `POST /location` — receives GPS, returns `{allowed, distance}` |
| 59–61 | DB + LoginManager init |
| 63–73 | `User` model |
| 75–103 | `Complaint` model |
| 105–113 | `Vote` model + unique constraint |
| 115–124 | `Admin` model |
| 126–130 | `@admin_required` decorator — checks `session['admin_logged_in']` |
| 132–139 | `update_disagree_flag()` — sets/clears `flagged_at` at 65% disagree |
| 141–150 | `GET /` — redirects logged-in users to feed |
| 152–185 | `POST /submit` — saves image, generates reference ID, creates complaint |
| 187–215 | Admin routes: dashboard, login, logout, settings, detail, status update |
| 217–230 | `GET /api/complaints` and `GET /api/stats` |
| 232–275 | `/register`, `/login`, `/logout` |
| 277–285 | `GET /feed` — loads complaints + builds `user_votes` dict |
| 287–320 | `POST /api/complaint/<id>/agree\|disagree` — toggle/switch/new vote logic |
| 322–330 | `db.create_all()` + seed default admin |
| 332–345 | APScheduler: runs `auto_delete_flagged_complaints()` every hour |
| 347–348 | `app.run(debug=True, host='0.0.0.0', port=5500)` |

### JS Files

| File | Purpose |
|---|---|
| `getlocation.js` | GPS on page load → POST `/location` → show form or warning |
| `script.js` | Dark mode, complaint form AJAX, char counter, validation |
| `feed.js` | Vote buttons → POST API → update counts + re-sort cards |
| `login.js` | Login form AJAX — email domain validation, POST `/login`, redirect to feed |
| `register.js` | Register form AJAX — email domain + password match validation, POST `/register`, redirect to feed |

---

## 8. 🌙 Dark Mode

Three layers work together: **CSS variables** (colors) · **`data-theme` attribute** (the switch) · **`localStorage`** (memory).

### Layer 1 — CSS Variables (`root.css`)

All colors are `var(--token)`. Two full sets are defined:

```css
:root                  { --bg-primary: #fcfaf2; --text-primary: #2d2d2a; ... }  /* light */
[data-theme="dark"]    { --bg-primary: #1a202c; --text-primary: #ffffff; ... }  /* dark  */
```

When `data-theme="dark"` is on `<body>`, every variable overrides at once. Extra explicit rules handle elements with hardcoded colors (inputs, cards, feed header, etc.).

### Layer 2 — Toggle Button (HTML)

Every page has two stacked icons — CSS shows/hides them:

```css
.theme-icon.moon                  { opacity: 0; transform: rotate(90deg); }   /* hidden by default */
[data-theme="dark"] .theme-icon.sun  { opacity: 0; transform: rotate(-90deg); }
[data-theme="dark"] .theme-icon.moon { opacity: 1; transform: rotate(0deg); }
```

`transition: all 0.3s ease` makes it a smooth rotation swap. ☀️ ↔ 🌙

### Layer 3 — JavaScript (`script.js`)

```
Click button
  └─► toggleTheme() reads body.getAttribute('data-theme')
        ├─► 'dark'  → body.removeAttribute('data-theme') + localStorage='light'
        └─► null    → body.setAttribute('data-theme','dark') + localStorage='dark'

Page load (DOMContentLoaded)
  └─► localStorage.getItem('theme') === 'dark' → setTheme('dark') immediately
        └─► No flash of wrong theme on navigation ✅
```

### ⚠️ Limitations
- Theme is **per-browser**, not per-account — different browser = light mode
- **No `prefers-color-scheme`** — OS dark mode setting is ignored
- Server has zero knowledge of the user's theme preference
