"""
ThirdBrain UI — Locust Load Test
=================================
Run with:  locust -f locustfile.py --host http://localhost:3000
Then open: http://localhost:8089

In the Locust UI you will see SEPARATE user classes you can enable/disable:
  ┌─────────────────────────────────────────────────────────┐
  │  ✅ ChatBotUser       → POST /api/v1/chat/query only    │
  │  ✅ PageBrowserUser   → visits all UI pages             │
  │  ✅ AuthApiUser       → hits /api/auth/* endpoints      │
  │  ✅ FullJourneyUser   → simulates a complete user flow  │
  └─────────────────────────────────────────────────────────┘
Each class can be given its own user count in the UI.
"""

import random
from locust import HttpUser, task, between

# ---------------------------------------------------------------------------
# Config — update these with real IDs for authenticated test results
# ---------------------------------------------------------------------------

PLACEHOLDER_USER_ID  = "1a048a15-a212-44df-ac43-9aea600f6718"
PLACEHOLDER_BRAND_ID = "357"

# The chat/query endpoint lives on the NEW INFRA backend, NOT on localhost:3000.
# Locust will use this full URL directly, bypassing the host setting.
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
]

PROTECTED_PAGES = ["/chat", "/admin", "/settings", "/qc-bot", "/internal-tools", "/client", "/csat"]
PUBLIC_PAGES    = ["/", "/signin"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _accept(response, ok_codes: set):
    """Mark a locust response as success/failure based on status code."""
    if response.status_code in ok_codes:
        response.success()
    elif response.status_code >= 500:
        response.failure(f"Server error {response.status_code} on {response.url}")


# ===========================================================================
# 1️⃣  ChatBotUser — stress-tests ONLY the chat query API
# ===========================================================================

class ChatBotUser(HttpUser):
    """
    SELECT THIS to stress-test the chat/query endpoint.
    Simulates users actively sending messages to the chatbot.
    """
    weight     = 1
    wait_time  = between(1, 3)

    @task
    def post_chat_query(self):
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
            BACKEND_CHAT_URL,
            data=form,
            catch_response=True,
            name="POST /api/v1/chat/query",
        ) as r:
            _accept(r, {200, 307, 308, 401, 403, 422})


# ===========================================================================
# 2️⃣  PageBrowserUser — visits UI pages only (no API calls)
# ===========================================================================

class PageBrowserUser(HttpUser):
    """
    SELECT THIS to test Next.js SSR rendering performance across all pages.
    Simulates users navigating around the app.
    """
    weight    = 1
    wait_time = between(2, 5)

    @task(5)
    def visit_landing(self):
        with self.client.get("/", catch_response=True, name="GET /") as r:
            _accept(r, {200, 304})

    @task(3)
    def visit_signin(self):
        with self.client.get("/signin", catch_response=True, name="GET /signin") as r:
            _accept(r, {200, 304})

    @task(4)
    def visit_chat(self):
        with self.client.get("/chat", catch_response=True, name="GET /chat") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(2)
    def visit_admin(self):
        with self.client.get("/admin", catch_response=True, name="GET /admin") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(2)
    def visit_settings(self):
        with self.client.get("/settings", catch_response=True, name="GET /settings") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(1)
    def visit_qcbot(self):
        with self.client.get("/qc-bot", catch_response=True, name="GET /qc-bot") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(1)
    def visit_internal_tools(self):
        with self.client.get("/internal-tools", catch_response=True, name="GET /internal-tools") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(1)
    def visit_random_protected(self):
        """Hits a random protected page."""
        page = random.choice(PROTECTED_PAGES)
        with self.client.get(page, catch_response=True, name=f"GET {page} [random]") as r:
            _accept(r, {200, 302, 307, 308, 304})

    @task(1)
    def favicon(self):
        self.client.get("/favicon.ico", name="GET /favicon.ico")


# ===========================================================================
# 3️⃣  AuthApiUser — hits Next.js /api/auth/* endpoints only
# ===========================================================================

class AuthApiUser(HttpUser):
    """
    SELECT THIS to test the NextAuth API layer in isolation.
    Useful for measuring session/provider/CSRF endpoint performance.
    """
    weight    = 1
    wait_time = between(1, 2)

    @task(5)
    def session(self):
        with self.client.get(
            "/api/auth/session", catch_response=True, name="GET /api/auth/session"
        ) as r:
            _accept(r, {200, 304})

    @task(3)
    def providers(self):
        with self.client.get(
            "/api/auth/providers", catch_response=True, name="GET /api/auth/providers"
        ) as r:
            _accept(r, {200, 304})

    @task(2)
    def csrf(self):
        with self.client.get(
            "/api/auth/csrf", catch_response=True, name="GET /api/auth/csrf"
        ) as r:
            _accept(r, {200, 304})


# ===========================================================================
# 4️⃣  FullJourneyUser — complete realistic user flow
# ===========================================================================

class FullJourneyUser(HttpUser):
    """
    SELECT THIS to simulate a real user flow:
    landing → sign-in → check session → browse → send a chat message.
    """
    weight    = 1
    wait_time = between(1, 4)

    @task
    def full_journey(self):
        # Step 1 — visit landing
        with self.client.get("/", catch_response=True, name="Journey: 1 Landing") as r:
            _accept(r, {200, 304})

        # Step 2 — visit sign-in page
        with self.client.get("/signin", catch_response=True, name="Journey: 2 Sign-In Page") as r:
            _accept(r, {200, 304})

        # Step 3 — fetch session (simulates NextAuth client-side check)
        with self.client.get(
            "/api/auth/session", catch_response=True, name="Journey: 3 Auth Session"
        ) as r:
            _accept(r, {200, 304})

        # Step 4 — navigate to chat
        with self.client.get("/chat", catch_response=True, name="Journey: 4 Chat Page") as r:
            _accept(r, {200, 302, 307, 308, 304})

        # Step 5 — send a chat message
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
            BACKEND_CHAT_URL, data=form,
            catch_response=True, name="Journey: 5 Chat Query"
        ) as r:
            _accept(r, {200, 307, 308, 401, 403, 422})