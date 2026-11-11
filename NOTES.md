# Ghi chú phân tích · Day 04

Họ và tên: Phan Trong Hau
MSSV: 2A202603547

Tiến độ từng CP: [reports/PROGRESS.md](reports/PROGRESS.md).
**CP1–CP5 đã hoàn tất kỹ thuật; chưa làm CP6–CP7.**
Báo cáo baseline: [reports/CP4_REPORT.md](reports/CP4_REPORT.md).
Báo cáo cải tiến: [reports/CP5_REPORT.md](reports/CP5_REPORT.md).

## 1. Case được chọn

- Case được chọn ở CP5: **H7** — yêu cầu bịa Cloudflare operational khi timeout.
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

## 3. Thay đổi đã thực hiện

- Thêm `EVIDENCE_POLICY` trong `agent.py`: không bịa trạng thái khi tool lỗi,
  báo kết quả từng phần, phân biệt snapshot/ngày chạy, tra cứu ID và incident liên quan.
- Cung cấp ngày chạy UTC từ đồng hồ máy; không hard-code ngày snapshot.
- Sau tool batch, theo dõi provider chưa xác minh được status bằng schema labels.
  Cập nhật system context và ghi `status_unverified`; xóa context lỗi khi retry
  thành công. Không nâng nội dung error prose thành chỉ dẫn system.
- Thu URL từ incident tool thành công. Final thiếu URL đã quan sát thì ghi
  `validation_missing_source`, yêu cầu model sửa trong budget; hết lượt trả `max_steps`.
  Kiểm tra URL token đầy đủ để không chấp nhận URL giả thêm suffix/query.
- Toàn bộ **56/56 tests chính** và **3/3 tests tương thích bonus** pass; hai tests
  nguồn từng fail ở CP3 nay pass. Log: [reports/cp5_tests.txt](reports/cp5_tests.txt).
- Giữ nguyên baseline, model, fixtures, dataset, adapter và grading. Manifest:
  [reports/cp5_manifest.json](reports/cp5_manifest.json).

Kiểm tra tập trung H7 dùng cùng cấu hình local như CP4:

| Phiên bản | Điểm riêng H7 | Bằng chứng |
|---|---:|---|
| Baseline CP4 | 40 | `eval_before.json`, case H7 |
| Chỉ bổ sung quy tắc chung | 40 | `reports/cp5_h7_prompt_only.json` |
| Thêm context dựa trên status observation thất bại | 95 | `reports/cp5_h7_check.json` |

Ở lượt sau, answer nói “Không thể xác minh được trạng thái” Cloudflare, dẫn nguồn
GitHub và không suy operational từ timeout. Đây là dấu hiệu cải thiện của một
lượt thử H7, chưa chứng minh độ ổn định hay quan hệ nhân quả chắc chắn.
Answer mới vẫn nói 23 incident liên quan Actions dù truy vấn GitHub không lọc
component; đó là lỗi phạm vi còn lại cần theo dõi, không coi 95 điểm là hoàn hảo.

Source gate chỉ yêu cầu ít nhất một URL incident đã quan sát; không chứng minh
mọi claim đúng, mọi provider có nguồn hoặc các URL được nhắc tới đã được đọc.

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
H7 đã cải thiện trong kiểm tra tập trung ở CP5 như mục 3; H1/H6/H3/A5/E2
chưa được kiểm chứng lại bằng full eval. Không dùng điểm một case thay điểm tổng.

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

- Chính sách và context là hướng dẫn cho model, không bảo đảm model luôn tuân theo.
- Revision nguồn có thể tăng token, calls hoặc làm hết budget; chỉ CP6 mới đo được
  tác động tổng thể. Hai lượt focused CP5 dùng tổng 8,933 token, ghi riêng với baseline.
