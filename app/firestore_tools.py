"""Firestore backend module and function tools for TriCoach AI.

HARDCODED PROJECT ID: "qwiklabs-gcp-01-44253ac8b396"
Important: On Agent Platform, google.auth.default() and GOOGLE_CLOUD_PROJECT return the
project NUMBER (e.g. 687482616499), which breaks Firestore database resolution.
Always use the string project ID directly.
"""

import uuid
from typing import Optional
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-44253ac8b396"


def _get_firestore_client() -> firestore.Client:
    """Helper to return a Firestore client pinned to the hardcoded project ID string."""
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_workout_catalog(sport: str = None, max_duration_minutes: int = None) -> str:
    """Reads structured workouts from the Firestore 'workouts' catalog collection.

    Args:
        sport: Optional sport filter (e.g., 'Run', 'Swim', 'Bike', 'Triathlon / Brick', 'Strength & Mobility').
        max_duration_minutes: Optional maximum workout duration filter in minutes.

    Returns:
        Formatted summary string of matching workouts from Firestore.
    """
    try:
        db = _get_firestore_client()
        query = db.collection("workouts")

        if sport and sport.strip():
            # Perform case-insensitive substring match or exact match
            sport_clean = sport.strip().title()
            query = query.where("sport", "==", sport_clean)

        docs = list(query.stream())
        if not docs:
            # Fallback to fetching all docs if exact sport query yielded no results
            docs = list(db.collection("workouts").stream())

        results = []
        for doc in docs:
            data = doc.to_dict()
            duration = data.get("duration_minutes", 0)
            if max_duration_minutes and duration > max_duration_minutes:
                continue

            item_str = (
                f"• [{data.get('id', doc.id)}] {data.get('title', 'Workout')}\n"
                f"  Sport: {data.get('sport')}, Duration: {duration} mins, Intensity: {data.get('intensity')}\n"
                f"  Target Zones: {data.get('target_zones')}\n"
                f"  Description: {data.get('description')}"
            )
            results.append(item_str)

        if not results:
            return "No workouts found matching the specified criteria in the Firestore catalog."

        return f"Found {len(results)} workout(s) in Firestore catalog:\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error querying Firestore workouts catalog: {str(e)}"


def get_workout_detail(workout_id: str) -> str:
    """Retrieves full details for a specific workout document from the Firestore 'workouts' collection.

    Args:
        workout_id: The unique document ID of the workout (e.g., 'tempo_run_45', 'bike_sweetspot_60').

    Returns:
        Formatted string containing workout attributes or error if not found.
    """
    try:
        db = _get_firestore_client()
        doc_ref = db.collection("workouts").document(workout_id.strip())
        doc = doc_ref.get()

        if not doc.exists:
            return f"Workout ID '{workout_id}' was not found in the Firestore catalog."

        data = doc.to_dict()
        return (
            f"Workout Details for '{data.get('title')}' (ID: {doc.id}):\n"
            f"- Sport: {data.get('sport')}\n"
            f"- Duration: {data.get('duration_minutes')} minutes\n"
            f"- Intensity: {data.get('intensity')}\n"
            f"- Target Zones: {data.get('target_zones')}\n"
            f"- Tags: {', '.join(data.get('tags', []))}\n"
            f"- Description: {data.get('description')}"
        )
    except Exception as e:
        return f"Error reading workout '{workout_id}' from Firestore: {str(e)}"


def log_workout_activity(
    workout_id: str,
    athlete_name: str = "Anupa",
    actual_duration_minutes: int = 45,
    perceived_exertion: int = 7,
    notes: str = "Completed session as planned.",
) -> str:
    """Logs a completed workout activity to the Firestore 'workout_logs' collection.

    Args:
        workout_id: The ID or title of the workout routine completed.
        athlete_name: Name of the athlete completing the workout.
        actual_duration_minutes: Actual duration of the session in minutes.
        perceived_exertion: Rate of Perceived Exertion (RPE on a 1-10 scale).
        notes: Performance notes, heart rate data, or athlete feedback.

    Returns:
        Confirmation message with the Firestore generated log entry ID.
    """
    try:
        db = _get_firestore_client()
        log_id = f"log_{uuid.uuid4().hex[:8]}"
        log_entry = {
            "id": log_id,
            "workout_id": workout_id,
            "athlete_name": athlete_name,
            "actual_duration_minutes": actual_duration_minutes,
            "perceived_exertion": perceived_exertion,
            "notes": notes,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }

        db.collection("workout_logs").document(log_id).set(log_entry)
        return (
            f"Successfully logged workout activity to Firestore!\n"
            f"- Log ID: {log_id}\n"
            f"- Athlete: {athlete_name}\n"
            f"- Workout: {workout_id}\n"
            f"- Duration: {actual_duration_minutes} mins (RPE: {perceived_exertion}/10)\n"
            f"- Notes: {notes}"
        )
    except Exception as e:
        return f"Error writing activity log to Firestore: {str(e)}"


def add_workout_to_catalog(
    title: str,
    sport: str,
    duration_minutes: int,
    intensity: str,
    description: str,
    target_zones: str,
) -> str:
    """Adds a new custom workout routine to the Firestore 'workouts' collection.

    Args:
        title: Title of the workout (e.g., '60-Min Zone 2 Long Run').
        sport: Sport type ('Run', 'Swim', 'Bike', 'Triathlon / Brick', 'Strength & Mobility').
        duration_minutes: Duration of workout in minutes.
        intensity: Intensity level ('Low', 'Moderate', 'High').
        description: Step-by-step description of warm-up, main set, and cool-down.
        target_zones: Heart rate or power target zones.

    Returns:
        Confirmation message with the new workout document ID in Firestore.
    """
    try:
        db = _get_firestore_client()
        clean_id = title.lower().replace(" ", "_").replace("-", "_")[:30]
        workout_id = f"{clean_id}_{duration_minutes}"

        doc_data = {
            "id": workout_id,
            "title": title.strip(),
            "sport": sport.strip().title(),
            "duration_minutes": duration_minutes,
            "intensity": intensity.strip().title(),
            "description": description.strip(),
            "target_zones": target_zones.strip(),
            "tags": [sport.lower(), intensity.lower(), "custom"],
        }

        db.collection("workouts").document(workout_id).set(doc_data)
        return (
            f"Successfully added new workout routine to Firestore catalog!\n"
            f"- Document ID: {workout_id}\n"
            f"- Title: {title}\n"
            f"- Sport: {sport}\n"
            f"- Duration: {duration_minutes} mins ({intensity} intensity)"
        )
    except Exception as e:
        return f"Error adding workout to Firestore catalog: {str(e)}"
