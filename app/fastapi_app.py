"""FastAPI web app for the Simpsons episode recommender UI."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import recommendation_algorithms
from app import recommender_db


app = FastAPI(title="Simpsons Episode Recommender")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def login_get(request: Request):
    """Render login page or redirect to recommendations if user is already set."""
    username = request.cookies.get("username")
    if username:
        return RedirectResponse(url="/recommendations", status_code=303)

    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/")
async def login_post(request: Request):
    """Create user from login form and store username in cookie."""
    form = await request.form()
    username = str(form.get("username", "")).strip()

    if not username:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Username is required."},
            status_code=400,
        )

    recommender_db.create_user(username)
    response = RedirectResponse(url="/recommendations", status_code=303)
    response.set_cookie("username", username)
    return response


@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations_get(request: Request):
    """Show recommendation cards for the active user."""
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=303)

    episode_names = recommendation_algorithms.top8_recommendation(username)
    episodes = []
    for episode_name in episode_names:
        episode = dict(recommender_db.get_episode(episode_name))
        episodes.append(episode)

    cant_valorados = len(recommender_db.get_reviews(username))
    cant_ignorados = len(recommender_db.get_ignored_episodes(username))

    return templates.TemplateResponse(
        "recommendations.html",
        {
            "request": request,
            "episodes": episodes,
            "username": username,
            "cant_valorados": cant_valorados,
            "cant_ignorados": cant_ignorados,
        },
    )


@app.post("/recommendations", response_class=HTMLResponse)
async def recommendations_post(request: Request):
    """Save submitted ratings and return a refreshed recommendations page."""
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=303)

    form = await request.form()
    for episode_name, rating_value in form.items():
        rating = int(rating_value)
        recommender_db.insert_reviews(username, episode_name, rating)

    episode_names = recommendation_algorithms.top8_recommendation(username)
    episodes = []
    for episode_name in episode_names:
        episode = dict(recommender_db.get_episode(episode_name))
        episodes.append(episode)

    cant_valorados = len(recommender_db.get_reviews(username))
    cant_ignorados = len(recommender_db.get_ignored_episodes(username))

    return templates.TemplateResponse(
        "recommendations.html",
        {
            "request": request,
            "episodes": episodes,
            "username": username,
            "cant_valorados": cant_valorados,
            "cant_ignorados": cant_ignorados,
        },
    )


@app.get("/reset")
async def reset(request: Request):
    """Clear all saved reviews for the current user."""
    username = request.cookies.get("username")
    if username:
        recommender_db.reset_user(username)

    return RedirectResponse(url="/recommendations", status_code=303)


@app.get("/change-user")
async def change_user():
    """Remove username cookie and return to login page."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("username")
    return response