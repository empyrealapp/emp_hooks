import logging
import os
from textwrap import dedent

from eth_rpc import EventData
from eth_rpc.networks import Base, Ethereum
from eth_typeshed.chainlink.eth_usd_feed import ChainlinkPriceOracle, ETHUSDPriceFeed
from eth_typeshed.erc20 import ERC20
from eth_typeshed.uniswap_v3.events import V3SwapEvent, V3SwapEventType
from eth_typeshed.uniswap_v3.pool import UniswapV3Pool
from eth_typing import HexAddress, HexStr
from tweepy.client import Client

from emp_hooks import log, manager, onchain

ETH_ADDRESS = HexAddress(HexStr("0x4200000000000000000000000000000000000006"))
ETH_PRICE: float = -1.0
token_cache = {}
symbol_cache = {}

# Configure logging
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)


def get_eth_price():
    eth_address = ChainlinkPriceOracle.Ethereum.ETH
    eth_price_feed = ETHUSDPriceFeed[Ethereum](address=eth_address)
    price = eth_price_feed.latest_round_data().get(sync=True)
    return price.answer / 1e8


if os.environ.get("ENVIRONMENT", "").lower() == "production":
    client = Client(
        bearer_token=os.environ["TWITTER_BEARER_TOKEN"],
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
else:
    # create a printer class to mimick tweeting for testing

    class TwitterMock:
        def create_tweet(self, text: str):
            print("TWEET:", text)

    client = TwitterMock()


@onchain.on_event(
    V3SwapEvent,
    Base,
    # only subscribe to current events
    subscribe=True,
)
def log_eth_price(event_data: EventData[V3SwapEventType]):
    global ETH_PRICE
    if ETH_PRICE == -1.0:
        ETH_PRICE = get_eth_price()
        log.debug("Initial ETH Price: %s", ETH_PRICE)

    event = event_data.event
    address = event_data.log.address
    amount0 = event.amount0
    amount1 = event.amount1

    pool = UniswapV3Pool[Base](address=address)
    if address not in token_cache:
        token0 = pool.token0().get(sync=True)
        token1 = pool.token1().get(sync=True)
        token_cache[address] = (token0, token1)

    token0, token1 = token_cache[address]

    if address == "0xb4CB800910B228ED3d0834cF79D697127BBB00e5":
        _amount0 = amount0 / 1e18
        _amount1 = amount1 / 1e6
        ETH_PRICE = abs(_amount1 / _amount0)
        log.debug("ETH Price: %s", ETH_PRICE)

    token_symbol: str
    buy_amount: float = 0.0
    sell_amount: float = 0.0

    if token0 == ETH_ADDRESS:
        if token1 not in symbol_cache:
            token_symbol = ERC20[Base](address=token1).symbol().get(sync=True)
            symbol_cache[token1] = token_symbol

        token_symbol = symbol_cache[token1]
        if amount0 > 0:
            buy_amount = abs(amount0 / 1e18 * ETH_PRICE)
        else:
            sell_amount = abs(amount0 / 1e18 * ETH_PRICE)
    elif token1 == ETH_ADDRESS:
        if token0 not in symbol_cache:
            token_symbol = ERC20[Base](address=token0).symbol().get(sync=True)
            symbol_cache[token0] = token_symbol
        token_symbol = symbol_cache[token0]
        if amount1 > 0:
            buy_amount = abs(amount1 / 1e18 * ETH_PRICE)
        else:
            sell_amount = abs(amount1 / 1e18 * ETH_PRICE)
    else:
        return

    if buy_amount > 0:
        log.debug(
            "Buy Amount: %s | tx_hash: %s", buy_amount, event_data.log.transaction_hash
        )
    elif sell_amount > 0:
        log.debug(
            "Sell Amount: %s | tx_hash: %s",
            sell_amount,
            event_data.log.transaction_hash,
        )

    if buy_amount > 10_000:
        client.create_tweet(
            text=dedent(
                f"""
            Large Buy
            --------------------------------
            ${buy_amount:,.2f} of {token_symbol}
            token address: {address}
            tx hash: {event_data.log.transaction_hash}
        """
            )
        )
    elif sell_amount > 10_000:
        client.create_tweet(
            text=dedent(
                f"""
            Large Sell
            --------------------------------
            ${sell_amount:,.2f} of {token_symbol}
            token address: {address}
            tx hash: {event_data.log.transaction_hash}
        """
            )
        )


if __name__ == "__main__":
    manager.hooks.run_forever()
