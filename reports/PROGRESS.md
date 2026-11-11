# Báo cáo tiến độ theo checkpoint

Quy trình: hoàn thiện một CP → ghi bằng chứng → commit và push → báo người học
và dừng trước CP tiếp theo. Chỉ đánh dấu hoàn tất khi đã kiểm tra tiêu chí của CP.

| CP | Nội dung | Trạng thái |
|---|---|---|
| CP1 | Setup và khám phá tools | Hoàn tất kỹ thuật |
| CP2 | Agent loop | Hoàn tất kỹ thuật |
| CP3 | Xử lý lỗi và trace | Hoàn tất kỹ thuật |
| CP4 | Eval lần 1, đủ 22 case | Hoàn tất — 84.27/100, 22/22 case |
| CP5 | Phân tích và cải tiến | Hoàn tất — 56/56 tests chính pass |
| CP6 | Eval lần 2 và so sánh | Hoàn tất — 85.73/100, 22/22 case |
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


## CP3 — Xử lý lỗi và trace

Ngày kiểm tra: 11/11/2026 (GMT+7). Kiểm tra offline bằng fake provider và tools
snapshot; không gọi LLM, không cần key, không phát sinh phí API.

### Checklist đã kiểm tra

- [x] `max_steps` giới hạn đúng số lần gọi model, không đếm theo số tools.
- [x] JSON lỗi hoặc JSON không phải object trả observation `INVALID_ARGUMENTS`.
- [x] Model có thể nhận lỗi, sửa arguments và gọi lại thành công trong budget.
- [x] Tool không tồn tại trả `UNKNOWN_TOOL`; status provider sai trả `ValueError`.
- [x] Timeout và exception từ tool được ghi vào trace, gửi lại model bằng đúng ID.
- [x] Exception của LLM provider dừng run với `error`, giữ trace và usage đã có.
- [x] `finish == 'length'`, `content_filter` hoặc lý do bất thường không trả `completed`.
- [x] Không thực thi partial tool calls khi model dừng bất thường.
- [x] `finish == 'tool_calls'` mà không có calls trả `error`.
- [x] Trace có `event`; tool event có `step`, `name`, `arguments`, `result`.
- [x] Thêm event `model_error` và `max_steps` để thấy rõ nguyên nhân dừng.
- [x] Chạy toàn bộ unit tests: **49 tests, 47 pass, 2 fail chỉ thuộc validation nguồn CP5**.

Phần error handling đã có trong bản loop nền. Lượt CP3 bổ sung trace lý do dừng
và 8 tests mới trong `tests/test_cp3_errors.py`; các tests có nhiều subcases về
kiểu arguments và finish reason. Không thay đổi prompt, dataset, fixtures, grading
hoặc các tests validation nguồn có sẵn.

### Bằng chứng

- [cp3_tests.txt](cp3_tests.txt): log nguyên bản toàn bộ unit tests.
- [cp3_errors.json](cp3_errors.json): 7 kịch bản chạy thật qua `run_agent` với response
  fake dựng sẵn để kiểm tra cơ chế. **Đây không phải câu trả lời từ LLM local và
  không phải điểm eval.** File có observation được nhận ở lượt model tiếp theo.

| Kịch bản offline | Trạng thái run | Kết quả cần quan sát |
|---|---|---|
| JSON lỗi rồi sửa arguments | `completed` | Nhận `INVALID_ARGUMENTS`, sau đó tool thành công. |
| Tool không tồn tại | `completed` | Model nhận `UNKNOWN_TOOL` và trả lời giới hạn dữ liệu. |
| Status provider không hỗ trợ | `completed` | Model nhận `ValueError`. |
| Tool timeout | `completed` | Model nhận `TimeoutError`, báo không đủ dữ liệu. |
| Model bị cắt output (`length`) | `error` | Trace có `model_error`, không coi partial answer là hoàn tất. |
| Exception từ LLM provider | `error` | Trace có `provider_error`. |
| Hết một lượt gọi model | `max_steps` | Không gọi vượt budget; trace có `max_steps`. |

`completed` trong các kịch bản lỗi tool chỉ có nghĩa model kết thúc trả lời;
không có nghĩa tool thành công hay dịch vụ đang hoạt động. Final ở đây được
fake provider dựng sẵn để xác minh loop cho model cơ hội nhận và báo lỗi.

### Chạy lại

```bash
# Tests tập trung CP3: phải pass cả 8 tests.
PYTHONPATH=tests python3 -m unittest -v test_cp3_errors

# Toàn bộ tests: ở giai đoạn CP3 còn đúng hai lỗi validation nguồn bên dưới.
python3 -m unittest discover -s tests -v
```

Hai test chưa pass và sẽ xử lý ở CP5, sau baseline eval CP4:

- `EvidenceGateTests.test_missing_url_gets_revision_within_budget`
- `EvidenceGateTests.test_missing_url_at_budget_limit_is_not_completed`

Lệnh toàn bộ tests hiện trả exit code 1 vì hai failures trên; không ghi nhận là
“toàn bộ tests pass”. Đây là trạng thái cho phép tại CP3 theo `CHECKPOINTS.md`.
Offline tests kiểm tra cơ chế xử lý lỗi, không chứng minh model thật luôn trả lời
đúng, chống injection tốt hay ổn định. Các nhận định đó cần trace/eval ở CP4–CP6.

Kết luận: **CP3 hoàn tất về kiểm soát lỗi, giới hạn bước và trace**. Chưa chạy CP4
trong lượt này; chưa áp dụng cải tiến kiểm tra nguồn của CP5.


## CP4 — Eval lần 1

Ngày chạy: 11/11/2026 (GMT+7). Baseline sau CP3 tại commit `430f084`.

### Checklist đã kiểm tra

- [x] Chạy đủ 22 case E1–E6, A1–A8, H1–H8 trong một lượt bằng Ollama local.
- [x] Lưu kết quả gốc tại [eval_before.json](../eval_before.json).
- [x] `summary.score_0_100 = 84.27`, `scored_cases = 22`, `unscored_cases = 0`.
- [x] Đọc `grade.reason`, `grade.improvement`, `grade.mechanical`, answer và trace.
- [x] Lập danh sách lỗi có bằng chứng: H7, H1/H6, H3, A5, E2.
- [x] Ghi nhận judge chấm sai hoặc thiếu căn cứ; không sửa tay điểm.
- [x] Thống kê 43 model calls agent, 32 tool calls, 22 lượt judge, 92,234 token tổng.
- [x] Lưu cấu hình, model digest và SHA-256; xác nhận code/dataset/fixtures không đổi.
- [x] Cập nhật `NOTES.md` với case dự kiến ưu tiên H7 và số liệu baseline.

### Tóm tắt phát hiện

- H7 (40): tool Cloudflare timeout nhưng agent vẫn khẳng định operational.
- H3 (50): không gọi tool nhưng tuyên bố ID không tồn tại.
- H1/H6 (60): không đọc tiếp incident được dẫn chiếu; bị áp trần bởi code.
- A5 (100): agent nói năm 2025 chưa đến, judge vẫn cho điểm tối đa — lỗi ẩn sau điểm cao.
- E2 (88): suy diễn phạm vi và trạng thái từ danh sách incident, chưa đọc update.
- Tất cả runs đều `completed`, cho thấy trạng thái kết thúc không chứng minh answer đúng.

Báo cáo chi tiết, bảng 22 case và phân tích judge: [CP4_REPORT.md](CP4_REPORT.md).
Log: [cp4_eval.log](cp4_eval.log). Cấu hình/hashes: [cp4_run_manifest.json](cp4_run_manifest.json).

### Chạy lại hoặc đọc kết quả

```bash
# Đọc báo cáo đã có mà không gọi model:
python3 -c 'import json; r=json.load(open("eval_before.json")); print(r["summary"]); print(r["config"])'

# Nếu cần tái chạy để thử, ghi file khác để giữ nguyên mốc baseline:
source local/env.sh
python3 evals/run_evals.py --max-steps 8 --workers 1 --output eval_results_cp4_retry.json
```

Không phát sinh phí API dịch vụ trong lượt local; chưa đo chi phí điện/phần cứng.
Điểm judge chỉ là ước lượng; CP4 không chỉnh score theo nhận xét thủ công.

Kết luận: **CP4 hoàn tất về eval baseline và phân tích lỗi**. Chưa implement
cải tiến CP5; chưa tạo `eval_after.json` của CP6.


## CP5 — Phân tích và cải tiến

Ngày thực hiện: 11/11/2026 (GMT+7). Case chọn: H7, baseline 40/100.

### Checklist đã kiểm tra

- [x] Chọn lỗi thật từ full eval CP4, ghi evidence và giả thuyết nguyên nhân.
- [x] Thêm quy tắc bằng chứng, ngày chạy UTC và ngữ cảnh provider chưa xác minh.
- [x] Xóa ngữ cảnh lỗi sau khi retry status thành công; không đưa error prose lên system.
- [x] Thêm source gate: `validation_missing_source`, revision trong budget,
  hết budget không báo `completed`, không ép nguồn từ incident tool thất bại.
- [x] Toàn bộ 56 tests chính pass, gồm hai tests nguồn từng fail.
- [x] 3 tests tương thích bonus pass, không chạy eval bonus.
- [x] Kiểm tra riêng H7 bằng model local: prompt chung vẫn 40 điểm;
  thêm context từ observation đạt 95 điểm trong lượt thử sau.
- [x] Giữ nguyên `eval_before.json`, dataset, fixtures, grading, adapter và weights.
- [x] Cập nhật `NOTES.md`; ghi rõ chưa có so sánh full eval trước–sau.

Report: [CP5_REPORT.md](CP5_REPORT.md). Tests: [cp5_tests.txt](cp5_tests.txt).
Evidence local: [cp5_h7_prompt_only.json](cp5_h7_prompt_only.json),
[cp5_h7_check.json](cp5_h7_check.json). Gate offline: [cp5_source_checks.json](cp5_source_checks.json).
Manifest: [cp5_manifest.json](cp5_manifest.json).

Giới hạn: source gate chỉ kiểm tra sự hiện diện một URL đã quan sát, không chứng
minh factuality. Model có thể tiếp tục sai ở case khác; answer H7 mới còn suy diễn
số incident Actions từ truy vấn không lọc. Cần full eval CP6 trước kết luận tổng thể.

Kết luận: **CP5 hoàn tất về implement cải tiến và tests**. Dừng trước CP6;
chưa tạo `eval_after.json`, chưa có điểm tổng sau cải tiến.


## CP6 — Eval lần 2 và so sánh

Ngày hoàn tất: 11/11/2026 (GMT+7). Agent sau CP5 tại commit `60308c3`.

### Checklist đã kiểm tra

- [x] Chạy lại đủ 22 case; `eval_after.json` có 85.73/100, không có `unscored`.
- [x] Config giống `eval_before.json`; model digest, snapshot, dataset, adapter,
  grading, context, output limit, temperature, max steps, workers và timeout không đổi.
- [x] Xác nhận hash agent sau CP5 không thay đổi trong CP6.
- [x] So sánh 22 case, source revision, model calls, tool calls, token và lỗi còn lại.
- [x] H7 tăng 40 → 93, không suy Cloudflare operational từ timeout trong lượt này.
- [x] Ghi nhận H2 regression, lỗi điều tra H1/H3/H6/A6 và sai sót judge H4/A5.
- [x] Cập nhật `NOTES.md` đầy đủ kết quả trước–sau và giới hạn.
- [x] Thêm harness checkpoint không sửa hàm chạy/chấm gốc; 59/59 tests pass.

### Kết quả chính

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Điểm tổng | 84.27 | 85.73 |
| Điểm H7 | 40 | 93 |
| Model calls agent | 43 | 46 |
| Tool calls | 32 | 32 |
| Tổng token agent + judge | 92,234 | 124,513 |

10 case tăng, 8 giữ nguyên, 4 giảm; token tăng 35%. Không kết luận bản mới tốt hơn
toàn diện: H2 thiếu bước đọc incident, H1/H3/H6 chưa sửa, A6 tăng điểm nhưng thiếu
điều tra, H4 bị judge phạt nguồn không phù hợp với bài thơ.

Lượt đầu bị ngắt và tiến trình mất; đã chạy lại toàn bộ từ E1 và lưu từng case.
Không trộn điểm từ lượt cũ. Report: [CP6_REPORT.md](CP6_REPORT.md).
Kết quả: [eval_after.json](../eval_after.json). So sánh: [cp6_comparison.json](cp6_comparison.json).
Manifest: [cp6_run_manifest.json](cp6_run_manifest.json). Tests: [cp6_tests.txt](cp6_tests.txt).

Kết luận: **CP6 hoàn tất về eval và phân tích trước–sau**. Dừng trước CP7;
chưa demo cuối, merge main hoặc nộp link LMS trong lượt này.
