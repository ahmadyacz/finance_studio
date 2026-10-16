from platform import python_revision
import re

from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template



db = SQL("sqlite:///finance.db")

app = Flask(__name__)

CURRENCY = "DZ"


# Ai made this function with a some edits from me
def get_timestamp(period, boundary):
    # error hendling
    if period not in ("month", "week"):
        raise ValueError('period must be "month" or "week"')
    if boundary not in ("start", "end"):
        raise ValueError('boundary must be "start" or "end"')

    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        start = today.replace(day=1)
        if start.month == 12:
            next_start = start.replace(year=start.year + 1, month=1)
        else:
            next_start = start.replace(month=start.month + 1)
    else:
        start = today - timedelta(days=today.weekday())
        next_start = start + timedelta(weeks=1)

    if boundary == "start":
        return start.timestamp()
    return (next_start - timedelta(microseconds=1)).timestamp()

# maded by help of AI
def merge_history(var1, var2):
    merged = [dict(item, type="purchase") for item in var1]
    merged.extend(dict(item, type="add") for item in var2)
    return sorted(merged, key=lambda item: item["date"], reverse=True)



@app.route("/", methods=["POST", "GET"])
def index():
    render_date = {}
    render_date["start"] = get_timestamp("month", "start")
    render_date["end"] = get_timestamp("month", "end")
    user_info = db.execute("SELECT * FROM user")
    if not user_info:
        return redirect("/register")

    
    if request.method == "GET":
        if request.args.get("period") == "week":
            render_date["start"] = get_timestamp("week", "start")
            render_date["end"] = get_timestamp("week", "end")
        elif request.args.get("period") == "custom":
            render_date["start"] = request.args.get("from")
            render_date["end"] = request.args.get("to")
            if not render_date["start"] or not render_date["end"]:
                return redirect("/")
        if not request.args.get("period"):
            period_label = "month"
        else:
            period_label = request.args.get("period")
        
        total_spent = 0
        ahistory = db.execute("SELECT * FROM ahistory WHERE unixepoch(date) >= ? AND unixepoch(date) < ?", render_date["start"], render_date["end"])
        phistory = db.execute("SELECT * FROM phistory WHERE unixepoch(date) >= ? AND unixepoch(date) < ?", render_date["start"], render_date["end"])
        for purchase in phistory:
            total_spent += purchase["amount"]
        history = merge_history(phistory, ahistory)
        return render_template("index.html", current_cash=user_info[0]["cash"], currency=CURRENCY, history=history, period_label=period_label, total_spent=total_spent)

    
    if request.method == "POST":
        # Adding money function
        added_amount = request.form.get("added_amount")
        if added_amount:
            db.execute("INSERT INTO ahistory (amount, description) VALUES (?, ?)", added_amount, request.form.get("description"))
            db.execute("UPDATE user SET cash = cash + ? WHERE name = ?", float(added_amount), user_info[0]["name"])
            return redirect("/")
        # -------------------------------------------------------
        # Add a purchase
        product_name = request.form.get("product_name")
        price = request.form.get("price")
        if price is None:
            return redirect("/")
        category = request.form.get("category")
        symbol = request.form.get("symbol")
        items = db.execute("SELECT * FROM items")
        item_found = False
        product = {}
        for item in items:
            if item["symbol"] == symbol and ( item["price"] == round(float(price)) or round(float(price)) == 0 ):
                item_found = True
                product = item
                break
            elif item["symbol"] == symbol and item["price"] != round(float(price)):
                db.execute("UPDATE items SET price = ? WHERE symbol = ?", round(float(price)), symbol)
                item_found = True
                product = item
                break
        if item_found:
            db.execute("INSERT INTO phistory (name, amount, category, symbol) VALUES (?, ?, ?, ?)", product["name"], product["price"], product["category"], symbol)
            db.execute("UPDATE user SET cash = cash - ? WHERE name = ?", product["price"], user_info[0]["name"])
        elif not item_found and product_name and category and symbol:
            db.execute("INSERT INTO items (name, price, category, symbol) VALUES (?, ?, ?, ?)", product_name, int(price), category.lower(), symbol)
            db.execute("INSERT INTO phistory (name, amount, category, symbol) VALUES (?, ?, ?, ?)", product_name, int(price), category.lower(), symbol)
            db.execute("UPDATE user SET cash = cash - ? WHERE name = ?", int(price), user_info[0]["name"])
        return redirect("/")
        # -------------------------------------------------------
    

    
    
    
    
    # Rendering the index page
    return render_template("index.html", current_cash=user_info[0]["cash"], currency=CURRENCY, history=history)

@app.route("/register", methods=["GET", "POST"])
def register():
    user_info = db.execute("SELECT * FROM user")
    if user_info:
        return redirect("/")
    if request.method == "GET":
        return render_template("register.html")
    if request.form.get("name") and request.form.get("amount"):
        db.execute("INSERT INTO user (name, cash) VALUES (?, ?)", request.form.get("name"), request.form.get("amount"), currency=CURRENCY)
    return redirect("/")
