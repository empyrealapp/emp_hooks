import os
from typing import Any, Callable

import requests
from tweepy import Tweet

from .hook_manager import hooks


def _register_twitter_username(twitter_username: str):
    requests.post(
        os.environ["TWITTER_USERNAME_REGISTRATION_URL"],
        json={"twitter_username": twitter_username},
        headers={"Authorization": f"Bearer {os.environ['EMP_API_KEY']}"},
    )


def on_tweet(twitter_username: str):
    def tweet_handler(func: Callable[[Tweet], Any]):
        return func

    _register_twitter_username(twitter_username)

    hooks.add_hook("tweet", tweet_handler)
    hooks.run()

    return tweet_handler
