from cs50 import SQL

db = SQL("sqlite:///finance.db")

username = "tim"
hash = "$6$rounds=656000$X45uEcVzvzqZZF7M$JHvoMRPfDSyW2pv1e5g39FO6ckIM2JiYsd9IyI0H9qmrHgu7.OwLJHio1iTSpQsFLZhai/nStfJ63ypJgRFem/"

(db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash_1)", 
        username=username, hash_1=hash))
