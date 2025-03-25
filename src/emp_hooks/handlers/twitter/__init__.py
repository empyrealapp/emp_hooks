import functools
import json
import os
import sys
from typing import Callable

from tweepy import Tweet

from ..sqs_hooks import sqs_hooks

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
    Decorator to register a function to handle tweets matching a specific query.

    Args:
        twitter_query (str): The Twitter query string to filter tweets.
        visibility_timeout (int, optional): The visibility timeout for the SQS message. Defaults to 30.
        loop_interval (int, optional): The interval in seconds between each poll of the SQS queue. Defaults to 5.
        daemon (bool, optional): Whether the SQS consumer thread should run as a daemon. Defaults to False.

    Returns:
        Callable: A decorator that registers the function to handle tweets matching the specified query.
    """

    def tweet_handler(func: Callable[[Tweet], bool]):
        """
        A tweet_handler must take a tweepy Tweet as an argument,
        and will return a bool to let the queue consumer know if it
        should delete the tweet.
        """

        @functools.wraps(func)
        def execute_tweet(data):
            tweet_json = json.loads(data["data"])
            tweet = Tweet(tweet_json)
            result = func(tweet)
            sys.stdout.flush()
            return result

        _register_twitter_query(twitter_query)
        sqs_hooks.add_hook(twitter_query, execute_tweet)
        sqs_hooks.run(
            visibility_timeout=visibility_timeout,
            loop_interval=loop_interval,
            daemon=daemon,
        )

        return execute_tweet

    return tweet_handler
