#!/bin/bash

cd "$(dirname "$0")"

# tạo thư mục result nếu chưa có
mkdir -p result

# Xoá các file trong thư mục result
rm -f result/*

# Tạo venv nếu chưa có
if [ ! -d "venv" ]; then
    echo "Đang tạo môi trường ảo..."
    python3 -m venv venv
fi

# Kích hoạt venv
source venv/bin/activate

# Cài đặt dependencies nếu cần
pip install -q -r requirements.txt

# Chạy chấm điểm (đọc tất cả file đáp án trong thư mục answers)
python app.py -a answers/ -i exams/