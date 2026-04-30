# VegaBot Deployment Guide - Railway.app

## What is VegaBot?

A Discord bot that:
- Posts your daily picks with `/todayspick` command
- Handles Stripe subscriptions ($19.99/month for premium tier)
- Auto-assigns premium role when payment completes
- Posts daily picks to #daily-picks channel automatically

## Prerequisites

1. **Discord Server** — "Vega's Picks" ✅
2. **Discord Bot Token** — Already have ✅
3. **Stripe API Keys** — Already have ✅
4. **Railway Account** — Free at railway.app (sign up with GitHub)

---

## Step 1: Create GitHub Repository for VegaBot

1. Go to **github.com**
2. Click **"New repository"**
3. Name it **`vegabot`**
4. Make it **Public**
5. Click **"Create repository"**

## Step 2: Push VegaBot Code to GitHub

In Terminal on your Mac:

```bash
cd ~/truelines/vegabot-railway
git init
git add .
git commit -m "Initial VegaBot commit"
git branch -M main
git remote add origin https://github.com/alphabetabot/vegabot.git
git push -u origin main
```

(Replace `alphabetabot` with your GitHub username)

---

## Step 3: Deploy to Railway

1. Go to **railway.app**
2. Sign in with GitHub
3. Click **"New Project"** (top right)
4. Select **"Deploy from GitHub Repo"**
5. Choose your **vegabot** repo
6. Click **"Create"**

Railway will automatically build and deploy. Wait for the build to complete (~2 minutes).

---

## Step 4: Add Environment Variables to Railway

Once deployed:

1. Go to your Railway project dashboard
2. Click the **vegabot** service
3. Click **"Variables"** tab
4. Add these variables:

| Variable | Value |
|----------|-------|
| `DISCORD_TOKEN` | *(from Discord Developer Portal)* |
| `STRIPE_SECRET_KEY` | *(from Stripe Dashboard)* |
| `STRIPE_WEBHOOK_SECRET` | *(from Stripe Dashboard)* |
| `STRIPE_PRICE_ID` | `price_1TRjAFFCKgaALK0xnt5WLpYI` |
| `DAILY_PICK_CHANNEL_ID` | (leave blank for now, optional) |

5. Click **"Save"** after each variable

---

## Step 5: Verify Bot is Online

1. Go to your Discord server "Vega's Picks"
2. In any channel, type `/todayspick` and press Enter
3. Bot should respond with today's pick ✅

---

## Step 6: Test Subscription Command

1. Type `/subscribe` in Discord
2. Click **"Subscribe Now"** button
3. Stripe checkout should open
4. After payment, your role should auto-update to **"Vega's Premium Picks"** ✅

---

## Step 7: (Optional) Enable Daily Auto-Posts

If you want the bot to post daily picks to #daily-picks automatically:

1. In Discord, right-click #daily-picks channel
2. Copy the Channel ID
3. Go back to Railway project
4. Add variable: `DAILY_PICK_CHANNEL_ID` = (your channel ID)
5. Bot will post picks daily at 7am PT

---

## Troubleshooting

**Bot won't come online:**
- Check Railway build logs (click service → view logs)
- Verify DISCORD_TOKEN is correct
- Restart the service in Railway

**Subscription not creating:**
- Verify Stripe keys are correct
- Check Stripe dashboard for errors
- Make sure STRIPE_PRICE_ID matches your product

**Commands not showing in Discord:**
- Sometimes takes 1-2 minutes to sync
- Try restarting Discord app

---

## Next Steps

Once bot is live:
1. Test all commands
2. Invite friends to Discord to test subscriptions
3. Monitor Stripe dashboard for payments
4. Track subscriber count in #premium-only channel

---

**Done?** Your bot is now running 24/7 on Railway. No more manual setup needed.
