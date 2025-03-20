import os
import json
from typing import Any, Callable

from tweepy import Tweet
from .hook_manager import hooks

_twitter_queries = set()

def _register_twitter_query(twitter_query: str):
    _twitter_queries.add(twitter_query)

    if schemata_path := os.environ.get("SCHEMATA_FILEPATH"):
        try:
            with open(schemata_path, 'w') as f:
                json.dump({"twitter_queries": list(_twitter_queries)}, f)
        except IOError as e:
            print(f"Warning: Could not write to {schemata_path}: {e}")

def on_tweet(twitter_query: str):
    def tweet_handler(func: Callable[[Tweet], Any]):
        return func

    _register_twitter_query(twitter_query)

    hooks.add_hook("tweet", tweet_handler)
    hooks.run()

    return tweet_handler
