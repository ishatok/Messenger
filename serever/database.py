import sqlite3
import os
from datetime import datetime


class Database:
    def __init__(self, db_path="messenger.db"):
        self.db_path = db_path
        self.init_db()
        self.create_test_data()

    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Инициализация базы данных при запуске"""
        print("🔄 Инициализация базы данных...")

        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица сообщений (упрощенная без статусов прочтения)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (receiver_id) REFERENCES users (id)
            )
        ''')

        # Включаем внешние ключи
        cursor.execute('PRAGMA foreign_keys = ON')

        conn.commit()

        # Проверяем создание таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table['name'] for table in tables]
        print(f"✅ Созданы таблицы: {table_names}")

        conn.close()
        return table_names

    def create_test_data(self):
        """Создание тестовых данных"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Проверяем, есть ли уже пользователи
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']

            if user_count == 0:
                print("📝 Создание тестовых пользователей...")

                # Создаем тестовых пользователей
                test_users = [
                    ("alice", "password123"),
                    ("bob", "password123"),
                    ("charlie", "password123")
                ]

                for username, password in test_users:
                    try:
                        cursor.execute(
                            "INSERT INTO users (username, password) VALUES (?, ?)",
                            (username, password)
                        )
                        print(f"   ✅ Создан пользователь: {username}")
                    except sqlite3.IntegrityError:
                        print(f"   ⚠️ Пользователь {username} уже существует")

                conn.commit()

                # Создаем тестовые сообщения
                print("💬 Создание тестовых сообщений...")

                # Получаем ID пользователей
                cursor.execute("SELECT id, username FROM users")
                users = {row['username']: row['id'] for row in cursor.fetchall()}

                test_messages = [
                    (users["alice"], users["bob"], "Привет, Боб! Как дела?"),
                    (users["bob"], users["alice"], "Привет, Алиса! Все отлично!"),
                    (users["alice"], users["bob"], "Рада слышать! Что нового?"),
                    (users["charlie"], users["alice"], "Всем привет! Я Чарли"),
                ]

                for sender_id, receiver_id, content in test_messages:
                    cursor.execute(
                        "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                        (sender_id, receiver_id, content)
                    )

                conn.commit()
                print("🎉 Тестовые данные созданы успешно!")
            else:
                print(f"📊 В базе уже есть {user_count} пользователей")

            conn.close()

        except Exception as e:
            print(f"❌ Ошибка создания тестовых данных: {e}")

    def create_user(self, username, password):
        """Создать нового пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            print(f"✅ Пользователь создан: {username} (ID: {user_id})")
            return True
        except sqlite3.IntegrityError:
            print(f"❌ Пользователь уже существует: {username}")
            return False
        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return False

    def get_user(self, username):
        """Получить пользователя по имени"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_user_by_id(self, user_id):
        """Получить пользователя по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_all_users(self):
        """Получить всех пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, created_at FROM users ORDER BY username"
        )
        users = cursor.fetchall()
        conn.close()
        return [dict(user) for user in users]

    def save_message(self, sender_id, receiver_id, content):
        """Сохранить сообщение в БД"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                (sender_id, receiver_id, content)
            )
            conn.commit()
            message_id = cursor.lastrowid
            conn.close()
            print(f"✅ Сообщение сохранено: {sender_id} -> {receiver_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщения: {e}")
            return False

    def get_messages(self, user1_id, user2_id, limit=100):
        """Получить историю сообщений между двумя пользователями"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.sender_id, m.receiver_id, m.content, m.timestamp,
                   u1.username as sender_name, u2.username as receiver_name
            FROM messages m
            JOIN users u1 ON m.sender_id = u1.id
            JOIN users u2 ON m.receiver_id = u2.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) 
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
        ''', (user1_id, user2_id, user2_id, user1_id))

        messages = cursor.fetchall()
        conn.close()
        return [dict(msg) for msg in messages]

    def get_stats(self):
        """Получить статистику базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM messages")
        message_count = cursor.fetchone()['count']

        conn.close()

        return {
            "users": user_count,
            "messages": message_count
        }