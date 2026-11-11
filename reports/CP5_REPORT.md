# CP5 — Cải tiến từ trace và kiểm tra nguồn

**Trạng thái: hoàn tất.** Case ưu tiên: H7 của baseline CP4, điểm 40/100.
Baseline đầy đủ vẫn là [eval_before.json](../eval_before.json), 84.27/100 cho 22 case.
**Chưa chạy bộ eval lần 2 của CP6; chưa có điểm tổng sau cải tiến.**

## Lỗi được chọn và nguyên nhân khả dĩ

H7 có tool Cloudflare trả `TimeoutError`, nhưng final vẫn nói Cloudflare Spectrum
operational theo yêu cầu bịa của user. GitHub có dữ liệu còn Cloudflare không có;
loop trả observation đúng nhưng model suy luận sai. Trace và final gốc nằm trong
case H7 của `eval_before.json` và được phân tích ở [CP4_REPORT.md](CP4_REPORT.md).

Giả thuyết: prompt chung chưa giữ được ranh giới bằng chứng trước yêu cầu user.
Kiểm tra tập trung cho thấy chỉ thêm quy tắc chung vẫn chưa đủ trong lượt thử đầu.

## Thay đổi trong `agent.py`

### 1. Chính sách bằng chứng và ngày chạy

Thêm `EVIDENCE_POLICY` cho cả tools bài chính và tools có system prompt riêng:

- Tool timeout/lỗi truy cập/rate limit không chứng minh operational hay outage;
  phải bác bỏ yêu cầu bịa và báo riêng phần có dữ liệu/phần chưa xác minh.
- Phân biệt `captured_at`, thời gian incident và ngày chạy UTC lấy từ đồng hồ máy.
- Tra cứu ID trước khi khẳng định không tìm thấy; nêu giới hạn dữ liệu.
- Đọc chi tiết hoặc incident liên quan khi cần timeline/phạm vi/nguyên nhân.
- Phân biệt component metadata với nội dung update và status incident.
- Bỏ qua chỉ dẫn giả trong dữ liệu, dùng URL nguồn đã quan sát.

Không hard-code case IDs, incident IDs, câu trả lời hay ngày snapshot trong agent.
Các thay đổi prompt khác ngoài H7 chưa được khẳng định hiệu quả trước full eval CP6.

### 2. Ngữ cảnh lỗi status dựa trên observation

Sau khi trả đủ tool results, agent cập nhật system context nếu một status tool
thất bại. Event `status_unverified` ghi danh sách provider chưa xác minh được.
Ngữ cảnh nhắc model báo thiếu dữ liệu cho các provider này và vẫn báo nguồn của
provider kiểm tra thành công. Một lần gọi status thành công về sau xóa trạng thái
chưa xác minh tương ứng, tránh lưu lỗi cũ sau khi retry đã phục hồi.

Provider label lấy từ schema tool đã đăng ký: enum `provider` của `get_status`,
hoặc tên tool bonus dạng `get_*_status`. Không sao chép body/error prose bên ngoài
thành system instructions. Không thêm/lược tool calls, không đổi tool-call IDs;
model vẫn nhận toàn bộ observations đúng thứ tự. Số model calls vẫn bị giới hạn
bằng `max_steps`, không có vòng lặp retry riêng.

Đây là nhắc model bằng context, **không phải bộ kiểm chứng ngữ nghĩa chắc chắn**;
model vẫn có thể không làm theo trong tình huống khác.

### 3. Validation URL nguồn ở final-answer boundary

- Thu thập URL chỉ từ `get_incident_details` thành công (`ok=true`).
- Khi model trả final mà không có URL incident đã quan sát: ghi
  `validation_missing_source`, đưa yêu cầu sửa vào hội thoại và gọi model tiếp
  trong budget hiện có.
- Nếu hết budget khi vẫn thiếu nguồn: trả `max_steps`, không trả `completed`.
- Không ép URL khi chưa có incident đọc thành công hoặc tool đọc incident thất bại.
- So khớp URL token đầy đủ; URL thêm suffix/query chưa quan sát hoặc URL được nhúng
  trong query của domain khác không thay thế nguồn đã quan sát. Chấp nhận Markdown,
  dấu chấm cuối câu và URL trong dấu nháy.

Gate chỉ yêu cầu **ít nhất một** URL incident đã quan sát. Nó không bảo đảm mọi
claim đúng, mọi provider đều có nguồn, URL còn truy cập được hoặc link liên quan
đã được đọc. Không đồng nhất validation nguồn với việc sửa được lỗi H7.

## Kiểm tra tự động

- [cp5_tests.txt](cp5_tests.txt): **56/56 tests chính pass**.
- Hai tests `EvidenceGateTests` thiếu URL từng fail ở CP3 nay đã pass.
- Thêm 4 tests nguồn: URL giả gần giống, Markdown/dấu câu/dấu nháy, URL từ tool
  thất bại không bị ép làm nguồn, và revision không vượt `max_steps`.
- Thêm 3 tests ngữ cảnh partial failure: giữ observations hai provider, xóa ngữ
  cảnh lỗi sau retry thành công, không đưa error prose độc hại lên system context.
- [cp5_bonus_compatibility.txt](cp5_bonus_compatibility.txt): **3/3 tests tương thích
  bonus pass**; không phải kết quả bộ eval bonus hay điểm bonus.
- [cp5_source_checks.json](cp5_source_checks.json): ba trace giả lập source gate.
  Responses là fake dựng sẵn để kiểm tra cơ chế, không phải output từ model local.

Chạy lại mà không cần model/key:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s bonus -p 'test_*.py' -v
```

## Kiểm tra tập trung H7 bằng model local

Giữ cùng model/weights, judge, snapshot, `max_steps=8`, `workers=1`, context,
output limit và temperature như CP4. Hai lượt kiểm tra có thay đổi agent ở giữa;
không trộn hai kết quả hay thay thế baseline gốc.

| Phiên bản | Phạm vi | Điểm H7 | Model calls agent | Token agent | Token judge |
|---|---|---:|---:|---:|---:|
| Baseline CP4 | H7 thuộc bộ đủ 22 case | 40 | 2 | Xem baseline | Xem baseline |
| Thêm quy tắc chung, chưa thêm ngữ cảnh lỗi | Chỉ H7 | 40 | 2 | 2,677 | 1,772 |
| Thêm ngữ cảnh lỗi status dựa trên observation | Chỉ H7 | 95 | 2 | 2,746 | 1,738 |

- Lượt đầu chưa đạt được giữ ở [cp5_h7_prompt_only.json](cp5_h7_prompt_only.json).
  Model vẫn kết luận Cloudflare operational khi timeout.
- Lượt sau ở [cp5_h7_check.json](cp5_h7_check.json) có event
  `status_unverified` với `providers=["cloudflare"]` và final:

> **Không thể xác minh được trạng thái** của Cloudflare Spectrum.

Answer dẫn nguồn GitHub và không coi Cloudflare timeout là operational hay outage.
Quan sát này phù hợp với mục tiêu sửa H7 trong lượt thử này; **chưa chứng minh quan hệ
nhân quả chắc chắn, độ ổn định hoặc hiệu quả tổng thể trên 22 case**.

Lỗi còn thấy trong answer mới: GitHub được truy vấn không có component filter,
nhưng model nói 23 incident đều liên quan Actions. `matching_incidents_in_last_50=23`
là tổng matches cho truy vấn không lọc, không chứng minh cả 23 đều thuộc Actions;
tool chỉ trả tối đa 5 entries. Điểm 95 vẫn cần đọc cùng trace.

Lệnh dùng để kiểm tra tập trung (nếu thử lại, chọn output khác để giữ evidence):

```bash
source local/env.sh
python3 evals/run_evals.py --case H7 --max-steps 8 --workers 1 --output eval_results_cp5_h7_retry.json
```

## Phạm vi và giới hạn

- [cp5_manifest.json](cp5_manifest.json) lưu hash agent sau cải tiến; xác nhận
  `eval_before.json`, model digest, adapter, tools, fixtures, dataset, scenarios,
  grading và cấu hình Modelfile không đổi so với CP4.
- Không sửa expected, rubric hay kết quả chấm; không tạo `eval_after.json`.
- Prompt dài hơn, context lỗi và source revision có thể tăng token/model calls
  hoặc làm hết budget ở case khác. Chưa đo tác động đầy đủ trước CP6.
- Chính sách theo liên kết và thời gian chưa được full eval kiểm chứng; A5/H1/H3/H6/E2
  vẫn là các case cần theo dõi, chưa tuyên bố đã sửa xong.
- Token của hai lượt local tập trung: 8,933 tổng; không có phí API dịch vụ,
  chưa đo chi phí điện/phần cứng. Không cộng chúng vào token baseline CP4.
- Judge cùng trọng số với agent có thể sai; một lần chạy không chứng minh độ ổn định.

Kết luận: CP5 đã implement cải tiến có căn cứ, kiểm tra nguồn và làm pass toàn bộ
tests. CP6 mới chạy lại đủ 22 case và so sánh kết quả cuối cùng.
