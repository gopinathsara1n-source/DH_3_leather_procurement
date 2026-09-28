# Sample Management — Streamlit + Supabase

Native Streamlit sample management application backed by Supabase.

## Tabs

1. **Sample** — WIP samples
2. **Sample Completed** — completed samples
3. **Add Sample** — create a new WIP sample

## Add Sample behavior

- Buyer is a dropdown containing the standard buyers.
- Buyer also accepts a custom typed value for exceptions.
- Supplier is a dropdown containing the standard suppliers.
- Supplier also accepts a custom typed value for exceptions.
- Thickness is a text field because values are ranges such as `0.6-0.7`.
- Quantity uses a step of `1000`; the user can still type a different quantity when required.
- Avg. Area is required.
- Status is automatically `WIP`.
- Unique ID is automatically generated from:
  `Indent No. | Article | Color`

## Important validation behavior

The form intentionally does **not** use `clear_on_submit=True`.

If a required field is missing, a duplicate Unique ID is found, or Supabase returns an error, the values already entered remain available. The user only needs to correct the problem and submit again.

After a successful save, the application refreshes and the sample appears in the WIP tab.

## Supabase setup

Run `supabase_schema.sql` in the Supabase SQL Editor.

Then configure Streamlit secrets:

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
```

For Streamlit Community Cloud, put these values in the app's Secrets settings.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Existing table warning

If the previous version of the table was already created with:

```sql
thickness_mm numeric
```

change it to text before using this version:

```sql
alter table public.samples
alter column thickness_mm type text
using thickness_mm::text;
```

The new version needs text because thickness is stored as ranges such as `0.6-0.7`.
