import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()

    def user_exists(self, user_id):
        self.cur.execute("SELECT * FROM users WHERE userid=?", (user_id,))
        return bool(self.cur.fetchone())

    def add_user(self, user_id, username, fullname):
        self.cur.execute("INSERT INTO users (userid, username, fullname) VALUES (?, ?, ?)", (user_id, username, fullname))
        self.conn.commit()

    def add_subs(self, userid, payMethod):
        self.cur.execute("INSERT INTO subs (subsuser, pay_method) VALUES (?, ?)", (userid, payMethod))
        self.conn.commit()

    def get_user(self, userid):
        return self.cur.execute("SELECT username, fullname FROM users WHERE userid=?", (userid,)).fetchone()

    def get_subs(self, userid):
        self.cur.execute("SELECT * FROM subs WHERE subsuser = ?", (userid,))
        return bool(self.cur.fetchone())
       
    def update_subs(self, userid):
        self.cur.execute("UPDATE subs SET start_sub = ? WHERE subsuser = ?", (datetime.now(), userid))
        self.conn.commit()

    def delete_user(self, user_id):
        self.cur.execute("DELETE FROM subs WHERE id = ?", (user_id,))
        self.conn.commit()
