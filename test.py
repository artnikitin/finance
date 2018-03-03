from cs50 import SQL
from helpers import *
# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

update_cash = lookup("GOOG")

sum_values = db.execute("SELECT SUM(amount), SUM(price) FROM log WHERE user_id = 1 and share = 'GOOG'")
        
# download average price from log
avg_price = sum_values[0]["SUM(price)"] / sum_values[0]["SUM(amount)"]

MAX = "(SELECT MAX(id) FROM log WHERE user_id = 1 and share = 'GOOG')"

var = db.execute("SELECT amount, price, price_per_share FROM log WHERE user_id = 1 and id = (SELECT MAX(id) FROM log WHERE user_id = 1 and share = 'GOOG') and share = 'GOOG'")
                    
# count the average interest rate         
interest_rate = update_cash["price"] * 100.0 / avg_price - 100.0

filtered_interest = db.execute("SELECT SUM(interest), COUNT(interest) FROM portfolio WHERE user_id = 2")