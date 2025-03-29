import requests
import time
import sys
import json

def test_api_endpoints(base_url="http://localhost:8000"):
    """
    Simple integration test to verify essential API endpoints are working.
    Run this after starting the API server.
    """
    print(f"Testing API at {base_url}...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("✅ Health check endpoint working")
        else:
            print(f"❌ Health check failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error accessing health endpoint: {str(e)}")
        return False
    
    # Test creating a task
    try:
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "duration": 60,
            "energy_cost": 5,
            "category": "WORK",
            "priority": 3,
            "dependencies": []
        }
        
        response = requests.post(f"{base_url}/tasks/", json=task_data)
        if response.status_code in (200, 201):
            task_id = response.json().get("id")
            print(f"✅ Created task with ID: {task_id}")
        else:
            print(f"❌ Task creation failed: {response.status_code}, {response.text}")
            return False
            
        # Test getting the created task
        response = requests.get(f"{base_url}/tasks/{task_id}")
        if response.status_code == 200:
            print("✅ Retrieved task successfully")
        else:
            print(f"❌ Task retrieval failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error with tasks endpoints: {str(e)}")
        return False
    
    # Test creating an objective
    try:
        objective_data = {
            "name": "Test Objective",
            "category": "WORK",
            "target_value": 10.0,
            "weight": 0.5,
            "measurement_unit": "hours",
            "time_frame": "WEEKLY",
            "current_value": 0.0
        }
        
        response = requests.post(f"{base_url}/objectives/", json=objective_data)
        if response.status_code in (200, 201):
            objective_id = response.json().get("id")
            print(f"✅ Created objective with ID: {objective_id}")
        else:
            print(f"❌ Objective creation failed: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error with objectives endpoints: {str(e)}")
        return False
    
    print("\n✅ All basic API tests passed!")
    return True

if __name__ == "__main__":
    # Allow passing a different base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Wait for server to start up if needed
    print("Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    success = test_api_endpoints(base_url)
    if not success:
        sys.exit(1)  # Return non-zero exit code if tests failed