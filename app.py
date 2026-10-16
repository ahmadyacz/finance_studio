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



@app.route("/", methods=["POST", "GET"])
def index():
    render_date = {}
    render_date["start"] = get_timestamp("month", "start")
    render_date["end"] = get_timestamp("month", "end")
    user_info = db.execute("SELECT * FROM user")
    if not user_info:
        return redirect("/register")
    if request.args.get("period") == "week":
        render_date["start"] = get_timestamp("week", "start")
        render_date["end"] = get_timestamp("week", "end")
    elif request.args.get("period") == "custom":
        render_date["start"] = request.args.get("from")
        render_date["end"] = request.args.get("to")
        if not render_date["start"] or not render_date["end"]:
            return redirect("/")
    ahistory = db.execute("SELECT * FROM ahistory WHERE ? < date < ?", render_date["start"], render_date["end"])

    
    if request.method == "POST":
        # Adding money function
        added_amount = request.form.get("added_amount")
        if added_amount:
            db.execute("INSERT INTO ahistory (amount, description) VALUES (?, ?)", added_amount, request.form.get("description"))
            db.execute("UPDATE user SET cash = cash + ? WHERE name = ?", float(added_amount), user_info[0]["name"])
            return redirect("/")
        # -------------------------------------------------------
    

    # Add a purchase
    
    # -------------------------------------------------------
    
    # Rendering the index page
    return render_template("index.html", current_cash=user_info[0]["cash"], currency=CURRENCY, history=ahistory)

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
