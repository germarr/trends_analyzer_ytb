import marimo

__generated_with = "0.14.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return


@app.cell
def _():
    from sqlmodel import SQLModel, Field, create_engine, Session
    from functions import extract_video_id, get_channel_id_from_video, get_channel_details, get_videos_from_playlist, iso8601_to_seconds,get_video_statistics,chunk_list
    import pandas as pd
    import duckdb
    import sqlite3
    import datetime
    return (
        chunk_list,
        duckdb,
        get_channel_details,
        get_video_statistics,
        get_videos_from_playlist,
        pd,
        sqlite3,
    )


app._unparsable_cell(
    r"""
    DATABASE_URL = \"C:\Users\gerym\Documents\ytb_trends\channel_app.db\"
    conn = duckdb.connect(DATABASE_URL, read_only=False)
    """,
    name="_"
)


@app.cell
def _(sqlite3):
    # Create a database connection and a new .db file
    connection = sqlite3.connect('C:\\Users\\gerym\\Documents\\ytb_trends\\channel_app.db')

    # Optionally, create a cursor object to execute SQL commands
    cursor = connection.cursor()

    # Create an empty table named 'main'
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS main (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        value REAL
    )
    ''')

    # Commit changes and close the connection
    connection.commit()
    connection.close()
    return


@app.cell
def _(get_channel_details):
    channelid = 'UC3aj05GEEyzdOqYM5FLSFeg'

    channel_details = get_channel_details(channelid)
    return channel_details, channelid


@app.cell
def _(channel_details, conn, duckdb, pd):
    channel_df = pd.DataFrame([channel_details])
    channel_df['publishedat'] = pd.to_datetime(channel_df['publishedat'])

    channel_exists_in_db = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'dim_channel'"
        ).fetchone()[0] > 0

    if not channel_exists_in_db:
        # Create the dim_channel table
        conn.execute("""
            CREATE TABLE dim_channel AS 
            SELECT * FROM channel_df LIMIT 0
        """)
        conn.execute("INSERT INTO dim_channel SELECT * FROM channel_df")
        print(f"Channel added.")

    else:
        db_channel = conn.execute("SELECT DISTINCT channelid FROM dim_channel").df()
        # Check for new videos not in the database
        export_channel = duckdb.sql("""
            SELECT * 
            FROM channel_df
            LEFT JOIN db_channel ON channel_df.channelid = db_channel.channelid
            WHERE db_channel.channelid is NULL
        """).df()

        if not export_channel.empty:
            conn.execute("INSERT INTO dim_channel SELECT * FROM export_channel")
            print(f"Channel added.")
        else:
            print("Channel already in db.")
    return channel_df, db_channel


@app.cell
def _(channel_details):
    upload_id = channel_details["uploadid_videos"]
    upload_id_shorts = channel_details["uploadid_shorts"]
    upload_id_live = channel_details['uploadid_live_videos']
    return upload_id, upload_id_live, upload_id_shorts


@app.cell
def _(
    get_videos_from_playlist,
    pd,
    upload_id,
    upload_id_live,
    upload_id_shorts,
):
    videos, api_calls = get_videos_from_playlist(upload_id, max_results=200)
    videos_shorts, api_calls_shorts = get_videos_from_playlist(upload_id_shorts, max_results=200)
    videos_live, api_calls_live = get_videos_from_playlist(upload_id_live, max_results=200)

    def create_video_table(videos_list):
        return [pd.DataFrame([video]) for video in videos_list]

    video_table = pd.concat(create_video_table(videos))
    video_table['video_type'] = 'video'
    video_table_shorts = pd.concat(create_video_table(videos_shorts))
    video_table_shorts['video_type'] = 'short'
    video_table_live = pd.concat(create_video_table(videos_live))
    video_table_live['video_type'] = 'live'

    all_videos = pd.concat([video_table, video_table_shorts, video_table_live], ignore_index=True)
    return (all_videos,)


@app.cell
def _(all_videos, chunk_list):
    id_for_stats = chunk_list(all_videos['videoid'].to_list(), chunk_size = 50)
    return (id_for_stats,)


@app.cell
def _(get_video_statistics, id_for_stats, pd):
    stats_list = []

    for i,listOfIds in enumerate(id_for_stats):
        statsdf = get_video_statistics(listOfIds)
        stats_list.append(pd.DataFrame(statsdf))

    stats_from_all_videos_df = pd.concat(stats_list)
    return (stats_from_all_videos_df,)


@app.cell
def _(all_videos, channelid, duckdb, stats_from_all_videos_df):
    stats = duckdb.sql("""
    SELECT videoid, categoryid,viewcount,duration,likecount,favoritecount, commentcount
    FROM stats_from_all_videos_df 
    """)

    export_df = duckdb.sql(f"""
    SELECT all_videos.* EXCLUDE(publishedat),all_videos.publishedat::TIMESTAMP publishedat, stats.* EXCLUDE(videoid), '{channelid}' as channelid FROM all_videos 
    LEFT JOIN stats ON all_videos.videoid = stats.videoid
    """).df()
    return export_df, stats


@app.cell
def _(export_df):
    export_df.dtypes
    return


@app.cell
def _(conn, duckdb, export_df):
    table_exists = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'all_videos'"
        ).fetchone()[0] > 0

    if not table_exists:
        # Create the dim_channel table
        conn.execute("""
            CREATE TABLE all_videos AS 
            SELECT * FROM export_df LIMIT 0
        """)

        conn.execute("INSERT INTO all_videos SELECT * FROM export_df")
        print(f"{export_df['videoid'].count():,} videos added.")
    else:
        db_data = conn.execute("SELECT DISTINCT videoid FROM all_videos").df()
        # Check for new videos not in the database
        export_df_n = duckdb.sql("""
            SELECT * 
            FROM export_df
            LEFT JOIN db_data ON export_df.videoid = db_data.videoid
            WHERE db_data.videoid is NULL
        """).df()

        if not export_df_n.empty:
            conn.execute("INSERT INTO all_videos SELECT * FROM export_df_n")
            print(f"{export_df_n['videoid'].count():,} videos added.")
        else:
            print("No new videos to add.")

    return (db_data,)


@app.cell
def _(conn):
    conn.execute('FROM dim_channel').fetchall()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
