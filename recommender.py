from enum import Enum
import json
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from API import api, base_id, get_similar_upcoming_matches, list_teams_records, list_sport_records

class EventType(Enum):
   MATCH = 1    
   TRAINING = 2
   PLAYER = 3
   CLUB = 4
   TOURNAMENT = 5
   LEAGUE = 6

class GroupSportType(Enum):
   TEAM = 1
   INDIVIDUAL = 2
   DEFAULT = 3
   
class ActivitiesEnjoyed(Enum):
   RUNNING = 1  # Trčanje
   STRENGTH_AND_ENDURANCE = 2  # Izgradnja snage i izdržljivosti
   STRATEGIC_PLANNING = 3  # Strateško planiranje poteza
   BALANCE_AND_AGILITY = 4  # Izgradnja ravnoteže i spretnosti
   MARTIAL_ARTS = 5  # Borilačke vještine
   SWIMMING_AND_WATER = 6  # Plivanje i vodene aktivnosti
   DANCE_AND_RHYTHM = 7  # Ples i ritmično kretanje
   BALL = 8  # Igranje lopte
   OTHER = 9  # Drugo
   
class AgeGroup(Enum):
   PRESCHOOL = 1  # (4-7 godina)
   PRIMARY_SCHOOL = 2  # (7-14 godina)
   JUNIORS = 3  # (15-18 godina)
   ADULTS = 4  # (18-40 godina)
   VETERANS = 5  # (35+ godina)
   
class RecommendationType(Enum):
   USER_BASED = 1
   ITEM_BASED = 2
   COLLABORATIVE = 3

class Recommendation(Enum):
   MATCHES = 1
   EVENTS = 2

class Recommender:
   def __init__(self, database_path, sports_ids, location_ids):
      self.database_path = database_path
      with open(database_path, 'r', encoding='utf-8') as f:
         self.database = json.load(f)
      self.users = self.database.get('users', {})
      self.user_ids = {user : i for i, user in enumerate(self.users.keys())}
      self.sports_ids = {sport: i for i, sport in enumerate(sports_ids)}
      self.sports_num = len(self.sports_ids)
      self._build_user_similarity_matrix()
   
   def _load_database(self):
      with open(self.database_path, 'r', encoding='utf-8') as f:
         self.database = json.load(f)
      self.users = self.database.get('users', {})
      self.user_ids = {user : i for i, user in enumerate(self.users.keys())}
      
   def _encode_location(self, city, distict):
      location = f"{city.lower()}_{distict.lower()}"
      loc_hash = abs(hash(location)) % 1000 +1
      return loc_hash / 10000
   
   def _build_user_similarity_matrix(self):
      """Build similarity matrix between users based on their profiles using fixed-length sport vectors"""
      features = []
      
      for user_id in self.database['users'].keys():
         user = self.users[user_id] 

         age_feature = user.get('age', 'JUNIORS')
         age_feature = AgeGroup[age_feature.upper()].value - 1 if age_feature in AgeGroup.__members__ else 0
         
         city = user.get('city', '').lower() if user.get('city') else ''
         district = user.get('district', '').lower() if user.get('district') else ''
         location_feature = self._encode_location(city, district)
         
         
         sport_interests_vector = [0] * (self.sports_num)
         sports_liked_vector = [0] * (self.sports_num)
         team_sport_vector = [0] * (self.sports_num)
         player_sports_vector = [0] * (self.sports_num)
         training_sports_vector = [0] * (self.sports_num)
         
         for sport in user.get('sport_interests', []):
            if sport in self.sports_ids:
               sport_id = self.sports_ids[sport]
               sport_interests_vector[sport_id] = 1
         
         for sport, count in user.get('sports_liked_count', {}).items():
            if sport in self.sports_ids:
               sport_id = self.sports_ids[sport]
               sports_liked_vector[sport_id] = count
         
         for sport, count in user.get('team_liked_sport', {}).items():
            if sport in self.sports_ids:
               sport_id = self.sports_ids[sport]
               team_sport_vector[sport_id] = count
         
         for sport, count in user.get('player_liked_sports_count', {}).items():
            if sport in self.sports_ids:
               sport_id = self.sports_ids[sport]
               player_sports_vector[sport_id] = count
      
         for sport, count in user.get('training_sports_liked', {}).items():
            if sport in self.sports_ids:
               sport_id = self.sports_ids[sport]
               training_sports_vector[sport_id] = count
         
         event_type_vector = [0] * len(EventType)
         for event_type in user.get('event_type_priority', []):
               event_id = EventType[event_type.upper()].value - 1  
               event_type_vector[event_id] = 1
 
         event_liked_vector = [0] * (self.sports_num)
         event_type_liked_vector = [0] * len(EventType)
         
         for event in user.get('events_liked', []):
            event_sport = event.get('sport_id', '')
            if event_sport in self.sports_ids:
               sport_id = self.sports_ids[event_sport]
               event_liked_vector[sport_id] += 1
            
            event_type = event.get('event_type', '')
            try:
               event_type_id = EventType[event_type.upper()].value - 1
               event_type_liked_vector[event_type_id] += 1
            except (KeyError, ValueError):
               continue
      
         user_vector = [
               age_feature,
               location_feature
         ]
         
         user_vector.extend(sport_interests_vector)
         user_vector.extend(sports_liked_vector)
         user_vector.extend(team_sport_vector)
         user_vector.extend(player_sports_vector)
         user_vector.extend(training_sports_vector)
         user_vector.extend(event_type_vector)
         user_vector.extend(event_liked_vector)
         user_vector.extend(event_type_liked_vector)
         
         features.append(user_vector)
      
      features_array = np.array(features)
      self.user_similarity = cosine_similarity(features_array)
      
   def _get_similar_users(self, user_id, n=3):
      """Get similar users based on similarity matrix - optimized version"""
      if user_id not in self.user_ids:
         return []
      user_index = self.user_ids[user_id]
         
      similarities = self.user_similarity[user_index]
      
      idx_to_user = {idx: uid for uid, idx in self.user_ids.items()}
      
      top_indices = np.argsort(similarities)[-n-1:][::-1]
      
      similar_users = []
      for idx in top_indices:
         if idx != user_index and idx in idx_to_user:
               similar_id = idx_to_user[idx]
               profile = self.get_user_profile(similar_id)
               if profile:
                  similar_users.append(profile)
                  if len(similar_users) >= n:
                     break
      
      return similar_users
   
   def update_user(self, user_id, user_data):
      if user_id not in self.user_ids:
         self.user_ids[user_id] = len(self.users)
      user = self.get_user_profile(user_id)
      self.users.update({"user_id": user_id, **user_data})     
      self._build_user_similarity_matrix()
   
   def get_user_profile(self, user_id):
      print(self.users)
      if user_id in self.user_ids:
         return self.users[user_id]
      return None
   
   def get_homepage_recommendations(self, user_id, limit=10):
      self._build_user_similarity_matrix()
      print(user_id)
      user = self.get_user_profile(user_id)
      
      similar_users = self._get_similar_users(user_id)
      print(f"Similar user : {similar_users}")
      recommendations = {
         "favorite_sports": self._get_favorite_sports(user, limit),
         "upcoming_events": self._get_upcoming_events(user, similar_users, limit),
         "recommended_teams": self._get_recommended_teams(user, similar_users, limit)
      }
      
      return recommendations
   
   def get_sport_recommendations(self, user_id, sport_name, limit=5):
      user = self.get_user_profile(user_id)
      
      similar_users = self._get_similar_users(user_id)
      
      recommended_teams = self._get_teams_by_sport(user, similar_users, sport_name, limit)
      
      recommended_events = self._get_events_by_sport(user, similar_users, sport_name, limit)
      
      recommended_training = self._get_training_by_sport(user, similar_users, sport_name, limit)
      
      recommendations = {
         "teams": recommended_teams,
         "events": recommended_events,
         "training": recommended_training,
      }
      
      return recommendations
   
   def get_event_recommendations(self, user_id, limit=5):
      """Get recommendations for the events page"""
      user = self.get_user_profile(user_id)
      if not user:
         return []
      
      similar_users = self._get_similar_users(user_id)
      
      recommendations = {
         "recommended_events": self._get_upcoming_events(user, similar_users, limit),
      }
      
      return recommendations
   
   def get_tournament_recommendations(self, user_id, limit=5):
      """Get tournament recommendations"""
      user = self.get_user_profile(user_id)
      if not user:
         return []
      
      similar_users = self._get_similar_users(user_id)
      
      tournaments = self._get_events_by_type(user, similar_users, "tournament", limit)
      
      return tournaments
   
   def _get_favorite_sports(self, user, limit=5):
      if isinstance(user, dict):
        user_profile = user
      else:
         user_profile = self.get_user_profile(user)
         if not user_profile:
               return []
      if user_profile.get('sport_interests'):
        return user_profile['sport_interests'][:limit]
    
      if 'sports_liked_count' in user_profile:
         sorted_sports = sorted(
               user_profile['sports_liked_count'].items(), 
               key=lambda x: x[1], 
               reverse=True
         )
         return [sport_id for sport_id, count in sorted_sports[:limit]]
      
      return []
         
   def _get_recommended_teams(self, user, similar_users, limit=5):
      """Get recommended teams based on user preferences and similar users"""
      user_teams = set(user.get('teams_liked', []))
      
      recommended_teams = []
      
      for similar_user in similar_users:
         if 'teams_clicked' in similar_user:
               for team_id, click_count in similar_user['teams_clicked'].items():
                  if team_id not in user_teams:
                     recommended_teams.append({
                           'team': team_id,
                           'clicks': click_count
                     })
      
      sorted_teams = sorted(recommended_teams, key=lambda x: x['clicks'], reverse=True)
      
      unique_teams = []
      seen = set()
      for team in sorted_teams:
         if team['team'] not in seen:
               seen.add(team['team'])
               unique_teams.append(team)
      
      teams_data = []
      for team_info in unique_teams[:limit]:
         team_id = team_info['team']
         try:
               team_record = list_teams_records(api, base_id, team_id)
               if team_record and 'fields' in team_record:
                  team_info['name'] = team_record['fields'].get('Team Name', 'Unknown Team')
                  if 'Team Logo' in team_record['fields'] and team_record['fields']['Team Logo']:
                     team_info['logo_url'] = team_record['fields']['Team Logo'][0]['url']
         except Exception as e:
               pass
         
         teams_data.append(team_info)
      
      return teams_data[:limit]
   
   def _get_teams_by_sport(self, user, similar_users, sport_name, limit=5):
      """Get recommended teams for a specific sport"""
      teams = []
      sport_id = self.sports.get(sport_name, None)
      
      if 'teams_liked' in user and 'team_liked_sport' in user:
         team_liked_sport = user['team_liked_sport'][sport_name]
         team_liked_locations = user['team_liked_location']
         teams_liked = user['teams_liked']
         
      unique_teams, unique_locations = [], []
      for similar_user in similar_users:
         if 'teams_liked' in similar_user and 'team_liked_sport' in similar_user:
               user_liked_sport = similar_user['team_liked_sport'].get(sport_name, None)
               user_liked_location = similar_user['team_liked_location']
               user_liked_teams = similar_user['teams_liked']
               unique_teams.append(user_liked_teams)
               unique_locations.append(user_liked_location)
           
      unique_teams, unique_locations = set(unique_teams), set(unique_locations)   
      seen = set()
      for team_info in teams:
         if team_info['team'] not in seen:
               seen.add(team_info['team'])
               unique_teams.append(team_info)
      
      return unique_teams[:limit]
   
   def _get_events_by_sport(self, user, similar_users, sport_id, limit=5):
      """Get events for a specific sport"""
      all_events = []
      
      if 'events_liked' in user:
         for event in user.get('events_liked', []):
               if event.get('event_sport') == sport_id:
                  all_events.append(event)
      
      for similar_user in similar_users:
         if 'events_liked' in similar_user:
               for event in similar_user.get('events_liked', []):
                  if event.get('event_sport') == sport_id:
                     all_events.append(event)
      
      unique_events = {}
      for event in all_events:
         event_id = event.get('event_id')
         if event_id and event_id not in unique_events:
               unique_events[event_id] = event
      
      events_list = list(unique_events.values())
      sorted_events = sorted(events_list, 
                           key=lambda x: pd.to_datetime(x.get('event_date', '1/1/2000'), format='%m/%d/%Y'))
      
      today = pd.Timestamp.now()
      upcoming = [e for e in sorted_events if pd.to_datetime(e.get('event_date', '1/1/2000'), 
                                                            format='%m/%d/%Y') > today]
      
      return upcoming[:limit]
   
   def _get_training_by_sport(self, user, similar_users, sport_id, limit=5):
      """Get training opportunities for a specific sport"""
      trainings = []
      
      if 'training_sport' in user and 'training_liked_teams' in user:
         for i, sport in enumerate(user.get('training_sport', [])):
               if sport == sport_id and i < len(user.get('training_liked_teams', [])):
                  team = user['training_liked_teams'][i]
                  location = user.get('training_location', [])[i] if i < len(user.get('training_location', [])) else None
                  trainings.append({"team": team, "location": location})
      
      for similar_user in similar_users:
         if 'training_sport' in similar_user and 'training_liked_teams' in similar_user:
               for i, sport in enumerate(similar_user.get('training_sport', [])):
                  if sport == sport_id and i < len(similar_user.get('training_liked_teams', [])):
                     team = similar_user['training_liked_teams'][i]
                     location = similar_user.get('training_location', [])[i] if i < len(similar_user.get('training_location', [])) else None
                     trainings.append({"team": team, "location": location})
      
      unique_trainings = []
      seen = set()
      for training in trainings:
         key = f"{training['team']}"
         if key not in seen:
               seen.add(key)
               unique_trainings.append(training)
      
      return unique_trainings[:limit]
   
   def _get_events_by_favorite_sports(self, user, limit=5):
      """Get events for the user's favorite sports"""
      favorite_sports = self._get_favorite_sports(user, 3)  # Top 3 favorite sports
      events = []
      
      if 'events_liked' in user:
         for event in user.get('events_liked', []):
               if event.get('event_sport') in favorite_sports:
                  events.append(event)
      
      sorted_events = sorted(events, 
                           key=lambda x: pd.to_datetime(x.get('event_date', '1/1/2000'), format='%m/%d/%Y'))
      
      today = pd.Timestamp.now()
      upcoming = [e for e in sorted_events if pd.to_datetime(e.get('event_date', '1/1/2000'), 
                                                            format='%m/%d/%Y') > today]
      
      return upcoming[:limit]
   
   def _get_events_by_type(self, user, similar_users, event_type, limit=5):
      """Get events by their type (tournament, match, etc.)"""
      type_events = []
      
      all_events = []
      if 'events_liked' in user:
         all_events.extend(user.get('events_liked', []))
      
      for similar_user in similar_users:
         if 'events_liked' in similar_user:
               all_events.extend(similar_user.get('events_liked', []))
      
      for event in all_events:
         if event.get('event_type') == event_type:
               type_events.append(event)
      
      sorted_events = sorted(type_events, 
                           key=lambda x: pd.to_datetime(x.get('event_date', '1/1/2000'), format='%m/%d/%Y'))
      
      today = pd.Timestamp.now()
      upcoming = [e for e in sorted_events if pd.to_datetime(e.get('event_date', '1/1/2000'), 
                                                            format='%m/%d/%Y') > today]
      
      unique_events = {}
      for event in upcoming:
         event_id = event.get('event_id')
         if event_id and event_id not in unique_events:
               unique_events[event_id] = event
      
      return list(unique_events.values())[:limit]
   
   def get_user_favorites(self, user_id, limit=5):
      user = self.get_user_profile(user_id)
      if not user:
         return {}
      
      favorites = {
         "sports": self._get_favorite_sports(user, limit),
         "teams": user.get('teams_liked', [])[:limit],
         "events": []
      }
      
      if 'events_liked' in user:
         events = user['events_liked']
         sorted_events = sorted(events, 
                                 key=lambda x: pd.to_datetime(x.get('event_date', '1/1/2000'), format='%m/%d/%Y'))
         
         today = pd.Timestamp.now()
         upcoming = [e for e in sorted_events if pd.to_datetime(e.get('event_date', '1/1/2000'), 
                                                               format='%m/%d/%Y') > today]
         favorites["events"] = upcoming[:limit]
      
      return favorites
   
   def _get_upcoming_events(self, user, similar_users, limit=5):
      """Get upcoming events based on user preferences and similar users"""
      all_events = []
      print(f"user : {user}")
      if 'events_liked' in user:
         all_events.extend(user['events_liked'])
      
      for similar_user in similar_users:
         if 'events_liked' in similar_user:
               all_events.extend(similar_user['events_liked'])
      
     
      try:
         if 'sports_liked_count' in user:
            if 'sport_interests' in user:
               favorite_sports = user['sport_interests'][:3]
            else:
               favorite_sports = sorted(user['sports_liked_count'].items(), key=lambda x: x[1], reverse=True)
               favorite_sports = [sport for sport, count in favorite_sports[:3]] 
            
            favorite_teams = user.get('teams_liked', [])[:10]
            
            api_matches = get_similar_upcoming_matches(
                  api, 
                  base_id,
                  sport_id=favorite_sports if favorite_sports else None,
                  team_id=favorite_teams if favorite_teams else None,
                  days_ahead=7
            )
            
            for match in api_matches:
               fields = match.get('fields', {})
               
               print(f"fields : {fields}")
               
               home_team = fields.get('Home Team', [''])[0] if fields.get('Home Team') else None
               away_team = fields.get('Away Team', [''])[0] if fields.get('Away Team') else None
               
               home_team_data  = list_teams_records(
                  api, base_id, team_id=home_team
               )
               
               away_team_data  = list_teams_records(
                  api, base_id, team_id=away_team
               )
               
               event = {
                  "event_id": match.get('id', ''),
                  "event_type": "MATCH",
                  "event_date": fields.get('Match Date', ''),
                  "sport_id": fields.get('Sport', [''])[0] if fields.get('Sport') else None,
                  "home_team_id": home_team,
                  "home_team_logo" : home_team_data['fields']['Team Logo'][0]['url'],
                  "away_team_id": away_team,
                  "away_team_logo" : away_team_data['fields']['Team Logo'][0]['url'],
                  "location_id": fields.get('Location', [''])[0] if fields.get('Location') else '',
                  "from_api": True ,
                  "kategorija" : fields.get('Kategorija', ['']) if fields.get('Kategorija') else None
               }
               all_events.append(event)
      except:
         return []
      
      return all_events[:limit]

   def get_real_time_match_recommendations(self, user_id, limit=5):
      self._build_user_similarity_matrix()
      user = self.get_user_profile(user_id)
      if not user:
         return []
      
      favorite_sports = []
      if 'sport_interests' in user:
         favorite_sports = user['sport_interests'][:3]
      elif 'sports_liked_count' in user:
         favorite_sports = sorted(user['sports_liked_count'].items(), key=lambda x: x[1], reverse=True)
         favorite_sports = [sport for sport, count in favorite_sports[:3]]  # Top 3 sports
      
      favorite_teams = user.get('teams_liked', [])[:5]  # Top 5 teams
      
      matches = get_similar_upcoming_matches(
         api, 
         base_id,
         sport_id=favorite_sports if favorite_sports else None,
         team_id=favorite_teams if favorite_teams else None,
         days_ahead=20 
      )
      
      if not matches and favorite_sports:
         matches = get_similar_upcoming_matches(
            api,
            base_id,
            sport_id=favorite_sports,
            days_ahead=7
         )
      
      if not matches:
         matches = get_similar_upcoming_matches(
            api,
            base_id,
            days_ahead=5
         )
      
      formatted_matches = []
      for match in matches[:limit]:
         fields = match.get('fields', {})
         
         home_team_id = fields.get('Home Team', [''])[0] if fields.get('Home Team') else ''
         away_team_id = fields.get('Away Team', [''])[0] if fields.get('Away Team') else ''
         home_team_name = "Unknown Team"
         away_team_name = "Unknown Team"
         home_team_logo = None
         away_team_logo = None

         try:
            if home_team_id:
                  home_team_info = list_teams_records(api, base_id, home_team_id)
                  home_team_name = home_team_info.get('fields', {}).get('Team Name', 'Unknown Team')
                  if 'Team Logo' in home_team_info.get('fields', {}) and home_team_info['fields']['Team Logo']:
                     home_team_logo = home_team_info['fields']['Team Logo'][0]['url']
            if away_team_id:
                  away_team_info = list_teams_records(api, base_id, away_team_id)
                  away_team_name = away_team_info.get('fields', {}).get('Team Name', 'Unknown Team')
                  if 'Team Logo' in away_team_info.get('fields', {}) and away_team_info['fields']['Team Logo']:
                     away_team_logo = away_team_info['fields']['Team Logo'][0]['url']
         except Exception:
            pass
         
         sport_id = fields.get('Sport', [''])[0] if fields.get('Sport') else ''
         sport_name = "Unknown Sport"
         
         try:
            if sport_id:
                  sport_info = list_sport_records(api, base_id, sport_id)
                  sport_name = sport_info.get('fields', {}).get('Sport Name', 'Unknown Sport')
         except Exception:
            pass
         
         formatted_match = {
            "event_id": match.get('id', ''),
            "event_type": "MATCH",
            "event_time": fields.get('Match Time', ''),
            "event_date": fields.get('Match Date', ''),
            "sport_id": sport_id,
            "sport_name": sport_name,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_team": home_team_name,
            "away_team": away_team_name,
            "home_team_logo": home_team_logo,	
            "away_team_logo": away_team_logo,
            "location_id": fields.get('Location', [''])[0] if fields.get('Location') else '',
            "is_recommended": True
         }
         
         formatted_matches.append(formatted_match)
      
      return formatted_matches
   

from typing import List
class RuleBasedRecommender:
   def __init__(self):
      self.sport_name_to_id = {
         'Hokej na travi' : 'recGfphnFce1DEBhE',
         'Ragbi' : 'recUmMssS0H4uzmgT',
         'Šah' : 'recj8YX9QFNCQitNX',
         'Nogomet' : 'rechBDkyGTVt63HkC',
         'Odbojka' : 'rec4Q3FEtoheO51gX'
      } 
      
   def get_user_recommendations(self, group_style: GroupSportType, activities: List[ActivitiesEnjoyed], age_group: AgeGroup):
      sport_scores = {
         'Hokej na travi': 0,
         'Ragbi': 0,
         'Šah': 0,
         'Nogomet': 0,
         'Odbojka': 0
      }
      
      if group_style == GroupSportType.TEAM:
        sport_scores['Hokej na travi'] += 2
        sport_scores['Ragbi'] += 2
        sport_scores['Nogomet'] += 2
        sport_scores['Odbojka'] += 2
        sport_scores['Šah'] -= 1  
      elif group_style == GroupSportType.INDIVIDUAL:
         sport_scores['Šah'] += 3 
    
      for activity in activities:
         if activity == ActivitiesEnjoyed.RUNNING:
               sport_scores['Hokej na travi'] += 2
               sport_scores['Nogomet'] += 2
               sport_scores['Ragbi'] += 1
         elif activity == ActivitiesEnjoyed.STRENGTH_AND_ENDURANCE:
               sport_scores['Ragbi'] += 3
               sport_scores['Nogomet'] += 1
               sport_scores['Hokej na travi'] += 1
         elif activity == ActivitiesEnjoyed.STRATEGIC_PLANNING:
               sport_scores['Šah'] += 3
               sport_scores['Hokej na travi'] += 1
               sport_scores['Nogomet'] += 1
               sport_scores['Odbojka'] += 1
         elif activity == ActivitiesEnjoyed.BALANCE_AND_AGILITY:
               sport_scores['Nogomet'] += 2
               sport_scores['Odbojka'] += 2
               sport_scores['Hokej na travi'] += 1
         elif activity == ActivitiesEnjoyed.MARTIAL_ARTS:
               sport_scores['Odbojka'] += 1  
         elif activity == ActivitiesEnjoyed.SWIMMING_AND_WATER:
               pass
         elif activity == ActivitiesEnjoyed.DANCE_AND_RHYTHM:
               pass
         elif activity == ActivitiesEnjoyed.BALL:
            sport_scores['Hokej na travi'] += 1
            sport_scores['Ragbi'] += 1
            sport_scores['Odbojka'] += 3
            sport_scores['Nogomet'] += 3
    
      if age_group == AgeGroup.PRESCHOOL:
         sport_scores['Hokej na travi'] -= 1  
         sport_scores['Ragbi'] -= 2  
      elif age_group == AgeGroup.VETERANS:
         sport_scores['Ragbi'] -= 2  
         sport_scores['Hokej na travi']  -= 1  
         sport_scores['Šah'] += 3
      
      sorted_sports = sorted(sport_scores.items(), key=lambda x: x[1], reverse=True)
      recommended_sport_name = sorted_sports[0][0]
      
      recommended_sport_id = self.sport_name_to_id.get(recommended_sport_name)
      if not recommended_sport_id:
         return [self.sport_name_to_id['Hokej na travi']]
      
      return recommended_sport_id