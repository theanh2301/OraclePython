from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import sys
import cx_Oracle


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập hệ thống")
        self.setGeometry(500, 300, 450, 350)
        self.setFixedSize(450, 350)


        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("ĐĂNG NHẬP HỆ THỐNG")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        # Username input
        username_layout = QVBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFont(QFont("Arial", 14))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.username_input.setFont(QFont("Arial", 14))
        self.username_input.setFixedHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        # Password input
        password_layout = QVBoxLayout()
        password_label = QLabel("Mật khẩu:")
        password_label.setFont(QFont("Arial", 14))

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 14))
        self.password_input.setFixedHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        # Buttons
        button_layout = QHBoxLayout()

        login_button = QPushButton("Đăng nhập")
        login_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        login_button.setFixedHeight(45)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        login_button.clicked.connect(self.login)

        cancel_button = QPushButton("Thoát")
        cancel_button.setFont(QFont("Arial", 14))
        cancel_button.setFixedHeight(45)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        cancel_button.clicked.connect(self.close)

        button_layout.addWidget(login_button)
        button_layout.addWidget(cancel_button)

        # Add to main layout
        main_layout.addWidget(title)
        main_layout.addLayout(username_layout)
        main_layout.addLayout(password_layout)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Default for testing
        self.username_input.setText("ad")
        self.password_input.setText("123")

    def connect_db(self):
        try:
            # Kết nối đến Oracle Database
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")  # Thay đổi service_name nếu cần
            connection = cx_Oracle.connect(user="truyenadmin", password="theanh2301", dsn=dsn)
            return connection
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến Oracle Database: {str(e)}")
            return None

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        connection = self.connect_db()
        if not connection:
            return


        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM TaiKhoan WHERE TenDangNhap=:1 AND MatKhau=:2", (username, password))
            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result:
                QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
                from MainWindow import MainWindow
                self.main_window = MainWindow()
                self.main_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "Lỗi đăng nhập", "Tên đăng nhập hoặc mật khẩu không đúng!")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi kiểm tra tài khoản:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
