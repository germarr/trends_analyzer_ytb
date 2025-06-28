from sqlmodel import DateTime, Field, SQLModel,select, delete,create_engine
import uuid as uuid_pkg
from typing import List, Optional,Set
from pytz import timezone
from sqlalchemy import Column
from sqlalchemy.types import Text, DateTime,String
import datetime
from sqlmodel import Session
from sqlalchemy import BigInteger
import os
import pandas as pd 

from dotenv import load_dotenv
load_dotenv()

# SQLite database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH')

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

def setupConnection(database_path=DATABASE_PATH):
    db_url = f'sqlite:///{database_path}'
    return db_url

def create_db_and_tables(e):
    SQLModel.metadata.create_all(e)

