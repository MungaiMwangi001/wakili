from fastapi.middleware.cors import CORSMiddleware
import re

# ── CORS ──────────────────────────────────────────────────────────────────────
raw_origins = settings.ALLOWED_ORIGINS
origins = []
if isinstance(raw_origins, str):
    try:
        origins = json.loads(raw_origins)
    except json.JSONDecodeError:
        origins = [o.strip() for o in raw_origins.split(",") if o]
else:
    origins = raw_origins

def is_allowed_origin(origin: str) -> bool:
    if origin in origins:
        return True
    # Allow all Vercel preview deployments for this project
    if re.match(r"https://wakili-.*\.vercel\.app", origin):
        return True
    return False

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://wakili-.*\.vercel\.app",
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)