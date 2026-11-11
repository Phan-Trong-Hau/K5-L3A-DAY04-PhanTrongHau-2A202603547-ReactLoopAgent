# Ghi chú phân tích · Day 04

Họ và tên: Phan Trong Hau
MSSV: 2A202603547

**Trạng thái: đang thực hiện.** Hiện chỉ có smoke test E2; chưa có hai bộ eval
đầy đủ 22 case. Nội dung dưới đây ghi nhận lỗi thật, không thay thế báo cáo cuối.

## 1. Case được chọn

- ID case: E2 — Cloudflare cache purge và phạm vi FedRAMP.
- Câu trả lời cần xem xét: “Một **website CLB không thuộc FedRAMP** **không bị ảnh hưởng** theo dữ liệu hiện tại.”
- Điểm smoke test: 83/100; **chưa phải điểm eval lần 1 toàn bộ**.
- File gốc: [reports/smoke_e2.json](reports/smoke_e2.json).

## 2. Bằng chứng trong trace

```json
{"event":"model","step":1,"finish":"tool_calls"}
{"event":"tool","step":1,"name":"get_status","arguments":{"provider":"cloudflare","component":"cache"}}
{"event":"model","step":2,"finish":"stop"}
```

Đoạn trên lược bỏ `result` để dễ đọc; trace đầy đủ có trong file JSON gốc.
Không có lời gọi `get_incident_details`. Agent suy diễn phạm vi từ tiêu đề
incident, chưa đọc update xác nhận; cũng không đủ dữ liệu để chẩn đoán website CLB.
Answer dùng homepage thay vì URL incident và gọi snapshot là trạng thái hiện tại.

## 3. Thay đổi đã thực hiện

- Đã hoàn thiện loop cơ bản, error observations, max_steps và trace tại `agent.py`.
- Đã thêm endpoint local, cấu hình Ollama và công cụ terminal chạy thử.
- **Chưa áp dụng cải tiến nguồn trong phiên bản smoke test này.** Dự kiến ở phần
  tiếp theo: hướng dẫn model đọc chi tiết và thêm validation URL nguồn trong budget.
- Lý do: trace cho thấy model dừng sớm trước khi thu thập đủ bằng chứng.

## 4. So sánh hai lần chạy

**Chưa thực hiện.** Smoke test E2 có 2 model calls, 1973 token agent và
1982 token judge. Không dùng các số này làm điểm tổng bộ eval.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng 22 case | Chưa chạy xong | Chưa chạy |
| Điểm case E2 | Chưa có bộ đầy đủ | Chưa chạy |
| Số model calls | Chưa thống kê | Chưa thống kê |
| Token, chi phí nếu có | Chưa thống kê | Chưa thống kê |

- Lỗi còn lại: thiếu validation nguồn; 2 tests `EvidenceGateTests` chưa pass ở baseline.
- Lỗi chất lượng quan sát được: suy diễn phạm vi ảnh hưởng, chưa đọc timeline.
- Chưa kết luận cải tiến tốt hơn khi chưa có dữ liệu trước/sau.

## 5. Giới hạn

- Agent và judge dùng cùng model local 4B nên đánh giá có thể thiên lệch hoặc sai.
  Trong E2, judge cho điểm khá cao dù trace thiếu bước đọc incident.
- Snapshot không chứng minh trạng thái dịch vụ tại thời điểm chạy thử.
- Tìm chuỗi trong 50 incident và timeline rút gọn có thể thiếu dữ liệu liên quan.
- Một case và một lần chạy không chứng minh độ ổn định, không đại diện 22 case.
- Chưa đo chi phí điện/phần cứng local; không có phí API dịch vụ trong lần thử này.
