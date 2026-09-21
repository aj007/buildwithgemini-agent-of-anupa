# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.a2ui_utils import a2ui_callback
from app.firestore_tools import (
    add_workout_to_catalog,
    get_workout_catalog,
    get_workout_detail,
    log_workout_activity,
)
from app.image_tools import generate_workout_badge
from app.rag_tools import consult_rag_corpus
from app.video_tools import generate_workout_video


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract durable facts and save session to Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(location: str) -> str:
    """Gets weather information for a specified location.

    Args:
        location: A string containing the city or location name.

    Returns:
        A string with weather information for the specified location.
    """
    loc = location.lower()
    if "sf" in loc or "san francisco" in loc:
        return "San Francisco: 62°F, Partly Cloudy with mild ocean breeze."
    elif "new york" in loc or "nyc" in loc:
        return "New York City: 72°F, Clear and Sunny."
    elif "tokyo" in loc:
        return "Tokyo: 22°C, Pleasant with light winds."
    elif "london" in loc:
        return "London: 18°C, Light drizzle."
    return f"{location.title()}: 70°F, Fair conditions."


def get_current_time(city: str) -> str:
    """Gets the current local time for a city.

    Args:
        city: The name of the city to check local time for.

    Returns:
        A string with the current formatted local time.
    """
    c = city.lower()
    if "sf" in c or "san francisco" in c or "los angeles" in c:
        tz_identifier = "America/Los_Angeles"
    elif "new york" in c or "nyc" in c:
        tz_identifier = "America/New_York"
    elif "london" in c:
        tz_identifier = "Europe/London"
    elif "tokyo" in c:
        tz_identifier = "Asia/Tokyo"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time in {city.title()} is {now.strftime('%Y-%m-%d %H:%M:%S %Z')}."


def get_anupa_summary() -> str:
    """Retrieves profile summary and preferences for Anupa.

    Returns:
        Profile summary and preferences string.
    """
    return (
        "Anupa's Profile:\n"
        "- Role: Triathlete, Fitness Enthusiast & AI Builder\n"
        "- Priorities: Multi-sport triathlon training, pace splits, TSS calculation, and personal health metrics\n"
        "- Preferred Tone: Encouraging, analytical, precise, and proactive"
    )


def calculate_heart_rate_zones(max_heart_rate: int, resting_heart_rate: int = 60) -> str:
    """Calculates target heart rate training zones (Zone 1 to Zone 5) using the Karvonen formula.

    Args:
        max_heart_rate: Maximum heart rate in beats per minute (bpm).
        resting_heart_rate: Resting heart rate in beats per minute (bpm). Defaults to 60 bpm.

    Returns:
        Formatted summary of target heart rate ranges for Zone 1 through Zone 5.
    """
    hrr = max_heart_rate - resting_heart_rate

    z1_low, z1_high = round(resting_heart_rate + hrr * 0.50), round(resting_heart_rate + hrr * 0.60)
    z2_low, z2_high = round(resting_heart_rate + hrr * 0.60), round(resting_heart_rate + hrr * 0.70)
    z3_low, z3_high = round(resting_heart_rate + hrr * 0.70), round(resting_heart_rate + hrr * 0.80)
    z4_low, z4_high = round(resting_heart_rate + hrr * 0.80), round(resting_heart_rate + hrr * 0.90)
    z5_low, z5_high = round(resting_heart_rate + hrr * 0.90), max_heart_rate

    return (
        f"Heart Rate Training Zones (Max HR: {max_heart_rate} bpm, Resting HR: {resting_heart_rate} bpm):\n"
        f"- Zone 1 (Active Recovery, 50-60% HRR): {z1_low} - {z1_high} bpm\n"
        f"- Zone 2 (Aerobic Endurance, 60-70% HRR): {z2_low} - {z2_high} bpm\n"
        f"- Zone 3 (Tempo / Aerobic Capacity, 70-80% HRR): {z3_low} - {z3_high} bpm\n"
        f"- Zone 4 (Threshold / Lactate, 80-90% HRR): {z4_low} - {z4_high} bpm\n"
        f"- Zone 5 (Anaerobic / Max Effort, 90-100% HRR): {z5_low} - {z5_high} bpm"
    )


def get_outdoor_training_conditions(latitude: float = 40.7128, longitude: float = -74.0060) -> str:
    """Fetches real-time outdoor triathlon training conditions (temp, wind speed, humidity) from the free Open-Meteo API.

    Args:
        latitude: Latitude coordinate for the workout location (e.g. 40.7128 for NYC, 37.7749 for SF).
        longitude: Longitude coordinate for the workout location (e.g. -74.0060 for NYC, -122.4194 for SF).

    Returns:
        Formatted string summarizing current outdoor weather, wind speed for cycling, and humidity.
    """
    try:
        api_key = os.environ.get("OPEN_METEO_API_KEY", "")
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )
        if api_key:
            url += f"&apikey={api_key}"

        req = urllib.request.Request(url, headers={"User-Agent": "TriCoachAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        current = data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")

        wind_advice = "Calm winds, ideal for aero bike posture." if isinstance(wind, (int, float)) and wind < 10 else "Moderate to high crosswinds expected on the bike leg."

        return (
            f"Real-Time Outdoor Training Conditions (Lat: {latitude}, Lon: {longitude}):\n"
            f"- Temperature: {temp}°F\n"
            f"- Relative Humidity: {humidity}%\n"
            f"- Wind Speed: {wind} mph\n"
            f"- Triathlon Cycling Assessment: {wind_advice}"
        )
    except Exception as e:
        return f"Error fetching outdoor training conditions: {str(e)}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are 'Agent of Anupa', a dedicated AI personal fitness and triathlon coach (TriCoach AI) built specifically for Anupa. "
        "You automatically retrieve and track all athlete personal details (such as weight, resting/max heart rate, "
        "fitness metrics, race goals, and training preferences) across sessions using your Memory Bank integration. "
        "You have access to a Firestore database containing a structured catalog of multi-sport workout routines ('workouts') "
        "and completed workout logs ('workout_logs'). "
        "use `calculate_heart_rate_zones` to calculate target heart rate zones based on max/resting heart rate, "
        "use `get_outdoor_training_conditions` to check live weather and wind speed for outdoor swim/bike/run sessions, "
        "use `generate_workout_badge` to generate custom milestone artwork and badges for completed workouts, "
        "use `generate_workout_video` to generate short video clips using Google's Omni model (gemini-omni-flash-preview) for workout items, "
        "use `consult_rag_corpus` to answer questions grounded in herbal, botanical, and health literature, "
        "use your Python sandbox code execution environment to run Python scripts for complex mathematical calculations, pace splits, and data science, "
        "and use your Firestore tools (`get_workout_catalog`, `get_workout_detail`, `log_workout_activity`, `add_workout_to_catalog`) "
        "to look up training routines, retrieve specific workout steps, and log completed sessions."
    ),
    workflow_description="Analyze the athlete's request, invoke appropriate tools, and return structured A2UI UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="agent_of_anupa",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    tools=[
        get_weather,
        get_current_time,
        get_anupa_summary,
        calculate_heart_rate_zones,
        get_outdoor_training_conditions,
        generate_workout_badge,
        generate_workout_video,
        consult_rag_corpus,
        get_workout_catalog,
        get_workout_detail,
        log_workout_activity,
        add_workout_to_catalog,
        PreloadMemoryTool(),
    ],
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name="projects/687482616499/locations/us-central1/reasoningEngines/4959628122304544768/sandboxEnvironments/1425293074795331584"
    ),
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
