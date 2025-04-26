from API import *
from recommender import Recommender
from click_tracker import ClickTracker
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

database_path = "user_clicks.json"
sports_ids = get_all_sport_ids(api, base_id)
locations_ids = get_all_location_ids(api, base_id)

recommender = Recommender(database_path, sports_ids, locations_ids)
click_tracker = ClickTracker(database_path)

app = FastAPI(title="AlterSport API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuizInit(BaseModel):
   user_id: Optional[str] = None
   user_name: Optional[str] = None
   age: Optional[str] = None 
   city: Optional[str] = None
   district: Optional[str] = None
   sport_type_preference: Optional[str] = None
   sport_interests: Optional[List[str]] = None
   event_type_priority: Optional[List[str]] = None
   personal_usage: Optional[str] = None

class UserUpdate(BaseModel):
   user_name: Optional[str] = None
   age: Optional[str] = None
   city: Optional[str] = None
   district: Optional[str] = None
   sport_interests: Optional[List[str]] = None
   event_type_priority: Optional[List[str]] = None

class DateRangeRequest(BaseModel):
   start_date: str
   end_date: str
   sport_id: Optional[str] = None
   location_id: Optional[str] = None
   team_id: Optional[str] = None
   limit: Optional[int] = 10
    
def get_user_or_error(user_id: str):
   """Get user or raise exception if not found"""
   user = click_tracker.get_user(user_id)
   if not user:
      raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
   return user

@app.post("/api/users/initialize/{user_id}")
async def initialize_user(user_id):
   if user_id is None:
      user_id = f"user_{int(datetime.now().timestamp())}"
   try:
      user = click_tracker.initialize_user(user_id)
      return {"user_id": user_id, "profile": user}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e)) 
   

@app.post("/api/users/update/{user_data}")
async def update_user(user_data: UserQuizInit):
   data_dict = user_data.dict()
   user_id = data_dict.get("user_id")
   try:
      user = click_tracker.update_user(user_id, data_dict)
      return {"user_id": user_id, "profile": user}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e)) 
   
@app.get("/api/users/{user_id}")
async def get_user_profile(user_id: str):
   user = get_user_or_error(user_id)
   return {"user_id": user_id, "profile": user}

@app.put("/api/users/{user_id}")
async def update_user_profile(user_id: str, user_data: UserUpdate):
   try:
      updated_user = click_tracker.set_user_stats(user_id, user_data.dict())
      return {"user_id": user_id, "profile": updated_user}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.post("/api/track/{user_id}/event/{event_id}")
async def track_event_click(user_id: str, event_id: str):
   try:
      result = click_tracker.track_event_click(user_id, event_id)
      if result:
         return {"status": "success", "data": result}
      raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found")
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.post("/api/track/{user_id}/team/{team_id}")
async def track_team_click(user_id: str, team_id: str):
   try:
      result = click_tracker.track_team_click(user_id, team_id)
      if result:
         return {"status": "success", "data": result}
      raise HTTPException(status_code=404, detail=f"Team with ID {team_id} not found")
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/track/{user_id}/sport/{sport_id}")
async def track_sport_click(user_id: str, sport_id: str):
   try:
      result = click_tracker.track_sport_click(user_id, sport_id)
      if result:
         return {"status": "success", "data": result}
      raise HTTPException(status_code=404, detail=f"Sport with ID {sport_id} not found")
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.post("/api/track/{user_id}/tournament/{tournament_id}")
async def track_tournament_click(user_id: str, tournament_id: str):
   try:
      result = click_tracker.track_tournament_click(user_id, tournament_id)
      if result:
         return {"status": "success", "data": result}
      raise HTTPException(status_code=404, detail=f"Tournament with ID {tournament_id} not found")
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/recommend/{user_id}/homepage")
async def get_homepage_recommendations(user_id: str, limit: int = 10):
   get_user_or_error(user_id)
   try:
      recommendations = recommender.get_homepage_recommendations(user_id, limit)
      return {"user_id": user_id, "recommendations": recommendations}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/recommend/{user_id}/sport/{sport_id}")
async def get_sport_recommendations(user_id: str, sport_id: str, limit: int = 5):
   get_user_or_error(user_id)
   try:
      recommendations = recommender.get_sport_recommendations(user_id, sport_id, limit)
      return {"user_id": user_id, "sport_id": sport_id, "recommendations": recommendations}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommend/{user_id}/events")
async def get_event_recommendations(user_id: str, limit: int = 5):
   get_user_or_error(user_id)
   try:
      recommendations = recommender.get_event_recommendations(user_id, limit)
      return {"user_id": user_id, "recommendations": recommendations}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/recommend/{user_id}/tournaments")
async def get_tournament_recommendations(user_id: str, limit: int = 5):
   get_user_or_error(user_id)
   try:
      recommendations = recommender.get_tournament_recommendations(user_id, limit)
      return {"user_id": user_id, "recommendations": recommendations}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/recommend/{user_id}/favorites")
async def get_user_favorites(user_id: str, limit: int = 5):
   get_user_or_error(user_id)
   try:
      favorites = recommender.get_user_favorites(user_id, limit)
      return {"user_id": user_id, "favorites": favorites}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommend/{user_id}/matches")
async def get_real_time_match_recommendations(user_id: str, limit: int = 5):
   get_user_or_error(user_id)
   try:
      matches = recommender.get_real_time_match_recommendations(user_id, limit)
      return {"user_id": user_id, "matches": matches}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.post("/api/events/date-range")
async def get_events_by_dates(request: DateRangeRequest):
   try:
      events = get_events_by_date_range(
         api,
         base_id,
         request.start_date,
         request.end_date,
         sport_id=request.sport_id,
         location_id=request.location_id,
         team_id=request.team_id
      )
      return {"events": events[:request.limit]}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/sports")
async def get_sports():
   """Get all available sports"""
   try:
      sports = list_sport_records(api, base_id)
      return {"sports": sports}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/teams")
async def get_teams():
   """Get all available teams"""
   try:
      teams = list_teams_records(api, base_id)
      return {"teams": teams}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations")
async def get_locations():
   """Get all available locations"""
   try:
      locations = list_locations_records(api, base_id)
      return {"locations": locations}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/events")
async def get_events(days_ahead: int = 7):
   """Get upcoming events for the next X days"""
   try:
      today = datetime.now().date()
      end_date = today + timedelta(days=days_ahead)
      events = get_events_by_date_range(api, base_id, today.isoformat(), end_date.isoformat())
      return {"events": events}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   
@app.get("/api/get_user_clicks")
async def get_user_clicks():
   """Get all clicks for a user"""
   try:
      database = click_tracker.get_db()
      return {"database" : database}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
   return {"status": "healthy", "sports_count": len(sports_ids), "locations_count": len(locations_ids)}

if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=8888)