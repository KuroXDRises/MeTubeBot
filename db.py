import sqlite3
import json
from datetime import datetime

DB_PATH = "metube.db"

class MongoLikeDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        con = self._connect()
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            uploader INTEGER,
            title TEXT,
            description TEXT,
            tags TEXT,
            views TEXT DEFAULT '[]',
            likes TEXT DEFAULT '[]',
            upload_time TEXT
        )
        """)
        con.commit()
        con.close()

    # ---------------- INSERT ----------------
    def insert_one(self, collection, data):
        con = self._connect()
        cur = con.cursor()
        data.setdefault("upload_time", datetime.utcnow().isoformat())
        data.setdefault("views", json.dumps([]))
        data.setdefault("likes", json.dumps([]))

        keys = ", ".join(data.keys())
        qmarks = ", ".join(["?"]*len(data))
        values = tuple(data.values())

        cur.execute(f"INSERT INTO {collection} ({keys}) VALUES ({qmarks})", values)
        con.commit()
        last_id = cur.lastrowid
        con.close()
        return last_id

    # ---------------- FIND ONE ----------------
    def find_one(self, collection, query):
        con = self._connect()
        cur = con.cursor()
        sql = f"SELECT * FROM {collection} WHERE "
        conditions = []
        values = []
        for k,v in query.items():
            conditions.append(f"{k}=?")
            values.append(v)
        sql += " AND ".join(conditions) + " LIMIT 1"
        cur.execute(sql, values)
        row = cur.fetchone()
        con.close()
        if not row:
            return None
        return self._row_to_dict(row, collection)

    # ---------------- FIND MANY ----------------
    def find(self, collection, query=None):
        con = self._connect()
        cur = con.cursor()
        sql = f"SELECT * FROM {collection}"
        values = []
        if query:
            conditions = []
            for k,v in query.items():
                conditions.append(f"{k}=?")
                values.append(v)
            sql += " WHERE " + " AND ".join(conditions)
        cur.execute(sql, values)
        rows = cur.fetchall()
        con.close()
        return [self._row_to_dict(r, collection) for r in rows]

    # ---------------- UPDATE ONE ----------------
    def update_one(self, collection, query, update):
        con = self._connect()
        cur = con.cursor()
        set_clause = ", ".join([f"{k}=?" for k in update.keys()])
        where_clause = " AND ".join([f"{k}=?" for k in query.keys()])
        values = list(update.values()) + list(query.values())
        sql = f"UPDATE {collection} SET {set_clause} WHERE {where_clause} LIMIT 1"
        cur.execute(sql, values)
        con.commit()
        con.close()

    # ---------------- DELETE ONE ----------------
    def delete_one(self, collection, query):
        con = self._connect()
        cur = con.cursor()
        where_clause = " AND ".join([f"{k}=?" for k in query.keys()])
        sql = f"DELETE FROM {collection} WHERE {where_clause} LIMIT 1"
        cur.execute(sql, list(query.values()))
        con.commit()
        con.close()

    # ---------------- INTERNAL ----------------
    def _row_to_dict(self, row, collection):
        if collection == "videos":
            keys = ["_id","file_name","uploader","title","description","tags","views","likes","upload_time"]
            d = dict(zip(keys,row))
            # convert JSON fields
            d["views"] = json.loads(d["views"])
            d["likes"] = json.loads(d["likes"])
            return d
        return dict(row)
