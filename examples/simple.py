import os

from tweepy import Tweet
from tweepy.client import Client

from emp_hooks import twitter


@twitter.on_tweet("simmi_io")
def on_tweet(tweet: Tweet):
    tweet_id = tweet.id
    author_id = tweet.author_id
    client = Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
    user = client.get_user(id=author_id)

    client.create_tweet(
        text=f"I hear you, {user.data.name}.",
        in_reply_to_tweet_id=tweet_id,
    )
