# utils
import subprocess
from dotenv import load_dotenv
import json
import os
import base64
import requests
import ast
from PIL import Image
from tempfile import mkstemp 

# twitter SDK
import tweepy

def setup():
    # load API keys
    load_dotenv()
    CONSUMER_KEY = os.getenv('CONSUMER_KEY')
    CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
    ACCESS_TOKEN= os.getenv('ACCESS_TOKEN')
    ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

    # authenticate to twitter
    auth = tweepy.OAuth1UserHandler(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    user = api.verify_credentials()
    if user:
        handle = user.screen_name
        own_id = user.id
    else:
        raise Exception('[ERROR] Unable to verify_credentials() with OAuth1, check your .env file and API keys!')
    
    #
    # read in config
    #
    with open('config.json', 'r') as file:
        config = json.load(file)
    global last_id_filename     # where to store the id of the oldest mention that's already processed
    global max_tweets_to_fetch  # max number of tweets to look at
    global step_size            # tweets to fetch at once
    global detection_url

    last_id_filename = config['last_id_filename']
    max_tweets_to_fetch = config['max_tweets_to_fetch']
    step_size = config['step_size']
    detection_url = config['detection_url']
    
    return api, handle, own_id


def check_mentions(api, handle):
    if os.path.isfile(last_id_filename):
        # load the stored id of the oldest mention that's already processed
        with open(last_id_filename, 'r') as file:
            most_recent_ids = json.load(file)
    else:
        # first time fetching mentions for the authenticated user
        most_recent_ids = {handle: None}

    if handle in most_recent_ids:
        newest_seen = most_recent_ids[handle]
    else:
        newest_seen = None



    oldest_seen = None
    highest_id_in_run = 0
    for i in range(0,int(max_tweets_to_fetch/step_size)):

        if not oldest_seen:
            if not newest_seen:
                status_list = api.mentions_timeline(count=step_size)
            else:
                status_list = api.mentions_timeline(count=step_size, since_id=newest_seen)
        else:
            if not newest_seen:
                status_list = api.mentions_timeline(count=step_size, max_id=oldest_seen-1)
            else:
                status_list = api.mentions_timeline(count=step_size, max_id=oldest_seen-1, since_id=newest_seen)

        if not status_list:
            # no more tweets left to fetch
            if highest_id_in_run > 0:
                most_recent_ids[handle] = highest_id_in_run
                with open(last_id_filename, 'w') as file:
                    json.dump(most_recent_ids, file)
                print(f'[INFO] done fetching mentions for user {handle}. newest mention id: {most_recent_ids[handle]}')
                break
            else:
                # no mentions since last loop execution
                print(f'[INFO] no new mentions to fetch for user {handle}. newest mention id: {most_recent_ids[handle]}')
            break
        
        # process the mentions
        for status in status_list:
            if not oldest_seen or status.id < oldest_seen:
                oldest_seen = status.id
            if status.id > highest_id_in_run:
                highest_id_in_run = status.id
            # TODO: respond to mentions
            # get image media, otherwise ignore
            if 'media' in status.extended_entities:
                media = status.extended_entities['media']
            

                if len(media) > 0:
                    resp_media_ids = []
                    for entry in media:
                        if entry['type'] == 'photo' and entry['media_url_https']:
                                # send media to endpoint
                                # recieve image back and build response
                                payload = {'input': entry['media_url_https'], 'output':1}
                                response = requests.post(detection_url+'/api/detect', data=payload)
                                
                                fd, path = mkstemp(suffix='.jpg')
                                with open(fd, 'wb') as file:
                                    file.write(base64.b64decode(bytes.fromhex(response.json()['annonated_image_b64'])))
 
                                resp = api.media_upload(path)
                                resp_media_ids.append(resp.media_id)
                # send the response 
                #print(res_media_ids)
                api.update_status(f'hi @{status.user.screen_name}! here are your results.', in_reply_to_status_id=status.id, auto_populate_reply_metadata=True, media_ids=resp_media_ids)

        i = i+1


if __name__ == '__main__':
    api, handle, own_id = setup()
    
    # maybe set up a cron job to check mentions every day?
    check_mentions(api, handle)
