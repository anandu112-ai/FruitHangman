from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import random
import os

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

_state: dict = {
    "secret": "",
    "display": [],
    "chances": 6,
    "guessed": [],
    "active": False,
}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/start")
async def start():
    _state["secret"] = random.choice(WORDS)
    _state["display"] = ["_"] * len(_state["secret"])
    _state["chances"] = 6
    _state["guessed"] = []
    _state["active"] = True
    return JSONResponse({
        "display": _state["display"],
        "chance": _state["chances"],
        "length": len(_state["secret"]),
        "guessed": [],
    })


@app.get("/guess")
async def guess(letter: str = Query(..., min_length=1, max_length=1)):
    if not _state["active"]:
        raise HTTPException(status_code=400, detail="Start a game first")

    letter = letter.lower()

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

    if "_" not in _state["display"]:
        _state["active"] = False
        return JSONResponse({
            "result": "win",
            "word": _state["secret"],
            "display": _state["display"],
            "guessed": _state["guessed"],
        })

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


@app.get("/state")
async def get_state():
    if not _state["active"]:
        return JSONResponse({"active": False})
    return JSONResponse({
        "active": True,
        "display": _state["display"],
        "chance": _state["chances"],
        "guessed": _state["guessed"],
        "length": len(_state["secret"]),
    })


# Serve static files (index.html) — must be LAST
app.mount("/", StaticFiles(directory="static", html=True), name="static")
