# SupportPilot

SupportPilot is an agentic customer support operations platform designed to demonstrate production-minded AI engineering.

The application will process support tickets through a traceable agent workflow that can classify issues, retrieve supporting information, use constrained backend tools, draft grounded responses, and recommend human approval or escalation.

## Project Goals

- Demonstrate stateful AI agent workflows
- Use constrained backend tools and structured outputs
- Provide full traceability into agent decisions
- Keep humans in control of final support actions
- Present the workflow through a polished support operations interface

## Planned Technology Stack

- React
- TypeScript
- Vite
- FastAPI
- Python
- PostgreSQL
- SQLAlchemy
- Pydantic
- Docker Compose
- LangGraph

## Repository Structure

```text
supportpilot/
├── apps/       # Frontend and backend applications
├── docs/       # Architecture and agent workflow documentation
├── infra/      # Local infrastructure configuration
├── .gitignore
└── README.md