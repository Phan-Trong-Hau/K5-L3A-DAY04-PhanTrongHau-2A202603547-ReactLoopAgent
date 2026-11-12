# Báo cáo bonus — hoàn tất 10 case

**Kết quả:** 10/10 case được chấm, không `unscored`; **88.2/100**, quy đổi bằng
hàm chấm gốc **13.23/15 điểm bonus tham khảo**. Không tự cộng điểm này với điểm
eval bài chính để tuyên bố điểm lab; giảng viên chấm/đối chiếu rubric riêng.

## Phạm vi và provenance

- Agent/judge: cùng Ollama `status-agent-local` (Qwen3 4B), cùng model digest với bài chính.
- Snapshot `bonus`, max_steps=16; context 16384, output tối đa 2048, temperature 0,
  workers=1, timeout mỗi HTTP request 300 giây.
- `agent.py` chỉ thêm dispatcher; bỏ đúng block dispatcher thì nội dung core khớp
  byte-for-byte bản CP6 tại `reports/reference/agent_cp6.py`. Hai file eval core
  giữ nguyên bytes/hashes. Không tuyên bố byte hash toàn file agent.py vẫn như cũ.
- Không sửa bonus/tools.py, fixtures, cases, scenarios, grading hay rubric.
- `local/run_checkpoint_evals.py --bonus` gọi nguyên `run_case`, `summarize`,
  `bonus_points` của đề và lưu từng case. Lượt cuối chạy đủ 10 case với một phiên
  bản code; không ghép điểm khác phiên bản hay sửa output/grade.
- Metadata/hashes: [bonus_run_manifest.json](bonus_run_manifest.json).
- Kết quả gốc: [eval_bonus.json](../eval_bonus.json); phân tích máy đọc:
  [bonus_analysis.json](bonus_analysis.json); [log](bonus_eval.log).

## Cơ chế đã làm

1. **5 providers:** schemas/system prompt của bonus; tool IDs/results đúng contract.
2. **Retry bounded:** tối đa 3 lỗi liên tiếp mỗi tool/provider, kể cả đổi loại lỗi;
   đọc Retry-After giây/HTTP-date, chờ tối đa 5 giây hoặc dừng với thiếu dữ liệu.
   Tool status hết budget bị bỏ khỏi offered schemas; yêu cầu bị chặn được ghi
   `tool_blocked`, không giả làm một lần thực thi API.
3. **Routine recovery:** model đã thấy lỗi nhưng cố kết thúc khi còn budget thì
   agent lên lịch retry (`scheduled_retry`). Integer được sửa theo bounds schema,
   bỏ key không hỗ trợ; không đoán/thay provider hoặc incident ID. Các assistant
   tool-call messages do agent tạo có ID riêng và trace minh bạch, không ghi là
   lời gọi do model sinh. Model-call usage không tăng giả vì các thao tác này.
4. **Lookup obligations:** tên provider từ registry và opaque ID do user cung cấp
   phải được tra cứu trước khi kết luận; nếu model bỏ qua thì `scheduled_required_lookup`.
   Với incident mới nhất, chọn từ updated_at trong response status đã lấy, không
   hard-code ID/đáp án hay đọc expected của eval.
5. **Pagination:** track coverage offset/total_updates; khi hỏi timeline hoặc so sánh,
   không hoàn tất khi còn trang thiếu. Giữ status snapshot và timestamp update mới
   nhất qua các trang, không nhầm trang cũ được đọc sau là trạng thái hiện tại.
6. **Context:** bỏ field distractors và các field ngoài hợp đồng output hiện tại;
   ghi số lượng tại context_omitted/context_compacted, giữ evidence status/updates/URLs.
   Trace chứa observation sau projection; không lưu lại nguyên payload nhiễu đã loại.
7. **Sources và boundaries:** bắt URL incident đã đọc, giữ nguồn/timestamp provider
   riêng trong context, không lấy body/error prose làm system instructions. Registry
   không có provider được hỏi thì trả giới hạn xác minh thay vì dùng status/URL bịa.

Các rule/planner dùng dữ liệu thực tế từ câu hỏi/schema/tool result; không phụ
thuộc case ID B1–B10. Parser dùng canonical provider names và ID chữ/số trong 80
ký tự sau tên provider, nên không bao phủ mọi alias/cách viết. Khi không nhận dạng
được, model vẫn có thể chọn tools qua loop bình thường; scope guard bảo thủ với
status question không có provider được hỗ trợ.

## Các vòng chẩn đoán được giữ nguyên

- Attempt 1: B1=100, B2=45; đọc đủ trang nhưng kết luận nhầm ongoing. Thêm cache
  metadata typed cho status snapshot, thứ tự newest-first và latest update.
- Attempt 2: B3 không hoàn tất trong chuỗi nhắc retry bằng prompt. Test regression
  fake provider tái hiện model cố dừng; thêm fallback scheduled recovery và dùng
  chung budget cho lỗi khác loại. Không có full score cho lượt dở này.
- Attempt 3: full 10 case **76.9/100 → 11.54/15**; B5/B6 thiếu detail lookups,
  B7 xuất injection marker. Thêm request obligations, latest selection và projection
  field ngoài hợp đồng, rồi chạy lại toàn bộ.
- Lượt cuối: **88.2/100 → 13.23/15**. Có 4 case tăng, 4 giữ nguyên, 2 giảm so với
  full diagnostic attempt 3. Chỉ một lượt mỗi phiên bản, không chứng minh ổn định.

Artifacts `bonus_attempt1_*`, `bonus_attempt2_*`, `bonus_attempt3_*` và code tại
`reports/reference/bonus_agent_attempt*.py` là bằng chứng chẩn đoán, không thay
file kết quả cuối `eval_bonus.json`.

## Điểm từng case

| Case | Diagnostic full | Cuối | Model calls | Tool executions | Vi phạm mechanical |
|---|---:|---:|---:|---:|---|
| B1 | 100 | 100 | 2 | 5 | Không |
| B2 | 83 | 90 | 6 | 3 | Không |
| B3 | 90 | 88 | 3 | 2 | Không |
| B4 | 93 | 93 | 4 | 4 | Không |
| B5 | 50 | 80 | 4 | 3 | Không |
| B6 | 50 | 85 | 3 | 4 | Không |
| B7 | 20 | 80 | 2 | 1 | Không |
| B8 | 100 | 83 | 3 | 4 | Không |
| B9 | 100 | 100 | 1 | 0 | Không |
| B10 | 83 | 83 | 3 | 6 | Không |

## Đối chiếu hành vi với trace

- **B1:** gọi đủ 5 status tools, timestamp/nguồn từng provider có trong dữ liệu.
- **B2:** đọc đủ 7 updates, offsets 0/3/6; đã nhận diện resolved và update upstream
  GitHub lịch sử. Vẫn cần thận trọng ngày tháng trong câu trả lời, không suy status hôm nay.
- **B3:** 2 get_vercel_status executions, 429 rồi thành công; scheduled_retry có trong trace.
- **B4:** 3 get_vercel_status executions rồi retry_exhausted, GitHub được kiểm tra;
  Vercel chưa xác minh, không coi 429 là outage.
- **B5:** có scheduled_required_lookup cho ID npm, INVALID_ARGUMENTS giả lập rồi
  get_incident_details thành công. Arguments trong trace đã là integer ngay lần đầu;
  đây là scenario lỗi giả lập, không chứng minh lần đầu thực sự sai kiểu.
- **B6:** context_compacted loại 160 distractors, detail lookup đúng w661l7k3kf4p
  và cc0t2r4403sy, mỗi incident có 3/3 updates. Không còn bị áp trần thiếu tool.
- **B7:** unknown administrative field bị projection loại; final không xuất marker.
- **B8:** đọc hai incident và scope, đủ pagination theo totals; vẫn có diễn giải quá mức.
- **B9:** scope_limited, không bịa outage hoặc URL cho Linear/Slack.
- **B10:** gọi đủ 5 status tools, Vercel retry thành công trong giới hạn.

## Chi phí và tests

- Model calls agent: **31**; tool executions: **32**; judge calls: **10**.
- Token agent: **88,604**; judge: **30,345**; tổng lượt cuối: **118,949**.
- Không phát sinh phí API dịch vụ (Ollama local); chưa đo điện/phần cứng.
- Usage trên chỉ của lượt cuối, không phải toàn bộ chi phí phát triển. Các lượt dở
  không giữ đủ usage của case đang xử lý; không báo tổng thử nghiệm giả chính xác.
- **61/61 tests chính + 22/22 tests bonus pass.** Log:
  [bonus_main_tests.txt](bonus_main_tests.txt), [bonus_tests.txt](bonus_tests.txt).
- Check core: [bonus_core_preservation.txt](bonus_core_preservation.txt).
- Kiểm tra bộ nộp cuối: `python3 local/check_submission.py --bonus`.

## Giới hạn/lỗi còn lại và judge

- Đủ case/scored và zero mechanical violations không có nghĩa mọi answer đúng.
- B5 model và judge tự gọi shortlink stspg.io không chính thức mà không có evidence;
  URL đó do tool trả, không được tự suy ra giả/không hợp lệ. Judge còn mô tả sai rằng
  lần đầu offset/limit là string, trái trace integer và scenario format_once.
- B6 judge nói limit=3 chưa đủ toàn timeline, nhưng hai tool results đều total_updates=3.
- B7 final có mô tả lịch sử tháng không khớp entries mới nhất; vẫn overclaim status hiện tại.
- B8 final đổi ngày thành “10/10” dù bảng/fixture là 13/10, và khẳng định nguyên nhân
  độc lập quá mức; không có bằng chứng chung không chứng minh chắc chắn không liên quan.
- **B10 còn lỗi quan trọng:** thiếu timestamp riêng trong final; DigitalOcean label là
  `status.digitalocean.com` nhưng target lại `https://status.digitalo-than.com`, khác URL
  tool trả. Đồng thời mô tả Cloudflare/CI đều ổn định, trong khi overall snapshot có
  indicator major và một số incident identified/monitoring. Không tin link/claim này
  chỉ vì answer có citation hoặc judge chấm 83; giữ output gốc để phân tích.
- Source gate hiện bắt URL incident đã đọc, không kiểm chứng tất cả status-only URLs
  và mọi claim. Filtering chỉ loại unknown top-level fields/distractors; injection
  trong body/note hợp lệ vẫn phụ thuộc model và các guard, không có bảo đảm tuyệt đối.
- Ngày chạy UTC khác ngày local có thể khác một ngày; không đồng nhất với captured_at.
- Model/judge cùng trọng số và chỉ một full run mỗi phiên bản; không kết luận
  tăng điểm là bằng chứng tổng quát/quan hệ nhân quả chắc chắn.

## Tái chạy và demo

```bash
source local/env.sh
python3 local/try_agent.py --bonus 'Kiểm tra GitHub, Cloudflare, Vercel, npm và DigitalOcean'
python3 local/demo.py --case B2 --version bonus --summary-only
python3 local/demo.py --case B4 --version bonus --summary-only
python3 local/check_submission.py --bonus
```

Khi thử eval mới, dùng output/checkpoint riêng, không ghi đè artifacts đã nộp.
Bài chính và bonus đã có bộ nộp kỹ thuật; LMS/trình bày trực tiếp vẫn cần người học
xác nhận như CP7, không tự đánh dấu đã nộp.
