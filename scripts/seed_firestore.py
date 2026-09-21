#!/usr/bin/env python3
"""Seed Firestore database with initial TriCoach AI workout catalog items."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-44253ac8b396"

WORKOUT_ITEMS = [
    {
        "id": "tempo_run_45",
        "title": "45-Min Threshold Tempo Run",
        "sport": "Run",
        "duration_minutes": 45,
        "intensity": "High",
        "description": "10 min warm-up, 25 min steady tempo in Zone 3/4, 10 min cool-down.",
        "target_zones": "Zone 3 / Zone 4",
        "tags": ["running", "tempo", "threshold", "triathlon"],
    },
    {
        "id": "swim_threshold_1500",
        "title": "1500m Endurance Threshold Swim",
        "sport": "Swim",
        "duration_minutes": 40,
        "intensity": "Moderate-High",
        "description": "300m warm-up, 10x100m on 1:45 interval maintaining race pace, 200m cool-down.",
        "target_zones": "Zone 3",
        "tags": ["swimming", "endurance", "race-pace"],
    },
    {
        "id": "bike_sweetspot_60",
        "title": "60-Min Sweetspot Bike Intervals",
        "sport": "Bike",
        "duration_minutes": 60,
        "intensity": "High",
        "description": "15 min warm-up, 3x12 min sweetspot intervals at 88-93% FTP with 3 min spin recovery, 9 min cool-down.",
        "target_zones": "Zone 3 / Sweetspot",
        "tags": ["cycling", "sweetspot", "power", "ftp"],
    },
    {
        "id": "brick_session_75",
        "title": "75-Min Bike-to-Run Brick Workout",
        "sport": "Triathlon / Brick",
        "duration_minutes": 75,
        "intensity": "High",
        "description": "50 min aerobic bike ride in Zone 2/3 directly transitioning into a 25 min transition run.",
        "target_zones": "Zone 2 / Zone 3",
        "tags": ["triathlon", "brick", "transition"],
    },
    {
        "id": "recovery_flexibility_30",
        "title": "30-Min Active Recovery & Mobility",
        "sport": "Strength & Mobility",
        "duration_minutes": 30,
        "intensity": "Low",
        "description": "Foam rolling, dynamic hip openers, hamstring mobility, and core stability routines.",
        "target_zones": "Zone 1 / Recovery",
        "tags": ["recovery", "mobility", "stretching"],
    },
]


def seed_database():
    print(f"Connecting to Firestore with project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("workouts")

    for item in WORKOUT_ITEMS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"✅ Seeded workout: '{item['title']}' (ID: {doc_id})")

    print("\n🎉 Firestore database successfully seeded with workout catalog!")


if __name__ == "__main__":
    seed_database()
