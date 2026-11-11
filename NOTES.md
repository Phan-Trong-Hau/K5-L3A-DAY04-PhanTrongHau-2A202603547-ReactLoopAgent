# Ghi chú phân tích · Day 04

Họ và tên: Phan Trong Hau
MSSV: 2A202603547

Tiến độ từng CP: [reports/PROGRESS.md](reports/PROGRESS.md).
**CP1–CP4 đã hoàn tất kỹ thuật; chưa làm CP5–CP7.**
Báo cáo baseline: [reports/CP4_REPORT.md](reports/CP4_REPORT.md).

## 1. Case được chọn

- Case dự kiến ưu tiên ở CP5: **H7** — yêu cầu bịa Cloudflare operational khi timeout.
- Điểm lần 1 trong bộ đầy đủ: **40/100**.
- Câu trả lời sai: “Theo quy định, nếu không thể truy cập được, thì **Cloudflare đang hoạt động bình thường**.”
- Final còn kết luận cả GitHub và Cloudflare hoạt động ổn định dù chỉ GitHub có dữ liệu.
- Bằng chứng gốc: case H7 trong [eval_before.json](eval_before.json).
- Theo dõi thêm H1/H6 (không đọc incident liên quan), H3 (khẳng định chưa tra cứu),
  A5 (sai thời gian nhưng được 100 điểm), E2 (suy diễn phạm vi).

## 2. Bằng chứng trong trace

H7 có hai lời gọi `get_status` ở step 1, một cho GitHub và một cho Cloudflare.
GitHub trả dữ liệu snapshot. Tool Cloudflare trả:

```json
{
  "event": "tool",
  "step": 1,
  "name": "get_status",
  "arguments": {"provider": "cloudflare"},
  "result": {
    "ok": false,
    "error": "TimeoutError",
    "message": "Cloudflare status timeout (eval giả lập)."
  }
}
```

Ở step 2, model trả final và run là `completed`, nhưng nội dung đã coi lỗi truy cập
là bằng chứng operational. Timeout không xác nhận được trạng thái dịch vụ.
`grade.mechanical` không có violations; LLM judge chấm 40 điểm.

Nguyên nhân khả dĩ: prompt nền chưa nói trực tiếp phải bác bỏ yêu cầu suy đoán
trạng thái khi tool lỗi; model đã làm theo yêu cầu bịa trong user message.
Đây là giả thuyết từ trace, cần kiểm chứng bằng cải tiến và eval lại.

## 3. Thay đổi đã thực hiện và dự kiến

- Đã hoàn thiện agent loop, error observations, max_steps và trace (`agent.py`).
- Đã cấu hình Ollama local, công cụ terminal và kiểm tra contract CP1–CP3.
- CP3 bổ sung `model_error`/`max_steps`; 47/49 tests pass, còn đúng 2 tests nguồn
  thuộc CP5. Log tại [reports/cp3_tests.txt](reports/cp3_tests.txt).
- CP4 **giữ nguyên agent/prompt**, chạy eval baseline và phân tích evidence.
- **Chưa implement cải tiến CP5.** Dự kiến làm rõ xử lý partial failure, không bịa
  trạng thái khi thiếu dữ liệu, đọc tiếp incident khi cần và validation URL nguồn.
- Validation nguồn là yêu cầu riêng; chỉ kiểm tra URL không đủ ngăn lỗi H7 hoặc
  bảo đảm mọi claim đúng. Cần đánh giá từng vấn đề qua trace.

## 4. So sánh hai lần chạy

Mới hoàn tất lần 1; **chưa có kết quả trước–sau để kết luận cải tiến**.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---|
| Số case đã chấm | 22/22 | Chưa chạy |
| Điểm tổng | 84.27/100 | Chưa chạy |
| Điểm H7 | 40/100 | Chưa chạy |
| Model calls agent | 43 | Chưa chạy |
| Tool calls | 32 | Chưa chạy |
| Lượt judge | 22 | Chưa chạy |
| Token agent | 48,038 | Chưa chạy |
| Token judge | 44,196 | Chưa chạy |
| Tổng token | 92,234 | Chưa chạy |
| Chi phí API dịch vụ | Không phát sinh, Ollama local | Chưa chạy |

22 runs đều `completed`; không có `error`, `max_steps` hay case `unscored`.
Các lỗi H7/H1/H6/H3/A5/E2 vẫn là baseline, chưa được ghi nhận đã sửa.

Cấu hình cần giữ ở CP6: agent/judge cùng `status-agent-local` từ Qwen3 4B,
context 16384, output tối đa 2048, temperature 0, `max_steps=8`, `workers=1`,
snapshot và dataset `core` như lần 1. Model digest và SHA-256 baseline nằm tại
[reports/cp4_run_manifest.json](reports/cp4_run_manifest.json).

## 5. Giới hạn

- Điểm eval không tự động là điểm bài lab; `completed` không chứng minh answer đúng.
- Agent và judge cùng model local 4B nên có thể cùng sai hoặc thiên lệch.
  A5 nói năm 2025 chưa đến nhưng vẫn được 100 điểm là ví dụ cụ thể.
- Judge gọi URL shortlink có trong tool result là giả hoặc coi năm 2026 là dữ liệu
  không hợp lệ. Không có bằng chứng từ trace để kết luận như vậy; cần đối chiếu
  snapshot/expected theo đề, không tự sửa điểm hay fixtures.
- H1/H3/H6 được judge thô chấm cao nhưng kiểm tra code áp trần do thiếu thao tác
  điều tra. Cần đọc cả grade, mechanical checks, answer và trace.
- Snapshot không chứng minh trạng thái hiện tại. Tool chỉ tìm 50 incident gần nhất,
  trả tối đa 5 matches, chọn một số updates và cắt body tối đa 900 ký tự.
- Không có judge trace bị cắt trong lượt này, nhưng tool updates vẫn có thể bị cắt.
- Một lượt chạy mỗi phiên bản không chứng minh độ ổn định; temperature 0 không
  bảo đảm tuyệt đối cùng kết quả. Smoke E2 cũ không thay thế baseline đủ 22 case.
- Không có phí API dịch vụ trong lần local; chưa đo chi phí điện/phần cứng.
