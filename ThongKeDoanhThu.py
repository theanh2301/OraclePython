import sys
import cx_Oracle
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QMessageBox, QHBoxLayout, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt


class RevenueStatistics(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle("Thống Kê Doanh Thu Truyện")
        self.setGeometry(100, 100, 1200, 700)

        # Layout chính
        main_layout = QVBoxLayout()

        # Layout thanh tìm kiếm và bộ lọc (trên cùng)
        filter_layout = QHBoxLayout()

        # Tìm kiếm theo tên truyện/tác giả
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên truyện hoặc tác giả để tìm kiếm...")
        self.search_input.returnPressed.connect(self.search_data)

        # Lọc theo thể loại
        self.category_filter = QComboBox()
        self.category_filter.addItem("Tất cả thể loại")
        self.load_categories()
        self.category_filter.currentTextChanged.connect(self.filter_data)

        # Lọc theo xếp hạng
        self.rank_filter = QComboBox()
        self.rank_filter.addItem("Tất cả xếp hạng")
        self.rank_filter.addItem("Bán nhiều nhất")
        self.rank_filter.addItem("Bán ít nhất")
        self.rank_filter.addItem("Bình thường")
        self.rank_filter.currentTextChanged.connect(self.filter_data)

        # Các nút chức năng
        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.clicked.connect(self.search_data)

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)

        self.btn_export = QPushButton("Xuất báo cáo")
        self.btn_export.clicked.connect(self.export_report)

        # Thêm các widget vào layout lọc
        filter_layout.addWidget(QLabel("Tìm kiếm:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Thể loại:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("Xếp hạng:"))
        filter_layout.addWidget(self.rank_filter)
        filter_layout.addWidget(self.btn_search)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addWidget(self.btn_export)

        main_layout.addLayout(filter_layout)

        # Bảng thống kê (giữa)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Mã Truyện", "Tên Truyện", "Tác Giả", "Thể Loại",
            "Tổng SL Bán", "Tổng Doanh Thu", "Xếp Hạng"
        ])

        # Thiết lập kích thước cột
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Mã Truyện
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Tên Truyện
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Tác Giả
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Thể Loại
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Tổng SL Bán
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Tổng Doanh Thu
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Xếp Hạng

        # Đặt chiều rộng tối thiểu cho các cột
        self.table.setColumnWidth(0, 100)  # Mã Truyện
        self.table.setColumnWidth(1, 200)  # Tên Truyện
        self.table.setColumnWidth(2, 150)  # Tác Giả
        self.table.setColumnWidth(3, 120)  # Thể Loại
        self.table.setColumnWidth(4, 100)  # Tổng SL Bán
        self.table.setColumnWidth(5, 120)  # Tổng Doanh Thu
        self.table.setColumnWidth(6, 120)  # Xếp Hạng

        # Cho phép chọn cả hàng
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Sắp xếp theo cột
        self.table.setSortingEnabled(True)

        main_layout.addWidget(self.table)

        # Layout thông tin tổng hợp (dưới cùng)
        summary_layout = QHBoxLayout()

        self.lbl_total_books = QLabel("Tổng số truyện: 0")
        self.lbl_total_sold = QLabel("Tổng số lượng bán: 0")
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

        summary_layout.addWidget(self.lbl_total_books)
        summary_layout.addWidget(self.lbl_total_sold)
        summary_layout.addWidget(self.lbl_total_revenue)
        summary_layout.addStretch()

        main_layout.addLayout(summary_layout)

        self.setLayout(main_layout)

    def connect_db(self):
        try:
            # Kết nối đến Oracle Database
            dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XEPDB1")
            connection = cx_Oracle.connect(user="truyenadmin", password="theanh2301", dsn=dsn)
            return connection
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi kết nối", f"Không thể kết nối đến Oracle Database: {str(e)}")
            return None

    def load_categories(self):
        """Tải danh sách thể loại từ database"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT TheLoai FROM V_ThongKeDoanhThu WHERE TheLoai IS NOT NULL ORDER BY TheLoai")
            categories = cursor.fetchall()
            conn.close()

            for category in categories:
                self.category_filter.addItem(category[0])
        except cx_Oracle.DatabaseError as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách thể loại: {str(e)}")

    def load_data(self):
        """Tải toàn bộ dữ liệu thống kê"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MaTruyen, TenTruyen, TacGia, TheLoai, 
                       TongSoLuongBan, TongDoanhThu, XepHang 
                FROM V_ThongKeDoanhThu
                ORDER BY TongSoLuongBan DESC
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
        """Tìm kiếm theo tên truyện hoặc tác giả"""
        keyword = self.search_input.text().strip()
        category = self.category_filter.currentText()
        rank = self.rank_filter.currentText()

        self.filter_and_search(keyword, category, rank)

    def filter_data(self):
        """Lọc dữ liệu theo thể loại và xếp hạng"""
        keyword = self.search_input.text().strip()
        category = self.category_filter.currentText()
        rank = self.rank_filter.currentText()

        self.filter_and_search(keyword, category, rank)

    def filter_and_search(self, keyword="", category="Tất cả thể loại", rank="Tất cả xếp hạng"):
        """Thực hiện tìm kiếm và lọc dữ liệu"""
        try:
            conn = self.connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            # Xây dựng câu truy vấn động
            query = """
                SELECT MaTruyen, TenTruyen, TacGia, TheLoai, 
                       TongSoLuongBan, TongDoanhThu, XepHang 
                FROM V_ThongKeDoanhThu 
                WHERE 1=1
            """
            params = {}

            # Thêm điều kiện tìm kiếm
            if keyword:
                query += " AND (UPPER(TenTruyen) LIKE UPPER(:keyword) OR UPPER(TacGia) LIKE UPPER(:keyword))"
                params['keyword'] = f"%{keyword}%"

            # Thêm điều kiện lọc thể loại
            if category != "Tất cả thể loại":
                query += " AND TheLoai = :category"
                params['category'] = category

            # Thêm điều kiện lọc xếp hạng
            if rank != "Tất cả xếp hạng":
                query += " AND XepHang = :rank"
                params['rank'] = rank

            query += " ORDER BY TongSoLuongBan DESC"

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
            for col_idx, value in enumerate(row_data):
                if col_idx == 4 or col_idx == 5:  # Cột số lượng và doanh thu
                    display_value = f"{value:,}" if value is not None else "0"
                else:
                    display_value = str(value) if value is not None else ""

                item = QTableWidgetItem(display_value)

                # Căn giữa cho các cột số
                if col_idx in [0, 4, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Tô màu theo xếp hạng
                if col_idx == 6:  # Cột xếp hạng
                    if value == "Bán nhiều nhất":
                        item.setBackground(Qt.GlobalColor.green)
                    elif value == "Bán ít nhất":
                        item.setBackground(Qt.GlobalColor.red)

                self.table.setItem(row_idx, col_idx, item)

    def update_summary(self, data):
        """Cập nhật thông tin tổng hợp"""
        total_books = len(data)
        total_sold = sum(row[4] for row in data if row[4] is not None)
        total_revenue = sum(row[5] for row in data if row[5] is not None)

        self.lbl_total_books.setText(f"Tổng số truyện: {total_books}")
        self.lbl_total_sold.setText(f"Tổng số lượng bán: {total_sold:,}")
        self.lbl_total_revenue.setText(f"Tổng doanh thu: {total_revenue:,} VNĐ")

    def export_report(self):
        """Xuất báo cáo (có thể mở rộng để xuất Excel/PDF)"""
        try:
            # Lấy dữ liệu hiện tại từ bảng
            row_count = self.table.rowCount()
            col_count = self.table.columnCount()

            if row_count == 0:
                QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất!")
                return

            # Tạo nội dung báo cáo dạng text
            report_content = "BÁO CÁO THỐNG KÊ DOANH THU TRUYỆN\n"
            report_content += "=" * 50 + "\n\n"

            # Header
            headers = []
            for col in range(col_count):
                headers.append(self.table.horizontalHeaderItem(col).text())
            report_content += "\t".join(headers) + "\n"
            report_content += "-" * 80 + "\n"

            # Data
            for row in range(row_count):
                row_data = []
                for col in range(col_count):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                report_content += "\t".join(row_data) + "\n"

            # Summary
            report_content += "\n" + "=" * 50 + "\n"
            report_content += "TỔNG KẾT:\n"
            report_content += self.lbl_total_books.text() + "\n"
            report_content += self.lbl_total_sold.text() + "\n"
            report_content += self.lbl_total_revenue.text() + "\n"

            # Lưu file (đơn giản)
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu báo cáo", "BaoCaoThongKe.txt", "Text Files (*.txt)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo tại: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi xuất báo cáo: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RevenueStatistics()
    window.show()
    sys.exit(app.exec())