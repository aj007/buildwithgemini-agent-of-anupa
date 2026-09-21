"""Video generation tool for TriCoach AI using gemini-omni-flash-preview model.

Key requirements:
1. Model: gemini-omni-flash-preview in global region
2. Save artifact using tool_context.save_artifact
3. Upload video bytes to public Cloud Storage bucket "tricoach-assets-44253ac8b396"
4. Return public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>)
5. Hardcode bucket name as a string
6. No local file write.
"""

import base64
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "tricoach-assets-44253ac8b396"
GCP_PROJECT_ID = "qwiklabs-gcp-01-44253ac8b396"


def generate_workout_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video clip for a triathlon training item using Google's Omni model (gemini-omni-flash-preview),
    saves it as an artifact in the playground, and uploads it to a public Cloud Storage bucket.

    Args:
        prompt: Detailed description of the video to generate (e.g., 'A 5-second video of a triathlete running along a scenic coastal path').
        tool_context: ADK ToolContext automatically injected by the runtime.

    Returns:
        The public HTTPS URL of the uploaded video asset.
    """
    try:
        client = genai.Client(vertexai=True, project=GCP_PROJECT_ID, location="global")
        
        # Call Google's Omni model for video generation
        video_bytes = None
        try:
            interaction = client.interactions.create(
                model="gemini-omni-flash-preview",
                input=f"A short high quality 5-second video clip for triathlon training: {prompt}"
            )
            if hasattr(interaction, "output_video") and interaction.output_video:
                raw_data = getattr(interaction.output_video, "data", None)
                if raw_data:
                    if isinstance(raw_data, bytes):
                        video_bytes = raw_data
                    elif isinstance(raw_data, str):
                        video_bytes = base64.b64decode(raw_data)
        except Exception as api_err:
            # Fallback to models.generate_content if interactions endpoint differs
            response = client.models.generate_content(
                model="gemini-omni-flash-preview",
                contents=f"A short video clip for triathlon training: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["VIDEO", "TEXT"],
                ),
            )
            if response.parts:
                for part in response.parts:
                    if part.inline_data and part.inline_data.data:
                        video_bytes = part.inline_data.data
                        break

        if not video_bytes:
            return "Failed to generate video bytes from model."

        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact in Playground
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to public GCS bucket (no local file write)
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"videos/{filename}")
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/videos/{filename}"
        return (
            f"Successfully generated video and uploaded to Cloud Storage!\n"
            f"- Public URL: {public_url}\n"
            f"- Artifact Saved: {filename}"
        )
    except Exception as e:
        return f"Error generating or uploading video: {str(e)}"
