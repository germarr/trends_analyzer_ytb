
def pull_channel_videos(channel_id: str, video_type: str = "videos", max_videos: int = 50) -> Dict:
    """
    Pull videos from a channel and store them in the database.
    
    Args:
        channel_id: YouTube channel ID
        video_type: Type of videos to pull ("videos", "shorts", "live")
        max_videos: Maximum number of videos to pull
        
    Returns:
        Dict with success status and statistics
    """
    try:
        # Get channel details first
        with Session(engine) as session:
            channel = session.exec(
                select(DIMChannel).where(DIMChannel.channelid == channel_id)
            ).first()
            
            if not channel:
                return {"success": False, "error": "Channel not found in database"}
        
        # Determine playlist ID based on video type
        playlist_mapping = {
            "videos": channel.uploadid_videos,
            "shorts": channel.uploadid_shorts,
            "live": channel.uploadid_live_videos
        }
        
        playlist_id = playlist_mapping.get(video_type)
        if not playlist_id:
            return {"success": False, "error": f"Invalid video type: {video_type}"}
        
        # Get videos from playlist
        videos, api_calls = get_videos_from_playlist(playlist_id, max_videos)
        
        if not videos:
            return {"success": False, "error": "No videos found in playlist"}
        
        # Get video IDs and fetch statistics in chunks
        video_ids = [video["videoid"] for video in videos]
        video_chunks = chunk_list(video_ids, 50)
        
        all_video_stats = []
        for chunk in video_chunks:
            stats = get_video_statistics(chunk)
            all_video_stats.extend(stats)
        
        # Process and store videos in database
        videos_added = 0
        videos_updated = 0
        
        with Session(engine) as session:
            for video_stat in all_video_stats:
                # Check if video already exists
                existing_video = session.exec(
                    select(ChannelVideos).where(ChannelVideos.videoid == video_stat["videoid"])
                ).first()
                
                if existing_video:
                    videos_updated += 1
                    continue
                
                # Add video type
                video_stat["typeofvideo"] = video_type
                
                # Create video record using ChannelVideos model
                video_record = ChannelVideos(
                    videoid=video_stat["videoid"],
                    title=video_stat["title"],
                    description=video_stat["description"],
                    thumbnails=video_stat["thumbnails"],
                    video_type=video_stat["typeofvideo"],
                    publishedat=datetime.fromisoformat(video_stat["publishedat"].replace('Z', '+00:00')),
                    categoryid=video_stat["categoryid"],
                    viewcount=video_stat["viewcount"],
                    duration=video_stat["duration"],
                    likecount=video_stat["likecount"],
                    favoritecount=video_stat["favoritecount"],
                    commentcount=video_stat["commentcount"]
                )
                
                session.add(video_record)
                videos_added += 1
            
            session.commit()
        
        return {
            "success": True,
            "message": f"Successfully processed {len(all_video_stats)} videos",
            "videos_added": videos_added,
            "videos_updated": videos_updated,
            "api_calls_used": api_calls + len(video_chunks),
            "channel_name": channel.channeltitle
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error pulling videos: {str(e)}"}

def get_all_channels() -> List[Dict]:
    """Get all channels from the database."""
    try:
        with Session(engine) as session:
            channels = session.exec(select(DIMChannel)).all()
            return [
                {
                    "channelid": channel.channelid,
                    "channeltitle": channel.channeltitle,
                    "channeldescription": channel.channeldescription,
                    "customurl": channel.customurl,
                    "thumbnail": channel.thumbnail,
                    "country": channel.country,
                    "viewcount": channel.viewcount,
                    "subscribercount": channel.subscribercount,
                    "videocount": channel.videocount,
                    "publishedat": channel.publishedat.isoformat() if channel.publishedat else None
                }
                for channel in channels
            ]
    except Exception as e:
        print(f"Error getting channels: {e}")
        return []

def add_channel_to_database(youtube_url: str) -> Dict:
    """
    Add a new channel to the database from a YouTube URL.
    
    Args:
        youtube_url: YouTube video URL to extract channel from
        
    Returns:
        Dict with success status and message
    """
    try:
        # Extract video ID from URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return {"success": False, "error": "Invalid YouTube URL"}
        
        # Get channel ID from video
        channel_info = get_channel_id_from_video(video_id)
        if not channel_info["success"]:
            return channel_info
        
        channel_id = channel_info["channelid"]
        
        # Get complete channel details
        channel_details = get_channel_details(channel_id)
        if not channel_details["success"]:
            return channel_details
        
        # Check if channel already exists
        with Session(engine) as session:
            existing_channel = session.exec(
                select(DIMChannel).where(DIMChannel.channelid == channel_id)
            ).first()
            
            if existing_channel:
                return {
                    "success": False, 
                    "error": f"Channel '{channel_details['channeltitle']}' already exists in database"
                }
            
            # Create new channel record
            new_channel = DIMChannel(**channel_details)
            session.add(new_channel)
            session.commit()
            
            return {
                "success": True,
                "message": f"Channel '{channel_details['channeltitle']}' added successfully",
                "channel_id": channel_id,
                "channel_name": channel_details['channeltitle']
            }
            
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
