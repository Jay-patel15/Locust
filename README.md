# 🦗 Locust Load Testing for ThirdBrain UI

Welcome to the **ThirdBrain UI Load Testing** repository! This repository contains automated load testing scripts built with [Locust](https://locust.io/) to ensure the ThirdBrain platform is stable, performant, and production-ready under real-world traffic.

## 🎯 Objective
Load testing helps us answer: **"What happens to our platform when many users access it at the same time?"**
These tests let us proactively find bottlenecks, plan capacity, and verify performance before and after major releases.

## 🗂️ Test Scripts Overview

We have separated our performance testing into specific files, each targeting a different part of the system:

| # | Script | Target | Purpose |
|---|---|---|---|
| 1 | `locustfile_chat.py` | **AI Chatbot API** | The core paid feature. Ensures the AI backend handles concurrent users without crashing or slowing down. |
| 2 | `locustfile_multiuser.py` | **Multi-User Chatbot API** | Tests the chat/query endpoint with a unique random user_id per virtual user to simulate real multi-user traffic. |
| 3 | `locustfile.py` | **Full System** | Combines chat users and page browsers to simulate real mixed traffic and complete usage flows. |

*Note: These tests efficiently simulate HTTP requests and API calls; they simulate exact server loads rather than doing UI/browser rendering or completing OAuth flows.*

## 🚀 How to Run

Before running the tests, make sure you have [Locust installed](https://docs.locust.io/en/stable/installation.html).

### 1. Test Chat API Only
```bash
locust -f locustfile_chat.py
```
*In the web UI (http://localhost:8089), set Host to your backend API URL.*

### 2. Test Chat API with Multi-User
*Each virtual user gets assigned a unique UUID to simulate real concurrent traffic.*
```bash
locust -f locustfile_multiuser.py
```

### 3. Full Combined Test
```bash
locust -f locustfile.py --host http://localhost:3000
```

> **Accessing the UI:** Once the Locust script starts, open [http://localhost:8089](http://localhost:8089) in your browser to configure virtual users, ramp-up rate, and start the swarm.

## 📈 Understanding the Metrics
When running tests, keep an eye on these metrics in the Locust Dashboard:

- **Avg Response Time:** Should ideally remain under 1000ms. If it climbs above 3000ms, the server is struggling.
- **Failures/Error Rate:** Look out for failure rates above 1%.
- **Charts / RPS:** Watch the RPS (Requests Per Second). It should stabilize if the server can handle the load. Repeated drops in RPS while simulated users increase mean the server is dropping requests.

---

*For detailed methodologies, test scenario configurations, and stress testing stages, please refer to the complete [`load-testing-guide.md`](./load-testing-guide.md) included in this repository.*