# Telegram AI Example

This example demonstrates how to build a Telegram bot powered by AI using the EMP framework. The bot maintains conversation history in a database and responds intelligently to messages using OpenAI's API.

## Run Locally

1. Install dependencies:


```bash
pip install -r requirements.txt
```

2. Create a `.env` file and set the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_API_KEY=your_telegram_bot_api_key
```

3. Upgrade local database:

```bash
export DEPLOYMENT_FILESYSTEM_PATH=./db.sqlite
alembic upgrade head
```

4. Run the bot:

```bash
python -m agent.main
```


## Deployment to emp cloud

TODO: quick overview of how to deploy this
