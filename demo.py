import os
import time
import random
from click_tracker import ClickTracker
from API import *

def generate_random_users(number_of_users=10):
    """Generate multiple random users for demo purposes"""
    
    # Initialize the tracker
    tracker = ClickTracker(database_path='user_clicks.json')
    
    # First names and last names for random generation
    first_names = ["Ana", "Ivan", "Marija", "Luka", "Nina", "Ante", "Petra", "Tomislav", "Ivana", "Mateo",
                  "Katarina", "Josip", "Maja", "Nikola", "Iva"]
    
    last_names = ["Horvat", "Kovačić", "Babić", "Marić", "Novak", "Jurić", "Vuković", "Knežević", "Pavić", "Petrović"]
    
    # Districts in Zagreb
    districts = ["Knežija", "Trešnjevka", "Trnje", "Dubrava", "Jarun", "Špansko", "Maksimir", "Črnomerec", "Savica", "Vrapče"]
    
    # Sport IDs for interests and training
    sport_ids = ["recGfphnFce1DEBhE", "recUmMssS0H4uzmgT", "recj8YX9QFNCQitNX"]
    
    # Cities
    cities = ["Zagreb", "Split", "Rijeka", "Osijek", "Zadar", "Pula"]
    
    user_ids = []
    
    print(f"Generating {number_of_users} random users...")
    
    for i in range(number_of_users):
        # Create a unique user ID
        user_id = f"demo_user_{int(time.time())}_{i}"
        
        # Generate random user data
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        # Randomize data
        user_data = {
            "user_name": full_name,
            "age": random.randint(18, 65),
            "city": random.choice(cities),
            "district": random.choice(districts),
            "sport_trained": random.choice(sport_ids),
            "sport_interests": random.sample(sport_ids, random.randint(1, len(sport_ids))),
            "personal_usage": random.choice(["yes", "no"]),
            "event_type_priority": random.choice([["match", "tournament"], ["tournament", "match"]])
        }
        
        # Initialize user
        user = tracker.initialize_user(user_id, user_data)
        print(f"Created user {i+1}/{number_of_users}: {user['user_name']} (ID: {user_id})")
        
        user_ids.append(user_id)
        
        # Simulate some activity for each user
        simulate_user_activity(tracker, user_id)
        
    print(f"\nSuccessfully generated {number_of_users} random users!")
    return user_ids

def simulate_user_activity(tracker, user_id):
    """Simulate random user activity for more realistic data"""
    
    # Randomize number of interactions per user
    num_sport_clicks = random.randint(1, 5)
    num_team_clicks = random.randint(1, 4)
    num_event_clicks = random.randint(0, 3)
    num_tournament_clicks = random.randint(0, 2)
    
    # Get data from Airtable
    try:
        # Sports
        all_sports = list_sport_records(api, base_id)
        if all_sports:
            sample_sports = random.sample(all_sports, min(num_sport_clicks, len(all_sports)))
            for sport in sample_sports:
                tracker.track_sport_click(user_id, sport.get('id'))
        
        # Teams
        all_teams = list_teams_records(api, base_id)
        if all_teams:
            sample_teams = random.sample(all_teams, min(num_team_clicks, len(all_teams)))
            for team in sample_teams:
                tracker.track_team_click(user_id, team.get('id'))
        
        # Events
        all_events = list_events_records(api, base_id)
        if all_events:
            sample_events = random.sample(all_events, min(num_event_clicks, len(all_events)))
            for event in sample_events:
                tracker.track_event_click(user_id, event.get('id'))
        
        # Tournaments
        all_tournaments = list_tournaments_records(api, base_id)
        if all_tournaments:
            sample_tournaments = random.sample(all_tournaments, min(num_tournament_clicks, len(all_tournaments)))
            for tournament in sample_tournaments:
                tracker.track_tournament_click(user_id, tournament.get('id'))
    except Exception as e:
        print(f"Error while simulating activity: {str(e)}")

def run_complete_demo():
    """Original complete demo showing all click tracking features"""
    
    # Initialize the tracker
    tracker = ClickTracker(database_path='user_clicks.json')
    
    # Create a new user for this demo
    user_id = "demo_user_" + str(int(time.time()))
    user_data = {
        "user_name": "Demo User",
        "age": 30,
        "city": "Zagreb",
        "district": "Knežija",
        "sport_trained": "recGfphnFce1DEBhE",
        "sport_interests": ["recGfphnFce1DEBhE",
                  "recUmMssS0H4uzmgT",
                  "recj8YX9QFNCQitNX"],
        "personal_usage": "yes"
    }
    
    # Initialize user
    user = tracker.initialize_user(user_id, user_data)
    print(f"Created demo user: {user['user_name']} (ID: {user_id})")
    
    # -------------------- SPORTS DEMO --------------------
    print("\n--- SPORTS DEMO ---")
    
    # Track clicks on sports
    sport_ids = ["recGfphnFce1DEBhE", "recUmMssS0H4uzmgT", "recj8YX9QFNCQitNX"]
    
    for sport_id in sport_ids:
        result = tracker.track_sport_click(user_id, sport_id)
        if result:
            print(f"Tracked click on sport: {result['sport_name']}")
    
    # -------------------- TEAMS DEMO --------------------
    print("\n--- TEAMS DEMO ---")
    
    # Get real teams from Airtable
    all_teams = list_teams_records(api, base_id)
    sample_teams = all_teams[:2] if len(all_teams) >= 2 else all_teams
    
    for team in sample_teams:
        team_id = team.get('id')
        result = tracker.track_team_click(user_id, team_id)
        if result:
            print(f"Tracked click on team: {result['team_name']}")
    
    # -------------------- EVENTS DEMO --------------------
    print("\n--- EVENTS DEMO ---")
    
    # Get real events from Airtable
    all_events = list_events_records(api, base_id)
    sample_events = all_events[:2] if len(all_events) >= 2 else all_events
    
    for event in sample_events:
        event_id = event.get('id')
        result = tracker.track_event_click(user_id, event_id)
        if result:
            print(f"Tracked click on event: {result['home_team']} vs {result['away_team']}")
    
    # -------------------- TOURNAMENTS DEMO --------------------
    print("\n--- TOURNAMENTS DEMO ---")
    
    # Get real tournaments from Airtable
    all_tournaments = list_tournaments_records(api, base_id)
    sample_tournaments = all_tournaments[:1] if all_tournaments else []
    
    for tournament in sample_tournaments:
        tournament_id = tournament.get('id')
        result = tracker.track_tournament_click(user_id, tournament_id)
        if result:
            print(f"Tracked click on tournament: {result['tournament_name']}")
    
    # -------------------- USER STATS --------------------
    print("\n--- USER STATS AFTER CLICKS ---")
    
    stats = tracker.get_user_stats(user_id)
    print(f"• Total events clicked: {stats['total_events_clicked']}")
    print(f"• Favorite sports: {[s[0] for s in stats['favorite_sports']]}")
    print(f"• Favorite teams: {stats['favorite_teams']}")
    print(f"• Sport interests: {stats['sport_interests']}")
    
    print("\nDemo completed successfully!")
    return user_id

if __name__ == "__main__":
    # Choose which demo to run
    run_random_users = True  # Set to False to run the original demo
    
    if run_random_users:
        user_ids = generate_random_users(10)  # Generate 10 random users
        print(f"\nGenerated {len(user_ids)} random users in your user_clicks.json file.")
    else:
        user_id = run_complete_demo()
        print(f"\nYou can check the demo user with ID: {user_id} in your user_clicks.json file.")