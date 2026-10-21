
Note for teammate : 
1.frontend is not specified in terms of functionality. This is only AI + Backend
2.SQLAlchemy / psycopg, statsmodels
SciPy
scikit-learn will be only used if necessary.

And importantly, these tools have different jobs:

Dagster     = data pipeline orchestration
LangGraph   = AI workflow orchestration
Pydantic    = contracts / structured schemas
Postgres    = canonical structured data
S3/MinIO    = raw immutable data
statsmodels = time-series mathematics
NetworkX    = dependency graph
GoRules     = deterministic business-policy enforcement
LangSmith   = AI tracing/evaluation/feedback
Evidently   = data-drift monitoring
FastAPI     = backend API
React       = presentation

DATA
Python
Polars
SQLAlchemy / psycopg
httpx
Unstructured
S3 / MinIO
PostgreSQL
Dagster

CONTRACTS
Pydantic
YAML / JSON

ANALYTICS
statsmodels
SciPy
scikit-learn
NetworkX
Custom Python

AGENTIC AI
LangGraph
LLM API
Pydantic structured output

GOVERNANCE
GoRules / ZenEngine

BACKEND
FastAPI

FRONTEND
React / Next.js

OBSERVABILITY
LangSmith

DATA DRIFT
Evidently