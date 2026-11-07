---
title: Aegis Edge — Kiểm thử bảo mật API ngay trên máy lập trình viên
audience: Trưởng nhóm kỹ thuật, kỹ sư backend và chuyên gia bảo mật ứng dụng
purpose: Giới thiệu sản phẩm phiên bản 1.0 và mời đăng ký dùng thử nội bộ
takeaway: Aegis Edge phát hiện lỗi phân quyền API trong 8 giây ngay trước khi mở pull request mà không gửi mã nguồn hay dữ liệu thử nghiệm lên đám mây.
template: tech-product
theme: keynote-night
language: vi
density: speaker
duration_minutes: 10
---

## 01 · Bắt lỗi phân quyền API **trước khi code rời máy bạn**
- layout: cover
- beat: title
- message: Aegis Edge chạy kiểm thử bảo mật ngữ nghĩa cục bộ ngay trong quy trình phát triển hàng ngày.
- content:
  - Phiên bản: 1.0 Release Candidate
  - Môi trường: CLI · VS Code · CI nội bộ
- status: illustrative

## 02 · Đưa kiểm thử phân quyền từ cuối quý về ngay trước mỗi commit
- layout: problem-solution
- beat: problem
- message: Đưa bước kiểm tra phân quyền về ngay lúc viết API giảm chi phí sửa lỗi gấp nhiều lần so với quét sau triển khai.
- content:
  - Đợt quét cuối quý phát hiện lỗi khi tính năng đã lên staging
  - Công cụ đám mây yêu cầu mở cổng mạng hoặc tải payload nhạy cảm ra ngoài
  - Cảnh báo tĩnh quá nhiều nhiễu khiến lập trình viên bỏ qua
  - Phân tích trực tiếp OpenAPI và route handler ngay trên máy cá nhân
  - Tự sinh kịch bản gọi thử chéo tài khoản trong container cô lập
  - Chỉ báo cáo lỗi có bằng chứng request/response tái hiện được
- status: illustrative

## 03 · Bốn bước từ git diff đến bằng chứng lỗi có thể tái hiện
- layout: process
- beat: how-it-works
- message: Toàn bộ chu trình chạy tự động sau mỗi lần lưu file hoặc trước khi tạo commit.
- content:
  - Đọc định tuyến — Dựng đồ thị endpoint và quy tắc xác thực từ mã nguồn
  - Sinh tác nhân thử — Tạo cặp tài khoản chuẩn và tài khoản chéo quyền trên môi trường giả lập
  - Đối chiếu phản hồi — Phát hiện rò rỉ trường dữ liệu hoặc thiếu kiểm tra chủ sở hữu
  - Gợi ý bản vá — Đính kèm dòng middleware cần bổ sung kèm test hồi quy
- status: illustrative

## 04 · Mỗi cảnh báo kèm bằng chứng tái hiện rõ ràng
- layout: image-split
- beat: demo
- message: Mỗi cảnh báo đi kèm cặp lệnh curl tái hiện và vị trí hàm xử lý thiếu kiểm tra quyền.
- content:
  - Không gửi mã nguồn hay token ra khỏi mạng nội bộ
  - Tích hợp sẵn định dạng SARIF cho GitHub và GitLab tự chủ
  - Tương thích Go, TypeScript, Python FastAPI và Java Spring
- status: illustrative

## 05 · Quét thay đổi cục bộ hoàn tất trong **0,13 phút** (8 giây)
- layout: chart
- beat: benchmark
- message: Tốc độ phản hồi dưới 10 giây đủ nhanh để lập trình viên chạy liên tục trước mỗi lần commit.
- content:
  - Nhanh hơn quét động truyền thống nhờ chỉ chạy lại nhánh route vừa thay đổi
- data: Rà soát thủ công 45 phút | Quét DAST staging 18 phút | Pipeline CI đầy đủ 4 phút | Aegis Edge cục bộ 0,13 phút
- status: illustrative
- visual: Biểu đồ thanh ngang so sánh thời gian phản hồi trên dự án mẫu 40 endpoint
- sources: Thử nghiệm nội bộ minh họa trên máy 16 GB RAM (2026)

## 06 · Từ công cụ cá nhân đến nền tảng kiểm chuẩn air-gapped
- layout: timeline
- beat: roadmap
- message: Bản 1.0 tập trung trải nghiệm lập trình viên, quý tới mở rộng chính sách tập trung cho khối tài chính.
- content:
  - Q2/2026 — Beta kín: Thử nghiệm với 15 nhóm backend mẫu
  - Q4/2026 — Ra mắt 1.0: Hỗ trợ OpenAPI 3.1, GraphQL và VS Code extension
  - Q1/2027 — Bản Enterprise: Quản lý quy tắc tập trung, chạy air-gapped 100%
  - Q3/2027 — Tự động hóa test: Sinh bộ integration test chuẩn theo từng ngôn ngữ
- status: illustrative

## 07 · Chạy thử trên một dịch vụ nội bộ ngay chiều nay
- layout: closing
- beat: cta
- message: Cài đặt một file nhị phân duy nhất, không cần tài khoản đám mây.
- content:
  - Cài đặt mẫu: aegis init --local
  - Tài liệu mẫu: docs/aegis-edge-demo
- status: illustrative
