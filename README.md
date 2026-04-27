# Phần Mềm Chấm Điểm Trắc Nghiệm

## Yêu cầu chung

- Python 3.10+.
- File đáp án đặt trong thư mục `answers/`, mỗi mã đề là một file `.txt`, ví dụ `001.txt`.
- Ảnh phiếu thi đặt trong thư mục `exams/`.
- Kết quả Excel sẽ được xuất vào thư mục `result/`.

## Cài đặt trên macOS

Mở Terminal tại thư mục dự án rồi chạy:

```bash
cd /duong/dan/den/cv-ocr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Nếu máy dùng lệnh `python` thay cho `python3`, có thể dùng:

```bash
python -m venv venv
```

## Cài đặt trên Windows

1. Tải Python từ [python.org/downloads](https://www.python.org/downloads/).
2. Khi cài đặt, tick **Add Python to PATH**.
3. Mở Command Prompt hoặc PowerShell tại thư mục dự án rồi chạy:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Cách chạy chấm điểm

### macOS

Chạy bình thường, có lưu ảnh debug vào thư mục `debug/`:

```bash
source venv/bin/activate
python run_grading.py -a answers/ -i exams/
```

Chạy production, bỏ qua lưu ảnh debug để nhanh hơn và không sinh file `debug/*_aligned.jpg`, `debug/*_thresh.jpg`:

```bash
source venv/bin/activate
python run_grading.py -a answers/ -i exams/ --prod
```

### Windows

Chạy bình thường, có lưu ảnh debug vào thư mục `debug\`:

```cmd
venv\Scripts\activate
python run_grading.py -a answers\ -i exams\
```

Chạy production, bỏ qua lưu ảnh debug để nhanh hơn và không sinh file `debug\*_aligned.jpg`, `debug\*_thresh.jpg`:

```cmd
venv\Scripts\activate
python run_grading.py -a answers\ -i exams\ --prod
```

Có thể chạy nhanh bằng file batch trên Windows:

```cmd
run_grading_windows.bat
```

## Tùy chọn dòng lệnh

| Tùy chọn | Mô tả | Mặc định |
|----------|-------|----------|
| `-a`, `--answers` | File đáp án hoặc thư mục đáp án | Bắt buộc nếu không dùng `-m` |
| `-i`, `--images` | Ảnh phiếu thi hoặc thư mục ảnh | Bắt buộc |
| `-o`, `--output` | File Excel output | `result/ketqua_YYYYMMDD_HHMMSS.xlsx` |
| `-n`, `--num-questions` | Số câu hỏi | 40 |
| `-p`, `--points` | Điểm mỗi câu | 0.25 |
| `--prod` | Không lưu ảnh debug aligned/thresh | Tắt |
| `-m`, `--manual` | Nhập đáp án thủ công từ terminal | Tắt |

## Phúc khảo một bài theo số báo danh

### macOS

```bash
source venv/bin/activate
python run_review.py 123456 -a answers/ -i exams/
```

### Windows

```cmd
venv\Scripts\activate
python run_review.py 123456 -a answers\ -i exams\
```

## Kết quả

File Excel trong thư mục `result/` gồm các sheet:

| Sheet | Nội dung |
|-------|----------|
| **Kết quả** | Điểm tổng quan của tất cả học sinh |
| **Chi tiết câu sai** | Liệt kê từng câu sai của mỗi học sinh |
| **Thống kê** | Điểm trung bình, cao nhất, thấp nhất, tỷ lệ đạt |

Nếu có phiếu lỗi, xem cột `status` và `error` trong file Excel.

## Xử lý lỗi thường gặp

| Lỗi | Cách sửa |
|-----|----------|
| `Python is not available` | Cài lại Python và tick **Add Python to PATH** trên Windows |
| `python: command not found` trên macOS | Dùng `python3` thay cho `python` |
| `pip install failed` | Kích hoạt venv rồi chạy lại `pip install -r requirements.txt` |
| `cv2 module not found` | Chạy `pip install -r requirements.txt` trong venv |
| Không xuất Excel | Kiểm tra thư mục `result/` và quyền ghi file |