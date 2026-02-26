# Deployment Guide: Streamlit Cloud + Supabase

This guide walks you through deploying the Dip-SIP app online with authentication and persistent storage.

---

## Prerequisites

1. GitHub account with `v-bansal/dip_sip` repo access
2. Supabase account (free tier is fine)
3. Streamlit Community Cloud account (free)

---

## Step 1: Create Supabase database

### 1.1 Create a new project
1. Go to [supabase.com](https://supabase.com)
2. Click **New Project**
3. Choose organization, name it `dip-sip`, set a strong database password
4. Wait ~2 minutes for provisioning

### 1.2 Run the schema SQL
1. Open **SQL Editor** (left sidebar)
2. Click **New query**
3. Copy the entire contents of `storage/supabase_schema.sql` from this repo
4. Paste into the editor and click **Run**
5. Verify tables created: go to **Table Editor** → you should see `prices`, `runs`, `ledgers`

### 1.3 Get API credentials
1. Go to **Settings** → **API**
2. Copy:
   - **Project URL** (e.g., `https://abcxyz.supabase.co`)
   - **anon public** key (starts with `eyJ...`)
3. Keep these for Step 3

---

## Step 2: Generate authentication cookie key

On your Mac terminal:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

Copy the output (32-character hex string). You'll use this in Step 3.

---

## Step 3: Deploy to Streamlit Community Cloud

### 3.1 Sign in
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account (`v-bansal`)

### 3.2 Create new app
1. Click **New app**
2. Fill in:
   - **Repository:** `v-bansal/dip_sip`
   - **Branch:** `dev`
   - **Main file path:** `app.py`
3. Click **Advanced settings**

### 3.3 Add secrets
In the **Secrets** text box, paste:

```toml
# Authentication
auth_cookie_name = "dip_sip_auth"
auth_cookie_key = "PASTE_YOUR_32_CHAR_KEY_FROM_STEP_2"
auth_cookie_expiry_days = 30

# Supabase
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_ANON_KEY_FROM_STEP_1"
```

**Replace:**
- `PASTE_YOUR_32_CHAR_KEY_FROM_STEP_2` → your generated key from Step 2
- `YOUR_PROJECT.supabase.co` → your Supabase project URL from Step 1.3
- `YOUR_ANON_KEY_FROM_STEP_1` → your Supabase anon key from Step 1.3

### 3.4 Deploy
1. Click **Deploy**
2. Wait ~2-3 minutes for build
3. Your app is live at `https://your-app.streamlit.app`

---

## Step 4: First login

### Default credentials
The app ships with demo accounts (defined in `config/credentials.yaml`):

- **Admin:** username `admin`, password `admin123`
- **Viewer:** username `viewer`, password `viewer123`

### Change passwords (REQUIRED for production)

1. On your Mac, in the `dip_sip` folder:
   ```bash
   python3 -c "import bcrypt; print(bcrypt.hashpw('your_new_password'.encode(), bcrypt.gensalt()).decode())"
   ```
2. Copy the output hash (starts with `$2b$12$...`)
3. Edit `config/credentials.yaml`:
   ```yaml
   credentials:
     usernames:
       admin:
         password: $2b$12$YOUR_NEW_HASH_HERE
   ```
4. Commit and push:
   ```bash
   git add config/credentials.yaml
   git commit -m "chore: update admin password"
   git push origin dev
   ```
5. Streamlit Cloud auto-redeploys in ~1 minute

---

## Step 5: Upload data

1. Log in to your deployed app
2. Go to **Data Manager** (left sidebar)
3. Select index: **NIFTY 50**, series type: **TRI**
4. Upload your CSV (columns: `Date`, `Close`)
5. Click **Save to cache**
6. Data is now in Supabase (permanent)
7. Go back to **Dashboard** → select `NIFTY50 / TRI / upload_csv`

---

## Step 6: Access control (optional)

### Option A: Private app (invite-only)
1. In Streamlit Cloud, go to your app settings
2. **Sharing** → **Access control**
3. Set to **Restricted**
4. Invite users by email (they need GitHub accounts)

### Option B: Keep public but require login
- Already done! Only users with credentials in `credentials.yaml` can access

### Option C: Add more users
Edit `config/credentials.yaml` and add entries:
```yaml
credentials:
  usernames:
    newuser:
      email: user@example.com
      name: User Name
      password: $2b$12$...  # Generate hash as in Step 4
```

---

## Verification checklist

- ✅ Supabase tables created (`prices`, `runs`, `ledgers`)
- ✅ Streamlit app deployed and accessible
- ✅ Login works with demo credentials
- ✅ Default passwords changed
- ✅ Data uploaded and cached in Supabase
- ✅ Backtest runs successfully
- ✅ Ledger saved and viewable in Run Viewer

---

## Troubleshooting

### Build fails on Streamlit Cloud
- Check **App logs** → look for `ModuleNotFoundError`
- Confirm `requirements.txt` includes all dependencies

### "Unable to connect to Supabase"
- Go to Streamlit app **Settings** → **Secrets**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Test connection: go to Supabase SQL Editor → run `SELECT 1;`

### "Table 'prices' does not exist"
- Re-run `storage/supabase_schema.sql` in Supabase SQL Editor
- Check **Table Editor** to confirm tables exist

### Login fails with correct password
- Verify `auth_cookie_key` in secrets matches between local `.streamlit/secrets.toml` and Streamlit Cloud
- Clear browser cookies for `streamlit.app`

### Data not persisting
- Confirm app is using Supabase (check logs for "Using SupabaseCache")
- If using SQLite accidentally, add secrets as in Step 3.3

---

## Costs

| Service | Tier | Cost | Limits |
|---|---|---|---|
| Streamlit Cloud | Free | $0/month | 1 app, unlimited visitors |
| Supabase | Free | $0/month | 500MB database, 2GB bandwidth |

**Estimated usage for this app:**
- NIFTY 50 TRI (2000-2024): ~6,000 rows × 4 indices = 24,000 rows ≈ 2MB
- 100 backtest runs with ledgers: ~1MB
- **Total:** ~5-10MB (well within free tier)

---

## Support

If you encounter issues:
1. Check **App logs** in Streamlit Cloud dashboard
2. Check Supabase **Logs** → **Postgres Logs**
3. Review this deployment guide
4. Verify all secrets are correctly configured
