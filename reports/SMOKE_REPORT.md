# Báo cáo chạy thử local — chưa phải báo cáo eval toàn bộ

- Ngày chạy: 11/11/2026 (GMT+7).
- Phiên bản agent: baseline `df52938`.
- Model agent và judge: `status-agent-local`, Ollama local qua OpenAI-compatible adapter.
- Context 16384, output tối đa 2048 tokens, temperature 0, max_steps 8.
- Dữ liệu: snapshot gốc, không sửa fixtures/scenarios/grading.
- Phạm vi: **chỉ case E2**, không phải 22 case bài chính.
- Kết quả: `completed`, điểm judge **83/100 cho E2**.
- Model calls của agent: 2; tool calls: 1.
- Token agent: 1973; token judge: 1982; tổng: 3955.
- Không phát sinh phí API dịch vụ; chưa đo thời gian/điện năng tiêu thụ local.

## Câu hỏi

Cloudflare cache purge có incident nào liên quan không? Một website CLB không thuộc FedRAMP có chắc bị ảnh hưởng không?

## Bằng chứng và vấn đề quan sát được

Trace chỉ có `get_status(provider="cloudflare", component="cache")` ở step 1,
sau đó model trả final ở step 2. Agent **chưa gọi `get_incident_details`**.
Tool status trả tiêu đề, ID và trạng thái incident; không trả timeline chứa
bằng chứng chi tiết về phạm vi FedRAMP.

Final answer có câu “Một **website CLB không thuộc FedRAMP** **không bị ảnh hưởng**
theo dữ liệu hiện tại.” Đây là kết luận quá chắc về website cụ thể khi agent chưa
đọc chi tiết incident và chưa có dữ liệu từ website đó. Answer còn gọi dữ liệu
snapshot là “trạng thái hiện tại”. Nguồn chỉ là homepage, chưa có URL incident.

Judge cho điểm tương đối cao nhưng lời giải thích có chỗ coi phạm vi FedRAMP là
đã được chứng minh; đối chiếu trace cho thấy agent chưa đọc update xác nhận phạm vi.
Vì vậy cần tự đọc evidence, không chỉ nhìn điểm 83.

## Hướng cải tiến ở phần tiếp theo

1. Yêu cầu đọc chi tiết incident khi cần kết luận timeline hoặc phạm vi.
2. Kiểm tra URL incident đã quan sát trước khi trả `completed`.
3. Phân biệt snapshot, incident lịch sử và ảnh hưởng thực tế của website.
4. Chạy đủ eval trước/sau cùng cấu hình để đo tác động; chưa thực hiện trong phần này.

## Tự xem kết quả

- `reports/smoke_e2.json`: answer, trace, usage và đánh giá gốc.
- `local/README.md`: lệnh chạy thử câu hỏi khác.
- `NOTES.md`: ghi chú phân tích đang thực hiện; chưa đủ điều kiện nộp bài hoàn chỉnh.

Tiến độ theo checkpoint được cập nhật tại [PROGRESS.md](PROGRESS.md).
