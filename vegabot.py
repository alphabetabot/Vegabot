import discord
from discord import app_commands
from discord.ext import tasks
import os
import stripe
import sqlite3
import aiohttp
from datetime import datetime
import json
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

# Configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_1TRjAFFCKgaALK0xnt5WLpYI")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PREMIUM_ROLE_NAME = "Vega's Premium Picks"
DAILY_PICK_CHANNEL = int(os.getenv("DAILY_PICK_CHANNEL_ID", 0)) if os.getenv("DAILY_PICK_CHANNEL_ID") else 0

# Database setup
def init_db():
    conn = sqlite3.connect('subscriptions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (discord_id INTEGER PRIMARY KEY, 
                  stripe_customer_id TEXT, 
                  stripe_subscription_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('subscriptions.db')
    conn.row_factory = sqlite3.Row
    return conn

# Stripe functions
async def get_todays_pick():
    """Fetch today's pick from TrueOddsIQ API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.trueoddsiq.com/api/todays-pick", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pick = data.get('pick', 'N/A')
                    sport = data.get('sport', 'Unknown')
                    bet = data.get('bet', 'N/A')
                    edge = data.get('edge', 'No edge available')
                    confidence = data.get('confidence', '⭐⭐⭐')
                    
                    embed = discord.Embed(
                        title=f"🏆 VEGA'S TOP PICK TODAY",
                        description=f"**{sport}**: {pick}",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="📊 Bet", value=bet, inline=False)
                    embed.add_field(name="⭐ Confidence", value=confidence, inline=True)
                    embed.add_field(name="💡 Edge", value=edge, inline=False)
                    embed.set_footer(text="Data powered by Vega AI | trueoddsiq.com")
                    return embed
                else:
                    return discord.Embed(title="Error", description="Could not fetch today's pick", color=discord.Color.red())
    except Exception as e:
        return discord.Embed(title="Error", description=f"Failed to fetch pick: {str(e)}", color=discord.Color.red())

# Discord Commands
@tree.command(name="todayspick", description="Get Vega's top pick for today")
async def todayspick(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = await get_todays_pick()
    await interaction.followup.send(embed=embed)

@tree.command(name="subscribe", description="Subscribe to Vega's Premium Picks - $19.99/month")
async def subscribe(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        # Create or get customer
        db = get_db()
        c = db.cursor()
        c.execute("SELECT stripe_customer_id FROM users WHERE discord_id = ?", (interaction.user.id,))
        row = c.fetchone()
        
        if row and row['stripe_customer_id']:
            customer_id = row['stripe_customer_id']
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=f"{interaction.user.id}@discord.local",
                metadata={"discord_id": str(interaction.user.id), "username": interaction.user.name}
            )
            customer_id = customer.id
            c.execute("INSERT OR REPLACE INTO users (discord_id, stripe_customer_id) VALUES (?, ?)",
                     (interaction.user.id, customer_id))
            db.commit()
        
        db.close()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1
            }],
            mode="subscription",
            success_url="https://discord.com",
            cancel_url="https://discord.com",
            metadata={"discord_id": str(interaction.user.id)}
        )
        
        embed = discord.Embed(
            title="✅ Subscribe to Vega's Premium Picks",
            description=f"Click the button below to complete your subscription\n\n**Price:** $19.99/month\n**Benefits:**\n• Exclusive premium picks\n• Access to #premium-only channel\n• Priority support",
            color=discord.Color.green()
        )
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Subscribe Now", url=session.url, style=discord.ButtonStyle.green))
        
        await interaction.followup.send(embed=embed, view=view)
        
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=f"Failed to create subscription: {str(e)}", color=discord.Color.red())
        await interaction.followup.send(embed=embed)

@tree.command(name="status", description="Check your subscription status")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        db = get_db()
        c = db.cursor()
        c.execute("SELECT stripe_subscription_id FROM users WHERE discord_id = ?", (interaction.user.id,))
        row = c.fetchone()
        db.close()
        
        if row and row['stripe_subscription_id']:
            sub = stripe.Subscription.retrieve(row['stripe_subscription_id'])
            status_text = sub.status.upper()
            next_billing = datetime.fromtimestamp(sub.current_period_end).strftime("%B %d, %Y")
            
            embed = discord.Embed(
                title="✅ Subscription Active",
                description=f"**Status:** {status_text}\n**Next Billing:** {next_billing}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ No Active Subscription",
                description="You don't have an active subscription. Use `/subscribe` to get started!",
                color=discord.Color.red()
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(title="❌ Error", description=f"Failed to check status: {str(e)}", color=discord.Color.red())
        await interaction.followup.send(embed=embed)

# Daily pick posting task
@tasks.loop(hours=24)
async def post_daily_pick():
    """Post today's pick to #daily-picks channel at 7am PT"""
    if DAILY_PICK_CHANNEL:
        try:
            channel = client.get_channel(DAILY_PICK_CHANNEL)
            if channel:
                embed = await get_todays_pick()
                await channel.send(embed=embed)
                print(f"✅ Posted daily pick to channel {DAILY_PICK_CHANNEL}")
        except Exception as e:
            print(f"❌ Failed to post daily pick: {e}")

@post_daily_pick.before_loop
async def before_daily_pick():
    await client.wait_until_ready()

# Discord events
@client.event
async def on_ready():
    print(f"✅ Vegabot online as {client.user}")
    await tree.sync()
    print("✅ Commands synced")
    
    # Start daily pick task if channel is set
    if DAILY_PICK_CHANNEL and not post_daily_pick.is_running():
        post_daily_pick.start()

# Run bot
def run_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN not set in environment variables")
    
    init_db()
    client.run(token)

if __name__ == "__main__":
    run_bot()
