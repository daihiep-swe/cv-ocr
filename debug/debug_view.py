#!/usr/bin/env python3
"""
Script debug - Vẽ khung lên các vùng được nhận diện
Hiển thị trực quan để dễ điều chỉnh các tham số
"""

import os
import sys
import cv2
import numpy as np

# Thêm thư mục gốc vào path để import được image_processor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== CÁC THAM SỐ CẦN ĐIỀU CHỈNH ====================
# Vùng SỐ BÁO DANH (6 cột)
SBD_X_START = 0.73      # Tỷ lệ x bắt đầu (so với width)
SBD_X_END = 0.85        # Tỷ lệ x kết thúc
SBD_Y_START = 0.09      # Tỷ lệ y bắt đầu (so với height)
SBD_Y_END = 0.285        # Tỷ lệ y kết thúc
SBD_NUM_COLS = 6        # Số cột (số chữ số)

# Vùng MÃ ĐỀ (3 cột)
EXAM_X_START = 0.88     # Tỷ lệ x bắt đầu
EXAM_X_END = 0.94       # Tỷ lệ x kết thúc
EXAM_Y_START = 0.09   # Tỷ lệ y bắt đầu
EXAM_Y_END = 0.285       # Tỷ lệ y kết thúc
EXAM_NUM_COLS = 3       # Số cột (số chữ số)

# Vùng ĐÁP ÁN PHẦN I (4 cột, mỗi cột 10 câu)
ANSWER_Y_START = 0.365  # Tỷ lệ y bắt đầu
ANSWER_Y_END = 0.523    # Tỷ lệ y kết thúc
ANSWER_COLUMNS = [
    (0.118, 0.265, 1),    # (x_start, x_end, câu_bắt_đầu) - Cột 1: câu 1-10 (rộng 0.147)
    (0.331, 0.478, 11),   # Cột 2: câu 11-20 (0.265 + 0.066 = 0.331)
    (0.544, 0.691, 21),   # Cột 3: câu 21-30 (0.478 + 0.066 = 0.544)
    (0.757, 0.904, 31),   # Cột 4: câu 31-40 (0.691 + 0.066 = 0.757)
]

# Tham số nhận diện
MIN_BUBBLES_PER_COL = 8     # Số ô tối thiểu trong 1 cột hợp lệ
COLUMN_TOLERANCE = 20       # Độ lệch x để nhóm cột
CONTRAST_THRESHOLD = 10     # Ngưỡng tương phản để xác định ô được tô
# ====================================================================


def _draw_text_with_background(image, text, position, font_scale=1.0, thickness=2, 
                                text_color=(0, 0, 0), bg_color=(255, 255, 255), padding=5):
    """
    Vẽ text với nền trắng để dễ đọc
    
    Args:
        image: Ảnh để vẽ lên
        text: Nội dung text
        position: Tuple (x, y) vị trí góc trái dưới của text
        font_scale: Kích thước font
        thickness: Độ dày nét chữ
        text_color: Màu chữ (mặc định đen)
        bg_color: Màu nền (mặc định trắng)
        padding: Khoảng đệm xung quanh text
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    x, y = position
    
    # Tính kích thước text
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Vẽ nền trắng
    cv2.rectangle(image, 
                  (x - padding, y - text_h - padding), 
                  (x + text_w + padding, y + baseline + padding), 
                  bg_color, -1)
    
    # Vẽ text đen với viền để dễ đọc hơn
    # Vẽ viền (outline)
    cv2.putText(image, text, (x-1, y-1), font, font_scale, (255, 255, 255), thickness + 2)
    cv2.putText(image, text, (x+1, y+1), font, font_scale, (255, 255, 255), thickness + 2)
    cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness + 1)


def _draw_full_grid(image, thresh_image, full_grid, original_bubbles, color_real, color_virtual, label):
    """
    Vẽ grid đầy đủ, phân biệt ô thật và ô ảo
    
    Args:
        image: Ảnh để vẽ lên
        thresh_image: Ảnh threshold để tính độ đậm
        full_grid: Grid đầy đủ từ _ensure_full_grid
        original_bubbles: Danh sách ô đã detect thực
        color_real: Màu cho ô thật
        color_virtual: Màu cho ô ảo (được tạo thêm)
        label: Nhãn cho vùng
    """
    if not full_grid:
        return
    
    # Tạo set các tọa độ ô thật để kiểm tra
    real_positions = set()
    for b in original_bubbles:
        real_positions.add((b[0], b[1]))
    
    total_real = 0
    total_virtual = 0
    
    for col_idx, col_bubbles in enumerate(full_grid):
        for row_idx, (x, y, w, h) in enumerate(col_bubbles):
            center_x = x + w // 2
            center_y = y + h // 2
            radius = min(w, h) // 2
            
            # Kiểm tra xem ô này có phải là ô thật không
            is_real = False
            for bx, by in real_positions:
                if abs(bx - x) < 15 and abs(by - y) < 15:
                    is_real = True
                    break
            
            if is_real:
                color = color_real
                total_real += 1
            else:
                color = color_virtual
                total_virtual += 1
            
            # Vẽ hình tròn
            cv2.circle(image, (center_x, center_y), radius, color, 2)
            
            # Ghi số "cột-hàng" vào giữa ô
            text = f"{col_idx+1}-{row_idx}"
            font_scale = 0.35
            thickness = 1
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x = center_x - text_w // 2
            text_y = center_y + text_h // 2
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (0, 0, 0), thickness + 1)  # Viền đen
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (255, 255, 255), thickness)  # Chữ trắng
    
    print(f"  {label}: {total_real} ô thật + {total_virtual} ô ảo = {total_real + total_virtual} tổng")


def _read_and_mark_digit_grid(image, thresh_image, full_grid, color_selected):
    """
    Đọc giá trị từ grid số (SBD, Mã đề) và đánh dấu ô được chọn
    
    Returns:
        Chuỗi số đọc được
    """
    if not full_grid:
        return ""
    
    result = ""
    
    for col_idx, col_bubbles in enumerate(full_grid):
        # Tính độ đậm của từng ô trong cột
        darkness_values = []
        for row_idx, (x, y, w, h) in enumerate(col_bubbles):
            bubble_roi = thresh_image[y:y+h, x:x+w]
            if bubble_roi.size > 0:
                avg_intensity = np.mean(bubble_roi)
                darkness_values.append((row_idx, avg_intensity, x, y, w, h))
            else:
                darkness_values.append((row_idx, 0, x, y, w, h))
        
        if darkness_values:
            # Sắp xếp theo độ đậm (cao nhất = được tô)
            darkness_values.sort(key=lambda x: x[1], reverse=True)
            selected = darkness_values[0]
            max_dark = selected[1]
            min_dark = darkness_values[-1][1]
            
            if max_dark - min_dark >= CONTRAST_THRESHOLD:
                digit = selected[0]
                result += str(digit)
                
                # Đánh dấu ô được chọn bằng viền đậm
                x, y, w, h = selected[2], selected[3], selected[4], selected[5]
                cv2.rectangle(image, (x-3, y-3), (x+w+3, y+h+3), color_selected, 3)
            else:
                result += "0"
        else:
            result += "0"
    
    return result


def _read_and_mark_answer_grid(image, thresh_image, full_grid, color_selected):
    """
    Đọc đáp án từ grid và đánh dấu ô được chọn
    
    Returns:
        Dict {câu_số: đáp_án}
    """
    if not full_grid:
        return {}
    
    choice_map = {0: "A", 1: "B", 2: "C", 3: "D"}
    answers = {}
    
    for row_idx, row_bubbles in enumerate(full_grid):
        # Tính độ đậm của từng ô trong hàng
        darkness_values = []
        for col_idx, (x, y, w, h) in enumerate(row_bubbles):
            bubble_roi = thresh_image[y:y+h, x:x+w]
            if bubble_roi.size > 0:
                avg_intensity = np.mean(bubble_roi)
                darkness_values.append((col_idx, avg_intensity, x, y, w, h))
            else:
                darkness_values.append((col_idx, 0, x, y, w, h))
        
        if darkness_values:
            # Sắp xếp theo độ đậm
            darkness_values.sort(key=lambda x: x[1], reverse=True)
            selected = darkness_values[0]
            max_dark = selected[1]
            min_dark = darkness_values[-1][1]
            
            if max_dark - min_dark >= CONTRAST_THRESHOLD:
                choice_idx = selected[0]
                if choice_idx < 4:
                    answers[row_idx + 1] = choice_map[choice_idx]
                    
                    # Đánh dấu ô được chọn
                    x, y, w, h = selected[2], selected[3], selected[4], selected[5]
                    cv2.rectangle(image, (x-3, y-3), (x+w+3, y+h+3), color_selected, 3)
    
    return answers


def _draw_full_answer_grid(image, thresh_image, full_grid, original_bubbles, color_real, color_virtual, label):
    """
    Vẽ grid đáp án đầy đủ (theo hàng), phân biệt ô thật và ô ảo
    
    Args:
        image: Ảnh để vẽ lên
        thresh_image: Ảnh threshold để tính độ đậm
        full_grid: Grid đầy đủ từ _ensure_full_answer_grid (list các hàng)
        original_bubbles: Danh sách ô đã detect thực
        color_real: Màu cho ô thật
        color_virtual: Màu cho ô ảo
        label: Nhãn cho vùng
    """
    if not full_grid:
        return
    
    # Tạo set các tọa độ ô thật để kiểm tra
    real_positions = set()
    for b in original_bubbles:
        real_positions.add((b[0], b[1]))
    
    total_real = 0
    total_virtual = 0
    
    for row_idx, row_bubbles in enumerate(full_grid):
        for col_idx, (x, y, w, h) in enumerate(row_bubbles):
            center_x = x + w // 2
            center_y = y + h // 2
            radius = min(w, h) // 2
            
            # Kiểm tra xem ô này có phải là ô thật không
            is_real = False
            for bx, by in real_positions:
                if abs(bx - x) < 15 and abs(by - y) < 15:
                    is_real = True
                    break
            
            if is_real:
                color = color_real
                total_real += 1
            else:
                color = color_virtual
                total_virtual += 1
            
            # Vẽ hình tròn
            cv2.circle(image, (center_x, center_y), radius, color, 2)
            
            # Ghi số "hàng-cột" (ví dụ: 1-A, 1-B, 2-C...)
            choice_labels = ['A', 'B', 'C', 'D']
            text = f"{row_idx+1}-{choice_labels[col_idx] if col_idx < 4 else col_idx}"
            font_scale = 0.3
            thickness = 1
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x = center_x - text_w // 2
            text_y = center_y + text_h // 2
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (255, 255, 255), thickness)
    
    print(f"  {label}: {total_real} ô thật + {total_virtual} ô ảo = {total_real + total_virtual} tổng")


def debug_draw_regions(image_path: str, output_path: str = None):
    """
    Vẽ khung lên các vùng đang được nhận diện
    Vẽ TẤT CẢ các ô với số thứ tự để kiểm tra
    Đảm bảo SBD luôn có đủ 60 ô (6 cột x 10 hàng)
    Đọc và hiển thị kết quả lên ảnh
    """
    from image_processor import ExamSheetProcessor
    
    # Đọc ảnh
    image = cv2.imread(image_path)
    if image is None:
        print(f"Không thể đọc ảnh: {image_path}")
        return None
    
    # Tạo processor
    processor = ExamSheetProcessor()
    
    # Resize ảnh về kích thước chuẩn (giống như preprocess_image)
    h, w = image.shape[:2]
    print(f"📐 Kích thước gốc: {w}x{h}")
    
    need_enhance = False
    if w != processor.STANDARD_WIDTH or h != processor.STANDARD_HEIGHT:
        if w < processor.STANDARD_WIDTH or h < processor.STANDARD_HEIGHT:
            need_enhance = True
            print(f"📐 Upscale về: {processor.STANDARD_WIDTH}x{processor.STANDARD_HEIGHT} (cần enhance)")
        else:
            print(f"📐 Downscale về: {processor.STANDARD_WIDTH}x{processor.STANDARD_HEIGHT}")
        image = cv2.resize(
            image, 
            (processor.STANDARD_WIDTH, processor.STANDARD_HEIGHT), 
            interpolation=cv2.INTER_CUBIC if need_enhance else cv2.INTER_AREA
        )
        
    height, width = image.shape[:2]
    
    # Lấy thresh_image và bubbles
    thresh_image = processor.preprocess_image(image_path)
    bubbles = processor.find_answer_bubbles(thresh_image)
    
    # Màu sắc
    COLOR_SBD = (255, 191, 0)       # Xanh da trời - Số báo danh (BGR)
    COLOR_SBD_VIRTUAL = (255, 191, 0)  # Xanh da trời - Ô ảo SBD
    COLOR_EXAM = (255, 191, 0)      # Xanh da trời - Mã đề
    COLOR_ANSWERS = (255, 191, 0)   # Xanh da trời - Vùng đáp án
    COLOR_SELECTED = (0, 165, 255)  # Cam - Ô được chọn
    
    # ========== 1. XỬ LÝ SỐ BÁO DANH ==========
    sbd_x1 = int(SBD_X_START * width)
    sbd_x2 = int(SBD_X_END * width)
    sbd_y1 = int(SBD_Y_START * height)
    sbd_y2 = int(SBD_Y_END * height)
    cv2.rectangle(image, (sbd_x1, sbd_y1), (sbd_x2, sbd_y2), COLOR_SBD, 3)
    
    # Lọc bubbles trong vùng SBD
    sbd_bubbles = [
        (x, y, w, h) for x, y, w, h in bubbles
        if SBD_X_START * width < x < SBD_X_END * width 
        and SBD_Y_START * height < y < SBD_Y_END * height
    ]
    
    # Đảm bảo có đủ 60 ô (6 cột x 10 hàng)
    sbd_full_grid = processor._ensure_full_grid(sbd_bubbles, num_cols=SBD_NUM_COLS, num_rows=10)
    
    # Vẽ grid SBD đầy đủ
    _draw_full_grid(image, thresh_image, sbd_full_grid, sbd_bubbles, COLOR_SBD, COLOR_SBD_VIRTUAL, "SBD")
    
    # Đọc và đánh dấu SBD
    sbd_result = _read_and_mark_digit_grid(image, thresh_image, sbd_full_grid, COLOR_SELECTED)
    _draw_text_with_background(image, f"SBD: {sbd_result}", (sbd_x1, sbd_y1 - 15), font_scale=0.8, thickness=2)
    
    # ========== 2. XỬ LÝ MÃ ĐỀ ==========
    exam_x1 = int(EXAM_X_START * width)
    exam_x2 = int(EXAM_X_END * width)
    exam_y1 = int(EXAM_Y_START * height)
    exam_y2 = int(EXAM_Y_END * height)
    cv2.rectangle(image, (exam_x1, exam_y1), (exam_x2, exam_y2), COLOR_EXAM, 3)
    
    # Lọc bubbles trong vùng mã đề
    exam_bubbles = [
        (x, y, w, h) for x, y, w, h in bubbles
        if EXAM_X_START * width < x < EXAM_X_END * width 
        and EXAM_Y_START * height < y < EXAM_Y_END * height
    ]
    
    # Đảm bảo có đủ 30 ô (3 cột x 10 hàng) cho mã đề
    COLOR_EXAM_VIRTUAL = (255, 191, 0)  # Xanh da trời
    exam_full_grid = processor._ensure_full_grid(exam_bubbles, num_cols=EXAM_NUM_COLS, num_rows=10)
    _draw_full_grid(image, thresh_image, exam_full_grid, exam_bubbles, COLOR_EXAM, COLOR_EXAM_VIRTUAL, "EXAM")
    
    # Đọc và đánh dấu Mã đề
    exam_result = _read_and_mark_digit_grid(image, thresh_image, exam_full_grid, COLOR_SELECTED)
    _draw_text_with_background(image, f"Ma de: {exam_result}", (exam_x1, exam_y1 - 15), font_scale=0.8, thickness=2)
    
    # ========== 3. XỬ LÝ ĐÁP ÁN ==========
    COLOR_ANS_VIRTUAL = (255, 191, 0)  # Xanh da trời
    all_answers = {}
    
    for col_idx, (col_x_start, col_x_end, start_q) in enumerate(ANSWER_COLUMNS):
        x1 = int(col_x_start * width)
        x2 = int(col_x_end * width)
        y1 = int(ANSWER_Y_START * height)
        y2 = int(ANSWER_Y_END * height)
        cv2.rectangle(image, (x1, y1), (x2, y2), COLOR_ANSWERS, 2)
        
        # Lọc bubbles trong vùng đáp án này
        ans_bubbles = [
            (x, y, w, h) for x, y, w, h in bubbles
            if col_x_start * width < x < col_x_end * width 
            and ANSWER_Y_START * height < y < ANSWER_Y_END * height
        ]
        
        # Đảm bảo có đủ 40 ô (4 cột x 10 hàng) - truyền đầy đủ vùng để tính grid chính xác
        ans_full_grid = processor._ensure_full_answer_grid(
            ans_bubbles, num_cols=4, num_rows=10,
            region_x_start=x1, region_x_end=x2,
            region_y_start=y1, region_y_end=y2
        )
        
        if ans_full_grid:
            _draw_full_answer_grid(image, thresh_image, ans_full_grid, ans_bubbles, COLOR_ANSWERS, COLOR_ANS_VIRTUAL, f"ANS{col_idx+1}")
            
            # Đọc và đánh dấu đáp án
            col_answers = _read_and_mark_answer_grid(image, thresh_image, ans_full_grid, COLOR_SELECTED)
            
            # Chuyển đổi số câu local sang global
            for local_q, answer in col_answers.items():
                global_q = start_q + local_q - 1
                all_answers[global_q] = answer
            
            # Hiển thị kết quả đáp án lên vùng
            ans_text = "".join([col_answers.get(i, "-") for i in range(1, 11)])
            _draw_text_with_background(image, f"{start_q}-{start_q+9}: {ans_text}", (x1, y1 - 15), font_scale=0.5, thickness=1)
    
    # ========== HIỂN THỊ TỔNG KẾT ==========
    y_pos = 50
    _draw_text_with_background(image, "KET QUA DOC:", (50, y_pos), font_scale=1.0, thickness=2)
    y_pos += 45
    
    _draw_text_with_background(image, f"So bao danh: {sbd_result}", (50, y_pos), font_scale=0.9, thickness=2)
    y_pos += 40
    
    _draw_text_with_background(image, f"Ma de: {exam_result}", (50, y_pos), font_scale=0.9, thickness=2)
    y_pos += 40
    
    # Hiển thị đáp án theo từng dãy
    _draw_text_with_background(image, "Dap an:", (50, y_pos), font_scale=0.9, thickness=2)
    y_pos += 35
    
    for start_q in [1, 11, 21, 31]:
        end_q = start_q + 9
        ans_line = f"  {start_q:02d}-{end_q:02d}: "
        for q in range(start_q, end_q + 1):
            ans_line += all_answers.get(q, "-")
        _draw_text_with_background(image, ans_line, (50, y_pos), font_scale=0.7, thickness=2)
        y_pos += 32
    
    # Lưu ảnh
    if output_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"debug/z_{timestamp}.jpg"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, image)
    
    # In ra console
    print(f"✓ Đã lưu: {output_path}")
    print(f"  SBD: {sbd_result} | Mã đề: {exam_result}")
    ans_str = " ".join([f"{q}:{all_answers.get(q, '-')}" for q in range(1, 41)])
    print(f"  Đáp án: {ans_str}")
    
    return output_path


def _draw_all_bubbles_with_numbers(image, processor, bubbles, color, label):
    """Vẽ tất cả bubbles và đánh số theo cột/hàng"""
    if not bubbles:
        return
    
    # Nhóm theo cột
    columns = processor._group_bubbles_by_column(bubbles, tolerance=COLUMN_TOLERANCE)
    
    for col_idx, col_bubbles in enumerate(columns):
        # Sắp xếp theo y (từ trên xuống)
        col_bubbles = sorted(col_bubbles, key=lambda b: b[1])
        
        for row_idx, (x, y, w, h) in enumerate(col_bubbles):
            # Vẽ hình tròn
            center_x = x + w // 2
            center_y = y + h // 2
            radius = min(w, h) // 2
            cv2.circle(image, (center_x, center_y), radius, color, 2)
            
            # Ghi số "cột-hàng" vào giữa ô (ví dụ: 1-0, 1-5, 2-3...)
            text = f"{col_idx+1}-{row_idx}"
            font_scale = 0.35
            thickness = 1
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_x = center_x - text_w // 2
            text_y = center_y + text_h // 2
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (0, 0, 0), thickness + 1)  # Viền đen
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_scale, (255, 255, 255), thickness)  # Chữ trắng


def _read_digit_columns(processor, thresh_image, bubbles, num_columns, image, color):
    """Đọc các cột số và vẽ ô được chọn"""
    if not bubbles:
        return "0" * num_columns
    
    columns = processor._group_bubbles_by_column(bubbles, tolerance=COLUMN_TOLERANCE)
    valid_columns = [col for col in columns if len(col) >= MIN_BUBBLES_PER_COL][:num_columns]
    
    result = ""
    
    for col_bubbles in valid_columns:
        # Sắp xếp theo y và lấy 10 ô
        col_bubbles = sorted(col_bubbles, key=lambda b: b[1])[:10]
        
        if len(col_bubbles) < 10:
            result += "0"
            continue
        
        # Tính độ đậm
        darkness_values = []
        for digit_idx, (x, y, w, h) in enumerate(col_bubbles):
            bubble_roi = thresh_image[y:y+h, x:x+w]
            if bubble_roi.size > 0:
                avg_intensity = np.mean(bubble_roi)
                darkness_values.append((digit_idx, avg_intensity, x, y, w, h))
        
        if darkness_values:
            darkness_values.sort(key=lambda x: x[1], reverse=True)
            selected = darkness_values[0]
            max_dark = selected[1]
            min_dark = darkness_values[-1][1]
            
            if max_dark - min_dark >= CONTRAST_THRESHOLD:
                # Vẽ ô được chọn
                x, y, w, h = selected[2], selected[3], selected[4], selected[5]
                cv2.rectangle(image, (x-2, y-2), (x+w+2, y+h+2), color, 3)
                result += str(selected[0])
            else:
                result += "0"
        else:
            result += "0"
    
    return result.ljust(num_columns, "0")[:num_columns]


import re

def is_valid_exam_filename(filename):
    """Kiểm tra tên file có hợp lệ không (format: XXX_YYYYYY.jpg)"""
    # Pattern: 3 chữ số _ 6 chữ số . extension
    pattern = r'^\d{3}_\d{6}\.(jpg|jpeg|png|bmp)$'
    return bool(re.match(pattern, filename.lower()))


def main():
    os.makedirs("debug", exist_ok=True)
    
    # Lấy danh sách ảnh
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            image_files = [path]
        elif os.path.isdir(path):
            # Lọc chỉ lấy file có tên hợp lệ
            all_files = os.listdir(path)
            valid_files = [f for f in all_files if is_valid_exam_filename(f)]
            image_files = [os.path.join(path, f) for f in valid_files]
        else:
            print(f"Không tìm thấy: {path}")
            return
    else:
        exams_dir = "exams"
        all_files = os.listdir(exams_dir)
        valid_files = [f for f in all_files if is_valid_exam_filename(f)]
        image_files = [os.path.join(exams_dir, f) for f in valid_files]
    
    if not image_files:
        print("Không tìm thấy ảnh hợp lệ!")
        print("Format tên file: XXX_YYYYYY.jpg (VD: 001_123456.jpg)")
        return
    
    # Sắp xếp theo tên file
    image_files.sort()
    
    print(f"Tìm thấy {len(image_files)} ảnh hợp lệ")
    print("=" * 50)
    print(f"Tham số hiện tại:")
    print(f"  SBD: x={SBD_X_START}-{SBD_X_END}, y={SBD_Y_START}-{SBD_Y_END}")
    print(f"  Mã đề: x={EXAM_X_START}-{EXAM_X_END}, y={EXAM_Y_START}-{EXAM_Y_END}")
    print("=" * 50)
    
    # Xử lý TẤT CẢ các file
    for idx, image_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] Đang xử lý: {os.path.basename(image_path)}")
        # Tạo output path dựa trên tên file gốc
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = f"debug/z_{base_name}.jpg"
        debug_draw_regions(image_path, output_path)
    
    print("\n" + "=" * 50)
    print(f"Hoàn thành! Đã xử lý {len(image_files)} ảnh")
    print("Xem ảnh debug trong thư mục debug/")
    print("Điều chỉnh các tham số ở đầu file nếu cần.")


if __name__ == "__main__":
    main()
