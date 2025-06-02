import sys
import cx_Oracle
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, \
    QLabel, QMessageBox, QFormLayout, QDialog


class AddEditClientDialog(QDialog):
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm/Sửa Khách Hàng")
        self.layout = QFormLayout()

        self.input_makh = QLineEdit()
        self.input_tenkh = QLineEdit()
        self.input_sdtkh = QLineEdit()
        self.input_diachi = QLineEdit()
        self.input_gmailkh = QLineEdit()

        self.layout.addRow("Mã khách hàng:", self.input_makh)
        self.layout.addRow("Tên khách hàng:", self.input_tenkh)
        self.layout.addRow("Số điện thoại:", self.input_sdtkh)
        self.layout.addRow("Địa chỉ:", self.input_diachi)
        self.layout.addRow("Gmail:", self.input_gmailkh)

        self.btn_save = QPushButton("Lưu")
        self.btn_save.clicked.connect(self.save_client)
        self.layout.addWidget(self.btn_save)

        self.setLayout(self.layout)

        if client:
            self.input_makh.setText(str(client["MaKH"]))
            self.input_makh.setReadOnly(True)  # Không cho phép sửa mã khách hàng khi edit
            self.input_tenkh.setText(client["TenKH"] or "")
            self.input_sdtkh.setText(str(client["SdtKH"]) if client["SdtKH"] else "")
            self.input_diachi.setText(client["DiaChi"] or "")
            self.input_gmailkh.setText(client["GmailKH"] or "")

    def save_client(self):
        makh = self.input_makh.text().strip()
        tenkh = self.input_tenkh.text().strip()
        sdtkh = self.input_sdtkh.text().strip()
        diachi = self.input_diachi.text().strip()
        gmailkh = self.input_gmailkh.text().strip()

        # Kiểm tra các trường bắt buộc
        if not makh or not tenkh:
            QMessageBox.warning(self, "Lỗi", "Mã khách hàng và Tên khách hàng là bắt buộc!")
            return

        # Kiểm tra số điện thoại nếu có nhập
        if sdtkh:
            try:
                sdtkh_int = int(sdtkh)
                if sdtkh_int < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Số điện thoại phải là số nguyên dương!")
                return
        else:
            sdtkh_int = None

        # Kiểm tra email format cơ bản nếu có nhập
        if gmailkh and "@" not in gmailkh:
            QMessageBox.warning(self, "Lỗi", "Định dạng email không hợp lệ!")
            return

        self.client_data = {
            "MaKH": makh,
            "TenKH": tenkh,
            "SdtKH": sdtkh_int,
            "DiaChi": diachi if diachi else None,
            "GmailKH": gmailkh if gmailkh else None
        }
        self.accept()


class ClientManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Quản lý khách hàng")
        self.setGeometry(100, 100, 900, 600)

        # Layout chính
        main_layout = QVBoxLayout()

        # Layout thanh tìm kiếm (trên cùng)
        from PyQt6.QtWidgets import QHBoxLayout
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập mã/tên/địa chỉ để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_client)  # Tìm kiếm khi nhấn Enter

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_client)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(search_layout)

        # Bảng dữ liệu (giữa)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Mã KH", "Tên KH", "SĐT", "Địa chỉ", "Gmail"])

        # Cho phép các cột co dãn
        from PyQt6.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Mã KH
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Tên KH - tự động dãn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # SĐT
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Địa chỉ - tự động dãn
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Gmail - tự động dãn

        # Đặt chiều rộng tối thiểu cho các cột
        self.table.setColumnWidth(0, 80)  # Mã KH
        self.table.setColumnWidth(1, 150)  # Tên KH
        self.table.setColumnWidth(2, 100)  # SĐT
        self.table.setColumnWidth(3, 200)  # Địa chỉ
        self.table.setColumnWidth(4, 200)  # Gmail

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        main_layout.addWidget(self.table)

        # Layout các nút chức năng (dưới cùng, ngang hàng)
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Thêm Khách Hàng")
        self.btn_add.clicked.connect(self.add_client)
        self.btn_add.setMinimumHeight(35)

        self.btn_edit = QPushButton("Sửa Khách Hàng")
        self.btn_edit.clicked.connect(self.edit_client)
        self.btn_edit.setMinimumHeight(35)

        self.btn_delete = QPushButton("Xóa Khách Hàng")
        self.btn_delete.clicked.connect(self.delete_client)
        self.btn_delete.setMinimumHeight(35)

        # Thêm các nút vào layout ngang
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_delete)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_db(self):
        try:
            # Kết nối đến Oracle Database
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")  # Thay đổi service_name nếu cần
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
            cursor.execute("SELECT MaKH, TenKH, SdtKH, DiaChi, GmailKH FROM KhachHang")
            data = cursor.fetchall()

            # Lấy tên cột
            column_names = [desc[0] for desc in cursor.description]

            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def search_client(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_data()
            return

        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            query = ("SELECT MaKH, TenKH, SdtKH, DiaChi, GmailKH "
                     "FROM KhachHang "
                     "WHERE UPPER(MaKH) LIKE UPPER(:keyword) "
                     "OR UPPER(TenKH) LIKE UPPER(:keyword) "
                     "OR UPPER(DiaChi) LIKE UPPER(:keyword)")
            cursor.execute(query, keyword=f"%{keyword}%")
            data = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tìm kiếm: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def add_client(self):
        dialog = AddEditClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client = dialog.client_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = "INSERT INTO KhachHang (MaKH, TenKH, SdtKH, DiaChi, GmailKH) VALUES (:makh, :tenkh, :sdtkh, :diachi, :gmailkh)"
                cursor.execute(query, makh=client["MaKH"], tenkh=client["TenKH"], sdtkh=client["SdtKH"],
                               diachi=client["DiaChi"], gmailkh=client["GmailKH"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Thêm khách hàng thành công!")
                self.load_data()
            except cx_Oracle.IntegrityError:
                QMessageBox.warning(self, "Lỗi", "Mã khách hàng đã tồn tại!")
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi thêm khách hàng: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def edit_client(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn khách hàng để sửa.")
            return

        client = {}
        col_keys = ["MaKH", "TenKH", "SdtKH", "DiaChi", "GmailKH"]
        for idx, key in enumerate(col_keys):
            item = self.table.item(selected_row, idx)
            if key == "SdtKH":
                try:
                    client[key] = int(item.text()) if item.text() else None
                except ValueError:
                    client[key] = None
            else:
                client[key] = item.text() if item.text() else None

        dialog = AddEditClientDialog(self, client)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client = dialog.client_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = "UPDATE KhachHang SET TenKH=:tenkh, SdtKH=:sdtkh, DiaChi=:diachi, GmailKH=:gmailkh WHERE MaKH=:makh"
                cursor.execute(query, tenkh=client["TenKH"], sdtkh=client["SdtKH"], diachi=client["DiaChi"],
                               gmailkh=client["GmailKH"], makh=client["MaKH"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Cập nhật khách hàng thành công!")
                self.load_data()
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật khách hàng: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def delete_client(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn khách hàng để xóa.")
            return

        makh = self.table.item(selected_row, 0).text()
        reply = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc chắn muốn xóa khách hàng {makh}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = "DELETE FROM KhachHang WHERE MaKH = :makh"
                cursor.execute(query, makh=makh)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Xóa khách hàng thành công!")
                self.load_data()
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi xóa khách hàng: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ClientManager()
    window.show()
    sys.exit(app.exec())