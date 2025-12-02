#!/usr/bin/env python3
"""
Tạo ảnh test dựa trên đáp án thực tế với phân bố điểm theo chuẩn quốc tế
Phân bố Normal Distribution (Bell Curve):
- ~2.5% điểm xuất sắc (90-100%)
- ~13.5% điểm giỏi (80-90%)
- ~34% điểm khá (65-80%)
- ~34% điểm trung bình (50-65%)
- ~13.5% điểm yếu (35-50%)
- ~2.5% điểm kém (<35%)
"""

import cv2
import numpy as np
import os
import sys
import random
from multiprocessing import Pool, cpu_count
import time

# Thêm thư mục gốc vào path để import được các module khác
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def read_answer_key(file_path: str) -> dict:
    """Đọc đáp án từ file text"""
    answer_key = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            import re
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"(\d+)[:.\s]*([A-Da-d])$", line)
                if match:
                    q_num = int(match.group(1))
                    answer = match.group(2).upper()
                    answer_key[q_num] = answer
    except Exception as e:
        print(f"Lỗi đọc file đáp án: {e}")
    return answer_key


def load_all_answer_keys(answers_dir: str) -> dict:
    """Đọc tất cả file đáp án trong thư mục"""
    all_keys = {}
    if os.path.isdir(answers_dir):
        for file in sorted(os.listdir(answers_dir)):
            if file.endswith('.txt'):
                exam_code = os.path.splitext(file)[0].zfill(3)
                file_path = os.path.join(answers_dir, file)
                answer_key = read_answer_key(file_path)
                if answer_key:
                    all_keys[exam_code] = answer_key
                    print(f"   ✓ Đã đọc đáp án mã đề {exam_code}")
    return all_keys


def generate_score_by_distribution() -> float:
    """
    Sinh điểm theo phân bố chuẩn quốc tế (Normal Distribution)
    Mean = 65%, Standard Deviation = 15%
    """
    # Phân bố chuẩn với mean=65, std=15
    score = np.random.normal(65, 15)
    # Giới hạn trong khoảng 10-100%
    score = max(10, min(100, score))
    return score / 100  # Trả về tỷ lệ 0.0-1.0


def generate_student_answers(answer_key: dict, target_correct_ratio: float) -> dict:
    """
    Tạo đáp án của sinh viên dựa trên đáp án chuẩn và tỷ lệ đúng mong muốn
    
    Args:
        answer_key: Dict đáp án chuẩn {câu: đáp_án}
        target_correct_ratio: Tỷ lệ trả lời đúng (0.0 - 1.0)
    
    Returns:
        Dict đáp án của sinh viên
    """
    num_questions = len(answer_key)
    num_correct = int(num_questions * target_correct_ratio)
    
    # Chọn ngẫu nhiên các câu sẽ trả lời đúng
    questions = list(answer_key.keys())
    correct_questions = set(random.sample(questions, num_correct))
    
    student_answers = {}
    choices = ["A", "B", "C", "D"]
    
    for q_num, correct_answer in answer_key.items():
        if q_num in correct_questions:
            # Trả lời đúng
            student_answers[q_num] = correct_answer
        else:
            # Trả lời sai - chọn đáp án khác
            wrong_choices = [c for c in choices if c != correct_answer]
            student_answers[q_num] = random.choice(wrong_choices)
    
    return student_answers


def generate_random_sbd():
    """Tạo số báo danh ngẫu nhiên 6 chữ số"""
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def create_test_image(
    base_image_path: str,
    output_path: str,
    sbd: str,
    exam_code: str,
    answers: dict,
    verbose: bool = False,
):
    """Tạo ảnh test với các ô được tô

    Args:
        base_image_path: Đường dẫn ảnh gốc
        output_path: Đường dẫn lưu ảnh
        sbd: Số báo danh
        exam_code: Mã đề
        answers: Dict đáp án của sinh viên
        verbose: In chi tiết hay không
    """
    # Đọc ảnh gốc
    image = cv2.imread(base_image_path)
    if image is None:
        print(f"Không thể đọc ảnh: {base_image_path}")
        return None

    height, width = image.shape[:2]

    # ========== TÔ SỐ BÁO DANH ==========
    sbd_x1 = int(SBD_X_START * width)
    sbd_x2 = int(SBD_X_END * width)
    sbd_y1 = int(SBD_Y_START * height)
    sbd_y2 = int(SBD_Y_END * height)

    col_width = (sbd_x2 - sbd_x1) / SBD_NUM_COLS
    row_height = (sbd_y2 - sbd_y1) / 10

    for col_idx, digit in enumerate(sbd):
        digit_val = int(digit)
        center_x = int(sbd_x1 + col_idx * col_width + col_width * 0.5)
        center_y = int(sbd_y1 + digit_val * row_height + row_height * 0.5)
        radius = int(min(col_width, row_height) * 0.3)
        cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)

    # ========== TÔ MÃ ĐỀ ==========
    exam_x1 = int(EXAM_X_START * width)
    exam_x2 = int(EXAM_X_END * width)
    exam_y1 = int(EXAM_Y_START * height)
    exam_y2 = int(EXAM_Y_END * height)

    col_width = (exam_x2 - exam_x1) / EXAM_NUM_COLS
    row_height = (exam_y2 - exam_y1) / 10

    for col_idx, digit in enumerate(exam_code):
        digit_val = int(digit)
        center_x = int(exam_x1 + col_idx * col_width + col_width * 0.5)
        center_y = int(exam_y1 + digit_val * row_height + row_height * 0.5)
        radius = int(min(col_width, row_height) * 0.3)
        cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)

    # ========== TÔ ĐÁP ÁN ==========
    answer_y1 = int(ANSWER_Y_START * height)
    answer_y2 = int(ANSWER_Y_END * height)
    row_height = (answer_y2 - answer_y1) / 10

    answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    OFFSET_A = -10
    OFFSET_D = 10

    for col_x_start, col_x_end, start_q in ANSWER_COLUMNS:
        x1 = int(col_x_start * width)
        x2 = int(col_x_end * width)
        col_width = (x2 - x1) / 4

        for q_offset in range(10):
            q_num = start_q + q_offset
            if q_num in answers:
                answer = answers[q_num]
                answer_idx = answer_map[answer]

                center_x = int(x1 + answer_idx * col_width + col_width * 0.5)
                if answer == "A":
                    center_x += OFFSET_A
                elif answer == "D":
                    center_x += OFFSET_D

                center_y = int(answer_y1 + q_offset * row_height + row_height * 0.5)
                radius = int(min(col_width, row_height) * 0.3)
                cv2.circle(image, (center_x, center_y), radius, (0, 0, 0), -1)

    # Resize ảnh để giảm dung lượng (giữ tỷ lệ)
    scale = 0.5  # Giảm 50% kích thước
    new_width = int(width * scale)
    new_height = int(height * scale)
    image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    # Lưu ảnh với compression (quality 70%)
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
    cv2.imwrite(output_path, image, encode_params)
    
    if verbose:
        print(f"✓ Đã lưu: {output_path}")

    return output_path, sbd, exam_code, answers


# Biến global để chia sẻ giữa các process
_base_image_path = ""
_exams_dir = ""
_all_answer_keys = {}


def _init_worker(base_image, exams_dir, answer_keys):
    """Khởi tạo worker với dữ liệu cần thiết"""
    global _base_image_path, _exams_dir, _all_answer_keys
    _base_image_path = base_image
    _exams_dir = exams_dir
    _all_answer_keys = answer_keys


def _create_single_image(args):
    """
    Tạo một ảnh test (chạy trong worker process)
    
    Args:
        args: Tuple (exam_code, index)
    
    Returns:
        Tuple (score, success)
    """
    global _base_image_path, _exams_dir, _all_answer_keys
    
    exam_code, idx = args
    
    try:
        answer_key = _all_answer_keys[exam_code]
        
        # Sinh điểm theo phân bố chuẩn
        target_ratio = generate_score_by_distribution()
        score = target_ratio * 100
        
        # Tạo đáp án sinh viên
        sbd = generate_random_sbd()
        student_answers = generate_student_answers(answer_key, target_ratio)
        
        # Tạo ảnh
        output_path = os.path.join(_exams_dir, f"{exam_code}_{sbd}.jpg")
        create_test_image(_base_image_path, output_path, sbd, exam_code, student_answers)
        
        return (score, True)
    except Exception as e:
        return (0, False)


def main():
    # Thư mục gốc của project
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Đường dẫn
    exams_dir = os.path.join(project_root, "exams")
    answers_dir = os.path.join(project_root, "answers")
    base_image = os.path.join(project_root, "paper.jpg")

    if not os.path.exists(base_image):
        print(f"❌ Không tìm thấy ảnh gốc: {base_image}")
        print("   Lưu ý: Cần có file paper.jpg trong thư mục gốc project")
        return

    print("=" * 60)
    print("TẠO PHIẾU THI VỚI PHÂN BỐ ĐIỂM CHUẨN QUỐC TẾ")
    print("=" * 60)
    
    # Đọc tất cả đáp án
    print("\n📖 Đang đọc đáp án...")
    all_answer_keys = load_all_answer_keys(answers_dir)
    
    if not all_answer_keys:
        print("❌ Không tìm thấy file đáp án trong thư mục answers/")
        return
    
    exam_codes = list(all_answer_keys.keys())
    print(f"\n✓ Đã đọc {len(all_answer_keys)} mã đề: {', '.join(exam_codes)}")

    # Xóa và tạo lại thư mục exams
    if os.path.exists(exams_dir):
        for f in os.listdir(exams_dir):
            os.remove(os.path.join(exams_dir, f))
    os.makedirs(exams_dir, exist_ok=True)

    # Số lượng phiếu mỗi mã đề
    num_per_code = 400
    total_images = len(exam_codes) * num_per_code
    num_workers = min(cpu_count(), 8)  # Tối đa 8 workers
    
    print(f"\n📝 Tạo {num_per_code} phiếu/mã đề x {len(exam_codes)} mã đề = {total_images} phiếu")
    print(f"🚀 Sử dụng {num_workers} luồng")
    print("\n📊 Phân bố điểm chuẩn (Normal Distribution):")
    print("   • Mean = 65%, Std = 15%")
    print("   • ~2.5% xuất sắc (90-100%)")
    print("   • ~13.5% giỏi (80-90%)")
    print("   • ~34% khá (65-80%)")
    print("   • ~34% trung bình (50-65%)")
    print("   • ~13.5% yếu (35-50%)")
    print("   • ~2.5% kém (<35%)")
    
    start_time = time.time()
    scores = []
    completed = [0]
    
    # Tạo danh sách tasks
    tasks = []
    for exam_code in exam_codes:
        for i in range(num_per_code):
            tasks.append((exam_code, i))
    
    def update_progress(result):
        """Callback khi hoàn thành 1 task"""
        completed[0] += 1
        percent = int(completed[0] * 100 / total_images)
        bar_length = 30
        filled = int(bar_length * completed[0] / total_images)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r⏳ Đang tạo: [{bar}] {percent}% ({completed[0]}/{total_images})", end="", flush=True)
        
        score, success = result
        if success:
            scores.append(score)
    
    # Sử dụng multiprocessing Pool
    with Pool(
        processes=num_workers,
        initializer=_init_worker,
        initargs=(base_image, exams_dir, all_answer_keys)
    ) as pool:
        # Submit tất cả tasks
        async_results = []
        for task in tasks:
            async_result = pool.apply_async(
                _create_single_image,
                args=(task,),
                callback=update_progress
            )
            async_results.append(async_result)
        
        # Đợi tất cả hoàn thành
        for ar in async_results:
            ar.wait()
    
    elapsed_time = time.time() - start_time
    
    # Thống kê
    bar = "█" * 30
    print(f"\r✅ Hoàn thành: [{bar}] 100% ({total_images}/{total_images})    ")
    print(f"\n⏱️  Thời gian: {elapsed_time:.1f} giây ({total_images/elapsed_time:.1f} phiếu/giây)")
    
    print("\n" + "=" * 60)
    print("THỐNG KÊ PHÂN BỐ ĐIỂM")
    print("=" * 60)
    
    scores = np.array(scores)
    print(f"📊 Điểm trung bình: {np.mean(scores):.1f}%")
    print(f"📊 Độ lệch chuẩn:   {np.std(scores):.1f}%")
    print(f"📊 Điểm cao nhất:   {np.max(scores):.1f}%")
    print(f"📊 Điểm thấp nhất:  {np.min(scores):.1f}%")
    
    # Phân loại
    excellent = np.sum(scores >= 90)
    good = np.sum((scores >= 80) & (scores < 90))
    fair = np.sum((scores >= 65) & (scores < 80))
    average = np.sum((scores >= 50) & (scores < 65))
    weak = np.sum((scores >= 35) & (scores < 50))
    poor = np.sum(scores < 35)
    
    print(f"\n📈 Phân loại:")
    print(f"   • Xuất sắc (≥90%): {excellent} ({excellent/total_images*100:.1f}%)")
    print(f"   • Giỏi (80-90%):   {good} ({good/total_images*100:.1f}%)")
    print(f"   • Khá (65-80%):    {fair} ({fair/total_images*100:.1f}%)")
    print(f"   • TB (50-65%):     {average} ({average/total_images*100:.1f}%)")
    print(f"   • Yếu (35-50%):    {weak} ({weak/total_images*100:.1f}%)")
    print(f"   • Kém (<35%):      {poor} ({poor/total_images*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print(f"✅ Đã tạo {total_images} phiếu trong thư mục exams/")
    print("=" * 60)


if __name__ == "__main__":
    main()
