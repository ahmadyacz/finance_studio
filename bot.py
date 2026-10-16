# bot.py
# Telegram bot: send a photo of a QR code / barcode.
#   - If the product is known    -> the bot replies with its name and price.
#   - If the product is unknown  -> the bot asks for "name, price" and saves it.

import os

import cv2
import numpy as np
from cs50 import SQL
from dotenv import load_dotenv
from pyzbar.pyzbar import decode
from telegram.ext import ApplicationBuilder, MessageHandler, filters


# =========================================================
# 1. SETTINGS  (change the texts here if you want)
# =========================================================

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Same database file as app.py, no matter where the bot is started from
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")
CURRENCY = "DZ"

MSG_CANT_READ = "I couldn't read a code. Send a closer, sharper photo."
MSG_NOT_REGISTERED = "Not registered. Send the name and price and category and symbol like this:\nMilk 1L, 120, Food, MILK"
MSG_WRONG_FORMAT = "Wrong format. Try: Milk 1L, 120, Food, MILK"
MSG_NO_USER = "No account yet. Open the website and register first."
MSG_SEND_PHOTO_FIRST = "Send me a photo of a code first."


# =========================================================
# 2. DATABASE
# =========================================================

open(DATABASE_FILE, "a").close()
db = SQL(f"sqlite:///{DATABASE_FILE}")


def find_product(code):
    rows = db.execute("SELECT name, price, category, symbol FROM items WHERE qrcode = ?", code)
    if len(rows) == 0:
        return None
    return rows[0]


def add_product(code, name, price, category, symbol):
    price = round(price)
    existing = db.execute("SELECT symbol FROM items WHERE symbol = ?", symbol)

    if existing:
        # Symbol already exists (maybe added from the website): attach this code to it
        db.execute("UPDATE items SET qrcode = ? WHERE symbol = ?", code, symbol)
    else:
        db.execute(
            "INSERT INTO items (qrcode, name, price, category, symbol) VALUES (?, ?, ?, ?, ?)",
            code, name, price, category.lower(), symbol,
        )
    return db.execute("SELECT name, price, category, symbol FROM items WHERE symbol = ?", symbol)[0]


def record_purchase(product):
    """Log the purchase and take the money out, exactly like the website does."""
    db.execute(
        "INSERT INTO phistory (name, amount, category, symbol) VALUES (?, ?, ?, ?)",
        product["name"], product["price"], product["category"], product["symbol"],
    )
    db.execute("UPDATE user SET cash = cash - ?", product["price"])


# =========================================================
# Maded by AI
# =========================================================

def read_code(image_bytes):
    # Turn the raw bytes into an image
    array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        return None

    # Grayscale makes detection easier
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Look for codes in the image
    results = decode(gray)
    if len(results) == 0:
        return None

    return results[0].data.decode()


def parse_name_and_price(text):
    """Turn 'Milk 1L, 120' into ('Milk 1L', 120.0). Return None if invalid."""
    try:
        name, price, category, symbol = text.rsplit(",", 3)   # split on the LAST comma
        name = name.strip()
        price = float(price)
        category = category.strip()
        symbol = symbol.strip()
    except ValueError:
        return None

    if name == "" or price <= 0 or category == "" or symbol == "":
        return None

    return name, price, category, symbol



async def handle_photo(update, context):
    """The user sent a photo."""

    # Download the biggest version of the photo
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = bytes(await photo_file.download_as_bytearray())

    # Read the code from the photo
    code = read_code(image_bytes)
    if code is None:
        await update.message.reply_text(MSG_CANT_READ)
        return

    # Is this product already in the database?
    product = find_product(code)

    if product is not None:
        # Known product: record the purchase (shows up on the website)
        if not db.execute("SELECT 1 FROM user"):
            await update.message.reply_text(MSG_NO_USER)
            return
        record_purchase(product)
        await update.message.reply_text(f"Purchase recorded: {product['name']} - {product['price']} {CURRENCY} - {product['category']} - {product['symbol']}")
    else:
        # Unknown product: remember the code and wait for the next message
        context.user_data["new_code"] = code
        await update.message.reply_text(MSG_NOT_REGISTERED)


async def handle_text(update, context):
    """The user sent text (we expect 'name, price' after an unknown code)."""

    # Did the user send a photo of an unknown code before?
    code = context.user_data.get("new_code")
    if code is None:
        await update.message.reply_text(MSG_SEND_PHOTO_FIRST)
        return

    # Read the name and price from the message
    result = parse_name_and_price(update.message.text)
    if result is None:
        await update.message.reply_text(MSG_WRONG_FORMAT)
        return

    name, price, category, symbol = result

    if not db.execute("SELECT 1 FROM user"):
        await update.message.reply_text(MSG_NO_USER)
        return

    # Save the product, record the purchase, and forget the waiting code
    product = add_product(code, name, price, category, symbol)
    record_purchase(product)
    del context.user_data["new_code"]

    await update.message.reply_text(f"Registered and purchase recorded: {product['name']} - {product['price']} {CURRENCY} - {product['category']} - {product['symbol']}")


# =========================================================
# 5. START THE BOT
# =========================================================

def main():
    if TOKEN is None:
        raise ValueError("TELEGRAM_TOKEN not set")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running... press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()