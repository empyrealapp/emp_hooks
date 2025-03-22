import os
import sys

from eth_rpc.networks import Base
from eth_typeshed.uniswap_v2.events import V2SwapEvent
from tweepy import Tweet
from tweepy.client import Client

from emp_hooks import onchain, twitter


@onchain.on_event(V2SwapEvent, Base)
def print_swaps(val):
    print("VAL:", val)
    sys.stdout.flush()


@twitter.on_tweet("simmi_io")
def on_simmi_tweet(tweet: Tweet) -> bool:
    tweet_id = tweet.id
    author_id = tweet.author_id

    client = Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
    user = client.get_user(id=author_id)

    client.create_tweet(
        text=f"I hear you, {user.data.name}.",
        in_reply_to_tweet_id=tweet_id,
    )

    return True


@twitter.on_tweet("empyreal")
def on_emp_tweet(tweet: Tweet) -> bool:
    tweet_id = tweet.id
    author_id = tweet.author_id

    client = Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
    user = client.get_user(id=author_id)

    client.create_tweet(
        text=f"I hear you, {user.data.name}.",
        in_reply_to_tweet_id=tweet_id,
    )

    return True
