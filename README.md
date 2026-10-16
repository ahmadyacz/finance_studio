# Finance Studio
#### Video Demo: https://www.youtube.com/watch?v=fkkxItQ0YZY
#### Description:

Finance Studio is a money-tracking web application made for students. Students usually live on a small, limited budget, but writing down every purchase by hand is boring, so most of them stop doing it after a few days. Finance Studio makes tracking fast. A student can add money (for example a monthly allowance), record purchases, and look at a full history of everything added and spent. To make recording purchases even quicker, the project also includes a Telegram bot: the student sends a photo of a product's QR code or barcode, and the bot recognizes the product or registers it if it is new.

The project has two programs that share one SQLite database: a Flask web application and a Telegram bot.

## Features

- **Add money:** deposits are saved with a date and increase the balance.
- **Add purchases:** each purchase has a name, price, and category, and decreases the balance.
- **History:** index page lists every deposit and purchase so the student can see where the money went.
- **Telegram bot:** reads a code from a photo, looks the product up, and registers it when it is unknown.

## Files

- `app.py`: the Flask application. It contains the routes for registering, adding money, adding purchases, and showing the history. 
- `bot.py`: the Telegram bot. It listens for messages using the python-telegram-bot library. When a photo arrives, it downloads it, reads the code with OpenCV and pyzbar, and searches the database. If the product exists, the bot replies with its name, price, category, and symbol. If it does not exist, the bot asks the user to send the details in the format `name, price, category, symbol`, then saves them.
- `templates/`: the HTML pages, written with Jinja templates and a shared layout.
- `static/`: the CSS and JavaScript files used by the pages.
- `requirements.txt`: the Python packages the project needs.
- `.env` (not included in the repository): holds the secrets, `TELEGRAM_TOKEN` and `SECRET_KEY`.

## How to run

1. Install the packages: `pip install -r requirements.txt`
2. Create a `.env` file with `TELEGRAM_TOKEN` (from @BotFather on Telegram) and `SECRET_KEY`.
3. Start the website: `flask run`
4. In a second terminal, start the bot: `python bot.py`

## Use of AI tools

As the course allows for the final project, I used AI tools (Claude by Anthropic) as helpers. AI generated the front-end design (the HTML and CSS templates), most of my helper functions, and the first version of the bot's handlers. I then edited and adapted that code, and I designed the idea, the database structure, how the web application and the bot share data, and the product registration flow myself, and I tested everything. The AI-assisted parts are marked with comments in the code.