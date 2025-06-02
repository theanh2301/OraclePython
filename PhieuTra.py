import sys
import cx_Oracle
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLineEdit, QLabel, QMessageBox, QFormLayout, QDialog, QTextEdit, QDateEdit,
                             QHBoxLayout, QHeaderView, QTabWidget, QGroupBox)
from PyQt6.QtCore import QDate, Qt


class CreatePhieuTraDialog(QDialog):
    def __init__(self, parent=None, phieu_thue_data=None):
        super().__init__(parent)
        self.setWindowTitle("Tạo Phiếu Trả")
        self.setMinimumSize(500, 400)
        self.phieu_thue_data = phieu_thue_data

        layout = QFormLayout()

        # Thông tin phiếu thuê (chỉ đọc)
        info_group = QGroupBox("Thông tin phiếu mượn")
        info_layout = QFormLayout()

        self.lbl_mapt = QLabel(phieu_thue_data["MaPT"])
        self.lbl_makh = QLabel(phieu_thue_data["MaKH"])
        self.lbl_ngaythue = QLabel(phieu_thue_data["NgayThue"])
        self.lbl_hantra = QLabel(phieu_thue_data["HanTra"])

        info_layout.addRow("Mã phiếu thuê:", self.lbl_mapt)
        info_layout.addRow("Mã khách hàng:", self.lbl_makh)
        info_layout.addRow("Ngày thuê:", self.lbl_ngaythue)
        info_layout.addRow("Hạn trả:", self.lbl_hantra)
        info_group.setLayout(info_layout)

        # Thông tin phiếu trả
        tra_group = QGroupBox("Thông tin phiếu trả")
        tra_layout = QFormLayout()

        self.input_maphieutra = QLineEdit()
        self.input_maphieutra.setPlaceholderText("Nhập mã phiếu trả...")

        self.input_ngaytra = QDateEdit()
        self.input_ngaytra.setCalendarPopup(True)
        self.input_ngaytra.setDate(QDate.currentDate())

        self.input_ghichu = QTextEdit()
        self.input_ghichu.setMaximumHeight(80)
        self.input_ghichu.setPlaceholderText("Ghi chú về tình trạng truyện...")

        self.input_phat = QLineEdit()
        self.input_phat.setPlaceholderText("0")

        tra_layout.addRow("Mã phiếu trả:", self.input_maphieutra)
        tra_layout.addRow("Ngày trả:", self.input_ngaytra)
        tra_layout.addRow("Ghi chú:", self.input_ghichu)
        tra_layout.addRow("Phí phạt:", self.input_phat)
        tra_group.setLayout(tra_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("Tạo Phiếu Trả")
        self.btn_cancel = QPushButton("Hủy")

        self.btn_save.clicked.connect(self.save_phieu_tra)
        self.btn_cancel.clicked.connect(self.reject)

        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(info_group)
        main_layout.addWidget(tra_group)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def save_phieu_tra(self):
        maphieutra = self.input_maphieutra.text().strip()
        qdate = self.input_ngaytra.date()
        # Chuyển QDate thành datetime.date
        from datetime import date
        ngaytra = date(qdate.year(), qdate.month(), qdate.day())
        ghichu = self.input_ghichu.toPlainText().strip()
        phat = self.input_phat.text().strip()

        if not maphieutra:
            QMessageBox.warning(self, "Lỗi", "Mã phiếu trả là bắt buộc!")
            return

        # Kiểm tra phí phạt
        phat_decimal = 0
        if phat:
            try:
                phat_decimal = float(phat)
                if phat_decimal < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Phí phạt phải là số không âm!")
                return

        self.phieu_tra_data = {
            "MaPhieuTra": maphieutra,
            "MaPT": self.phieu_thue_data["MaPT"],
            "NgayTra": ngaytra,
            "GhiChu": ghichu if ghichu else None,
            "Phat": phat_decimal
        }
        self.accept()


class ChiTietPhieuThueDialog(QDialog):
    def __init__(self, parent=None, phieu_thue=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chi tiết phiếu mượn - {phieu_thue['MaPT']}")
        self.setMinimumSize(800, 600)
        # Cho phép resize
        self.resize(1000, 700)
        self.phieu_thue = phieu_thue
        self.parent_window = parent

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Thông tin phiếu thuê
        info_group = QGroupBox("Thông tin phiếu mượn")
        info_layout = QFormLayout()
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        info_layout.addRow("Mã phiếu thuê:", QLabel(phieu_thue["MaPT"]))
        info_layout.addRow("Mã khách hàng:", QLabel(phieu_thue["MaKH"]))
        info_layout.addRow("Ngày thuê:", QLabel(phieu_thue["NgayThue"]))
        info_layout.addRow("Hạn trả:", QLabel(phieu_thue["HanTra"]))

        status_text = "Đã trả" if phieu_thue["DaTra"] == 1 else "Chưa trả"
        status_label = QLabel(status_text)
        if phieu_thue["DaTra"] == 1:
            status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        else:
            status_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        info_layout.addRow("Trạng thái:", status_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Danh sách truyện đã mượn
        truyen_group = QGroupBox("Danh sách truyện đã mượn")
        truyen_layout = QVBoxLayout()

        self.table_chitiet = QTableWidget()
        self.table_chitiet.setColumnCount(4)
        self.table_chitiet.setHorizontalHeaderLabels(["Mã truyện", "Tên truyện", "Số lượng", "Giá thuê"])

        # Cấu hình co dãn cho bảng chi tiết
        header = self.table_chitiet.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mã truyện
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Tên truyện - co dãn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Số lượng
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Giá thuê

        # Style cho bảng
        self.table_chitiet.setAlternatingRowColors(True)
        self.table_chitiet.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        truyen_layout.addWidget(self.table_chitiet)
        truyen_group.setLayout(truyen_layout)
        layout.addWidget(truyen_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_tra_truyen = QPushButton("Trả Truyện")
        self.btn_tra_truyen.clicked.connect(self.tra_truyen)
        self.btn_tra_truyen.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        # Disable nút trả nếu đã trả rồi
        if phieu_thue["DaTra"] == 1:
            self.btn_tra_truyen.setEnabled(False)
            self.btn_tra_truyen.setText("Đã Trả")

        self.btn_close = QPushButton("Đóng")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        button_layout.addStretch()  # Đẩy buttons về bên phải
        button_layout.addWidget(self.btn_tra_truyen)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load chi tiết
        self.load_chitiet()

    def load_chitiet(self):
        try:
            conn = self.parent_window.connect_db()
            if conn is None:
                return

            cursor = conn.cursor()
            query = """
                SELECT ct.MaTruyen, t.TenTruyen, ct.SoLuong, ct.GiaThue
                FROM ChiTietPhieuThue ct
                JOIN Truyen t ON ct.MaTruyen = t.MaTruyen
                WHERE ct.MaPT = :mapt
            """
            cursor.execute(query, mapt=self.phieu_thue["MaPT"])
            data = cursor.fetchall()
            conn.close()

            self.table_chitiet.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 3:  # Giá thuê
                        display_value = f"{value:,.0f} VNĐ" if value else "0 VNĐ"
                    else:
                        display_value = str(value) if value is not None else ""
                    self.table_chitiet.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải chi tiết: {str(e)}")

    def tra_truyen(self):
        dialog = CreatePhieuTraDialog(self, self.phieu_thue)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            phieu_tra_data = dialog.phieu_tra_data

            try:
                conn = self.parent_window.connect_db()
                if conn is None:
                    return

                cursor = conn.cursor()

                # Tạo phiếu trả
                insert_query = """
                    INSERT INTO PhieuTra (MaPhieuTra, MaPT, NgayTra, GhiChu, Phat) 
                    VALUES (:maphieutra, :mapt, :ngaytra, :ghichu, :phat)
                """
                cursor.execute(insert_query,
                               maphieutra=phieu_tra_data["MaPhieuTra"],
                               mapt=phieu_tra_data["MaPT"],
                               ngaytra=phieu_tra_data["NgayTra"],
                               ghichu=phieu_tra_data["GhiChu"],
                               phat=phieu_tra_data["Phat"])

                # Cập nhật trạng thái đã trả
                update_query = "UPDATE PhieuThue SET DaTra = 1 WHERE MaPT = :mapt"
                cursor.execute(update_query, mapt=phieu_tra_data["MaPT"])

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Thành công", "Tạo phiếu trả thành công!")

                # Cập nhật giao diện
                self.btn_tra_truyen.setEnabled(False)
                self.btn_tra_truyen.setText("Đã Trả")
                self.phieu_thue["DaTra"] = 1

                # Refresh parent window
                if hasattr(self.parent_window, 'load_data'):
                    self.parent_window.load_data()

            except cx_Oracle.IntegrityError as e:
                QMessageBox.warning(self, "Lỗi", "Mã phiếu trả đã tồn tại!")
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi tạo phiếu trả: {str(e)}")


class PhieuMuonManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Quản lý Phiếu Mượn Truyện")
        self.setGeometry(100, 100, 1200, 700)
        # Cho phép resize cửa sổ
        self.setMinimumSize(800, 500)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Thanh tìm kiếm
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập mã phiếu thuê/mã khách hàng để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_phieu)
        self.search_input.setMinimumHeight(30)

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_phieu)
        self.btn_search.setMinimumHeight(30)
        self.btn_search.setFixedWidth(100)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_refresh.setMinimumHeight(30)
        self.btn_refresh.setFixedWidth(100)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(search_layout)

        # Bảng dữ liệu
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Thêm 1 cột cho nút
        self.table.setHorizontalHeaderLabels(
            ["Mã phiếu thuê", "Mã khách hàng", "Ngày thuê", "Hạn trả", "Trạng thái", "Thao tác"])

        header = self.table.horizontalHeader()
        # Cấu hình co dãn theo màn hình
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mã phiếu thuê
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Mã khách hàng - co dãn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Ngày thuê
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Hạn trả
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Trạng thái
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Thao tác - cố định

        # Đặt chiều rộng tối thiểu
        self.table.setColumnWidth(5, 120)  # Cột thao tác

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Bỏ double click vì đã có nút riêng
        # self.table.doubleClicked.connect(self.view_chitiet)

        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def connect_db(self):
        try:
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")
            connection = cx_Oracle.connect(user="truyenadmin", password="theanh2301", dsn=dsn)
            return connection
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến Oracle Database: {str(e)}")
            return None

    def load_data(self):
        try:
            conn = self.connect_db()
            if conn is None:
                return

            cursor = conn.cursor()
            cursor.execute("SELECT MaPT, MaKH, NgayThue, HanTra, DaTra FROM PhieuThue ORDER BY NgayThue DESC")
            data = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    if col_idx in [2, 3] and value:  # Cột NgayThue, HanTra
                        display_value = value.strftime("%d/%m/%Y") if hasattr(value, 'strftime') else str(value)
                    elif col_idx == 4:  # Cột DaTra
                        display_value = "Đã trả" if value == 1 else "Chưa trả"
                    else:
                        display_value = str(value) if value is not None else ""

                    item = QTableWidgetItem(display_value)

                    # Tô màu trạng thái
                    if col_idx == 4:
                        if value == 1:
                            item.setBackground(Qt.GlobalColor.lightGray)
                        else:
                            # Kiểm tra quá hạn
                            han_tra = row_data[3]
                            if han_tra and hasattr(han_tra, 'date'):
                                from datetime import date
                                current_date = date.today()
                                if han_tra.date() < current_date:
                                    item.setBackground(Qt.GlobalColor.red)
                                    item.setForeground(Qt.GlobalColor.white)

                    self.table.setItem(row_idx, col_idx, item)

                # Thêm nút "Xem Chi Tiết" vào cột cuối
                btn_view = QPushButton("Xem Chi Tiết")
                btn_view.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #0D47A1;
                    }
                """)
                btn_view.clicked.connect(lambda checked, row=row_idx: self.view_chitiet_by_row(row))
                self.table.setCellWidget(row_idx, 5, btn_view)

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def search_phieu(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_data()
            return

        try:
            conn = self.connect_db()
            if conn is None:
                return

            cursor = conn.cursor()
            query = """SELECT MaPT, MaKH, NgayThue, HanTra, DaTra 
                      FROM PhieuThue 
                      WHERE UPPER(MaPT) LIKE UPPER(:keyword) 
                         OR UPPER(MaKH) LIKE UPPER(:keyword)
                      ORDER BY NgayThue DESC"""
            cursor.execute(query, keyword=f"%{keyword}%")
            data = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    if col_idx in [2, 3] and value:
                        display_value = value.strftime("%d/%m/%Y") if hasattr(value, 'strftime') else str(value)
                    elif col_idx == 4:
                        display_value = "Đã trả" if value == 1 else "Chưa trả"
                    else:
                        display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

                # Thêm nút "Xem Chi Tiết" vào cột cuối
                btn_view = QPushButton("Xem Chi Tiết")
                btn_view.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #0D47A1;
                    }
                """)
                btn_view.clicked.connect(lambda checked, row=row_idx: self.view_chitiet_by_row(row))
                self.table.setCellWidget(row_idx, 5, btn_view)

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tìm kiếm: {str(e)}")

    def view_chitiet_by_row(self, row):
        """Xem chi tiết phiếu mượn từ hàng được chỉ định"""
        # Lấy thông tin phiếu thuê từ hàng
        phieu_thue = {}
        col_keys = ["MaPT", "MaKH", "NgayThue", "HanTra", "DaTra"]
        for idx, key in enumerate(col_keys):
            item = self.table.item(row, idx)
            if item is None:
                continue
            if key in ["NgayThue", "HanTra"]:
                phieu_thue[key] = item.text() if item.text() else ""
            elif key == "DaTra":
                phieu_thue[key] = 1 if item.text() == "Đã trả" else 0
            else:
                phieu_thue[key] = item.text() if item.text() else ""

        dialog = ChiTietPhieuThueDialog(self, phieu_thue)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhieuMuonManager()
    window.show()
    sys.exit(app.exec())