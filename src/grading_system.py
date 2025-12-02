"""
Module chấm điểm tự động
So sánh đáp án thí sinh với đáp án chuẩn và tính điểm
"""

from typing import Dict, List, Tuple


class GradingSystem:
    """Hệ thống chấm điểm tự động"""

    def __init__(self, answer_key: Dict[int, str], points_per_question: float = 0.25):
        """
        Khởi tạo hệ thống chấm điểm

        Args:
            answer_key: Đáp án chuẩn {câu_hỏi: đáp_án}
            points_per_question: Số điểm cho mỗi câu đúng
        """
        self.answer_key = answer_key
        self.points_per_question = points_per_question
        self.total_questions = len(answer_key)
        self.max_score = self.total_questions * points_per_question

    def grade_exam(self, student_answers: Dict[int, str]) -> Tuple[float, int, int]:
        """
        Chấm điểm một bài thi

        Args:
            student_answers: Đáp án của thí sinh {câu_hỏi: đáp_án}

        Returns:
            Tuple (điểm, số câu đúng, số câu sai)
        """
        correct_count = 0
        incorrect_count = 0

        for question_num, correct_answer in self.answer_key.items():
            student_answer = student_answers.get(question_num, None)

            if student_answer is None:
                # Không trả lời -> tính là sai
                incorrect_count += 1
            elif student_answer.upper() == correct_answer.upper():
                correct_count += 1
            else:
                incorrect_count += 1

        score = correct_count * self.points_per_question

        return score, correct_count, incorrect_count

    def get_detailed_results(
        self, student_id: str, student_answers: Dict[int, str]
    ) -> Dict:
        """
        Lấy kết quả chi tiết của một bài thi

        Args:
            student_id: Số báo danh
            student_answers: Đáp án của thí sinh

        Returns:
            Dict chứa thông tin chi tiết
        """
        score, correct, incorrect = self.grade_exam(student_answers)

        # Tìm các câu sai
        wrong_questions = []
        for question_num, correct_answer in self.answer_key.items():
            student_answer = student_answers.get(question_num, None)
            if (
                student_answer is None
                or student_answer.upper() != correct_answer.upper()
            ):
                wrong_questions.append(
                    {
                        "question": question_num,
                        "correct_answer": correct_answer,
                        "student_answer": student_answer or "Không trả lời",
                    }
                )

        return {
            "student_id": student_id,
            "score": score,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "total_questions": self.total_questions,
            "max_score": self.max_score,
            "percentage": (score / self.max_score * 100) if self.max_score > 0 else 0,
            "wrong_questions": wrong_questions,
        }

    def grade_multiple_exams(
        self, exams: List[Tuple[str, Dict[int, str]]]
    ) -> List[Dict]:
        """
        Chấm điểm nhiều bài thi

        Args:
            exams: List các tuple (student_id, student_answers)

        Returns:
            List các dict kết quả
        """
        results = []

        for student_id, student_answers in exams:
            result = self.get_detailed_results(student_id, student_answers)
            results.append(result)

        return results

    def get_statistics(self, results: List[Dict]) -> Dict:
        """
        Tính thống kê tổng quan

        Args:
            results: List các kết quả đã chấm

        Returns:
            Dict chứa thống kê
        """
        if not results:
            return {
                "total_students": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "pass_rate": 0,
            }

        scores = [r["score"] for r in results]
        pass_threshold = self.max_score * 0.5  # Điểm đạt = 50% tổng điểm
        passed_count = sum(1 for score in scores if score >= pass_threshold)

        return {
            "total_students": len(results),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "pass_rate": (passed_count / len(results) * 100) if results else 0,
            "pass_threshold": pass_threshold,
        }
