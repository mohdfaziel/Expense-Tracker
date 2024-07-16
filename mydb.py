import sqlite3

class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS expense_record (category_name text, item_name text, item_price float, purchase_date date, budget float)"
        )
        self.conn.commit()

    def fetchRecord(self, query):
        self.cur.execute(query)
        rows = self.cur.fetchall()
        return rows

    def insertRecord(self, category_name, item_name, item_price, purchase_date, budget):
        self.cur.execute("INSERT INTO expense_record (category_name, item_name, item_price, purchase_date, budget) VALUES (?, ?, ?, ?, ?)",
                 (category_name, item_name, item_price, purchase_date, budget))

        self.conn.commit()

    def removeRecord(self, rwid):
        self.cur.execute("DELETE FROM expense_record WHERE rowid=?", (rwid,))
        self.conn.commit()

    def updateRecord(self, category_name, item_name, item_price, purchase_date, budget, rid):
        self.cur.execute("UPDATE expense_record SET category_name = ?, item_name = ?, item_price = ?, purchase_date = ?, budget = ? WHERE rowid = ?",
                         (category_name, item_name, item_price, purchase_date, budget, rid))
        self.conn.commit()

    def __del__(self):
        self.conn.close()