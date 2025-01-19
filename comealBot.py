import discord
from discord import app_commands
import json
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from iRacingCommands import race_results, team_stats, special_events_calendar, irating_percentile

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

    # Parse the secret string into a JSON for extraction
    secrets = get_secret_value_response['SecretString']
    secret_dict = json.loads(secrets)

    # Extract the specific key from AWS (e.g., Discord_SECRET)
    secret = secret_dict.get("Discord_SECRET")
    return secret

GUILDS = [823227580583772200, 822462437626347540]
discord_secret = get_discord_secret()

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to the guilds
        for guild_id in GUILDS:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


# Discord command that displays the IMSA GTP results for a given session ID
@client.tree.command(name='imsa_gtp_race_results', description='Show the latest IMSA race GTP results for a given session ID.')
async def raceresults(interaction: discord.Interaction, session_id: str):
    try:
        # Ask user to input the session ID
        await interaction.response.defer()

        # Check if the session ID is a valid integer or not
        if not session_id.isdigit():
            await interaction.followup.send("Session ID Should be a Number")
            return

        # Call the race_results function with the user input
        race_results_df = race_results(session_id)

        if race_results_df is None or race_results_df.empty:
            await interaction.followup.send("No Race Result Available.")
            return

        # Create an embed
        embed = discord.Embed(
            title="Race Result",
            description="Here are the GTP results the IMSA race session:",
            color=discord.Color.blue()
        )
        # Add fields for each driver
        for index, row in race_results_df.iterrows():
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


# Discord command that displays the team irating and safety rating for the SOP team
@client.tree.command(name='sop_team_stats', description='Show the stats of SOP team members.')
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


# Discord command that returns "Hello" to the user
@client.tree.command()
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


# Discord command that displays the special events calendar
@client.tree.command(name='special_events_calendar', description='Show the Upcoming iRacing Special Events for 2025.')
async def special_events(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        calendar_df = special_events_calendar()
        if calendar_df.empty:
            await interaction.followup.send("Error retrieving dates.")
            return

        # Create an embed
        embed = discord.Embed(
            title="Upcoming 2025 iRacing Special Events.",
            color=discord.Color.red()
        )
        # Add fields for each event
        for index, row in calendar_df.iterrows():
            events = row['Event']
            # Format the event info
            event_info = f"{row['Date']}, Cars: {row['Cars']}"

            # Add the event information as a field
            embed.add_field(name=events, value=event_info, inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


# Discord command that displays the irating percentile of the given driver
@client.tree.command(name='irating_driver_percentile', description='Show the iRating Percentile for a Given Driver.')
async def iratingpercentile(interaction: discord.Interaction, driver_name: str):
    try:
        # Ask user to input the driver name
        await interaction.response.defer()

        # Call the race_results function with the user input
        drivers_df = irating_percentile(driver_name)
        if drivers_df is None or drivers_df.empty:
            await interaction.followup.send("Driver Name Not Found or Incorrect")
            return
        driver = drivers_df.iloc[0]['driver']
        percentile = drivers_df.iloc[0]['percentile']
        rank = drivers_df.iloc[0]['rank']

        # Create an embed
        embed = discord.Embed(
            title="iRating Percentile",
            description="The percentile is calculated from the sportscar irating of drivers who have completed at least one sportscar race.",
            color=discord.Color.green()
        )

        embed.add_field(
            name=driver,
            value=(
                f" This driver is in the top {percentile:.2f}% of all sportscar drivers. They are ranked {rank}."
            )
        )

        # Send the embed
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")


client.run(discord_secret)