import requests
import json
from datetime import datetime, timedelta
import random
import time
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8888/api"  # Change if your server runs on a different port
HEADERS = {"Content-Type": "application/json"}
DEBUG = False  # Set to True to see detailed error information

def print_separator(title):
    """Print a separator line with title for better readability"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def debug_log(message, data=None):
    """Log debug information if DEBUG is enabled"""
    if DEBUG:
        print(f"DEBUG: {message}")
        if data:
            try:
                if isinstance(data, dict) or isinstance(data, list):
                    print(json.dumps(data, indent=2))
                else:
                    print(data)
            except:
                print(f"Could not print data: {type(data)}")
        print()

def create_user():
    """Create a test user and return the user_id"""
    first_names = ["Ana", "Ivan", "Marija", "Luka", "Nina", "Ante", "Petra", "Tomislav"]
    last_names = ["Horvat", "Kovačić", "Babić", "Marić", "Novak", "Jurić", "Vuković"]
    districts = ["Knežija", "Trešnjevka", "Trnje", "Dubrava", "Jarun", "Špansko", "Maksimir"]
    cities = ["Zagreb", "Split", "Rijeka", "Osijek", "Zadar"]
    sport_ids = ["recGfphnFce1DEBhE", "recGfphnFce1DEBhE", "recGfphnFce1DEBhE", 
                "recGfphnFce1DEBhE", "recGfphnFce1DEBhE"]
    
    _user_id = f"{random.choice(first_names)} {random.choice(last_names)}"
    user_data = {
        "user_id" : _user_id,
        "user_name": _user_id,
        "age": str(random.randint(18, 65)),
        "city": random.choice(cities).lower(),
        "district": random.choice(districts).lower(),
        "sport_interests": random.sample(sport_ids, random.randint(1, len(sport_ids))),
        "event_type_priority": random.choice([["match", "tournament"], ["tournament", "match"]]),
        "personal_usage": random.choice(["yes", "no"])
    }
    
    print_separator("CREATING NEW USER")
    print(f"Creating user: {user_data['user_name']} from {user_data['city']}")
    debug_log("User data:", user_data)
    
    try:
        response = requests.post(f"{BASE_URL}/users/initialize/{_user_id}", json=user_data, headers=HEADERS)
        response.raise_for_status()
        result = response.json()
        user_id = result["user_id"]
        print(f"User created successfully with ID: {user_id}")
        return user_id
    except requests.exceptions.HTTPError as e:
        print(f"Failed to create user: {e}")
        debug_log("Response body:", response.text)
        return None
    except Exception as e:
        print(f"Unexpected error creating user: {e}")
        return None

def simulate_user_activity(user_id):
    """Simulate user activity by tracking clicks on sports, teams, events, and tournaments"""
    print_separator("SIMULATING USER ACTIVITY")
    
    # Get available data with error handling
    sports = []
    teams = []
    events = []
    
    # Fetch sports
    print("Fetching available sports...")
    try:
        response = requests.get(f"{BASE_URL}/sports", headers=HEADERS)
        response.raise_for_status()
        sports_data = response.json()["sports"]
        sports = [sport["id"] for sport in sports_data]
        debug_log(f"Retrieved {len(sports)} sports")
    except Exception as e:
        print(f"Failed to get sports: {e}")
    
    # Fetch teams
    print("Fetching available teams...")
    try:
        response = requests.get(f"{BASE_URL}/teams", headers=HEADERS)
        response.raise_for_status()
        teams_data = response.json()["teams"]
        teams = ["recbBO2dEP83DqOuF" for team in teams_data]
        debug_log(f"Retrieved {len(teams)} teams")
    except Exception as e:
        print(f"Failed to get teams: {e}")
    
    # Fetch events
    print("Fetching available events...")
    try:
        response = requests.get(f"{BASE_URL}/events", headers=HEADERS)
        response.raise_for_status()
        events_data = response.json()["events"]
        events = [event["id"] for event in events_data if "id" in event]
        debug_log(f"Retrieved {len(events)} events")
    except Exception as e:
        print(f"Failed to get events: {e}")
    
    # Simulate clicks with better error handling
    print("\nSimulating clicks:")
    
    # Track clicks on sports (1-3 sports)
    num_sport_clicks = min(random.randint(1, 3), len(sports))
    for _ in range(num_sport_clicks):
        if sports:
            sport_id = random.choice(sports)
            sport_id  = 'recGfphnFce1DEBhE'
            print(f"  • Clicking on sport: {sport_id}")
            try:
                response = requests.post(f"{BASE_URL}/track/{user_id}/sport/{sport_id}", headers=HEADERS)
                response.raise_for_status()
                print(f"    Success: {response.json()['data']['sport_name']}")
            except requests.exceptions.HTTPError as e:
                print(f"    Failed: {response.status_code}")
                debug_log(f"Error response: {response.text}")
            except Exception as e:
                print(f"    Failed: {str(e)}")
            time.sleep(0.5)  # Small delay to avoid overwhelming the server
    
    # Track clicks on teams (2-5 teams)
    num_team_clicks = min(random.randint(2, 5), len(teams))
    for _ in range(num_team_clicks):
        if teams:
            team_id = random.choice(teams)
            team_id = 'recbBO2dEP83DqOuF'
            print(f"  • Clicking on team: {team_id}")
            try:
                response = requests.post(f"{BASE_URL}/track/{user_id}/team/{team_id}", headers=HEADERS)
                response.raise_for_status()
                print(f"    Success: {response.json()['data']['team_name']}")
            except requests.exceptions.HTTPError as e:
                print(f"    Failed: {response.status_code}")
                debug_log(f"Error response: {response.text}")
            except Exception as e:
                print(f"    Failed: {str(e)}")
            time.sleep(0.5)
    
    # Track clicks on events (1-2 events)
    num_event_clicks = min(random.randint(1, 2), len(events))
    for _ in range(num_event_clicks):
        if events:
            event_id = random.choice(events)
            print(f"  • Clicking on event: {event_id}")
            try:
                response = requests.post(f"{BASE_URL}/track/{user_id}/event/{event_id}", headers=HEADERS)
                response.raise_for_status()
                event_data = response.json()['data']
                print(f"    Success: {event_data.get('home_team', '')} vs {event_data.get('away_team', '')}")
            except requests.exceptions.HTTPError as e:
                print(f"    Failed: {response.status_code}")
                debug_log(f"Error response: {response.text}")
            except Exception as e:
                print(f"    Failed: {str(e)}")
            time.sleep(0.5)
    
    # Get user stats after activity
    print("\nGetting user statistics after activity:")
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
        response.raise_for_status()
        user_data = response.json()["profile"]
        if "sports_clicked" in user_data:
            print(f"  • Sports clicked: {len(user_data['sports_clicked'])}")
        if "teams_clicked" in user_data:
            print(f"  • Teams clicked: {len(user_data['teams_clicked'])}")
        if "events_clicked" in user_data:
            print(f"  • Events clicked: {len(user_data['events_clicked'])}")
        debug_log("Full user data:", user_data)
    except Exception as e:
        print(f"Failed to get user stats: {e}")

def get_recommendations(user_id):
    """Get recommendations for the user"""
    print_separator("GETTING RECOMMENDATIONS")
    
    # Get homepage recommendations
    print("Getting homepage recommendations...")
    try:
        print(f"User ID: {user_id}")
        print(f"{BASE_URL}/recommend/{user_id}/homepage")
        response = requests.get(f"{BASE_URL}/recommend/{user_id}/homepage", headers=HEADERS)
        response.raise_for_status()
        recommendations = response.json()["recommendations"]
        print("Homepage recommendations:")
        if "favorite_sports" in recommendations:
            print(f"  • Favorite sports: {len(recommendations['favorite_sports'])}")
        if "upcoming_events" in recommendations:
            print(f"  • Upcoming events: {len(recommendations['upcoming_events'])}")
        if "recommended_teams" in recommendations:
            print(f"  • Recommended teams: {len(recommendations['recommended_teams'])}")
        debug_log("Full homepage recommendations:", recommendations)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get homepage recommendations: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to get homepage recommendations: {e}")
    
    # Get event recommendations
    print("\nGetting event recommendations...")
    try:
        response = requests.get(f"{BASE_URL}/recommend/{user_id}/events", headers=HEADERS)
        response.raise_for_status()
        recommendations = response.json()["recommendations"]
        if "recommended_events" in recommendations:
            events = recommendations["recommended_events"]
            print(f"Found {len(events)} recommended events")
            
            # Show sample of events if available
            if events:
                print("\nSample events:")
                for event in events[:3]:
                    if "home_team" in event and "away_team" in event:
                        print(f"  • {event['home_team']} vs {event['away_team']} ({event.get('event_date', 'No date')})")
                    elif "tournament_name" in event:
                        print(f"  • Tournament: {event['tournament_name']} ({event.get('start_date', 'No date')})")
            debug_log("Full event recommendations:", recommendations)
        else:
            print("No recommended events found")
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get event recommendations: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to get event recommendations: {e}")
    
    # Try to get matches directly as an alternative 
    print("\nTrying direct event search as fallback...")
    try:
        response = requests.get(f"{BASE_URL}/events?days_ahead=14", headers=HEADERS)
        response.raise_for_status()
        events = response.json()["events"]
        print(f"Found {len(events)} events in the next 14 days")
        if events:
            print("\nSample upcoming events:")
            for event in events[:3]:
                fields = event.get('fields', {})
                print(f"  • {fields.get('Match Date', 'No date')}: Event ID {event.get('id', 'unknown')}")
    except Exception as e:
        print(f"Failed to get direct events: {e}")
    
    # Get matches in real-time
    print("\nGetting real-time match recommendations...")
    try:
        response = requests.get(f"{BASE_URL}/recommend/{user_id}/matches", headers=HEADERS)
        response.raise_for_status()
        matches = response.json()["matches"]
        print(f"Found {len(matches)} real-time match recommendations")
        
        # Show sample of matches if available
        if matches:
            print("\nSample matches:")
            for match in matches[:3]:
                print(f"  • {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')} ({match.get('event_date', 'No date')})")
            debug_log("Full match recommendations:", matches)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to get real-time matches: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to get real-time matches: {e}")

def find_events_by_date_range():
    """Find events in specific date ranges"""
    print_separator("FINDING EVENTS BY DATE RANGE")
    
    # Find events in the next few days (using default endpoint)
    print("Finding events in the next 7 days...")
    try:
        response = requests.get(f"{BASE_URL}/events?days_ahead=7", headers=HEADERS)
        response.raise_for_status()
        events = response.json()["events"]
        print(f"Found {len(events)} events in the next 7 days")
        
        # Show sample of events if available
        if events:
            print("\nSample events:")
            for event in events[:3]:
                fields = event.get('fields', {})
                sport = fields.get('Sport', ['Unknown Sport'])[0] if isinstance(fields.get('Sport'), list) else fields.get('Sport', 'Unknown Sport')
                print(f"  • {fields.get('Match Date', 'No date')}: {sport}")
            debug_log("Event details example:", events[0] if events else None)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to find events: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to find events: {e}")
    
    # Find events in a specific date range
    print("\nFinding events between 29/05/2025 and 23/08/2025...")
    date_range_request = {
        "start_date": "2025-05-29",
        "end_date": "2025-08-23",
        "limit": 10
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events/date-range", json=date_range_request, headers=HEADERS)
        response.raise_for_status()
        events = response.json()["events"]
        print(f"Found {len(events)} events in the specified date range")
        
        # Show sample of events if available
        if events:
            print("\nSample events:")
            for event in events[:3]:
                fields = event.get('fields', {})
                sport = fields.get('Sport', ['Unknown Sport'])[0] if isinstance(fields.get('Sport'), list) else fields.get('Sport', 'Unknown Sport')
                date = fields.get('Match Date', 'No date')
                
                # Handle potentially missing team data
                try:
                    home_team = fields.get('Home Team', [''])[0] if fields.get('Home Team') else 'Unknown'
                    away_team = fields.get('Away Team', [''])[0] if fields.get('Away Team') else 'Unknown'
                    print(f"  • {date}: {home_team} vs {away_team} ({sport})")
                except (IndexError, TypeError):
                    print(f"  • {date}: Teams not available ({sport})")
            debug_log("Date range event details example:", events[0] if events else None)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to find events in date range: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to find events in date range: {e}")

def find_events_on_specific_date():
    """Find events on a specific date and compare with a date range"""
    print_separator("FINDING EVENTS ON SPECIFIC DATE VS DATE RANGE")
    
    print("Finding events on a specific date (5/10/2025)...")
    specific_date_request = {
        "start_date": "2025-05-10",
        "end_date": "2025-05-10",
        "limit": 10
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events/date-range", json=specific_date_request, headers=HEADERS)
        response.raise_for_status()
        events = response.json()["events"]
        print(f"Found {len(events)} events on 5/10/2025")
        
        # Show sample of events if available
        if events:
            print("\nSample events in date range:")
            for event in events[:3]:
                fields = event.get('fields', {})
                sport = fields.get('Sport', ['Unknown Sport'])[0] if isinstance(fields.get('Sport'), list) else fields.get('Sport', 'Unknown Sport')
                date = fields.get('Match Date', 'No date')
                
                # Handle potentially missing team data
                try:
                    home_team = fields.get('Home Team', [''])[0] if fields.get('Home Team') else 'Unknown'
                    away_team = fields.get('Away Team', [''])[0] if fields.get('Away Team') else 'Unknown'
                    print(f"  • {date}: {home_team} vs {away_team} ({sport})")
                except (IndexError, TypeError):
                    print(f"  • {date}: Teams not available ({sport})")
            debug_log("Date range event details example:", events[0] if events else None)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to find events in date range: {response.status_code}")
        debug_log(f"Error response: {response.text}")
    except Exception as e:
        print(f"Failed to find events in date range: {e}")
    
    # Test 2: Find events in a date range (5/10/2025 - 5/17/2025)
    print("\nFinding events in a date range (5/10/2025 - 5/17/2025)...")
    date_range_request = {
        "start_date": "2025-05-9",
        "end_date": "2025-05-11",
        "limit": 10
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events/date-range", json=date_range_request, headers=HEADERS)
        response.raise_for_status()
        events = response.json()["events"]
        print(f"Found {len(events)} events between 5/9/2025 and 5/11/2025")
        print(events)
        
        # Show sample of events if available
        if events:
            print("\nSample events in date range:")
            for event in events[:3]:
                fields = event.get('fields', {})
                sport = fields.get('Sport', ['Unknown Sport'])[0] if isinstance(fields.get('Sport'), list) else fields.get('Sport', 'Unknown Sport')
                date = fields.get('Match Date', 'No date')
                
                # Handle potentially missing team data
                try:
                    home_team = fields.get('Home Team', [''])[0] if fields.get('Home Team') else 'Unknown'
                    away_team = fields.get('Away Team', [''])[0] if fields.get('Away Team') else 'Unknown'
                    print(f"  • {date}: {home_team} vs {away_team} ({sport})")
                except (IndexError, TypeError):
                    print(f"  • {date}: Teams not available ({sport})")
    except Exception as e:
        print(f"Failed to find events in date range: {e}")
        
def test_user_update_after_wizard():
    """Test the update_after_wizard API endpoint with proper enum mapping"""
    print_separator("TESTING USER UPDATE AFTER WIZARD (FIXED VERSION)")
    
    # First create a basic user to work with
    user_id = create_user()
    if not user_id:
        print("Failed to create test user, skipping wizard update tests")
        return
    
    print("Testing update_after_wizard with different user profiles...")
    
    # Test Case 1: Group sport preference with tennis interests
    print("\nTest Case 1: Group sport preference with tennis interests")
    test_data_1 = {
        "user_name": f"{user_id}_updated",
        "age": "ADULTS",
        "group_style": "TEAM",  # This matches the actual enum
        "activities": ["RUNNING", "STRENGTH_AND_ENDURANCE"],
        "city": "zagreb",
        "district": "trnje",
        "sport_interests": ["recGfphnFce1DEBhE"],  # Tennis sport ID
        "event_type_priority": ["match", "tournament"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/update/{user_id}", json=test_data_1, headers=HEADERS)
        debug_log("Request payload (Test Case 1):", test_data_1)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Update successful")
        print(f"  • Recommended sport: {result.get('recommended_sport', 'None')}")
        print(f"  • Updated username: {result.get('user_profile', {}).get('user_name', 'None')}")
        debug_log("Full update response:", result)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Update failed with HTTP error: {e}")
        debug_log("Response body:", response.text)
    except Exception as e:
        print(f"✗ Unexpected error during update: {e}")
    
    # Test Case 2: Individual sport preference for seniors
    print("\nTest Case 2: Individual sport preference for seniors (with age mapping)")
    # SENIORS isn't a valid enum, it should be VETERANS
    test_data_2 = {
        "user_name": f"{user_id}_senior",
        "age": "VETERANS",  # Changed from SENIORS to match actual enum
        "group_style": "INDIVIDUAL",
        "activities": ["SWIMMING_AND_WATER", "STRATEGIC_PLANNING"],
        "city": "split"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/update/{user_id}", json=test_data_2, headers=HEADERS)
        debug_log("Request payload (Test Case 2):", test_data_2)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Update successful")
        print(f"  • Recommended sport: {result.get('recommended_sport', 'None')}")
        print(f"  • City: {result.get('user_profile', {}).get('city', 'None')}")
        debug_log("Full update response:", result)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Update failed with HTTP error: {e}")
        debug_log("Response body:", response.text)
    except Exception as e:
        print(f"✗ Unexpected error during update: {e}")
    
    # Test Case 3: Youth activities with minimal data
    print("\nTest Case 3: Youth activities with minimal data (with age mapping)")
    # YOUTH isn't a valid enum, it should be JUNIORS
    test_data_3 = {
        "user_name": f"{user_id}_youth",
        "age": "JUNIORS",  # Changed from YOUTH to match actual enum
        "group_style": "TEAM",
        "activities": ["OTHER"],
        "city": "osijek"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/update/{user_id}", json=test_data_3, headers=HEADERS)
        debug_log("Request payload (Test Case 3):", test_data_3)
        response.raise_for_status()
        result = response.json()
        print(f"✓ Update successful")
        print(f"  • Recommended sport: {result.get('recommended_sport', 'None')}")
        print(f"  • Age group: {result.get('user_profile', {}).get('age', 'None')}")
        debug_log("Full update response:", result)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Update failed with HTTP error: {e}")
        debug_log("Response body:", response.text)
    except Exception as e:
        print(f"✗ Unexpected error during update: {e}")
    
    # Get the user profile after all updates to verify changes were saved
    print("\nRetrieving final user profile after wizard updates:")
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
        response.raise_for_status()
        user_profile = response.json()["profile"]
        print(f"Final user profile:")
        print(f"  • Username: {user_profile.get('user_name', 'None')}")
        print(f"  • Age: {user_profile.get('age', 'None')}")
        print(f"  • Sport interests: {user_profile.get('sport_interests', 'None')}")
        print(f"  • City: {user_profile.get('city', 'None')}")
        debug_log("Complete final profile:", user_profile)
    except Exception as e:
        print(f"Failed to get final user profile: {e}")
        
def main():
    """Main function to execute the test script"""
    print("Starting Sport Recommendation API Test Script...")
    
    # Add command line arguments for debug mode
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        global DEBUG
        DEBUG = True
        print("Debug mode enabled")
    
    # Check if the API is alive
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        health_data = response.json()
        print("API is running!")
        print(f"Sports count: {health_data.get('sports_count', 'unknown')}")
        print(f"Locations count: {health_data.get('locations_count', 'unknown')}")
    except requests.exceptions.HTTPError as e:
        print(f"API health check failed: {e}")
        debug_log("Response:", response.text)
        return
    except requests.RequestException as e:
        print(f"Failed to connect to API: {e}")
        print(f"Make sure the server is running at {BASE_URL}")
        return
    
    # user_id = create_user()
    # if not user_id:
    #     return
    
    # simulate_user_activity(user_id)
    
    # get_recommendations(user_id)
    
    
    # find_events_on_specific_date()
    
    test_user_update_after_wizard()
    
    print("\nTest script completed successfully!")

if __name__ == "__main__":
    main()