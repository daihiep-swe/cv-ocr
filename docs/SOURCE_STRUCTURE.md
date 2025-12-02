# Exam Grading System - Source Code Structure

## 📁 Cấu Trúc Thư Mục

```
scan/
├── src/                        # Source code chính
│   ├── __init__.py            # Package initialization
│   ├── app.py                 # Main application (CLI)
│   ├── image_processor.py     # Module xử lý ảnh
│   ├── grading_system.py      # Module chấm điểm
│   ├── csv_exporter.py        # Module xuất CSV
│   ├── excel_exporter.py      # Module xuất Excel
│   └── review.py              # Module phúc khảo
│
├── run_grading.py             # Script chạy chương trình chính
├── run_review.py              # Script chạy phúc khảo
├── requirements.txt           # Python dependencies
│
├── answers/                   # Thư mục đáp án
├── exams/                     # Thư mục ảnh phiếu thi
├── result/                    # Thư mục kết quả
│
├── debug/                     # Debug tools
├── docs/                      # Documentation
└── demo/                      # Demo version
```

## 🚀 Cách Chạy

### Từ Root Directory

**Sử dụng Shell Scripts (Khuyến nghị):**
```bash
# Chấm điểm
./run_grading.sh -a answers/ -i exams/

# Phúc khảo
./run_review.sh 123456 -a answers/ -i exams/
```

**Sử dụng Python trực tiếp:**
```bash
# Chấm điểm
python3 run_grading.py -a answers/ -i exams/

# Phúc khảo
python3 run_review.py 123456 -a answers/ -i exams/
```

### Import trong Code

```python
# Import từ src package
from src import ExamSheetProcessor, GradingSystem, CSVExporter

# Hoặc import trực tiếp
from src.image_processor import ExamSheetProcessor
from src.grading_system import GradingSystem
```

## 📦 Modules

### 1. `image_processor.py`
- **Class:** `ExamSheetProcessor`
- **Chức năng:** Xử lý ảnh, nhận diện SBD, mã đề, đáp án
- **Input:** Ảnh phiếu thi
- **Output:** Số báo danh, mã đề, dict đáp án

### 2. `grading_system.py`
- **Class:** `GradingSystem`
- **Chức năng:** Chấm điểm, so sánh đáp án
- **Input:** Đáp án chuẩn, đáp án học sinh
- **Output:** Điểm số, thống kê

### 3. `csv_exporter.py`
- **Class:** `CSVExporter`
- **Chức năng:** Xuất kết quả ra CSV
- **Input:** List kết quả chấm điểm
- **Output:** File CSV (kết quả, chi tiết, thống kê)

### 4. `app.py`
- **Function:** `main()`
- **Chức năng:** CLI application, multiprocessing
- **Features:**
  - Đọc đáp án từ file/folder
  - Xử lý đa luồng
  - Progress bar
  - Export CSV

### 5. `review.py`
- **Function:** `main()`
- **Chức năng:** Phúc khảo chi tiết 1 bài thi
- **Input:** Số báo danh
- **Output:** Chi tiết nhận diện và chấm điểm

## 🔧 Wrapper Scripts

### `run_grading.py`
```python
# Wrapper để chạy từ root directory
# Tự động add src/ vào Python path
import sys
sys.path.insert(0, 'src')
from src.app import main
```

### `run_review.py`
```python
# Wrapper cho review script
import sys
sys.path.insert(0, 'src')
from src.review import main
```

## 📝 Lưu Ý

1. **Python Path:** Wrapper scripts tự động thêm `src/` vào Python path
2. **Import:** Luôn import từ `src` package khi dùng trong code khác
3. **Data Directories:** `answers/`, `exams/`, `result/` ở root level
