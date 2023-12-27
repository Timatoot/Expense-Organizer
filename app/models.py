from flask_login import UserMixin
from .database import get_db_connection

class User(UserMixin):
    def __init__(self, id=None, username=None):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (int(user_id),)).fetchone()
        conn.close()
        if user:
            return User(id=user['id'], username=user['username'])
        return None
