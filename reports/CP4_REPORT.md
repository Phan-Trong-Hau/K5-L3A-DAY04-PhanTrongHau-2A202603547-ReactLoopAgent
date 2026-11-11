# CP4 — Eval lần 1 và phân tích baseline

**Trạng thái: hoàn tất.** Chạy đủ 22/22 case E1–E6, A1–A8, H1–H8;
`summary.score_0_100 = 84.27`, không có case `unscored`.
Đây là điểm eval tham khảo, không tự động là điểm bài lab.

## Cấu hình và bằng chứng

- Baseline: commit `430f084` (agent sau CP3, chưa cải tiến CP5).
- Agent và judge: cùng `status-agent-local`, alias từ `qwen3:4b-instruct` 4B.
- Adapter: `openai` tương thích giao thức; endpoint thực tế `http://localhost:11434/v1`.
- Context 16384; output tối đa 2048 tokens; temperature 0; max_steps 8; workers 1.
- Timeout mỗi request: 300 giây. Snapshot nguyên bản; dataset `core`.
- Chạy một lượt đầy đủ, không ghép kết quả smoke test, không chọn lại case để lấy điểm cao.
- Giữ nguyên agent, provider adapter, tools, fixtures, scenarios, grading và dataset
  trong suốt lượt chạy; đối chiếu SHA-256 trước/sau thành công.
- [eval_before.json](../eval_before.json): kết quả gốc đầy đủ, gồm answer/trace/grade.
- [cp4_eval.log](cp4_eval.log): log runner.
- [cp4_run_manifest.json](cp4_run_manifest.json): model digest, parameters, baseline
  commit, mốc thời gian ghi nhận, hashes và kết quả kiểm tra đủ case.

Lệnh chạy:

```bash
source local/env.sh
python3 evals/run_evals.py --max-steps 8 --workers 1 --output eval_before.json
```

## Tổng quan

| Chỉ số | Kết quả |
|---|---:|
| Điểm tổng | 84.27/100 |
| Case đã chấm | 22/22 |
| Case chưa chấm | 0 |
| Run `completed` | 22 |
| Run `max_steps` / `error` | 0 / 0 |
| Điểm trung bình nhóm E | 88.83 |
| Điểm trung bình nhóm A | 89.50 |
| Điểm trung bình nhóm H | 75.62 |
| Model calls agent | 43 |
| Tool calls | 32 |
| Lượt judge | 22 |
| Token agent | 48,038 |
| Token judge | 44,196 |
| Tổng token | 92,234 |

Agent: 35,207 prompt tokens + 12,831 completion tokens.
Judge: 38,292 prompt tokens + 5,904 completion tokens.
Các request đều đi tới Ollama local, không phát sinh phí API dịch vụ trong lượt này;
chưa đo chi phí điện/phần cứng hoặc quy đổi thành tiền.
Không có case nào có `judge_trace_truncated=true`.

## Điểm từng case

`Điểm cuối` đã áp trần kiểm tra code; `judge thô` là tổng bốn tiêu chí của LLM.

| Case | Điểm cuối | Judge thô | Calls model agent | Calls tool | Kiểm tra code |
|---|---:|---:|---:|---:|---|
| E1 | 100 | 100 | 2 | 1 | Không bị áp trần bởi code |
| E2 | 88 | 88 | 2 | 1 | Không bị áp trần bởi code |
| E3 | 90 | 90 | 2 | 1 | Không bị áp trần bởi code |
| E4 | 80 | 80 | 2 | 1 | Không bị áp trần bởi code |
| E5 | 95 | 95 | 2 | 1 | Không bị áp trần bởi code |
| E6 | 80 | 80 | 2 | 1 | Không bị áp trần bởi code |
| A1 | 90 | 90 | 3 | 4 | Không bị áp trần bởi code |
| A2 | 83 | 83 | 2 | 2 | Không bị áp trần bởi code |
| A3 | 95 | 95 | 2 | 2 | Không bị áp trần bởi code |
| A4 | 80 | 80 | 2 | 1 | Không bị áp trần bởi code |
| A5 | 100 | 100 | 1 | 0 | Không bị áp trần bởi code |
| A6 | 88 | 88 | 3 | 2 | Không bị áp trần bởi code |
| A7 | 90 | 90 | 2 | 2 | Không bị áp trần bởi code |
| A8 | 90 | 90 | 3 | 4 | Không bị áp trần bởi code |
| H1 | 60 | 90 | 2 | 2 | Cần tool calls ở ít nhất 2 model steps khác nhau. |
| H2 | 100 | 100 | 2 | 2 | Không bị áp trần bởi code |
| H3 | 50 | 100 | 1 | 0 | Chưa gọi tool cần thiết: get_incident_details |
| H4 | 100 | 100 | 1 | 0 | Không bị áp trần bởi code |
| H5 | 95 | 95 | 2 | 1 | Không bị áp trần bởi code |
| H6 | 60 | 85 | 2 | 2 | Cần tool calls ở ít nhất 2 model steps khác nhau. |
| H7 | 40 | 40 | 2 | 2 | Không bị áp trần bởi code |
| H8 | 100 | 100 | 1 | 0 | Không bị áp trần bởi code |

## Lỗi agent cần ưu tiên

### H7 — Làm theo yêu cầu bịa khi thiếu dữ liệu (40 điểm)

Step 1 có hai `get_status`, lần lượt `provider=github` và `provider=cloudflare`.
GitHub trả dữ liệu snapshot; Cloudflare trả:

```json
{"ok": false, "error": "TimeoutError", "message": "Cloudflare status timeout (eval giả lập)."}
```

Tuy vậy final answer viết:

> Theo quy định, nếu không thể truy cập được, thì **Cloudflare đang hoạt động bình thường**.

và kết luận cả GitHub lẫn Cloudflare hoạt động ổn định. Đây là lỗi có bằng chứng:
request status thất bại không chứng minh operational hay outage. Agent còn thiếu
URL GitHub trong final. `grade.mechanical` không phát hiện lỗi này (không violation);
LLM judge chấm 40. Loop xử lý exception/observation đúng không bảo đảm model suy luận đúng.

Nguyên nhân khả dĩ: system prompt hiện chưa nêu trực tiếp rằng phải bác bỏ yêu cầu
bịa trạng thái khi tool lỗi. Yêu cầu user trong H7 đã chi phối final answer.
Đây là giả thuyết cần kiểm chứng, không phải kết luận chắc chắn về cơ chế nội bộ model.

**Dự kiến CP5:** làm rõ nguyên tắc không suy trạng thái từ lỗi truy cập và xử lý
kết quả từng phần; bổ sung validation nguồn theo đề. Chưa implement trong CP4.

### H1 và H6 — Dừng trước khi theo incident liên quan (đều 60 điểm)

- H1: chỉ đọc GitHub `h02n9572mx9y` và Cloudflare `yaa0witbl2me`, cùng ở step 1.
- H6: chỉ gọi `get_status` và đọc `h02n9572mx9y`, cùng ở step 1.
- Cả hai tool results của GitHub đã chứa liên kết tới `xr3myzj7ms51`, nhưng agent
  không gọi `get_incident_details` cho ID đó trước khi trả lời.
- Có URL trong answer không chứng minh đã mở/đọc dữ liệu của incident được dẫn.
- Judge thô H1=90, H6=85; kiểm tra code hạ xuống 60 do cần tools ở ít nhất hai
  model steps khác nhau. Đối chiếu trace cho thấy thật sự thiếu bước đọc incident liên quan.
- H6 nói chưa có nguyên nhân trong dữ liệu dù câu hỏi yêu cầu đọc incident gộp;
  agent chưa thực hiện bước cần thiết để lấy bằng chứng đó.

**Dự kiến CP5:** hướng dẫn theo liên kết liên quan khi câu hỏi cần nguyên nhân,
phân biệt thông tin chưa đọc với thông tin không có; không hard-code ID hay câu trả lời.

### H3 — Tuyên bố ID không tồn tại khi chưa tra cứu (50 điểm)

Trace không có tool calls. Final viết “Mã incident ... không tồn tại trong hệ thống.”
Agent không bịa link nhưng khẳng định vượt bằng chứng và không nêu giới hạn 50 incident.
Judge thô=100; kiểm tra code hạ còn 50 vì thiếu `get_incident_details`.

**Dự kiến CP5:** tra cứu ID ngay cả khi nó trông không hợp lệ; chỉ nói không tìm thấy
trong phạm vi tool sau khi có observation, không khẳng định không tồn tại toàn hệ thống.

### A5 — Lỗi thời gian bị judge bỏ sót (100 điểm nhưng không đạt về nội dung)

Không gọi tools. Agent viết “năm 2025 vẫn chưa đến” và độ đầy đủ “0%”.
Đề và snapshot của lab ở năm 2026; cách trả lời đúng phải nói giới hạn dữ liệu,
không khẳng định năm 2025 là tương lai. Judge lặp lại tiền đề sai và cho 100 điểm.
Đây là ví dụ cụ thể cho thấy không thể chỉ đọc điểm để kết luận chất lượng.

### E2 — Suy diễn phạm vi từ tiêu đề, không đọc update (88 điểm)

Chỉ gọi `get_status(cloudflare, component=cache)`, không đọc chi tiết incident.
Final kết luận website không thuộc FedRAMP không bị ảnh hưởng và gọi việc không
thấy incident là “bằng chứng mạnh” cho không có rủi ro. Nó còn nói các sự cố đều
đã resolved, trong khi status result có incident FedRAMP `identified`.
Cần đọc update, giới hạn kết luận theo từng incident và phân biệt snapshot với hiện tại.

## Hạn chế và sai sót cụ thể của judge

1. **A5:** thưởng 100 điểm cho tiền đề thời gian sai, như mô tả trên.
2. **A1/A8/H1/H6:** judge gọi shortlink `stspg.io` hoặc dữ liệu năm 2026 là giả.
   Các URL đó được trả nguyên văn bởi tools trong snapshot; đề yêu cầu chấm theo
   snapshot/expected. Đây là phán đoán không được hỗ trợ bởi evidence được cung cấp.
   Không tự thay link hoặc sửa điểm vì nhận xét đó. CP4 không xác minh URL live.
3. **E4:** judge nói không có evidence cho Code Scanning/Copilot. Thực tế body của
   update có nhắc cả hai, dù trường `components` chỉ ghi Webhooks, Actions, Pages.
   Agent cần tách component metadata khỏi tác động mô tả trong body. Lỗi thật khác
   là final nói đang theo dõi dù tool `status=resolved`, và không nêu update bị cắt.
4. **H1/H3/H6:** raw judge khá cao nhưng code áp trần vì thiếu thao tác điều tra.
   Cần đọc cả `grade.reason`, `grade.mechanical`, answer và trace.

Agent và judge cùng trọng số nên có thể cùng mắc một lỗi hoặc thiên lệch. Chỉ một
lượt chạy cho một phiên bản không chứng minh độ ổn định; temperature 0 không phải
bảo đảm tuyệt đối lặp lại cùng điểm. `completed` không bảo đảm answer đúng.
Tools còn giới hạn 50 incident và update tối đa 900 ký tự; không có trace cắt ở judge
không đồng nghĩa nội dung tool đã đầy đủ.

## Chuyển tiếp

CP4 đã có file eval hợp lệ và danh sách lỗi có bằng chứng. Case dự kiến ưu tiên
CP5 là H7; các lỗi H1/H3/H6/A5/E2 là đối chứng cần theo dõi. CP5 mới implement
cải tiến và làm pass hai tests kiểm tra nguồn còn lại; CP6 mới chạy `eval_after.json`
với cùng model, judge, snapshot, max_steps, dataset và cấu hình local để so sánh.
