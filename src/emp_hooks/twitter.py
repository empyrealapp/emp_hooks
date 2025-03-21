import functools
import json
import os
import sys
from typing import Callable

from tweepy import Tweet

from .sqs_hooks import hooks

_twitter_queries = set()


def _register_twitter_query(twitter_query: str):
    _twitter_queries.add(twitter_query)

    if schemata_path := os.environ.get("SCHEMATA_FILEPATH"):
        os.makedirs(os.path.dirname(schemata_path), exist_ok=True)

        try:
            with open(schemata_path, "r") as f:
                data = json.loads(f.read() or "{}")
        except IOError:
            data = {}

        with open(schemata_path, "w") as f:
            data["twitter_queries"] = list(_twitter_queries)
            json.dump(data, f)


def on_tweet(
    twitter_query: str,
    visibility_timeout: int = 30,
    loop_interval: int = 5,
    daemon: bool = False,
):
    """
    A tweet_handler must take a tweepy Tweet as an argument,
    and will return a bool to let the queue consumer know if it
    should delete the tweet.
    """

    def tweet_handler(func: Callable[[Tweet], bool]):
        @functools.wraps(func)
        def execute_tweet(data):
            tweet_json = json.loads(data["data"])
            tweet = Tweet(tweet_json)
            result = func(tweet)
            sys.stdout.flush()
            return result

        _register_twitter_query(twitter_query)
        hooks.add_hook(twitter_query, execute_tweet)
        hooks.run(
            visibility_timeout=visibility_timeout,
            loop_interval=loop_interval,
            daemon=daemon,
        )

        return execute_tweet

    return tweet_handler
