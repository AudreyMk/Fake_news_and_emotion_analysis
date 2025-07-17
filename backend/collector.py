import os
import json
from datetime import datetime
from urllib.parse import urlparse
from atproto import Client
from dotenv import load_dotenv
import os

load_dotenv()

BLUESKY_IDENTIFIER = os.getenv("BLUESKY_IDENTIFIER")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")


def search_bluesky_posts(query="Bluesky", limit=100, lang=None):
    client = Client(base_url="https://bsky.social")
    client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
    all_posts = []
    cursor = None
    while len(all_posts) < limit:
        params = {
            "q": query,
            "limit": min(100, limit - len(all_posts)),
            "cursor": cursor
        }
        if lang:
            params["lang"] = lang
        search_response = client.app.bsky.feed.search_posts(params)
        batch = getattr(search_response, "posts", [])
        if not batch:
            break
        for post_view in batch:
            try:
                record = post_view.record
                author = post_view.author
                viewer = getattr(author, 'viewer', None)
                info = {
                    'post_uri': post_view.uri,
                    'post_url': f"https://bsky.app/profile/{author.handle}/post/{post_view.uri.split('/')[-1]}",
                    'post_cid': post_view.cid,
                    'text': getattr(record, 'text', '').replace('\n', ' ').strip(),
                    'createdat_post': getattr(record, 'created_at', ''),
                    'indexedat_post': getattr(post_view, 'indexed_at', ''),
                    'embed': json.dumps(getattr(record, 'embed', {}) or {}, default=str),
                    'likecount': getattr(post_view, 'like_count', 0),
                    'repostcount': getattr(post_view, 'repost_count', 0),
                    'replycount': getattr(post_view, 'reply_count', 0),
                    'did': author.did,
                    'handle': author.handle,
                    'displayname': getattr(author, 'display_name', ''),
                    'bio': author.description.replace('\n', ' ').strip() if hasattr(author, 'description') and isinstance(author.description, str) else '',
                    'followerscount': getattr(author, 'followers_count', 0),
                    'followscount': getattr(author, 'follows_count', 0),
                    'postscount': getattr(author, 'posts_count', 0),
                    'createdat_profile': getattr(author, 'created_at', ''),
                    'indexedat_profile': getattr(author, 'indexed_at', ''),
                    'viewer_muted': getattr(viewer, 'muted', None) if viewer else None,
                    'viewer_following': getattr(viewer, 'following', None) if viewer else None,
                    'viewer_blockedby': getattr(viewer, 'blocked_by', None) if viewer else None,
                    'labels': json.dumps(getattr(author, 'labels', []) or []),
                    'collectedat': datetime.utcnow().isoformat() + 'Z'
                }
                all_posts.append(info)
            except Exception:
                continue
        cursor = getattr(search_response, "cursor", None)
        if not cursor:
            break
    return all_posts

def extract_handle_from_url(profile_url):
    path_parts = urlparse(profile_url).path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'profile':
        return path_parts[1]
    return None

def fetch_profile_and_posts(handle, limit=50):
    client = Client(base_url="https://bsky.social")
    client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
    profile = client.app.bsky.actor.get_profile({'actor': handle})
    user_data = {
        'did': profile.did,
        'handle': profile.handle,
        'displayname': getattr(profile, 'display_name', ''),
        'bio': profile.description.replace('\n', ' ').strip() if isinstance(profile.description, str) else '',
        'followerscount': getattr(profile, 'followers_count', 0),
        'followscount': getattr(profile, 'follows_count', 0),
        'postscount': getattr(profile, 'posts_count', 0),
        'createdat_profile': getattr(profile, 'created_at', ''),
        'indexedat_profile': getattr(profile, 'indexed_at', ''),
        'viewer_muted': getattr(profile, 'viewer', None) and getattr(profile.viewer, 'muted', None),
        'viewer_following': getattr(profile, 'viewer', None) and getattr(profile.viewer, 'following', None),
        'viewer_blockedby': getattr(profile, 'viewer', None) and getattr(profile.viewer, 'blocked_by', None),
        'labels': json.dumps(getattr(profile, 'labels', []) or []),
        'collectedat': datetime.utcnow().isoformat() + 'Z'
    }
    posts = []
    cursor = None
    while len(posts) < limit:
        resp = client.app.bsky.feed.get_author_feed({
            'actor': handle,
            'limit': min(100, limit - len(posts)),
            'cursor': cursor
        })
        for item in resp.feed:
            post = item.post
            record = post.record
            post_data = {
                'post_uri': post.uri,
                'post_cid': post.cid,
                'did': profile.did,
                'post_url': f"https://bsky.app/profile/{handle}/post/{post.uri.split('/')[-1]}",
                'text': getattr(record, 'text', '').replace('\n', ' ').strip(),
                'createdat_post': getattr(record, 'created_at', ''),
                'indexedat_post': getattr(post, 'indexed_at', ''),
                'embed': json.dumps(getattr(record, 'embed', {}) or {}, default=str),
                'likecount': getattr(post, 'like_count', 0),
                'repostcount': getattr(post, 'repost_count', 0),
                'replycount': getattr(post, 'reply_count', 0),
                'collectedat': datetime.utcnow().isoformat() + 'Z'
            }
            posts.append(post_data)
        cursor = getattr(resp, 'cursor', None)
        if not cursor:
            break
    return user_data, posts

def extract_handle_and_post_id(post_url):
    parsed = urlparse(post_url)
    parts = parsed.path.strip('/').split('/')
    try:
        profile_index = parts.index('profile')
        post_index = parts.index('post')
        handle = parts[profile_index + 1]
        post_id = parts[post_index + 1]
        return handle, post_id
    except (ValueError, IndexError):
        return None, None

def fetch_post_from_url(url):
    client = Client(base_url="https://bsky.social")
    client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
    handle, post_id = extract_handle_and_post_id(url)
    if not handle or not post_id:
        raise ValueError("❌ URL de post Bluesky invalide.")
    resolved = client.com.atproto.identity.resolve_handle({'handle': handle})
    did = resolved.did
    uri = f"at://{did}/app.bsky.feed.post/{post_id}"
    post_thread = client.app.bsky.feed.get_post_thread({'uri': uri})
    post = post_thread.thread.post
    record = post.record
    post_data = {
        'post_uri': post.uri,
        'post_cid': post.cid,
        'did': did,
        'post_url': url,
        'text': getattr(record, 'text', '').replace('\n', ' ').strip(),
        'createdat_post': getattr(record, 'created_at', ''),
        'indexedat_post': getattr(post, 'indexed_at', ''),
        'embed': json.dumps(getattr(record, 'embed', {}) or {}, default=str),
        'likecount': getattr(post, 'like_count', 0),
        'repostcount': getattr(post, 'repost_count', 0),
        'replycount': getattr(post, 'reply_count', 0),
        'collectedat': datetime.utcnow().isoformat() + 'Z'
    }
    return post_data
