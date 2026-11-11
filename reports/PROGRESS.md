# Báo cáo tiến độ theo checkpoint

Quy trình: hoàn thiện một CP → ghi bằng chứng → commit và push → báo người học
và dừng trước CP tiếp theo. Chỉ đánh dấu hoàn tất khi đã kiểm tra tiêu chí của CP.

| CP | Nội dung | Trạng thái |
|---|---|---|
| CP1 | Setup và khám phá tools | Hoàn tất kỹ thuật |
| CP2 | Agent loop | Hoàn tất kỹ thuật |
| CP3 | Xử lý lỗi và trace | Có code nền, chưa chốt riêng CP |
| CP4 | Eval lần 1, đủ 22 case | Chưa hoàn tất |
| CP5 | Phân tích và cải tiến | Chưa hoàn tất |
| CP6 | Eval lần 2 và so sánh | Chưa thực hiện |
| CP7 | Demo và nộp bài | Chưa thực hiện |

## CP1 — Setup và khám phá tools

Ngày kiểm tra: 11/11/2026 (GMT+7).

### Checklist đã kiểm tra

- [x] Repo cá nhân đúng mẫu tên L3A; remote thuộc tài khoản `Phan-Trong-Hau`.
- [x] Branch `feat/local-status-agent` đã push thành công ở các commit trước.
- [x] Python 3.12.3 đáp ứng yêu cầu Python 3.10+; không cần package bổ sung.
- [x] Ollama có model `qwen3:4b-instruct` và alias `status-agent-local:latest`.
- [x] Cấu hình provider/model/endpoint local có trong `local/env.sh`.
- [x] Model local gọi được tool: smoke E2 kết thúc `completed`, có `get_status`.
- [x] Gọi trực tiếp `get_status('github', 'Actions')` thành công.
- [x] Gọi trực tiếp `get_incident_details('cloudflare', 'wp49bp8bqo6c')` thành công.
- [x] Lưu JSON đầy đủ làm bằng chứng trong [cp1_tools.json](cp1_tools.json).

Theo yêu cầu dùng local của người học, cấu hình dùng adapter `openai` với endpoint
`http://localhost:11434/v1`. `OPENAI_API_KEY=local` chỉ là giá trị giả để adapter
hoạt động; không dùng API key cloud hay gọi OpenAI cho lần chạy này.

### Kết quả khám phá tools

| Tool | Kết quả quan sát trên snapshot |
|---|---|
| `get_status('github', 'Actions')` | Overall `none` / `All Systems Operational`; trả 5 incident gần đây khớp chuỗi. |
| `get_incident_details('cloudflare', 'wp49bp8bqo6c')` | Incident `Fedramp Customers have Delayed Purges`, trạng thái `identified`; trả 2/2 updates. |

Update của incident Cloudflare có câu `Non-fedramp customers are not impacted by this issue.`
Đây là phạm vi của incident đó, không phải kết luận về mọi lỗi của một website.

### Những điểm cần hiểu trước CP2

- `get_status`: trả trạng thái tổng quan, component khớp và tối đa 5 incident;
  có `captured_at` và nguồn. Incident `resolved` là lịch sử, không có nghĩa đang lỗi.
- Tìm kiếm là khớp chuỗi trong 50 incident gần nhất. Từ khóa không khớp ngôn ngữ,
  tên sản phẩm hoặc incident cũ ngoài tập dữ liệu có thể làm kết quả rỗng.
  Vì vậy **không tìm thấy không chứng minh không có sự cố**.
- `get_incident_details`: đọc theo ID để biết timeline, phạm vi, trạng thái và URL
  incident; xem `updates_total` và `truncated` để biết giới hạn dữ liệu trả về.
- Overall status không chứng minh tất cả component, khu vực hay khách hàng đều bị ảnh hưởng.
- Snapshot là dữ liệu lưu sẵn; không dùng để kết luận trạng thái thực tế hôm nay.

Phần hiểu bài ở trên là hướng dẫn để người học tự đối chiếu, không phải tuyên bố
đã kiểm tra kiến thức cá nhân qua demo/hỏi đáp.

### Tự chạy lại

Chạy từ thư mục gốc repo; hai lệnh này không cần LLM hoặc API key:

```bash
python3 -c 'import json; from status_tools import StatusTools; print(json.dumps(StatusTools().get_status("github", "Actions"), ensure_ascii=False, indent=2))'
python3 -c 'import json; from status_tools import StatusTools; print(json.dumps(StatusTools().get_incident_details("cloudflare", "wp49bp8bqo6c"), ensure_ascii=False, indent=2))'
```

Kết luận tại thời điểm chốt CP1: **CP1 hoàn tất về setup và kiểm tra tools**.


## CP2 — Agent loop

Ngày kiểm tra: 11/11/2026 (GMT+7). Model `status-agent-local` qua Ollama;
`run.py` mặc định snapshot, `max_steps=6`. Không chạy LLM judge trong kiểm tra CP2.

### Checklist đã kiểm tra

- [x] `run_agent(question, provider, tools, max_steps=6)` trả `status`, `answer`, `trace`, `usage`.
- [x] Khởi tạo hội thoại system + user, truyền schemas vào `provider.complete`.
- [x] Giữ nguyên assistant message, kể cả content và toàn bộ tool calls.
- [x] Parse arguments JSON rồi gọi `tools.execute(name, arguments)`.
- [x] Trả đúng `tool_call_id`, content JSON và role `tool` cho từng observation.
- [x] Xử lý toàn bộ calls của một response trước lần gọi model tiếp theo.
- [x] Chỉ hoàn tất khi `finish == 'stop'` và không còn calls.
- [x] Lưu usage theo mỗi model call, trace tool đúng các key yêu cầu.
- [x] Chạy câu hỏi GitHub Actions theo checkpoint và nhận `completed`.
- [x] 5/5 tests tập trung cho CP2 pass; lưu log trong [cp2_tests.txt](cp2_tests.txt).

Code loop đã có từ commit nền `df52938`; lượt CP2 rà soát contract, sửa mô tả
module còn ghi “chưa có lời giải”, bổ sung chú thích và 2 tests hội thoại/usage.
Không đổi prompt hay thêm validation nguồn trong lượt này.

### Bằng chứng chạy model local

Lệnh thực tế:

```bash
source local/env.sh
python3 run.py 'GitHub Actions hiện có sự cố không? Hãy kiểm tra incident gần đây.' > reports/cp2_github_actions.json
```

Kết quả gốc: [cp2_github_actions.json](cp2_github_actions.json).

- `status`: `completed`.
- Step 1: model chọn `get_status` với `{"provider":"github"}`.
- Tool trả overall `none` / `All Systems Operational`, cùng incident trong snapshot.
- Step 2: model trả final, phân biệt các incident được liệt kê là `resolved`.
- 2 model calls, 1 tool call; tổng token agent: 1575.
- Không có điểm eval: đây là bài kiểm tra luồng CP2, chưa phải CP4.

### Vì sao phải giữ assistant message và tool-call IDs?

Assistant message ghi lại các lời gọi mà model đã yêu cầu. Mỗi tool result phải
tham chiếu ID tương ứng để provider ghép đúng observation với lời gọi, nhất là
khi model yêu cầu nhiều tools cùng lúc. Bỏ assistant message, đổi ID hoặc bỏ sót
một result có thể làm request tiếp theo không hợp lệ hoặc khiến model thiếu dữ liệu.

Tests kiểm tra hội thoại thực sự nhận bởi lần gọi model tiếp theo: thứ tự
`system → user → assistant → tool → tool`, nội dung assistant được giữ nguyên,
hai kết quả có ID `github-id` và `cloudflare-id` đúng provider. Một test khác
kiểm tra luồng `get_status → get_incident_details → final` trên snapshot.

Chạy lại tests CP2, không cần model/API key:

```bash
PYTHONPATH=tests python3 -m unittest -v test_lab.LoopTests.test_tool_result_is_returned_with_id test_lab.LoopTests.test_multiple_tool_calls test_lab.FullTrajectoryTests.test_two_tools_and_final_with_real_snapshot test_cp2_contract
```

### Giới hạn còn lại

- `completed` chỉ xác nhận loop dừng bình thường, không khẳng định nội dung đúng.
- Answer local dùng “hiện tại” dù dữ liệu là snapshot; chưa đọc timeline incident.
  Cần giữ lỗi này để phân tích và cải tiến tại CP5 sau baseline eval CP4.
- Chưa chốt CP3 trong lượt này; chưa chạy bộ eval 22 case hay cải tiến kiểm tra nguồn.

Kết luận: **CP2 hoàn tất về agent loop và kiểm tra chạy model local**.
