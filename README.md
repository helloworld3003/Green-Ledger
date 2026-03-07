# 🌿 The Green Ledger
**Empowering Small-Scale Farmers for the Global Carbon Economy**

**Team:** DataGeeks (Jadavpur University)
**Track:** Green Technology



## 🌍 Introduction & Vision
Indian farmers often face severe economic challenges. However, with the recent boom in the global carbon credit exchange ecosystem, these farmers have a massive, untapped opportunity to leverage their farms' CO2 capturing capabilities. The barrier? The traditional verification process is overly complex, manual, and prohibitively expensive for small-scale agriculture.

**Our Vision:** We replace expensive human auditors with a "Phygital" (Physical + Digital) verification node. By erecting a single pole in the middle of a farm equipped with a 360-degree panoramic camera and basic environmental sensors (temperature/humidity), we can gather raw, localized data. This data is autonomously processed via our Python Computer Vision and AI pipeline to calculate, verify, and mint carbon credits with zero friction.

---

## 🛠️ The Architecture & Codebase
Our system is driven by a lightweight, modular Python backend and a zero-build React frontend.

### 1. `carbon_engine.py`
* **Summary:** The core math engine. Calculates estimated biomass, carbon sequestered, and CO2 credits based on plant counts and sensor data.
* **USP (Environmental Penalty Logic):** Acts as a smart contract valuer. It dynamically penalizes the farm's "Consistency Score" if the temperature spikes (>35°C) or humidity drops (<40%), ensuring credits reflect true crop conditions.

### 2. `video_processing.py`
* **Summary:** Processes `.mp4` farm videos using OpenCV at 1 FPS. Applies ROI (Region of Interest) masks, converts frames to HSV to isolate green plant clusters, and counts contours to calculate average plant numbers and crop health.
* **USP (RGB-based NDVI):** Simulates an NDVI (Normalized Difference Vegetation Index) using standard RGB/HSV video inputs, completely removing the need for expensive multispectral cameras.

### 3. `sensor_ingestion.py`
* **Summary:** Reads local hardware sensor data from a mock JSON file to provide real-time temperature and humidity metrics.
* **USP (Fault Tolerance):** Built-in redundancy. It automatically falls back to default optimal values if the external IoT JSON file is missing or corrupted, ensuring the main pipeline never crashes due to hardware failure.

### 4. `main.py`
* **Summary:** The FastAPI orchestrator. Exposes endpoints to run farm analysis, fetch real-time weather from Open-Meteo, and provides the complete API backend.
* **USP (Event-Driven Automation):** Uses an asynchronous background directory watcher combined with Server-Sent Events (SSE). Dropping a new video into the folder automatically triggers background analysis and pushes a real-time update event to all connected frontend clients.

### 5. `api_data.json` & `wokwi_mock.json`
* **`api_data.json` (The Green Ledger):** A local JSON storage file tracking the history of all processed dates, farm metrics, and calculated carbon credits. It functions as a lightweight, persistent history of verified metrics without the overhead of a full database.
* **`wokwi_mock.json`:** A simple flat mock file containing simulated IoT hardware sensor outputs. Its easily modifiable structure allows for rapid end-to-end testing of environmental edge cases.

### 6. `green_ledger.html`
* **Summary:** A full single-page React application running natively within the HTML file (via Babel standalone). The UI is split into two primary portals:
  * **Farmer Dashboard:** Allows farmers to view environmental metrics and carbon credits. Includes a hardware simulation toggle for testing different dates (`test_{date}.mp4`) and provides a visual breakdown of how carbon credits are calculated from total biomass.
  * **Trader Marketplace:** Simulates a carbon credit exchange where traders can purchase verified GreenCredit Tokens (GCT) with mock transaction hashing (simulating Polygon Amoy testnet).
* **API Integration:** Dynamically connects to the FastAPI backend to fetch available dates, load history, trigger the Python analytics pipeline on-demand, display Open-Meteo alerts, and subscribe to Server-Sent Events (SSE) for auto-reloading.
* **USP (Zero-Build SVG Analytics):** Features a zero-build React architecture using pure native SVG to render complex charts (Line, Area, Health Rings) without bloated external dependencies. The UI features glassmorphism, CSS animations, and a real-time SSE loop.

---

## 🚀 Hackathon Implementation Notes
To deliver a working prototype within the 36-hour time limit, we utilized the following tools and workarounds:
* **Demo Data:** We generated photorealistic panoramic videos of cabbage and mustard farms using the **Veo 3** AI video model to feed our OpenCV pipeline.
* **Simulated Hardware:** IoT sensor data was mocked using Wokwi JSON outputs.
* **Web3 Simulation:** Polygon Amoy testnet transactions were simulated via mock transaction hashing on the frontend.
* **Deployment:** We used `localtunnel` to create a temporary public server for our local FastAPI workspace, while the frontend UI was deployed seamlessly via Netlify.

---

## 👨‍💻 Team DataGeeks & Contributions

| Name | Role | Core Contributions | Tools Used |
| :--- | :--- | :--- | :--- |
| **Tapomoy Sarkar** | Team Leader & AI Lead | Engineered the core Python logic, OpenCV video processing pipeline, FastAPI architecture, and mock data generation. | VSCode, Python, OpenCV 3, FastAPI |
| **Dibyajyoti Ganguly** | Backend Integration | Handled dynamic FastAPI integration, backend routing, and CSS styling architecture. | Node.js, CSS, Cursor |
| **Krishnendu Koley** | Frontend UI/UX | "Vibe Coded" the entire zero-build React frontend, SVG charts, and dashboard layouts. | HTML/JS, Claude, Antigravity |
| **Rahin Anushah** | Data & Testing | Engineered the Veo 3 prompts to gather perfect test data and assisted with end-to-end QA testing. | Veo 3, Prompt Engineering |
