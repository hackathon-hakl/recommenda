import json
import os
from datetime import datetime
from API import api, base_id, list_sport_records, list_teams_records, list_events_records, list_tournaments_records, list_category_records, list_locations_records

class ClickTracker:
   def __init__(self, database_path='user_clicks.json'):
      self.user_db_path = database_path
      self._load_or_create_db()
      
   def _load_or_create_db(self):
      """Load existing click database or create new one if it doesn't exist"""
      if os.path.exists(self.user_db_path):
         with open(self.user_db_path, 'r', encoding='utf-8') as f:
               self.user_db = json.load(f)
      else:
         self.user_db = {"users": {}}
         self._save_db()
   
   def _save_db(self):
      with open(self.user_db_path, 'w', encoding='utf-8') as f:
         json.dump(self.user_db, f, indent=4, ensure_ascii=False)
   
   def initialize_user(self, user_id, user_data):
      """Initialize a new user with profile data"""
      users = self.user_db["users"]
      if user_id not in users:
         users[user_id] = {
               "user_id": user_id,
               "age": "DEFAULT", 
               "city": None,
               "district": None,
               "user_name": None,
               "sport_interests": [],        
               "sports_liked_count": {},     
               "teams_liked": [],             
               "team_liked_sport": {},        
               "team_liked_location": {},    
               "player_liked_sports_count": {},
               "events_liked": [],           
               "training_liked_teams": [],
               "training_sports_liked": {},
               "training_location": [],
               "event_type_priority": ["match", "tournament"],
               "events_clicked": {},        
               "sports_clicked": {},          
               "teams_clicked": {}           
         }
         
         if user_data:
            users[user_id]["user_name"] = user_data.get("user_name")
            users[user_id]["age"] = user_data.get("age", 25)
            users[user_id]["city"] = user_data.get("city", "").lower() if user_data.get("city") else None
            users[user_id]["district"] = user_data.get("district", "").lower() if user_data.get("district") else None
            users[user_id]["sport_interests"] = user_data.get("sport_interests", [])
            users[user_id]["event_type_priority"] = user_data.get("event_type_priority", ["match", "tournament"])
            
            for sport_id in users[user_id]["sport_interests"]:
               users[user_id]["sports_liked_count"][sport_id] = 1
               
         self._save_db()
      
      return users[user_id]
   
   def update_user(self, user_id, user_data):
      """Update user profile data"""
      users = self.user_db["users"]
      if user_id in users:
         if "user_name" in user_data:
            users[user_id]["user_name"] = user_data["user_name"]
         if "age" in user_data:
            users[user_id]["age"] = int(user_data["age"])
         if "city" in user_data:
            users[user_id]["city"] = user_data["city"].lower()
         if "district" in user_data:
            users[user_id]["district"] = user_data["district"].lower()
         if "sport_interests" in user_data:
            users[user_id]["sport_interests"] = user_data["sport_interests"]
         if "event_type_priority" in user_data:
            users[user_id]["event_type_priority"] = user_data["event_type_priority"]
         if 'sport_type_preference' in user_data:
            users[user_id]["sport_type_preference"] = user_data["sport_type_preference"]
         self._save_db()
      return users[user_id]
   
   def get_user(self, user_id):
      users = self.user_db["users"]
      if user_id not in users:
         return self.initialize_user(user_id, None)
      return users[user_id]

   def track_event_click(self, user_id, event_id):
      user = self.get_user(user_id)
      
      try:
         event_data = list_events_records(api, base_id, event_id)
         
         event_fields = event_data.get("fields", {})
         
         event_time = event_fields.get("Match Time", [None])[0] if "Match Time" in event_fields else None
         event_date = event_fields.get("Match Date", [None])[0] if "Match Date" in event_fields else None
         location_id = event_fields.get("Location", [None])[0] if "Location" in event_fields else None
         home_team_id = event_fields.get("Home Team", [None])[0] if "Home Team" in event_fields else None
         away_team_id = event_fields.get("Away Team", [None])[0] if "Away Team" in event_fields else None
         sport_id = event_fields.get("Sport", [None])[0] if "Sport" in event_fields else None
         category_id = event_fields.get("Kategorija", [None])[0] if "Kategorija" in event_fields else None

         sport_info = list_sport_records(api, base_id, sport_id) if sport_id else {}
         home_team_info = list_teams_records(api, base_id, home_team_id) if home_team_id else {}
         away_team_info = list_teams_records(api, base_id, away_team_id) if away_team_id else {}
         
         sport_name = sport_info.get("fields", {}).get("Sport Name", "") if sport_info else ""
         
         event_metadata = {
               "event_id": event_id,
               "event_type": "MATCH",
               "event_time": event_time,
               "event_date": event_date,
               "sport_id": sport_id,
               "sport_name": sport_name,
               "home_team_id": home_team_id,
               "away_team_id": away_team_id,
               "home_team": home_team_info.get("fields", {}).get("Team Name", "") if home_team_info else "", 
               "away_team": away_team_info.get("fields", {}).get("Team Name", "") if away_team_info else "", 
               "category_id": category_id,
               "location_id": location_id,
               "timestamp": datetime.now().isoformat()
         }
         
         if event_id not in user["events_clicked"]:
               user["events_clicked"][event_id] = 0
         user["events_clicked"][event_id] += 1
         
         user["events_liked"].append(event_metadata)
         
         if sport_id:
               if sport_id not in user["sports_clicked"]:
                  user["sports_clicked"][sport_id] = 0
               user["sports_clicked"][sport_id] += 1
               
               if sport_id not in user["sports_liked_count"]:
                  user["sports_liked_count"][sport_id] = 0
               user["sports_liked_count"][sport_id] += 1
               
               if sport_id not in user["sport_interests"]:
                  user["sport_interests"].append(sport_id)
         
         for team_id in [home_team_id, away_team_id]:
               if team_id:
                  if team_id not in user["teams_liked"]:
                     user["teams_liked"].append(team_id)
                  
                  if team_id not in user["teams_clicked"]:
                     user["teams_clicked"][team_id] = 0
                  user["teams_clicked"][team_id] += 1
                  
                  if sport_id:
                     if sport_id not in user["team_liked_sport"]:
                        user["team_liked_sport"][sport_id] = 0
                     user["team_liked_sport"][sport_id] += 1
         
         self._save_db()
                  
         return event_metadata
         
      except Exception as e:
         print(f"Error tracking event click: {e}")
         return None

   def track_team_click(self, user_id, team_id):
      user = self.get_user(user_id)
      
      try:
         team_data = list_teams_records(api, base_id, team_id)
         
         team_fields = team_data.get("fields", {})
         team_name = team_fields.get("Team Name", "")
         home_team_matches = team_fields.get("Matches (Home Team)", [])
         away_team_matches = team_fields.get("Matches (Away Team)", [])
         
         sport_ids = team_fields.get("Sport", []) if isinstance(team_fields.get("Sport"), list) else [team_fields.get("Sport")]
         team_category_id = team_fields.get("Category", [None])[0] if "Category" in team_fields else None

         if team_id not in user["teams_clicked"]:
               user["teams_clicked"][team_id] = 0
         user["teams_clicked"][team_id] += 1
         
         if team_id not in user["teams_liked"]:
               user["teams_liked"].append(team_id)
         
         sport_names = []  
         for sport_id in sport_ids:
               if sport_id:
                  try:
                     sport_info = list_sport_records(api, base_id, sport_id)
                     if sport_info and "fields" in sport_info:
                           sport_name = sport_info["fields"].get("Sport Name", "")
                           if sport_name:
                              sport_names.append(sport_name)  
                              
                           if sport_id not in user["team_liked_sport"]:
                              user["team_liked_sport"][sport_id] = 0
                           user["team_liked_sport"][sport_id] += 1
                           
                           if sport_id not in user["sports_liked_count"]:
                              user["sports_liked_count"][sport_id] = 0
                           user["sports_liked_count"][sport_id] += 1
                           
                           if sport_id not in user["sport_interests"]:
                              user["sport_interests"].append(sport_id)
                  except Exception as e:
                     print(f"Error processing sport {sport_id} for team {team_id}: {e}")
         
         self._save_db()
                        
         return {
               "team_id": team_id,
               "team_name": team_name,  
               "sport_ids": sport_ids,
               "sport_names": sport_names,  
               "home_team_matches": home_team_matches,
               "away_team_matches": away_team_matches,
               "category_id": team_category_id
         }
         
      except Exception as e:
         print(f"Error tracking team click: {e}")
         return None

   def track_sport_click(self, user_id, sport_id):
      user = self.get_user(user_id)
      print(f"Tracking sport click for user {user_id} and sport {sport_id}")
      try:
         if sport_id:
            print(f"Sport ID: {sport_id}")
            if sport_id not in user["sports_clicked"]:
               user["sports_clicked"][sport_id] = 0
            user["sports_clicked"][sport_id] += 1
            
            if sport_id not in user["sports_liked_count"]:
               user["sports_liked_count"][sport_id] = 0
            user["sports_liked_count"][sport_id] += 1
            
            if sport_id not in user["sport_interests"]:
               user["sport_interests"].append(sport_id)
         print(f"User {user_id} clicked on sport {sport_id}.")
         print(f"User data before saving: {user}")
         
         self._save_db()
                     
         return {
               "sport_id": sport_id,
               "sport_name": sport_id
         }
         
      except Exception as e:
         print(f"Error tracking sport click: {e}")
         return None
   
   def track_tournament_click(self, user_id, tournament_id):
      user = self.get_user(user_id)
      
      try:
         tournament_data = list_tournaments_records(api, base_id, tournament_id)
         
         tournament_fields = tournament_data.get("fields", {})
         tournament_name = tournament_fields.get("Tournament Name", "") 
         start_date = tournament_fields.get("Start Date", [None])[0] if "Start Date" in tournament_fields else None
         end_date = tournament_fields.get("End Date", [None])[0] if "End Date" in tournament_fields else None
         sport_id = tournament_fields.get("Sport", [None])[0] if "Sport" in tournament_fields else None
         category_id = tournament_fields.get("Kategorija", [None])[0] if "Kategorija" in tournament_fields else None
         location_id = tournament_fields.get("Location", [None])[0] if "Location" in tournament_fields else None
         matches = tournament_fields.get("Matches", []) if "Matches" in tournament_fields else []
         
         sport_name = ""
         if sport_id:
               sport_info = list_sport_records(api, base_id, sport_id)
               if sport_info and "fields" in sport_info:
                  sport_name = sport_info["fields"].get("Sport Name", "")
         
         tournament_metadata = {
               "event_id": tournament_id,
               "event_type": "TOURNAMENT",
               "start_date": start_date,
               "end_date": end_date,
               "sport_id": sport_id,
               "sport_name": sport_name, 
               "tournament_name": tournament_name, 
               "category_id": category_id,
               "location_id": location_id,
               "match_ids": matches,
               "timestamp": datetime.now().isoformat()
         }
         
         user["events_liked"].append(tournament_metadata)
         
         if sport_id:
               if sport_id not in user["sports_liked_count"]:
                  user["sports_liked_count"][sport_id] = 0
               user["sports_liked_count"][sport_id] += 1
               
               if sport_id not in user["sport_interests"]:
                  user["sport_interests"].append(sport_id)
         
         if "tournament" not in user["event_type_priority"] and "TOURNAMENT" not in user["event_type_priority"]:
               user["event_type_priority"].append("tournament")
         
         self._save_db()
         
         return tournament_metadata
         
      except Exception as e:
         print(f"Error tracking tournament click: {e}")
         return None

   def set_user_stats(self, user_id, user_data):
      user = self.get_user(user_id)

      if "age" in user_data:
         user["age"] = int(user_data["age"])
      if "sport_interests" in user_data:
         user["sport_interests"] = user_data["sport_interests"]  
      if "city" in user_data:
         user["city"] = user_data["city"].lower()
      if "district" in user_data:
         user["district"] = user_data["district"].lower()
      if "event_type_priority" in user_data:
         user["event_type_priority"] = user_data["event_type_priority"]
      if "user_name" in user_data:
         user["user_name"] = user_data["user_name"]

      self._save_db()
      return user
   
   def get_user_stats(self, user_id):
      """Get statistics about user interactions"""
      user = self.get_user(user_id)
      
      favorite_sports = []
      for sport_id, count in sorted(user.get("sports_liked_count", {}).items(), key=lambda x: x[1], reverse=True)[:5]:
         try:
            sport_data = list_sport_records(api, base_id, sport_id)
            sport_name = sport_data.get("fields", {}).get("Sport Name", "Unknown")
            favorite_sports.append((sport_id, sport_name, count))
         except:
            favorite_sports.append((sport_id, "Unknown Sport", count))
      
      favorite_teams = []
      for team_id in user.get("teams_liked", [])[:5]:
         try:
            team_data = list_teams_records(api, base_id, team_id)
            team_name = team_data.get("fields", {}).get("Team Name", "Unknown")
            favorite_teams.append((team_id, team_name))
         except:
            favorite_teams.append((team_id, "Unknown Team"))
      
      return {
         "total_events_clicked": len(user.get("events_clicked", {})),
         "favorite_sports": favorite_sports,
         "favorite_teams": favorite_teams,    
         "recent_events": user.get("events_liked", [])[-5:],
         "sport_interests": user.get("sport_interests", [])  
      }

   def get_db(self):
      return self.user_db