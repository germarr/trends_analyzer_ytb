import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from functions import extract_video_id, get_channel_id_from_video, store_channel_and_videos_data
from models import DIMChannel, setupConnection, create_db_and_tables
from sqlmodel import Session, create_engine, select
from .stats import get_channel_video_statistics

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Database setup
DATABASE_PATH = "C:\\Users\\gerym\\Documents\\ytb_trends\\channel.db"
engine = create_engine(setupConnection(DATABASE_PATH))
create_db_and_tables(engine)

def human_format(num):
    num = float(num)
    for unit in ['', 'K', 'M', 'B', 'T']:
        if abs(num) < 1000.0:
            return f"{num:.2f}{unit}"
        num /= 1000.0
    return f"{num:.2f}P"

templates.env.filters['human_format'] = human_format

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit_youtube_link(request: Request, youtube_url: str = Form(...)):
    video_id = extract_video_id(youtube_url)
    
    if not video_id:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "error": "Invalid YouTube URL. Please provide a valid YouTube video link."
        })
    
    channel_info = get_channel_id_from_video(video_id)
    
    if not channel_info["success"]:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "error": channel_info["error"]
        })
    
    # Use the new function to store channel and videos data in database
    result = store_channel_and_videos_data(channel_info["channelid"], max_videos=200)
    
    if not result["success"]:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "error": result["error"]
        })
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "video_info": channel_info,
        "channel_info": result["channel_info"],
        "youtube_url": youtube_url,
        "videos": result["videos"],
        "total_videos": result["total_videos"],
        "api_calls_used": result["api_calls_used"],
        "database_stats": result["database_stats"]
    })

@app.get("/channels", response_class=HTMLResponse)
async def show_channels(request: Request):
    with Session(engine) as session:
        statement = select(DIMChannel)
        channels = session.exec(statement).all()
    
    return templates.TemplateResponse("channels.html", {
        "request": request,
        "channels": channels,
        "total_channels": len(channels)
    })

@app.get("/statistics/{channel_id}", response_class=HTMLResponse)
async def show_channel_statistics(request: Request, channel_id: str):
    stats = get_channel_video_statistics(channel_id)
    
    if not stats["channel_info"]:
        return templates.TemplateResponse("results.html", {
            "request": request,
            "error": "Channel not found in database."
        })
    
    return templates.TemplateResponse("statistics.html", {
        "request": request,
        "stats": stats
    })