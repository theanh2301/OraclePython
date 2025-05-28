from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QStackedWidget, QListWidgetItem
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QSize
import sys

from KhachHang import ClientManager
from PhieuMua import SalesForm
from PhieuThue import RentalForm
from PhieuTra import PhieuTraManager
from ThongKeDoanhThu import RevenueStatistics
from ThongKeKhachHang import CustomerStatistics


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pytho nhóm 11")
        self.setGeometry(100, 100, 1300, 600)

        # Main Layout
        main_layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("""
            QListWidget {
                border-radius: 10px;
            }
            QListWidget::item {
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
                color: #333;
                background-color: white;
                margin: 5px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
        """)

        self.sidebar_items = {
            "Quản lý khách hàng": "KhachHang",
            "Quản lý phiếu mua": "PhieuMua",
            "Quản lý phiếu thuê": "PhieuThue",
            "Quản lý phiếu trả": "PhieuTra",
            "Thống kê doanh thu": "ThongKeDoanhThu",
            "Thống kê khách hàng": "ThongKeKhachHang",
        }

        for item in self.sidebar_items.keys():
            list_item = QListWidgetItem(item)
            list_item.setFont(QFont("Arial", 16))
            list_item.setSizeHint(QSize(200, 60))
            self.sidebar.addItem(list_item)

        self.sidebar.itemClicked.connect(self.switch_content)

        # Top Bar
        top_bar = QHBoxLayout()
        logo = QLabel("Python")
        logo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        exit_button = QPushButton("Thoát chương trình")

        # Styling buttons
        button_style = """
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
                border-radius: 5px;
                background-color: #d9534f;
                color: white;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """
        exit_button.setStyleSheet(button_style)
        exit_button.clicked.connect(self.close)

        top_bar.addWidget(logo)
        top_bar.addStretch()
        top_bar.addWidget(exit_button)

        # Content Area - QStackedWidget để chuyển đổi giao diện
        self.content_stack = QStackedWidget()
        self.default_content = QLabel("Chọn một mục bên trái để xem nội dung.", alignment=Qt.AlignmentFlag.AlignCenter)
        self.default_content.setFont(QFont("Arial", 14))

        self.content_stack.addWidget(self.default_content)

        # Layout Wrapping
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.sidebar)

        right_layout = QVBoxLayout()
        right_layout.addLayout(top_bar)
        right_layout.addWidget(self.content_stack)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        # Lưu các giao diện con
        self.pages = {}

    def switch_content(self, item):
        page_name = self.sidebar_items.get(item.text(), None)

        if page_name:
            if page_name not in self.pages:
                if page_name == "KhachHang":
                    self.pages[page_name] = ClientManager()
                elif page_name == "PhieuMua":
                    self.pages[page_name] = SalesForm()
                elif page_name == "PhieuThue":
                    self.pages[page_name] = RentalForm()
                elif page_name == "PhieuTra":
                    self.pages[page_name] = PhieuTraManager()
                elif page_name == "ThongKeDoanhThu":
                    self.pages[page_name] = RevenueStatistics()
                elif page_name == "ThongKeKhachHang":
                    self.pages[page_name] = CustomerStatistics()

                self.content_stack.addWidget(self.pages[page_name])

            self.content_stack.setCurrentWidget(self.pages[page_name])
        else:
            self.content_stack.setCurrentWidget(self.default_content)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
