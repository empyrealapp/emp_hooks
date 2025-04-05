# Emp Hooks

Emp Hooks is a collection of hooks designed to work in conjunction with empctl. This library provides various hooks to handle events, schedules, and Twitter interactions.

## Installation

To install Emp Hooks, use pip:

```bash
pip install emp-hooks
```

## Usage

### Onchain Hooks

Onchain hooks are used to listen for events on a specific blockchain.

```python
from emp_hooks import onchain

@onchain.on_event(
    event=V3SwapEvent,
    network=Base,
)
def log_eth_price(event_data: EventData[V3SwapEventType]):
    event = event_data.event
    amount0 = event.amount0 / 1e18
    amount1 = event.amount1 / 1e6

    price = abs(amount1 / amount0)
    log.debug("ETH Price: %s", price)
```

### Scheduler Hooks

Scheduler hooks are used to schedule functions to run at a specific interval or cron schedule.

```python
from emp_hooks import scheduler

@scheduler.on_schedule(
    execution_frequency="0 0 * * *",
)
def periodic_function():
    print("Do scheduled task")
```

### Twitter Hooks

Twitter hooks are used to listen for tweets matching a specific query.

```python
from emp_hooks import twitter

@twitter.on_tweet(
    query="simmi_io",
)
def on_simmi_tweet(tweet: Tweet):
    print(tweet)
```

### Running Hooks

Make sure to import the manager and call `run_forever` on it.
This will ensure that all hooks are running indefinitely, and will handle the SIGINT and SIGTERM signals to stop the hooks gracefully.

```python
from emp_hooks import manager

if __name__ == "__main__":
    manager.hooks.run_forever()
```

## Contributing


To contribute to Emp Hooks, please follow these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Create a pull request.
