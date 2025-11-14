import sys
import requests
import time
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('MainWindow.ui', self)

        self.stackedWidget.setCurrentIndex(0)
        self.setup_global_notification()
        self.setup_connections()

    def setup_global_notification(self):
        self.global_show_animation = QPropertyAnimation(self.global_notification, b"geometry")
        self.global_show_animation.setDuration(400)
        self.global_show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.global_hide_animation = QPropertyAnimation(self.global_notification, b"geometry")
        self.global_hide_animation.setDuration(350)
        self.global_hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        self.global_hide_timer = QTimer()
        self.global_hide_timer.setSingleShot(True)
        self.global_hide_timer.timeout.connect(self.hide_global_notification)

    def setup_connections(self):
        self.global_notify_close.clicked.connect(self.hide_global_notification)

        if hasattr(self, 'login_button'):
            self.login_button.clicked.connect(self.on_login_clicked)

        if hasattr(self, 'register_confirm_button'):
            self.register_confirm_button.clicked.connect(self.on_register_clicked)

        if hasattr(self, 'send_button'):
            self.send_button.clicked.connect(self.on_send_message_clicked)

    def get_notification_geometry(self, visible=True):
        window_width = self.width()
        notification_width = 300
        notification_height = 60
        margin = 20

        x = (window_width - notification_width) // 2
        y = margin

        if not visible:
            y = -notification_height - margin

        return QRect(x, y, notification_width, notification_height)

    def show_global_notification(self, message, notification_type="info"):
        self.global_show_animation.stop()
        self.global_hide_animation.stop()
        self.global_hide_timer.stop()

        self.global_notify_label.setText(message)
        self.force_global_notification_style(notification_type)

        end_geo = self.get_notification_geometry(visible=True)
        start_geo = self.get_notification_geometry(visible=False)

        self.global_notification.setGeometry(start_geo)
        self.global_notification.show()
        self.global_notification.raise_()

        self.global_show_animation.setStartValue(start_geo)
        self.global_show_animation.setEndValue(end_geo)
        self.global_show_animation.start()

        self.global_hide_timer.start(3000)

    def force_global_notification_style(self, notification_type):
        self.global_notification.setStyleSheet("")
        QApplication.processEvents()

        self.global_notification.setProperty("notificationType", notification_type)
        self.global_notification.style().unpolish(self.global_notification)
        self.global_notification.style().polish(self.global_notification)
        self.global_notification.update()

    def hide_global_notification(self):
        self.global_hide_timer.stop()
        self.global_show_animation.stop()
        self.global_hide_animation.stop()

        current_geo = self.global_notification.geometry()
        end_geo = self.get_notification_geometry(visible=False)

        self.global_hide_animation.setStartValue(current_geo)
        self.global_hide_animation.setEndValue(end_geo)
        self.global_hide_animation.start()

        self.global_hide_animation.finished.connect(self._on_global_hide_finished)

    def _on_global_hide_finished(self):
        self.global_notification.hide()
        self.global_hide_animation.finished.disconnect(self._on_global_hide_finished)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.global_notification.isVisible():
            new_geo = self.get_notification_geometry(visible=True)
            self.global_notification.setGeometry(new_geo)

    def show_error(self, message):
        self.show_global_notification(f"❌ {message}", "error")

    def show_success(self, message):
        self.show_global_notification(f"✅ {message}", "success")

    def show_warning(self, message):
        self.show_global_notification(f"⚠️ {message}", "warning")

    def show_info(self, message):
        self.show_global_notification(f"ℹ️ {message}", "info")

class MessagePoller(QThread):
    new_messages = pyqtSignal(list)

    def __init__(self, server_url, user_id, current_chat_user_id):
        super().__init__()
        self.server_url = server_url
        self.user_id = user_id
        self.current_chat_user_id = current_chat_user_id
        self.running = True
        self.last_message_ids = set()

    def run(self):
        while self.running:
            try:
                if self.current_chat_user_id:
                    response = requests.get(
                        f"{self.server_url}/messages/{self.user_id}/{self.current_chat_user_id}",
                        timeout=5
                    )

                    if response.status_code == 200:
                        messages = response.json()
                        current_ids = {msg['id'] for msg in messages}

                        new_messages = [
                            msg for msg in messages
                            if msg['id'] not in self.last_message_ids
                               and msg['sender_id'] != self.user_id
                        ]

                        if new_messages:
                            self.new_messages.emit(new_messages)

                        self.last_message_ids = current_ids

                time.sleep(2)

            except Exception:
                time.sleep(5)

    def update_chat_user(self, chat_user_id):
        self.current_chat_user_id = chat_user_id
        self.last_message_ids = set()

    def stop_polling(self):
        self.running = False
        self.wait(2000)

class MessengerClient(MyWidget):
    def __init__(self):
        super().__init__()

        self.server_url = "http://94.228.121.212:8000"
        self.current_user = None
        self.current_chat_user = None
        self.message_poller = None

        self.stackedWidget.setCurrentIndex(0)
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.chat_display.clear()

        self.setup_connections()

    def setup_connections(self):
        self.login_button.clicked.connect(self.on_login_clicked)
        self.register_button.clicked.connect(self.show_register_page)
        self.register_confirm_button.clicked.connect(self.on_register_clicked)
        self.register_back_button.clicked.connect(self.show_login_page)
        self.send_button.clicked.connect(self.on_send_message_clicked)
        self.contacts_list.itemClicked.connect(self.on_contact_selected)
        self.message_input.returnPressed.connect(self.on_send_message_clicked)

        self.reg_username_input.textChanged.connect(self.validate_registration)
        self.reg_password_input.textChanged.connect(self.validate_registration)
        self.reg_confirm_input.textChanged.connect(self.validate_registration)

    def show_register_page(self):
        self.stackedWidget.setCurrentIndex(1)

    def show_login_page(self):
        self.stackedWidget.setCurrentIndex(0)

    def validate_registration(self):
        username = self.reg_username_input.text().strip()
        password = self.reg_password_input.text()
        confirm = self.reg_confirm_input.text()

        valid = (len(username) >= 3 and
                 len(password) >= 4 and
                 password == confirm)
        self.register_confirm_button.setEnabled(valid)

    def on_login_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            return

        self.login_button.setEnabled(False)

        try:
            response = requests.post(
                f"{self.server_url}/login",
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.current_user = data
                self.show_success(f"Добро пожаловать, {username}!")
                self.load_contacts()
                self.stackedWidget.setCurrentIndex(2)
                self.username_input.clear()
                self.password_input.clear()
            else:
                self.show_error("Неверный логин или пароль")

        except Exception:
            self.show_error("Ошибка подключения к серверу")
        finally:
            self.login_button.setEnabled(True)

    def on_register_clicked(self):
        username = self.reg_username_input.text().strip()
        password = self.reg_password_input.text()

        if not username or not password:
            return

        self.register_confirm_button.setEnabled(False)

        try:
            response = requests.post(
                f"{self.server_url}/register",
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                self.show_success("Регистрация успешна!")
                self.show_login_page()
                self.username_input.setText(username)
                self.reg_username_input.clear()
                self.reg_password_input.clear()
                self.reg_confirm_input.clear()
            else:
                self.show_error("Логин уже занят")

        except Exception:
            self.show_error("Ошибка регистрации")
        finally:
            self.validate_registration()

    def load_contacts(self):
        if not self.current_user:
            return

        try:
            response = requests.get(f"{self.server_url}/users", timeout=10)
            if response.status_code == 200:
                users = response.json()
                self.contacts_list.clear()

                for user in users:
                    if user["id"] != self.current_user["user_id"]:
                        self.contacts_list.addItem(f"{user['username']}")

        except Exception:
            self.show_error("Ошибка загрузки контактов")

    def on_contact_selected(self, item):
        if not self.current_user:
            return

        username = item.text()

        if self.current_chat_user and self.current_chat_user["username"] == username:
            return

        try:
            user_id = self.get_user_id_by_username(username)
            if not user_id:
                self.show_error("Ошибка получения ID пользователя")
                return

            self.current_chat_user = {"id": user_id, "username": username}
            self.chat_title.setText(f"Чат с {username}")
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.message_input.setFocus()

            if self.message_poller:
                self.message_poller.stop_polling()

            self.load_chat_history(user_id)
            self.start_message_polling(user_id)

        except Exception:
            self.show_error("Ошибка выбора контакта")

    def get_user_id_by_username(self, username):
        try:
            response = requests.get(f"{self.server_url}/users", timeout=10)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user["username"] == username:
                        return user["id"]
        except Exception:
            pass
        return None

    def load_chat_history(self, contact_id):
        if not self.current_user:
            return

        try:
            response = requests.get(
                f"{self.server_url}/messages/{self.current_user['user_id']}/{contact_id}",
                timeout=10
            )

            if response.status_code == 200:
                messages = response.json()
                self.chat_display.clear()

                for msg in messages:
                    is_own = msg["sender_id"] == self.current_user["user_id"]
                    self.display_message(msg, is_own)

                self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

        except Exception:
            self.show_error("Ошибка загрузки истории")

    def start_message_polling(self, contact_id):
        self.message_poller = MessagePoller(
            self.server_url,
            self.current_user["user_id"],
            contact_id
        )
        self.message_poller.new_messages.connect(self.handle_new_messages)
        self.message_poller.start()

    def handle_new_messages(self, messages):
        for msg in messages:
            is_own = msg["sender_id"] == self.current_user["user_id"]
            if not is_own:
                self.display_message(msg, is_own)

        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def display_message(self, message, is_own):
        content = message['content']
        if is_own:
            text = f"Вы: {content}\n"
        else:
            sender = message.get('sender_name', 'Собеседник')
            text = f"{sender}: {content}\n"

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.chat_display.setTextCursor(cursor)

    def on_send_message_clicked(self):
        if not self.current_user or not self.current_chat_user:
            self.show_error("Выберите контакт для отправки сообщения")
            return

        message_text = self.message_input.text().strip()
        if not message_text:
            return

        self.display_message({
            "content": message_text,
            "sender_name": self.current_user["username"]
        }, is_own=True)

        self.message_input.clear()

        try:
            response = requests.post(
                f"{self.server_url}/send_message",
                json={
                    "sender_id": self.current_user["user_id"],
                    "receiver_id": self.current_chat_user["id"],
                    "content": message_text
                },
                timeout=10
            )

            if response.status_code != 200:
                self.show_warning("Сообщение отправлено, но есть проблемы с сервером")

        except Exception:
            self.show_error("Ошибка отправки сообщения")

    def closeEvent(self, event):
        if self.message_poller:
            self.message_poller.stop_polling()
        event.accept()

def main():
    app = QApplication(sys.argv)
    client = MessengerClient()
    client.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()