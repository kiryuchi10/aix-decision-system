# Supplement documentation

This folder contains design and requirements supplements. **Do not put credentials, API keys, or deployment secrets in any file here.**

| Document | Description |
|----------|-------------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Product requirements (Dashboard, FDC, DoE, ML Pipeline, etc.) |
| [DESIGN.md](DESIGN.md) | Architecture, API, data models, DB schema, deployment |
| [TASKS.md](TASKS.md) | Implementation plan and phases |
| [INTERLOCK_GLOSSARY_AND_MODEL_SPEC.md](INTERLOCK_GLOSSARY_AND_MODEL_SPEC.md) | Interlock terminology and model spec |

For setup and usage, see the root [README.md](../README.md).  
Database schema: [backend/schema.sql](../backend/schema.sql).  
Environment variables: use `.env` locally (never committed); copy from `.env.example` in backend/frontend if provided.
