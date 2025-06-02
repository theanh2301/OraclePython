import sys
import cx_Oracle
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, \
    QLabel, QMessageBox, QFormLayout, QDialog, QTextEdit, QSpinBox


class AddEditTruyenDialog(QDialog):
    def __init__(self, parent=None, truyen=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm/Sửa Truyện")
        self.setMinimumSize(500, 400)
        self.layout = QFormLayout()

        self.input_matruyen = QLineEdit()
        self.input_tentruyen = QLineEdit()
        self.input_theloai = QLineEdit()
        self.input_tacgia = QLineEdit()

        # Sử dụng QSpinBox cho SoLuong để đảm bảo nhập số nguyên
        self.input_soluong = QSpinBox()
        self.input_soluong.setMinimum(0)
        self.input_soluong.setMaximum(999999)

        self.input_giaban = QLineEdit()
        self.input_giathue = QLineEdit()

        # Sử dụng QTextEdit cho Mô tả vì có thể dài
        self.input_mota = QTextEdit()
        self.input_mota.setMaximumHeight(100)

        self.layout.addRow("Mã truyện:", self.input_matruyen)
        self.layout.addRow("Tên truyện:", self.input_tentruyen)
        self.layout.addRow("Thể loại:", self.input_theloai)
        self.layout.addRow("Tác giả:", self.input_tacgia)
        self.layout.addRow("Số lượng:", self.input_soluong)
        self.layout.addRow("Giá bán:", self.input_giaban)
        self.layout.addRow("Giá thuê:", self.input_giathue)
        self.layout.addRow("Mô tả:", self.input_mota)

        self.btn_save = QPushButton("Lưu")
        self.btn_save.clicked.connect(self.save_truyen)
        self.layout.addWidget(self.btn_save)

        self.setLayout(self.layout)

        if truyen:
            self.input_matruyen.setText(str(truyen["MaTruyen"]))
            self.input_matruyen.setReadOnly(True)
            self.input_tentruyen.setText(truyen["TenTruyen"] or "")
            self.input_theloai.setText(truyen["TheLoai"] or "")
            self.input_tacgia.setText(truyen["TacGia"] or "")
            self.input_soluong.setValue(truyen["SoLuong"] if truyen["SoLuong"] else 0)
            self.input_giaban.setText(str(truyen["GiaBan"]) if truyen["GiaBan"] else "")
            self.input_giathue.setText(str(truyen["GiaThue"]) if truyen["GiaThue"] else "")
            self.input_mota.setPlainText(truyen["Mota"] or "")

    def save_truyen(self):
        matruyen = self.input_matruyen.text().strip()
        tentruyen = self.input_tentruyen.text().strip()
        theloai = self.input_theloai.text().strip()
        tacgia = self.input_tacgia.text().strip()
        soluong = self.input_soluong.value()
        giaban = self.input_giaban.text().strip()
        giathue = self.input_giathue.text().strip()
        mota = self.input_mota.toPlainText().strip()

        # Kiểm tra các trường bắt buộc
        if not matruyen or not tentruyen:
            QMessageBox.warning(self, "Lỗi", "Mã truyện và Tên truyện là bắt buộc!")
            return

        # Kiểm tra giá bán nếu có nhập
        giaban_decimal = None
        if giaban:
            try:
                giaban_decimal = float(giaban)
                if giaban_decimal < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Giá bán phải là số dương!")
                return

        # Kiểm tra giá thuê nếu có nhập
        giathue_decimal = None
        if giathue:
            try:
                giathue_decimal = float(giathue)
                if giathue_decimal < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Giá thuê phải là số dương!")
                return

        self.truyen_data = {
            "MaTruyen": matruyen,
            "TenTruyen": tentruyen,
            "TheLoai": theloai if theloai else None,
            "TacGia": tacgia if tacgia else None,
            "SoLuong": soluong,
            "GiaBan": giaban_decimal,
            "GiaThue": giathue_decimal,
            "Mota": mota if mota else None
        }
        self.accept()


class TruyenManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Quản lý truyện")
        self.setGeometry(100, 100, 1200, 700)

        # Layout chính
        main_layout = QVBoxLayout()

        # Layout thanh tìm kiếm (trên cùng)
        from PyQt6.QtWidgets import QHBoxLayout
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập mã/tên/thể loại/tác giả để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_truyen)  # Tìm kiếm khi nhấn Enter

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_truyen)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(search_layout)

        # Bảng dữ liệu (giữa)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Mã truyện", "Tên truyện", "Thể loại", "Tác giả", "Số lượng", "Giá bán", "Giá thuê", "Mô tả"])

        # Cho phép các cột co dãn
        from PyQt6.QtWidgets import QHeaderView
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Mã truyện
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Tên truyện - tự động dãn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Thể loại
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Tác giả
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Số lượng
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Giá bán
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Giá thuê
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # Mô tả - tự động dãn

        # Đặt chiều rộng tối thiểu cho các cột
        self.table.setColumnWidth(0, 80)  # Mã truyện
        self.table.setColumnWidth(1, 200)  # Tên truyện
        self.table.setColumnWidth(2, 120)  # Thể loại
        self.table.setColumnWidth(3, 150)  # Tác giả
        self.table.setColumnWidth(4, 80)  # Số lượng
        self.table.setColumnWidth(5, 100)  # Giá bán
        self.table.setColumnWidth(6, 100)  # Giá thuê
        self.table.setColumnWidth(7, 200)  # Mô tả

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        main_layout.addWidget(self.table)

        # Layout các nút chức năng (dưới cùng, ngang hàng)
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Thêm Truyện")
        self.btn_add.clicked.connect(self.add_truyen)
        self.btn_add.setMinimumHeight(35)

        self.btn_edit = QPushButton("Sửa Truyện")
        self.btn_edit.clicked.connect(self.edit_truyen)
        self.btn_edit.setMinimumHeight(35)

        self.btn_delete = QPushButton("Xóa Truyện")
        self.btn_delete.clicked.connect(self.delete_truyen)
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
            cursor.execute("SELECT MaTruyen, TenTruyen, TheLoai, TacGia, SoLuong, GiaBan, GiaThue, Mota FROM Truyen")
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

    def search_truyen(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_data()
            return

        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            query = """SELECT MaTruyen, TenTruyen, TheLoai, TacGia, SoLuong, GiaBan, GiaThue, Mota 
                      FROM Truyen 
                      WHERE UPPER(MaTruyen) LIKE UPPER(:keyword) 
                         OR UPPER(TenTruyen) LIKE UPPER(:keyword) 
                         OR UPPER(TheLoai) LIKE UPPER(:keyword) 
                         OR UPPER(TacGia) LIKE UPPER(:keyword)"""
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

    def add_truyen(self):
        dialog = AddEditTruyenDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            truyen = dialog.truyen_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = """INSERT INTO Truyen (MaTruyen, TenTruyen, TheLoai, TacGia, SoLuong, GiaBan, GiaThue, Mota) 
                          VALUES (:matruyen, :tentruyen, :theloai, :tacgia, :soluong, :giaban, :giathue, :mota)"""
                cursor.execute(query,
                               matruyen=truyen["MaTruyen"],
                               tentruyen=truyen["TenTruyen"],
                               theloai=truyen["TheLoai"],
                               tacgia=truyen["TacGia"],
                               soluong=truyen["SoLuong"],
                               giaban=truyen["GiaBan"],
                               giathue=truyen["GiaThue"],
                               mota=truyen["Mota"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Thêm truyện thành công!")
                self.load_data()
            except cx_Oracle.IntegrityError:
                QMessageBox.warning(self, "Lỗi", "Mã truyện đã tồn tại!")
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi thêm truyện: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def edit_truyen(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn truyện để sửa.")
            return

        truyen = {}
        col_keys = ["MaTruyen", "TenTruyen", "TheLoai", "TacGia", "SoLuong", "GiaBan", "GiaThue", "Mota"]
        for idx, key in enumerate(col_keys):
            item = self.table.item(selected_row, idx)
            if key == "SoLuong":
                try:
                    truyen[key] = int(item.text()) if item.text() else 0
                except ValueError:
                    truyen[key] = 0
            elif key in ["GiaBan", "GiaThue"]:
                try:
                    truyen[key] = float(item.text()) if item.text() else None
                except ValueError:
                    truyen[key] = None
            else:
                truyen[key] = item.text() if item.text() else None

        dialog = AddEditTruyenDialog(self, truyen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            truyen = dialog.truyen_data
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = """UPDATE Truyen SET TenTruyen=:tentruyen, TheLoai=:theloai, TacGia=:tacgia, 
                          SoLuong=:soluong, GiaBan=:giaban, GiaThue=:giathue, Mota=:mota 
                          WHERE MaTruyen=:matruyen"""
                cursor.execute(query,
                               tentruyen=truyen["TenTruyen"],
                               theloai=truyen["TheLoai"],
                               tacgia=truyen["TacGia"],
                               soluong=truyen["SoLuong"],
                               giaban=truyen["GiaBan"],
                               giathue=truyen["GiaThue"],
                               mota=truyen["Mota"],
                               matruyen=truyen["MaTruyen"])
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Cập nhật truyện thành công!")
                self.load_data()
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật truyện: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def delete_truyen(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn truyện để xóa.")
            return

        matruyen = self.table.item(selected_row, 0).text()
        tentruyen = self.table.item(selected_row, 1).text()
        reply = QMessageBox.question(self, "Xác nhận",
                                     f"Bạn có chắc chắn muốn xóa truyện '{tentruyen}' (Mã: {matruyen})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = self.connect_db()
                if conn is None:
                    return
                cursor = conn.cursor()
                query = "DELETE FROM Truyen WHERE MaTruyen = :matruyen"
                cursor.execute(query, matruyen=matruyen)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Thành công", "Xóa truyện thành công!")
                self.load_data()
            except cx_Oracle.DatabaseError as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi xóa truyện: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TruyenManager()
    window.show()
    sys.exit(app.exec())