import json
import os

def get_sensor_data(file_path="wokwi_mock.json"):
    """
    Reads sensor data from a local JSON file (simulating Wokwi mock data).
    If the file doesn't exist or is invalid, returns default optimal values.
    
    Returns:
        dict: Sensor data containing humidity, temperature, and solar_radiation.
    """
    default_values = {
        "humidity": 65.5,
        "temperature": 28.2
    }
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure we have the required keys by merging with defaults
                for key in default_values.keys():
                    if key in data:
                        default_values[key] = data[key]
        except json.JSONDecodeError:
            print(f"Error: {file_path} contains invalid JSON. Using default values.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}. Using default values.")
    else:
        print(f"Warning: {file_path} not found. Using default optimal values.")
        
    return default_values

