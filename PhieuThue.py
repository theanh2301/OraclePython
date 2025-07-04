import sys
import cx_Oracle

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
                             QLabel, QMessageBox, QFormLayout, QDialog, QSpinBox,
                             QHeaderView, QSplitter, QFrame, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont


class RentalDetailDialog(QDialog):
    """Form hiển thị chi tiết phiếu thuê"""

    def __init__(self, parent=None, rental_data=None):
        super().__init__(parent)
        self.setWindowTitle("Chi tiết phiếu thuê")
        self.setMinimumSize(800, 600)
        self.rental_data = rental_data
        self.initUI()
        self.center_on_screen()

    def center_on_screen(self):
        """Hiển thị dialog ở giữa màn hình"""
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.frameGeometry()
        center_point = screen.center()
        dialog_geometry.moveCenter(center_point)
        self.move(dialog_geometry.topLeft())

    def initUI(self):
        layout = QVBoxLayout()

        # Thông tin phiếu thuê
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_layout = QFormLayout()

        font = QFont()
        font.setBold(True)
        font.setPointSize(12)

        title = QLabel("PHIẾU CHO THUÊ TRUYỆN")
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        info_layout.addRow("Mã phiếu thuê:", QLabel(self.rental_data.get('MaPT', '')))
        info_layout.addRow("Mã khách hàng:", QLabel(self.rental_data.get('MaKH', '')))
        info_layout.addRow("Ngày thuê:", QLabel(self.rental_data.get('NgayThue', '')))
        info_layout.addRow("Hạn trả:", QLabel(self.rental_data.get('HanTra', '')))
        info_layout.addRow("Tổng tiền thuê:", QLabel(f"{self.rental_data.get('TongTien', 0):,.0f} VNĐ"))

        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)

        # Bảng chi tiết
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(["Mã truyện", "Tên truyện", "Số lượng", "Giá thuê"])

        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        self.load_rental_details()
        layout.addWidget(self.detail_table)

        # Nút đóng
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def connect_db(self):
        try:
            # Kết nối đến Oracle Database
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")  # Thay đổi service_name nếu cần
            connection = cx_Oracle.connect(user="truyenadmin", password="theanh2301", dsn=dsn)
            return connection
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến Oracle Database: {str(e)}")
            return None

    def load_rental_details(self):
        conn = None
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            query = """
                SELECT ct.MaTruyen, t.TenTruyen, ct.SoLuong, ct.GiaThue
                FROM ChiTietPhieuThue ct
                JOIN Truyen t ON ct.MaTruyen = t.MaTruyen
                WHERE ct.MaPT = :mapt
            """
            cursor.execute(query, mapt=self.rental_data['MaPT'])
            details = cursor.fetchall()

            self.detail_table.setRowCount(len(details))
            for row_idx, row_data in enumerate(details):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 3:  # Giá thuê
                        display_value = f"{value:,.0f}"
                    else:
                        display_value = str(value) if value is not None else ""
                    self.detail_table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải chi tiết phiếu thuê: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")
        finally:
            if conn:
                conn.close()


class RentalForm(QWidget):
    """Form thuê truyện chính"""

    def __init__(self):
        super().__init__()
        self.cart_items = []  # Danh sách truyện trong giỏ hàng
        self.initUI()
        self.load_books()
        self.center_on_screen()

    def center_on_screen(self):
        """Hiển thị form ở giữa màn hình"""
        screen = QApplication.primaryScreen().geometry()
        form_geometry = self.frameGeometry()
        center_point = screen.center()
        form_geometry.moveCenter(center_point)
        self.move(form_geometry.topLeft())

    def initUI(self):
        self.setWindowTitle("Form Thuê Truyện")
        self.setGeometry(100, 100, 1400, 800)

        main_layout = QHBoxLayout()

        # Splitter để có thể điều chỉnh kích thước
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Bảng bên trái - Danh sách truyện
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Tìm kiếm
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm truyện...")
        self.search_input.returnPressed.connect(self.search_books)

        btn_search = QPushButton("Tìm kiếm")
        btn_search.clicked.connect(self.search_books)

        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(self.load_books)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_refresh)
        left_layout.addLayout(search_layout)

        # Bảng truyện
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(6)
        self.books_table.setHorizontalHeaderLabels(["Mã", "Tên sách", "Tác giả", "Thể loại", "Giá thuê", "Giá bán"])

        # Thiết lập header
        header = self.books_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)

        self.books_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.books_table)

        # Số lượng và nút thêm
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Số lượng:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setMaximumWidth(100)
        quantity_layout.addWidget(self.quantity_spin)

        btn_add_to_cart = QPushButton("+ Thêm vào giỏ hàng")
        btn_add_to_cart.clicked.connect(self.add_to_cart)
        btn_add_to_cart.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        quantity_layout.addWidget(btn_add_to_cart)

        quantity_layout.addStretch()
        left_layout.addLayout(quantity_layout)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # Phần bên phải
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # Thông tin khách hàng và ngày thuê
        customer_frame = QFrame()
        customer_frame.setFrameStyle(QFrame.Shape.Box)
        customer_layout = QFormLayout()

        self.customer_id = QLineEdit()
        self.customer_id.setMaxLength(10)
        self.customer_name = QLineEdit()
        self.customer_phone = QLineEdit()
        self.customer_diachi = QLineEdit()

        # Ngày thuê và hạn trả
        self.rental_date = QDateEdit()
        self.rental_date.setDate(QDate.currentDate())
        self.rental_date.setCalendarPopup(True)

        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate().addDays(7))  # Mặc định thuê 7 ngày
        self.return_date.setCalendarPopup(True)

        customer_layout.addRow("Mã khách hàng:", self.customer_id)
        customer_layout.addRow("Tên khách hàng:", self.customer_name)
        customer_layout.addRow("Số điện thoại:", self.customer_phone)
        customer_layout.addRow("Địa chỉ:", self.customer_diachi)
        customer_layout.addRow("Ngày thuê:", self.rental_date)
        customer_layout.addRow("Hạn trả:", self.return_date)

        customer_frame.setLayout(customer_layout)
        right_layout.addWidget(customer_frame)

        # Bảng giỏ hàng
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["STT", "Tên sách", "Tác giả", "Số lượng", "Giá thuê", "Xóa"])

        cart_header = self.cart_table.horizontalHeader()
        cart_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        cart_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cart_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        cart_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        cart_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        cart_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)

        self.cart_table.setColumnWidth(0, 50)
        self.cart_table.setColumnWidth(5, 60)
        right_layout.addWidget(self.cart_table)

        # Tổng tiền và nút tạo phiếu
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Tổng tiền thuê:"))
        self.total_label = QLabel("0 đ")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: red;")
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()

        btn_create_rental = QPushButton("Tạo phiếu thuê")
        btn_create_rental.clicked.connect(self.create_rental)
        btn_create_rental.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold; padding: 10px 20px; font-size: 14px;")
        total_layout.addWidget(btn_create_rental)
        right_layout.addLayout(total_layout)

        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        # Thiết lập tỷ lệ cho splitter
        splitter.setSizes([800, 600])
        main_layout.addWidget(splitter)

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

    def load_books(self):
        """Tải danh sách truyện"""
        conn = None
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            query = """
                SELECT MaTruyen, TenTruyen, TacGia, TheLoai, GiaThue, GiaBan, SoLuong
                FROM Truyen 
                WHERE SoLuong > 0 AND GiaThue IS NOT NULL
                ORDER BY TenTruyen
            """
            cursor.execute(query)
            books = cursor.fetchall()

            self.books_table.setRowCount(len(books))
            for row_idx, row_data in enumerate(books):
                for col_idx, value in enumerate(row_data[:6]):
                    if col_idx in [4, 5] and value is not None:  # Giá thuê và giá bán
                        display_value = f"{value:,.0f}"
                    else:
                        display_value = str(value) if value is not None else ""
                    self.books_table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách truyện: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")
        finally:
            if conn:
                conn.close()

    def search_books(self):
        """Tìm kiếm truyện"""
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_books()
            return

        conn = None
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            query = """
                SELECT MaTruyen, TenTruyen, TacGia, TheLoai, GiaThue, GiaBan, SoLuong
                FROM Truyen 
                WHERE SoLuong > 0 AND GiaThue IS NOT NULL AND (
                    UPPER(TenTruyen) LIKE UPPER(:keyword) OR
                    UPPER(TacGia) LIKE UPPER(:keyword) OR
                    UPPER(TheLoai) LIKE UPPER(:keyword)
                )
                ORDER BY TenTruyen
            """
            cursor.execute(query, keyword=f"%{keyword}%")
            books = cursor.fetchall()

            self.books_table.setRowCount(len(books))
            for row_idx, row_data in enumerate(books):
                for col_idx, value in enumerate(row_data[:6]):
                    if col_idx in [4, 5] and value is not None:
                        display_value = f"{value:,.0f}"
                    else:
                        display_value = str(value) if value is not None else ""
                    self.books_table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tìm kiếm: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")
        finally:
            if conn:
                conn.close()

    def add_to_cart(self):
        """Thêm truyện vào giỏ hàng"""
        selected_row = self.books_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn truyện để thêm vào giỏ hàng!")
            return

        # Lấy thông tin truyện
        ma_truyen = self.books_table.item(selected_row, 0).text()
        ten_truyen = self.books_table.item(selected_row, 1).text()
        tac_gia = self.books_table.item(selected_row, 2).text()
        gia_thue_text = self.books_table.item(selected_row, 4).text()

        if not gia_thue_text or gia_thue_text == "None":
            QMessageBox.warning(self, "Lỗi", "Truyện này chưa có giá thuê!")
            return

        gia_thue = float(gia_thue_text.replace(",", ""))
        so_luong = self.quantity_spin.value()

        # Kiểm tra xem truyện đã có trong giỏ hàng chưa
        for i, item in enumerate(self.cart_items):
            if item['MaTruyen'] == ma_truyen:
                # Cập nhật số lượng
                self.cart_items[i]['SoLuong'] += so_luong
                break
        else:
            # Thêm mới vào giỏ hàng
            self.cart_items.append({
                'MaTruyen': ma_truyen,
                'TenTruyen': ten_truyen,
                'TacGia': tac_gia,
                'SoLuong': so_luong,
                'GiaThue': gia_thue
            })

        self.update_cart_display()
        self.calculate_total()

    def update_cart_display(self):
        """Cập nhật hiển thị giỏ hàng"""
        self.cart_table.setRowCount(len(self.cart_items))
        for row_idx, item in enumerate(self.cart_items):
            self.cart_table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            self.cart_table.setItem(row_idx, 1, QTableWidgetItem(item['TenTruyen']))
            self.cart_table.setItem(row_idx, 2, QTableWidgetItem(str(item['TacGia'])))
            self.cart_table.setItem(row_idx, 3, QTableWidgetItem(str(item['SoLuong'])))
            self.cart_table.setItem(row_idx, 4, QTableWidgetItem(f"{item['GiaThue']:,.0f}"))

            # Tạo nút xóa
            btn_delete = QPushButton("Xóa")
            btn_delete.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            btn_delete.clicked.connect(lambda checked, row=row_idx: self.remove_from_cart(row))
            self.cart_table.setCellWidget(row_idx, 5, btn_delete)

    def remove_from_cart(self, row_index):
        """Xóa item khỏi giỏ hàng"""
        if 0 <= row_index < len(self.cart_items):
            item_name = self.cart_items[row_index]['TenTruyen']
            reply = QMessageBox.question(self, "Xác nhận",
                                         f"Bạn có chắc chắn muốn xóa '{item_name}' khỏi giỏ hàng?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                del self.cart_items[row_index]
                self.update_cart_display()
                self.calculate_total()

    def calculate_total(self):
        """Tính tổng tiền thuê"""
        total = sum(item['SoLuong'] * item['GiaThue'] for item in self.cart_items)
        self.total_label.setText(f"{total:,.0f} đ")
        return total

    def create_rental(self):
        """Tạo phiếu thuê"""
        if not self.cart_items:
            QMessageBox.warning(self, "Lỗi", "Giỏ hàng trống! Vui lòng thêm truyện vào giỏ hàng.")
            return

        customer_id = self.customer_id.text().strip()
        if not customer_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mã khách hàng!")
            return

        # Kiểm tra độ dài mã khách hàng
        if len(customer_id) > 10:
            QMessageBox.warning(self, "Lỗi", "Mã khách hàng không được quá 10 ký tự!")
            return

        # Kiểm tra ngày hợp lệ
        rental_date = self.rental_date.date().toPyDate()
        return_date = self.return_date.date().toPyDate()

        if return_date <= rental_date:
            QMessageBox.warning(self, "Lỗi", "Hạn trả phải sau ngày thuê!")
            return

        conn = None
        try:
            conn = self.connect_db()
            if conn is None:
                return

            cursor = conn.cursor()

            # Kiểm tra xem khách hàng có tồn tại không
            cursor.execute("SELECT COUNT(*) FROM KhachHang WHERE MaKH = :makh", {'makh': customer_id})
            customer_exists = cursor.fetchone()[0] > 0

            if not customer_exists:
                # Nếu khách hàng chưa tồn tại, thêm mới
                customer_name = self.customer_name.text().strip() or "Khách hàng mới"
                customer_phone = self.customer_phone.text().strip() or ""
                customer_diachi = self.customer_diachi.text().strip() or ""

                try:
                    cursor.execute("""
                        INSERT INTO KhachHang (MaKH, TenKH, SoDienThoai, DiaChi)
                        VALUES (:makh, :tenkh, :sdt, :diachi)
                    """, {
                        'makh': customer_id,
                        'tenkh': customer_name,
                        'sdt': customer_phone,
                        'diachi': customer_diachi
                    })
                except cx_Oracle.DatabaseError as e:
                    if "unique constraint" in str(e).lower():
                        pass  # Khách hàng đã tồn tại, bỏ qua lỗi
                    else:
                        raise e

            # Tạo mã phiếu thu
            cursor.execute("SELECT NVL(MAX(SUBSTR(MaPT, 3)), 0) + 1 FROM PhieuThue WHERE MaPT LIKE 'PT%'")
            next_id = cursor.fetchone()[0]
            ma_pt = f"PT{next_id:02d}"

            # Thêm phiếu thuê
            cursor.execute("""
                INSERT INTO PhieuThue (MaPT, MaKH, NgayThue, HanTra, DaTra)
                VALUES (:mapt, :makh, :ngaythue, :hantra, :datra)
            """, {
                'mapt': ma_pt,
                'makh': customer_id,
                'ngaythue': rental_date,
                'hantra': return_date,
                'datra': 0
            })

            # Thêm chi tiết phiếu thuê và cập nhật số lượng
            for item in self.cart_items:
                # Kiểm tra số lượng tồn kho trước khi thuê
                cursor.execute("SELECT SoLuong FROM Truyen WHERE MaTruyen = :matruyen",
                               {'matruyen': item['MaTruyen']})
                result = cursor.fetchone()

                if result is None:
                    conn.rollback()
                    QMessageBox.critical(self, "Lỗi", f"Không tìm thấy truyện có mã: {item['MaTruyen']}")
                    return

                current_stock = result[0]
                if current_stock < item['SoLuong']:
                    conn.rollback()
                    QMessageBox.critical(self, "Lỗi",
                                         f"Không đủ số lượng cho truyện '{item['TenTruyen']}'!\n"
                                         f"Số lượng hiện có: {current_stock}, Yêu cầu: {item['SoLuong']}")
                    return

                # Thêm chi tiết phiếu thuê
                cursor.execute("""
                    INSERT INTO ChiTietPhieuThue (MaPT, MaTruyen, SoLuong, GiaThue)
                    VALUES (:mapt, :matruyen, :soluong, :giathue)
                """, {
                    'mapt': ma_pt,
                    'matruyen': item['MaTruyen'],
                    'soluong': item['SoLuong'],
                    'giathue': item['GiaThue']
                })

                # Cập nhật số lượng truyện (giảm số lượng có sẵn)
                cursor.execute("""
                    UPDATE Truyen SET SoLuong = SoLuong - :soluong 
                    WHERE MaTruyen = :matruyen
                """, {
                    'soluong': item['SoLuong'],
                    'matruyen': item['MaTruyen']
                })

            conn.commit()

            tong_tien = self.calculate_total()
            QMessageBox.information(self, "Thành công", f"Tạo phiếu thuê thành công!\nMã phiếu thuê: {ma_pt}")

            # Hiển thị form phiếu thuê
            rental_data = {
                'MaPT': ma_pt,
                'MaKH': customer_id,
                'NgayThue': rental_date.strftime('%d/%m/%Y'),
                'HanTra': return_date.strftime('%d/%m/%Y'),
                'TongTien': tong_tien
            }

            rental_dialog = RentalDetailDialog(self, rental_data)
            rental_dialog.exec()

            # Reset form
            self.cart_items.clear()
            self.update_cart_display()
            self.calculate_total()
            self.load_books()

            # Clear customer info
            self.customer_id.clear()
            self.customer_name.clear()
            self.customer_phone.clear()
            self.customer_diachi.clear()
            self.rental_date.setDate(QDate.currentDate())
            self.return_date.setDate(QDate.currentDate().addDays(7))

        except cx_Oracle.DatabaseError as e:
            if conn:
                conn.rollback()
            error_msg = f"Lỗi Database: {str(e)}"
            print(error_msg)  # In ra console để debug
            QMessageBox.critical(self, "Lỗi Database", error_msg)
        except Exception as e:
            if conn:
                conn.rollback()
            error_msg = f"Lỗi không xác định: {str(e)}"
            print(error_msg)  # In ra console để debug
            QMessageBox.critical(self, "Lỗi", error_msg)
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RentalForm()
    window.show()
    sys.exit(app.exec())