#!/bin/bash
# Exam Grading System - Main Script
# Chạy chương trình chấm điểm trắc nghiệm tự động

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Lấy thư mục script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Exam Grading System${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 không được cài đặt!${NC}"
    echo "Vui lòng cài đặt Python 3.7 trở lên"
    exit 1
fi

# Kiểm tra version Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "✓ Python version: ${GREEN}$PYTHON_VERSION${NC}"

# Kiểm tra thư mục src
if [ ! -d "src" ]; then
    echo -e "${RED}❌ Không tìm thấy thư mục src/${NC}"
    exit 1
fi

# Kiểm tra file app.py
if [ ! -f "src/app.py" ]; then
    echo -e "${RED}❌ Không tìm thấy src/app.py${NC}"
    exit 1
fi

# Kiểm tra requirements
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}⚠️  Kiểm tra dependencies...${NC}"
    python3 -c "import cv2, numpy, yaml" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Một số thư viện chưa được cài đặt${NC}"
        echo "Chạy: pip3 install -r requirements.txt"
        read -p "Bạn có muốn cài đặt ngay không? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip3 install -r requirements.txt
        fi
    fi
fi

# Tạo thư mục cần thiết
mkdir -p result logs

# Chạy chương trình với tất cả arguments
echo -e "${GREEN}🚀 Khởi động chương trình chấm điểm...${NC}"
echo ""

python3 run_grading.py "$@"

# Kiểm tra exit code
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Hoàn thành thành công!${NC}"
else
    echo -e "${RED}❌ Có lỗi xảy ra (Exit code: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE
