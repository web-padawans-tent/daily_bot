import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()

    def user_exists(self, user_id):
        self.cur.execute("SELECT * FROM users WHERE userid=?", (user_id,))
        return bool(self.cur.fetchone())

    def add_user(self, user_id, username, fullname):
        self.cur.execute(
            "INSERT INTO users (userid, username, fullname) VALUES (?, ?, ?)", (user_id, username, fullname))
        self.conn.commit()

    def add_subs(self, userid, payMethod, order_reference):
        now = datetime.now().replace(microsecond=0)
        next_month = now + relativedelta(months=1)
        self.cur.execute(
            "INSERT INTO subs (subsuser, pay_method, start_sub, next_sub, order_reference) VALUES (?, ?, ?, ?, ?)",
            (userid, payMethod, now, next_month, order_reference)
        )
        self.conn.commit()

    def get_user(self, userid):
        return self.cur.execute("SELECT username, fullname FROM users WHERE userid=?", (userid,)).fetchone()

    def get_subs(self, userid):
        self.cur.execute("SELECT * FROM subs WHERE subsuser = ?", (userid,))
        return bool(self.cur.fetchone())

    def update_subs(self, userid, payMethod, order_reference):
        now = datetime.now().replace(microsecond=0)
        next_month = now + relativedelta(months=1)
        self.cur.execute(
            "UPDATE subs SET pay_method = ?, start_sub = ?, next_sub = ?, tried_pay = ?, order_reference = ? WHERE subsuser = ?",
            (payMethod, now, next_month, now, order_reference, userid)
        )
        self.conn.commit()

    def payment_attempt(self, user_id):
        now = datetime.now().replace(microsecond=0)
        self.cur.execute(
            "UPDATE subs SET tried_pay = ? WHERE subsuser = ?", (now, user_id))
        self.conn.commit()
