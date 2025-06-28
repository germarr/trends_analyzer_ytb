"""
Simplified YouTube API functions for FastAPI integration.
Contains essential functions for adding channels and pulling YouTube data.
"""

import re
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from googleapiclient.discovery import build
from sqlmodel import Session, select, delete, create_engine, SQLModel
from models import (
    DIMChannel, ChannelVideos
)
from dotenv import load_dotenv
from dateutil import parser
load_dotenv()

# YouTube API setup
youtube_key = os.getenv('youtube_key')
youtube = build('youtube', 'v3', developerKey=youtube_key)

# SQLite database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH')
CONNECTION_STRING = f'sqlite:///{DATABASE_PATH}'

def create_db_and_tables(e):
    SQLModel.metadata.create_all(e)

engine = create_engine(CONNECTION_STRING, echo=False)
create_db_and_tables(engine)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL (regular and shorts)."""
    videoid = re.search(r"(?:v=|\/shorts\/)([^&\/]+)", url)
    if videoid:
        return videoid.group(1)
    return None


def get_channel_id_from_video(video_id: str) -> Dict:
    """Get channel ID and basic info from a video ID."""
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if "items" in response and len(response["items"]) > 0:
            snippet = response["items"][0]["snippet"]
            stats = response["items"][0]["statistics"]
            
            return {
                "channelid": snippet["channelId"],
                "video_title": snippet["title"],
                "channel_name": snippet["channelTitle"],
                "view_count": stats.get("viewCount", 0),
                "success": True
            }
        else:
            return {"success": False, "error": "Video not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_channel_details(channel_id: str) -> Dict:
    """Get complete channel details from YouTube API."""
    try:
        request = youtube.channels().list(
            part="contentDetails,statistics,snippet",
            id=channel_id
        )
        response = request.execute()
        
        if "items" in response and len(response["items"]) > 0:
            item = response["items"][0]
            snippet = item["snippet"]
            stats = item["statistics"]
            content_details = item["contentDetails"]
            
            # Get upload playlist IDs
            uploads_playlist_id = content_details["relatedPlaylists"]["uploads"]
            
            return {
                "channelid": channel_id,
                "channeltitle": snippet["title"],
                "channeldescription": snippet.get("description", ""),
                "customurl": snippet.get("customUrl", ""),
                "publishedat": snippet["publishedAt"],
                "thumbnail": snippet["thumbnails"]["default"]["url"],
                "country": snippet.get("country", ""),
                "viewcount": int(stats["viewCount"]),
                "subscribercount": int(stats["subscriberCount"]),
                "videocount": int(stats["videoCount"]),
                "uploadid": uploads_playlist_id,
                "uploadid_videos": "UULF" + uploads_playlist_id[2:],
                "uploadid_shorts": "UUSH" + uploads_playlist_id[2:],
                "uploadid_live_videos": "UULV" + uploads_playlist_id[2:],
                "success": True
            }
        else:
            return {"success": False, "error": "Channel not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_videos_from_playlist(playlist_id: str, max_results: int = 50) -> Tuple[List[Dict], int]:
    """Get videos from a YouTube playlist with pagination."""
    videos = []
    api_calls = 0
    
    try:
        next_page_token = None
        total_fetched = 0
        
        while total_fetched < max_results:
            api_calls += 1
            remaining = max_results - total_fetched
            page_size = min(50, remaining)  # YouTube API max is 50 per page
            
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=page_size,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response["items"]:
                video_data = {
                    "videoid": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "publishedat": item["snippet"]["publishedAt"],
                    "description": item["snippet"]["description"],
                    "thumbnails": item["snippet"]["thumbnails"]["default"]["url"],
                }
                videos.append(video_data)
                total_fetched += 1

            next_page_token = response.get("nextPageToken")
            if not next_page_token or total_fetched >= max_results:
                break
                
        return videos, api_calls
    except Exception as e:
        return [], api_calls


def chunk_list(elements: List, chunk_size: int = 50) -> List[List]:
    """Break list into chunks for batch processing."""
    return [elements[i:i + chunk_size] for i in range(0, len(elements), chunk_size)]


def iso8601_to_seconds(duration: str) -> int:
    """Convert YouTube's ISO8601 duration to seconds."""
    if duration is None:
        return 0
    hours = minutes = seconds = 0
    match = re.match(r'PT((\d+)H)?((\d+)M)?((\d+)S)?', duration)
    if match:
        hours = int(match.group(2)) if match.group(2) else 0
        minutes = int(match.group(4)) if match.group(4) else 0
        seconds = int(match.group(6)) if match.group(6) else 0
    return hours * 3600 + minutes * 60 + seconds


def get_video_statistics(video_ids: List[str]) -> List[Dict]:
    """Get detailed statistics for a list of video IDs."""
    try:
        videoids_str = ','.join(video_ids)
        
        request = youtube.videos().list(
            part="statistics,snippet,contentDetails",
            id=videoids_str
        )
        response = request.execute()

        video_stats = []
        
        for item in response['items']:
            snippet = item['snippet']
            content_details = item['contentDetails']
            video_id = item['id']
            stats = item['statistics']

            # Handle tags safely
            tags = ",".join(snippet.get('tags', [])) if snippet.get('tags') else "No Tags"
            
            # Convert duration to seconds
            duration_seconds = iso8601_to_seconds(content_details.get('duration'))

            video_stats.append({
                'videoid': video_id,
                'publishedat': snippet['publishedAt'],
                'channelid': snippet['channelId'],
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'thumbnails': snippet['thumbnails']['default']['url'],
                'channeltitle': snippet['channelTitle'],
                'tags': tags,
                'categoryid': snippet.get('categoryId', ''),
                'viewcount': int(stats.get('viewCount', 0)),
                'duration': duration_seconds,
                'likecount': int(stats.get('likeCount', 0)),
                'favoritecount': int(stats.get('favoriteCount', 0)),
                'commentcount': int(stats.get('commentCount', 0))
            })

        return video_stats
    except Exception as e:
        print(f"Error getting video statistics: {e}")
        return []


def store_channel_and_videos_data(channel_id: str, max_videos: int = 200) -> Dict:
    """
    Store channel data and its videos in the database automatically.
    This function is called whenever channel data is requested from the FastAPI app.
    
    Args:
        channel_id: YouTube channel ID
        max_videos: Maximum number of videos to fetch per type (default 200)
        
    Returns:
        Dict with success status, channel info, videos, and statistics
    """
    try:
        # Get channel details from YouTube API
        channel_details = get_channel_details(channel_id)
        if not channel_details["success"]:
            return channel_details
        
        # Check if channel exists in database, if not add it
        with Session(engine) as session:
            existing_channel = session.exec(
                select(DIMChannel).where(DIMChannel.channelid == channel_id)
            ).first()
            
            if not existing_channel:
                # Create new channel record using DIMChannel model
                new_channel = DIMChannel(
                    channelid=channel_details["channelid"],
                    channeltitle=channel_details["channeltitle"],
                    channeldescription=channel_details["channeldescription"],
                    customurl=channel_details["customurl"],
                    publishedat=parser.isoparse(channel_details["publishedat"]),
                    thumbnail=channel_details["thumbnail"],
                    country=channel_details["country"],
                    viewcount=channel_details["viewcount"],
                    subscribercount=channel_details["subscribercount"],
                    videocount=channel_details["videocount"],
                    uploadid=channel_details["uploadid"],
                    uploadid_videos=channel_details["uploadid_videos"],
                    uploadid_shorts=channel_details["uploadid_shorts"],
                    uploadid_live_videos=channel_details["uploadid_live_videos"],
                    success=True
                )
                session.add(new_channel)
                session.commit()
                channel_added = True
            else:
                channel_added = False
        
        # Get videos from all playlists (videos, shorts, live)
        playlist_types = {
            "videos": channel_details["uploadid_videos"],
            "shorts": channel_details["uploadid_shorts"], 
            "live": channel_details["uploadid_live_videos"]
        }
        
        all_videos = []
        total_api_calls = 0
        videos_processed = {"added": 0, "updated": 0, "skipped": 0}
        
        # Fetch videos from each playlist type
        for video_type, playlist_id in playlist_types.items():
            videos, api_calls = get_videos_from_playlist(playlist_id, max_videos)
            total_api_calls += api_calls
            
            if videos:
                # Get video IDs and fetch detailed statistics
                video_ids = [video["videoid"] for video in videos]
                video_chunks = chunk_list(video_ids, 50)
                
                # Get detailed statistics for all videos
                for chunk in video_chunks:
                    stats = get_video_statistics(chunk)
                    total_api_calls += 1  # Each statistics call counts as 1 API call
                    
                    # Process each video with its statistics
                    for video_stat in stats:
                        video_stat["video_type"] = video_type
                        all_videos.append(video_stat)
        
        # Store videos in database
        with Session(engine) as session:
            for video_data in all_videos:
                # Check if video already exists
                existing_video = session.exec(
                    select(ChannelVideos).where(ChannelVideos.videoid == video_data["videoid"])
                ).first()
                
                if existing_video:
                    videos_processed["skipped"] += 1
                    continue
                
                try:
                    # Create video record using ChannelVideos model
                    video_record = ChannelVideos(
                        videoid=video_data["videoid"],
                        channelid=channel_details["channelid"],
                        title=video_data["title"],
                        description=video_data["description"],
                        thumbnails=video_data["thumbnails"],
                        video_type=video_data["video_type"],
                        publishedat=parser.isoparse(video_data["publishedat"]),
                        categoryid=video_data["categoryid"],
                        viewcount=video_data["viewcount"],
                        duration=video_data["duration"],
                        likecount=video_data["likecount"],
                        favoritecount=video_data["favoritecount"],
                        commentcount=video_data["commentcount"]
                    )
                    
                    session.add(video_record)
                    videos_processed["added"] += 1
                    
                except Exception as e:
                    print(f"Error processing video {video_data['videoid']}: {e}")
                    videos_processed["skipped"] += 1
                    continue
            
            session.commit()
        
        # Prepare response with channel info and basic video list for display
        display_videos = []
        for video in all_videos[:5]:  # Limit to first 50 for display
            display_videos.append({
                "videoid": video["videoid"],
                "title": video["title"],
                "publishedat": video["publishedat"],
                "description": video["description"][:100] + "..." if len(video["description"]) > 100 else video["description"],
                "thumbnails": video["thumbnails"],
                "video_type": video["video_type"]
            })
        
        return {
            "success": True,
            "channel_info": channel_details,
            "videos": display_videos,
            "total_videos": len(all_videos),
            "api_calls_used": total_api_calls,
            "database_stats": {
                "channel_added": channel_added,
                "videos_added": videos_processed["added"],
                "videos_skipped": videos_processed["skipped"]
            },
            "message": f"Successfully processed channel '{channel_details['channeltitle']}' with {len(all_videos)} videos"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error storing channel data: {str(e)}"}


def delete_channel_from_database(channel_id: str) -> Dict:
    """
    Delete a channel and all its associated videos from the database.
    
    Args:
        channel_id: YouTube channel ID to delete
        
    Returns:
        Dict with success status and message
    """
    try:
        with Session(engine) as session:
            # Check if channel exists
            channel = session.exec(
                select(DIMChannel).where(DIMChannel.channelid == channel_id)
            ).first()
            
            if not channel:
                return {"success": False, "error": "Channel not found"}
            
            channel_name = channel.channeltitle
            
            # Delete associated videos (fact and dimension tables)
            session.exec(delete(ChannelVideos).where(ChannelVideos.channelid == channel_id))
            session.exec(delete(DIMChannel).where(DIMChannel.channelid == channel_id))
            
            # Delete channel
            session.exec(delete(DIMChannel).where(DIMChannel.channelid == channel_id))
            
            session.commit()
            
            return {
                "success": True,
                "message": f"Channel '{channel_name}' and all associated videos deleted successfully"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error deleting channel: {str(e)}"}
    