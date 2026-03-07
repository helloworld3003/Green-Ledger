from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from video_processing import analyze_farm_video
from sensor_ingestion import get_sensor_data
from carbon_engine import calculate_carbon_credits
import glob
import os
import json
import asyncio
import re
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FARM_NAME = "Green Valley Carbon Farm"
DATA_FILE = os.path.join(BASE_DIR, "api_data.json")

clients_event = asyncio.Event()

def save_to_history(payload):
    history = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                history = json.load(f)
            except:
                pass
    date = payload.get("date")
    # avoid duplicates
    history = [h for h in history if h.get("date") != date]
    history.append(payload)
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=4)

async def watch_folder():
    # regex matches: test_YYYY-MM-DD.mp4 or test_YYYY-M-D.mp4
    valid_pattern = re.compile(r"^test_(\d{4}-\d{1,2}-\d{1,2})\.mp4$")
    
    def get_valid_videos():
        all_videos = glob.glob(os.path.join(BASE_DIR, "test_*.mp4"))
        return set([v for v in all_videos if valid_pattern.match(os.path.basename(v))])
        
    known_videos = get_valid_videos()
    while True:
        await asyncio.sleep(2)
        current_videos = get_valid_videos()
        new_videos = current_videos - known_videos
        
        if new_videos:
            for nv in new_videos:
                match = valid_pattern.match(os.path.basename(nv))
                date = match.group(1) if match else "N/A"
                print(f"New video detected: {nv}, analyzing in background...")
                try:
                    await asyncio.to_thread(run_analysis_and_store, nv, date)
                except Exception as e:
                    print(f"Error analyzing {nv}: {e}")
            
            # Notify clients to reload page
            clients_event.set()
            await asyncio.sleep(0.1)
            clients_event.clear()
            
            known_videos = current_videos

def run_analysis_and_store(video_path, date):
    plant_count, health_index = analyze_farm_video(video_path, farm_area_polygon=None)
    sensor_data = get_sensor_data(os.path.join(BASE_DIR, "wokwi_mock.json"))
    carbon_results = calculate_carbon_credits(plant_count, sensor_data)
    total_co2_kg = carbon_results.get("co2_credits", 0.0)
    credits_generated = total_co2_kg / 1000.0
    
    response_payload = {
        "status": "success",
        "farm_name": FARM_NAME,
        "date": date,
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
    save_to_history(response_payload)
    return response_payload

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
    videos = glob.glob(os.path.join(BASE_DIR, "test_*.mp4"))
    dates = []
    valid_pattern = re.compile(r"^test_(\d{4}-\d{1,2}-\d{1,2})\.mp4$")
    for vp in videos:
        match = valid_pattern.match(os.path.basename(vp))
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
    
    save_to_history(response_payload)
    
    return response_payload

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(watch_folder())

@app.get("/api/v1/history")
async def get_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

async def event_generator(request: Request):
    while True:
        if await request.is_disconnected():
            break
        await clients_event.wait()
        yield "data: reload\n\n"

@app.get("/api/v1/stream")
async def stream(request: Request):
    return StreamingResponse(event_generator(request), media_type="text/event-stream")

@app.get("/api/v1/weather")
async def get_weather(lat: float = 22.5004, lon: float = 88.3709):
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
