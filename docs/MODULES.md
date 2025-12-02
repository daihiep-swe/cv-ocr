# 📚 Giải Thích Chi Tiết Từng File Python

## 📋 Mục Lục

1. [app.py](#1-apppy---chương-trình-chính)
2. [image_processor.py](#2-image_processorpy---xử-lý-ảnh)
3. [grading_system.py](#3-grading_systempy---chấm-điểm)
4. [csv_exporter.py](#4-csv_exporterpy---xuất-csv)
5. [excel_exporter.py](#5-excel_exporterpy---xuất-excel)
6. [review.py](#6-reviewpy---phúc-khảo)

---

## 1. `app.py` - Chương Trình Chính

### 📝 Mô tả
File điều khiển chính của ứng dụng, xử lý tham số dòng lệnh và điều phối các module khác.

### 🔧 Import
```python
import argparse          # Xử lý tham số command line
import os                # Thao tác file/thư mục
from multiprocessing import Pool, cpu_count  # Xử lý đa luồng
from datetime import datetime  # Lấy thời gian hiện tại
```

### 📦 Các hàm chính

#### `is_valid_exam_code(exam_code: str) -> bool`
Kiểm tra mã đề có hợp lệ không (phải là 3 chữ số).

```python
def is_valid_exam_code(exam_code: str) -> bool:
    return len(exam_code) == 3 and exam_code.isdigit()
    # "001" -> True
    # "1"   -> False
    # "ABC" -> False
```

#### `read_answer_key_from_text(file_path: str) -> Tuple[str, Dict]`
Đọc đáp án từ file text. Mã đề lấy từ tên file.

**Input:** `answers/001.txt`
```
1A
2B
3C
...
```

**Output:** `("001", {1: "A", 2: "B", 3: "C", ...})`

#### `read_all_answer_keys(folder_path: str) -> Dict[str, Dict]`
Đọc tất cả file đáp án trong thư mục.

**Output:**
```python
{
    "001": {1: "A", 2: "B", ...},
    "002": {1: "C", 2: "D", ...},
    ...
}
```

#### `_init_worker(answer_keys, num_q, points)`
Khởi tạo biến global cho mỗi worker process. Cần thiết vì multiprocessing tạo process riêng biệt.

```python
# Biến global để chia sẻ giữa các process
_all_answer_keys = {}
_num_questions = 40
_points_per_question = 0.25

def _init_worker(answer_keys, num_q, points):
    global _all_answer_keys, _num_questions, _points_per_question
    _all_answer_keys = answer_keys
    _num_questions = num_q
    _points_per_question = points
```

#### `_process_single_image(image_path: str) -> Dict`
Xử lý và chấm điểm 1 ảnh. Chạy trong worker process.

```python
def _process_single_image(image_path: str) -> Dict:
    # 1. Tạo processor
    processor = ExamSheetProcessor(_num_questions)
    
    # 2. Xử lý ảnh -> lấy SBD, mã đề, đáp án
    result = processor.process_exam_sheet(image_path)
    student_id, exam_code, student_answers = result
    
    # 3. Tìm đáp án chuẩn theo mã đề
    answer_key = _all_answer_keys.get(exam_code)
    
    # 4. Chấm điểm
    grading_system = GradingSystem(answer_key, _points_per_question)
    graded_result = grading_system.get_detailed_results(student_id, student_answers)
    
    return graded_result
```

#### `process_and_grade(...) -> List[Dict]`
Xử lý đa luồng với multiprocessing Pool.

```python
def process_and_grade(image_files, all_answer_keys, num_questions, points_per_question):
    num_workers = min(cpu_count(), len(image_files), 8)  # Tối đa 8 workers
    
    with Pool(processes=num_workers, initializer=_init_worker, 
              initargs=(all_answer_keys, num_questions, points_per_question)) as pool:
        
        for image_path in image_files:
            pool.apply_async(
                _process_single_image, 
                args=(image_path,), 
                callback=update_progress  # Cập nhật progress bar
            )
    
    return results
```

#### `main()`
Hàm chính - điều phối toàn bộ luồng:
1. Parse tham số dòng lệnh
2. Đọc đáp án
3. Lấy danh sách ảnh
4. Chấm điểm
5. Hỏi xuất CSV

---

## 2. `image_processor.py` - Xử Lý Ảnh

### 📝 Mô tả
Module cốt lõi xử lý ảnh phiếu thi, nhận diện SBD, mã đề và đáp án.

### 🔧 Import
```python
import cv2              # OpenCV - xử lý ảnh
import numpy as np      # Tính toán ma trận
from typing import List, Tuple, Dict, Optional
```

### 📦 Class: `ExamSheetProcessor`

#### Hằng số quan trọng
```python
# Kích thước chuẩn của phiếu thi
STANDARD_WIDTH = 1920
STANDARD_HEIGHT = 2755

# Vùng SỐ BÁO DANH (tỷ lệ % so với kích thước ảnh)
SBD_X_START = 0.73    # Bắt đầu từ 73% chiều rộng
SBD_X_END = 0.85      # Kết thúc ở 85% chiều rộng
SBD_Y_START = 0.09    # Từ 9% chiều cao
SBD_Y_END = 0.285     # Đến 28.5% chiều cao

# Vùng MÃ ĐỀ
EXAM_X_START = 0.88
EXAM_X_END = 0.94
# Y giống SBD

# Vùng ĐÁP ÁN - 4 cột
ANSWER_COLUMNS = [
    (0.118, 0.265, 1),    # x_start, x_end, câu_bắt_đầu
    (0.331, 0.478, 11),
    (0.544, 0.691, 21),
    (0.757, 0.904, 31),
]
```

#### `preprocess_image(image_path: str) -> np.ndarray`
Tiền xử lý ảnh để dễ nhận diện.

```python
def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
    # 1. Đọc ảnh
    image = cv2.imread(image_path)
    
    # 2. Resize về kích thước chuẩn (nếu cần)
    if w != STANDARD_WIDTH or h != STANDARD_HEIGHT:
        image = cv2.resize(image, (STANDARD_WIDTH, STANDARD_HEIGHT))
    
    # 3. Chuyển sang grayscale (ảnh xám)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 4. Làm mờ để giảm nhiễu
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 5. Áp dụng threshold OTSU
    # -> Chuyển ảnh thành đen trắng (binary)
    _, thresh = cv2.threshold(blurred, 0, 255, 
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 6. Nếu upscale, dùng dilation để làm đậm bubble
    if need_enhance:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.dilate(thresh, kernel, iterations=1)
    
    return thresh
```

**Giải thích:**
- **Grayscale:** Chuyển ảnh màu thành xám (1 kênh thay vì 3)
- **GaussianBlur:** Làm mờ để loại bỏ nhiễu nhỏ
- **Threshold OTSU:** Tự động tìm ngưỡng tối ưu để chuyển thành ảnh nhị phân
- **Dilation:** Làm "phình" các vùng trắng (bubble đã tô)

#### `find_answer_bubbles(thresh_image: np.ndarray) -> List[Tuple]`
Tìm tất cả các ô tròn (bubble) trên phiếu.

```python
def find_answer_bubbles(self, thresh_image: np.ndarray):
    # 1. Tìm contours (đường viền)
    contours, _ = cv2.findContours(
        thresh_image, 
        cv2.RETR_LIST,           # Lấy tất cả contours
        cv2.CHAIN_APPROX_SIMPLE  # Nén contour
    )
    
    bubbles = []
    for contour in contours:
        # 2. Tính diện tích
        area = cv2.contourArea(contour)
        if area < 200 or area > 3000:  # Lọc kích thước
            continue
        
        # 3. Lấy bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # 4. Kiểm tra tỷ lệ (gần vuông)
        aspect_ratio = w / float(h)
        if not (0.7 <= aspect_ratio <= 1.4):
            continue
        
        # 5. Kiểm tra độ tròn
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter ** 2)
        # Hình tròn hoàn hảo = 1.0
        if circularity >= 0.3:
            bubbles.append((x, y, w, h))
    
    return bubbles
```

#### `_ensure_full_answer_grid(...) -> List[List[Tuple]]`
Tạo grid cố định cho vùng đáp án. Đảm bảo mỗi câu hỏi đều có 4 ô A, B, C, D.

```python
def _ensure_full_answer_grid(self, bubbles, num_cols=4, num_rows=10,
                              region_x_start=None, region_x_end=None,
                              region_y_start=None, region_y_end=None):
    # 1. Tính kích thước mỗi ô trong grid
    cell_width = (region_x_end - region_x_start) / num_cols
    cell_height = (region_y_end - region_y_start) / num_rows
    
    # 2. Tạo grid
    full_grid = []
    for row_idx in range(num_rows):
        row_bubbles = []
        for col_idx in range(num_cols):
            # Tìm bubble nằm trong ô này
            # Nếu không có -> tạo ô ảo
            ...
        full_grid.append(row_bubbles)
    
    return full_grid
```

#### `extract_student_id_and_exam_code(...) -> Tuple[str, str]`
Trích xuất SBD và mã đề.

```python
def extract_student_id_and_exam_code(self, image, bubbles):
    # 1. Lọc bubbles trong vùng SBD
    sbd_bubbles = [b for b in bubbles 
                   if SBD_X_START * width < b[0] < SBD_X_END * width]
    
    # 2. Đọc từng cột số (6 cột cho SBD)
    student_id = self._read_digit_columns(image, sbd_bubbles, num_columns=6)
    
    # 3. Tương tự cho mã đề (3 cột)
    exam_code = self._read_digit_columns(image, exam_bubbles, num_columns=3)
    
    return student_id, exam_code
```

#### `extract_answers(...) -> Dict[int, str]`
Trích xuất đáp án 40 câu.

```python
def extract_answers(self, image, bubbles):
    answers = {}
    
    for col_x_start, col_x_end, start_question in ANSWER_COLUMNS:
        # 1. Lọc bubbles trong cột này
        col_bubbles = [b for b in bubbles if col_x_start * width < b[0] < col_x_end * width]
        
        # 2. Tạo grid đầy đủ (10 hàng x 4 cột)
        full_grid = self._ensure_full_answer_grid(col_bubbles, ...)
        
        # 3. Đọc đáp án từng hàng
        for row_idx, row_bubbles in enumerate(full_grid):
            question_num = start_question + row_idx
            
            # Tính độ đậm của từng ô
            darkness_values = []
            for bubble in row_bubbles:
                roi = image[y:y+h, x:x+w]
                avg_intensity = np.mean(roi)
                darkness_values.append(avg_intensity)
            
            # Ô đậm nhất = đáp án được chọn
            selected_idx = np.argmax(darkness_values)
            answers[question_num] = ["A", "B", "C", "D"][selected_idx]
    
    return answers
```

---

## 3. `grading_system.py` - Chấm Điểm

### 📝 Mô tả
Module so sánh đáp án và tính điểm.

### 📦 Class: `GradingSystem`

```python
class GradingSystem:
    def __init__(self, answer_key: Dict[int, str], points_per_question: float = 0.25):
        """
        Args:
            answer_key: Đáp án chuẩn {1: "A", 2: "B", ...}
            points_per_question: Điểm mỗi câu (mặc định 0.25 -> 40 câu = 10 điểm)
        """
        self.answer_key = answer_key
        self.points_per_question = points_per_question
```

#### `grade_answers(student_answers: Dict) -> Tuple[float, int, int]`
Chấm điểm và trả về kết quả.

```python
def grade_answers(self, student_answers: Dict[int, str]) -> Tuple[float, int, int]:
    correct = 0
    wrong = 0
    
    for q_num, correct_ans in self.answer_key.items():
        student_ans = student_answers.get(q_num, "")
        
        if student_ans == correct_ans:
            correct += 1
        else:
            wrong += 1
    
    score = correct * self.points_per_question
    return score, correct, wrong
```

#### `get_detailed_results(...) -> Dict`
Trả về kết quả chi tiết.

```python
def get_detailed_results(self, student_id: str, student_answers: Dict) -> Dict:
    score, correct, wrong = self.grade_answers(student_answers)
    
    return {
        "student_id": student_id,
        "score": score,
        "correct_count": correct,
        "wrong_count": wrong,
        "percentage": (correct / len(self.answer_key)) * 100,
        "answers": student_answers,
        "correct_answers": self.answer_key  # Để so sánh chi tiết
    }
```

---

## 4. `csv_exporter.py` - Xuất CSV

### 📝 Mô tả
Xuất kết quả chấm điểm ra file CSV.

### 📦 Class: `CSVExporter`

```python
import csv

class CSVExporter:
    def export_results(self, results: List[Dict], output_path: str, 
                       include_details: bool = False) -> bool:
        """
        Args:
            results: Danh sách kết quả từ GradingSystem
            output_path: Đường dẫn file output
            include_details: Có xuất chi tiết từng câu không
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header
                header = ["STT", "Số báo danh", "Mã đề", "Điểm", "Đúng", "Sai", "%"]
                if include_details:
                    header.extend([f"Câu {i}" for i in range(1, 41)])
                writer.writerow(header)
                
                # Data rows
                for idx, result in enumerate(results, 1):
                    row = [
                        idx,
                        result["student_id"],
                        result["exam_code"],
                        f"{result['score']:.2f}",
                        result["correct_count"],
                        result["wrong_count"],
                        f"{result['percentage']:.1f}%"
                    ]
                    
                    if include_details:
                        for q in range(1, 41):
                            row.append(result["answers"].get(q, "-"))
                    
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Lỗi xuất CSV: {e}")
            return False
```

**Lưu ý:** Dùng `utf-8-sig` để Excel đọc được tiếng Việt.

---

## 5. `excel_exporter.py` - Xuất Excel

### 📝 Mô tả
Xuất kết quả ra file Excel với định dạng đẹp.

### 📦 Class: `ExcelExporter`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

class ExcelExporter:
    def export_results(self, results: List[Dict], output_path: str) -> bool:
        wb = Workbook()
        ws = wb.active
        ws.title = "Kết quả chấm điểm"
        
        # 1. Header với style
        headers = ["STT", "SBD", "Mã đề", "Điểm", ...]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="4472C4")
            cell.alignment = Alignment(horizontal="center")
        
        # 2. Data rows
        for row_idx, result in enumerate(results, 2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value=result["student_id"])
            ...
        
        # 3. Tự động điều chỉnh độ rộng cột
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = max_length + 2
        
        wb.save(output_path)
        return True
```

---

## 6. `review.py` - Phúc Khảo

### 📝 Mô tả
Công cụ kiểm tra chi tiết bài thi của 1 học sinh theo SBD.

### 📦 Các hàm chính

#### `find_student_image(student_id: str, exams_dir: str) -> str`
Tìm file ảnh theo SBD.

```python
def find_student_image(student_id: str, exams_dir: str = "exams") -> str:
    """
    Tên file format: XXX_YYYYYY.jpg (mã_đề_SBD)
    VD: 001_123456.jpg
    """
    for file in os.listdir(exams_dir):
        base_name = os.path.splitext(file)[0]
        parts = base_name.split('_')
        if len(parts) >= 2 and parts[1] == student_id:
            return os.path.join(exams_dir, file)
    return None
```

#### `review_student(student_id: str, ...) -> Dict`
Phúc khảo bài thi.

```python
def review_student(student_id: str, answers_dir: str = "answers", exams_dir: str = "exams"):
    # 1. Tìm file ảnh
    image_path = find_student_image(student_id, exams_dir)
    
    # 2. Xử lý ảnh
    processor = ExamSheetProcessor()
    detected_sbd, exam_code, student_answers = processor.process_exam_sheet(image_path)
    
    # 3. Đọc đáp án chuẩn
    answer_key = read_answer_key(f"{answers_dir}/{exam_code}.txt")
    
    # 4. So sánh và hiển thị
    for q in range(1, 41):
        correct_ans = answer_key.get(q, "-")
        student_ans = student_answers.get(q, "-")
        
        if student_ans == correct_ans:
            status = "✅ Đúng"
        elif student_ans == "-":
            status = "⬜ Bỏ trống"
        else:
            status = "❌ Sai"
        
        print(f"Câu {q}: Đáp án {correct_ans} | Bài làm {student_ans} | {status}")
    
    # 5. Tính điểm
    score = correct_count * 0.25
    print(f"Điểm: {score}/10")
```

---

## 🔗 Quan Hệ Giữa Các Module

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                               │
│                    (Điều phối chính)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   image_    │  │  grading_   │  │    csv_     │
│  processor  │  │   system    │  │  exporter   │
│             │  │             │  │             │
│ • Đọc ảnh   │  │ • So sánh   │  │ • Xuất CSV  │
│ • Tìm bubble│  │ • Tính điểm │  │             │
│ • Trích xuất│  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  review.py  │
                  │             │
                  │ • Phúc khảo │
                  │ • Chi tiết  │
                  └─────────────┘
```

---

*Tài liệu được tạo tự động - Cập nhật: December 2024*
