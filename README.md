# 📝 Phần Mềm Chấm Điểm Trắc Nghiệm - Hướng Dẫn Windows

## 🚀 Cài Đặt

### Bước 1: Cài đặt Python

1. Tải Python từ [python.org/downloads](https://www.python.org/downloads/)
2. Chạy file cài đặt
3. ✅ **QUAN TRỌNG:** Tick vào **"Add Python to PATH"** ở màn hình đầu tiên
4. Nhấn **Install Now**

### Bước 2: Kiểm tra cài đặt

Mở **Command Prompt** (nhấn `Win + R`, gõ `cmd`, Enter) và chạy:

```cmd
python --version
```

Nếu hiện `Python 3.x.x` là thành công ✅

---

## ▶️ Chạy Chương Trình

### Chuẩn bị

1. **Đáp án:** Đặt file `.txt` trong thư mục `answers\` (mỗi file = 1 mã đề)
2. **Ảnh phiếu thi:** Đặt vào thư mục `exams\`

### Chạy chấm điểm

**Cách 1: Double-click (đơn giản nhất)**
- Mở thư mục chứa chương trình
- Double-click vào file `run_grading_windows.bat`

**Cách 2: Chạy thuần Python (từng bước)**

Mở **Command Prompt** và chạy lần lượt:

```cmd
cd C:\đường\dẫn\đến\thư\mục\scan

rem Tạo môi trường ảo (chỉ cần chạy 1 lần)
python -m venv venv

rem Kích hoạt môi trường ảo
venv\Scripts\activate

rem Cài đặt thư viện (chỉ cần chạy 1 lần)
pip install -r requirements.txt

rem Chạy chấm điểm
python run_grading.py -a answers\ -i exams\
```

> 💡 **Lưu ý:** Từ lần sau chỉ cần kích hoạt venv và chạy:
> ```cmd
> venv\Scripts\activate
> python run_grading.py -a answers\ -i exams\
> ```

### Các tùy chọn

| Tùy chọn | Mô tả | Mặc định |
|----------|-------|----------|
| `-a` | Thư mục đáp án | (bắt buộc) |
| `-i` | Thư mục ảnh phiếu thi | (bắt buộc) |
| `-o` | File Excel output | `result\ketqua_*.xlsx` |
| `-n` | Số câu hỏi | 40 |
| `-p` | Điểm mỗi câu | 0.25 |

---

## 🔍 Phúc Khảo Bài Thi

Kiểm tra chi tiết bài thi của 1 học sinh theo số báo danh:

```cmd
python run_review.py 123456 -a answers\ -i exams\
```

---

## 📊 Kết Quả

File Excel sẽ được lưu trong thư mục `result\` với 3 sheet:

| Sheet | Nội dung |
|-------|----------|
| **Kết quả** | Điểm tổng quan của tất cả học sinh |
| **Chi tiết câu sai** | Liệt kê từng câu sai của mỗi học sinh |
| **Thống kê** | Điểm TB, cao nhất, thấp nhất, tỷ lệ đạt |

---

## ❌ Xử Lý Lỗi

| Lỗi | Cách sửa |
|-----|----------|
| Python is not available | Cài lại Python, tick **"Add Python to PATH"** |
| pip install failed | Chạy cmd với quyền **Admin** |
| cv2 module not found | `pip install opencv-python numpy pandas openpyxl` |

---

Made with ❤️ by AI Assistant
# 📝 Phần Mềm Chấm Điểm Trắc Nghiệm - Hướng Dẫn Windows