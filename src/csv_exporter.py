"""
Module xuất kết quả ra file CSV
"""

import csv
from typing import List, Dict


class CSVExporter:
    """Xuất kết quả chấm điểm ra file CSV"""

    def __init__(self):
        """Khởi tạo exporter"""
        pass

    def export_results(
        self, results: List[Dict], output_path: str, include_details: bool = False
    ) -> bool:
        """
        Xuất kết quả ra file CSV

        Args:
            results: List các dict kết quả chấm điểm
            output_path: Đường dẫn file CSV output
            include_details: Có xuất chi tiết câu sai không (sẽ tạo file riêng)

        Returns:
            True nếu thành công, False nếu có lỗi
        """
        try:
            # Đảm bảo đuôi file là .csv
            if not output_path.endswith('.csv'):
                output_path = output_path.rsplit('.', 1)[0] + '.csv'

            # Sắp xếp kết quả theo số báo danh
            sorted_results = sorted(results, key=lambda x: x["student_id"])

            # Xuất file kết quả chính
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [
                    "Số báo danh",
                    "Mã đề",
                    "Điểm",
                    "Số câu đúng",
                    "Số câu sai",
                    "Tổng số câu",
                    "Điểm tối đa",
                    "Phần trăm (%)",
                    "Tên file ảnh",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in sorted_results:
                    writer.writerow({
                        "Số báo danh": result["student_id"],
                        "Mã đề": result.get("exam_code", "000"),
                        "Điểm": result["score"],
                        "Số câu đúng": result["correct_count"],
                        "Số câu sai": result["incorrect_count"],
                        "Tổng số câu": result["total_questions"],
                        "Điểm tối đa": result["max_score"],
                        "Phần trăm (%)": round(result["percentage"], 2),
                        "Tên file ảnh": result.get("image_file", ""),
                    })

            # Xuất file chi tiết câu sai (nếu yêu cầu)
            if include_details:
                detail_path = output_path.rsplit('.', 1)[0] + '_chi_tiet.csv'
                detail_data = []
                for result in sorted_results:
                    for wrong_q in result["wrong_questions"]:
                        detail_data.append({
                            "Số báo danh": result["student_id"],
                            "Mã đề": result.get("exam_code", "000"),
                            "Câu hỏi": wrong_q["question"],
                            "Đáp án đúng": wrong_q["correct_answer"],
                            "Đáp án của sinh viên": wrong_q["student_answer"],
                        })

                if detail_data:
                    with open(detail_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                        fieldnames = [
                            "Số báo danh",
                            "Mã đề",
                            "Câu hỏi",
                            "Đáp án đúng",
                            "Đáp án của sinh viên",
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(detail_data)
                    print(f"Đã xuất chi tiết câu sai ra file: {detail_path}")

            # Xuất file thống kê (nếu có nhiều hơn 1 bài thi)
            if len(results) > 1:
                stats_path = output_path.rsplit('.', 1)[0] + '_thong_ke.csv'
                scores = [r["score"] for r in results]
                max_score = results[0]["max_score"] if results else 10

                with open(stats_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ["Chỉ số", "Giá trị"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    stats_data = [
                        {"Chỉ số": "Tổng số sinh viên", "Giá trị": len(results)},
                        {"Chỉ số": "Điểm trung bình", "Giá trị": round(sum(scores) / len(scores), 2) if scores else 0},
                        {"Chỉ số": "Điểm cao nhất", "Giá trị": max(scores) if scores else 0},
                        {"Chỉ số": "Điểm thấp nhất", "Giá trị": min(scores) if scores else 0},
                        {"Chỉ số": "Số sinh viên đạt (>= 5)", "Giá trị": sum(1 for s in scores if s >= max_score * 0.5)},
                        {"Chỉ số": "Tỷ lệ đạt (%)", "Giá trị": round(sum(1 for s in scores if s >= max_score * 0.5) / len(scores) * 100, 2) if scores else 0},
                    ]
                    writer.writerows(stats_data)
                print(f"Đã xuất thống kê ra file: {stats_path}")

            print(f"Đã xuất kết quả ra file: {output_path}")
            return True

        except Exception as e:
            print(f"Lỗi khi xuất file CSV: {e}")
            return False

    def export_answer_key(self, answer_key: Dict[int, str], output_path: str) -> bool:
        """
        Xuất đáp án chuẩn ra file CSV

        Args:
            answer_key: Dict đáp án chuẩn
            output_path: Đường dẫn file CSV output

        Returns:
            True nếu thành công, False nếu có lỗi
        """
        try:
            # Đảm bảo đuôi file là .csv
            if not output_path.endswith('.csv'):
                output_path = output_path.rsplit('.', 1)[0] + '.csv'

            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ["Câu hỏi", "Đáp án"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for question_num in sorted(answer_key.keys()):
                    writer.writerow({
                        "Câu hỏi": question_num,
                        "Đáp án": answer_key[question_num]
                    })

            print(f"Đã xuất đáp án chuẩn ra file: {output_path}")
            return True

        except Exception as e:
            print(f"Lỗi khi xuất đáp án: {e}")
            return False

    @staticmethod
    def read_answer_key_from_csv(file_path: str) -> Dict[int, str]:
        """
        Đọc đáp án chuẩn từ file CSV

        Args:
            file_path: Đường dẫn đến file CSV chứa đáp án

        Returns:
            Dict đáp án {câu_hỏi: đáp_án}
        """
        try:
            answer_key = {}

            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    question_num = int(row["Câu hỏi"])
                    answer = str(row["Đáp án"]).strip().upper()
                    answer_key[question_num] = answer

            return answer_key

        except Exception as e:
            print(f"Lỗi khi đọc đáp án từ CSV: {e}")
            return {}


# Alias để tương thích ngược
ExcelExporter = CSVExporter
