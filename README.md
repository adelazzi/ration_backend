# Ration

Ration is a web app for concrete block yards. A manager enters how many full and half blocks a job needs, sees what each mixture (sand, stone and cement per batch) would need in tonnes and cost for the whole project, chooses one, adjusts the project's prices if needed, and sends it to an accountant for approval. Completed projects are saved as history with the prices that were used.

Built with Django 6.1 and server-rendered templates. It runs on SQLite locally and on Postgres in production (Render).

## Product documentation

The [requirements documentation](docs/README.md) describes the product vision and scope,
stakeholders and personas, use cases, user stories, and software requirements. It is based on
the current implementation and the latest customer meeting notes. Outstanding requests and
questions are distinguished from implemented behaviour.

## Contents

- [Product documentation](#product-documentation)
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Running the app](#running-the-app)
- [Sharing it with ngrok](#sharing-it-with-ngrok)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [How costs are calculated](#how-costs-are-calculated)
- [Tests](#tests)
- [Deployment (Render + GitHub Actions)](#deployment-render--github-actions)
- [Troubleshooting](#troubleshooting)

## Features

**Roles**

| Role | Can do |
|---|---|
| Manager | Create, edit and delete projects (while they're drafts), choose the project's mixture, set the project's material prices (drafts and pending projects), add mixes, materials and default prices, move projects through their statuses. |
| Accountant | Approve or decline material prices (optionally replacing a wrong price), approve or decline projects that are waiting for approval. |
| Creator | Read approved and completed projects only. |
| Superuser | Everything, plus the Django admin at `/admin/`. |

There is no public sign-up. Accounts are created by an administrator in `/admin/` → **Users** → **Add user** (username, email, full name, role, password). People log in with their **email** and password.

**Project status flow**

```
Draft ──Send for approval──▶ Pending ──Approve (accountant)──▶ Approved ──Mark completed──▶ Completed
  ▲                             │
  └──Back to draft / Decline────┘
```

- **Draft**: everything can be edited.
- **Pending**: only the project's material prices can change. The manager moves it back to draft to edit anything else.
- **Approved**: nothing can be edited. Visible to creators.
- **Completed**: the total, the mixture and the prices are saved as a snapshot and the project is locked for good.

**Prices**

- **Default prices** apply to every project. They're added on the **Materials** page and wait for an accountant's approval before they're used.
- **Project prices** are set by the manager on the project page and apply to that project only. They're used straight away; the accountant checks them when approving the project and can decline it with a comment such as "the sand price is too high".
- Quantities and prices are shown **per tonne**, with wheelbarrows and bags as a smaller second line for the people mixing on site. Each material has a weight per unit (starting values: sand 0.100 t and stone 0.090 t per wheelbarrow, cement 0.050 t per bag), editable on its material page.
- Default prices can be entered per tonne, per unit (wheelbarrow, bag) or per cubic metre for sand and stone (1 m³ = 16 wheelbarrows).

## Requirements

- Python 3.12 or newer (production uses 3.13)
- pip and `venv`
- Git
- Optional: Postgres 16, only if you want to run against Postgres locally. Docker is the easiest way.

## Setup

```bash
git clone https://github.com/adelazzi/ration_backend.git
cd ration_backend
```

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create your local settings file. With `DJANGO_DEBUG=true` and no `DATABASE_URL`, the app uses a local SQLite file (`db.sqlite3`):

```bash
cp .env.example .env
```

Create the database tables. This also loads the starting data: the materials **Sand**, **Stone 13mm** and **Cement 50kg**, and the mixes **Batch 1** to **Batch 4**.

```bash
python manage.py migrate
```

Create the first admin account (you'll be asked for a username, email and password):

```bash
python manage.py createsuperuser
```

Optional: load the sample Cape Town prices (sand R 16.43 and stone R 21.75 per wheelbarrow, cement R 85.00 per bag, which is R 164.30, R 241.67 and R 1,700.00 per tonne) as approved prices, recorded under an existing user's email:

```bash
python manage.py load_cape_town_prices admin@example.com
```

## Running the app

```bash
python manage.py runserver
```

Open http://localhost:8000 and log in with the email and password of the account you created.

First steps after logging in as the superuser:

1. Go to http://localhost:8000/admin/ → **Users** and create a manager and an accountant (or give your own account a role).
2. As a manager, open **New project**, enter the block counts and pick one of the mixtures. Each mixture shows the tonnes of each material and the total for the project as you type.
3. Click **Send for approval**. As an accountant, open the project and click **Approve**.
4. As a manager, click **Mark completed** to save the project as history.

## Sharing it with ngrok

[ngrok](https://ngrok.com) gives your computer a public HTTPS link, so someone else (a professor, a client) can use the app running on your machine with your local data. The link works only while you keep it running.

**One-time setup**

1. Create a free account at https://ngrok.com and [install ngrok](https://ngrok.com/download).
2. Sign in from the terminal with the token from https://dashboard.ngrok.com/get-started/your-authtoken:

   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

3. Optional but recommended: claim your free fixed domain at https://dashboard.ngrok.com/domains and add it to `.env`, so the link is the same every time:

   ```
   NGROK_DOMAIN=your-name.ngrok-free.app
   ```

**Every time you want to share**

```bash
./share.sh
```

The script applies migrations, collects the CSS files, starts the app with gunicorn and **debug mode off** on port 8001 (so it doesn't clash with `runserver` on 8000), and opens the tunnel. It prints the link to give out. Press Ctrl+C to stop both the app and the link. Use `PORT=8002 ./share.sh` for another port.

**Good to know**

- On the free plan, visitors first see an ngrok page saying they're about to visit a site served by ngrok; they click **Visit Site** once.
- Give each tester their own account in `/admin/` (for example one manager and one accountant to try the approval flow). Don't share your own password.
- Visitors see your real local projects and prices.
- The deployed Render site is an alternative link that works even when your computer is off.

## Configuration

Settings are read from environment variables, or from a `.env` file in the project folder for local development.

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_DEBUG` | `false` | `true` for local development. Never `true` in production. |
| `DJANGO_SECRET_KEY` | none | Required when debug is off. Render generates one. |
| `DATABASE_URL` | local SQLite | Postgres connection string, e.g. `postgres://user:pass@host:5432/ration`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names the site answers to. Render's own host name is added automatically. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Extra trusted origins, e.g. a custom domain `https://ration.example.com`. |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` | Redirect HTTP to HTTPS when debug is off. Set to `false` only for tests. |
| `DJANGO_HSTS_SECONDS` | `3600` | HSTS duration when debug is off. |
| `DJANGO_EMAIL_BACKEND` | console (debug) / SMTP | The app doesn't send email yet. |
| `DJANGO_NGROK` | `false` | Allows `*.ngrok-free.app` and other ngrok addresses. `share.sh` turns it on. |
| `NGROK_DOMAIN` | unset | Your fixed ngrok domain, used by `share.sh`. |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | unset | Used once by `build.sh` on Render to create the first admin. Remove them after the first deploy. |

## Project structure

```
ration_backend/
├── manage.py                     Django command-line entry point
├── requirements.txt              Python dependencies
├── build.sh                      Render build: install, collect static files, migrate
├── share.sh                      Share the local app through an ngrok tunnel
├── render.yaml                   Render blueprint: web service + Postgres database
├── .env.example                  Template for local settings
├── .python-version               Python version used on Render and in CI
├── .github/workflows/deploy.yml  Tests on Postgres, then triggers a Render deploy
│
├── config/                       Project settings
│   ├── settings.py               Environment-based settings, database, static files, security
│   ├── urls.py                   Routes: /admin/, accounts and core
│   ├── wsgi.py / asgi.py         Server entry points (gunicorn uses wsgi.py)
│
├── accounts/                     Users and login
│   ├── models.py                 Custom User: email, full name, role and the role rules
│   ├── admin.py                  Admin pages for creating and editing users
│   ├── forms.py / views.py       Email + password login, logout
│   ├── templates/accounts/       Login page and its layout
│   ├── migrations/
│   └── tests.py
│
└── core/                         Projects, mixes, materials and prices
    ├── models.py                 Project, ProjectBlock, Material, MixRatio, MixIngredient,
    │                             MaterialPrice, ProjectEstimate, EstimateMaterial, ProjectApproval
    ├── services.py               Cost calculation, price lookup, saving estimate snapshots
    ├── views.py                  All pages and actions, with role and status checks
    ├── forms.py                  Project (with mixture), mix (fixed materials), material and price forms
    ├── permissions.py            manager_required, price_reviewer_required, ...
    ├── urls.py                   /projects/..., /mixes/, /materials/, /history/
    ├── admin.py                  Admin pages for the core tables
    ├── templatetags/ration.py    money, measure, recipe bars and material colours
    ├── management/commands/
    │   └── load_cape_town_prices.py
    ├── static/core/ration.css    All styles (navy theme)
    ├── templates/
    │   ├── 403.html              "You can't open this page"
    │   └── core/                 Pages (project list, project form for new/edit, project detail,
    │                             mixes and prices)
    │                             and partials (files starting with _)
    ├── migrations/               Tables, starting materials and mixes, data fixes
    └── tests.py
```

**Main pages**

| URL | Page |
|---|---|
| `/login/` | Log in |
| `/projects/` | Project list with status filters and search |
| `/projects/new/` | Create a project (managers) |
| `/projects/<id>/` | Project total, mixture, materials in tonnes, project prices and status |
| `/projects/<id>/edit/` | Edit a draft project (managers) |
| `/mixes/` | All mixtures (batch recipes) |
| `/config/mixes/new/`, `/config/mixes/<id>/` | Create or edit a mixture |
| `/materials/` | Materials, their weight per unit and default prices; add a material or a default price |
| `/history/` | Every default and project price, filtered by status; accountants approve or decline here |
| `/admin/` | Django admin (superusers) |

## How costs are calculated

A project uses one mixture for all its blocks. A mixture marked "both" can be used for any project; a half-only or full-only mixture only for projects with just that kind of block.

1. **Batches** = block count ÷ blocks per batch, rounded up, separately for full and half blocks.
2. **Material quantity** = quantity per batch × batches, in the material's own unit (wheelbarrows of sand and stone, bags of cement), added up for full and half blocks.
3. **Tonnes** = quantity × the material's tonnes per unit.
4. **Unit price** = the project's own price for that material if it has one, otherwise the latest approved default price. A price per tonne is multiplied by the tonnes per unit, and a price per m³ is divided by 16 for a wheelbarrow.
5. **Total** = sum of quantity × unit price for every material. **Cost per block** = total ÷ blocks.

## Tests

```bash
python manage.py test
```

To run the tests the same way CI does, against Postgres with production settings:

```bash
docker run -d --rm --name ration-pg -e POSTGRES_USER=ration -e POSTGRES_PASSWORD=ration -e POSTGRES_DB=ration -p 5432:5432 postgres:16
```

```bash
DATABASE_URL=postgres://ration:ration@localhost:5432/ration DJANGO_DEBUG=false DJANGO_SECRET_KEY=local-test-secret-key-long-enough-to-pass-checks DJANGO_SECURE_SSL_REDIRECT=false python manage.py collectstatic --no-input && DATABASE_URL=postgres://ration:ration@localhost:5432/ration DJANGO_DEBUG=false DJANGO_SECRET_KEY=local-test-secret-key-long-enough-to-pass-checks DJANGO_SECURE_SSL_REDIRECT=false python manage.py test
```

```bash
docker stop ration-pg
```

## Deployment (Render + GitHub Actions)

The app is deployed to [Render](https://render.com). GitHub Pages can't host it, because it needs a Python server and a database.

**One-time setup**

1. In Render, choose **New → Blueprint** and select this repository. Render reads `render.yaml` and creates the `ration` web service and the `ration-db` Postgres database. It also generates `DJANGO_SECRET_KEY` and connects `DATABASE_URL`.
2. In Render, open **ration → Settings → Deploy Hook** and copy the URL.
3. In GitHub, open **Settings → Secrets and variables → Actions** and add it as the secret `RENDER_DEPLOY_HOOK_URL`.
4. To create the first admin online, set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` on the Render service, deploy once, then delete them.

**Every push to `main`**

The workflow in `.github/workflows/deploy.yml`:

1. Runs the tests against a temporary Postgres 16 with production settings, after checking for missing migrations and collecting static files.
2. If they pass, calls the Render deploy hook.
3. Render then runs `build.sh` (install, `collectstatic`, `migrate`) and starts `gunicorn config.wsgi:application`.

Pull requests run the tests only.

**Limits of the free plan**

- The web service sleeps when unused, so the first visit afterwards takes about a minute.
- The free Postgres database expires after 30 days unless upgraded.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ImproperlyConfigured: Set DJANGO_SECRET_KEY` | Create `.env` from `.env.example` (sets `DJANGO_DEBUG=true`), or set `DJANGO_SECRET_KEY`. |
| Styles look old after an update | Hard-refresh the page (Ctrl+Shift+R). |
| A project shows no total | Choose a mixture, and make sure every material in it has a price (a default price or a project price). |
| "You can't open this page" | Your role doesn't allow that page. An administrator can change your role in `/admin/`. |
| `git push` asks for a password | GitHub needs a personal access token or `gh auth login`, not your account password. |
| `load_cape_town_prices` says no user | Create the user first (`createsuperuser` or `/admin/`), then pass that user's email. |
