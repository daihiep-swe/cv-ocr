#!/usr/bin/env python3
"""
Tạo ảnh test với các ô được tô NGẪU NHIÊN để kiểm tra chương trình
Mỗi lần chạy sẽ tạo số báo danh, mã đề và đáp án khác nhau
"""

import cv2
import numpy as np
import os
import random

# ==================== THAM SỐ TỪ debug_view.py ====================
# Vùng SỐ BÁO DANH (6 cột x 10 hàng = 60 ô)
SBD_X_START = 0.73
SBD_X_END = 0.85
SBD_Y_START = 0.09
SBD_Y_END = 0.285
SBD_NUM_COLS = 6

# Vùng MÃ ĐỀ (3 cột x 10 hàng = 30 ô)
EXAM_X_START = 0.88
EXAM_X_END = 0.94
EXAM_Y_START = 0.09
EXAM_Y_END = 0.285
EXAM_NUM_COLS = 3

# Vùng ĐÁP ÁN (4 cột x 10 câu x 4 lựa chọn = 160 ô)
ANSWER_Y_START = 0.365
ANSWER_Y_END = 0.523
ANSWER_COLUMNS = [
    (0.118, 0.265, 1),
    (0.331, 0.478, 11),
    (0.544, 0.691, 21),
    (0.757, 0.904, 31),
]
# ====================================================================


def generate_random_sbd():
    """Tạo số báo danh ngẫu nhiên 6 chữ số"""
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def generate_random_exam_code():
    """Tạo mã đề ngẫu nhiên 3 chữ số (001-009)"""
    return f"{random.randint(1, 9):03d}"


def generate_random_answers(num_questions=40):
    """Tạo đáp án ngẫu nhiên cho các câu hỏi"""
    choices = ["A", "B", "C", "D"]
    return {q: random.choice(choices) for q in range(1, num_questions + 1)}


def create_test_image(
    base_image_path: str,
    output_path: str,
    sbd: str = None,
    exam_code: str = None,
    answers: dict = None,
):
    """Tạo ảnh test với các ô được tô ngẫu nhiên

    Args:
        base_image_path: Đường dẫn ảnh gốc
        output_path: Đường dẫn lưu ảnh
        sbd: Số báo danh (nếu None sẽ tạo ngẫu nhiên)
        exam_code: Mã đề (nếu None sẽ tạo ngẫu nhiên)
        answers: Dict đáp án (nếu None sẽ tạo ngẫu nhiên)
    """

    # Tạo giá trị ngẫu nhiên nếu không được cung cấp
    if sbd is None:
        sbd = generate_random_sbd()
    if exam_code is None:
        exam_code = generate_random_exam_code()
    if answers is None:
        answers = generate_random_answers()

    # Đọc ảnh gốc
    image = cv2.imread(base_image_path)
    if image is None:
        print(f"Không thể đọc ảnh: {base_image_path}")
        return None

    height, width = image.shape[:2]
    print(f"Kích thước ảnh: {width} x {height}")

    # ========== TÔ SỐ BÁO DANH (60 ô) ==========
    sbd_x1 = int(SBD_X_START * width)
    sbd_x2 = int(SBD_X_END * width)
    sbd_y1 = int(SBD_Y_START * height)
    sbd_y2 = int(SBD_Y_END * height)

    col_width = (sbd_x2 - sbd_x1) / SBD_NUM_COLS
    row_height = (sbd_y2 - sbd_y1) / 10

    print(f"\n=== SỐ BÁO DANH: {sbd} ===")
    for col_idx, digit in enumerate(sbd):
        digit_val = int(digit)
        # Tính vị trí tâm ô cần tô
        center_x = int(sbd_x1 + col_idx * col_width + col_width * 0.5)
        center_y = int(sbd_y1 + digit_val * row_height + row_height * 0.5)
        radius = int(min(col_width, row_height) * 0.3)

        # Tô đen ô hình tròn
        cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)
        print(f"  Cột {col_idx + 1}: tô số {digit} tại ({center_x}, {center_y})")

    # ========== TÔ MÃ ĐỀ (30 ô) ==========
    exam_x1 = int(EXAM_X_START * width)
    exam_x2 = int(EXAM_X_END * width)
    exam_y1 = int(EXAM_Y_START * height)
    exam_y2 = int(EXAM_Y_END * height)

    col_width = (exam_x2 - exam_x1) / EXAM_NUM_COLS
    row_height = (exam_y2 - exam_y1) / 10

    print(f"\n=== MÃ ĐỀ: {exam_code} ===")
    for col_idx, digit in enumerate(exam_code):
        digit_val = int(digit)
        center_x = int(exam_x1 + col_idx * col_width + col_width * 0.5)
        center_y = int(exam_y1 + digit_val * row_height + row_height * 0.5)
        radius = int(min(col_width, row_height) * 0.3)

        cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)
        print(f"  Cột {col_idx + 1}: tô số {digit} tại ({center_x}, {center_y})")

    # ========== TÔ ĐÁP ÁN (160 ô) ==========
    answer_y1 = int(ANSWER_Y_START * height)
    answer_y2 = int(ANSWER_Y_END * height)
    row_height = (answer_y2 - answer_y1) / 10

    answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}

    # Offset điều chỉnh vị trí (pixel) - đảo ngược hướng
    OFFSET_A = -10  # Câu A lệch trái 10px
    OFFSET_D = 10  # Câu D lệch phải 10px

    print(f"\n=== ĐÁP ÁN ===")
    for col_x_start, col_x_end, start_q in ANSWER_COLUMNS:
        x1 = int(col_x_start * width)
        x2 = int(col_x_end * width)
        col_width = (x2 - x1) / 4  # 4 lựa chọn A B C D

        print(f"  Câu {start_q}-{start_q + 9}:")
        for q_offset in range(10):
            q_num = start_q + q_offset
            if q_num in answers:
                answer = answers[q_num]
                answer_idx = answer_map[answer]

                center_x = int(x1 + answer_idx * col_width + col_width * 0.5)

                # Điều chỉnh offset cho câu A và D
                if answer == "A":
                    center_x += OFFSET_A  # Lệch phải 1mm
                elif answer == "D":
                    center_x += OFFSET_D  # Lệch trái 1mm

                center_y = int(answer_y1 + q_offset * row_height + row_height * 0.5)
                radius = int(min(col_width, row_height) * 0.3)

                cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)
                print(f"    Câu {q_num}: {answer}")

    # Lưu ảnh
    cv2.imwrite(output_path, image)
    print(f"\n✓ Đã lưu: {output_path}")

    return output_path, sbd, exam_code, answers


def main():
    # Tìm ảnh gốc trong thư mục exams
    exams_dir = "exams"
    base_image = os.path.join("paper.jpg")

    if not os.path.exists(base_image):
        print(f"Không tìm thấy ảnh gốc: {base_image}")
        print("Lưu ý: Cần có file paper.jpg trong thư mục exams")
        return

    print(f"Sử dụng ảnh gốc: {base_image}")
    # tạo thư mục exams nếu chưa có
    # xoá thư mục exams nếu đã có
    if not os.path.exists(exams_dir):
        os.makedirs(exams_dir, exist_ok=True)
    else:
        for f in os.listdir(exams_dir):
            os.remove(os.path.join(exams_dir, f))
    # tạo thư mục exams nếu chưa có
    os.makedirs(exams_dir, exist_ok=True)

    # Tạo 50 ảnh test
    num_images = 50
    print(f"\n=== Tạo {num_images} ảnh test ===\n")
    
    for i in range(num_images):
        # Tạo giá trị ngẫu nhiên cho mỗi ảnh
        sbd = generate_random_sbd()
        exam_code = generate_random_exam_code()
        answers = generate_random_answers()

        # Tạo ảnh test với tên chứa mã đề và số báo danh
        output_path = os.path.join(exams_dir, f"{exam_code}_{sbd}.jpg")

        result = create_test_image(base_image, output_path, sbd, exam_code, answers)

        if result:
            print(f"[{i+1}/{num_images}] SBD: {sbd} | Mã đề: {exam_code}")
    
    print("\n" + "=" * 50)
    print(f"Hoàn thành! Đã tạo {num_images} ảnh test trong thư mục {exams_dir}/")
    print("=" * 50)
    print("\nChạy debug/debug_view.py để kiểm tra:")
    print(f"  python debug/debug_view.py exams")


if __name__ == "__main__":
    main()
