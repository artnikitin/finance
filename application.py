from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *
from stocks import fifo, lifo, margin

import datetime

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("postgres://rtftnncsrjvkls:f29bddfd0f3e72b02b61ad562531d83473978451f816e1a6dc7d03b083c0c288@ec2-54-221-220-59.compute-1.amazonaws.com:5432/d5a5bl2nfuatkj")

@app.route("/")
@login_required
def index():
    
    # get cash
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
    
    # check the portfolio
    stocks = db.execute("SELECT shares, amount FROM portfolio WHERE user_id = :user_id", user_id = session["user_id"])
    
    # total revenue
    total_revenue = 0
    
    # if empty, return an empty index page with cash and total
    if not stocks:
        return render_template ("index_empty.html", cash=cash)
    
    # if not empty, update the portfolio with current prices for each stock
    for stock in stocks:
        
        # check current prices
        update_cash = lookup(stock["shares"])
        
        # update portfolio
        (db.execute("UPDATE portfolio SET price = :price, total = :total WHERE user_id = :user_id and shares = :shares", 
                price = update_cash["price"], total = update_cash["price"] * stock["amount"],
                user_id = session["user_id"], shares = stock["shares"]))
        
        # select sum values of amount and price for counting average
        sum_values = (db.execute("SELECT SUM(amount), SUM(price) FROM log WHERE user_id = :user_id and share = :share", 
                    user_id = session["user_id"], share = stock["shares"]))
        
        # download average price from log
        avg_price = sum_values[0]["SUM(price)"] / sum_values[0]["SUM(amount)"]
                    
        # count the average interest rate         
        interest_rate = update_cash["price"] * 100.0 / avg_price - 100.0
        
        # update interest
        (db.execute("UPDATE portfolio SET interest = :interest WHERE user_id = :user_id and shares = :shares",
                    interest = round(interest_rate, 2), user_id = session["user_id"], shares = stock["shares"]))
    
    # avoid adding zero values
    filtered_interest = db.execute("SELECT SUM(interest), COUNT(interest) FROM portfolio WHERE user_id = :user_id and interest NOT LIKE 0", user_id = session["user_id"])
    
    # count total revenue
    total_revenue = round((filtered_interest[0]["SUM(interest)"] / filtered_interest[0]["COUNT(interest)"]), 2)
    
    # get back the updated portfolio with prices           
    stocks_new = db.execute("SELECT * FROM portfolio WHERE user_id = :user_id", user_id = session["user_id"])
    
    # counting total assets (cash + current price of all stocks in portfolio)
    assets_list = db.execute("SELECT SUM(total) FROM portfolio WHERE user_id = :user_id", user_id = session["user_id"])
    
    # SUM call returns a dict of type [{'SUM(total)': <value>}]
    assets = assets_list[0]["SUM(total)"] + cash[0]["cash"]
    
    return render_template("index.html", stocks=stocks_new, cash=cash, assets=assets, total_revenue=total_revenue)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "POST":
        
        # handle invalid user requests
        if not request.form.get("share"):
            return apology("no shares provided")
        
        elif not lookup(request.form.get("share")):
            return apology("share not found")
        
        elif "'" in request.form.get("share") or ";" in request.form.get("share") or request.form.get("share").isnumeric():
            return apology("incorrect share input")
        
        elif not request.form.get("amount"):
            return apology("provide amount of shares to buy")
            
        elif request.form.get("amount").isalpha() or "'" in request.form.get("amount") or ";" in request.form.get("amount"):
            return apology("incorrect amount")
        
        elif int(request.form.get("amount")) <= 0:
            return apology("give me a positive number of shares")
            
        # check if user has enough money
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        
        stock_price = lookup(request.form.get("share"))
        purchase = stock_price["price"] * int(request.form.get("amount"))
        
        if cash[0]["cash"] < purchase:
            return apology("Sorry, not enough cash")
        
        # purchase stocks
        
        (db.execute("INSERT INTO transactions (user_id, share, amount, price, date) VALUES (:user_id, :share, :amount, :price, :date)", 
                    user_id = session["user_id"], share = stock_price["symbol"], amount = int(request.form.get("amount")),
                    price = purchase, date = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")))
        
        # log the transaction         
        db.execute("INSERT INTO log (transaction_id, user_id, share, amount, price, date) SELECT id, user_id, share, amount, price, date FROM transactions WHERE id = (SELECT MAX(id) FROM transactions)")
        (db.execute("UPDATE log SET price_per_share=((SELECT price FROM log WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log)) / (SELECT amount FROM log WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log))) WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log)", 
                    user_id = session["user_id"]))
        
        # charge the user
        db.execute("UPDATE users SET cash = (cash - :cash) WHERE id = :id", cash = purchase, id = session["user_id"])
        
        # update portfolio
        in_portfolio = (db.execute("UPDATE portfolio SET amount = (amount + :amount) WHERE user_id = :user_id AND shares = :shares",
                        amount = int(request.form.get("amount")), user_id = session["user_id"], shares = stock_price["symbol"]))
        
        if not in_portfolio:
            db.execute("INSERT INTO portfolio (user_id, shares, amount, name) VALUES (:user_id, :shares, :amount, :name)", user_id = session["user_id"], shares = stock_price["symbol"], amount = int(request.form.get("amount")), name = stock_price["name"])
        
        flash("Bought!")        
        return redirect(url_for("index"))
    
    else:
        return render_template("buy.html")
        
@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
    # download transactions
    list_of_transactions = (db.execute("SELECT share, amount, price, date FROM transactions WHERE user_id = :user_id",
                            user_id = session["user_id"]))
                            
    # return apology if no history yet
    if not list_of_transactions:
        return apology("No history yet")
    
    return render_template("history.html", transactions=list_of_transactions)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    
    # if user entered quotes
    if request.method == "POST":
        
        # check for blank form
        if not request.form.get("quote"):
            return apology("no quote provided")
        
        # check for valid quote
        quote = lookup(request.form.get("quote"))
        if not quote:
            return apology("quote not found")
        else:
            return render_template("quoted.html", name=quote["name"], symbol=quote["symbol"], price=usd(quote["price"]))
            
    # if user arrived via GET    
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # forget any user_id
    session.clear()

    # if user submitted the register form
    if request.method == "POST":

        # check if fields aren't blank
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("username").isalpha() and not request.form.get("username").isdigit():
            return apology("username must not contain punctuation")
        if not request.form.get("password"):
            return apology("missing password")
        if not request.form.get("password_confirm"):
            return apology("please, confirm password")

        # compare passwords
        if request.form.get("password") != request.form.get("password_confirm"):
            apology("passwords don't match")

        # check for unique username
        unique_username = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if not unique_username:
            apology("username already exists")

        # hash the password
        hash_password = pwd_context.hash(request.form.get("password"))

        print(request.form.get("username"))
        print(hash_password)
        
        usernameZZZ = request.form.get("username")
        
        # save new username and password
        db.execute("""INSERT INTO users (username, hash) 
                      VALUES (:username, :hash_1)""", 
                      username = usernameZZZ, 
                      hash_1 = hash_password)
        
        
        # query for new user
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        print(rows)
        # save user to session
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # if user reaches the route via GET
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "POST":
        
        # handle empty request and not valid shares
        if not request.form.get("share"):
            return apology("no shares provided")
        
        # check shares
        check_shares = lookup(request.form.get("share"))
        
        # report if incorrect symbol
        if not check_shares:
            return apology("incorrect share symbol")
        
        # check if user has the queried shares
        in_portfolio = (db.execute("SELECT shares, amount FROM portfolio WHERE user_id = :id and shares = :shares",
                        shares = check_shares["symbol"], id = session["user_id"]))
        if not in_portfolio:
            return apology("you don't have selected shares")
            
        # check for empty amount
        if not request.form.get("amount"):
            return apology("provide amount of shares to buy")
        
        # SQL injection   
        if "'" in request.form.get("amount") or ";" in request.form.get("amount") or request.form.get("amount").isalpha():
            return apology("incorrect amount input")
        
        # handle nonpositive inputs
        elif int(request.form.get("amount")) <= 0:
            return apology("give me a positive number of shares")
            
        elif int(request.form.get("amount")) > in_portfolio[0]["amount"]:
            return apology("you don't have so many shares")
        
        # sell stocks
        (db.execute("INSERT INTO transactions (user_id, share, amount, price, date) VALUES (:user_id, :share, :amount, :price, :date)", 
                    user_id = session["user_id"], share = check_shares["symbol"], amount = -(int(request.form.get("amount"))),
                    price = check_shares["price"], date = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")))
        
        # check the selected sell type
        sell_type = db.execute("SELECT sell_type FROM users WHERE id = :id", id=session["user_id"])
        
        # update log
        if sell_type[0]["sell_type"] == "FIFO":
            fifo("amount", session["user_id"], check_shares["symbol"])
                    
        elif sell_type[0]["sell_type"] == "LIFO":
            lifo("amount", session["user_id"], check_shares["symbol"])
                    
        elif sell_type[0]["sell_type"] == "MARGIN":
            margin("amount", session["user_id"], check_shares["symbol"])
            
        # send cash
        db.execute("UPDATE users SET cash = (cash + :cash) WHERE id = :id", cash = check_shares["price"], id = session["user_id"])
        
        # update portfolio
        (db.execute("UPDATE portfolio SET amount = (amount + :amount) WHERE user_id = :user_id AND shares = :shares",
                        amount = -(int(request.form.get("amount"))), user_id = session["user_id"], shares = check_shares["symbol"]))
        
        # delete stock from portfolio if number of shares is 0
        zero_shares = (db.execute("SELECT amount FROM portfolio WHERE user_id = :user_id and shares = :shares", 
                        user_id = session["user_id"], shares = check_shares["symbol"]))
        if zero_shares[0]["amount"] == 0:
            (db.execute("DELETE FROM portfolio WHERE user_id = :user_id and shares = :shares", 
            user_id = session["user_id"], shares = check_shares["symbol"]))
    
        flash("Sold!")
        return redirect(url_for("index"))
    
    else:
        return render_template("sell.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """ gives the user a selection of selling algorithms """
    
    if request.method == "POST":
        if request.form.get("checkbox") == "FIFO":
            db.execute("UPDATE users SET sell_type='FIFO' WHERE id = :id", id=session["user_id"])
            flash("You've picked FIFO!")
            return redirect(url_for("profile"))
            
        elif request.form.get("checkbox") == "LIFO":
            db.execute("UPDATE users SET sell_type='LIFO' WHERE id = :id", id=session["user_id"])
            flash("You've picked LIFO!")
            return redirect(url_for("profile"))
            
        elif request.form.get("checkbox") == "MARGIN":
            db.execute("UPDATE users SET sell_type='MARGIN' WHERE id = :id", id=session["user_id"])
            flash("You've picked MARGIN!")
            return redirect(url_for("profile"))
    else:
        rows = db.execute("SELECT sell_type FROM users WHERE id = :id", id = session["user_id"])
        return render_template("profile.html", sell_type = rows[0]["sell_type"])