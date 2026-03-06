from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from video_processing import analyze_farm_video, analyze_farm_period
from sensor_ingestion import get_sensor_data
from carbon_engine import calculate_carbon_credits
import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FARM_NAME = "Green Valley Carbon Farm"

# Initialize the FastAPI application
app = FastAPI(
    title="Carbon Credits Farm Analyzer API",
    description="API for analyzing farm video and sensor data to generate carbon credits.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/available-dates")
async def get_available_dates():
    """Returns a sorted list of dates extracted from the available test_*.mp4 videos."""
    import glob, re, os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    videos = glob.glob(os.path.join(BASE_DIR, "test_*.mp4"))
    dates = []
    for vp in videos:
        match = re.search(r"test_(.*)\.mp4", os.path.basename(vp))
        if match:
            dates.append(match.group(1))
    dates.sort()
    return {"status": "success", "dates": dates}

@app.get("/api/v1/analyze-farm")
async def analyze_farm(date: str = Query(None, description="Date of the video to analyze (e.g., '2023-10-01'). If omitted, finds the first available test video.")):
    """
    Executes the complete pipeline for a single farm/date:
    1. Analyzes farm video to get plant count and health index.
    2. Fetches sensor data (temperature, humidity, etc.).
    3. Calculates carbon footprint / credits.
    4. Returns a formatted JSON payload.
    """
    # 1. Execute video analysis
    if date:
        video_path = os.path.join(BASE_DIR, f"test_{date}.mp4")
    else:
        # Try finding the first 'test_<date>.mp4' if 'test.mp4' doesn't exist
        available_videos = glob.glob(os.path.join(BASE_DIR, "test_*.mp4"))
        video_path = available_videos[0] if available_videos else os.path.join(BASE_DIR, "test.mp4")
        
    import re
    match = re.search(r"test_(.*)\.mp4", video_path)
    processed_date = date if date else (match.group(1) if match else "N/A")
        
    # Use the entire frame to capture all plants
    plant_count, health_index = analyze_farm_video(video_path, farm_area_polygon=None)
    
    # 2. Fetch sensor data
    # Fetches from wokwi_mock.json if available, or uses default optimal values
    sensor_data = get_sensor_data(os.path.join(BASE_DIR, "wokwi_mock.json"))
    
    # 3. Run the carbon math
    carbon_results = calculate_carbon_credits(plant_count, sensor_data)
    
    # The carbon_engine's 'co2_credits' reflects kg of CO2 sequestered.
    total_co2_kg = carbon_results.get("co2_credits", 0.0)
    
    # Scale to typical carbon credits (Assuming 1 credit = 1 metric ton / 1000 kg)
    credits_generated = total_co2_kg / 1000.0
    
    # 4. Construct the required JSON payload structure
    response_payload = {
        "status": "success",
        "farm_name": FARM_NAME,
        "date": processed_date,
        "farm_metrics": {
            "plant_count": plant_count,
            "health_index": round(health_index, 2),
            "temperature": sensor_data.get("temperature", 0.0),
            "humidity": sensor_data.get("humidity", 0.0)
        },
        "carbon_data": {
            "total_co2_sequestered_kg": round(total_co2_kg, 1),
            "credits_generated": round(credits_generated, 2),
            "consistency_score": carbon_results.get("consistency_score", 0),
            "verified_by": "Virtual Satellite AI"
        }
    }
    
    return response_payload

@app.get("/api/v1/analyze-period")
async def analyze_period(directory: str = Query(None, description="Directory containing test_*.mp4 videos. If None, uses the app directory.")):
    """
    Executes the pipeline for a time period, reading videos named 'test_<date>.mp4'.
    Returns metrics and aggregated carbon credits for each date.
    """
    if not directory:
        directory = BASE_DIR
        
    # 1. Execute video analysis for the period using full frame to capture all plants
    period_results = analyze_farm_period(directory, farm_area_polygon=None)
    
    # 2. Fetch sensor data (using a single mocked file for now)
    sensor_data = get_sensor_data(os.path.join(BASE_DIR, "wokwi_mock.json"))
    
    response_payload = {
        "status": "success",
        "farm_name": FARM_NAME,
        "period_data": {}
    }
    
    total_period_credits = 0.0
    total_plants = 0
    total_health = 0.0
    
    for date_str, metrics in period_results.items():
        plant_count = metrics["plant_count"]
        health_index = metrics["health_index"]
        
        # 3. Run the carbon math for this date
        carbon_results = calculate_carbon_credits(plant_count, sensor_data)
        
        total_co2_kg = carbon_results.get("co2_credits", 0.0)
        credits_generated = total_co2_kg / 1000.0
        total_period_credits += credits_generated
        total_plants += plant_count
        total_health += health_index
        
        response_payload["period_data"][date_str] = {
            "farm_metrics": {
                "plant_count": plant_count,
                "health_index": round(health_index, 2),
                "temperature": sensor_data.get("temperature", 0.0),
                "humidity": sensor_data.get("humidity", 0.0)
            },
            "carbon_data": {
                "total_co2_sequestered_kg": round(total_co2_kg, 1),
                "credits_generated": round(credits_generated, 2),
                "consistency_score": carbon_results.get("consistency_score", 0)
            }
        }
        
    dates = list(period_results.keys())
    date_range = f"{dates[0]} to {dates[-1]}" if dates else "N/A"
    
    num_days = len(period_results)
    avg_plants = total_plants / num_days if num_days > 0 else 0
    avg_health = total_health / num_days if num_days > 0 else 0.0

    response_payload["summary"] = {
        "date_range": date_range,
        "analyzed_dates": dates,
        "total_credits_for_period": round(total_period_credits, 2),
        "average_plant_count": round(avg_plants),
        "average_health_index": round(avg_health, 2),
        "days_analyzed": num_days,
        "verified_by": "Virtual Satellite AI"
    }
    
    return response_payload

import urllib.request
import json

@app.get("/api/v1/weather")
async def get_weather(lat: float = 20.5937, lon: float = 78.9629):
    """Fetches real-time weather data from Open-Meteo API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
        
        current = data.get("current", {})
        temp = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        precip = current.get("precipitation", 0)

        alerts = []
        status = "OPTIMAL"

        if temp > 40:
            alerts.append("CRITICAL: Extreme heat detected. Increase irrigation immediately.")
            status = "CRITICAL"
        elif temp > 35:
            alerts.append("WARNING: High temperature. Monitor soil moisture.")
            if status != "CRITICAL": status = "WARNING"

        if humidity < 30:
            alerts.append("CRITICAL: Very low humidity. Crop stress risk is high.")
            status = "CRITICAL"
        elif humidity < 40:
            alerts.append("WARNING: Low humidity conditions.")
            if status != "CRITICAL": status = "WARNING"
            
        if wind > 40:
            alerts.append("CRITICAL: Gale force winds. Secure loose farm structures!")
            status = "CRITICAL"
        elif wind > 25:
            alerts.append("WARNING: High winds. Spraying operations not recommended.")
            if status != "CRITICAL": status = "WARNING"
            
        if precip > 20:
            alerts.append("CRITICAL: Heavy rainfall. Risk of waterlogging.")
            status = "CRITICAL"
        elif precip > 0:
            alerts.append("INFO: Light to moderate precipitation detected.")

        if not alerts:
            alerts.append("All climatic conditions are optimal for Agriculture.")

        return {
            "status": "success",
            "weather": {
                "temperature": temp,
                "humidity": humidity,
                "wind": wind,
                "precipitation": precip
            },
            "alerts_status": status,
            "alerts": alerts
        }
    except Exception as e:
        return {"status": "error", "message": f"Could not fetch weather data: {str(e)}"}

if __name__ == "__main__":
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
