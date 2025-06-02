import sys
import cx_Oracle
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QMessageBox, QHBoxLayout, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt

class CustomerStatistics(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Thống Kê Khách Hàng")
        self.setGeometry(100, 100, 1300, 750)

        # Layout chính
        main_layout = QVBoxLayout()

        # Layout thanh tìm kiếm và bộ lọc (trên cùng)
        filter_layout = QHBoxLayout()

        # Tìm kiếm theo tên khách hàng
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên khách hàng để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_data)

        # Lọc theo phân loại khách hàng
        self.category_filter = QComboBox()
        self.category_filter.addItem("Tất cả phân loại")
        self.category_filter.addItem("Mua nhiều")
        self.category_filter.addItem("Thuê nhiều")
        self.category_filter.addItem("Khá tích cực")
        self.category_filter.addItem("Ít giao dịch")
        self.category_filter.currentTextChanged.connect(self.filter_data)

        # Lọc theo mức độ chi tiêu
        self.spending_filter = QComboBox()
        self.spending_filter.addItem("Tất cả mức chi tiêu")
        self.spending_filter.addItem("Chi tiêu cao (>500k)")
        self.spending_filter.addItem("Chi tiêu trung bình (100k-500k)")
        self.spending_filter.addItem("Chi tiêu thấp (<100k)")
        self.spending_filter.currentTextChanged.connect(self.filter_data)

        # Các nút chức năng
        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_data)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)

        self.btn_export = QPushButton("Xuất báo cáo")
        self.btn_export.clicked.connect(self.export_report)

        # Thêm nút debug để kiểm tra dữ liệu
        self.btn_debug = QPushButton("Kiểm tra View")
        self.btn_debug.clicked.connect(self.debug_view)

        # Thêm các widget vào layout lọc
        filter_layout.addWidget(QLabel("Tìm kiếm:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Phân loại:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Chi tiêu:"))
        filter_layout.addWidget(self.spending_filter)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addWidget(self.btn_export)
        filter_layout.addWidget(self.btn_debug)

        main_layout.addLayout(filter_layout)

        # Bảng thống kê (giữa)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Mã KH", "Tên Khách Hàng", "SL Mua", "Tiền Mua",
            "SL Thuê", "Tiền Thuê", "Tổng Chi Tiêu", "Phân Loại"
        ])

        # Thiết lập kích thước cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Mã KH
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Tên KH
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # SL Mua
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Tiền Mua
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # SL Thuê
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Tiền Thuê
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Tổng Chi Tiêu
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Phân Loại

        # Đặt chiều rộng tối thiểu cho các cột
        self.table.setColumnWidth(0, 80)  # Mã KH
        self.table.setColumnWidth(1, 200)  # Tên KH
        self.table.setColumnWidth(2, 80)  # SL Mua
        self.table.setColumnWidth(3, 120)  # Tiền Mua
        self.table.setColumnWidth(4, 80)  # SL Thuê
        self.table.setColumnWidth(5, 120)  # Tiền Thuê
        self.table.setColumnWidth(6, 120)  # Tổng Chi Tiêu
        self.table.setColumnWidth(7, 120)  # Phân Loại

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Sắp xếp theo cột
        self.table.setSortingEnabled(True)

        main_layout.addWidget(self.table)

        # Layout thông tin tổng hợp (dưới cùng)
        summary_layout = QHBoxLayout()

        self.lbl_total_customers = QLabel("Tổng số khách hàng: 0")
        self.lbl_total_purchase = QLabel("Tổng tiền mua: 0 VNĐ")
        self.lbl_total_rental = QLabel("Tổng tiền thuê: 0 VNĐ")
        self.lbl_total_revenue = QLabel("Tổng doanh thu: 0 VNĐ")

        # Làm nổi bật label tổng doanh thu
        self.lbl_total_revenue.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2E8B57;
                padding: 5px;
                border: 2px solid #2E8B57;
                border-radius: 5px;
                background-color: #F0FFF0;
            }
        """)

        summary_layout.addWidget(self.lbl_total_customers)
        summary_layout.addWidget(self.lbl_total_purchase)
        summary_layout.addWidget(self.lbl_total_rental)
        summary_layout.addWidget(self.lbl_total_revenue)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

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
        """Tải toàn bộ dữ liệu thống kê khách hàng"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MaKH, TenKH, SoLuongMua, TongTienMua, 
                       SoLuongThue, TongTienThue, PhanLoai
                FROM ThongKeKhachHang
                ORDER BY (TongTienMua + TongTienThue) DESC
            """)
            data = cursor.fetchall()
            conn.close()

            self.populate_table(data)
            self.update_summary(data)
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def search_data(self):
        """Tìm kiếm theo tên khách hàng"""
        keyword = self.search_input.text().strip()
        category = self.category_filter.currentText()
        spending = self.spending_filter.currentText()

        self.filter_and_search(keyword, category, spending)

    def filter_data(self):
        """Lọc dữ liệu theo phân loại và mức chi tiêu"""
        keyword = self.search_input.text().strip()
        category = self.category_filter.currentText()
        spending = self.spending_filter.currentText()

        self.filter_and_search(keyword, category, spending)

    def filter_and_search(self, keyword="", category="Tất cả phân loại", spending="Tất cả mức chi tiêu"):
        """Thực hiện tìm kiếm và lọc dữ liệu"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            # Xây dựng câu truy vấn động
            query = """
                SELECT MaKH, TenKH, SoLuongMua, TongTienMua, 
                       SoLuongThue, TongTienThue, PhanLoai
                FROM ThongKeKhachHang 
                WHERE 1=1
            """
            params = {}

            # Thêm điều kiện tìm kiếm
            if keyword:
                query += " AND UPPER(TenKH) LIKE UPPER(:keyword)"
                params['keyword'] = f"%{keyword}%"

            # Thêm điều kiện lọc phân loại
            if category != "Tất cả phân loại":
                query += " AND PhanLoai = :category"
                params['category'] = category

            # Thêm điều kiện lọc mức chi tiêu
            if spending != "Tất cả mức chi tiêu":
                if spending == "Chi tiêu cao (>500k)":
                    query += " AND (TongTienMua + TongTienThue) > 500000"
                elif spending == "Chi tiêu trung bình (100k-500k)":
                    query += " AND (TongTienMua + TongTienThue) BETWEEN 100000 AND 500000"
                elif spending == "Chi tiêu thấp (<100k)":
                    query += " AND (TongTienMua + TongTienThue) < 100000"

            query += " ORDER BY (TongTienMua + TongTienThue) DESC"

            cursor.execute(query, params)
            data = cursor.fetchall()
            conn.close()

            self.populate_table(data)
            self.update_summary(data)

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi tìm kiếm/lọc dữ liệu: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")

    def populate_table(self, data):
        """Đổ dữ liệu vào bảng"""
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):

            for col_idx in range(8):
                if col_idx < 6:
                    value = row_data[col_idx] if col_idx < len(row_data) else None
                    if col_idx in [2, 3, 4, 5]:  # Các cột số lượng và tiền
                        display_value = f"{value:,}" if value is not None else "0"
                    else:
                        display_value = str(value) if value is not None else ""
                elif col_idx == 6:  # Cột tổng chi tiêu (tính toán)
                    total_spending = (row_data[3] or 0) + (row_data[5] or 0)
                    display_value = f"{total_spending:,}"
                elif col_idx == 7:  # Cột phân loại (index 6 trong data)
                    display_value = str(row_data[6]) if len(row_data) > 6 and row_data[
                        6] is not None else "Chưa phân loại"

                item = QTableWidgetItem(display_value)

                # Căn giữa cho các cột số
                if col_idx in [0, 2, 3, 4, 5, 6]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Tô màu theo phân loại
                if col_idx == 7:  # Cột phân loại
                    category_value = row_data[6] if len(row_data) > 6 else ""
                    if category_value == "Mua nhiều":
                        item.setBackground(Qt.GlobalColor.lightGreen)
                    elif category_value == "Thuê nhiều":
                        item.setBackground(Qt.GlobalColor.lightBlue)
                    elif category_value == "Khá tích cực":
                        item.setBackground(Qt.GlobalColor.yellow)
                    elif category_value == "Ít giao dịch":
                        item.setBackground(Qt.GlobalColor.lightGray)

                self.table.setItem(row_idx, col_idx, item)

    def update_summary(self, data):
        """Cập nhật thông tin tổng hợp"""
        total_customers = len(data)
        total_purchase = sum(row[3] for row in data if row[3] is not None)
        total_rental = sum(row[5] for row in data if row[5] is not None)
        total_revenue = total_purchase + total_rental

        self.lbl_total_customers.setText(f"Tổng số khách hàng: {total_customers}")
        self.lbl_total_purchase.setText(f"Tổng tiền mua: {total_purchase:,} VNĐ")
        self.lbl_total_rental.setText(f"Tổng tiền thuê: {total_rental:,} VNĐ")
        self.lbl_total_revenue.setText(f"Tổng doanh thu: {total_revenue:,} VNĐ")

    def export_report(self):
        """Xuất báo cáo thống kê khách hàng"""
        try:
            # Lấy dữ liệu hiện tại từ bảng
            row_count = self.table.rowCount()
            col_count = self.table.columnCount()

            if row_count == 0:
                QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất!")
                return

            # Tạo nội dung báo cáo dạng text
            report_content = "BÁO CÁO THỐNG KÊ KHÁCH HÀNG\n"
            report_content += "=" * 60 + "\n\n"

            # Header
            headers = []
            for col in range(col_count):
                headers.append(self.table.horizontalHeaderItem(col).text())
            report_content += "\t".join(headers) + "\n"
            report_content += "-" * 100 + "\n"

            # Data
            for row in range(row_count):
                row_data = []
                for col in range(col_count):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                report_content += "\t".join(row_data) + "\n"

            # Summary
            report_content += "\n" + "=" * 60 + "\n"
            report_content += "TỔNG KẾT:\n"
            report_content += self.lbl_total_customers.text() + "\n"
            report_content += self.lbl_total_purchase.text() + "\n"
            report_content += self.lbl_total_rental.text() + "\n"
            report_content += self.lbl_total_revenue.text() + "\n"

            # Phân tích thêm
            report_content += "\nPHÂN TÍCH KHÁCH HÀNG THEO PHÂN LOẠI:\n"
            categories = {}
            for row in range(row_count):
                category_item = self.table.item(row, 7)
                if category_item:
                    category = category_item.text()
                    categories[category] = categories.get(category, 0) + 1

            for category, count in categories.items():
                report_content += f"- {category}: {count} khách hàng\n"

            # Lưu file
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu báo cáo", "BaoCaoThongKeKhachHang.txt", "Text Files (*.txt)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo tại: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi xuất báo cáo: {str(e)}")

    def debug_view(self):
        """Kiểm tra dữ liệu từ view để debug"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            # Kiểm tra xem view có tồn tại không
            cursor.execute("""
                SELECT COUNT(*) FROM USER_VIEWS WHERE VIEW_NAME = 'THONGKEKHACHHANG'
            """)
            view_exists = cursor.fetchone()[0]

            if view_exists == 0:
                QMessageBox.warning(self, "Cảnh báo",
                                    "View 'ThongKeKhachHang' không tồn tại!\nVui lòng tạo view trước.")
                cursor.close()
                conn.close()
                return

            # Lấy 5 dòng đầu để kiểm tra
            cursor.execute("""
                SELECT MaKH, TenKH, SoLuongMua, TongTienMua, 
                       SoLuongThue, TongTienThue, PhanLoai
                FROM ThongKeKhachHang
                WHERE ROWNUM <= 5
            """)
            data = cursor.fetchall()

            # Hiển thị dữ liệu debug
            debug_text = "KIỂM TRA DỮ LIỆU VIEW:\n"
            debug_text += "=" * 50 + "\n"
            debug_text += f"Số dòng tìm thấy: {len(data)}\n\n"

            for i, row in enumerate(data):
                debug_text += f"Dòng {i + 1}:\n"
                debug_text += f"  MaKH: {row[0]}\n"
                debug_text += f"  TenKH: {row[1]}\n"
                debug_text += f"  SoLuongMua: {row[2]}\n"
                debug_text += f"  TongTienMua: {row[3]}\n"
                debug_text += f"  SoLuongThue: {row[4]}\n"
                debug_text += f"  TongTienThue: {row[5]}\n"
                debug_text += f"  PhanLoai: '{row[6]}'\n"
                debug_text += "-" * 30 + "\n"

            # Kiểm tra các giá trị phân loại có trong DB
            cursor.execute("""
                SELECT DISTINCT PhanLoai, COUNT(*) 
                FROM ThongKeKhachHang 
                GROUP BY PhanLoai
            """)
            categories = cursor.fetchall()

            debug_text += "\nCÁC PHÂN LOẠI TRONG DATABASE:\n"
            for cat, count in categories:
                debug_text += f"  '{cat}': {count} khách hàng\n"

            conn.close()

            # Hiển thị trong MessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Debug View")
            msg.setText(debug_text)
            msg.setStyleSheet("QLabel{min-width: 500px; min-height: 400px;}")
            msg.exec()

        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi Database", f"Lỗi kiểm tra view: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi không xác định: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomerStatistics()
    window.show()
    sys.exit(app.exec())