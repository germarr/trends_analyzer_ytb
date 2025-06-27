# YouTube Trends Tracker

A Python application for analyzing YouTube channel performance and video metrics with both programmatic API and web interface.

## Features

- **Channel Discovery**: Extract channel information from any YouTube video URL
- **Video Analytics**: Fetch detailed statistics for videos, shorts, and live streams
- **Data Storage**: Store all data in SQLite database for persistent analysis
- **Web Interface**: FastAPI-powered web application for easy channel analysis
- **Video Type Classification**: Automatically categorize content as videos, shorts, or live streams
- **Comprehensive Metrics**: Track views, likes, comments, duration, and more
- **Batch Processing**: Efficiently process large amounts of video data

## Tech Stack

- **Python 3.10+**
- **FastAPI** - Web framework for the user interface
- **SQLModel** - Database ORM with Pydantic integration
- **Google API Client** - YouTube Data API v3 integration
- **SQLite** - Database storage
- **Pandas** - Data manipulation and analysis
- **Jinja2** - HTML templating

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ytb_trends
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up your environment variables:
```bash
# Create a .env file with your YouTube API key
youtube_key=YOUR_YOUTUBE_API_KEY
```

## Usage

### Web Interface

Start the FastAPI application:
```bash
cd app
uvicorn main:app --reload
```

Visit `http://localhost:8000` to access the web interface where you can:
- Submit YouTube video URLs to analyze channels
- View channel statistics and video metrics
- Browse stored channel data

### Programmatic Usage

```python
from functions import extract_video_id, get_channel_id_from_video, store_channel_and_videos_data

# Extract video ID from URL
video_id = extract_video_id("https://www.youtube.com/watch?v=VIDEO_ID")

# Get channel information
channel_info = get_channel_id_from_video(video_id)

# Store comprehensive channel and video data
data = store_channel_and_videos_data(channel_info["channel_id"], max_videos=200)
```

## Database Schema

### DIMChannel Table
- Channel metadata (ID, title, description, subscriber count, etc.)
- Upload playlist IDs for different content types
- Channel statistics and thumbnails

### ChannelVideos Table
- Video details (ID, title, description, thumbnails)
- Performance metrics (views, likes, comments)
- Video metadata (duration, category, publication date)
- Video type classification

## Data Analysis

The project includes Marimo notebooks in the `notebooks/` directory for data analysis and visualization of the collected YouTube metrics.

## API Limits

- YouTube Data API v3 has daily quotas
- The application implements efficient batching (50 videos per API call)
- Monitor your API usage through the Google Cloud Console

## Project Structure

```
ytb_trends/
├── app/                    # FastAPI web application
│   ├── main.py            # Web app entry point
│   ├── stats.py           # Statistics utilities
│   ├── templates/         # HTML templates
│   └── static/           # CSS and static assets
├── functions.py          # Core YouTube API functions
├── models.py            # SQLModel database schemas
├── notebooks/           # Data analysis notebooks
├── main.py             # CLI entry point
└── pyproject.toml      # Project configuration
```

## License

This project is open source and available under the MIT License.

---

**Note**: Remember to respect YouTube's Terms of Service and API usage policies when using this tool.