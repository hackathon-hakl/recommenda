import pyairtable
import os
import json
from datetime import datetime, timedelta, date

with open('api_keys.json') as f:
   api_keys = json.load(f)
    
api_key = api_keys["AIRTABLE_API_KEY"].replace(" ", "")
base_id = api_keys["AIRTABLE_BASE_ID"]

api = pyairtable.Api(api_key)

def list_sport_records(api, base_id, sport_id = None):
   """ 
      sport_id example: 'recGfphnFce1DEBhE'
   """
   if sport_id is not None:
      records = api.table(base_id, 'Sport').get(sport_id)
   else:
      records = api.table(base_id, 'Sport').all(view='Grid view')
   return records

def list_teams_records(api, base_id, team_id=None):
   """ 
      team_id example : 'recbBO2dEP83DqOuF'
   """
   if team_id is not None:
      records = api.table(base_id, 'Momčadi').get(team_id)
   else:
      records = api.table(base_id, 'Momčadi').all(view='Grid view')
   return records

def list_category_records(api, base_id, category_id=None):
   """ 
      category_id example : 'reczS4xKNcQ9TFauy'
"""
   if category_id is not None:
      records = api.table(base_id, 'Kategorija').get(category_id)
   else:
      records = api.table(base_id, 'Kategorija').all(view='Grid view')
   return records

def list_events_records(api, base_id, event_id=None):
   """ 
      event_id example : 'rec2c8QDkYPO9q4JA'
   """
   if event_id is not None:
      records = api.table(base_id, 'Događanje').get(event_id)
   else:
      records = api.table(base_id, 'Događanje').all(view='Grid view')
   return records
      
def list_tournaments_records(api, base_id, tournament_id=None):
   """ 
      tournament_id example : 'recxbA9SfiL57VLkB'
   """
   if tournament_id is not None:
      records = api.table(base_id, 'Tournaments').get(tournament_id)
   else:
      records = api.table(base_id, 'Tournaments').all(view='Grid view')
   return records

def list_locations_records(api, base_id, location_id=None):
   """ 
      location_id example : 'recyRV88nRMAZIEuE'
   """
   if location_id is not None:
      records = api.table(base_id, 'Lokacije').get(location_id)
   else:
      records = api.table(base_id, 'Lokacije').all(view='Grid view')
   return records

def list_officials_records(api, base_id, official_id=None):
   if official_id is not None:
      records = api.table(base_id, 'Officials').get(official_id)
   else:
      records = api.table(base_id, 'Officials').all(view='Grid view')
   return records


def get_similar_upcoming_matches(api, base_id, sport_id=None, location_id=None, team_id=None, days_ahead=7):
   today = datetime.now().date()
   end_date = today + timedelta(days=days_ahead)

   today_str = today.isoformat()
   end_date_str = end_date.isoformat()

   date_condition = f"AND(IS_AFTER({{Match Date}}, '{today_str}'), IS_BEFORE({{Match Date}}, '{end_date_str}'))"

   try:
      records = api.table(base_id, 'Događanje').all(
         formula=date_condition,
         sort=["Match Date"]
      )
      if not records: return []
   except Exception as e:
      return []
   
   if sport_id is not None:
      sport_ids = sport_id if isinstance(sport_id, list) else [sport_id]
      
      by_sport_events = [
         match for match in records 
         if match['fields'].get('Sport') and 
         any(sid in sport_ids for sid in match['fields']['Sport'])
      ]
      
      if not by_sport_events:
         return records 
   else:
      by_sport_events = records
      
   if team_id is not None:
      team_ids = team_id if isinstance(team_id, list) else [team_id]
      
      by_team_ids = []
      for match in by_sport_events:
         home_team = match['fields'].get('Home Team', [])
         away_team = match['fields'].get('Away Team', [])
         
         if (any(tid in home_team for tid in team_ids) or 
             any(tid in away_team for tid in team_ids)):
            by_team_ids.append(match)
            
      if not by_team_ids and sport_id is not None:
         return by_sport_events
         
      filtered_matches = by_team_ids
   else:
      filtered_matches = by_sport_events
      
   if location_id is not None:
      by_location = [
         match for match in filtered_matches 
         if match['fields'].get('Location') and location_id in match['fields']['Location']
      ]
      if not by_location:
         return filtered_matches
      
      return by_location
      
   return filtered_matches

def get_all_sport_ids(api, base_id):
   sports = list_sport_records(api, base_id)
   sport_ids = [sport['id'] for sport in sports]
   return sport_ids
 
def get_all_location_ids(api, base_id):
   locations = list_locations_records(api, base_id)
   location_ids = [location['id'] for location in locations]
   return location_ids

def get_events_by_date_range(api, base_id, start_date, end_date, sport_id=None, location_id=None, team_id=None):
   if isinstance(start_date, datetime) or isinstance(start_date, date):
      start_date_str = start_date.isoformat()
   else:
      start_date_str = start_date
      
   if isinstance(end_date, datetime) or isinstance(end_date, date):
      end_date_str = end_date.isoformat()
   else:
      end_date_str = end_date
      
   if start_date_str == end_date_str:
      date_condition = f"DATETIME_FORMAT({{Match Date}}, 'YYYY-MM-DD') = '{start_date_str[:10]}'"
   else:
      start_date_formatted = start_date_str[:10]  
      end_date_formatted = end_date_str[:10]     
      
      date_condition = f"AND(IS_SAME_OR_AFTER(DATETIME_FORMAT({{Match Date}}, 'YYYY-MM-DD'), '{start_date_formatted}'), IS_BEFORE(DATETIME_FORMAT({{Match Date}}, 'YYYY-MM-DD'), '{end_date_formatted}', FALSE))"
      
   print(f"Date condition: {date_condition}")
   try:
      records = api.table(base_id, 'Događanje').all(
         formula=date_condition,
         sort=["Match Date"]
      )
      if not records: 
         return []
   except Exception as e:
      print(f"Error fetching events by date range: {e}")
      return []
   
   if sport_id is not None:
      sport_ids = sport_id if isinstance(sport_id, list) else [sport_id]
      
      by_sport_events = [
         match for match in records 
         if match['fields'].get('Sport') and 
         any(sid in sport_ids for sid in match['fields']['Sport'])
      ]
      
      if not by_sport_events:
         return records  
   else:
      by_sport_events = records
   
   if team_id is not None:
      team_ids = team_id if isinstance(team_id, list) else [team_id]
      
      by_team_ids = []
      for match in by_sport_events:
         home_team = match['fields'].get('Home Team', [])
         away_team = match['fields'].get('Away Team', [])
         
         if (any(tid in home_team for tid in team_ids) or 
               any(tid in away_team for tid in team_ids)):
               by_team_ids.append(match)
               
      if not by_team_ids and sport_id is not None:
         return by_sport_events 
         
      filtered_matches = by_team_ids
   else:
      filtered_matches = by_sport_events
   
   if location_id is not None:
      location_ids = location_id if isinstance(location_id, list) else [location_id]
      
      by_location = [
         match for match in filtered_matches 
         if match['fields'].get('Location') and 
         any(lid in match['fields']['Location'] for lid in location_ids)
      ]
      
      if not by_location:
         return filtered_matches 
      
      return by_location
   
   return filtered_matches