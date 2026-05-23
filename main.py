from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import random

app = FastAPI(title="WordCipher API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WORDS = [
    "mango", "apple", "orange", "banana", "guava",
    "cherry", "grape", "jackfruit", "kiwi", "papaya",
    "lychee", "coconut", "lemon", "peach",
    "plum", "berry", "melon", "pear", "fig"
]

# Per-session game state:  session_id -> game dict
_sessions: dict = {}

# Per-session scores:  session_id -> { wins, losses, streak }
_scores: dict = {}


def get_game(sid: str) -> dict:
    if sid not in _sessions:
        _sessions[sid] = {
            "secret": "",
            "display": [],
            "chances": 6,
            "guessed": [],
            "active": False,
        }
    return _sessions[sid]


def get_score(sid: str) -> dict:
    if sid not in _scores:
        _scores[sid] = {"wins": 0, "losses": 0, "streak": 0}
    return _scores[sid]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/start")
async def start(sid: str = Query(..., description="Session ID")):
    game = get_game(sid)
    game["secret"]  = random.choice(WORDS)
    game["display"] = ["_"] * len(game["secret"])
    game["chances"] = 6
    game["guessed"] = []
    game["active"]  = True
    return JSONResponse({
        "display": game["display"],
        "chance":  game["chances"],
        "length":  len(game["secret"]),
        "guessed": [],
    })


@app.get("/guess")
async def guess(
    sid:    str = Query(..., description="Session ID"),
    letter: str = Query(..., min_length=1, max_length=1),
):
    game = get_game(sid)
    if not game["active"]:
        raise HTTPException(status_code=400, detail="Start a game first")

    letter = letter.lower()

    if letter in game["guessed"]:
        return JSONResponse({
            "display": game["display"],
            "chance":  game["chances"],
            "guessed": game["guessed"],
            "info":    "already_guessed",
        })

    game["guessed"].append(letter)
    hit = False

    for i, ch in enumerate(game["secret"]):
        if ch == letter:
            game["display"][i] = letter
            hit = True

    if not hit:
        game["chances"] -= 1

    if "_" not in game["display"]:
        game["active"] = False
        score = get_score(sid)
        score["wins"]   += 1
        score["streak"] += 1
        return JSONResponse({
            "result":  "win",
            "word":    game["secret"],
            "display": game["display"],
            "guessed": game["guessed"],
            "score":   score,
        })

    if game["chances"] <= 0:
        game["active"] = False
        score = get_score(sid)
        score["losses"] += 1
        score["streak"]  = 0
        return JSONResponse({
            "result":  "lose",
            "word":    game["secret"],
            "display": game["display"],
            "guessed": game["guessed"],
            "score":   score,
        })

    return JSONResponse({
        "display": game["display"],
        "chance":  game["chances"],
        "guessed": game["guessed"],
        "hit":     hit,
    })


@app.get("/score")
async def score(sid: str = Query(..., description="Session ID")):
    return JSONResponse(get_score(sid))


@app.get("/state")
async def get_state(sid: str = Query(..., description="Session ID")):
    game = get_game(sid)
    if not game["active"]:
        return JSONResponse({"active": False})
    return JSONResponse({
        "active":  True,
        "display": game["display"],
        "chance":  game["chances"],
        "guessed": game["guessed"],
        "length":  len(game["secret"]),
    })


# Serve static files — must be LAST
app.mount("/", StaticFiles(directory="static", html=True), name="static")
