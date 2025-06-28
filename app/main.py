import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from functions import extract_video_id, get_channel_id_from_video, store_channel_and_videos_data
from models import DIMChannel, setupConnection, create_db_and_tables
from sqlmodel import Session, create_engine, select
from .stats import (
    get_channel_video_statistics, 
    get_channel_upload_timeline,
    get_video_duration_distribution,
    get_engagement_metrics,
    get_top_channels_comparison,
    get_channels_scatter_data,
    get_video_performance_trends,
    get_upload_frequency_analysis,
    get_view_distribution_by_video_type
)
from dotenv import load_dotenv
load_dotenv()



app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# SQLite database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH')
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

# Chart Data API Endpoints
@app.get("/api/channel/{channel_id}/upload-timeline")
async def get_upload_timeline_data(channel_id: str):
    """API endpoint for upload timeline chart data"""
    data = get_channel_upload_timeline(channel_id)
    return JSONResponse(content=data)

@app.get("/api/channel/{channel_id}/duration-distribution")
async def get_duration_distribution_data(channel_id: str):
    """API endpoint for duration distribution chart data"""
    data = get_video_duration_distribution(channel_id)
    return JSONResponse(content=data)

@app.get("/api/channel/{channel_id}/engagement-metrics")
async def get_engagement_metrics_data(channel_id: str):
    """API endpoint for engagement metrics chart data"""
    data = get_engagement_metrics(channel_id)
    return JSONResponse(content=data)

@app.get("/api/channel/{channel_id}/performance-trends")
async def get_performance_trends_data(channel_id: str):
    """API endpoint for performance trends chart data"""
    data = get_video_performance_trends(channel_id)
    return JSONResponse(content=data)

@app.get("/api/channel/{channel_id}/upload-frequency")
async def get_upload_frequency_data(channel_id: str):
    """API endpoint for upload frequency chart data"""
    data = get_upload_frequency_analysis(channel_id)
    return JSONResponse(content=data)

@app.get("/api/channels/comparison")
async def get_channels_comparison_data():
    """API endpoint for channels comparison chart data"""
    data = get_top_channels_comparison()
    return JSONResponse(content=data)

@app.get("/api/channels/scatter")
async def get_channels_scatter_chart_data():
    """API endpoint for channels scatter plot data"""
    data = get_channels_scatter_data()
    return JSONResponse(content=data)

@app.get("/api/channel/{channel_id}/view-distribution")
async def get_view_distribution_data(channel_id: str):
    """API endpoint for view distribution by video type chart data"""
    data = get_view_distribution_by_video_type(channel_id)
    return JSONResponse(content=data)