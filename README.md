# itb

### Infratrix Telegram Bot

#### Overview

Infratrix is a simple and easy-to-use Telegram bot developed using the official [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) Python library.  
It leverages Webhook processes, allowing it to be hosted on Google's free AppEngine hosting service.  

#### Features

* Simple and Intuitive: The bot is designed to be straightforward and user-friendly.
* Webhook Integration: Utilizes Webhook processes for efficient communication.
* Free Hosting: Can be hosted on Google's AppEngine at no cost.

#### Installation

Clone the Repository:

```bash
git clone https://github.com/carpaty/itb.git
cd itb
cp app.yaml.example app.yaml
cp src/menu.yaml.example src/menu.yaml
cp src/calls/button_func.py.example src/calls/button_func.py
```

Install Dependencies:  
Ensure you have Python installed, then run:  

```bash
pip install -r requirements.txt
```

Set Up Your Bot:  
Create a new bot on Telegram using BotFather and get the API token. Replace TELEGRAM_TOKEN, TELEGRAM_WEBHOOK_URL in the app.yaml file with your actual token and url.  

Configure Webhook:  
Set up your webhook URL. You will need a publicly accessible URL for this or use Google's URL.

```yaml
env_variables:
  TELEGRAM_TOKEN: 111111:AAAAAAA
  TELEGRAM_WEBHOOK_URL: https://example.com
```


#### Hosting on Google AppEngine

[Install](https://cloud.google.com/sdk/docs/install) Google Cloud SDK 

Initialize Google Cloud SDK:

```bash
gcloud init
```

Deploy to AppEngine:  

```bash
gcloud app deploy
gcloud app deploy cron.yaml
```

#### Usage

Once deployed, the bot will listen to incoming messages and respond based on the defined handlers.  
You can customize the bot's behavior by modifying the handlers in the main.py file.  

#### Conclusion

Infratrix Telegram Bot is a powerful yet easy-to-use tool for creating Telegram bots.  
By leveraging the python-telegram-bot library and Google's AppEngine, you can quickly deploy a robust bot with minimal effort.  

For more detailed information, refer to the official python-telegram-bot documentation.
