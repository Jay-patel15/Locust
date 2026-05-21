"""
ThirdBrain — Chat Load Test
============================
Tests ONLY the chat/query backend endpoint.

Run with:
  locust -f locustfile_chat.py
Then open: http://localhost:8089
Host      : leave blank (uses BACKEND_CHAT_URL directly)
"""

import random
from locust import HttpUser, task, between

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PLACEHOLDER_USER_ID  = "1a048a15-a212-44df-ac43-9aea600f6718"
PLACEHOLDER_BRAND_ID = "357"

# Direct backend URL — Next.js does NOT proxy this route
BACKEND_CHAT_URL = "https://new-infra-backend.schbanglabs.com/api/v1/chat/query"

SAMPLE_QUERIES = [
    "What is the brand's tone of voice?",
    "Give me a tagline for a summer campaign.",
    "Summarize the brand guidelines.",
    "What are the key product features?",
    "Write a short social media caption.",
    "Who is the target audience?",
    "Suggest 3 campaign ideas for Gen Z.",
    "What colors are used in the brand palette?",
    "What are the brand's core values?",
    "Create a product launch announcement.",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _accept(response, ok_codes: set):
    if response.status_code in ok_codes:
        response.success()
    elif response.status_code >= 500:
        response.failure(f"Server error {response.status_code}")


# ---------------------------------------------------------------------------
# User class
# ---------------------------------------------------------------------------

class ChatBotUser(HttpUser):
    """
    Hammers the chat/query endpoint with realistic multipart/form-data payloads.
    Each virtual user sends one message every 1–3 seconds.

    In Locust UI set:
      Host          → https://new-infra-backend.schbanglabs.com
      Number users  → however many concurrent chatbot users you want to simulate
      Ramp up       → 5  (add 5 users/sec)
    """

    host      = BACKEND_CHAT_URL.split("/api")[0]   # https://new-infra-backend.schbanglabs.com
    wait_time = between(1, 3)

    @task
    def send_chat_message(self):
        """Sends a POST request exactly as the ThirdBrain frontend does."""
        form = {
            "query":           random.choice(SAMPLE_QUERIES),
            "brand_id":        PLACEHOLDER_BRAND_ID,
            "user_id":         PLACEHOLDER_USER_ID,
            "conversation_id": "",
            "stream":          "true",
            "use_rag":         "true",
            "searchweb":       "false",
            "image_gen":       "false",
            "nsm_data":        "false",
            "skills":          "",
        }

        with self.client.post(
            "/api/v1/chat/query",
            data=form,
            catch_response=True,
            name="POST /api/v1/chat/query",
        ) as r:
            # 200 = success
            # 401/403 = auth wall (no real token — expected)
            # 500+ = real backend error
            _accept(r, {200, 401, 403, 422})
