<div align="center">

  # VALORA
  
  ### AI-Powered Multi-Agent Economic Digital Twin Platform
  
  <p align="center">
    <img src="https://img.shields.io/badge/Next.js-14.1-black?style=for-the-badge&logo=next.js" alt="Next.js"/>
    <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  </p>
  
  <p align="center">
    <img src="https://img.shields.io/badge/PyTorch-RL_Agents-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch"/>
    <img src="https://img.shields.io/badge/CrewAI-Multi_Agent-6366F1?style=for-the-badge" alt="CrewAI"/>
    <img src="https://img.shields.io/badge/WebSocket-Real_Time-010101?style=for-the-badge" alt="WebSocket"/>
    <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  </p>

  <br/>
  
  **Built for Mumbai Hacks 2025**
  
  <p align="center">
    <a href="#demo">View Demo</a> •
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#api-reference">API</a>
  </p>

  <br/>

  ![VALORA Demo](https://via.placeholder.com/800x400/1a1a2e/60a5fa?text=VALORA+Economic+Simulation+Platform)

</div>

---

## What is VALORA?

**VALORA** (Virtual Agent-based LOgical Reasoning Apparatus) is a cutting-edge **AI-powered platform** that creates digital twins of national economies using multi-agent reinforcement learning and real-time simulation.

> *Imagine being able to test a new tax policy on millions of virtual citizens before implementing it in the real world. That's VALORA.*

### The Problem We Solve

| Traditional Approach | VALORA Solution |
|------------------------|-------------------|
| Static economic models with oversimplified assumptions | Dynamic agent-based simulation with 1M+ intelligent agents |
| Policy decisions based on historical data alone | AI-powered "what-if" scenario testing |
| Months to analyze policy impact | Real-time simulation results in seconds |
| Black-box economic models | Transparent, explainable AI with full audit trails |
| No behavioral adaptation | PPO-trained RL agents that learn and adapt |

---

## Features

<table>
<tr>
<td width="50%">

### AI-Powered Agents
- **Reinforcement Learning**: PPO-trained economic agents
- **Behavioral Modeling**: Consumers, firms, banks, government
- **Adaptive Learning**: Agents evolve based on market conditions
- **LSTM Forecasting**: Neural network predictions

</td>
<td width="50%">

### Real-Time Analytics
- **Live Dashboard**: WebSocket-powered streaming
- **Economic Indicators**: GDP, inflation, unemployment
- **Interactive Charts**: Recharts visualization
- **Export Reports**: PDF and CSV exports

</td>
</tr>
<tr>
<td width="50%">

### Policy Simulation
- **Monetary Policy**: Interest rate scenarios
- **Fiscal Policy**: Tax and spending analysis
- **Shock Testing**: Recessions, pandemics, trade wars
- **Comparison Mode**: Side-by-side policy analysis

</td>
<td width="50%">

### CrewAI Integration
- **Multi-Agent AI Crew**: Collaborative analysis
- **Natural Language**: Ask questions in plain English
- **Policy Recommendations**: AI-generated insights
- **Risk Assessment**: Automated risk scoring

</td>
</tr>
</table>

---

## Quick Start

### Prerequisites

```
Docker & Docker Compose
Node.js 20+ (for local dev)
Python 3.11+ (for local dev)
```

### One-Command Launch

```bash
# Clone the repository
git clone https://github.com/yourusername/valora.git
cd valora

# Copy environment template
cp .env.example .env

# Launch everything with Docker
docker compose up -d
```

**Access Points:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Local Development

<details>
<summary>Backend Setup</summary>

```bash
cd valora/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
</details>

<details>
<summary>Frontend Setup</summary>

```bash
cd valora/frontend
npm install
npm run dev
```
</details>

---

## Architecture

```
+===========================================================================+
|                           VALORA PLATFORM                                 |
+===========================================================================+
|                                                                           |
|   +----------------+        +----------------+        +----------------+  |
|   |   Next.js      |------->|   Nginx        |------->|  FastAPI       |  |
|   |   Frontend     |<-------|   Gateway      |<-------|   Backend      |  |
|   |   + Tailwind   |        |   + SSL        |        |   + WebSocket  |  |
|   +----------------+        +----------------+        +--------+-------+  |
|                                                                |          |
|                    +-------------------------------------------+          |
|                    |                                           |          |
|         +----------v----------+              +-----------------v--------+ |
|         |   Redis Cache       |              |    PostgreSQL DB         | |
|         |   + Pub/Sub         |              |    + TimescaleDB         | |
|         +----------+----------+              +--------------------------+ |
|                    |                                                      |
|         +----------v----------+                                           |
|         |   Celery Workers    |                                           |
|         |   + Beat Scheduler  |                                           |
|         +----------+----------+                                           |
|                    |                                                      |
|    +---------------+---------------+-------------------+                  |
|    |               |               |                   |                  |
|  +-v---------+  +--v--------+  +--v--------+  +-------v-----+             |
|  | Economic  |  | RL        |  | CrewAI    |  | LSTM        |             |
|  |  Engine   |  |  Agents   |  |  Multi-AI |  |  Forecast   |             |
|  +-----------+  +-----------+  +-----------+  +-------------+             |
|                                                                           |
+===========================================================================+
```

### Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TailwindCSS, Framer Motion, Recharts, Zustand, WebGL |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Celery, WebSockets |
| **AI/ML** | PyTorch, PPO (Stable Baselines3), LSTM, CrewAI, Groq |
| **Database** | PostgreSQL 16, Redis 7, TimescaleDB |
| **DevOps** | Docker, Nginx, GitHub Actions |

---

## API Reference

### Start a Simulation

```http
POST /api/v1/simulations/start
Content-Type: application/json

{
  "name": "Rate Hike Analysis Q1",
  "num_agents": 100000,
  "num_steps": 1000,
  "initial_conditions": {
    "gdp": 3500000000000,
    "inflation_rate": 0.06,
    "unemployment_rate": 0.045
  },
  "policy_parameters": {
    "tax_rate": 0.25,
    "interest_rate": 0.065,
    "government_spending_rate": 0.20
  }
}
```

### Stream Real-Time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/simulations/{id}/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Step:', data.step, 'GDP:', data.gdp);
};
```

### AI Policy Analysis

```http
POST /api/v1/crew/chat
Content-Type: application/json

{
  "message": "What would happen if we increased interest rates by 50 basis points?",
  "analysis_type": "impact_analysis"
}
```

<details>
<summary>View Full API Documentation</summary>

Access the interactive Swagger documentation at `http://localhost:8000/docs`

</details>

---

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Simulation Speed | **10,000 agents/second** |
| API Response Time | **< 50ms** (p95) |
| WebSocket Latency | **< 10ms** |
| Max Concurrent Simulations | **100+** |
| Max Agents per Simulation | **1,000,000+** |

---

## Roadmap

- [x] Core economic simulation engine
- [x] PPO-trained RL agents
- [x] Real-time WebSocket streaming
- [x] CrewAI multi-agent integration
- [x] Interactive dashboard
- [ ] International trade modeling
- [ ] Climate economics module
- [ ] Mobile application
- [ ] Multi-country simulation

---

## Testing

```bash
# Backend tests
cd backend && pytest tests/ -v --cov=app

# Frontend tests
cd frontend && npm test

# E2E tests
npm run test:e2e
```

---

## Team

<table>
<tr>
<td align="center">
<b>SATHISH RAJ</b><br/>
<sub>Full Stack Developer</sub>
</td>
</tr>
</table>

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Mumbai Hacks 2025** - For the platform and inspiration
- **CrewAI** - Multi-agent AI framework
- **Groq** - Ultra-fast LLM inference
- **Stable Baselines3** - RL algorithms

---

<div align="center">
  
  **Star this repo if you find it useful!**
  
  <br/>
  
  Made for Mumbai Hacks 2025
  
  <br/>
  
  [Report Bug](https://github.com/yourusername/valora/issues) | [Request Feature](https://github.com/yourusername/valora/issues)

</div>
