import discord
from discord import app_commands
import json
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from iRacingCommands import race_results, team_stats, special_events_calendar, get_all_session_id

# Only used whilst running locally
envs = load_dotenv(dotenv_path='C:/Users/matth/PycharmProjects/ComealiRacingDiscordBot/.venv/envs.env')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')


def get_discord_secret():

    secret_name = "discordiRacingBotSecrets"
    region_name = "eu-north-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Parse the secret string into a JSON object
    secrets = get_secret_value_response['SecretString']
    secret_dict = json.loads(secrets)

    # Extract the specific key (e.g., Discord_SECRET)
    secret = secret_dict.get("Discord_SECRET")
    return secret

GUILDS = [823227580583772200, 822462437626347540]
discord_secret = get_discord_secret()

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        for guild_id in GUILDS:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.tree.command(name='imsa_gtp_race_results', description='Show the latest IMSA race GTP results for a given session ID')
async def raceresults(interaction: discord.Interaction, session_id: str):
    try:
        # Ask user to input the session ID
        await interaction.response.defer()

        # Check if the session ID is a valid integer or not
        if not session_id.isdigit():
            await interaction.followup.send("Session ID Should be a Number")
            return

        # Call the race_results function with the user input
        df = race_results(session_id)

        if df is None or df.empty:
            await interaction.followup.send("No Race Result Available.")
            return

        # Create an embed
        embed = discord.Embed(
            title="Race Result",
            description="Here are the GTP results the IMSA race session:",
            color=discord.Color.blue()
        )
        # Add fields for each driver
        for index, row in df.iterrows():
            result = row['Result']
            driver_info = (
                f"**Driver**: {row['Driver']}\n"
                f"**Class**: {row['Class']}\n"
                f"**Car**: {row['Car']}\n"
            )
            embed.add_field(name=f"Position: {result}", value=driver_info, inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@client.tree.command(name='sop_team_stats', description='Show the stats of SOP team members')
async def teamstats(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        df = team_stats()
        if df.empty:
            await interaction.followup.send("Error retrieving team stats.")
            return

        # Create an embed
        embed = discord.Embed(
            title="SOP Esports Racing Team Members",
            color=discord.Color.pink()
        )
        # Add fields for each driver
        for index, row in df.iterrows():
            driver = row['Driver']
            # Format the driver info
            driver_info = f"{row['iRating']} iRating, {row['License Class']}, {row['Safety Rating']}"

            # Add the driver information as a field
            embed.add_field(name=driver, value=driver_info, inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


@client.tree.command()
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@client.tree.command(name='special_events_calendar', description='Show the Upcoming iRacing Special Events for 2025')
async def special_events(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        df = special_events_calendar()
        if df.empty:
            await interaction.followup.send("Error retrieving dates.")
            return

        # Create an embed
        embed = discord.Embed(
            title="Upcoming 2025 iRacing Special Events",
            color=discord.Color.red()
        )
        # Add fields for each event
        for index, row in df.iterrows():
            events = row['Event']
            # Format the event info
            event_info = f"{row['Date']}, Cars: {row['Cars']}"

            # Add the event information as a field
            embed.add_field(name=events, value=event_info, inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

client.run(discord_secret)