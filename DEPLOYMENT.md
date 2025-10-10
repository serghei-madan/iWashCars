# iWashCars Deployment Guide - Railway

This guide will help you deploy iWashCars to Railway with automatic deployments from GitHub.

## Prerequisites

- GitHub account
- Railway account (free tier available: https://railway.app)
- Your repository pushed to GitHub

## Step 1: Prepare Your Repository

All necessary files have been created:
- ✅ `Procfile` - Defines web, worker, and release processes
- ✅ `railway.toml` - Railway deployment configuration
- ✅ `nixpacks.toml` - Build configuration (installs deps, runs collectstatic)
- ✅ `runtime.txt` - Python version (3.10.12)
- ✅ `build.sh` - Build script (alternative to nixpacks.toml)
- ✅ `requirements.txt` - Updated with production dependencies
- ✅ `.env.example` - Environment variables template

## Step 2: Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

## Step 3: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your iWashCars repository
5. Railway will automatically detect Django and start building

## Step 4: Add PostgreSQL Database

1. In your Railway project dashboard, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically:
   - Create the database
   - Add `DATABASE_URL` environment variable
   - Connect it to your Django app

## Step 5: Configure Environment Variables

In Railway dashboard, go to your service → "Variables" and add:

### Required Variables:

```bash
SECRET_KEY=generate-a-random-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app.railway.app
SITE_URL=https://your-app.railway.app
```

### Stripe Configuration:

```bash
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_DEPOSIT_AMOUNT=2500
```

### Email Configuration (Mailgun):

```bash
EMAIL_BACKEND=main.mailgun_backend.MailgunEmailBackend
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_SANDBOX_DOMAIN=your-mailgun-domain
MAILGUN_BASE_URL=https://api.mailgun.net
```

### Business Information:

```bash
DRIVER_NOTIFICATION_EMAIL=driver@yourdomain.com
DRIVER_NOTIFICATION_PHONE=+1234567890
```

### Optional (Twilio SMS):

```bash
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Step 6: Generate SECRET_KEY

Generate a secure secret key using Python:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and use it as your `SECRET_KEY` in Railway.

## Step 7: Deploy Worker Service

The Django-Q background worker needs to run as a separate service:

1. In Railway, click "+ New" → "Empty Service"
2. Connect the same GitHub repository
3. In settings, set the "Start Command" to:
   ```bash
   python manage.py qcluster
   ```
4. Add all the same environment variables

## Step 8: Configure Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. URL: `https://your-app.railway.app/stripe/webhook/`
4. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy the webhook secret and add to Railway as `STRIPE_WEBHOOK_SECRET`

## Step 9: Custom Domain (Optional)

1. In Railway dashboard, go to Settings → Domains
2. Click "Add Domain"
3. Follow instructions to configure DNS
4. Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` with your domain

## Auto-Deploy Setup

✅ Railway automatically deploys when you push to GitHub!

Every time you push to your `main` branch:
1. Railway detects the push
2. Runs `build.sh` (installs dependencies, collects static files, runs migrations)
3. Starts web server with `gunicorn`
4. Restarts the worker service

## Monitoring

- **Logs**: Railway dashboard → Your service → "Logs" tab
- **Metrics**: Railway dashboard → Your service → "Metrics" tab
- **Database**: Railway dashboard → PostgreSQL service

## Troubleshooting

### Build Fails

Check the build logs in Railway. Common issues:
- **"pip: command not found"**: This is fixed by using `nixpacks.toml` instead of custom build commands. Railway's Nixpacks automatically detects Python and sets up the environment.
- Missing environment variables
- Python version mismatch
- Dependency conflicts

**Note**: The project uses `nixpacks.toml` which tells Railway exactly how to build:
1. Setup phase: Install Python 3.10 and PostgreSQL
2. Install phase: Run `pip install -r requirements.txt`
3. Build phase: Run `python manage.py collectstatic`
4. Start: Run gunicorn server

### Static Files Not Loading

Make sure:
- `STATIC_ROOT` is set in settings.py ✅
- `collectstatic` runs in `build.sh` ✅
- WhiteNoise is in `MIDDLEWARE` ✅

### Database Connection Error

- Railway should automatically provide `DATABASE_URL`
- Check if PostgreSQL service is running
- Verify `DATABASE_URL` is in environment variables

### Worker Not Processing Tasks

- Make sure worker service is running
- Check worker logs in Railway
- Verify Django-Q configuration in settings.py

## Cost Estimate

Railway pricing (as of 2024):
- **Free Tier**: $5 credit per month
  - Good for testing and small apps

- **Paid**: ~$5-15/month
  - Web service: ~$5/month
  - Worker service: ~$5/month
  - PostgreSQL: $5/month (after free tier)

## Rollback

To rollback to a previous version:
1. Railway dashboard → Deployments
2. Find the previous successful deployment
3. Click "Redeploy"

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Django Docs: https://docs.djangoproject.com

## Next Steps

- [ ] Set up custom domain
- [ ] Configure SSL certificate (automatic with Railway)
- [ ] Set up database backups
- [ ] Monitor application performance
- [ ] Set up error tracking (e.g., Sentry)
