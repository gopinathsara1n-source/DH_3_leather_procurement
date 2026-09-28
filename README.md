# Sample Management — Streamlit + Supabase

A native Streamlit sample-order management application.

## Features

- WIP Sample tab
- Completed Sample tab
- Add Sample tab
- Global search bar
- Buyer filter
- Supplier filter
- Article filter
- Color filter
- Automatic Unique ID:
  `Indent No. | Article | Color`
- New records automatically start as `WIP`
- Mark a WIP sample as `Completed`
- Delivered date captured when completing
- Lead Days:
  - WIP = today - order date
  - Completed = delivered date - order date
- Completed records automatically appear in the Completed tab
- Native Streamlit UI only
- No custom CSS
- No HTML
- Supabase database

## 1. Create the Supabase table

Open Supabase SQL Editor and run:

`supabase_schema.sql`

## 2. Add Streamlit secrets

Create:

`.streamlit/secrets.toml`

with:

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
```

For Streamlit Community Cloud, put the same values into:

App → Settings → Secrets

## 3. Install

```bash
pip install -r requirements.txt
```

## 4. Run

```bash
streamlit run app.py
```

## Data behavior

There is one `samples` table.

A sample is not physically copied to another table when completed.

Instead:

- `status = WIP` → shown in Sample tab
- `status = Completed` → shown in Sample Completed tab

This avoids duplicate records and keeps reporting consistent.
