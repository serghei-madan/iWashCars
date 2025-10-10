# iWashCars Docker Deployment Guide

This guide covers Docker-based deployment for both local development and Railway production deployment.

## Why Docker?

✅ **Test builds locally** before deploying
✅ **Predictable** - works the same everywhere
✅ **No provider detection issues** (like Nixpacks)
✅ **Industry standard** - works on any platform
✅ **Full control** over the build process

## Prerequisites

- Docker installed (https://docs.docker.com/get-docker/)
- Docker Compose installed (included with Docker Desktop)
- Railway account (https://railway.app)
- GitHub repository connected to Railway

## Local Development with Docker

### Quick Start

1. **Start all services** (web, database, redis, worker):
```bash
docker-compose up
```

2. **Access the application**:
   - Web: http://localhost:8000
   - Database: localhost:5432
   - Redis: localhost:6379

3. **Stop all services**:
```bash
docker-compose down
```

### Detailed Commands

**Build the Docker image**:
```bash
docker build -t iwashcars .
```

**Run migrations**:
```bash
docker-compose run web python manage.py migrate
```

**Create superuser**:
```bash
docker-compose run web python manage.py createsuperuser
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f db
```

**Run Django management commands**:
```bash
docker-compose run web python manage.py <command>
```

**Rebuild after code changes**:
```bash
docker-compose up --build
```

**Clean up everything** (including volumes):
```bash
docker-compose down -v
```

## Docker Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build:

1. **Builder stage**: Installs all build dependencies
2. **Runtime stage**: Only copies what's needed for production (smaller image)

### Services in docker-compose.yml

- **web**: Django application (port 8000)
- **db**: PostgreSQL 15 database (port 5432)
- **redis**: Redis for caching and Django-Q (port 6379)
- **worker**: Django-Q background task processor

### Security Features

- Runs as non-root user (appuser)
- Minimal runtime dependencies
- Health checks for all services
- Environment-based configuration

## Railway Deployment

### Step 1: Push to GitHub

Make sure all Docker files are committed:

```bash
git add Dockerfile docker-compose.yml railway.toml .dockerignore
git commit -m "Add Docker deployment configuration"
git push origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your iWashCars repository
5. Railway will automatically detect the Dockerfile and build

### Step 3: Add PostgreSQL Database

1. In Railway dashboard, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway automatically adds `DATABASE_URL` to your environment

### Step 4: Configure Environment Variables

In Railway dashboard → Variables, add:

```bash
# Django Core
SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app.railway.app
SITE_URL=https://your-app.railway.app

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_DEPOSIT_AMOUNT=2500

# Mailgun
EMAIL_BACKEND=main.mailgun_backend.MailgunEmailBackend
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_API_KEY=your-api-key
MAILGUN_SANDBOX_DOMAIN=your-domain
MAILGUN_BASE_URL=https://api.mailgun.net

# Business
DRIVER_NOTIFICATION_EMAIL=driver@yourdomain.com
DRIVER_NOTIFICATION_PHONE=+1234567890

# Twilio (Optional)
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
```

**Generate SECRET_KEY**:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Step 5: Deploy Worker Service

Django-Q needs a separate worker process:

1. In Railway, click "+ New" → "Empty Service"
2. Connect the same GitHub repository
3. Set "Start Command": `python manage.py qcluster`
4. Add the same environment variables

### Step 6: Configure Stripe Webhook

1. Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-app.railway.app/stripe/webhook/`
3. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
4. Copy webhook secret → Add to Railway as `STRIPE_WEBHOOK_SECRET`

## Railway Auto-Deploy

✅ **Automatic deployments enabled!**

Every push to `main` branch:
1. Railway detects the push
2. Builds Docker image from Dockerfile
3. Runs health checks
4. Deploys new version
5. Restarts worker service

## Testing the Docker Build Locally

Before pushing to Railway, test locally:

```bash
# 1. Build the image
docker build -t iwashcars .

# 2. Check image size (should be ~200-300MB)
docker images iwashcars

# 3. Test the build
docker-compose up

# 4. Verify in browser
# Open http://localhost:8000

# 5. Check logs for errors
docker-compose logs
```

## Troubleshooting

### Build fails locally

**Check Docker logs**:
```bash
docker-compose logs web
```

**Rebuild from scratch**:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database connection errors

**Check database is running**:
```bash
docker-compose ps
```

**View database logs**:
```bash
docker-compose logs db
```

**Reset database**:
```bash
docker-compose down -v  # Warning: deletes all data
docker-compose up
```

### Static files not loading

**Collect static files manually**:
```bash
docker-compose run web python manage.py collectstatic --noinput
```

### Railway build fails

**Check Railway logs**:
- Go to Railway dashboard → Your service → "Logs" tab
- Look for build errors

**Common issues**:
- Missing environment variables → Add them in Railway
- Out of memory → Reduce workers in Dockerfile CMD
- Database not ready → Check DATABASE_URL is set

### Worker not processing tasks

**Check worker logs**:
```bash
# Local
docker-compose logs worker

# Railway
Check worker service logs in dashboard
```

**Verify Django-Q configuration**:
```bash
docker-compose run web python manage.py shell
>>> from django_q.models import Task
>>> Task.objects.all()
```

## Monitoring

### Local Monitoring

**Container stats**:
```bash
docker stats
```

**Service health**:
```bash
docker-compose ps
```

### Railway Monitoring

- **Logs**: Railway dashboard → Service → "Logs"
- **Metrics**: Railway dashboard → Service → "Metrics"
- **Database**: Railway dashboard → PostgreSQL → "Metrics"

## Advantages Over Nixpacks

| Feature | Nixpacks | Docker |
|---------|----------|--------|
| Local testing | ❌ No | ✅ Yes |
| Build reliability | ⚠️ Auto-detection issues | ✅ Predictable |
| Debugging | ❌ Limited | ✅ Full access |
| Provider lock-in | ⚠️ Railway/Render only | ✅ Works anywhere |
| Build control | ❌ Limited | ✅ Complete |
| Multi-language projects | ⚠️ Can conflict | ✅ No issues |

## Docker Image Optimization

Current Dockerfile includes:

- ✅ Multi-stage build (smaller image)
- ✅ Minimal base image (python:3.10-slim)
- ✅ Non-root user for security
- ✅ Health checks
- ✅ Layer caching optimization
- ✅ No cache pip installs
- ✅ Static files collected during build

**Expected image size**: ~200-300MB

## Environment Variables Reference

### Required for Production

- `SECRET_KEY` - Django secret key (generate new for production)
- `DEBUG` - Should be `False` in production
- `DATABASE_URL` - Provided automatically by Railway PostgreSQL
- `ALLOWED_HOSTS` - Your Railway domain
- `CSRF_TRUSTED_ORIGINS` - Your Railway domain with https://

### Payment Processing

- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_DEPOSIT_AMOUNT` (default: 2500 = $25)

### Email (Mailgun)

- `MAILGUN_API_KEY`
- `MAILGUN_SANDBOX_DOMAIN`
- `DEFAULT_FROM_EMAIL`

### Business

- `DRIVER_NOTIFICATION_EMAIL`
- `DRIVER_NOTIFICATION_PHONE`

### Optional (SMS)

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

## Production Checklist

Before deploying to production:

- [ ] Test Docker build locally: `docker build -t iwashcars .`
- [ ] Test with docker-compose: `docker-compose up`
- [ ] Verify all services start correctly
- [ ] Test database migrations
- [ ] Test static files loading
- [ ] Generate new SECRET_KEY for production
- [ ] Set DEBUG=False
- [ ] Configure all environment variables in Railway
- [ ] Add PostgreSQL database in Railway
- [ ] Set up worker service in Railway
- [ ] Configure Stripe webhook
- [ ] Test payment flow in production
- [ ] Set up custom domain (optional)
- [ ] Configure SSL (automatic with Railway)

## Rollback

If a deployment fails:

1. Railway dashboard → "Deployments"
2. Find the previous working deployment
3. Click "Redeploy"

## Support Resources

- **Docker Docs**: https://docs.docker.com
- **Railway Docs**: https://docs.railway.app
- **Django Deployment**: https://docs.djangoproject.com/en/5.2/howto/deployment/
- **Railway Discord**: https://discord.gg/railway

## Next Steps

- [ ] Test locally with `docker-compose up`
- [ ] Push to GitHub
- [ ] Monitor Railway build
- [ ] Configure environment variables
- [ ] Set up worker service
- [ ] Test in production
- [ ] Set up custom domain
- [ ] Configure monitoring/alerts
