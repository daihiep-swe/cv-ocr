"""
Phiên bản command line - không cần GUI
Chạy trực tiếp từ terminal
"""

import argparse
import os
from typing import Dict, List, Tuple
from image_processor import ExamSheetProcessor
from grading_system import GradingSystem
from excel_exporter import ExcelExporter
from datetime import datetime
from multiprocessing import Pool, cpu_count
import sys


def is_valid_exam_code(exam_code: str) -> bool:
    """
    Kiểm tra mã đề có hợp lệ không (3 chữ số)

    Args:
        exam_code: Mã đề cần kiểm tra

    Returns:
        True nếu mã đề hợp lệ (3 chữ số), False nếu không
    """
    return len(exam_code) == 3 and exam_code.isdigit()


# Biến global để chia sẻ giữa các process
_all_answer_keys = {}
_num_questions = 40
_points_per_question = 0.25
_debug_enabled = True


def _init_worker(answer_keys, num_q, points, debug_enabled=True):
    """Khởi tạo worker với dữ liệu cần thiết"""
    global _all_answer_keys, _num_questions, _points_per_question, _debug_enabled
    _all_answer_keys = answer_keys
    _num_questions = num_q
    _points_per_question = points
    _debug_enabled = debug_enabled


def _error_result(
    image_path: str,
    error: str,
    student_id: str = "",
    exam_code: str = "",
) -> Dict:
    """Tạo kết quả lỗi để vẫn xuất được Excel/CSV."""
    return {
        "image_file": os.path.basename(image_path),
        "student_id": student_id,
        "exam_code": exam_code,
        "score": "",
        "correct_count": "",
        "incorrect_count": "",
        "total_questions": _num_questions,
        "max_score": _num_questions * _points_per_question,
        "percentage": "",
        "wrong_questions": [],
        "status": "error",
        "error": error,
    }


def _process_single_image(image_path: str) -> Dict:
    """
    Xử lý và chấm điểm một ảnh (chạy trong worker process)

    Returns:
        Dict kết quả, luôn có status/error nếu lỗi
    """
    global _all_answer_keys, _num_questions, _points_per_question

    try:
        processor = ExamSheetProcessor(_num_questions, debug=_debug_enabled)
        result = processor.process_exam_sheet(image_path)

        if not result:
            return _error_result(image_path, "Không đọc được phiếu")

        student_id, exam_code, student_answers = result

        # Kiểm tra mã đề
        if not is_valid_exam_code(exam_code):
            return _error_result(
                image_path,
                f"Invalid exam_code: {exam_code}",
                student_id=student_id,
                exam_code=exam_code,
            )

        # Tìm đáp án theo mã đề
        answer_key = _all_answer_keys.get(exam_code)
        if answer_key is None:
            return _error_result(
                image_path,
                f"Answer key not found for exam_code: {exam_code}",
                student_id=student_id,
                exam_code=exam_code,
            )

        # Chấm điểm
        grading_system = GradingSystem(answer_key, _points_per_question)
        graded_result = grading_system.get_detailed_results(
            student_id, student_answers
        )
        graded_result["exam_code"] = exam_code
        graded_result["image_file"] = os.path.basename(image_path)
        graded_result["status"] = "ok"
        graded_result["error"] = ""
        return graded_result
    except Exception as e:
        return _error_result(image_path, str(e))


def read_answer_key_from_text(file_path: str) -> Tuple[str, Dict]:
    """
    Đọc đáp án từ file text
    Mã đề được lấy từ tên file (ví dụ: 001.txt -> mã đề 001)
    Format đáp án: 1A, 2B, 3C, ... hoặc 1:A, 2:B, ...

    Returns:
        Tuple (mã_đề, dict_đáp_án)
    """
    import re

    answer_key = {}

    # Lấy mã đề từ tên file (ví dụ: 001.txt -> 001)
    file_name = os.path.basename(file_path)
    exam_code = os.path.splitext(file_name)[0].zfill(3)  # Đảm bảo 3 chữ số

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Format: 1A, 2B, 3C, ... hoặc 1:A, 2:B, ...
                match = re.match(r"(\d+)[:.\s]*([A-Da-d])$", line)
                if match:
                    q_num = int(match.group(1))
                    answer = match.group(2).upper()
                    answer_key[q_num] = answer

        return exam_code, answer_key

    except Exception as e:
        print(f"Lỗi khi đọc file đáp án: {e}")
        return "000", {}


def read_all_answer_keys(folder_path: str) -> Dict[str, Dict]:
    """
    Đọc tất cả file đáp án trong thư mục
    Mã đề được lấy từ tên file (ví dụ: 001.txt -> mã đề 001)

    Args:
        folder_path: Đường dẫn đến thư mục chứa các file đáp án

    Returns:
        Dict với key là mã đề, value là dict đáp án
    """
    all_answer_keys = {}

    if os.path.isfile(folder_path):
        # Nếu là file đơn lẻ
        exam_code, answer_key = read_answer_key_from_text(folder_path)
        if answer_key:
            if is_valid_exam_code(exam_code):
                all_answer_keys[exam_code] = answer_key
            else:
                print(f"   ⚠️  Mã đề {exam_code} không hợp lệ (cần 3 chữ số)")
    elif os.path.isdir(folder_path):
        # Nếu là thư mục, đọc tất cả file .txt
        for file in sorted(os.listdir(folder_path)):
            if file.endswith(".txt"):
                file_path = os.path.join(folder_path, file)
                exam_code, answer_key = read_answer_key_from_text(file_path)
                if answer_key:
                    if is_valid_exam_code(exam_code):
                        all_answer_keys[exam_code] = answer_key
                    else:
                        print(
                            f"   ⚠️  Mã đề {exam_code} từ {file} không hợp lệ (cần 3 chữ số)"
                        )

    # Hiển thị tổng kết
    if all_answer_keys:
        print(
            f"\n   📋 Tổng cộng: {len(all_answer_keys)} mã đề hợp lệ: {', '.join(sorted(all_answer_keys.keys()))}"
        )
    else:
        print(f"\n   ❌ Không có mã đề hợp lệ nào!")

    return all_answer_keys


def manual_input_answers(num_questions: int) -> Dict[int, str]:
    """Nhập đáp án thủ công từ terminal"""
    print("\n" + "=" * 50)
    print("NHẬP ĐÁP ÁN CHUẨN")
    print("=" * 50)
    print("Nhập đáp án cho từng câu (A/B/C/D)")
    print("Nhấn Enter để bỏ qua câu nào đó")
    print("-" * 50)

    answer_key = {}

    for i in range(1, num_questions + 1):
        while True:
            answer = input(f"Câu {i:2d}: ").strip().upper()

            if not answer:
                break

            if answer in ["A", "B", "C", "D"]:
                answer_key[i] = answer
                break
            else:
                print("   ⚠️  Vui lòng nhập A, B, C hoặc D")

    return answer_key


def display_answer_key(answer_key: Dict):
    """Hiển thị đáp án chuẩn"""
    print("\n" + "=" * 80)
    print("ĐÁP ÁN CHUẨN")
    print("=" * 80)

    # Sắp xếp và hiển thị đáp án
    sorted_keys = sorted(answer_key.keys())
    for i, q_num in enumerate(sorted_keys):
        print(f"{q_num}:{answer_key[q_num]}", end="  ")
        if (i + 1) % 10 == 0:
            print()

    if len(sorted_keys) % 10 != 0:
        print()

    print("=" * 80)


def process_and_grade(
    image_files: List[str],
    all_answer_keys: Dict[str, Dict],
    num_questions: int,
    points_per_question: float,
    debug_enabled: bool = True,
):
    """
    Xử lý và chấm điểm các phiếu thi (đa luồng)

    Args:
        image_files: Danh sách đường dẫn ảnh
        all_answer_keys: Dict chứa đáp án theo mã đề {mã_đề: {câu: đáp_án}}
        num_questions: Số câu hỏi
        points_per_question: Điểm mỗi câu
        debug_enabled: Có lưu ảnh debug aligned/thresh hay không
    """
    import time

    print("\n" + "=" * 50)
    print("BẮT ĐẦU CHẤM ĐIỂM")
    print("=" * 50)

    total = len(image_files)
    num_workers = min(cpu_count(), total, 8)  # Tối đa 8 workers

    print(f"📊 Sử dụng {num_workers} luồng để xử lý {total} phiếu")

    results = []
    completed = [0]  # Dùng list để có thể modify trong callback
    start_time = time.time()

    def update_progress(result):
        """Callback khi hoàn thành 1 task"""
        completed[0] += 1
        percent = int(completed[0] * 100 / total)
        bar_length = 30
        filled = int(bar_length * completed[0] / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(
            f"\r⏳ Đang chấm điểm: [{bar}] {percent}% ({completed[0]}/{total})",
            end="",
            flush=True,
        )

        if result is not None:
            results.append(result)

    # Sử dụng multiprocessing Pool
    with Pool(
        processes=num_workers,
        initializer=_init_worker,
        initargs=(all_answer_keys, num_questions, points_per_question, debug_enabled),
    ) as pool:
        # Submit tất cả tasks
        async_results = []
        for image_path in image_files:
            async_result = pool.apply_async(
                _process_single_image, args=(image_path,), callback=update_progress
            )
            async_results.append(async_result)

        # Đợi tất cả hoàn thành
        for ar in async_results:
            ar.wait()

    # Tính thời gian thực thi
    elapsed_time = time.time() - start_time

    # Xuống dòng sau khi hoàn thành
    bar = "█" * 30
    print(f"\r✅ Hoàn thành chấm điểm: [{bar}] 100% ({total}/{total})    ")

    error_count = sum(1 for result in results if result.get("status") == "error")
    if error_count > 0:
        print(f"   ⚠️  Có {error_count} phiếu lỗi, xem cột status/error trong file xuất")

    # Log thời gian
    if elapsed_time < 60:
        print(
            f"⏱️  Thời gian: {elapsed_time:.2f} giây ({total/elapsed_time:.1f} phiếu/giây)"
        )
    else:
        minutes = int(elapsed_time // 60)
        seconds = elapsed_time % 60
        print(
            f"⏱️  Thời gian: {minutes} phút {seconds:.1f} giây ({total/elapsed_time:.1f} phiếu/giây)"
        )

    return results


def display_results(results: List[Dict]):
    """Hiển thị kết quả chi tiết"""

    if not results:
        print("\n⚠️  Không có kết quả nào để hiển thị")
        return

def main():
    """Hàm main"""
    parser = argparse.ArgumentParser(
        description="Phần mềm chấm điểm trắc nghiệm tự động (Command Line)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python app.py -a answers.txt -i exam1.jpg exam2.jpg exam3.jpg
  python app.py -a answers/ -i exams/  # Đọc tất cả đáp án trong thư mục
  python app.py -m -i folder/*.jpg -o results.csv
        """,
    )

    parser.add_argument(
        "-a",
        "--answers",
        help="File đáp án hoặc thư mục chứa nhiều file đáp án. Dòng đầu file chứa: # Mã đề: XXX",
    )

    parser.add_argument(
        "-m", "--manual", action="store_true", help="Nhập đáp án thủ công từ terminal"
    )

    parser.add_argument(
        "-i",
        "--images",
        nargs="+",
        required=True,
        help="Đường dẫn đến ảnh phiếu thi hoặc thư mục chứa ảnh",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="File Excel output (mặc định: ketqua_YYYYMMDD_HHMMSS.xlsx)",
    )

    parser.add_argument(
        "-n", "--num-questions", type=int, default=40, help="Số câu hỏi (mặc định: 40)"
    )

    parser.add_argument(
        "-p", "--points", type=float, default=0.25, help="Điểm mỗi câu (mặc định: 0.25)"
    )

    parser.add_argument(
        "--prod",
        action="store_true",
        help="Chế độ production: không lưu ảnh debug aligned/thresh",
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "=" * 80)
    print(" " * 20 + "PHẦN MỀM CHẤM ĐIỂM TRẮC NGHIỆM")
    print("=" * 80)

    # 1. Đọc đáp án
    all_answer_keys = {}

    if args.manual:
        answer_key = manual_input_answers(args.num_questions)
        all_answer_keys["000"] = answer_key
    elif args.answers:
        print("\n📖 Đang đọc đáp án...")
        all_answer_keys = read_all_answer_keys(args.answers)
    else:
        print("\n⚠️  Bạn phải chọn một trong hai:")
        print("   • Dùng -a để chỉ định file/thư mục đáp án")
        print("   • Dùng -m để nhập đáp án thủ công")
        return

    if not all_answer_keys:
        print("\n❌ Không có đáp án. Thoát chương trình.")
        return

    # Hiển thị đáp án của mã đề đầu tiên (hoặc mã đề 000)
    display_code = (
        "000" if "000" in all_answer_keys else list(all_answer_keys.keys())[0]
    )

    # 2. Lấy danh sách file ảnh
    image_files = []
    for path in args.images:
        if os.path.isdir(path):
            # Nếu là thư mục, lấy tất cả ảnh trong đó
            for file in os.listdir(path):
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    image_files.append(os.path.join(path, file))
        elif os.path.isfile(path):
            image_files.append(path)

    if not image_files:
        print("\n❌ Không tìm thấy file ảnh nào. Thoát chương trình.")
        return

    print(f"\n✓ Tìm thấy {len(image_files)} ảnh phiếu thi")

    # 3. Xử lý và chấm điểm
    results = process_and_grade(
        image_files,
        all_answer_keys,
        args.num_questions,
        args.points,
        debug_enabled=not args.prod,
    )

    # 4. Hiển thị kết quả
    display_results(results)

    # 5. Hỏi người dùng có muốn xuất Excel không
    if results:
        print("\n" + "-" * 50)
        export_choice = (
            input("Bạn có muốn xuất kết quả ra file Excel không? (y/n): ").strip().lower()
        )

        if export_choice in ["y", "yes", "có", "co", ""]:
            # Tạo thư mục result nếu chưa có
            result_dir = "result"
            os.makedirs(result_dir, exist_ok=True)

            output_file = args.output or os.path.join(
                result_dir, f"ketqua_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

            # Đảm bảo file nằm trong thư mục result
            if not output_file.startswith(result_dir):
                output_file = os.path.join(result_dir, os.path.basename(output_file))

            exporter = ExcelExporter()
            if exporter.export_results(results, output_file, include_details=True):
                print(f"\n✓ Đã xuất kết quả ra file: {output_file}")
            else:
                print(f"\n✗ Không thể xuất file Excel")
        else:
            print("\n⏭️  Bỏ qua xuất file Excel")

    print("\n" + "=" * 80)
    print("HOÀN THÀNH!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
