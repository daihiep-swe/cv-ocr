"""
Module xuất kết quả ra file Excel
"""

import pandas as pd
from typing import List, Dict
from datetime import datetime


class ExcelExporter:
    """Xuất kết quả chấm điểm ra file Excel"""

    def __init__(self):
        """Khởi tạo exporter"""
        pass

    def export_results(
        self, results: List[Dict], output_path: str, include_details: bool = False
    ) -> bool:
        """
        Xuất kết quả ra file Excel

        Args:
            results: List các dict kết quả chấm điểm
            output_path: Đường dẫn file Excel output
            include_details: Có xuất chi tiết câu sai không

        Returns:
            True nếu thành công, False nếu có lỗi
        """
        try:
            # Tạo DataFrame chính với thông tin tổng quan
            main_data = []
            for result in results:
                main_data.append(
                    {
                        "Số báo danh": result["student_id"],
                        "Mã đề": result.get("exam_code", "000"),
                        "Điểm": result["score"],
                        "Số câu đúng": result["correct_count"],
                        "Số câu sai": result["incorrect_count"],
                        "Tổng số câu": result["total_questions"],
                        "Điểm tối đa": result["max_score"],
                        "Phần trăm (%)": round(result["percentage"], 2),
                    }
                )

            df_main = pd.DataFrame(main_data)

            # Tạo Excel writer
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Sheet 1: Kết quả tổng quan
                df_main.to_excel(writer, sheet_name="Kết quả", index=False)

                # Sheet 2: Chi tiết câu sai (nếu yêu cầu)
                if include_details:
                    detail_data = []
                    for result in results:
                        for wrong_q in result["wrong_questions"]:
                            detail_data.append(
                                {
                                    "Số báo danh": result["student_id"],
                                    "Mã đề": result.get("exam_code", "000"),
                                    "Câu hỏi": wrong_q["question"],
                                    "Đáp án đúng": wrong_q["correct_answer"],
                                    "Đáp án của sinh viên": wrong_q["student_answer"],
                                }
                            )

                    if detail_data:
                        df_detail = pd.DataFrame(detail_data)
                        df_detail.to_excel(
                            writer, sheet_name="Chi tiết câu sai", index=False
                        )

                # Sheet 3: Thống kê (nếu có nhiều hơn 1 bài thi)
                if len(results) > 1:
                    from grading_system import GradingSystem

                    # Tạo một instance tạm để tính thống kê
                    # (Trong thực tế, thống kê nên được truyền vào từ ngoài)
                    scores = [r["score"] for r in results]
                    max_score = results[0]["max_score"] if results else 10

                    stats_data = {
                        "Chỉ số": [
                            "Tổng số sinh viên",
                            "Điểm trung bình",
                            "Điểm cao nhất",
                            "Điểm thấp nhất",
                            "Số sinh viên đạt (>= 5)",
                            "Tỷ lệ đạt (%)",
                        ],
                        "Giá trị": [
                            len(results),
                            round(sum(scores) / len(scores), 2) if scores else 0,
                            max(scores) if scores else 0,
                            min(scores) if scores else 0,
                            sum(1 for s in scores if s >= max_score * 0.5),
                            (
                                round(
                                    sum(1 for s in scores if s >= max_score * 0.5)
                                    / len(scores)
                                    * 100,
                                    2,
                                )
                                if scores
                                else 0
                            ),
                        ],
                    }

                    df_stats = pd.DataFrame(stats_data)
                    df_stats.to_excel(writer, sheet_name="Thống kê", index=False)

            print(f"Đã xuất kết quả ra file: {output_path}")
            return True

        except Exception as e:
            print(f"Lỗi khi xuất file Excel: {e}")
            return False

    def export_answer_key(self, answer_key: Dict[int, str], output_path: str) -> bool:
        """
        Xuất đáp án chuẩn ra file Excel

        Args:
            answer_key: Dict đáp án chuẩn
            output_path: Đường dẫn file Excel output

        Returns:
            True nếu thành công, False nếu có lỗi
        """
        try:
            data = []
            for question_num in sorted(answer_key.keys()):
                data.append(
                    {"Câu hỏi": question_num, "Đáp án": answer_key[question_num]}
                )

            df = pd.DataFrame(data)
            df.to_excel(output_path, sheet_name="Đáp án chuẩn", index=False)

            print(f"Đã xuất đáp án chuẩn ra file: {output_path}")
            return True

        except Exception as e:
            print(f"Lỗi khi xuất đáp án: {e}")
            return False

    @staticmethod
    def read_answer_key_from_excel(file_path: str) -> Dict[int, str]:
        """
        Đọc đáp án chuẩn từ file Excel

        Args:
            file_path: Đường dẫn đến file Excel chứa đáp án

        Returns:
            Dict đáp án {câu_hỏi: đáp_án}
        """
        try:
            df = pd.read_excel(file_path)
            answer_key = {}

            # Giả sử file có 2 cột: 'Câu hỏi' và 'Đáp án'
            for _, row in df.iterrows():
                question_num = int(row["Câu hỏi"])
                answer = str(row["Đáp án"]).strip().upper()
                answer_key[question_num] = answer

            return answer_key

        except Exception as e:
            print(f"Lỗi khi đọc đáp án từ Excel: {e}")
            return {}
