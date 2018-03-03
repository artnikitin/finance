from cs50 import SQL
from flask import session, request

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

def fifo(request_name, user_num, share_symbol):
    """ sells stocks via FIFO (First in First Out) algorithm """

    for share in range(int(request.form.get(request_name))):
        amount_price = db.execute("SELECT amount, price, price_per_share FROM log WHERE user_id = :user_id and id = (SELECT MIN(id) FROM log WHERE user_id = :user_id and share = :share) and share = :share", user_id = user_num, share = share_symbol)    
                
        amount = amount_price[0]["amount"]
        price = amount_price[0]["price"]
        price_per_share = amount_price[0]["price_per_share"]
                
        if amount >= 1:
            db.execute("UPDATE log SET amount = :amount_var WHERE user_id = :user_id and id = (SELECT MIN(id) FROM log WHERE user_id = :user_id and share = :share)", amount_var = amount - 1, user_id = user_num, share = share_symbol)
        if price > price_per_share:
            db.execute("UPDATE log SET price = :price_var WHERE user_id = :user_id and id = (SELECT MIN(id) FROM log WHERE user_id = :user_id and share = :share)", user_id = user_num, price_var = price - price_per_share, share = share_symbol)
        db.execute("DELETE FROM log WHERE user_id = :user_id and amount = 0", user_id = user_num)
    return

def lifo(request_name, user_num, share_symbol):
    """ sells stocks via LIFO (Last in First Out) algorithm """
    
    for share in range(int(request.form.get(request_name))):
        amount_price = db.execute("SELECT amount, price, price_per_share FROM log WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log WHERE user_id = :user_id and share = :share) and share = :share", user_id = user_num, share = share_symbol)    
                
        amount = amount_price[0]["amount"]
        price = amount_price[0]["price"]
        price_per_share = amount_price[0]["price_per_share"]
                
        if amount >= 1:
            db.execute("UPDATE log SET amount = :amount_var WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log WHERE user_id = :user_id and share = :share)", amount_var = amount - 1, user_id = user_num, share = share_symbol)
        if price > price_per_share:
            db.execute("UPDATE log SET price = :price_var WHERE user_id = :user_id and id = (SELECT MAX(id) FROM log WHERE user_id = :user_id and share = :share)", user_id = user_num, price_var = price - price_per_share, share = share_symbol)
        db.execute("DELETE FROM log WHERE user_id = :user_id and amount = 0", user_id = user_num)
    return
    
def margin(request_name, user_num, share_symbol):
    """ sells stocks via MARGIN (sell stocks with the lowerst purchase price) algorithm """
       
    for share in range(int(request.form.get(request_name))):
        amount_price = db.execute("SELECT amount, price, price_per_share FROM log WHERE user_id = :user_id and id = (SELECT MIN(price_per_share) FROM log WHERE user_id = :user_id and share = :share) and share = :share", user_id = user_num, share = share_symbol)
        
        if not amount_price:
            fifo(request_name, user_num, share_symbol)
            return
        
        amount = amount_price[0]["amount"]
        price = amount_price[0]["price"]
        price_per_share = amount_price[0]["price_per_share"]
                
        if amount >= 1:
            db.execute("UPDATE log SET amount = :amount_var WHERE user_id = :user_id and id = (SELECT MIN(price_per_share) FROM log WHERE user_id = :user_id and share = :share)", amount_var = amount - 1, user_id = user_num, share = share_symbol)
        if price > price_per_share:
            db.execute("UPDATE log SET price = :price_var WHERE user_id = :user_id and id = (SELECT MIN(price_per_share) FROM log WHERE user_id = :user_id and share = :share)", user_id = user_num, price_var = price - price_per_share, share = share_symbol)
        db.execute("DELETE FROM log WHERE user_id = :user_id and amount = 0", user_id = user_num)
    return