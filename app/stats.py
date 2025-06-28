import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, func
from models import ChannelVideos, DIMChannel, setupConnection, create_engine
from typing import Dict, List, Any
import datetime
from collections import defaultdict
import calendar

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

def get_channel_upload_timeline(channel_id: str) -> Dict[str, Any]:
    """Get monthly upload timeline for charts"""
    with Session(engine) as session:
        videos = session.exec(
            select(ChannelVideos.publishedat)
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.publishedat.isnot(None))
        ).all()
        
        monthly_counts = defaultdict(int)
        for video_date in videos:
            if video_date:
                month_key = video_date.strftime('%Y-%m')
                monthly_counts[month_key] += 1
        
        sorted_months = sorted(monthly_counts.keys())
        
        return {
            "labels": [datetime.datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in sorted_months],
            "data": [monthly_counts[month] for month in sorted_months]
        }

def get_video_duration_distribution(channel_id: str) -> Dict[str, Any]:
    """Get video duration distribution for histogram"""
    with Session(engine) as session:
        durations = session.exec(
            select(ChannelVideos.duration)
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.duration > 0)
        ).all()
        
        duration_ranges = {
            "0-2 min": 0,
            "2-5 min": 0,
            "5-10 min": 0,
            "10-20 min": 0,
            "20+ min": 0
        }
        
        for duration in durations:
            duration_min = duration / 60
            if duration_min <= 2:
                duration_ranges["0-2 min"] += 1
            elif duration_min <= 5:
                duration_ranges["2-5 min"] += 1
            elif duration_min <= 10:
                duration_ranges["5-10 min"] += 1
            elif duration_min <= 20:
                duration_ranges["10-20 min"] += 1
            else:
                duration_ranges["20+ min"] += 1
        
        return {
            "labels": list(duration_ranges.keys()),
            "data": list(duration_ranges.values())
        }

def get_engagement_metrics(channel_id: str) -> Dict[str, Any]:
    """Get engagement metrics for charts"""
    with Session(engine) as session:
        videos = session.exec(
            select(ChannelVideos.viewcount, ChannelVideos.likecount, ChannelVideos.commentcount)
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.viewcount > 0)
        ).all()
        
        engagement_data = []
        for video in videos:
            if video[0] > 0:  # viewcount > 0
                like_rate = (video[1] / video[0]) * 100 if video[1] else 0
                comment_rate = (video[2] / video[0]) * 100 if video[2] else 0
                engagement_data.append({
                    "views": video[0],
                    "like_rate": round(like_rate, 2),
                    "comment_rate": round(comment_rate, 2)
                })
        
        return {"engagement_data": engagement_data}

def get_top_channels_comparison() -> Dict[str, Any]:
    """Get top channels data for comparison charts"""
    with Session(engine) as session:
        top_channels = session.exec(
            select(DIMChannel.channeltitle, DIMChannel.subscribercount, DIMChannel.viewcount, DIMChannel.videocount)
            .where(DIMChannel.success == True)
            .order_by(DIMChannel.subscribercount.desc())
            .limit(10)
        ).all()
        
        return {
            "labels": [channel[0][:20] + "..." if len(channel[0]) > 20 else channel[0] for channel in top_channels],
            "subscriber_data": [channel[1] for channel in top_channels],
            "view_data": [channel[2] for channel in top_channels],
            "video_data": [channel[3] for channel in top_channels]
        }

def get_channels_scatter_data() -> Dict[str, Any]:
    """Get scatter plot data for channels"""
    with Session(engine) as session:
        channels = session.exec(
            select(DIMChannel.channeltitle, DIMChannel.subscribercount, DIMChannel.viewcount)
            .where(DIMChannel.success == True)
            .where(DIMChannel.subscribercount > 0)
            .where(DIMChannel.viewcount > 0)
        ).all()
        
        scatter_data = [
            {
                "x": channel[1],  # subscribers
                "y": channel[2],  # views
                "label": channel[0][:15] + "..." if len(channel[0]) > 15 else channel[0]
            }
            for channel in channels
        ]
        
        return {"scatter_data": scatter_data}

def get_video_performance_trends(channel_id: str) -> Dict[str, Any]:
    """Get video performance trends over time"""
    with Session(engine) as session:
        videos = session.exec(
            select(ChannelVideos.publishedat, ChannelVideos.viewcount, ChannelVideos.likecount)
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.publishedat.isnot(None))
            .order_by(ChannelVideos.publishedat)
        ).all()
        
        trend_data = []
        for video in videos:
            if video[0]:  # publishedat exists
                trend_data.append({
                    "date": video[0].strftime('%Y-%m-%d'),
                    "views": video[1],
                    "likes": video[2]
                })
        
        return {"trend_data": trend_data}

def get_upload_frequency_analysis(channel_id: str) -> Dict[str, Any]:
    """Get upload frequency by day of week"""
    with Session(engine) as session:
        videos = session.exec(
            select(ChannelVideos.publishedat)
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.publishedat.isnot(None))
        ).all()
        
        day_counts = defaultdict(int)
        for video_date in videos:
            if video_date:
                day_name = calendar.day_name[video_date.weekday()]
                day_counts[day_name] += 1
        
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            "labels": days_order,
            "data": [day_counts[day] for day in days_order]
        }

def get_view_distribution_by_video_type(channel_id: str) -> Dict[str, Any]:
    """Get view distribution by video type over time (dates as x-axis, stacked by type)"""
    with Session(engine) as session:
        # Group by date (month) and video_type
        results = session.exec(
            select(
                func.strftime('%Y-%m', ChannelVideos.publishedat),
                ChannelVideos.video_type,
                func.sum(ChannelVideos.viewcount)
            )
            .where(ChannelVideos.channelid == channel_id)
            .where(ChannelVideos.publishedat.isnot(None))
            .where(ChannelVideos.viewcount > 0)
            .group_by(func.strftime('%Y-%m', ChannelVideos.publishedat), ChannelVideos.video_type)
            .order_by(func.strftime('%Y-%m', ChannelVideos.publishedat))
        ).all()

        if not results:
            return {"labels": [], "datasets": []}

        # Build a set of all months and all video types
        months = sorted(set(row[0] for row in results))
        types = sorted(set(row[1] if row[1] != 'No Information' else 'Other' for row in results))

        # Build a mapping: {type: {month: views}}
        data_map = {t: {m: 0 for m in months} for t in types}
        for month, vtype, views in results:
            t = vtype if vtype != 'No Information' else 'Other'
            data_map[t][month] = views

        # Prepare datasets for Chart.js
        color_palette = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#C9CBCF', '#4BC0C0', '#36A2EB', '#1976d2'
        ]
        datasets = []
        for idx, t in enumerate(types):
            datasets.append({
                "label": t,
                "data": [data_map[t][m] for m in months],
                "backgroundColor": color_palette[idx % len(color_palette)]
            })

        return {
            "labels": months,
            "datasets": datasets
        }