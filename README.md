# 📝 Phần Mềm Chấm Điểm Trắc Nghiệm Tự Động

Phần mềm chấm điểm tự động các phiếu thi trắc nghiệm bằng xử lý ảnh với hỗ trợ **đa luồng** để tăng tốc độ xử lý.

## ✨ Tính năng

- 🚀 **Xử lý đa luồng** - Chấm điểm nhanh với nhiều CPU cores
- 📊 **Hỗ trợ nhiều mã đề** - Đọc đáp án từ thư mục, mỗi file là một mã đề
- 🎯 **Nhận diện chính xác** - Số báo danh, mã đề và 40 câu trắc nghiệm
- 📈 **Progress bar** - Hiển thị tiến độ và thời gian thực thi
- 📁 **Xuất CSV** - Kết quả chi tiết với thống kê

## 📁 Cấu Trúc Thư Mục

```
scan/
├── app.py                 # Chương trình chính
├── image_processor.py     # Module xử lý ảnh
├── grading_system.py      # Module chấm điểm
├── csv_exporter.py        # Module xuất CSV
├── paper.jpg              # Ảnh phiếu trắng (template)
├── requirements.txt       # Thư viện cần thiết
│
├── answers/               # Thư mục chứa đáp án
│   ├── 001.txt           # Đáp án mã đề 001
│   ├── 002.txt           # Đáp án mã đề 002
│   └── ...
│
├── exams/                 # Thư mục chứa ảnh phiếu thi
│   ├── 001_123456.jpg    # Phiếu: mã đề 001, SBD 123456
│   └── ...
│
├── result/                # Thư mục kết quả
│   └── ketqua_*.csv
│
└── debug/                 # Công cụ debug
    ├── debug_view.py      # Hiển thị vùng nhận diện
    └── generate_test_image.py  # Tạo phiếu test
```

## 🚀 Cài Đặt

### 1. Clone hoặc tải về

```bash
cd /path/to/scan
```

### 2. Cài đặt thư viện

```bash
pip3 install -r requirements.txt
```

Hoặc:
```bash
pip3 install opencv-python numpy
```

## 📖 Hướng Dẫn Sử Dụng

### Bước 1: Chuẩn bị đáp án

Tạo file đáp án trong thư mục `answers/`. Mỗi file là một mã đề.

**Ví dụ file `answers/001.txt`:**
```
1A
2B
3C
4D
5A
...
40C
```

> **Lưu ý:** Tên file = mã đề (001.txt → mã đề 001)

### Bước 2: Chuẩn bị ảnh phiếu thi

Đặt ảnh phiếu thi vào thư mục `exams/`

### Bước 3: Chạy chấm điểm

**Cách 1: Sử dụng shell script (Khuyến nghị)**
```bash
./run_grading.sh -a answers/ -i exams/
```

**Cách 2: Sử dụng Python trực tiếp**
```bash
python3 run_grading.py -a answers/ -i exams/
```

## 💻 Các Lệnh

### Chấm điểm cơ bản

```bash
# Chấm tất cả phiếu trong thư mục exams/
./run_grading.sh -a answers/ -i exams/

# Chấm các phiếu cụ thể
./run_grading.sh -a answers/ -i exams/001_*.jpg

# Chấm một phiếu
./run_grading.sh -a answers/001.txt -i exams/001_123456.jpg
```

### Các tùy chọn

| Tùy chọn | Mô tả | Mặc định |
|----------|-------|----------|
| `-a, --answers` | File hoặc thư mục đáp án | (bắt buộc) |
| `-i, --images` | File hoặc thư mục ảnh | (bắt buộc) |
| `-o, --output` | File CSV output | `result/ketqua_*.csv` |
| `-n, --num-questions` | Số câu hỏi | 40 |
| `-p, --points` | Điểm mỗi câu | 0.25 |
| `-m, --manual` | Nhập đáp án thủ công | - |

### Ví dụ nâng cao

```bash
# Chấm với 50 câu, mỗi câu 0.2 điểm
./run_grading.sh -a answers/ -i exams/

# Nhập đáp án thủ công
./run_grading.sh -m -i exams/
```

### Phúc khảo bài thi

Kiểm tra chi tiết bài thi của 1 học sinh theo số báo danh:

```bash
# Phúc khảo theo số báo danh
./run_review.sh 123456

# Chỉ định thư mục đáp án và ảnh
./run_review.sh 123456 -a answers/ -i exams/
```

**Kết quả phúc khảo:**
```
🔍 PHÚC KHẢO BÀI THI
==================================================
📋 Số báo danh: 123456
📄 File ảnh: 001_123456.jpg

📊 KẾT QUẢ NHẬN DIỆN:
   SBD phát hiện: 123456
   Mã đề: 001

📝 CHI TIẾT BÀI LÀM
  Câu │ Đáp án │Bài làm│  Kết quả  
------┼--------┼-------┼----------
   1  │   A    │   A   │ ✅ Đúng
   2  │   B    │   B   │ ✅ Đúng
   5  │   C    │   B   │ ❌ Sai
  12  │   A    │   -   │ ⬜ Bỏ trống
  ...

📊 TỔNG KẾT
   ✅ Số câu đúng:    38/40
   ❌ Số câu sai:      1/40
   ⬜ Số câu bỏ trống: 1/40
   🏆 ĐIỂM SỐ:        9.50/10.00
```

## 🛠 Debug & Test

### Tạo phiếu test với phân bố điểm chuẩn

```bash
python3 debug/generate_test_image.py
```

Tạo 50 phiếu/mã đề với phân bố điểm theo Normal Distribution:
- Mean = 65%, Std = 15%
- ~2.5% xuất sắc (90-100%)
- ~13.5% giỏi (80-90%)
- ~34% khá (65-80%)
- ~34% trung bình (50-65%)
- ~16% yếu-kém (<50%)

### Xem vùng nhận diện trên ảnh

```bash
python3 debug/debug_view.py exams/
```

Tạo ảnh debug với các vùng được đánh dấu trong thư mục `debug/`

## 📊 Output Mẫu

```
================================================================================
                    PHẦN MỀM CHẤM ĐIỂM TRẮC NGHIỆM
================================================================================

📖 Đang đọc đáp án...
   ✓ Đã đọc đáp án mã đề 001
   ✓ Đã đọc đáp án mã đề 002
   ...

✓ Tìm thấy 450 ảnh phiếu thi

==================================================
BẮT ĐẦU CHẤM ĐIỂM
==================================================
📊 Sử dụng 8 luồng để xử lý 450 phiếu
⏳ Đang chấm điểm: [██████████████████████████████] 100% (450/450)
✅ Hoàn thành chấm điểm
⏱️  Thời gian: 12.5 giây (36.0 phiếu/giây)

==========================================================================================
KẾT QUẢ CHẤM ĐIỂM
==========================================================================================
Số báo danh  Mã đề    Điểm       Đúng     Sai      Phần trăm   
------------------------------------------------------------------------------------------
123456       001      8.50       34       6        85.0%
234567       002      7.25       29       11       72.5%
...

THỐNG KÊ:
  • Tổng số sinh viên: 450
  • Điểm trung bình: 6.52
  • Điểm cao nhất: 10.00
  • Điểm thấp nhất: 2.25
  • Số sinh viên đạt: 387/450 (86.0%)
```

## 📋 Format File Đáp Án

```
# Định dạng đơn giản (khuyến nghị)
1A
2B
3C
4D
...
40A

# Hoặc với dấu phân cách
1:A
2:B
3.C
4 D
```

## ⚠️ Lưu Ý

1. **Ảnh phiếu thi** cần rõ ràng, không bị mờ hoặc nghiêng quá nhiều
2. **Mã đề** trong file đáp án = tên file (001.txt → mã đề 001)
3. **Phiếu không hợp lệ** (mã đề sai, không nhận diện được) sẽ bị bỏ qua
4. **Kết quả** được lưu trong thư mục `result/`

## 📞 Hỗ Trợ

Nếu gặp lỗi, chạy debug để kiểm tra:

```bash
# Xem vùng nhận diện
python3 debug/debug_view.py exams/ten_file.jpg

# Kiểm tra file debug trong thư mục debug/
```

---

Made with ❤️ by AI Assistant
