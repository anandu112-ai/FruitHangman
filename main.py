from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import random

app = FastAPI(title="Word Puzzle API", version="2.0")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Static + Templates
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Word Bank
# -----------------------------
WORDS = [
    "mango", "apple", "orange", "banana", "guava",
    "cherry", "grape", "jackfruit", "kiwi", "papaya",
    "lychee", "coconut", "lemon", "peach",
    "plum", "berry", "melon", "pear", "fig"
]

# -----------------------------
# Game State
# -----------------------------
_state = {
    "secret": "",
    "display": [],
    "chances": 6,
    "guessed": [],
    "active": False,
}

# -----------------------------
# FRONTEND ROUTE
# -----------------------------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# -----------------------------
# API STATUS
# -----------------------------
@app.get("/api")
async def api():
    return {
        "status": "ok",
        "message": "Word Puzzle API v2"
    }

# -----------------------------
# START GAME
# -----------------------------
@app.get("/start")
async def start():

    secret = random.choice(WORDS)

    _state["secret"] = secret
    _state["display"] = ["_"] * len(secret)
    _state["chances"] = 6
    _state["guessed"] = []
    _state["active"] = True

    return JSONResponse({
        "display": _state["display"],
        "chance": _state["chances"],
        "length": len(secret),
        "guessed": [],
    })

# -----------------------------
# GUESS LETTER
# -----------------------------
@app.get("/guess")
async def guess(letter: str = Query(..., min_length=1, max_length=1)):

    if not _state["active"]:
        raise HTTPException(
            status_code=400,
            detail="Start a game first"
        )

    letter = letter.lower()

    # Already guessed
    if letter in _state["guessed"]:
        return JSONResponse({
            "display": _state["display"],
            "chance": _state["chances"],
            "guessed": _state["guessed"],
            "info": "already_guessed",
        })

    _state["guessed"].append(letter)

    hit = False

    for i, ch in enumerate(_state["secret"]):
        if ch == letter:
            _state["display"][i] = letter
            hit = True

    if not hit:
        _state["chances"] -= 1

    # WIN
    if "_" not in _state["display"]:
        _state["active"] = False

        return JSONResponse({
            "result": "win",
            "word": _state["secret"],
            "display": _state["display"],
            "guessed": _state["guessed"],
        })

    # LOSE
    if _state["chances"] <= 0:
        _state["active"] = False

        return JSONResponse({
            "result": "lose",
            "word": _state["secret"],
            "display": _state["display"],
            "guessed": _state["guessed"],
        })

    return JSONResponse({
        "display": _state["display"],
        "chance": _state["chances"],
        "guessed": _state["guessed"],
        "hit": hit,
    })

# -----------------------------
# GAME STATE
# -----------------------------
@app.get("/state")
async def state():

    if not _state["active"]:
        return JSONResponse({
            "active": False
        })

    return JSONResponse({
        "active": True,
        "display": _state["display"],
        "chance": _state["chances"],
        "guessed": _state["guessed"],
        "length": len(_state["secret"]),
    })