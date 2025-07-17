import json
import sys
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from atproto import Client
import os
import sys


try:
    from atproto import Client
except ImportError:
    print("Veuillez installer le SDK AT Protocol Python : pip install atproto")
    sys.exit(1)

# Identifiants Bluesky
BLUESKY_IDENTIFIER = 'bbskyprojet.bsky.social'
BLUESKY_APP_PASSWORD = 'n3b7-57x2-m552-lbjv'
OUTPUT_CSV_SEARCH = 'bluesky_search_results.csv'

def search_bluesky_posts(query, limit=100, lang=None):
    client = Client(base_url="https://bsky.social")
    try:
        print(f"Tentative de connexion à Bluesky pour {BLUESKY_IDENTIFIER}...")
        client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
        print("Connexion réussie !\n")

        all_posts = []
        cursor = None

        print(f"Recherche de posts contenant '{query}' avec une limite de {limit}...")
        if lang:
            print(f"Filtrage par langue : {lang}")

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

            print(f"Posts reçus dans ce batch de l'API : {len(batch)}")

            if not batch:
                print("Plus de posts disponibles pour cette recherche.\n")
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
                        'createdAt_post': getattr(record, 'created_at', ''),
                        'indexedAt_post': getattr(post_view, 'indexed_at', ''),
                        'embed': json.dumps(getattr(record, 'embed', {}) or {}, default=str),
                        'likeCount': getattr(post_view, 'like_count', 0),
                        'repostCount': getattr(post_view, 'repost_count', 0),
                        'replyCount': getattr(post_view, 'reply_count', 0),
                        'did': author.did,
                        'handle': author.handle,
                        'displayName': getattr(author, 'display_name', ''),
                        'followersCount': getattr(author, 'followers_count', 0),
                        'followsCount': getattr(author, 'follows_count', 0),
                        'postsCount': getattr(author, 'posts_count', 0),
                        'createdAt_profile': getattr(author, 'created_at', ''),
                        'indexedAt_profile': getattr(author, 'indexed_at', ''),
                        'viewer_muted': getattr(viewer, 'muted', None) if viewer else None,
                        'viewer_following': getattr(viewer, 'following', None) if viewer else None,
                        'viewer_blockedBy': getattr(viewer, 'blocked_by', None) if viewer else None,
                        #'labels': json.dumps(getattr(author, 'labels', []) or []),
                        'collectedAt': datetime.utcnow().isoformat() + 'Z'
                    }

                    all_posts.append(info)

                except Exception as post_e:
                    print(f"Erreur lors du traitement du post {getattr(post_view, 'uri', 'inconnu')} : {post_e}")
                    continue

            cursor = getattr(search_response, "cursor", None)
            print(f"Cursor pour la prochaine requête : {cursor}\n")

            if not cursor:
                break

            if all_posts:
              df = pd.DataFrame(all_posts)
            return df
        else:
            print("Aucun post n'a été collecté, retour d'un DataFrame vide.")
            return pd.DataFrame() # Retourne un DataFrame vide si aucune donnée

    except Exception as e:
        print(f"Erreur globale lors de la récupération des posts : {e}")
        return pd.DataFrame() # Retourne un DataFrame vide en cas d'erreu

# df = search_bluesky_posts("test", limit=10, lang="fr")
# df.to_csv(OUTPUT_CSV_SEARCH, index=False, encoding='utf-8-sig', sep=';')
# print(df.head())




# collecte via url
def collect_user_posts_to_dataframe(profile_url: str, limit: int) -> pd.DataFrame:

    # 1. Extraction du handle de l'URL
    path_parts = urlparse(profile_url).path.strip('/').split('/')
    if not (len(path_parts) >= 2 and path_parts[0] == 'profile'):
        print("❌ Format de l’URL incorrect. Utilisez une URL de type https://bsky.social/profile/handle")
        return pd.DataFrame() # Retourne un DataFrame vide en cas d'erreur de format d'URL

    handle = path_parts[1]
    print(f"Handle extrait : {handle}")

    # 2. Connexion au client Bluesky
    client = Client(base_url="https://bsky.social")
    try:
        print(f"Tentative de connexion à Bluesky pour {BLUESKY_IDENTIFIER}...")
        client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
        print("Connexion réussie !\n")
    except Exception as e:
        print(f"❌ Erreur de connexion à Bluesky : {e}")
        return pd.DataFrame()

    # 3. Récupération du profil
    try:
        profile = client.app.bsky.actor.get_profile({'actor': handle})
        user_data = {
            'username': profile.handle,
            'user_id': profile.did,
            'bio': profile.description.replace('\n', ' ').strip() if isinstance(profile.description, str) else '',
            'followers_count': getattr(profile, 'followers_count', 0),
            'follows_count': getattr(profile, 'follows_count', 0),
            'posts_count': getattr(profile, 'posts_count', 0),
            'profile_created_at': getattr(profile, 'created_at', ''),
        }
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du profil de '{handle}' : {e}")
        return pd.DataFrame()

    # 4. Récupération des posts
    posts = []
    cursor = None
    print(f"Récupération des posts pour l'utilisateur '{handle}' avec une limite de {limit}...")

    try:
        while len(posts) < limit:
            resp = client.app.bsky.feed.get_author_feed({
                'actor': handle,
                'limit': min(100, limit - len(posts)),
                'cursor': cursor
            })

            batch = resp.feed
            print(f"Posts reçus dans ce batch de l'API : {len(batch)}")

            if not batch:
                print("Plus de posts disponibles pour cet utilisateur.\n")
                break

            for item in batch:
                post = item.post
                record = post.record

                post_data = {
                    **user_data, # Inclut les données de l'utilisateur dans chaque post
                    'post_uri': post.uri,
                    'post_url': f"https://bsky.app/profile/{handle}/post/{post.uri.split('/')[-1]}",
                    'post_text': getattr(record, 'text', '').replace('\n', ' ').strip(),
                    'post_created_at': getattr(record, 'created_at', ''),
                    'post_indexed_at': getattr(post, 'indexed_at', ''),
                    'like_count': getattr(post, 'like_count', 0),
                    'repost_count': getattr(post, 'repost_count', 0),
                    'reply_count': getattr(post, 'reply_count', 0),
                    'collected_at': datetime.utcnow().isoformat() + 'Z',
                }
                posts.append(post_data)

            cursor = getattr(resp, 'cursor', None)
            if not cursor:
                break
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des posts de l'utilisateur : {e}")
        return pd.DataFrame()

    # 5. Conversion en DataFrame et retour
    if posts:
        df = pd.DataFrame(posts)
        print(f"✅ Collecte terminée. {len(df)} posts prêts pour le DataFrame.")
        return df
    else:
        print("Aucun post n'a été collecté, retour d'un DataFrame vide.")
        return pd.DataFrame()


# df = collect_user_posts_to_dataframe("https://bsky.app/profile/jenniferlmeyer.bsky.social", limit=10)
# df.to_csv(OUTPUT_CSV_SEARCH, index=False, encoding='utf-8-sig', sep=';')
# print(df.head())


OUTPUT_CSV = 'bluesky_single_post.csv'

def collect_single_post_to_dataframe(post_url: str) -> pd.DataFrame:

    # 1. Extraction du handle et de l'ID du post depuis l'URL
    parsed = urlparse(post_url)
    parts = parsed.path.strip('/').split('/')
    
    handle = None
    post_id = None
    try:
        profile_index = parts.index('profile')
        post_index = parts.index('post')
        handle = parts[profile_index + 1]
        post_id = parts[post_index + 1]
    except (ValueError, IndexError):
        print("❌ URL de post Bluesky invalide. Le format attendu est https://bsky.app/profile/handle/post/post_id")
        return pd.DataFrame() # Retourne un DataFrame vide en cas d'URL invalide

    if not handle or not post_id:
        print("❌ URL de post Bluesky invalide. Impossible d'extraire le handle ou l'ID du post.")
        return pd.DataFrame()

    print(f"Handle extrait : {handle}, ID du post extrait : {post_id}")

    # 2. Connexion au client Bluesky
    client = Client(base_url="https://bsky.social")
    try:
        print(f"Tentative de connexion à Bluesky pour {BLUESKY_IDENTIFIER}...")
        client.login(BLUESKY_IDENTIFIER, BLUESKY_APP_PASSWORD)
        print("Connexion réussie !\n")
    except Exception as e:
        print(f"❌ Erreur de connexion à Bluesky : {e}")
        return pd.DataFrame()

    # 3. Résolution du DID depuis le handle
    did = None
    try:
        resolved = client.com.atproto.identity.resolve_handle({'handle': handle})
        did = resolved.did
        print(f"DID de l'utilisateur '{handle}' résolu : {did}")
    except Exception as e:
        print(f"❌ Erreur lors de la résolution du DID pour '{handle}' : {e}")
        return pd.DataFrame()

    # 4. Construction de l'URI du post
    uri = f"at://{did}/app.bsky.feed.post/{post_id}"
    print(f"URI du post construit : {uri}")

    # 5. Récupération du post via son URI
    try:
        post_thread = client.app.bsky.feed.get_post_thread({'uri': uri})
        post = post_thread.thread.post
        record = post.record

        post_data = {
            'username': handle,
            'user_id': did,
            'post_uri': post.uri,
            'post_cid': post.cid,
            'post_text': getattr(record, 'text', '').replace('\n', ' ').strip(),
            'post_created_at': getattr(record, 'created_at', ''),
            'post_indexed_at': getattr(post, 'indexed_at', ''),
            'like_count': getattr(post, 'like_count', 0),
            'repost_count': getattr(post, 'repost_count', 0),
            'reply_count': getattr(post, 'reply_count', 0),
            'collected_at': datetime.utcnow().isoformat() + 'Z',
        }
        print("✅ Post récupéré avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du post '{post_url}' : {e}")
        return pd.DataFrame()

    # 6. Conversion en DataFrame et retour
    df = pd.DataFrame([post_data]) # Créer un DataFrame à partir d'une liste contenant un seul dictionnaire
    return df


# df = collect_single_post_to_dataframe("https://bsky.app/profile/jenniferlmeyer.bsky.social/post/3lsw4nxtm5k2c")
# df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig', sep=';')
# print(df.head())

