import json
import os

from tweepy import Tweet
from tweepy.client import Client

from emp_hooks import twitter
from emp_hooks.hook_manager import hooks


@twitter.on_tweet("simmi_io")
def on_tweet(tweet: Tweet):
    data = json.loads(tweet["data"])

    tweet_id = data["id"]
    author_id = data["author_id"]

    client = Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
    user = client.get_user(id=author_id)

    client.create_tweet(
        text=f"I hear you, {user.data.name}.",
        in_reply_to_tweet_id=tweet_id,
    )


hooks.run(keep_alive=True)
