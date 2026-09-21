# 🚴‍♂️ TriCoach AI - Intelligent Triathlon & Fitness Agent

![TriCoach AI Demo](demo.gif)

**TriCoach AI** is an intelligent multi-sport triathlon training assistant built with the **Google Agent Development Kit (ADK)** and deployed on **Vertex AI Agent Engine (Agent Runtime)**. It tracks athlete performance, calculates heart rate and power training zones, queries multi-sport workout catalogs, generates custom milestone artwork and training videos, and presents structured UI cards using A2UI.

---

## 🚀 Capabilities & Implemented Features

### 1. 🧠 Long-Term Memory (Vertex AI Memory Bank)
- Automatically retains athlete profile details, weight, resting/max heart rate, and training preferences across sessions via `PreloadMemoryTool` and durable session memory callbacks (`add_session_to_memory`).

### 2. 🗄️ Multi-Sport Workout Catalog & Activity Logging (Google Cloud Firestore)
- Queries structured multi-sport training routines (`workouts` collection) and logs completed athlete sessions (`workout_logs` collection).
- Tools: `get_workout_catalog`, `get_workout_detail`, `log_workout_activity`, `add_workout_to_catalog`.

### 3. 📚 Health & Botanical Knowledge Retrieval (Vertex AI RAG Engine)
- Answers queries grounded in health, nutritional, and athletic recovery literature using serverless RAG retrieval (`consult_rag_corpus`).

### 4. 🎨 Custom Fitness Badge Generation (Gemini 3.1 Flash Lite Image)
- Generates custom digital milestone artwork and finisher badges for completed workouts using `gemini-3.1-flash-lite-image` in the `global` region (`generate_workout_badge`).
- Uploads generated image assets to Google Cloud Storage (`tricoach-assets-44253ac8b396`) and renders them live inside A2UI card components.

### 5. 🎬 Training Video Generation (Gemini Omni Model)
- Generates 5-second instructional video clips for triathlon items using `gemini-omni-flash-preview` in the `global` region (`generate_workout_video`).
- Saves video artifacts directly to the Agent Engine Playground panel and uploads them to Google Cloud Storage.

### 6. 🧮 Math & Data Analysis Sandbox (Agent Engine Code Execution)
- Runs Python code in a isolated Cloud Sandbox (`AgentEngineSandboxCodeExecutor`) for pace splits, TSS estimation, and Karvonen heart rate training zone calculations (`calculate_heart_rate_zones`).

### 7. ⛅ Outdoor Training Weather Conditions (Open-Meteo Integration)
- Fetches real-time temperature, humidity, and wind speed assessment for outdoor cycling and running routes (`get_outdoor_training_conditions`).

### 8. 📱 Rich UI Cards (A2UI v0.8 Basic Catalog)
- Uses `A2uiSchemaManager` (v0.8) and `a2ui_callback` to emit native display cards (Card, Column, Row, Text, Image) for adk web and custom web frontends.

---

## 📁 Repository Structure

```
.
├── app/
│   ├── agent.py            # ADK root agent definition, model, and tool bindings
│   ├── a2ui_utils.py       # A2UI callback and surface renderer helpers
│   ├── firestore_tools.py  # Firestore database query & logging tools
│   ├── image_tools.py      # Gemini image generation & GCS upload tool
│   ├── video_tools.py      # Gemini Omni video generation tool
│   └── rag_tools.py        # Vertex AI RAG retrieval tool
├── frontend/
│   ├── main.py             # FastAPI proxy server (A2A protocol)
│   ├── requirements.txt    # Frontend dependencies
│   └── static/
│       └── index.html      # Custom web UI with A2UI renderer & prompt chips
├── demo.gif                # Looping demonstration recording
├── agents-cli-manifest.yaml # Agent manifest configuration
└── deployment_metadata.json# Deployed Reasoning Engine resource metadata
```

---

## 🛠️ Local Development & Execution

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`) authenticated with project access
- `agents-cli` installed

### 1. Running the Agent Playground Locally
From the project root:
```bash
agents-cli web
```
This launches the ADK Web Playground for testing tool calls, Memory Bank persistence, and A2UI cards.

### 2. Running the Custom Frontend Locally
Navigate to the `frontend/` directory, set environment variables, and start the FastAPI proxy server:
```bash
cd frontend
uv pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
uv run python main.py
```
Open a browser and navigate to `http://localhost:8080`.

---

## ☁️ Deployment Instructions

### Deploying the Agent to Vertex AI Agent Runtime
```bash
agents-cli deploy --project <YOUR_GCP_PROJECT_ID> --region us-central1
```

### Deploying the Frontend to Cloud Run
```bash
gcloud run deploy agent-frontend \
  --source ./frontend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<REASONING_ENGINE_RESOURCE_NAME>",AGENT_DIRECTORY="app"
```
