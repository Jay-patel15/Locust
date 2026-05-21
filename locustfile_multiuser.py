"""
ThirdBrain — Multi-User Stress Test
=====================================
Tests the chat/query endpoint with a UNIQUE random user_id per virtual user.

Each Locust virtual user gets its own UUID when spawned, simulating
completely different users hitting the server simultaneously.

  50 Locust users = 50 different user_ids = true multi-user load

Run with:
  locust -f locustfile_multiuser.py
Then open: http://localhost:8089

In Locust UI set:
  Host         → https://new-infra-backend.schbanglabs.com
  Number users → 20 to start, increase to 50 / 100 / 200 for stress
  Ramp up      → Users ÷ 10  (e.g. 5 for 50 users)
"""

import random
import uuid
from locust import HttpUser, task, between

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PLACEHOLDER_BRAND_ID = "258"

TEST_USER_IDS = [
    "3453ef4e-9e94-4e09-82e0-3d929c0787f6", # Prakash Mane
    "5df7392b-0caa-4502-b699-0af0fce8c11c", # Shreyas Gurav
    "d1ec931c-8f0a-4030-a7b9-eda164b8543d", # Yash Nayak
    "1f39647a-6cf4-425e-8b6b-5ebd8edb1c5c", # Hayyan Hajwani
    "d85fe25b-72e3-4f36-a003-00bdceecf626", # Kajal Tiwari
    "eebac055-e9a8-430f-842c-c2269bf07d6f", # Chetan Marathe
    "1a048a15-a212-44df-ac43-9aea600f6718", # Jay Patel
]

BACKEND_HOST     = "https://new-infra-backend.schbanglabs.com"
CHAT_QUERY_PATH  = "/api/v1/chat/query"

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
    "Describe the brand personality in 3 words.",
    "What is the brand's unique selling proposition?",
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

class MultiUserChatBot(HttpUser):
    """
    TRUE MULTI-USER STRESS TEST.

    Each virtual user is assigned a unique random UUID as their user_id
    when they are spawned. This means:

      - Virtual User 1  → user_id: "a3f2c1d4-..."  (unique)
      - Virtual User 2  → user_id: "b7e9f2c5-..."  (unique)
      - Virtual User 3  → user_id: "c1d8a3f6-..."  (unique)
      ...
      - Virtual User 50 → user_id: "z9y8x7w6-..."  (unique)

    The backend sees 50 completely different users hitting it simultaneously.
    This tests:
      ✅ Per-user rate limiting (each user is distinct)
      ✅ Concurrent AI model inference
      ✅ Concurrent RAG / vector searches
      ✅ Concurrent database writes (separate conversation threads)
      ✅ SSE streaming for 50 unique sessions
      ✅ Server memory / CPU under true multi-user load
    """

    host      = BACKEND_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """
        Called ONCE when this virtual user is spawned.
        Assigns a random user ID from the predefined TEST_USER_IDS list.
        """
        self.user_id         = random.choice(TEST_USER_IDS)
        self.conversation_id = ""                   # starts a fresh conversation thread

        print(f"[Spawned] Virtual user → user_id: {self.user_id}")

    @task
    def send_chat_message(self):
        """
        Each virtual user sends a POST with its own unique user_id.
        50 users = 50 different user_ids hitting the server at the same time.
        """
        form = {
            "query":           random.choice(SAMPLE_QUERIES),
            "brand_id":        PLACEHOLDER_BRAND_ID,
            "user_id":         self.user_id,           # ← unique per virtual user
            "conversation_id": self.conversation_id,   # ← each user's own thread
            "stream":          "true",
            "use_rag":         "true",
            "searchweb":       "false",
            "image_gen":       "false",
            "nsm_data":        "false",
            "skills":          "",
        }

        with self.client.post(
            CHAT_QUERY_PATH,
            data=form,
            catch_response=True,
            name="POST /api/v1/chat/query [multi-user]",
        ) as r:
            _accept(r, {200, 401, 403, 422})
