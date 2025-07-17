import psycopg
import pandas as pd
from test_getall_data import (
    search_bluesky_posts,
    collect_user_posts_to_dataframe,
    collect_single_post_to_dataframe
)

from dotenv import load_dotenv
import os

load_dotenv()

# Chargement de la variable d'environnement pour la connexion à la base de données
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is not set. Please set it in your .env file.")

# Fonction pour nettoyer les dates dans un DataFrame
def clean_dataframe_dates(df: pd.DataFrame, date_cols: list):
    # 1) Remplace toutes les chaînes vides par None
    df = df.replace({'': None})
    # 2) Tente de convertir en datetime, échoue → NaT
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    # 3) Remplace NaT par None
    return df.where(pd.notnull(df), None)

# Fonction pour insérer des posts de recherche Bluesky dans la base de données
def insert_bluesky_search_posts(query: str, limit: int = 100, lang: str = None):
    # 1) Collecte
    df = search_bluesky_posts(query, limit=limit, lang=lang)
    if df.empty:
        print("⚠️ Aucun post search à insérer.")
        return

    # 2) Mapping colonnes
    column_map = {
        "post_uri": "post_uri",
        "post_url": "post_url",
        "post_cid": "post_cid",
        "text": "text",
        "createdAt_post": "created_at_post",
        "indexedAt_post": "indexed_at_post",
        "embed": "embed",
        "likeCount": "like_count",
        "repostCount": "repost_count",
        "replyCount": "reply_count",
        "did": "did",
        "handle": "handle",
        "displayName": "display_name",
        "followersCount": "followers_count",
        "followsCount": "follows_count",
        "postsCount": "posts_count",
        "createdAt_profile": "created_at_profile",
        "indexedAt_profile": "indexed_at_profile",
        "viewer_muted": "viewer_muted",
        "viewer_following": "viewer_following",
        "viewer_blockedBy": "viewer_blocked_by",
        "collectedAt": "collected_at",
    }
    df.rename(columns=column_map, inplace=True)

    df = clean_dataframe_dates(df, [
        "created_at_post", "indexed_at_post",
        "created_at_profile", "indexed_at_profile",
        "collected_at"
    ])

    # 3) Insertion SQL
    sql = """
        INSERT INTO bluesky_search_posts (
            post_uri, post_url, post_cid, text,
            created_at_post, indexed_at_post, embed,
            like_count, repost_count, reply_count,
            did, handle, display_name,
            followers_count, follows_count, posts_count,
            created_at_profile, indexed_at_profile,
            viewer_muted, viewer_following, viewer_blocked_by,
            collected_at
        )
        VALUES (
            %(post_uri)s, %(post_url)s, %(post_cid)s, %(text)s,
            %(created_at_post)s, %(indexed_at_post)s, %(embed)s,
            %(like_count)s, %(repost_count)s, %(reply_count)s,
            %(did)s, %(handle)s, %(display_name)s,
            %(followers_count)s, %(follows_count)s, %(posts_count)s,
            %(created_at_profile)s, %(indexed_at_profile)s,
            %(viewer_muted)s, %(viewer_following)s, %(viewer_blocked_by)s,
            %(collected_at)s
        )
        ON CONFLICT (post_uri) DO NOTHING;
    """

    # 4) Boucle d'insertion
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            for i, row in df.iterrows():
                try:
                    cur.execute(sql, row.to_dict())
                except Exception as e:
                    print(f"❌ Erreur insertion bluesky_search_posts ligne {i}: {e}")
                    conn.rollback()
        conn.commit()
    print(f"✅ {len(df)} posts insérés dans bluesky_search_posts.")




##### insertion des posts d'un compte 
def insert_bluesky_user_posts(profile_url: str, limit: int = 100):
    df = collect_user_posts_to_dataframe(profile_url, limit)
    if df.empty:
        print("⚠️ Aucun post user à insérer.")
        return

    column_map = {
        "username": "username",
        "user_id": "user_id",
        "bio": "bio",
        "followers_count": "followers_count",
        "follows_count": "follows_count",
        "posts_count": "posts_count",
        "profile_created_at": "profile_created_at",
        "post_uri": "post_uri",
        "post_url": "post_url",
        "post_text": "post_text",
        "post_created_at": "post_created_at",
        "post_indexed_at": "post_indexed_at",
        "like_count": "like_count",
        "repost_count": "repost_count",
        "reply_count": "reply_count",
        "collected_at": "collected_at",
    }
    df.rename(columns=column_map, inplace=True)

    df = clean_dataframe_dates(df, [
        "profile_created_at", "post_created_at",
        "post_indexed_at", "collected_at"
    ])

    sql = """
        INSERT INTO bluesky_user_posts (
            username, user_id, bio,
            followers_count, follows_count, posts_count,
            profile_created_at,
            post_uri, post_url, post_text,
            post_created_at, post_indexed_at,
            like_count, repost_count, reply_count,
            collected_at
        )
        VALUES (
            %(username)s, %(user_id)s, %(bio)s,
            %(followers_count)s, %(follows_count)s, %(posts_count)s,
            %(profile_created_at)s,
            %(post_uri)s, %(post_url)s, %(post_text)s,
            %(post_created_at)s, %(post_indexed_at)s,
            %(like_count)s, %(repost_count)s, %(reply_count)s,
            %(collected_at)s
        )
        ON CONFLICT (post_uri) DO NOTHING;
    """
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            for i, row in df.iterrows():
                try:
                    cur.execute(sql, row.to_dict())
                except Exception as e:
                    print(f"❌ Erreur insertion bluesky_user_posts ligne {i}: {e}")
                    conn.rollback()
        conn.commit()
    print(f"✅ {len(df)} posts insérés dans bluesky_user_posts.")

 
#### insertion d'un tweet à la fois 
def insert_bluesky_single_post(post_url: str):
    df = collect_single_post_to_dataframe(post_url)
    if df.empty:
        print("⚠️ Aucun single post à insérer.")
        return

    column_map = {
        "username": "username",
        "user_id": "user_id",
        "post_uri": "post_uri",
        "post_cid": "post_cid",
        "post_text": "post_text",
        "post_created_at": "post_created_at",
        "post_indexed_at": "post_indexed_at",
        "like_count": "like_count",
        "repost_count": "repost_count",
        "reply_count": "reply_count",
        "collected_at": "collected_at",
    }
    df.rename(columns=column_map, inplace=True)

    df = clean_dataframe_dates(df, [
        "post_created_at", "post_indexed_at", "collected_at"
    ])

    sql = """
        INSERT INTO bluesky_single_posts (
            username, user_id,
            post_uri, post_cid, post_text,
            post_created_at, post_indexed_at,
            like_count, repost_count, reply_count,
            collected_at
        )
        VALUES (
            %(username)s, %(user_id)s,
            %(post_uri)s, %(post_cid)s, %(post_text)s,
            %(post_created_at)s, %(post_indexed_at)s,
            %(like_count)s, %(repost_count)s, %(reply_count)s,
            %(collected_at)s
        )
        ON CONFLICT (post_uri) DO NOTHING;
    """
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            for i, row in df.iterrows():
                try:
                    cur.execute(sql, row.to_dict())
                except Exception as e:
                    print(f"❌ Erreur insertion bluesky_single_posts ligne {i}: {e}")
                    conn.rollback()
        conn.commit()
    print(f"✅ {len(df)} post(s) inséré(s) dans bluesky_single_posts.")


#insert_tweet = insert_bluesky_search_posts("political", limit=10, lang="en")
#insert_user = insert_bluesky_user_posts("https://bsky.app/profile/jenniferlmeyer.bsky.social", limit=20)
#insert_single_tweet = insert_bluesky_single_post("https://bsky.app/profile/jenniferlmeyer.bsky.social/post/3lsw4nxtm5k2c")




