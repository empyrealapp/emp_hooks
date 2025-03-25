import logging
import os

from eth_rpc import EventData
from eth_rpc.networks import Base
from eth_rpc.types import HexAddress, HexStr
from eth_typeshed.uniswap_v3.events import V3SwapEvent, V3SwapEventType
from tweepy import Tweet
from tweepy.client import Client

from emp_hooks import log, onchain, scheduler
from emp_hooks.handlers import twitter

# Configure logging
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)


@onchain.on_event(
    V3SwapEvent,
    Base,
    address=HexAddress(HexStr("0xb4CB800910B228ED3d0834cF79D697127BBB00e5")),
    start_block=28048000,
    # forces the start block to be overwritten, otherwise resumes from the last checkpoint
    force_set_block=True,
)
def log_eth_price(event_data: EventData[V3SwapEventType]):
    event = event_data.event
    amount0 = event.amount0 / 1e18
    amount1 = event.amount1 / 1e6

    price = abs(amount1 / amount0)
    log.debug("ETH Price: %s", price)


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


@scheduler.on_schedule("* * * * *")
def print_hello():
    print("Hello, world!")


@scheduler.on_schedule(execution_frequency=15)
def print_hello_quickly():
    print("Hello again!")
