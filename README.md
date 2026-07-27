# RLM-SECURE

Security validation service for the RLM ecosystem.

- Port: `8797`
- Role: security pattern validation, PES
- Stack: Flask + SQLite (future state persistence)

## Endpoints

| Method | Path       | Purpose                       |
|--------|------------|-------------------------------|
| GET    | /health    | Liveness check                |
| GET    | /metrics   | Validation counts             |
| POST   | /vote      | Record a vote                 |
| POST   | /validate  | Validate a target for security issues |
| GET    | /status    | Service status                |

## Run

```powershell
python src/app.py
```

## Test

```powershell
pytest tests/test_app.py -q
```

## Archi notes

- MVP: simple static checks on /validate input
- Next: integrate with KIX for runner credential scanning, BDCP mode checks
