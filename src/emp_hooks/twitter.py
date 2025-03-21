import functools
import json
import os
import sys
from typing import Any, Callable

from tweepy import Tweet

from .hook_manager import hooks

_twitter_queries = set()


def _register_twitter_query(twitter_query: str):
    _twitter_queries.add(twitter_query)

    if schemata_path := os.environ.get("SCHEMATA_FILEPATH"):
        try:
            os.makedirs(os.path.dirname(schemata_path), exist_ok=True)
            with open(schemata_path, "w") as f:
                json.dump({"twitter_queries": list(_twitter_queries)}, f)
        except IOError as e:
            print(f"Warning: Could not write to {schemata_path}: {e}")


def on_tweet(twitter_query: str):
    def tweet_handler(func: Callable[[Tweet], Any]):
        @functools.wraps(func)
        def execute_tweet(data):
            tweet_json = json.loads(data["data"])
            tweet = Tweet(tweet_json)
            result = func(tweet)
            sys.stdout.flush()
            return result

        _register_twitter_query(twitter_query)
        hooks.add_hook(twitter_query, execute_tweet)
        hooks.run()

        return execute_tweet

    return tweet_handler
