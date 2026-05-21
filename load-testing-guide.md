# ThirdBrain — Load Test Files

**Project:** SecondBrain  
**Tool:** Locust 2.23.1 (Python 3.11.9)  
**Prepared by:** Jay Patel QA   
**Date:** April 2026

---

## Executive Summary *(For Managers,Team Leads & Devs)*

As part of ensuring the ThirdBrain platform is production-ready and can handle real-world traffic, the engineering team has implemented **automated load testing** using an industry-standard open-source tool called **Locust**.

Load testing answers the question: **"What happens to our platform when many users access it at the same time?"**

Three separate test scripts have been created, each targeting a different part of the system:

| # | File | What it tests | Why it matters |
|---|---|---|---|
| 1 | `locustfile_chat.py` | AI chatbot API | The core paid feature — needs to handle concurrent users without slowing down or crashing |
| 2 | locustfile_multiuser.py | Chat API with unique users | Tests chat/query endpoint with a unique random user_id per virtual user |
| 3 | `locustfile.py` | Full system combined | Simulates real mixed traffic — the most realistic test scenario |

### Why This Was Done

- **Proactive quality assurance** — find problems before users do, not after
- **Capacity planning** — understand how many users the system can handle before performance degrades
- **Confidence before releases** — run tests after any major change to confirm the system still holds up
- **Identify bottlenecks** — pinpoint exactly which endpoint or page slows down first under pressure

### What the Tests Do NOT Do

- They do **not** test UI design, visual appearance, or business logic
- They do **not** perform real Google logins (the tool cannot do OAuth flows) — protected pages will redirect to sign-in, which is the correct and expected behaviour
- They do **not** replace manual QA or functional testing

---

## What Was Built

Three separate Locust test files were created in `d:\second brain\thirdbrain-ui\` to allow isolated and combined load testing of the ThirdBrain platform.

---

## File 1 — `locustfile_chat.py`

**Tests:** Chat API endpoint only  
**Target server:** `https://new-infra-backend.schbanglabs.com`

### What it does
Sends `POST` requests directly to the AI chat backend with realistic multipart/form-data payloads. Each virtual user picks a random query from a pool of 10 sample questions and fires it at the endpoint every 1–3 seconds.

### Endpoint tested
```
POST https://new-infra-backend.schbanglabs.com/api/v1/chat/query
```

### Payload sent
```
query           → random question from sample pool
brand_id        → 357
user_id         → 1a048a15-a212-44df-ac43-9aea600f6718
stream          → true
use_rag         → true
conversation_id → (empty)
searchweb       → false
image_gen       → false
nsm_data        → false
skills          → (empty)
```

> **Why direct to backend?** The `/api/v1/chat/query` route does not exist on the Next.js frontend (`localhost:3000`). It lives entirely on the new-infra backend. Sending it to localhost returned a `404`. The fix was to use the full backend URL directly.

### How to run
```powershell
cd "d:\second brain\thirdbrain-ui"
locust -f locustfile_chat.py
```
Open `http://localhost:8089` and set:
- **Host:** `https://new-infra-backend.schbanglabs.com`
- **Users:** 20–50
- **Ramp Up:** 2–5

---

## File 2 — `locustfile_multiuser.py`

**Tests:** Chat API endpoint with multiple unique users  
**Target server:** `https://new-infra-backend.schbanglabs.com`

### What it does
Tests the chat/query endpoint with a UNIQUE random `user_id` per virtual user. Each Locust virtual user is assigned a unique random UUID when spawned, simulating completely different users hitting the server simultaneously.

This allows testing of:
- Per-user rate limiting (each user is distinct)
- Concurrent AI model inference
- Concurrent RAG / vector searches
- Concurrent database writes (separate conversation threads)
- SSE streaming for unique sessions
- Server memory / CPU under true multi-user load

### Endpoint tested
```
POST https://new-infra-backend.schbanglabs.com/api/v1/chat/query
```

### Payload sent
```
query           → random question from sample pool
brand_id        → 258
user_id         → random unique UUID (assigned from predefined list per virtual user)
stream          → true
use_rag         → true
conversation_id → (empty / unique per user thread)
searchweb       → false
image_gen       → false
nsm_data        → false
skills          → (empty)
```

> **Why use unique user IDs?** A real-world load consists of multiple separate users hitting the server. Using the same user ID for all concurrent requests fails to trigger per-user rate limiters, does not test concurrent session handling, and fails to check how databases handle concurrent writes on separate user conversation threads. Assigning unique user IDs simulates real multi-user traffic.

### How to run
```powershell
cd "d:\second brain\thirdbrain-ui"
locust -f locustfile_multiuser.py
```
Open `http://localhost:8089` and set:
- **Host:** `https://new-infra-backend.schbanglabs.com`
- **Users:** 20–100 (for stress testing)
- **Ramp Up:** Users / 10

---

## File 3 — `locustfile.py`

**Tests:** Everything combined  
**Target server:** `http://localhost:3000` (pages) + backend (chat)

### What it does
Runs all four user classes at the same time to simulate a realistic mixed-traffic scenario:

| User Class | What it simulates |
|---|---|
| `ChatBotUser` | Users actively sending chat messages |
| `PageBrowserUser` | Users browsing through pages |
| `AuthApiUser` | Clients checking session/auth state |
| `FullJourneyUser` | Complete flow: landing → signin → session check → chat page → send message |

> **Why tests are run on localhost (Hybrid Testing):** Next.js frontend UI pages (like `/`, `/chat`, `/admin`) and authentication API endpoints (`/api/auth/*`) run on the local development server (`http://localhost:3000` via `npm run dev`). Setting the host to `localhost:3000` allows Locust to resolve these relative paths locally. For chat messages, the script explicitly uses the absolute backend URL (`https://new-infra-backend.schbanglabs.com/api/v1/chat/query`), bypassing the localhost setting. This allows the script to perform a hybrid test targeting both the local frontend UI and remote backend endpoints simultaneously.

### How to run
```powershell
# Make sure npm run dev is already running in another terminal
cd "d:\second brain\thirdbrain-ui"
locust -f locustfile.py --host http://localhost:3000
```
Open `http://localhost:8089` and set:
- **Host:** `http://localhost:3000`
- **Users:** 40
- **Ramp Up:** 4

---

## Comparison Table

| | `locustfile_chat.py` | `locustfile_multiuser.py` | `locustfile.py` |
|---|---|---|---|
| **Chat API** | ✅ | ✅ | ✅ |
| **UI Pages** | ❌ | ❌ | ✅ |
| **Auth API** | ❌ | ❌ | ✅ |
| **Full journey** | ❌ | ❌ | ✅ |
| **Host** | Backend URL | Backend URL | localhost:3000 |
| **Use when** | Chatbot stress | Multi-user stress | Full system test |

---

## Key Issues Fixed During Setup

### 1. `405 Method Not Allowed` on chat endpoint
The chat query endpoint only accepts `POST` — the initial test file was using `GET`. Fixed by changing the method to `POST` with the correct `multipart/form-data` payload.

### 2. `404 Not Found` on chat endpoint
The route `/api/v1/chat/query` does not exist on `localhost:3000`. It is a backend route on `new-infra-backend.schbanglabs.com`. Fixed by pointing the chat task directly at the full backend URL.

### 3. Port 8089 already in use
Locust's web UI failed to start because a previous instance was still holding port 8089. Fixed by killing the old process before restarting.

---

## Quick Reference

```powershell
# File 1 — Chat API only
locust -f locustfile_chat.py
# → Set host to: https://new-infra-backend.schbanglabs.com

# File 2 — Multi-User Chatbot API
locust -f locustfile_multiuser.py
# → Set host to: https://new-infra-backend.schbanglabs.com

# File 3 — Full combined test (needs npm run dev)
locust -f locustfile.py --host http://localhost:3000
# → Set host to: http://localhost:3000

# Locust Web UI
http://localhost:8089
```

---

## What Good Results Look Like

After running any of the tests, the Locust UI shows a statistics table. Here is how to interpret the results at a glance:

| Metric | Green (Good) | Yellow (Watch) | Red (Action Required) |
|---|---|---|---|
| **Avg Response Time** | < 1000ms | 1000–3000ms | > 3000ms |
| **Failure Rate** | 0% | < 1% | > 1% |
| **95th Percentile** | < 2000ms | 2000–5000ms | > 5000ms |
| **Requests/sec** | Stable | Gradually dropping | Sudden drop |

> A **0% failure rate** at 50 concurrent users with average response times under 1 second would be considered a **passing result** for the current stage of the product.

---

## Observed Behaviour During Testing

### The "Synchronized Wave" Effect *(Observed with 3 users)*

During initial testing of `locustfile_chat.py` with **3 concurrent users**, the RPS chart showed a repeating square wave pattern — RPS rising to ~0.2, then dropping back to 0, then rising again — **even without stopping the test**.

This is expected behaviour and is explained below.

#### Why it happens

The chat endpoint (`/api/v1/chat/query`) uses **streaming AI responses (SSE)** which take approximately **24 seconds** to complete. With only 3 users all starting at the same time, they stay perfectly synchronized:

```
t=0s     → All 3 users send a request simultaneously
           Requests are IN FLIGHT — nothing has finished yet
           RPS = 0

t=24s    → All 3 responses complete at roughly the same time
           RPS spikes briefly to ~0.2

t=24–27s → Each user waits their 1–3s (wait_time), then sends a new request

t=27s    → All 3 users are IN FLIGHT again
           RPS drops back to 0

           ... pattern repeats indefinitely
```

Because all 3 users started together, they stay **synchronized** — they all wait together, complete together, and wait again together. This creates the square wave pattern visible in the charts.

#### Why this does not happen in real life

Real users are never synchronized. One person sends a message at 1:30 PM, another at 1:31 PM, another at 1:32:47 PM. With enough concurrent users, request completions are spread out over time and RPS stays stable and flat.

#### How user count affects the chart

| Users | Chart Pattern | Reason |
|---|---|---|
| **3 users** | Square wave — RPS pulses between 0 and 0.2 | All users stay synchronized |
| **10 users** | Partially smoothed — small dips visible | Users begin to desynchronize |
| **20+ users** | Flat stable line | Completions are fully spread out |

#### Recommendation

For more meaningful RPS charts when testing the chat endpoint, use **at least 20 users with a ramp-up of 5**. This desynchronizes users and produces a steady, readable RPS line.

```
Users: 20   Ramp Up: 5   Host: https://new-infra-backend.schbanglabs.com
```

> **Note:** This behaviour is not a bug in the test script or the server. It is a natural property of load testing slow streaming endpoints with a small number of users. The server is functioning correctly — it is simply taking the expected amount of time to generate and stream AI responses.

---

*This load testing setup was implemented by the engineering team as part of ongoing quality engineering efforts for the ThirdBrain platform.*


1. **Run File 1** (`locustfile_chat.py`) with 20 users against the live backend and record the average response time — this is your current baseline.
2. **Gradually increase** users from 20 → 50 → 100 to find where response times start climbing.
3. **Run File 2** (`locustfile_multiuser.py`) with 50 users to test how the server performs under true multi-user chat traffic.
4. **Run File 3** (`locustfile.py`) before every major release as a full system health check.
5. **Document results** after each test run and compare over time to spot regressions.

---

## Load Testing Stages — ThirdBrain Chat API

When running `locustfile_chat.py`, follow these stages progressively. Start from Baseline and work upward. **Do not jump straight to Stress or Heavy** — always establish a baseline first.

| Stage | Number of Users | Ramp Up | Purpose |
|---|---|---|---|
| **Baseline** | 20 | 4 | Establish normal performance benchmark |
| **Medium** | 50 | 5 | Simulate a busy working day with many active users |
| **Stress** | 200 | 10 | Push beyond expected limits — find degradation point |
| **Heavy** | 500 | 20 | Simulate a large-scale usage event or viral moment |
| **Extreme** | 1000 | 50 | Maximum capacity test — server may begin to fail here |

### How to run each stage

```
1. Start at Baseline (20 users) — run for 3–5 minutes, record results
2. Click the pencil/edit icon in Locust UI to increase users (no restart needed)
3. Move to Medium (50) — run for 3–5 minutes, record results
4. Continue upward only if the STOP conditions below are NOT triggered
5. Stop as soon as any STOP condition is hit — that is your capacity limit
```

---

## Stop Conditions — When to Halt the Test

Stop increasing users and record the current stage as the **capacity limit** if **any** of the following are observed:

| Condition | Threshold | What it means |
|---|---|---|
| **Average Response Time** | > 3,000 ms (3 seconds) | Server is struggling to handle the load |
| **Failure Rate** | > 1% | More than 1 in 100 requests are erroring out |
| **95th Percentile** | > 8,000 ms | Even the "fast" requests are becoming slow |
| **Failures/s rising** | Any upward trend | Error rate is growing — server is degrading |

> **Example:** If at 200 users the average response time climbs above 3 seconds, stop there. The system's safe capacity is somewhere between 50 and 200 users. Report this to the backend team for investigation.

### Visual indicators in the Locust Charts tab

- 🔴 **Red dots appearing** on the RPS chart = failures are occurring
- 📈 **Response time line climbing steeply** = server slowing under load
- 📉 **RPS dropping** while users stay constant = server can't keep up

---

*This load testing setup was implemented by the engineering team as part of ongoing quality engineering efforts for the ThirdBrain platform.*

---
---

# Stress Testing Guide — ThirdBrain Chat API

This section explains how Locust performs stress testing, what each stage means, and what to watch for during a test run.

---

## How Locust Performs Stress Testing

Locust gradually increases the number of virtual users over time until the system starts showing signs of failure. At each step, the server receives more and more simultaneous requests — simulating heavier and heavier real-world traffic.

### Example configuration

```
Users:   2000
Ramp-up: 100 users/sec
```

### What happens second by second

```
 0 sec  →  100 users active
 1 sec  →  200 users active
 2 sec  →  300 users active
 3 sec  →  400 users active
 ...
20 sec  →  2000 users active  ← full load
```

This pushes the server harder with every passing second until it either handles the load gracefully or begins to degrade.

---

## Example Stress Test Workflow — `/api/v1/chat/query`

Follow these 4 steps in sequence. **Never skip straight to Step 3 or 4** without first completing Steps 1 and 2 — you need a baseline to compare against.

---

### Step 1 — Baseline

```
Users: 20    Ramp-up: 2/sec
```

**Run for:** 3–5 minutes  
**Record:**
- Average response time
- Failure rate

This is your performance benchmark — the numbers everything else will be compared against. If the server is already slow here, the backend needs investigation before proceeding.

---

### Step 2 — Load Test

```
Users: 100    Ramp-up: 5/sec
```

**Run for:** 3–5 minutes  
**Check:** Does performance remain similar to baseline?

If response times and failure rates remain close to Step 1 numbers, the system is handling normal production load well.

---

### Step 3 — Stress Test

```
Users: 500    Ramp-up: 20/sec
```

**Run for:** 3–5 minutes  
**Check:** Is the system under heavy pressure?

Response times will likely increase. Watch for the first signs of failures. This is where the system begins to be genuinely tested.

---

### Step 4 — Breaking Point

```
Users: 1000+    Ramp-up: 50/sec
```

**Run for:** Until failure conditions are hit  
**You will observe:**
- Response times increasing significantly
- Errors appearing (`500 Internal Server Error`, `503 Service Unavailable`)
- Request rate (RPS) dropping even as user count stays the same

**This is the system's capacity limit.** Record the user count at which these signs appear and report it to the backend team.

---

## Metrics to Watch During Stress Testing

Focus on these four metrics in the Locust Statistics and Charts tabs:

| Metric | Location in Locust | What it tells you |
|---|---|---|
| **Avg Response Time** | Statistics tab → Avg (ms) | How fast the server is responding on average |
| **95th Percentile** | Statistics tab → 95% | Worst-case experience for most users |
| **Failure Rate** | Statistics tab → # Fails | System stability — % of requests that errored |
| **Requests/sec (RPS)** | Charts tab → green line | Server throughput — how many requests per second it handles |

### Warning signs — stop the test if you see any of these

| Warning | Threshold | Action |
|---|---|---|
| ⚠️ Avg response time rising | **> 3,000 ms** | Server is struggling |
| ⚠️ Failure rate increasing | **> 1%** | System is unstable |
| ⚠️ RPS dropping | While users stay constant | Server cannot keep up |
| ⚠️ Red dots on RPS chart | Any appearance | Requests are failing |
| ⚠️ 95th percentile > 8s | Consistently | Even fast paths are degraded |

> These indicate the system is **overloaded**. Stop the test, note the user count, and report the finding.

---

## Types of Stress Tests Available with Locust

### 1️⃣ Gradual Stress Test
Increase users slowly in steps. Best for finding the exact breaking point.

```
20 → 50 → 100 → 200 → 500
```

**How:** Use the pencil/edit icon in the Locust UI to increase users without restarting.  
**Best for:** Understanding exactly at which user count performance starts degrading.

---

### 2️⃣ Spike Stress Test
All users start at once — simulates a sudden traffic burst.

```
Users: 1000    Ramp-up: 1000/sec
```

**Simulates:** A company-wide announcement, a viral post, or a product launch that sends everyone to the platform at the same moment.  
**Best for:** Testing if the server can survive sudden unexpected surges.

---

### 3️⃣ Endurance Stress Test (Soak Test)
Run a moderate-heavy load for an extended period.

```
Users: 300    Duration: 1 hour
```

**Best for:** Finding **memory leaks** — where the server starts fast but slows down over time as memory fills up. Also finds database connection pool exhaustion and file handle leaks.  
**Signs of a problem:** Response times that look fine at minute 5 but are significantly worse at minute 45.

---

## Summary — Which Test to Run When

| Scenario | Test Type | Users | Ramp-up |
|---|---|---|---|
| Before a release | Baseline + Load | 20 → 100 | 2 → 5 |
| Finding capacity limit | Gradual Stress | 20 → 500 | Incremental |
| Preparing for a launch event | Spike | 1000 | 1000/sec |
| Checking for memory leaks | Endurance | 300 | 10 |

---

# Appendix — Understanding Locust: Complete Reference Guide

This section explains everything about the Locust tool itself — how it works, what every term means, and how to read the dashboard — written for someone who has never used it before.


---

## What is Locust?

**Locust** is a free, open-source load testing tool built in Python. The name comes from the idea of a swarm of locusts — just like a swarm of insects can overwhelm a field, Locust sends a swarm of virtual users to overwhelm (or simply stress-test) a server.

**In simple terms:**
> Locust pretends to be hundreds of users visiting your website at the same time and records how fast and reliably the server responds.

It does **not** open real browsers. Instead it sends raw HTTP requests (the same underlying network calls a browser makes), which is much faster and allows thousands of simulated users from a single machine.

---

## How Locust Works — Step by Step

```
1. You write a Python script (locustfile.py) that describes
   what ONE user does — which pages they visit, in what order,
   how long they wait between actions.

2. You run: locust -f locustfile.py

3. Locust starts a Web UI at http://localhost:8089

4. You enter:
   → How many users to simulate
   → How fast to add them (ramp up)
   → Which server to target (host)

5. Locust spawns N copies of your user script,
   each running independently at the same time.

6. Every request is timed and recorded.
   Results appear live in the dashboard.
```

---

## The "Start New Load Test" Form — Every Field Explained

When you open `http://localhost:8089`, you see a form before the test starts:

### Number of Users *(peak concurrency)*
- **What it means:** The maximum number of virtual users that will be active simultaneously at the peak of the test.
- **Example:** Enter `50` → at full load, 50 fake users are hitting your server at the same time.
- **Think of it as:** How many people are in the store at once.

### Ramp Up *(users started/second)*
- **What it means:** How many new users Locust adds every second until it reaches the total user count.
- **Example:** Users = 50, Ramp Up = 5 → Locust adds 5 new users every second for 10 seconds until all 50 are active.
- **Why not start all at once?** Gradual ramp-up simulates real organic traffic growth. Starting all at once simulates a spike.

```
Ramp Up = 5, Total Users = 15:

t=0s  →  5 users active
t=1s  →  10 users active
t=2s  →  15 users active  ← full load reached, stays here
t=3s  →  15 users (steady)
```

### Host
- **What it means:** The base URL of the server you want to test. All relative paths in the test script (like `/chat`, `/api/auth/session`) get appended to this.
- **Example:** `http://localhost:3000` → every request goes to your local Next.js server.
- **Important:** Do NOT include a path here. Just the protocol + domain + port.

### Advanced Options
- Allows setting a **run time limit** (e.g. stop automatically after 5 minutes) — useful for automated CI/CD pipelines. Not needed for manual testing.

### START SWARM Button
- Begins the test. Users are spawned at the rate you set and start making requests immediately.

---

## The Locust Dashboard — All Tabs Explained

Once the test is running, the dashboard has 7 tabs:

---

### 1. STATISTICS Tab

The main data table. Each row is one **endpoint** (URL) being tested.

| Column | Full Name | What it means |
|---|---|---|
| **Type** | HTTP Method | GET (fetching a page) or POST (submitting data) |
| **Name** | Endpoint name | The URL path being tested |
| **# Reqs** | Number of Requests | Total requests sent to that endpoint so far |
| **# Fails** | Number of Failures | Requests that returned an error |
| **Avg (ms)** | Average Response Time | Mean time across all requests in milliseconds |
| **Min (ms)** | Minimum Response Time | Fastest single response recorded |
| **Max (ms)** | Maximum Response Time | Slowest single response recorded |
| **Med (ms)** | Median Response Time | Middle value — more reliable than average |
| **req/s** | Requests per Second | How many requests per second this endpoint is handling right now |
| **Failures/s** | Failures per Second | How many requests are failing each second |

**The bottom row "Aggregated"** = totals across all endpoints combined.

---

### 2. CHARTS Tab

Live real-time graphs. Three charts are shown:

#### Total Requests per Second (RPS)
- **Green line (RPS):** How many successful requests per second the server is handling.
- **Orange/red dots (Failures/s):** How many requests per second are failing.
- **What to look for:** RPS should rise as users are added and stay stable. If it suddenly drops while users stay the same, the server is struggling.

#### Response Times (ms)
- **Yellow line:** Average response time across all requests.
- **Purple line:** 95th percentile — meaning 95% of requests are faster than this value.
- **What to look for:** Both lines should stay flat as users increase. If they start climbing steeply, the server is slowing down under load.

#### Number of Users
- Shows how many virtual users are currently active.
- Goes up during ramp-up, then stays flat at the target number.

---

### 3. FAILURES Tab

A detailed list of every request that failed, including:
- The URL that failed
- The HTTP method (GET/POST)
- The error message (e.g. `404 Not Found`, `500 Internal Server Error`, `Connection timeout`)

Use this tab to investigate **why** requests are failing, not just that they are.

---

### 4. EXCEPTIONS Tab

Shows Python-level errors in the test script itself (not server errors). If your locustfile has a bug, it appears here. Under normal circumstances this tab should be empty.

---

### 5. CURRENT RATIO Tab

Shows the **distribution of user types** when multiple `HttpUser` classes are defined in the test file (like in `locustfile.py` which has 4 user classes). It shows what percentage of the total virtual users belong to each class.

---

### 6. DOWNLOAD DATA Tab

Exports test results as CSV files for reporting or analysis in Excel:
- **Download Statistics CSV** — the full statistics table
- **Download Failures CSV** — all failure details
- **Download Exceptions CSV** — script errors

---

### 7. LOGS Tab

Shows Locust's internal log output — useful for debugging if something unexpected happens during the test.

---

## All Short Forms & Terms Glossary

| Term / Shortform | Full Form | Simple Meaning |
|---|---|---|
| **RPS** | Requests Per Second | How many requests the server handles every second |
| **ms** | Milliseconds | Unit of response time. 1000ms = 1 second |
| **Avg** | Average | Sum of all values divided by count |
| **Med** | Median | The middle value when all responses are sorted by speed |
| **Min** | Minimum | The fastest response ever recorded in the test |
| **Max** | Maximum | The slowest response ever recorded in the test |
| **95th %ile** | 95th Percentile | 95% of requests were faster than this value |
| **GET** | HTTP GET | Fetching/reading a page or data (no data sent) |
| **POST** | HTTP POST | Sending data to the server (e.g. submitting a form) |
| **SSE** | Server-Sent Events | A streaming connection where the server sends data continuously (used by the chat endpoint) |
| **HTTP** | HyperText Transfer Protocol | The standard protocol for web communication |
| **200 OK** | HTTP 200 | Request succeeded ✅ |
| **302 / 307** | HTTP Redirect | Server is sending the user to a different page |
| **401** | Unauthorized | No valid login session — access denied |
| **403** | Forbidden | Logged in but not allowed to access this resource |
| **404** | Not Found | The URL/route does not exist |
| **405** | Method Not Allowed | Used GET on an endpoint that only accepts POST (or vice versa) |
| **500** | Internal Server Error | The server crashed trying to handle the request |
| **503** | Service Unavailable | Server is overloaded or down |
| **SSR** | Server-Side Rendering | The Next.js server builds the HTML page on every request (vs. sending a static file) |
| **OAuth** | Open Authorization | The login standard used by Google Sign-In |
| **CSRF** | Cross-Site Request Forgery | A security token that proves a request came from the real app |
| **Greenlet** | — | Locust's lightweight virtual thread — one per simulated user |
| **Concurrency** | — | Number of users doing things at the exact same time |
| **Ramp Up** | — | The rate at which new users are added (users per second) |
| **Swarm** | — | The group of all active virtual users running the test |
| **Locustfile** | — | The Python script that defines what virtual users do |
| **HttpUser** | — | The Locust class that represents one type of virtual user |
| **@task** | — | A Python decorator that marks a function as something a virtual user will do |
| **weight** | — | A number that controls how often a task is chosen relative to others |
| **wait_time** | — | How long each virtual user pauses between tasks |
| **between(a, b)** | — | A random wait time between `a` and `b` seconds |

---

## Common Questions

**Q: Why do I see 302/307 responses on protected pages — is that a failure?**
> No. A redirect to the sign-in page means the authentication middleware is working correctly. Locust does not log in via Google OAuth, so protected pages always redirect it. This is counted as a success in our test scripts.

**Q: Why is the chat response time 20–30 seconds?**
> The chat endpoint uses streaming AI responses (SSE). The server starts streaming tokens one by one and the connection stays open until the full answer is sent. Locust measures the total time from request sent to connection closed — so 20–30 seconds represents the full AI generation time, not a failure.

**Q: Why is RPS so low (near 0)?**
> Either no users are spawned yet (click START SWARM), or the `wait_time` is set high and users are between tasks. Also, if the server is very slow (high response times), fewer requests complete per second naturally.

**Q: What is a good number of users to start with?**
> Start with 10 users, ramp up 2/sec. Watch response times. If everything looks healthy, increase to 50, then 100. Stop when you see response times climbing significantly or failures appearing.

**Q: Does Locust test the UI/frontend visually?**
> No. Locust sends raw HTTP requests — it does not run a real browser, execute JavaScript, or render CSS. It measures purely how fast the server responds to network requests.

---

*End of Appendix*
