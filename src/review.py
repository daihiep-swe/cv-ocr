#!/usr/bin/env python3
"""
Phúc khảo - Chấm điểm lại cho 1 học sinh theo số báo danh
Hiển thị chi tiết kết quả để kiểm tra
"""

import os
import sys
import argparse
from typing import Dict, Tuple
from image_processor import ExamSheetProcessor
from grading_system import GradingSystem


def read_answer_key(file_path: str) -> Dict[int, str]:
    """Đọc đáp án từ file text"""
    import re
    answer_key = {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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
        print(f"❌ Lỗi đọc file đáp án: {e}")
    
    return answer_key


def find_student_image(student_id: str, exams_dir: str = "exams") -> str:
    """
    Tìm file ảnh của học sinh theo số báo danh
    Format tên file: XXX_YYYYYY.jpg (mã đề_số báo danh)
    """
    if not os.path.isdir(exams_dir):
        return None
    
    for file in os.listdir(exams_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            # Kiểm tra số báo danh trong tên file
            base_name = os.path.splitext(file)[0]
            parts = base_name.split('_')
            if len(parts) >= 2 and parts[1] == student_id:
                return os.path.join(exams_dir, file)
    
    return None


def review_student(student_id: str, answers_dir: str = "answers", exams_dir: str = "exams"):
    """
    Phúc khảo bài thi của 1 học sinh
    
    Args:
        student_id: Số báo danh (6 chữ số)
        answers_dir: Thư mục chứa đáp án
        exams_dir: Thư mục chứa ảnh bài thi
    """
    print("\n" + "=" * 60)
    print("🔍 PHÚC KHẢO BÀI THI")
    print("=" * 60)
    print(f"📋 Số báo danh: {student_id}")
    
    # 1. Tìm file ảnh
    image_path = find_student_image(student_id, exams_dir)
    if not image_path:
        print(f"\n❌ Không tìm thấy bài thi của SBD: {student_id}")
        print(f"   Kiểm tra thư mục: {exams_dir}")
        print(f"   Format tên file: XXX_{student_id}.jpg")
        return None
    
    print(f"📄 File ảnh: {os.path.basename(image_path)}")
    
    # 2. Xử lý ảnh
    print("\n⏳ Đang xử lý ảnh...")
    processor = ExamSheetProcessor(num_questions=40)
    result = processor.process_exam_sheet(image_path)
    
    if not result:
        print("❌ Không thể đọc được phiếu thi!")
        return None
    
    detected_sbd, exam_code, student_answers = result
    
    print(f"\n📊 KẾT QUẢ NHẬN DIỆN:")
    print("-" * 40)
    print(f"   SBD phát hiện: {detected_sbd}")
    print(f"   Mã đề: {exam_code}")
    
    if detected_sbd != student_id:
        print(f"\n⚠️  CẢNH BÁO: SBD trong file ({student_id}) khác với SBD nhận diện ({detected_sbd})")
    
    # 3. Đọc đáp án
    answer_file = os.path.join(answers_dir, f"{exam_code}.txt")
    if not os.path.isfile(answer_file):
        print(f"\n❌ Không tìm thấy file đáp án cho mã đề: {exam_code}")
        print(f"   Cần file: {answer_file}")
        return None
    
    answer_key = read_answer_key(answer_file)
    if not answer_key:
        print(f"❌ File đáp án rỗng hoặc lỗi!")
        return None
    
    print(f"   Đáp án: {len(answer_key)} câu")
    
    # 4. Chấm điểm
    print("\n" + "=" * 60)
    print("📝 CHI TIẾT BÀI LÀM")
    print("=" * 60)
    
    correct_count = 0
    wrong_questions = []
    empty_questions = []
    
    # Header
    print(f"\n{'Câu':^5}│{'Đáp án':^8}│{'Bài làm':^8}│{'Kết quả':^10}")
    print("-" * 5 + "┼" + "-" * 8 + "┼" + "-" * 8 + "┼" + "-" * 10)
    
    for q in range(1, 41):
        correct_ans = answer_key.get(q, "-")
        student_ans = student_answers.get(q, "-")
        
        if student_ans == "-" or student_ans == "":
            status = "⬜ Bỏ trống"
            empty_questions.append(q)
        elif student_ans == correct_ans:
            status = "✅ Đúng"
            correct_count += 1
        else:
            status = "❌ Sai"
            wrong_questions.append((q, correct_ans, student_ans))
        
        # Hiển thị tất cả câu
        print(f"{q:^5}│{correct_ans:^8}│{student_ans:^8}│{status}")
    
    # 5. Tổng kết
    total = 40
    wrong_count = len(wrong_questions)
    empty_count = len(empty_questions)
    score = correct_count * 0.25
    
    print("\n" + "=" * 60)
    print("📊 TỔNG KẾT")
    print("=" * 60)
    print(f"   ✅ Số câu đúng:    {correct_count}/{total}")
    print(f"   ❌ Số câu sai:     {wrong_count}/{total}")
    print(f"   ⬜ Số câu bỏ trống: {empty_count}/{total}")
    print("-" * 40)
    print(f"   🏆 ĐIỂM SỐ:        {score:.2f}/10.00")
    print("=" * 60)
    
    # Hiển thị chi tiết câu sai
    if wrong_questions:
        print("\n📋 CHI TIẾT CÂU SAI:")
        print("-" * 40)
        for q, correct, student in wrong_questions:
            print(f"   Câu {q:2d}: Đáp án {correct}, chọn {student}")
    
    # Hiển thị câu bỏ trống
    if empty_questions:
        print(f"\n📋 CÂU BỎ TRỐNG: {', '.join(map(str, empty_questions))}")
    
    print("\n" + "=" * 60)
    
    return {
        "student_id": detected_sbd,
        "exam_code": exam_code,
        "correct": correct_count,
        "wrong": wrong_count,
        "empty": empty_count,
        "score": score,
        "answers": student_answers
    }


def main():
    parser = argparse.ArgumentParser(
        description="Phúc khảo bài thi - Chấm điểm chi tiết cho 1 học sinh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python review.py 123456
  python review.py 123456 -a answers/ -i exams/
  python review.py 123456 --show-all
        """
    )
    
    parser.add_argument(
        "student_id",
        help="Số báo danh của học sinh (6 chữ số)"
    )
    
    parser.add_argument(
        "-a", "--answers",
        default="answers",
        help="Thư mục chứa file đáp án (mặc định: answers/)"
    )
    
    parser.add_argument(
        "-i", "--images",
        default="exams",
        help="Thư mục chứa ảnh bài thi (mặc định: exams/)"
    )
    
    args = parser.parse_args()
    
    # Validate số báo danh
    if not args.student_id.isdigit() or len(args.student_id) != 6:
        print("❌ Số báo danh phải là 6 chữ số!")
        print(f"   Bạn nhập: {args.student_id}")
        sys.exit(1)
    
    # Phúc khảo
    result = review_student(
        args.student_id,
        args.answers,
        args.images
    )
    
    if result:
        print("\n✅ Phúc khảo hoàn tất!")
    else:
        print("\n❌ Phúc khảo thất bại!")
        sys.exit(1)


if __name__ == "__main__":
    main()
