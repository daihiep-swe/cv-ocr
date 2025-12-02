#!/bin/bash
# Exam Review System - Review Script
# Phúc khảo chi tiết bài thi của học sinh

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Lấy thư mục script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Exam Review System${NC}"
echo -e "${BLUE}========================================${NC}"
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

# Kiểm tra file review.py
if [ ! -f "src/review.py" ]; then
    echo -e "${RED}❌ Không tìm thấy src/review.py${NC}"
    exit 1
fi

# Kiểm tra argument
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Cách sử dụng:${NC}"
    echo "  ./run_review.sh <SỐ_BÁO_DANH> [options]"
    echo ""
    echo -e "${YELLOW}Ví dụ:${NC}"
    echo "  ./run_review.sh 123456"
    echo "  ./run_review.sh 123456 -a answers/ -i exams/"
    echo ""
    exit 1
fi

# Kiểm tra dependencies
python3 -c "import cv2, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Một số thư viện chưa được cài đặt${NC}"
    echo "Chạy: pip3 install -r requirements.txt"
fi

# Chạy chương trình với tất cả arguments
echo -e "${GREEN}🔍 Bắt đầu phúc khảo bài thi...${NC}"
echo ""

python3 run_review.py "$@"

# Kiểm tra exit code
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Phúc khảo hoàn tất!${NC}"
else
    echo -e "${RED}❌ Có lỗi xảy ra (Exit code: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE
