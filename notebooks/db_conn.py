import marimo

__generated_with = "0.14.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from sqlmodel import SQLModel, Field, create_engine, Session
    import datetime
    from sqlalchemy import Column
    from sqlalchemy.types import DateTime
    from pytz import timezone
    from typing import List, Optional
    import duckdb
    return (
        Column,
        DateTime,
        Field,
        Optional,
        SQLModel,
        create_engine,
        datetime,
        duckdb,
    )


@app.cell
def _(Column, DateTime, Field, Optional, SQLModel, datetime):
    class DIMChannel(SQLModel, table=True):
        channelid: str = Field(primary_key=True)
        channeltitle: str = Field(default='No Information')
        channeldescription: str = Field(default='No Information')
        customurl: str = Field(default='No Information')
        publishedat: Optional[datetime.datetime] = Field(
            default=None,
            sa_column=Column(DateTime(timezone=True),default=datetime.datetime.now()
        ))
        thumbnail: str = Field(default='No Information')
        country: str = Field(default='No Information')
        viewcount: int = Field(default=0)
        subscribercount: int = Field(default=0)
        videocount: int = Field(default=0)
        uploadid: str = Field(default='No Information')
        uploadid_videos: str = Field(default='No Information')
        uploadid_shorts: str = Field(default='No Information')
        uploadid_live_videos: str = Field(default='No Information')
        success: bool = Field(default=False)


    return


@app.cell
def _(Column, DateTime, Field, Optional, SQLModel, datetime):
    class ChannelVideos(SQLModel, table=True):
        videoid: str = Field(default='No Information', primary_key=True)
        channelid:str= Field(default='No Information')
        title: str = Field(default='No Information')
        description: str = Field(default='No Information')
        thumbnails: str = Field(default='No Information')
        video_type: str = Field(default='No Information')
        publishedat: Optional[datetime.datetime] = Field(
            default=None,
            sa_column=Column(DateTime(timezone=True),default=datetime.datetime.now()
        ))
        categoryid: str = Field(default='No Information')
        viewcount: int = Field(default=0)
        duration: int = Field(default=0)
        likecount: int = Field(default=0)
        favoritecount: int = Field(default=0)
        commentcount: int = Field(default=0)


    return


@app.cell
def _(SQLModel, create_engine):
    # Database configuration
    DATABASE_URL = "sqlite:///C:\\Users\\gerym\\Documents\\ytb_trends\\channel.db"  # Change this to your DB URL

    def create_db_and_tables():
        engine = create_engine(DATABASE_URL)
        SQLModel.metadata.create_all(engine)

        return engine 

    conn = create_db_and_tables()

    return


@app.cell
def _(duckdb):
    abra = duckdb.connect('C:/Users/gerym/Documents/ytb_trends/channel.db')

    return (abra,)


@app.cell
def _(abra):
    abra.execute("""
    SELECT 
    """)
    return


@app.cell
def _(abra):
    abra.execute("""
    WITH base as (
    SELECT channelid, 
        video_type, 
        date_trunc('month', publishedat::DATE) as fdom,
        COUNT(videoid) as published_videos, 
        SUM(viewcount) total_views, 
        SUM(duration) total_duration, 
        SUM(likecount) total_likes, 
        SUM(commentcount) total_comments, 
        AVG(COUNT(videoid)) OVER() as avg_published_videos,
        AVG(viewcount) as avg_total_views,
        AVG(duration) avg_duration,
        AVG(likecount)  as avg_total_likes,
        AVG(commentcount) as avg_total_comments
    FROM channelvideos 
    GROUP BY 1, 2, 3
    )
    SELECT * 
    FROM base 
    WHERE video_type = 'videos'
    ORDER BY fdom DESC
    LIMIT 12
    """).df()
    return


@app.cell
def _(abra):
    abra.execute("""
    WITH base as (
    SELECT channelid, video_type, date_trunc('month', publishedat::DATE) as fdom,
        COUNT(videoid) as published_videos, 
        SUM(viewcount) viewcount, ROUND(MEDIAN(duration), 2) duration, SUM(likecount) likecount, SUM(commentcount) commentcount
        FROM channelvideos 
        GROUP BY 1, 2, 3
    ),
    rolling_avg AS (
        SELECT channelid, video_type, fdom,
               viewcount,
               ROUND(AVG(viewcount) OVER (PARTITION BY video_type ORDER BY fdom ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS rolling_viewcount
        FROM base
    ),
    std_dev AS (
        SELECT 
            channelid, 
            video_type, 
            fdom,
            viewcount,
            rolling_viewcount,
            ROUND(STDDEV(viewcount) OVER (PARTITION BY video_type), 2) AS global_std_deviation,
            ROUND(STDDEV(viewcount) OVER (PARTITION BY video_type, date_trunc('year', fdom)), 2) + 1 AS yearly_std_deviation
        FROM rolling_avg
    )

    SELECT dimchannel.channeltitle, std_dev.*
    FROM std_dev
    LEFT JOIN dimchannel ON std_dev.channelid = dimchannel.channelid
    WHERE video_type = 'videos'
    ORDER BY fdom DESC

    """).df()
    return


@app.cell
def _(abra):
    abra.execute("""SELECT channeltitle, channelid FROM dimchannel""").df()
    return


@app.cell
def _():
    return


@app.cell
def _(abra):
    abra.execute("""with base as (SELECT channelid, video_type, date_trunc('month', publishedat::DATE) as fdom,
        COUNT(videoid) as published_videos, 
        SUM(viewcount) viewcount, ROUND(MEDIAN(duration), 2) duration, SUM(likecount) likecount, SUM(commentcount) commentcount
        FROM channelvideos
        GROUP BY 1, 2, 3)
    SELECT base.*, channeltitle
    FROM base
    LEFT JOIN dimchannel ON base.channelid = dimchannel.channelid
    WHERE base.channelid = 'UCarEovlrD9QY-fy-Z6apIDQ'
    """).df()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
