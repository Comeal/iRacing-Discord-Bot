from iracingdataapi.client import irDataClient
import json
from datetime import datetime, timedelta
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import pandas as pd
import re


envs = load_dotenv(dotenv_path='C:/Users/matth/PycharmProjects/ComealiRacingDiscordBot/.venv/envs.env')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')


def get_iracing_secret():

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
    secret = secret_dict.get("iRacing_SECRET")

    return secret


def get_iracing_user():

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
    user = secret_dict.get("iRacing_USER")

    return user


iracing_pass = get_iracing_secret()
iracing_user = get_iracing_user()


idc = irDataClient(username=iracing_user, password=iracing_pass)


# Calculate time from last tuesday, for current weeks races
def get_previous_tuesday():
    today = datetime.now()
    # Weekday is an integer where Monday is 0 and Sunday is 6.
    weekday = today.weekday()
    # Calculate days since the last Tuesday.
    days_since_tuesday = (weekday - 1) % 7
    # Subtract those days to get to the previous Tuesday.
    last_tuesday = today - timedelta(days=days_since_tuesday)
    # Set time to the start of the day, if needed.
    last_tuesday_start = last_tuesday.replace(hour=0, minute=0, second=0, microsecond=0)
    return last_tuesday_start.strftime("%Y-%m-%dT%H:%MZ")


# Generate df that lists this week's IMSA race sessions
def this_week_imsa_races():
    latest_week = get_previous_tuesday()
    try:
        # Get all recent events from a set time
        stats = idc.result_search_series(event_types=[1], start_range_begin=latest_week)

        # Flatten all nested dictionaries
        imsa_race_ids = pd.json_normalize(stats, sep="_")
        imsa_races = []

        # Extract IMSA only race session information
        for _, race in imsa_race_ids.iterrows():
            if re.search("IMSA", race["series_name"]) and race["event_type_name"] == "Race":
                imsa_races.append(race)
            else:
                continue

        # Convert to a dataframe and drop columns
        imsa_race_ids = pd.DataFrame(imsa_races)
        imsa_race_ids.drop(columns=["session_id", "end_time", "license_category_id", "license_category", "num_drivers", "num_cautions",
                         "num_caution_laps", "num_lead_changes", "event_laps_complete", "driver_changes", "winner_group_id",
                         "winner_ai", "official_session", "season_id", "season_year", "season_quarter", "event_type",
                         "series_id", "series_short_name", "race_week_num", "event_strength_of_field", "event_average_lap",
                         "event_best_lap_time", "track_config_name", "track_track_id"], inplace=True)

        # Rename columns
        imsa_race_ids.rename(
            columns={"subsession_id": "ID", "winner_name": "Winner", "event_type_name": "Event", "series_name": "Series",
                     "track_track_name": "Track", "start_time": "Time"}, inplace=True)

        return imsa_race_ids
    except:
        print("No IMSA Races This Week")

# Create function to grab all session IDs from this week's IMSA races function
def get_all_session_id():
    weekly_races = this_week_imsa_races()
    session_ids = weekly_races["ID"].tolist()

    return session_ids

# Create function to take a user input session ID (that must be valid from the IMSA list) and output the race results
def race_results(session_id: str):
    try:
        session_id = session_id
        # Check if the session ID is valid from the get_all_session_id function
        if session_id in get_all_session_id():
            session = session_id
            return session
        else:
            print("Session ID not a Valid IMSA Session")

        # Convert the session to an integer and raise and error if it is not
        try:
            session = int(session_id)
        except TypeError as e:
            print(f"Session ID Must be a Number: {str(e)}")
            return None

        race_result = idc.result(subsession_id=session, include_licenses=False)

        # Find results dict nested within sub dictionaries and append to a new list
        imsa_race_results = []
        imsa_sessions = []

        if "session_results" in race_result:
            session_result = race_result["session_results"]
            for sessions in session_result:
                imsa_sessions.append(sessions)
                if sessions.get("simsession_name") == 'RACE' and "results" in sessions:
                    results = sessions["results"]
                    for result in results:
                        imsa_race_results.append(result)

        results = pd.json_normalize(imsa_race_results, sep="_")
        results.drop(columns=['cust_id', 'aggregate_champ_points', 'ai', 'average_lap', 'best_lap_num', 'best_lap_time',
                     'best_nlaps_num', 'best_nlaps_time', 'best_qual_lap_at', 'best_qual_lap_num', 'best_qual_lap_time',
                     'car_class_id', 'car_class_short_name', 'car_id', 'champ_points', 'class_interval', 'club_id',
                     'club_name', 'club_points', 'club_shortname', 'country_code', 'division', 'division_name',
                     'drop_race', 'finish_position_in_class', 'friend', 'incidents', 'interval', 'laps_complete',
                     'laps_lead', 'league_agg_points', 'league_points', 'license_change_oval', 'license_change_road',
                     'max_pct_fuel_fill', 'multiplier', 'new_cpi', 'new_license_level', 'new_sub_level', 'new_ttrating',
                     'newi_rating', 'old_cpi', 'old_license_level', 'old_sub_level', 'old_ttrating', 'oldi_rating',
                     'opt_laps_complete', 'position', 'qual_lap_time', 'reason_out', 'reason_out_id',
                     'starting_position', 'starting_position_in_class', 'watched', 'weight_penalty_kg',
                     'helmet_pattern', 'helmet_color1', 'helmet_color2', 'helmet_color3', 'helmet_face_type',
                     'helmet_helmet_type', 'livery_car_id', 'livery_pattern', 'livery_color1', 'livery_color2',
                     'livery_color3', 'livery_number_font', 'livery_number_color1', 'livery_number_color2',
                     'livery_number_color3', 'livery_number_slant', 'livery_sponsor1', 'livery_sponsor2',
                     'livery_car_number', 'livery_wheel_color', 'livery_rim_type', 'suit_pattern', 'suit_color1',
                     'suit_color2', 'suit_color3'], inplace=True)

        # Filter out non GTP cars
        results_df = results.loc[results['car_class_name'] == 'GTP']

        # Rename columns
        results_df.rename(columns={"display_name": "Driver", "car_class_name": "Class", "car_name": "Car",
                       "finish_position": "Result"}, inplace=True)

        # Add +1 onto race result position for correct position
        results_df['Result'] = results_df['Result'].astype(int) +1

        return results_df

    except:
        print("Invalid Session ID")
        return None


def team_stats():
    sop_team_id = 272234
    sop_roster = []
    sop_licenses = []
    sop_team_stats = idc.team(team_id=sop_team_id, include_licenses=True)
    if "roster" in sop_team_stats:
        sop_members = sop_team_stats["roster"]
        for member in sop_members:
            sop_roster.append(member)
            if "licenses" in member:
                for license_entry in member["licenses"]:
                    if license_entry.get("category") == "sports_car":
                        sop_licenses.append(license_entry)

    # Normalize the roster data
    df = pd.json_normalize(sop_roster, sep="_")

    # Normalize and filter licenses for Sports Car
    licenses_df = pd.json_normalize(sop_licenses, sep="_")

    # Add an identifier to maintain alignment with the original roster
    licenses_df = licenses_df.reset_index().rename(columns={"index": "license_index"})
    df = df.reset_index().rename(columns={"index": "roster_index"})

    # Merge the filtered license information back to the main roster dataframe
    team_roster = pd.merge(df, licenses_df, left_on="roster_index", right_index=True, how="inner")

    # Tidy up the final DataFrame
    team_roster = team_roster.loc[team_roster["category"] == "sports_car"]
    team_roster.drop(columns=["cust_id", "owner", "helmet_face_type", "helmet_helmet_type", "helmet_color3",
                                  "helmet_color2", "helmet_color1", "helmet_pattern", "mpr_num_tts", "seq",
                                  "pro_promotable", "tt_rating", "mpr_num_races", "color", "roster_index", "group_id",
                                  "category_id", "category", "category_name", "cpi", "license_level", "license_index", "licenses",
                                  "admin"],
                         inplace=True)
    team_roster.rename(columns={"display_name": "Driver", "safety_rating": "Safety Rating",
                                    "irating": "iRating", "group_name": "License Class"}, inplace=True)

    team_roster = team_roster.sort_values(by='iRating', ascending=False)

    return team_roster


def special_events_calendar():
    # Manually entered information for all iRacing special events in 2025
    events_calendar = [
        {"event": "Roar Before the 24", "date": "January 10-11", "cars": "LMP3"", " "GT4"", " "Touring Cars", "end_date": 20250112},
        {"event": "Daytona 24", "date": "January 17-19", "cars": "GTP/HY"", " "LMP2"", " "GT3", "end_date": 20250120},
        {"event": "Daytona 500", "date": "February 12-17", "cars": "NASCAR Cup Series", "end_date": 20250218},
        {"event": "Bathurst 12 Hour", "date": "February 21-23", "cars": "GT3", "end_date": 20250224},
        {"event": "Sebring 12 Hour", "date": "March 21-23", "cars": "GTP/HY"", " "LMP2"", " "GT3", "end_date": 20250324},
        {"event": "Fixed Setup Indy 500", "date": "May 6-12", "cars": "Dallara IR-18", "end_date": 20250513},
        {"event": "Open Setup Indy 500", "date": "May 13-19", "cars": "Dallara IR-18", "end_date": 20250520},
        {"event": "Coke 600", "date": "May 21-26", "cars": "NASCAR Cup Series", "end_date": 20250527},
        {"event": "Nürburgring 24 Hour", "date": "June 6-8", "cars": "GT3"", " "Porsche Cup"", " "GT4"", " "TCR"", " "BMW M2", "end_date": 20250609},
        {"event": "Watkins Glen 6 Hour", "date": "June 27-28", "cars": "GTP/HY"", " "LMP2"", " "GT3", "end_date": 20250629},
        {"event": "Spa 24 Hours", "date": "July 11-13", "cars": "GT3", "end_date": 20250714},
        {"event": "Brickyard 400", "date": "July 23-28", "cars": "NASCAR Cup Series", "end_date": 20250729},
        {"event": "Indy 6 Hour", "date": "September 5-6", "cars": "GTP/HY"", " "LMP2"", " "GT3", "end_date": 20250907},
        {"event": "Bristol Night Race", "date": "September 10-15", "cars": "NASCAR Cup Series", "end_date": 20250916},
        {"event": "Bathurst 1000", "date": "September 26-27", "cars": "Supercars", "end_date": 20250928},
        {"event": "Petit Le Mans", "date": "October 3-5", "cars": "GTP/HY"", " "LMP2"", " "GT3", "end_date": 20251006},
        {"event": "Suzuka 1000km", "date": "November 14-16", "cars": "GT3", "end_date": 20251117}]

    calendar = pd.json_normalize(events_calendar, sep="_")
    # Convert the end_date column to datetime format
    calendar['end_date'] = pd.to_datetime(calendar['end_date'], format='%Y%m%d')
    # Rename columns
    calendar.rename(columns={"event": "Event", "date": "Date", "cars": "Cars"}, inplace=True)

    # Get today's date to compare against the end date
    today = datetime.now()
    # Filter out rows where the end date is after today
    calendar = calendar[calendar["end_date"] > today]

    return calendar

