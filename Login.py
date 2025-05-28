from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
import sys
import cx_Oracle


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập hệ thống")
        self.setGeometry(500, 300, 400, 300)
        self.setFixedSize(400, 300)

        # Set background color
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("ĐĂNG NHẬP HỆ THỐNG")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")

        # Username field
        username_layout = QVBoxLayout()
        username_label = QLabel("Tên đăng nhập:")
        username_label.setFont(QFont("Arial", 12))
        username_label.setStyleSheet("color: #34495e;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.username_input.setFont(QFont("Arial", 12))
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)

        # Password field
        password_layout = QVBoxLayout()
        password_label = QLabel("Mật khẩu:")
        password_label.setFont(QFont("Arial", 12))
        password_label.setStyleSheet("color: #34495e;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
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
        login_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
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
        cancel_button.setFont(QFont("Arial", 12))
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
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

        # Add all layouts to main layout
        main_layout.addWidget(title)
        main_layout.addLayout(username_layout)
        main_layout.addLayout(password_layout)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Set default values for testing
        self.username_input.setText("sys")
        self.password_input.setText("theanh2301")

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        # Kết nối Oracle Database
        try:
            # Thay đổi connection string theo cấu hình Oracle của bạn
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")  # Hoặc SID của bạn
            connection = cx_Oracle.connect(username, password, dsn)

            QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
            connection.close()

            # Mở main window
            from MainWindow import MainWindow
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()

        except cx_Oracle.Error as e:
            error_msg = str(e)
            if "ORA-01017" in error_msg:
                QMessageBox.critical(self, "Lỗi đăng nhập", "Tên đăng nhập hoặc mật khẩu không đúng!")
            elif "ORA-12541" in error_msg:
                QMessageBox.critical(self, "Lỗi kết nối",
                                     "Không thể kết nối đến database!\nVui lòng kiểm tra Oracle service.")
            else:
                QMessageBox.critical(self, "Lỗi", f"Lỗi kết nối database:\n{error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())