# twitter-od-bot
A twitter bot that replies to tweets containing image media and runs the images through an Object Detection ML model.
## Setup
### API Keys
---
A `.env` file in this directory root with the apropriate API keys is required. The required format is:  
```
CONSUMER_KEY="..."
CONSUMER_SECRET="..."
ACCESS_TOKEN="..."
ACCESS_TOKEN_SECRET="..."
```
The managing account needs to be a developer account with elevated access (required for 1.1 API access).  
The account that should post the tweets needs to authorized the app from the developer account (using [twurl](https://github.com/twitter/twurl) for convenience):  
```
twurl authorize --consumer-key <key> --consumer-secret <secret>
```
The `ACCESS_TOKEN` (token) and `ACCESS_TOKEN_SECRET` (secret) can then be found in `~/.twurlrc`.  

### Setup the venv
---
```
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python bot.py 
```