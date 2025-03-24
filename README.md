# README

# Comeal's Discord Bot for Useful iRacing Commands
## Uses jasondilworth5 wrapper for the iRacing API: [[jasondilworth5](https://github.com/jasondilworth56/iracingdataapi/blob/main/src/iracingdataapi/client.py)](https://github.com/jasondilworth56/iracingdataapi/tree/main)

### Contains the following useful functions for use within the discord bot:

### get_previous_tuesday():
Function to get the time from last tuesday, used to find current weeks races

### this_week_imsa_races():
Function that lists this weeks IMSA race sessions (from get_previous_tuesday function)

### get_all_session_id():
Function to grab all session IDs from this_week_IMSA_races function

### race_results():
Function to take a user input session ID (that must be a valid IMSA session) and output the GTP race results

### team_stats():
Function to get the irating and safety rating for the given team ID

### special_events_calendar():
Function to display the upcoming special events for this year

### irating_percentile():
Function that gets all the sportscar drivers irating and calculates their percentile of those who have completed at least one race
