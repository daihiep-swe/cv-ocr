"""
Module xử lý ảnh phiếu thi trắc nghiệm
Nhận diện số báo danh và các ô tô trên phiếu
Format: Xử lý đầy đủ 3 phần
- PHẦN I: 40 câu trắc nghiệm (A, B, C, D)
- PHẦN II: 8 câu (mỗi câu 2 ô Đúng/Sai)
- PHẦN III: 6 câu điền số (mỗi câu 4 chữ số, mỗi chữ số 0-9)
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import re


class ExamSheetProcessor:
    """Xử lý và nhận diện phiếu thi trắc nghiệm"""

    def __init__(self, num_questions: int = 40):
        """
        Khởi tạo processor

        Args:
            num_questions: Số câu hỏi PHẦN I (mặc định 40)
        """
        self.num_questions = num_questions
        self.choices_per_question = 4  # A, B, C, D
        # self.part2_questions = 8  # PHẦN II: 8 câu
        # self.part3_questions = 6  # PHẦN III: 6 câu
    
    # Kích thước chuẩn của phiếu thi (paper.jpg)
    STANDARD_WIDTH = 1920
    STANDARD_HEIGHT = 2755
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Tiền xử lý ảnh phiếu thi
        
        Args:
            image_path: Đường dẫn đến file ảnh

        Returns:
            Ảnh đã được xử lý hoặc None nếu lỗi
        """
        try:
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Resize về kích thước chuẩn nếu khác tỷ lệ
            h, w = image.shape[:2]
            need_enhance = False
            if w != self.STANDARD_WIDTH or h != self.STANDARD_HEIGHT:
                # Nếu upscale (ảnh nhỏ hơn chuẩn) thì cần enhance
                if w < self.STANDARD_WIDTH or h < self.STANDARD_HEIGHT:
                    need_enhance = True
                image = cv2.resize(
                    image, 
                    (self.STANDARD_WIDTH, self.STANDARD_HEIGHT), 
                    interpolation=cv2.INTER_CUBIC if need_enhance else cv2.INTER_AREA
                )

            # Chuyển sang grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Làm mờ để giảm nhiễu
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Áp dụng threshold OTSU trực tiếp (không cần đảo ngược)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Nếu ảnh được upscale, dùng morphology để làm đậm bubble
            if need_enhance:
                # Dilation để làm đậm các vùng đen (bubble đã tô)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                thresh = cv2.dilate(thresh, kernel, iterations=1)

            return thresh

        except Exception as e:
            print(f"Lỗi khi xử lý ảnh: {e}")
            return None

    def find_answer_bubbles(
        self, thresh_image: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        Tìm các ô tô (bubbles) trên phiếu - CHỈ LẤY Ô HÌNH TRÒN

        Args:
            thresh_image: Ảnh đã qua threshold

        Returns:
            List các ô tô dạng (x, y, width, height)
        """
        # Tìm contours - dùng RETR_LIST để lấy tất cả
        contours, _ = cv2.findContours(
            thresh_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        bubbles = []

        # Lọc các contours theo kích thước VÀ HÌNH DẠNG TRÒN
        for contour in contours:
            area = cv2.contourArea(contour)

            # Lọc theo kích thước
            if area < 200 or area > 3000:
                continue

            # Lấy bounding box
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0

            # Kiểm tra tỷ lệ gần vuông (cho hình tròn)
            if not (0.7 <= aspect_ratio <= 1.4):
                continue
            
            # Kiểm tra độ tròn (circularity)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Hình tròn hoàn hảo có circularity = 1.0
            # Chấp nhận từ 0.3 trở lên (để bắt cả ô đã tô đen)
            if circularity >= 0.3:
                bubbles.append((x, y, w, h))

        # Lọc bỏ các ô trùng lặp
        bubbles = self._remove_duplicate_bubbles(bubbles)

        # Sắp xếp các ô theo vị trí (từ trên xuống, trái sang phải)
        bubbles = sorted(bubbles, key=lambda b: (b[1], b[0]))

        return bubbles
    
    def _remove_duplicate_bubbles(self, bubbles: List[Tuple], threshold: int = 25) -> List[Tuple]:
        """Loại bỏ các ô trùng lặp hoặc quá gần nhau"""
        if not bubbles:
            return []
        
        # Sắp xếp theo vị trí
        sorted_bubbles = sorted(bubbles, key=lambda b: (b[1], b[0]))
        
        unique = []
        for b in sorted_bubbles:
            is_dup = False
            for u in unique:
                # Kiểm tra tâm của 2 ô có quá gần nhau không
                center_b = (b[0] + b[2]//2, b[1] + b[3]//2)
                center_u = (u[0] + u[2]//2, u[1] + u[3]//2)
                dist = ((center_b[0] - center_u[0])**2 + (center_b[1] - center_u[1])**2)**0.5
                
                if dist < threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(b)
        return unique
    
    def _normalize_column(self, col_bubbles: List[Tuple]) -> List[Tuple]:
        """Chuẩn hóa cột về đúng 10 ô (từ số 0 đến số 9)"""
        if len(col_bubbles) <= 10:
            return col_bubbles
        
        # Sắp xếp theo y (từ trên xuống)
        sorted_col = sorted(col_bubbles, key=lambda b: b[1])
        
        # Nếu có nhiều hơn 10 ô, cần loại bỏ các ô thừa (có thể là label hoặc nhiễu)
        if len(sorted_col) > 10:
            # Tính khoảng cách giữa các ô liên tiếp
            gaps = []
            for i in range(len(sorted_col) - 1):
                gap = sorted_col[i + 1][1] - sorted_col[i][1]
                gaps.append(gap)
            
            # Tính khoảng cách chuẩn (median của các gap lớn)
            # Các ô đáp án thường có khoảng cách đều nhau khoảng 60-70px
            sorted_gaps = sorted(gaps, reverse=True)
            # Lấy median của 9 gap lớn nhất (vì có 10 ô = 9 gap)
            if len(sorted_gaps) >= 9:
                standard_gap = sorted(sorted_gaps[:9])[4]  # median
            else:
                standard_gap = sum(gaps) / len(gaps) if gaps else 60
            
            # Tìm và loại bỏ các ô có gap quá nhỏ (< 50% standard_gap)
            # Giữ lại ô SAU trong cặp quá gần (vì ô trước thường là label/nhiễu)
            filtered_col = []
            skip_next = False
            
            for i in range(len(sorted_col)):
                if skip_next:
                    skip_next = False
                    continue
                    
                if i < len(sorted_col) - 1:
                    gap_to_next = sorted_col[i + 1][1] - sorted_col[i][1]
                    
                    # Nếu khoảng cách quá nhỏ, bỏ ô hiện tại (có thể là label)
                    if gap_to_next < standard_gap * 0.5:
                        continue
                
                filtered_col.append(sorted_col[i])
            
            # Nếu vẫn còn nhiều hơn 10 ô, lấy 10 ô có khoảng cách đều nhất
            if len(filtered_col) > 10:
                # Lấy 10 ô cuối (bỏ các ô đầu có thể là label)
                filtered_col = filtered_col[-10:]
            
            sorted_col = filtered_col
        
        return sorted_col[:10]

    def extract_student_id_and_exam_code(
        self, image: np.ndarray, bubbles: List[Tuple]
    ) -> Tuple[str, str]:
        """
        Trích xuất số báo danh và mã đề thi từ các ô tô ở góc phải trên
        Sử dụng logic giống debug_view.py với các tham số đã calibrate
        Format:
        - Số báo danh: 6 cột, mỗi cột 10 ô (số 0-9, từ trên xuống)
        - Mã đề: 3 cột, mỗi cột 10 ô (số 0-9, từ trên xuống)

        Args:
            image: Ảnh đã xử lý (threshold)
            bubbles: Danh sách các ô tô

        Returns:
            Tuple (số_báo_danh, mã_đề) ví dụ: ("102001", "001")
        """
        height, width = image.shape

        # Tham số từ debug_view.py đã calibrate
        # Vùng SỐ BÁO DANH (6 cột)
        SBD_X_START = 0.73
        SBD_X_END = 0.85
        SBD_Y_START = 0.09
        SBD_Y_END = 0.285
        SBD_NUM_COLS = 6

        # Vùng MÃ ĐỀ (3 cột)
        EXAM_X_START = 0.88
        EXAM_X_END = 0.94
        EXAM_Y_START = 0.09
        EXAM_Y_END = 0.285
        EXAM_NUM_COLS = 3
        
        CONTRAST_THRESHOLD = 10  # Ngưỡng tương phản để xác định ô được tô

        # Lọc bubbles trong vùng SBD
        sbd_bubbles = [
            (x, y, w, h)
            for x, y, w, h in bubbles
            if SBD_X_START * width < x < SBD_X_END * width 
            and SBD_Y_START * height < y < SBD_Y_END * height
        ]
        
        # Lọc bubbles trong vùng mã đề
        exam_code_bubbles = [
            (x, y, w, h)
            for x, y, w, h in bubbles
            if EXAM_X_START * width < x < EXAM_X_END * width 
            and EXAM_Y_START * height < y < EXAM_Y_END * height
        ]

        # Đảm bảo có đủ grid và đọc giá trị
        sbd_full_grid = self._ensure_full_grid(sbd_bubbles, num_cols=SBD_NUM_COLS, num_rows=10)
        exam_full_grid = self._ensure_full_grid(exam_code_bubbles, num_cols=EXAM_NUM_COLS, num_rows=10)

        student_id = self._read_digit_grid(image, sbd_full_grid, CONTRAST_THRESHOLD)
        exam_code = self._read_digit_grid(image, exam_full_grid, CONTRAST_THRESHOLD)

        return student_id, exam_code
    
    def _read_digit_grid(self, image: np.ndarray, full_grid: List[List[Tuple]], contrast_threshold: float = 10) -> str:
        """
        Đọc giá trị từ grid số (SBD, Mã đề) - logic giống debug_view.py
        
        Args:
            image: Ảnh threshold
            full_grid: Grid đầy đủ từ _ensure_full_grid
            contrast_threshold: Ngưỡng tương phản
            
        Returns:
            Chuỗi số đọc được
        """
        if not full_grid:
            return ""
        
        result = ""
        
        for col_idx, col_bubbles in enumerate(full_grid):
            # Tính độ đậm của từng ô trong cột
            darkness_values = []
            for row_idx, (x, y, w, h) in enumerate(col_bubbles):
                bubble_roi = image[y:y+h, x:x+w]
                if bubble_roi.size > 0:
                    avg_intensity = np.mean(bubble_roi)
                    darkness_values.append((row_idx, avg_intensity))
                else:
                    darkness_values.append((row_idx, 0))
            
            if darkness_values:
                # Sắp xếp theo độ đậm (cao nhất = được tô)
                darkness_values.sort(key=lambda x: x[1], reverse=True)
                selected = darkness_values[0]
                max_dark = selected[1]
                min_dark = darkness_values[-1][1]
                
                if max_dark - min_dark >= contrast_threshold:
                    digit = selected[0]
                    result += str(digit)
                else:
                    result += "0"
            else:
                result += "0"
        
        return result
    
    def _ensure_full_grid(self, bubbles: List[Tuple], num_cols: int, num_rows: int = 10) -> List[List[Tuple]]:
        """
        Đảm bảo luôn có đủ grid num_cols x num_rows ô
        Nếu không detect đủ, tự động tạo grid dựa trên các ô đã tìm thấy
        
        Args:
            bubbles: Danh sách các ô đã detect được
            num_cols: Số cột cần có
            num_rows: Số hàng cần có (mặc định 10)
        
        Returns:
            List các cột, mỗi cột có đúng num_rows ô
        """
        if not bubbles:
            return []
        
        # Nhóm các ô theo cột
        columns = self._group_bubbles_by_column(bubbles, tolerance=20)
        
        if not columns:
            return []
        
        # Tính kích thước ô trung bình từ các ô đã detect
        all_widths = [b[2] for b in bubbles]
        all_heights = [b[3] for b in bubbles]
        avg_w = int(np.median(all_widths)) if all_widths else 30
        avg_h = int(np.median(all_heights)) if all_heights else 30
        
        # Tính vị trí x trung bình của mỗi cột
        col_x_positions = []
        for col in columns:
            if col:
                avg_x = int(np.mean([b[0] for b in col]))
                col_x_positions.append(avg_x)
        
        # Tính khoảng cách giữa các cột
        if len(col_x_positions) >= 2:
            col_gaps = [col_x_positions[i+1] - col_x_positions[i] for i in range(len(col_x_positions)-1)]
            avg_col_gap = int(np.median(col_gaps))
        else:
            avg_col_gap = avg_w + 10  # Ước lượng
        
        # Tính khoảng cách giữa các hàng từ cột có nhiều ô nhất
        row_gaps = []
        for col in columns:
            if len(col) >= 2:
                sorted_col = sorted(col, key=lambda b: b[1])
                for i in range(len(sorted_col) - 1):
                    gap = sorted_col[i+1][1] - sorted_col[i][1]
                    if gap > avg_h * 0.5:  # Chỉ lấy gap hợp lệ
                        row_gaps.append(gap)
        
        avg_row_gap = int(np.median(row_gaps)) if row_gaps else avg_h + 10
        
        # Tìm vị trí y bắt đầu (hàng đầu tiên)
        all_y = [b[1] for b in bubbles]
        min_y = min(all_y)
        
        # Tạo grid đầy đủ
        full_grid = []
        
        for col_idx in range(num_cols):
            col_bubbles = []
            
            # Xác định x cho cột này
            if col_idx < len(col_x_positions):
                col_x = col_x_positions[col_idx]
            elif col_x_positions:
                # Ngoại suy vị trí x
                col_x = col_x_positions[-1] + avg_col_gap * (col_idx - len(col_x_positions) + 1)
            else:
                continue
            
            # Lấy các ô đã detect trong cột này
            existing_col = columns[col_idx] if col_idx < len(columns) else []
            existing_col = sorted(existing_col, key=lambda b: b[1])
            
            # Tạo đủ 10 ô cho cột
            for row_idx in range(num_rows):
                expected_y = min_y + row_idx * avg_row_gap
                
                # Tìm ô đã detect gần vị trí expected
                found_bubble = None
                for b in existing_col:
                    if abs(b[1] - expected_y) < avg_row_gap * 0.5:
                        found_bubble = b
                        break
                
                if found_bubble:
                    col_bubbles.append(found_bubble)
                else:
                    # Tạo ô ảo tại vị trí expected
                    virtual_bubble = (col_x, expected_y, avg_w, avg_h)
                    col_bubbles.append(virtual_bubble)
            
            full_grid.append(col_bubbles)
        
        return full_grid
    
    def _ensure_full_answer_grid(self, bubbles: List[Tuple], num_cols: int = 4, num_rows: int = 10, 
                                     region_x_start: int = None, region_x_end: int = None,
                                     region_y_start: int = None, region_y_end: int = None) -> List[List[Tuple]]:
        """
        Tạo grid cố định dựa trên vùng đã calibrate.
        Grid được chia đều thành num_cols x num_rows ô.
        Mỗi bubble được gán vào ô gần nhất trong grid.
        
        Args:
            bubbles: Danh sách các ô đã detect được
            num_cols: Số cột (A, B, C, D = 4)
            num_rows: Số hàng (câu hỏi, mặc định 10)
            region_x_start: Vị trí x bắt đầu của vùng
            region_x_end: Vị trí x kết thúc của vùng
            region_y_start: Vị trí y bắt đầu của vùng
            region_y_end: Vị trí y kết thúc của vùng
        
        Returns:
            List các hàng, mỗi hàng có đúng num_cols ô
        """
        if region_x_start is None or region_x_end is None:
            return self._ensure_full_answer_grid_fallback(bubbles, num_cols, num_rows)
        
        # Tính kích thước ô từ vùng đã calibrate
        region_width = region_x_end - region_x_start
        cell_width = region_width / num_cols
        
        # Tính kích thước bubble trung bình (nếu có)
        if bubbles:
            all_widths = [b[2] for b in bubbles]
            all_heights = [b[3] for b in bubbles]
            avg_w = int(np.median(all_widths))
            avg_h = int(np.median(all_heights))
        else:
            avg_w = int(cell_width * 0.6)
            avg_h = avg_w
        
        # Tính vùng y từ bubbles nếu không được cung cấp
        if region_y_start is None or region_y_end is None:
            if bubbles:
                all_y = [b[1] for b in bubbles]
                region_y_start = min(all_y) - avg_h // 2
                region_y_end = max(all_y) + avg_h + avg_h // 2
            else:
                return []
        
        region_height = region_y_end - region_y_start
        cell_height = region_height / num_rows
        
        # Tạo grid cố định - mỗi ô có tọa độ trung tâm cố định
        # Bubble sẽ được gán vào ô dựa trên vị trí
        full_grid = []  # [row][col] = (x, y, w, h)
        
        for row_idx in range(num_rows):
            row_bubbles = []
            # Tọa độ y trung tâm của hàng
            cell_center_y = region_y_start + (row_idx + 0.5) * cell_height
            
            for col_idx in range(num_cols):
                # Tọa độ x trung tâm của cột
                cell_center_x = region_x_start + (col_idx + 0.5) * cell_width
                
                # Tìm bubble gần nhất nằm trong ô này
                best_bubble = None
                min_distance = float('inf')
                
                # Định nghĩa boundary của ô
                cell_x1 = region_x_start + col_idx * cell_width
                cell_x2 = region_x_start + (col_idx + 1) * cell_width
                cell_y1 = region_y_start + row_idx * cell_height
                cell_y2 = region_y_start + (row_idx + 1) * cell_height
                
                for b in bubbles:
                    bx, by, bw, bh = b
                    bubble_center_x = bx + bw / 2
                    bubble_center_y = by + bh / 2
                    
                    # Kiểm tra bubble có nằm trong ô này không
                    if cell_x1 <= bubble_center_x < cell_x2 and cell_y1 <= bubble_center_y < cell_y2:
                        # Tính khoảng cách đến trung tâm ô
                        distance = ((bubble_center_x - cell_center_x) ** 2 + 
                                   (bubble_center_y - cell_center_y) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            best_bubble = b
                
                if best_bubble:
                    row_bubbles.append(best_bubble)
                else:
                    # Tạo ô ảo tại vị trí trung tâm
                    virtual_x = int(cell_center_x - avg_w / 2)
                    virtual_y = int(cell_center_y - avg_h / 2)
                    virtual_bubble = (virtual_x, virtual_y, avg_w, avg_h)
                    row_bubbles.append(virtual_bubble)
            
            full_grid.append(row_bubbles)
        
        return full_grid
    
    def _ensure_full_answer_grid_fallback(self, bubbles: List[Tuple], num_cols: int = 4, num_rows: int = 10) -> List[List[Tuple]]:
        """
        Fallback khi không có vùng calibrate - dùng bubble detect để tính grid
        """
        if not bubbles:
            return []
        
        # Tính kích thước ô trung bình
        all_widths = [b[2] for b in bubbles]
        all_heights = [b[3] for b in bubbles]
        avg_w = int(np.median(all_widths)) if all_widths else 30
        avg_h = int(np.median(all_heights)) if all_heights else 30
        
        # Nhóm theo hàng trước
        rows = self._group_bubbles_by_row(bubbles, tolerance=15)
        
        if not rows:
            return []
        
        # Tính vị trí y trung bình của mỗi hàng
        row_y_positions = []
        for row in rows:
            if row:
                avg_y = int(np.mean([b[1] for b in row]))
                row_y_positions.append(avg_y)
        
        # Tính khoảng cách giữa các hàng
        if len(row_y_positions) >= 2:
            row_gaps = [row_y_positions[i+1] - row_y_positions[i] for i in range(len(row_y_positions)-1)]
            avg_row_gap = int(np.median(row_gaps))
        else:
            avg_row_gap = avg_h + 10
        
        # Tính khoảng cách giữa các cột
        col_gaps = []
        for row in rows:
            if len(row) >= 2:
                sorted_row = sorted(row, key=lambda b: b[0])
                for i in range(len(sorted_row) - 1):
                    gap = sorted_row[i+1][0] - sorted_row[i][0]
                    if gap > avg_w * 0.5:
                        col_gaps.append(gap)
        
        avg_col_gap = int(np.median(col_gaps)) if col_gaps else avg_w + 10
        all_x = [b[0] for b in bubbles]
        min_x = min(all_x)
        
        # Tìm vị trí y bắt đầu
        min_y = min(row_y_positions) if row_y_positions else min([b[1] for b in bubbles])
        
        # Tạo grid đầy đủ theo hàng
        full_grid = []
        
        for row_idx in range(num_rows):
            row_bubbles = []
            
            if row_idx < len(row_y_positions):
                row_y = row_y_positions[row_idx]
            elif row_y_positions:
                row_y = row_y_positions[-1] + avg_row_gap * (row_idx - len(row_y_positions) + 1)
            else:
                row_y = min_y + row_idx * avg_row_gap
            
            existing_row = rows[row_idx] if row_idx < len(rows) else []
            existing_row = sorted(existing_row, key=lambda b: b[0])
            
            for col_idx in range(num_cols):
                expected_x = min_x + col_idx * avg_col_gap
                
                found_bubble = None
                for b in existing_row:
                    if abs(b[0] - expected_x) < avg_col_gap * 0.5:
                        found_bubble = b
                        break
                
                if found_bubble:
                    row_bubbles.append(found_bubble)
                else:
                    virtual_bubble = (expected_x, row_y, avg_w, avg_h)
                    row_bubbles.append(virtual_bubble)
            
            full_grid.append(row_bubbles)
        
        return full_grid
    
    def _read_digit_columns(self, image: np.ndarray, bubbles: List[Tuple], num_columns: int) -> str:
        """Đọc các cột số từ danh sách ô tô"""
        if not bubbles:
            return "0" * num_columns

        # Đảm bảo có đủ grid num_columns x 10
        full_grid = self._ensure_full_grid(bubbles, num_columns, num_rows=10)
        
        if not full_grid:
            # Fallback: dùng cách cũ
            columns = self._group_bubbles_by_column(bubbles, tolerance=20)
            valid_columns = [col for col in columns if len(col) >= 8][:num_columns]
            valid_columns = [self._normalize_column(col) for col in valid_columns]
        else:
            valid_columns = full_grid

        result = ""

        for col_bubbles in valid_columns:
            # Sắp xếp theo y (từ trên xuống)
            col_bubbles = sorted(col_bubbles, key=lambda b: b[1])
            
            # Đảm bảo có đúng 10 ô, nếu thiếu thì bỏ qua cột này
            if len(col_bubbles) < 10:
                result += "0"
                continue
            
            col_bubbles = col_bubbles[:10]
            
            # Tính khoảng cách trung bình giữa các ô để kiểm tra
            y_positions = [b[1] for b in col_bubbles]
            gaps = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0

            # Tính độ đậm của từng ô
            darkness_values = []
            for digit_idx, (x, y, w, h) in enumerate(col_bubbles):
                bubble_roi = image[y : y + h, x : x + w]

                if bubble_roi.size == 0:
                    darkness_values.append((digit_idx, 0))
                    continue

                avg_intensity = np.mean(bubble_roi)
                darkness_values.append((digit_idx, avg_intensity))

            # Tìm ô tối nhất
            if darkness_values:
                darkness_values.sort(key=lambda x: x[1], reverse=True)
                selected_digit = darkness_values[0][0]
                max_darkness = darkness_values[0][1]
                min_darkness = darkness_values[-1][1]
                contrast = max_darkness - min_darkness
                
                has_filled = contrast >= 10  # Giảm ngưỡng từ 15 xuống 10
            else:
                selected_digit = 0
                has_filled = False

            if has_filled:
                result += str(selected_digit)
            else:
                result += "0"

        # Đảm bảo đúng độ dài
        result = result.ljust(num_columns, "0")[:num_columns]

        return result

    def extract_answers(
        self, image: np.ndarray, bubbles: List[Tuple]
    ) -> Dict[int, str]:
        """
        Trích xuất đáp án PHẦN I (40 câu) từ các ô tô
        Sử dụng logic giống debug_view.py

        Args:
            image: Ảnh đã xử lý
            bubbles: Danh sách các ô tô

        Returns:
            Dict với key là số câu hỏi (1-40), value là đáp án (A/B/C/D)
        """
        answers = {}
        height, width = image.shape

        # Tham số từ debug_view.py đã calibrate
        ANSWER_Y_START = 0.365
        ANSWER_Y_END = 0.523
        ANSWER_COLUMNS = [
            (0.118, 0.265, 1),    # Cột 1: câu 1-10
            (0.331, 0.478, 11),   # Cột 2: câu 11-20
            (0.544, 0.691, 21),   # Cột 3: câu 21-30
            (0.757, 0.904, 31),   # Cột 4: câu 31-40
        ]
        CONTRAST_THRESHOLD = 10

        choice_map = {0: "A", 1: "B", 2: "C", 3: "D"}

        for col_x_start, col_x_end, start_question in ANSWER_COLUMNS:
            # Lọc bubbles trong vùng cột này
            col_bubbles = [
                (x, y, w, h)
                for x, y, w, h in bubbles
                if col_x_start * width < x < col_x_end * width 
                and ANSWER_Y_START * height < y < ANSWER_Y_END * height
            ]

            if not col_bubbles:
                continue

            # Tính vị trí pixel của vùng cột
            region_x_start = int(col_x_start * width)
            region_x_end = int(col_x_end * width)
            region_y_start = int(ANSWER_Y_START * height)
            region_y_end = int(ANSWER_Y_END * height)

            # Đảm bảo có đủ 40 ô (4 cột A,B,C,D x 10 hàng)
            full_grid = self._ensure_full_answer_grid(
                col_bubbles, num_cols=4, num_rows=10,
                region_x_start=region_x_start, region_x_end=region_x_end,
                region_y_start=region_y_start, region_y_end=region_y_end
            )
            
            if not full_grid:
                continue

            # Đọc đáp án từ grid
            for row_idx, row_bubbles in enumerate(full_grid):
                question_num = start_question + row_idx
                if question_num > 40:
                    break

                # Tính độ đậm của từng ô trong hàng
                darkness_values = []
                for col_idx, (x, y, w, h) in enumerate(row_bubbles):
                    bubble_roi = image[y:y+h, x:x+w]
                    if bubble_roi.size > 0:
                        avg_intensity = np.mean(bubble_roi)
                        darkness_values.append((col_idx, avg_intensity, x, y, w, h))
                    else:
                        darkness_values.append((col_idx, 0, x, y, w, h))

                if darkness_values:
                    # Sắp xếp theo độ đậm (cao nhất = được tô)
                    darkness_values.sort(key=lambda x: x[1], reverse=True)
                    selected = darkness_values[0]
                    max_dark = selected[1]
                    min_dark = darkness_values[-1][1]

                    if max_dark - min_dark >= CONTRAST_THRESHOLD:
                        choice_idx = selected[0]
                        if choice_idx < 4:
                            answers[question_num] = choice_map[choice_idx]

        return answers

    def extract_part2_answers(
        self, image: np.ndarray, bubbles: List[Tuple]
    ) -> Dict[str, str]:
        """
        Trích xuất đáp án PHẦN II (8 câu, mỗi câu 2 đáp án Đúng/Sai)
        """
        answers = {}
        height, width = image.shape

        # Vùng PHẦN II: khoảng 58-70% chiều cao
        part2_bubbles = [
            (x, y, w, h)
            for x, y, w, h in bubbles
            if 0.58 * height < y < 0.70 * height and 0.05 * width < x < 0.95 * width
        ]

        rows = self._group_bubbles_by_row(part2_bubbles, tolerance=15)
        parts = ["a", "b", "c", "d"]

        row_idx = 0
        for q_num in range(1, 9):  # 8 câu
            for part in parts:  # 4 phần mỗi câu
                if row_idx >= len(rows):
                    break

                row_bubbles = rows[row_idx]
                if len(row_bubbles) >= 2:
                    dung_bubble = row_bubbles[0]
                    sai_bubble = row_bubbles[1]

                    x1, y1, w1, h1 = dung_bubble
                    x2, y2, w2, h2 = sai_bubble

                    dung_roi = image[y1 : y1 + h1, x1 : x1 + w1]
                    sai_roi = image[y2 : y2 + h2, x2 : x2 + w2]

                    dung_filled = (
                        cv2.countNonZero(dung_roi) / dung_roi.size
                        if dung_roi.size > 0
                        else 0
                    )
                    sai_filled = (
                        cv2.countNonZero(sai_roi) / sai_roi.size
                        if sai_roi.size > 0
                        else 0
                    )

                    if dung_filled >= 0.4 or sai_filled >= 0.4:
                        key = f"P2_Q{q_num}_{part}"
                        answers[key] = "D" if dung_filled > sai_filled else "S"

                row_idx += 1

        return answers

    def extract_part3_answers(
        self, image: np.ndarray, bubbles: List[Tuple]
    ) -> Dict[str, str]:
        """
        Trích xuất đáp án PHẦN III (6 câu điền số)
        """
        answers = {}
        height, width = image.shape

        # Vùng PHẦN III: khoảng 70-95% chiều cao
        part3_bubbles = [
            (x, y, w, h)
            for x, y, w, h in bubbles
            if 0.70 * height < y < 0.95 * height and 0.05 * width < x < 0.95 * width
        ]

        columns = self._group_bubbles_by_column(part3_bubbles, tolerance=15)

        # 6 câu, mỗi câu 4 cột
        for q_num in range(1, 7):
            start_col = (q_num - 1) * 4
            end_col = start_col + 4

            if end_col > len(columns):
                break

            number = ""
            for col_idx in range(start_col, end_col):
                col_bubbles = sorted(columns[col_idx], key=lambda b: b[1])[:10]

                digit = 0
                max_filled = 0

                for digit_idx, (x, y, w, h) in enumerate(col_bubbles):
                    bubble_roi = image[y : y + h, x : x + w]
                    if bubble_roi.size == 0:
                        continue

                    filled_ratio = cv2.countNonZero(bubble_roi) / bubble_roi.size
                    if filled_ratio > max_filled:
                        max_filled = filled_ratio
                        digit = digit_idx

                if max_filled >= 0.35:
                    number += str(digit)
                else:
                    number += "0"

            if len(number) == 4:
                answers[f"P3_Q{q_num}"] = number

        return answers

    def _group_bubbles_by_row(
        self, bubbles: List[Tuple], tolerance: int = 20
    ) -> List[List[Tuple]]:
        """
        Nhóm các ô tô theo hàng ngang

        Args:
            bubbles: Danh sách các ô tô
            tolerance: Độ lệch cho phép về tọa độ y

        Returns:
            List các hàng, mỗi hàng chứa list các ô
        """
        if not bubbles:
            return []

        rows = []
        current_row = [bubbles[0]]
        current_y = bubbles[0][1]

        for bubble in bubbles[1:]:
            y = bubble[1]

            # Nếu y gần với y hiện tại -> cùng hàng
            if abs(y - current_y) <= tolerance:
                current_row.append(bubble)
            else:
                # Sắp xếp hàng theo x (trái sang phải)
                current_row.sort(key=lambda b: b[0])
                rows.append(current_row)

                # Bắt đầu hàng mới
                current_row = [bubble]
                current_y = y

        # Thêm hàng cuối
        if current_row:
            current_row.sort(key=lambda b: b[0])
            rows.append(current_row)

        return rows

    def _group_bubbles_by_column(
        self, bubbles: List[Tuple], tolerance: int = 20
    ) -> List[List[Tuple]]:
        """
        Nhóm các ô tô theo cột dọc

        Args:
            bubbles: Danh sách các ô tô
            tolerance: Độ lệch cho phép về tọa độ x

        Returns:
            List các cột, mỗi cột chứa list các ô
        """
        if not bubbles:
            return []

        # Sắp xếp theo x
        sorted_bubbles = sorted(bubbles, key=lambda b: b[0])

        columns = []
        current_col = [sorted_bubbles[0]]
        current_x = sorted_bubbles[0][0]

        for bubble in sorted_bubbles[1:]:
            x = bubble[0]

            if abs(x - current_x) <= tolerance:
                current_col.append(bubble)
            else:
                # Sắp xếp cột theo y (trên xuống)
                current_col.sort(key=lambda b: b[1])
                columns.append(current_col)

                current_col = [bubble]
                current_x = x

        if current_col:
            current_col.sort(key=lambda b: b[1])
            columns.append(current_col)

        return columns

    def process_exam_sheet(
        self, image_path: str
    ) -> Optional[Tuple[str, str, Dict[int, str]]]:
        """
        Xử lý toàn bộ phiếu thi và trả về kết quả

        Args:
            image_path: Đường dẫn đến file ảnh

        Returns:
            Tuple (số báo danh, mã đề, dict đáp án) hoặc None nếu lỗi
        """
        # Tiền xử lý ảnh
        thresh_image = self.preprocess_image(image_path)
        if thresh_image is None:
            return None

        # Tìm các ô tô
        bubbles = self.find_answer_bubbles(thresh_image)
        if not bubbles:
            print("Không tìm thấy ô tô nào trên phiếu")
            return None

        # Đọc lại ảnh gốc cho việc trích xuất
        original_image = cv2.imread(image_path)

        # Trích xuất số báo danh và mã đề
        student_id, exam_code = self.extract_student_id_and_exam_code(
            thresh_image, bubbles
        )

        # Trích xuất đáp án PHẦN I (40 câu trắc nghiệm)
        answers = self.extract_answers(thresh_image, bubbles)

        return student_id, exam_code, answers

    def debug_draw_regions(self, image_path: str, output_path: str = None) -> str:
        """
        Vẽ khung lên các vùng đang được chương trình nhận diện để debug
        
        Args:
            image_path: Đường dẫn ảnh gốc
            output_path: Đường dẫn lưu ảnh debug (mặc định: thêm _debug vào tên file)
            
        Returns:
            Đường dẫn file ảnh debug
        """
        import os
        
        # Đọc ảnh gốc
        image = cv2.imread(image_path)
        if image is None:
            print(f"Không thể đọc ảnh: {image_path}")
            return None
            
        height, width = image.shape[:2]
        
        # Tiền xử lý để tìm bubbles
        thresh_image = self.preprocess_image(image_path)
        bubbles = self.find_answer_bubbles(thresh_image)
        
        # Màu sắc cho các vùng
        COLOR_SBD = (0, 255, 0)       # Xanh lá - Số báo danh
        COLOR_EXAM = (255, 0, 0)      # Xanh dương - Mã đề
        COLOR_ANSWERS = (0, 0, 255)   # Đỏ - Vùng đáp án
        COLOR_SELECTED = (255, 0, 255) # Tím - Ô được chọn (tô đậm nhất)
        
        # ========== VẼ VÙNG SỐ BÁO DANH ==========
        sbd_x1 = int(0.71 * width)
        sbd_x2 = int(0.85 * width)
        sbd_y1 = int(0.10 * height)
        sbd_y2 = int(0.30 * height)
        cv2.rectangle(image, (sbd_x1, sbd_y1), (sbd_x2, sbd_y2), COLOR_SBD, 3)
        cv2.putText(image, "SO BAO DANH", (sbd_x1, sbd_y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_SBD, 2)
        
        # Lọc bubbles trong vùng SBD
        sbd_bubbles = [
            (x, y, w, h) for x, y, w, h in bubbles
            if 0.71 * width < x < 0.85 * width and 0.10 * height < y < 0.30 * height
        ]
        
        # Vẽ tất cả bubbles trong vùng SBD
        for (x, y, w, h) in sbd_bubbles:
            cv2.rectangle(image, (x, y), (x + w, y + h), COLOR_SBD, 1)
        
        # Nhóm theo cột và tìm ô được chọn
        sbd_columns = self._group_bubbles_by_column(sbd_bubbles, tolerance=20)
        valid_sbd_cols = [col for col in sbd_columns if len(col) >= 8][:6]
        
        student_id = ""
        for col_bubbles in valid_sbd_cols:
            col_bubbles = sorted(col_bubbles, key=lambda b: b[1])[:10]
            
            # Tính độ đậm
            darkness_values = []
            for digit_idx, (x, y, w, h) in enumerate(col_bubbles):
                bubble_roi = thresh_image[y:y+h, x:x+w]
                if bubble_roi.size > 0:
                    avg_intensity = np.mean(bubble_roi)
                    darkness_values.append((digit_idx, avg_intensity, x, y, w, h))
            
            if darkness_values:
                darkness_values.sort(key=lambda x: x[1], reverse=True)
                selected = darkness_values[0]
                max_dark = selected[1]
                min_dark = darkness_values[-1][1]
                
                if max_dark - min_dark >= 15:
                    # Vẽ ô được chọn với màu tím và đường dày hơn
                    x, y, w, h = selected[2], selected[3], selected[4], selected[5]
                    cv2.rectangle(image, (x-2, y-2), (x+w+2, y+h+2), COLOR_SELECTED, 3)
                    student_id += str(selected[0])
                else:
                    student_id += "0"
        
        # ========== VẼ VÙNG MÃ ĐỀ ==========
        exam_x1 = int(0.86 * width)
        exam_x2 = int(0.96 * width)
        exam_y1 = int(0.10 * height)
        exam_y2 = int(0.30 * height)
        cv2.rectangle(image, (exam_x1, exam_y1), (exam_x2, exam_y2), COLOR_EXAM, 3)
        cv2.putText(image, "MA DE", (exam_x1, exam_y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_EXAM, 2)
        
        # Lọc bubbles trong vùng mã đề
        exam_bubbles = [
            (x, y, w, h) for x, y, w, h in bubbles
            if 0.86 * width < x < 0.96 * width and 0.10 * height < y < 0.30 * height
        ]
        
        for (x, y, w, h) in exam_bubbles:
            cv2.rectangle(image, (x, y), (x + w, y + h), COLOR_EXAM, 1)
        
        # Nhóm theo cột và tìm ô được chọn cho mã đề
        exam_columns = self._group_bubbles_by_column(exam_bubbles, tolerance=20)
        valid_exam_cols = [col for col in exam_columns if len(col) >= 8][:3]
        
        exam_code = ""
        for col_bubbles in valid_exam_cols:
            col_bubbles = sorted(col_bubbles, key=lambda b: b[1])[:10]
            
            darkness_values = []
            for digit_idx, (x, y, w, h) in enumerate(col_bubbles):
                bubble_roi = thresh_image[y:y+h, x:x+w]
                if bubble_roi.size > 0:
                    avg_intensity = np.mean(bubble_roi)
                    darkness_values.append((digit_idx, avg_intensity, x, y, w, h))
            
            if darkness_values:
                darkness_values.sort(key=lambda x: x[1], reverse=True)
                selected = darkness_values[0]
                max_dark = selected[1]
                min_dark = darkness_values[-1][1]
                
                if max_dark - min_dark >= 15:
                    x, y, w, h = selected[2], selected[3], selected[4], selected[5]
                    cv2.rectangle(image, (x-2, y-2), (x+w+2, y+h+2), COLOR_SELECTED, 3)
                    exam_code += str(selected[0])
                else:
                    exam_code += "0"
        
        # ========== VẼ VÙNG ĐÁP ÁN PHẦN I ==========
        Y_START = 0.355
        Y_END = 0.523
        COLUMNS = [
            (0.095, 0.245, 1),
            (0.32, 0.47, 11),
            (0.545, 0.695, 21),
            (0.77, 0.92, 31),
        ]
        
        for col_x_start, col_x_end, start_q in COLUMNS:
            x1 = int(col_x_start * width)
            x2 = int(col_x_end * width)
            y1 = int(Y_START * height)
            y2 = int(Y_END * height)
            cv2.rectangle(image, (x1, y1), (x2, y2), COLOR_ANSWERS, 2)
            cv2.putText(image, f"Cau {start_q}-{start_q+9}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_ANSWERS, 2)
        
        # ========== HIỂN THỊ KẾT QUẢ ==========
        # Thêm text kết quả nhận diện
        cv2.putText(image, f"SBD: {student_id}", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(image, f"Ma de: {exam_code}", (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(image, f"Bubbles found: {len(bubbles)}", (50, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
        cv2.putText(image, f"SBD cols: {len(valid_sbd_cols)}, Exam cols: {len(valid_exam_cols)}", 
                    (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
        
        # Lưu ảnh
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_debug{ext}"
        
        cv2.imwrite(output_path, image)
        print(f"✓ Đã lưu ảnh debug: {output_path}")
        print(f"  - Số báo danh nhận diện: {student_id}")
        print(f"  - Mã đề nhận diện: {exam_code}")
        
        return output_path