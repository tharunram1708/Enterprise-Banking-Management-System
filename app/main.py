from time import monotonic

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import accounts, auth, branches, cards, customers, employees, loans, notifications, reports, security_ops, transactions
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limit_bucket: dict[str, list[float]] = {}


@app.middleware("http")
async def simple_rate_limiter(request: Request, call_next):
    ip_address = request.client.host if request.client else "unknown"
    now = monotonic()
    recent_requests = [seen_at for seen_at in rate_limit_bucket.get(ip_address, []) if now - seen_at < 60]

    if len(recent_requests) >= 120:
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Too many requests"})

    recent_requests.append(now)
    rate_limit_bucket[ip_address] = recent_requests
    return await call_next(request)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name}


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(customers.router, prefix=settings.api_v1_prefix)
app.include_router(accounts.router, prefix=settings.api_v1_prefix)
app.include_router(transactions.router, prefix=settings.api_v1_prefix)
app.include_router(loans.router, prefix=settings.api_v1_prefix)
app.include_router(cards.router, prefix=settings.api_v1_prefix)
app.include_router(branches.router, prefix=settings.api_v1_prefix)
app.include_router(employees.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(security_ops.router, prefix=settings.api_v1_prefix)
