import discord
from discord import app_commands
import json
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from iRacingCommands import race_results, team_stats


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

MY_GUILD = discord.Object(id=823227580583772200)
discord_secret = get_discord_secret()

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.tree.command(name='gtp_race_results', description='Show the latest IMSA race GTP results')
async def raceresults(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        df = race_results()
        if df.empty:
            await interaction.followup.send("No race results available.")
            return
        # Create an embed
        embed = discord.Embed(
            title="Race Results",
            description="Here are the latest race results:",
            color=discord.Color.blue()
        )
        # Add fields for each driver
        for index, row in df.iterrows():
            result = int(row['Result']) + 1
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
            title="SOP Team Members",
            color=discord.Color.pink()
        )
        # Add fields for each driver
        for index, row in df.iterrows():
            driver = row['Driver']
            # Format the driver info as requested
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


client.run(discord_secret)