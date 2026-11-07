"""Neutral placeholder content per layout, used to preview saved templates WITHOUT copying the user's private deck content."""
from __future__ import annotations

VI = {
    'cover': {'eyebrow': 'Mẫu trình bày', 'title': 'Tiêu đề nói **điều quan trọng nhất**', 'subtitle': 'Một câu mô tả ngắn về nội dung và điều người nghe nhận được.', 'meta': ['Trình bày: Tên người trình bày', 'Ngày: dd/mm/yyyy']},
    'agenda': {'eyebrow': 'Nội dung', 'title': 'Bốn phần của bài trình bày', 'items': [{'title': 'Bối cảnh', 'detail': 'Vì sao chủ đề quan trọng'}, {'title': 'Phân tích', 'detail': 'Dữ liệu và phát hiện'}, {'title': 'Đề xuất', 'detail': 'Phương án và lý do'}, {'title': 'Bước tiếp theo', 'detail': 'Việc cần làm'}]},
    'section': {'section_number': '01', 'eyebrow': 'Phần 1', 'title': 'Câu hỏi mà phần này trả lời', 'subtitle': 'Một câu dẫn ngắn.'},
    'statement': {'eyebrow': 'Luận điểm', 'title': 'Một câu khẳng định **rõ ràng** mà người nghe cần nhớ.', 'subtitle': 'Một câu giải thích ngắn bổ sung.'},
    'metrics': {'eyebrow': 'Số liệu mẫu', 'title': 'Ba con số tóm tắt bức tranh', 'items': [{'value': '42%', 'label': 'chỉ số thứ nhất', 'detail': 'Giải thích ngắn'}, {'value': '1.250', 'label': 'chỉ số thứ hai', 'detail': 'Giải thích ngắn'}, {'value': '3,5x', 'label': 'chỉ số thứ ba', 'detail': 'Giải thích ngắn'}]},
    'kpi-dashboard': {'eyebrow': 'Chỉ số', 'title': 'Hai chỉ số đạt mục tiêu, một chỉ số cần theo dõi', 'period': 'Kỳ báo cáo', 'items': [{'label': 'Chỉ số A', 'value': '92%', 'delta': '+3 đ', 'status': 'up', 'trend': [80, 84, 86, 89, 92]}, {'label': 'Chỉ số B', 'value': '1.240', 'delta': '+8%', 'status': 'up', 'trend': [900, 980, 1050, 1150, 1240]}, {'label': 'Chỉ số C', 'value': '36', 'delta': '+5%', 'status': 'bad', 'trend': [30, 31, 33, 34, 36]}]},
    'cards': {'eyebrow': 'Ba nhóm', 'title': 'Ba nhóm ý ngang hàng', 'items': [{'title': 'Nhóm thứ nhất', 'body': 'Mô tả ngắn một đến hai dòng.', 'icon': 'layers'}, {'title': 'Nhóm thứ hai', 'body': 'Mô tả ngắn một đến hai dòng.', 'icon': 'target'}, {'title': 'Nhóm thứ ba', 'body': 'Mô tả ngắn một đến hai dòng.', 'icon': 'lightbulb'}]},
    'process': {'eyebrow': 'Quy trình', 'title': 'Bốn bước từ đầu vào đến kết quả', 'steps': [{'title': 'Bước 1', 'detail': 'Mô tả ngắn'}, {'title': 'Bước 2', 'detail': 'Mô tả ngắn'}, {'title': 'Bước 3', 'detail': 'Mô tả ngắn'}, {'title': 'Bước 4', 'detail': 'Mô tả ngắn'}]},
    'timeline': {'eyebrow': 'Lộ trình', 'title': 'Bốn mốc chính', 'items': [{'date': 'Mốc 1', 'title': 'Khởi động', 'detail': 'Mô tả ngắn', 'state': 'done'}, {'date': 'Mốc 2', 'title': 'Thử nghiệm', 'detail': 'Mô tả ngắn', 'state': 'now'}, {'date': 'Mốc 3', 'title': 'Đánh giá', 'detail': 'Mô tả ngắn', 'state': 'next'}, {'date': 'Mốc 4', 'title': 'Mở rộng', 'detail': 'Mô tả ngắn', 'state': 'next'}]},
    'comparison': {'eyebrow': 'So sánh', 'title': 'Hai phương án tối ưu cho hai mục tiêu', 'highlight': 'left', 'left': {'title': 'Phương án A', 'bullets': ['Ưu điểm thứ nhất', 'Ưu điểm thứ hai', 'Giới hạn chính']}, 'right': {'title': 'Phương án B', 'bullets': ['Ưu điểm thứ nhất', 'Ưu điểm thứ hai', 'Giới hạn chính']}, 'verdict': 'Kết luận ngắn về lựa chọn.'},
    'table': {'eyebrow': 'Ma trận', 'title': 'So sánh theo ba tiêu chí', 'columns': ['Tiêu chí', 'Phương án A', 'Phương án B'], 'highlight': 'Phương án A', 'rows': [['Tiêu chí 1', 'Tốt', 'Trung bình'], ['Tiêu chí 2', 'Trung bình', 'Tốt'], ['Tiêu chí 3', 'Tốt', 'Thấp']]},
    'chart': {'eyebrow': 'Dữ liệu mẫu', 'title': 'Chỉ số tăng đều qua các kỳ', 'chart': {'type': 'column', 'categories': ['Kỳ 1', 'Kỳ 2', 'Kỳ 3', 'Kỳ 4', 'Kỳ 5'], 'series': [{'name': 'Giá trị', 'values': [42, 48, 55, 61, 70]}]}, 'caption': 'Dữ liệu minh họa.'},
    'case': {'eyebrow': 'Tình huống mẫu', 'title': 'Một trường hợp cụ thể', 'value': '~120', 'value_label': 'đơn vị đo của con số chính', 'body': 'Mô tả ngắn điều đã xảy ra và vì sao nó đáng chú ý.'},
    'evidence-levels': {'eyebrow': 'Mức độ tin cậy', 'title': 'Bốn mức bằng chứng', 'levels': [{'label': 'Mức 1', 'detail': 'Mô tả'}, {'label': 'Mức 2', 'detail': 'Mô tả'}, {'label': 'Mức 3', 'detail': 'Mô tả'}, {'label': 'Mức 4', 'detail': 'Mô tả'}]},
    'problem-solution': {'eyebrow': 'Vấn đề và giải pháp', 'title': 'Từ vấn đề đến hướng xử lý', 'problem': {'points': ['Vấn đề thứ nhất', 'Vấn đề thứ hai', 'Vấn đề thứ ba']}, 'solution': {'points': ['Giải pháp thứ nhất', 'Giải pháp thứ hai', 'Giải pháp thứ ba']}},
    'methodology': {'eyebrow': 'Phương pháp', 'title': 'Thiết kế nghiên cứu', 'facts': [{'value': 'n = 300', 'label': 'cỡ mẫu'}, {'value': '6 tháng', 'label': 'thời gian'}], 'steps': [{'title': 'Thu thập', 'detail': 'Mô tả ngắn'}, {'title': 'Xử lý', 'detail': 'Mô tả ngắn'}, {'title': 'Phân tích', 'detail': 'Mô tả ngắn'}]},
    'diagram': {'eyebrow': 'Sơ đồ', 'title': 'Bốn thành phần quanh một trung tâm', 'center': 'Trung tâm', 'nodes': [{'title': 'Thành phần 1', 'icon': 'layers'}, {'title': 'Thành phần 2', 'icon': 'database'}, {'title': 'Thành phần 3', 'icon': 'users'}, {'title': 'Thành phần 4', 'icon': 'settings'}]},
    'learning-objectives': {'eyebrow': 'Mục tiêu', 'title': 'Sau phần này, người nghe có thể', 'items': ['Giải thích khái niệm chính', 'So sánh hai cách tiếp cận', 'Áp dụng vào một tình huống']},
    'definition': {'eyebrow': 'Khái niệm', 'term': 'Thuật ngữ', 'definition': 'Định nghĩa ngắn gọn, dễ hiểu trong một đến hai câu.', 'example': 'Một ví dụ cụ thể minh họa khái niệm.'},
    'image-split': {'eyebrow': 'Hình ảnh', 'title': 'Một hình ảnh minh họa luận điểm', 'image': '__sample__.jpg', 'image_alt': 'Hình minh họa', 'bullets': ['Ý thứ nhất', 'Ý thứ hai']},
    'full-bleed-image': {'eyebrow': 'Bối cảnh', 'title': 'Một câu ngắn trên nền ảnh', 'image': '__sample__.jpg', 'image_alt': 'Hình minh họa'},
    'quote': {'quote': 'Một câu trích dẫn có thật, được kiểm chứng và ghi nguồn.', 'attribution': 'Tên người, vai trò'},
    'key-takeaways': {'eyebrow': 'Kết luận', 'title': 'Ba điều cần nhớ', 'bullets': ['Điều thứ nhất', 'Điều thứ hai', 'Điều thứ ba']},
    'references': {'title': 'Tài liệu tham khảo', 'items': ['Tác giả (Năm). Tên tài liệu. Nơi xuất bản.', 'Tác giả (Năm). Tên tài liệu. Nơi xuất bản.']},
    'closing': {'eyebrow': 'Hỏi đáp', 'title': 'Cảm ơn', 'subtitle': 'Câu kết hoặc lời kêu gọi hành động.'},
}


def neutral_deck(layouts: list[str], title: str = 'Bộ mẫu trung tính', language: str = 'vi') -> dict:
    slides = []
    for i, lay in enumerate(layouts, 1):
        base = dict(VI.get(lay, VI['statement']))
        base.update({'id': f'{lay}-{i}', 'layout': lay})
        slides.append(base)
    return {'title': title, 'audience': 'Xem trước template', 'takeaway': 'Xem trước phong cách', 'language': language,
            'brand': 'TEMPLATE PREVIEW', 'demo': True, 'slides': slides}

