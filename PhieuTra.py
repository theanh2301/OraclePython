import sys
import cx_Oracle
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, \
    QLabel, QMessageBox, QFormLayout, QDialog, QTextEdit, QDateEdit
from PyQt6.QtCore import QDate


class AddEditPhieuTraDialog(QDialog):
    def __init__(self, parent=None, phieutra=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm/Sửa Phiếu Trả")
        self.setMinimumSize(500, 400)
        self.layout = QFormLayout()

        self.input_maphieutra = QLineEdit()
        self.input_mapt = QLineEdit()

        # Sử dụng QDateEdit cho NgayTra
        self.input_ngaytra = QDateEdit()
        self.input_ngaytra.setCalendarPopup(True)
        self.input_ngaytra.setDate(QDate.currentDate())

        # Sử dụng QTextEdit cho Ghi chú vì có thể dài
        self.input_ghichu = QTextEdit()
        self.input_ghichu.setMaximumHeight(100)

        self.input_phat = QLineEdit()

        self.layout.addRow("Mã phiếu trả:", self.input_maphieutra)
        self.layout.addRow("Mã phiếu thuê:", self.input_mapt)
        self.layout.addRow("Ngày trả:", self.input_ngaytra)
        self.layout.addRow("Ghi chú:", self.input_ghichu)
        self.layout.addRow("Phạt:", self.input_phat)

        self.btn_save = QPushButton("Lưu")
        self.btn_save.clicked.connect(self.save_phieutra)
        self.layout.addWidget(self.btn_save)

        self.setLayout(self.layout)

        if phieutra:
            self.input_maphieutra.setText(str(phieutra["MaPhieuTra"]))
            self.input_maphieutra.setReadOnly(True)  # Không cho phép sửa mã phiếu trả khi edit
            self.input_mapt.setText(phieutra["MaPT"] or "")

            # Xử lý ngày trả
            if phieutra["NgayTra"]:
                # Giả sử ngày từ database là datetime object hoặc string
                if isinstance(phieutra["NgayTra"], str):
                    # Nếu là string, parse thành QDate
                    date_parts = phieutra["NgayTra"].split('-')
                    if len(date_parts) == 3:
                        self.input_ngaytra.setDate(QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])))
                else:
                    # Nếu là datetime object
                    self.input_ngaytra.setDate(QDate(phieutra["NgayTra"]))

            self.input_ghichu.setPlainText(phieutra["GhiChu"] or "")
            self.input_phat.setText(str(phieutra["Phat"]) if phieutra["Phat"] else "")

    def save_phieutra(self):
        maphieutra = self.input_maphieutra.text().strip()
        mapt = self.input_mapt.text().strip()
        ngaytra = self.input_ngaytra.date().toPython()
        ghichu = self.input_ghichu.toPlainText().strip()
        phat = self.input_phat.text().strip()

        # Kiểm tra các trường bắt buộc
        if not maphieutra or not mapt:
            QMessageBox.warning(self, "Lỗi", "Mã phiếu trả và Mã phiếu thuê là bắt buộc!")
            return

        # Kiểm tra phí phạt nếu có nhập
        phat_decimal = None
        if phat:
            try:
                phat_decimal = float(phat)
                if phat_decimal < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Phí phạt phải là số không âm!")
                return

        self.phieutra_data = {
            "MaPhieuTra": maphieutra,
            "MaPT": mapt,
            "NgayTra": ngaytra,
            "GhiChu": ghichu if ghichu else None,
            "Phat": phat_decimal
        }
        self.accept()


class PhieuTraManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Quản lý Phiếu Trả")
        self.setGeometry(100, 100, 1200, 700)

        # Layout chính
        main_layout = QVBoxLayout()

        # Layout thanh tìm kiếm (trên cùng)
        from PyQt6.QtWidgets import QHBoxLayout
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập mã phiếu trả/mã phiếu thuê để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_phieutra)  # Tìm kiếm khi nhấn Enter

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_phieutra)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(search_layout)

        # Bảng dữ liệu (giữa)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Mã phiếu trả", "Mã phiếu thuê", "Ngày trả", "Ghi chú", "Phạt"])

        # Cho phép các cột co dãn
        from PyQt6.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Mã phiếu trả
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Mã phiếu thuê
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Ngày trả
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Ghi chú - tự động dãn
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Phạt

        # Đặt chiều rộng tối thiểu cho các cột
        self.table.setColumnWidth(0, 120)  # Mã phiếu trả
        self.table.setColumnWidth(1, 120)  # Mã phiếu thuê
        self.table.setColumnWidth(2, 120)  # Ngày trả
        self.table.setColumnWidth(3, 300)  # Ghi chú
        self.table.setColumnWidth(4, 100)  # Phạt

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        main_layout.addWidget(self.table)

        # Layout các nút chức năng (dưới cùng, ngang hàng)
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Thêm Phiếu Trả")
        self.btn_add.clicked.connect(self.add_phieutra)
        self.btn_add.setMinimumHeight(35)

        self.btn_edit = QPushButton("Sửa Phiếu Trả")
        self.btn_edit.clicked.connect(self.edit_phieutra)
        self.btn_edit.setMinimumHeight(35)

        self.btn_delete = QPushButton("Xóa Phiếu Trả")
        self.btn_delete.clicked.connect(self.delete_phieutra)
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
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")  # Thay đổi service_name nếu cần
            connection = cx_Oracle.connect(user="sys", password="theanh2301", dsn=dsn, mode=cx_Oracle.SYSDBA)
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
            cursor.execute("SELECT MaPhieuTra, MaPT, NgayTra, GhiChu, Phat FROM PhieuTra")
            data = cursor.fetchall()

            # Lấy tên cột
            column_names = [desc[0] for desc in cursor.description]

            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 2 and value:  # Cột NgayTra
                        # Format ngày tháng
                        display_value = value.strftime("%d/%m/%Y") if hasattr(value, 'strftime') else str(value)
                    else:
                        display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def search_phieutra(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_data()
            return

        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            query = """SELECT MaPhieuTra, MaPT, NgayTra, GhiChu, Phat 
                      FROM PhieuTra 
                      WHERE UPPER(MaPhieuTra) LIKE UPPER(:keyword) 
                         OR UPPER(MaPT) LIKE UPPER(:keyword)"""
            cursor.execute(query, keyword=f"%{keyword}%")
            data = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 2 and value:  # Cột NgayTra
                        # Format ngày tháng
                        display_value = value.strftime("%d/%m/%Y") if hasattr(value, 'strftime') else str(value)
                    else:
                        display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tìm kiếm: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def add_phieutra(self):
        dialog = AddEditPhieuTraDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            phieutra = dialog.phieutra_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = """INSERT INTO PhieuTra (MaPhieuTra, MaPT, NgayTra, GhiChu, Phat) 
                          VALUES (:maphieutra, :mapt, :ngaytra, :ghichu, :phat)"""
                cursor.execute(query,
                               maphieutra=phieutra["MaPhieuTra"],
                               mapt=phieutra["MaPT"],
                               ngaytra=phieutra["NgayTra"],
                               ghichu=phieutra["GhiChu"],
                               phat=phieutra["Phat"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Thêm phiếu trả thành công!")
                self.load_data()
            except cx_Oracle.IntegrityError as e:
                if "PhieuTra_PhieuThue_FK" in str(e):
                    QMessageBox.warning(self, "Lỗi", "Mã phiếu thuê không tồn tại!")
                else:
                    QMessageBox.warning(self, "Lỗi", "Mã phiếu trả đã tồn tại!")
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi thêm phiếu trả: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def edit_phieutra(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phiếu trả để sửa.")
            return

        phieutra = {}
        col_keys = ["MaPhieuTra", "MaPT", "NgayTra", "GhiChu", "Phat"]
        for idx, key in enumerate(col_keys):
            item = self.table.item(selected_row, idx)
            if key == "NgayTra":
                # Xử lý ngày tháng
                date_str = item.text() if item.text() else ""
                phieutra[key] = date_str
            elif key == "Phat":
                try:
                    phieutra[key] = float(item.text()) if item.text() else None
                except ValueError:
                    phieutra[key] = None
            else:
                phieutra[key] = item.text() if item.text() else None

        dialog = AddEditPhieuTraDialog(self, phieutra)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            phieutra = dialog.phieutra_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = """UPDATE PhieuTra SET MaPT=:mapt, NgayTra=:ngaytra, GhiChu=:ghichu, Phat=:phat 
                          WHERE MaPhieuTra=:maphieutra"""
                cursor.execute(query,
                               mapt=phieutra["MaPT"],
                               ngaytra=phieutra["NgayTra"],
                               ghichu=phieutra["GhiChu"],
                               phat=phieutra["Phat"],
                               maphieutra=phieutra["MaPhieuTra"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Cập nhật phiếu trả thành công!")
                self.load_data()
            except cx_Oracle.IntegrityError as e:
                if "PhieuTra_PhieuThue_FK" in str(e):
                    QMessageBox.warning(self, "Lỗi", "Mã phiếu thuê không tồn tại!")
                else:
                    QMessageBox.warning(self, "Lỗi", "Lỗi ràng buộc dữ liệu!")
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật phiếu trả: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def delete_phieutra(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn phiếu trả để xóa.")
            return

        maphieutra = self.table.item(selected_row, 0).text()
        mapt = self.table.item(selected_row, 1).text()
        reply = QMessageBox.question(self, "Xác nhận",
                                     f"Bạn có chắc chắn muốn xóa phiếu trả '{maphieutra}' (Phiếu thuê: {mapt})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = "DELETE FROM PhieuTra WHERE MaPhieuTra = :maphieutra"
                cursor.execute(query, maphieutra=maphieutra)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Xóa phiếu trả thành công!")
                self.load_data()
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi xóa phiếu trả: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhieuTraManager()
    window.show()
    sys.exit(app.exec())