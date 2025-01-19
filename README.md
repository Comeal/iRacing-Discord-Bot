# README

# Comeal's Discord Bot for Useful iRacing Commands
## Uses jasondilworth5 wrapper for the iRacing API: [jasondilworth5](https://github.com/jasondilworth56/iracingdataapi/blob/main/src/iracingdataapi/client.py)

### Contains the following useful functions for use within the discord bot:

### get_previous_tuesday():
Function to get the time from last tuesday, used for current weeks races

### this_week_imsa_races()::
Function that lists weeks IMSA race sessions
def 

### get_all_session_id():
Function to grab all session IDs from this week's IMSA races function

### race_results():
Function to take a user input session ID (that must be valid from the IMSA list) and output the race results

### team_stats():
Function to get the irating and safety rating for the given team

### special_events_calendar():
Function to hold a list of special events

### irating_percentile():
Function that gets all the sportscar drivers irating and calculates their percentile
