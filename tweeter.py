import os
import requests
from requests_oauthlib import OAuth1Session
import json
from unsplash.api import Api
from unsplash.auth import Auth
import tweepy
import datetime

# Unsplash credentials
unsplash_client_id = os.getenv("UNSPLASH_CLIENT_ID")
unsplash_client_secret = os.getenv("UNSPLASH_CLIENT_SECRET")
unsplash_redirect_uri = os.getenv("UNSPLASH_REDIRECT_URI")
unsplash_code = ""

# Twitter OAuth credentials
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
TOKEN_SECRET = os.getenv("TOKEN_SECRET")

# ChatGPT API credentials
GPT_API_KEY = os.getenv("GPT_API_KEY")

# API endpoints
GPT_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
TWITTER_API_ENDPOINT = "https://api.twitter.com/2/tweets"


# Read topics from the external file
with open("topics.txt", "r") as file:
    TOPICS_BY_DAY = [line.strip() for line in file]

# Read sub topics from the external file
with open("subtopics.txt", "r") as file:
    SUB_TOPICS_BY_HOUR = [line.strip() for line in file]

# Get the current day of the year
day_of_year = datetime.datetime.now().timetuple().tm_yday

# Get the current date and time
current_datetime = datetime.datetime.now()

# Get the current hour
current_hour = current_datetime.hour

# Format the current date and time as a string
formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

# Check if the day is within the range of available topics
if 1 <= day_of_year <= len(TOPICS_BY_DAY):
    selected_topic = TOPICS_BY_DAY[day_of_year - 1]
    print(f"Topic for today: {selected_topic}")
else:
    print("No corresponding topic for the current day.")

# Check if the hour is within the range of available sub topics
if 0 <= current_hour <= len(SUB_TOPICS_BY_HOUR):
    selected_sub_topic = SUB_TOPICS_BY_HOUR[current_hour]
    print(f"Sub topic for the current hour: {selected_sub_topic}")
else:
    print("No corresponding sub topic for the current hour.")

# Prompt for ChatGPT
GPT_PROMPT = "Write me a motivational, inspirational tweet to inspire people in less than 250 letters about {} and {}. The current time is {}. Please consider the year or month or date or time or part of the day when writing the poem. Add relevant tags at the end. Dont use special characters other than # in the tags. Do not use the words - whisper and embrace. The total output should not exceed 280 characters".format(
    selected_topic, selected_sub_topic, formatted_datetime
)

print(GPT_PROMPT)

# Authenticate with Unsplash
unsplash_auth = Auth(
    unsplash_client_id,
    unsplash_client_secret,
    unsplash_redirect_uri,
    code=unsplash_code,
)
unsplash_api = Api(unsplash_auth)

# authenticating to access the twitter API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, TOKEN_SECRET)
api = tweepy.API(auth)

# Create an OAuth1Session for Twitter
twitter = OAuth1Session(
    client_key=CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=ACCESS_TOKEN,
    resource_owner_secret=TOKEN_SECRET,
)

# Make a request to ChatGPT API
gpt_response = requests.post(
    GPT_API_ENDPOINT,
    headers={"Authorization": f"Bearer {GPT_API_KEY}"},
    json={
        "messages": [{"role": "user", "content": GPT_PROMPT}],
        "temperature": 0.7,
        "model": "gpt-3.5-turbo",
    },
)

# Parse response from ChatGPT
gpt_data = gpt_response.json()

print(gpt_data)
poem = gpt_data["choices"][0]["message"]["content"].strip().replace('"','')


# Get a random photo from Unsplash
random_photos = unsplash_api.photo.random()

# Assuming random_photos is a list, extract the first photo
random_photo = random_photos[0]

# Get the URL of the photo
photo_url = random_photo.urls.full
photo_filename = "random_photo.jpg"
response = requests.get(photo_url)
with open(photo_filename, "wb") as f:
    f.write(response.content)

# Generate text tweet with media (image)
# media upload response is Media(_api=<tweepy.api.API object at 0x10307dd90>, media_id=1695817901175898114, media_id_string='1695817901175898114', size=2861667, expires_after_secs=86400, image={'image_type': 'image/jpeg', 'w': 6000, 'h': 4000})
media_id = api.media_upload(photo_filename).media_id_string


# Tweet the generated poem
tweet_text = poem
tweet_body = {"text": tweet_text, "media": {"media_ids": [media_id]}}
tweet_headers = {"Content-Type": "application/json"}

tweet_response = twitter.post(
    TWITTER_API_ENDPOINT, data=json.dumps(tweet_body), headers=tweet_headers
)

# Check the tweet response
if tweet_response.status_code == 201:
    print("Tweet posted successfully: ", tweet_response.text)
else:
    print("Error posting tweet:", tweet_response.text)
