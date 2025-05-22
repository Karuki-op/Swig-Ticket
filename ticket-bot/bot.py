 import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

with open("config.json") as f:
    config = json.load(f)

def is_admin():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == config["admin_role_id"] for role in interaction.user.roles)
    return app_commands.check(predicate)

def is_staff():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == config["staff_role_id"] for role in interaction.user.roles)
    return app_commands.check(predicate)

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🎟️ Open Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        category = interaction.guild.get_channel(config["ticket_categories"]["support"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.get_role(config["staff_role_id"]): discord.PermissionOverwrite(view_channel=True)
        }

        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message(f"You already have an open ticket: {existing.mention}", ephemeral=True)
            return

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            overwrites=overwrites,
            category=category
        )

        await interaction.response.send_message(f"🎟️ Ticket created: {channel.mention}", ephemeral=True)
        await channel.send(f"{interaction.user.mention}, thanks for reaching out. A staff member will be with you shortly.")

@bot.event
async def on_ready():
    await tree.sync()
    bot.add_view(TicketView())
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="ticket_setup", description="Setup ticket categories")
@is_admin()
async def ticket_setup(interaction: discord.Interaction):
    guild = interaction.guild
    created = []
    for name in ["Package Purchase", "General Support", "Closed Tickets"]:
        if not any(cat.name == name for cat in guild.categories):
            await guild.create_category(name)
            created.append(name)
    await interaction.response.send_message(f"Setup complete. Created: {', '.join(created) if created else 'none'}", ephemeral=True)

@tree.command(name="ticket_claim", description="Claim the ticket")
@is_staff()
async def ticket_claim(interaction: discord.Interaction):
    await interaction.response.send_message(f"{interaction.user.mention} has claimed this ticket.", ephemeral=False)

@tree.command(name="ticket_close", description="Close the ticket")
@is_staff()
async def ticket_close(interaction: discord.Interaction):
    closed_category = interaction.guild.get_channel(config["ticket_categories"]["closed"])
    if closed_category:
        await interaction.channel.edit(category=closed_category)
        await interaction.response.send_message("✅ Ticket closed.", ephemeral=False)

@tree.command(name="ticket_reopen", description="Reopen the ticket")
@is_staff()
async def ticket_reopen(interaction: discord.Interaction):
    support_category = interaction.guild.get_channel(config["ticket_categories"]["support"])
    if support_category:
        await interaction.channel.edit(category=support_category)
        await interaction.response.send_message("🔓 Ticket reopened.", ephemeral=False)

@tree.command(name="ticket_panel", description="Send the ticket panel")
@is_admin()
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Swig Management Support Center",
        description=(
            "👋 Welcome to the MCL Support Center!\n\n"
            "Need help with something? We've got you covered.\n"
            "Select a button according to your need. Our you will get connected with our team."
        ),
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket panel sent!", ephemeral=True)

bot.run(os.getenv("TOKEN"))
