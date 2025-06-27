import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, func
from models import ChannelVideos, DIMChannel, setupConnection, create_engine
from typing import Dict, List, Any
import datetime

DATABASE_PATH = "C:\\Users\\gerym\\Documents\\ytb_trends\\channel.db"
engine = create_engine(setupConnection(DATABASE_PATH))

def get_channel_video_statistics(channel_id: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a channel's videos"""
    with Session(engine) as session:
        # Basic counts and totals
        total_videos = session.exec(
            select(func.count(ChannelVideos.videoid))
            .where(ChannelVideos.channelid == channel_id)
        ).first()
        
        total_views = session.exec(
            select(func.sum(ChannelVideos.viewcount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        total_likes = session.exec(
            select(func.sum(ChannelVideos.likecount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        total_comments = session.exec(
            select(func.sum(ChannelVideos.commentcount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        # Average statistics
        avg_views = session.exec(
            select(func.avg(ChannelVideos.viewcount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        avg_likes = session.exec(
            select(func.avg(ChannelVideos.likecount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        avg_comments = session.exec(
            select(func.avg(ChannelVideos.commentcount))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        avg_duration = session.exec(
            select(func.avg(ChannelVideos.duration))
            .where(ChannelVideos.channelid == channel_id)
        ).first() or 0
        
        # Top performing videos
        top_videos_by_views = session.exec(
            select(ChannelVideos)
            .where(ChannelVideos.channelid == channel_id)
            .order_by(ChannelVideos.viewcount.desc())
            .limit(5)
        ).all()
        
        top_videos_by_likes = session.exec(
            select(ChannelVideos)
            .where(ChannelVideos.channelid == channel_id)
            .order_by(ChannelVideos.likecount.desc())
            .limit(5)
        ).all()
        
        # Video type distribution
        video_types = session.exec(
            select(ChannelVideos.video_type, func.count(ChannelVideos.videoid))
            .where(ChannelVideos.channelid == channel_id)
            .group_by(ChannelVideos.video_type)
        ).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        recent_videos = session.exec(
            select(func.count(ChannelVideos.videoid))
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.publishedat >= thirty_days_ago)
        ).first() or 0
        
        # Get channel info
        channel_info = session.exec(
            select(DIMChannel)
            .where(DIMChannel.channelid == channel_id)
        ).first()
        
        return {
            "channel_info": channel_info,
            "total_videos": total_videos or 0,
            "total_views": int(total_views),
            "total_likes": int(total_likes),
            "total_comments": int(total_comments),
            "avg_views": round(avg_views, 2) if avg_views else 0,
            "avg_likes": round(avg_likes, 2) if avg_likes else 0,
            "avg_comments": round(avg_comments, 2) if avg_comments else 0,
            "avg_duration": round(avg_duration / 60, 2) if avg_duration else 0,  # Convert to minutes
            "top_videos_by_views": top_videos_by_views,
            "top_videos_by_likes": top_videos_by_likes,
            "video_types": dict(video_types) if video_types else {},
            "recent_videos": recent_videos
        }

def get_all_channels_with_video_count() -> List[Dict[str, Any]]:
    """Get all channels with their video counts for statistics overview"""
    with Session(engine) as session:
        channels_with_counts = session.exec(
            select(
                DIMChannel.channelid,
                DIMChannel.channeltitle,
                DIMChannel.subscribercount,
                DIMChannel.viewcount,
                func.count(ChannelVideos.videoid).label('video_count')
            )
            .outerjoin(ChannelVideos, DIMChannel.channelid == ChannelVideos.channelid)
            .group_by(DIMChannel.channelid)
        ).all()
        
        return [
            {
                "channelid": row[0],
                "channeltitle": row[1],
                "subscribercount": row[2],
                "viewcount": row[3],
                "video_count": row[4]
            }
            for row in channels_with_counts
        ]