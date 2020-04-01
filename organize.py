import sys
import spotipy
import spotipy.util

def get_playlists(username, sp):
    ret = dict()
   
    playlists = sp.user_playlists(username)
    while True:
        for playlist in playlists['items']:
            if playlist['owner']['id'] == username:
                ret[playlist['name']] = playlist['id']
               
        if not playlists['next']:
            break
        playlists = sp.next(playlists)

    return ret

def get_decade(track):
    release_date = track['album']['release_date']
    year = release_date[:4]
    decade = (int(year[2:])//10)*10
    return "%.2d's" % (decade)
   
def sort_tracks(username, sp, tracks):
    buckets = dict()
    album_ids = dict()
    artist_ids = dict()

    # sort by decade and get the artists/albums
    while True:
        for item in tracks['items']:
            track = item['track']
            track_id = track['id']
            decade = get_decade(track)
            buckets.setdefault(decade, []).append(track_id)
            album_ids.setdefault(track['album']['id'], []).append(track_id)
            artist_ids.setdefault(track['artists'][0]['id'], []).append(track_id)

        if not tracks['next']:
            break
        tracks = sp.next(tracks)

    '''
    albums = list()
    for i in range(0, len([*album_ids]), 20):
        albums.extend(sp.albums([*album_ids][i:i+20])['albums'])

    for album in albums:
        for genre in album['genres']:
            buckets.setdefault(genre, []).extend(album_ids[album['id']])
    '''

    artists = list()
    for i in range(0, len([*artist_ids]), 50):
        artists.extend(sp.artists([*artist_ids][i:i+20])['artists'])

    for artist in artists:
        for genre in artist['genres']:
            buckets.setdefault(genre, []).extend(artist_ids[artist['id']])
    
    return buckets

def put_in_playlists(username, sp, buckets, min_tracks):
    for bucket in buckets:
        if len(buckets[bucket]) >= min_tracks:
            playlist_id = playlists.get(bucket, None)
            if not playlist_id:
                playlist_id = sp.user_playlist_create(username, bucket, public=False)['id']
            for i in range(0, len(buckets[bucket]), 100):
                if not i:
                    sp.user_playlist_replace_tracks(username, playlist_id, buckets[bucket][:100])
                else:
                    sp.user_playlist_add_tracks(username, playlist_id, buckets[bucket][i:i+100])

scope = 'playlist-read-private playlist-modify-public playlist-modify-private'

if __name__ == "__main__":
    if len(sys.argv) > 2:
        username = sys.argv[1]
        playlist = sys.argv[2]
    else:
        print("usage: python3 organize.py [username] [playlist]")
        sys.exit()

    if len(sys.argv) > 3:
        min_tracks = int(sys.argv[3])
    else:
        min_tracks = 50

    token = spotipy.util.prompt_for_user_token(username, scope)
    
    if token:
        sp = spotipy.Spotify(auth=token)
        # get name:id dict of playlists
        print("Getting user profile...")
        playlists = get_playlists(username, sp)
        # get tracks from the playlist to sort
        print("Getting playlist...")
        results = sp.user_playlist(username, playlist, fields="tracks,next")
        # bucket sort tracks based on decade/genre
        print("Sorting into buckets...")
        buckets = sort_tracks(username, sp, results['tracks'])
        # put the buckets into playlists
        print("Creating playlists...")
        put_in_playlists(username, sp, buckets, min_tracks)
        print("Done!")
    else:
        print("Can't get token for", username)
