import os

from eth_rpc import EventData
from eth_rpc.networks import Base
from eth_typeshed.uniswap_v2.events import V2SwapEvent, V2SwapEventType
from tweepy import Tweet
from tweepy.client import Client

from emp_hooks import onchain, twitter


@onchain.on_event(V2SwapEvent, Base)
def print_swaps(event_data: EventData[V2SwapEventType]):
    event = event_data.event
    address = event_data.log.address
    amount0 = event.amount0_in - event.amount0_out
    amount1 = event.amount1_in - event.amount1_out

    print(
        address,
        "Amounts:",
        amount0,
        amount1,
    )


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
