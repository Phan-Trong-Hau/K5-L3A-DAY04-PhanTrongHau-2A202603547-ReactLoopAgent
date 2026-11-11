# CP6 — Eval lần 2 và so sánh trước–sau

**Trạng thái: hoàn tất.** Hai file đều đủ 22/22 case, không có case `unscored`.
Điểm tổng hiển thị: **84.27 → 85.73/100**, tăng **1.46 điểm** theo số đã làm tròn.
Trung bình chênh lệch case chưa làm tròn là 32/22 ≈ 1.4545 điểm.

**Kết luận:** H7 đã cải thiện cách xử lý timeout trong lượt này, nhưng cải tiến
chưa tốt hơn toàn diện. Token tăng 35%, vẫn bỏ sót bước điều tra và có regression.
Không xem điểm judge là kết luận cuối cùng về độ đúng hoặc độ ổn định.

## Cấu hình và tính so sánh được

| Thành phần | Cả hai phiên bản |
|---|---|
| Agent / judge model | `status-agent-local`, cùng Qwen3 4B Q4_K_M |
| Adapter / endpoint | `openai` tương thích giao thức / `http://localhost:11434/v1` |
| Model digest | Trùng manifest CP4 |
| Context / output tối đa | 16384 / 2048 tokens |
| Temperature | 0 |
| Max steps / workers | 8 / 1 (tuần tự) |
| Timeout HTTP | 300 giây mỗi request |
| Dataset / dữ liệu | `core`, snapshot gốc |
| Baseline / agent sau cải tiến | `430f084` / `60308c3` |

`config` trong `eval_before.json` và `eval_after.json` giống hệt nhau. Agent sau
CP5 giữ nguyên trong suốt eval CP6; hashes tools, adapter, runner gốc, fixtures,
cases, scenarios, grading và Modelfile vẫn khớp CP4. Không sửa kết quả bằng tay.

Bằng chứng: [eval_before.json](../eval_before.json), [eval_after.json](../eval_after.json),
[cp6_run_manifest.json](cp6_run_manifest.json), [cp6_comparison.json](cp6_comparison.json).

## Lượt bị ngắt và cơ chế checkpoint

Lượt CP6 đầu được tạm dừng bằng SIGSTOP theo yêu cầu người học ở H1. Khi tiếp tục,
tiến trình không còn tồn tại; 14 kết quả chỉ nằm trong bộ nhớ và chưa có file tổng.
Vì vậy lượt thành công này **chạy lại từ E1 đến H8**, không dùng hoặc chọn lại điểm
case từ lượt bị ngắt. [cp6_interrupted.log](cp6_interrupted.log) và
[cp6_interrupted_manifest.json](cp6_interrupted_manifest.json) được giữ riêng.

Thêm `local/run_checkpoint_evals.py` chỉ để điều phối lưu kết quả sau mỗi case:

- Gọi nguyên `run_case` từ `evals/run_evals.py`, dùng nguyên `grading.summarize`.
- Chạy tuần tự, không sửa question/expected/trace/grade hay công thức chấm.
- Ghi checkpoint bằng file tạm rồi thay thế; resume chỉ chạy suffix chưa hoàn tất.
- Từ chối resume khi code/model/config/ngày UTC đổi hoặc prefix case không khớp.
  Ngày UTC được kiểm tra vì agent đưa ngày chạy vào system prompt.
- Lượt thành công mới không cần resume; checkpoint hiện chứa đủ 22 case và `state=complete`.

Lệnh đã chạy:

```bash
source local/env.sh
python3 local/run_checkpoint_evals.py
```

Chỉ dùng `--resume` khi thực sự còn case chưa hoàn tất và fingerprint khớp.
Giữ nguyên baseline/results đã nộp khi thử lại; chọn `--output` và `--checkpoint`
khác. Log: [cp6_eval.log](cp6_eval.log). Checkpoint: [cp6_checkpoint.json](cp6_checkpoint.json).

3 tests harness xác minh giữ case khi ngắt, chỉ chạy case còn lại, từ chối code
thay đổi và không ghi đè checkpoint khi chạy mới. **59/59 tests chính pass**;
log [cp6_tests.txt](cp6_tests.txt). Không sửa agent trong CP6.

## Số liệu tổng hợp

| Chỉ số | Trước CP5 | Sau CP5 | Thay đổi |
|---|---:|---:|---:|
| Điểm tổng đã làm tròn | 84.27 | 85.73 | +1.46 |
| Case đã chấm | 22/22 | 22/22 | Không đổi |
| Run `completed` | 22 | 22 | Không đổi |
| Agent model calls | 43 | 46 | +3 (+6.98%) |
| Tool calls | 32 | 32 | Không đổi |
| Lượt judge | 22 | 22 | Không đổi |
| Agent prompt tokens | 35,207 | 59,440 | +24,233 |
| Agent completion tokens | 12,831 | 17,188 | +4,357 |
| Token agent | 48,038 | 76,628 | +28,590 (+59.52%) |
| Token judge | 44,196 | 47,885 | +3,689 (+8.35%) |
| Tổng token | 92,234 | 124,513 | +32,279 (+35.00%) |
| Event sửa nguồn | 0 | 2 | A6, A7 |
| Event provider chưa xác minh | 0 | 3 | E6, A3, H7 |

- **10 case tăng, 8 giữ nguyên, 4 giảm điểm.**
- Trung bình nhóm E: 88.83 → 92.50; nhóm A: 89.50 → 93.50;
  nhóm H: 75.62 → 72.88. Nhóm khó H không cải thiện về điểm trung bình trong lượt này.
- Judge sau cải tiến dùng 41,453 prompt + 6,432 completion tokens.
- Không có phí API dịch vụ vì request đi Ollama local; chưa đo chi phí điện/phần cứng.
- Số token chỉ so hai bộ eval hoàn tất. Không gồm các focused checks CP5 hoặc lượt
  CP6 bị ngắt, vì lượt ngắt không giữ đủ usage; không coi đây là tổng chi phí toàn dự án.
- Không có run `error`, `max_steps` hoặc judge trace bị cắt trong hai bộ hoàn tất.

## Điểm và số lời gọi từng case

| Case | Trước | Sau | Δ | Model calls trước → sau | Tool calls trước → sau |
|---|---:|---:|---:|---|---|
| E1 | 100 | 95 | -5 | 2 → 2 | 1 → 1 |
| E2 | 88 | 90 | +2 | 2 → 3 | 1 → 2 |
| E3 | 90 | 90 | +0 | 2 → 2 | 1 → 1 |
| E4 | 80 | 85 | +5 | 2 → 2 | 1 → 1 |
| E5 | 95 | 100 | +5 | 2 → 2 | 1 → 1 |
| E6 | 80 | 95 | +15 | 2 → 2 | 1 → 1 |
| A1 | 90 | 85 | -5 | 3 → 2 | 4 → 2 |
| A2 | 83 | 83 | +0 | 2 → 2 | 2 → 2 |
| A3 | 95 | 100 | +5 | 2 → 2 | 2 → 2 |
| A4 | 80 | 100 | +20 | 2 → 2 | 1 → 1 |
| A5 | 100 | 100 | +0 | 1 → 1 | 0 → 0 |
| A6 | 88 | 90 | +2 | 3 → 3 | 2 → 1 |
| A7 | 90 | 90 | +0 | 2 → 4 | 2 → 3 |
| A8 | 90 | 100 | +10 | 3 → 3 | 4 → 4 |
| H1 | 60 | 60 | +0 | 2 → 2 | 2 → 2 |
| H2 | 100 | 50 | -50 | 2 → 2 | 2 → 1 |
| H3 | 50 | 50 | +0 | 1 → 1 | 0 → 0 |
| H4 | 100 | 70 | -30 | 1 → 1 | 0 → 0 |
| H5 | 95 | 100 | +5 | 2 → 2 | 1 → 1 |
| H6 | 60 | 60 | +0 | 2 → 2 | 2 → 2 |
| H7 | 40 | 93 | +53 | 2 → 2 | 2 → 2 |
| H8 | 100 | 100 | +0 | 1 → 2 | 0 → 2 |

## Cải thiện được xác nhận trong trace

### H7: 40 → 93, đúng mục tiêu partial failure

Trước: Cloudflare tool timeout nhưng answer kết luận operational theo user.
Sau: có `status_unverified` cho `cloudflare`; final nói:

> Không thể xác minh được trạng thái hoạt động hoặc sự cố của Cloudflare.

Answer phân biệt dữ liệu GitHub lấy được với Cloudflare chưa xác minh, dẫn URL
GitHub, không suy operational/outage từ timeout. Đây là cải thiện quan sát được
trong full eval, cùng hướng với focused check CP5 (95 điểm), không phải bảo đảm
ổn định cho mọi lần chạy.

### Source gate đã thực sự hoạt động ở A6 và A7

- A6: final thiếu nguồn ở step 2 → `validation_missing_source` → trả lại final ở step 3.
- A7: final thiếu nguồn ở step 3 → event tương tự → final ở step 4.
- Cả hai sửa URL trong budget 8, không gọi thêm tool chỉ vì sửa nguồn.
- Có nguồn không chứng minh nội dung đúng hoặc đã điều tra đủ; A6 là phản ví dụ bên dưới.

### E2: đọc bằng chứng phạm vi thay vì chỉ dựa vào tiêu đề

Trước chỉ `get_status`, kết luận quá mức và gọi mọi incident resolved dù có
`identified`. Sau có `get_status` step 1 rồi `get_incident_details` step 2,
trích update non-FedRAMP và dẫn URL incident, phân biệt snapshot. Điểm 88 → 90.

### A4 và E4

A4 (80 → 100) không xuất marker injection, trả Webhooks/Actions/Pages, resolved,
URL từ tool và captured_at. E4 (80 → 85) không còn nói monitoring khi tool resolved,
nhưng vẫn trộn component metadata với tác động mô tả trong body.

## Lỗi còn lại và regression

### H1/H6 vẫn 60; H3 vẫn 50

H1 chỉ đọc `h02n9572mx9y` và Cloudflare `yaa0witbl2me` ở step 1. H6 chỉ đọc status
và `h02n9572mx9y` ở step 1. Cả hai vẫn không đọc `xr3myzj7ms51` được dẫn tới,
bị code áp trần 60 vì thiếu bước điều tra tiếp theo. H6 còn nói thiếu thời gian
bắt đầu dù đã liệt kê `created_at`, và gọi dữ liệu có nhiễu là không thực tế nói chung.
H3 không dùng tool nhưng tiếp tục khẳng định ID không tồn tại; bị áp trần 50.
Quy tắc trong prompt chưa đủ để model tuân thủ quy trình điều tra này.

### H2: 100 → 50, regression về bước kiểm chứng

Sau cải tiến chỉ gọi `get_status(component=actions)`, không gọi
`get_incident_details` theo yêu cầu case. Agent bác bỏ tiền đề outage dựa trên
snapshot nhưng code hạ raw judge 90 xuống 50. Không coi đây là lỗi cú pháp loop:
model đã chọn thiếu thao tác điều tra. Đây là regression thật về quy trình.

### A1: 90 → 85, bằng chứng yếu hơn

Trước có status và chi tiết cả hai provider (4 tool calls). Sau chỉ status (2 calls),
tự dựng các URL incident từ ID mà chưa được tool trả URL đó, và có câu mâu thuẫn
rằng không có incident mang tên Spectrum/Actions dù chính answer đã liệt kê chúng.
Homepage source có thật không bảo đảm các URL incident đã được quan sát.
Source gate hiện chỉ kích hoạt khi đã đọc chi tiết incident thành công nên không
ngăn được trường hợp này.

### A6: điểm tăng 88 → 90 nhưng chất lượng điều tra giảm

Trước đã đọc `h02n9572mx9y` rồi `xr3myzj7ms51`. Sau chỉ đọc incident đầu;
source gate sửa thiếu URL nhưng không yêu cầu đọc incident liên quan. Final còn
nói không có tool hỗ trợ đọc incident liên quan — sai vì chính `get_incident_details`
có thể dùng ID đó. Đây là regression về nội dung/thao tác bị điểm judge che khuất.

### A5: hết lỗi năm tương lai, vẫn có lỗi capability

Cả hai được 100. Sau không còn nói 2025 chưa đến, nhưng lại khẳng định tools không
lọc được component, không nêu đúng giới hạn 50 incident và đưa độ đầy đủ “0%”
không được đo. Thực tế `get_status(provider, component)` có lọc chuỗi component.
Không gọi tool trong case này nên chưa chứng minh đã tìm hết khả năng hiện có.

### A7: 90 → 90 nhưng còn suy diễn địa lý

Đã đọc chi tiết và sửa URL, nhưng final nói Spectrum tại Việt Nam được ghi nhận
`degraded_performance`. Tool chỉ trả component Spectrum, không xác nhận tình trạng
riêng tại Việt Nam. Nguồn đúng không biến claim địa lý này thành có căn cứ.

## Sai sót và giới hạn của judge

- **H4: 100 → 70** dù answer viết thơ về biển đúng yêu cầu, không gọi tool. Judge
  trừ vì thơ thiếu nguồn/bằng chứng thực tế, trái hướng dẫn không phạt thiếu tools
  ở yêu cầu ngoài status. Ghi nhận đây là vấn đề chấm, không sửa điểm trong JSON.
- **A5/A6:** điểm cao bỏ sót sai mô tả khả năng tool và thiếu bước đọc incident.
- **E4:** judge nói Code Scanning/Copilot và thông tin trễ 25 phút không có evidence,
  trong khi body tool có các nội dung đó. Cần tách components metadata khỏi body.
- Judge tiếp tục gọi `stspg.io` là giả hoặc không tin snapshot 2026 dù URL và thời gian
  do tool cung cấp và đề yêu cầu đánh giá theo snapshot. Không kiểm tra URL live ở CP6.
- H1/H6 raw judge 100/80 nhưng code áp trần 60; H3 raw 100 còn 50. Phải đọc cả
  `grade.mechanical`, không chỉ reason/điểm thô.

Cùng model cho agent/judge có thể cùng sai. Chỉ một lượt hoàn tất mỗi phiên bản,
không đủ tách tác động cải tiến khỏi biến động model/judge. Điểm ở lượt bị ngắt
cũng khác lượt mới dù agent không đổi; không ghép hoặc chọn điểm thuận lợi.

## Kết luận và trạng thái tiếp theo

CP6 đã có hai bộ đủ case, cùng cấu hình, so sánh điểm/calls/token và phân tích lỗi
có evidence. Bản mới sửa được H7 trong lượt này, source gate có hoạt động, nhưng
chi phí token tăng nhiều so với mức tăng điểm tổng và chưa cải thiện toàn diện.
Không tự sửa agent trong lúc eval để tối ưu kết quả. **Dừng trước CP7**; chưa merge
main, demo cuối hay nộp link lên LMS trong lượt này.
