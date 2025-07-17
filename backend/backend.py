from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg
from collector import (
    search_bluesky_posts,
    extract_handle_from_url,
    fetch_profile_and_posts,
    fetch_post_from_url
)
from db import insert_bluesky_search_posts,insert_bluesky_user_posts,insert_bluesky_single_post 

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    limit: int = 100
    lang: str = None

class ProfileRequest(BaseModel):
    profile_url: str
    limit: int = 50

class TweetRequest(BaseModel):
    tweet_url: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bluesky Import API"}

@app.post("/import/search")
def import_search(data: SearchRequest):
    try:
        posts = search_bluesky_posts(data.query, data.limit, data.lang)
        inserted = 0
        users_seen = set()
        for post in posts:
            # insérer user si pas déjà vu (pour limiter les requêtes, tu peux faire plus complexe)
            user_tuple = (post['did'], post['handle'])
            if user_tuple not in users_seen:
                user_data = {k: post[k] for k in [
                    'did','handle','displayname','bio','followerscount','followscount','postscount',
                    'createdat_profile','indexedat_profile','viewer_muted','viewer_following',
                    'viewer_blockedby','labels','collectedat'
                ]}
                insert_bluesky_search_posts(user_data)
                users_seen.add(user_tuple)
            # insérer tweet
            post_data = {k: post[k] for k in [
                'post_uri','post_cid','did','post_url','text','createdat_post','indexedat_post',
                'embed','likecount','repostcount','replycount','collectedat'
            ]}
            for key in post_data:
                if post_data[key] == "":
                    post_data[key] = None

            insert_bluesky_search_posts(post_data)
            inserted += 1
        return {"inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@app.post("/import/profile")
def import_profile(data: ProfileRequest):
    try:
        handle = extract_handle_from_url(data.profile_url)
        if not handle:
            raise ValueError("URL de profil invalide")
        user, posts = fetch_profile_and_posts(handle, data.limit)
        insert_bluesky_user_posts(user)
        for post in posts:
            insert_bluesky_user_posts(post)
        return {"user": user["handle"], "posts_inserted": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/import/tweet_url")
def import_tweet_url(data: TweetRequest):
    try:
        post = fetch_post_from_url(data.tweet_url)
        for key in post:
            if post[key] == "":
                post[key] = None
        insert_bluesky_single_post(post)
        return {"tweet_uri": post["post_uri"], "inserted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


