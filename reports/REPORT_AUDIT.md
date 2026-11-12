# Đối chiếu report với đề bài

Ngày kiểm tra: 12/11/2026. Bản repo được đối chiếu: `1da1845` (đã gồm PR #2 bonus).
Nguồn yêu cầu: [GUIDE](../GUIDE.md), [SUBMISSION](../SUBMISSION.md),
[RUBRIC](../RUBRIC.md), [RULES](../RULES.md), [CHECKPOINTS](../CHECKPOINTS.md).

## Kết luận

Báo cáo và các tệp nộp đã có đủ các nội dung bắt buộc của bài chính và bonus.
Điều này không có nghĩa agent trả lời đúng mọi case hoặc đã đạt toàn bộ điểm rubric.
Demo trực tiếp, việc người học giải thích code, nộp LMS và đúng hạn vẫn chưa có xác nhận.
UI và báo cáo PDF không phải tệp bắt buộc trong đề; `NOTES.md` là phần phân tích bắt buộc,
`REPORT.md` tổng hợp và các report từng CP cung cấp bằng chứng chi tiết.

## Yêu cầu và bằng chứng

| Yêu cầu | Bằng chứng | Kết quả kiểm tra |
|---|---|---|
| Tự viết vòng ReAct Python, giữ assistant/tool messages, tool_call_id, nhiều calls và điều kiện dừng | [agent.py](../agent.py), [tests](../tests), [DEMO](../DEMO.md) | Có triển khai và tests; cần tự giải thích trong demo |
| Xử lý JSON arguments, lỗi tool/provider, giới hạn bước và trace | [NOTES mục 3](../NOTES.md), [CP5](CP5_REPORT.md), tests | Có; không đồng nghĩa mọi câu trả lời model đúng |
| Tệp nộp bắt buộc | [agent.py](../agent.py), [eval_before.json](../eval_before.json), [eval_after.json](../eval_after.json), [NOTES.md](../NOTES.md) | Đủ |
| Hai full eval cùng model, judge, snapshot, dataset và max_steps | [CP6 report](CP6_REPORT.md), [manifest](cp6_run_manifest.json), hai eval | 22/22 mỗi bộ, đều có điểm; config giống nhau |
| NOTES mục 1: case, câu trả lời, điểm trước | [NOTES mục 1](../NOTES.md) | H7, 40 điểm; có câu trả lời thực tế |
| NOTES mục 2: trace lỗi, nguyên nhân khả dĩ | [NOTES mục 2](../NOTES.md) | Có tool timeout và final sai; bổ sung event và câu trả lời sau cải tiến |
| NOTES mục 3: sửa gì, ở đâu, vì sao | [NOTES mục 3](../NOTES.md), [CP5](CP5_REPORT.md) | Có prompt, trạng thái chưa xác minh và source gate |
| NOTES mục 4: trước/sau tổng và case, calls, tokens, chi phí, lỗi còn lại/mới | [NOTES mục 4](../NOTES.md), [CP6](CP6_REPORT.md) | Đủ; nêu cả regression và chi phí token tăng |
| NOTES mục 5: giới hạn judge, snapshot, chỉ một lượt mỗi phiên bản | [NOTES mục 5](../NOTES.md) | Có; không suy rộng thành độ ổn định thống kê |
| Không thay fixtures, cases, grading hoặc sửa tay điểm | [manifests](cp6_run_manifest.json), [kiểm tra bộ nộp](report_audit_submission_checks.txt) | Artifact eval và logic core tham chiếu được giữ nguyên |
| Repo public, đúng tên; không nộp .env/keys | Repo GitHub và kiểm tra tracked files | Public, tên đúng; không có file `.env` tracked; quét mẫu secret phổ biến không phát hiện |
| Bonus 5 status tools, incident details, schemas và system prompt động | [bonus/agent.py](../bonus/agent.py), [bonus/tools.py](../bonus/tools.py), [BONUS_REPORT](BONUS_REPORT.md) | Có triển khai |
| Bonus retry 429/Retry-After, sửa arguments, timeout và partial failure | [BONUS_REPORT](BONUS_REPORT.md), [bonus tests](report_audit_bonus_tests.txt) | Có budget và giới hạn thời gian; ghi rõ scheduled retries |
| Bonus pagination, 160 distractors, scope/date/source/injection | [BONUS_REPORT](BONUS_REPORT.md), [eval_bonus.json](../eval_bonus.json) | Có cơ chế và phân tích; còn lỗi ngày, nguồn và diễn giải trạng thái |
| Bonus đủ B1–B10, cách tính điểm và giới hạn | [eval_bonus.json](../eval_bonus.json), [bonus manifest](bonus_run_manifest.json), [NOTES](../NOTES.md) | 10/10 có điểm, trung bình 88.2; quy đổi 13.23/15 theo công thức, không phải điểm giảng viên xác nhận |
| Demo trace nhiều bước và một lỗi agent | [DEMO](../DEMO.md), replay trong [CP7](CP7_REPORT.md) | Đã chuẩn bị và kiểm tra replay; chưa xác nhận trình bày trực tiếp |
| Nộp link repo bằng tài khoản cá nhân, đúng hạn theo ca học | [LMS_SUBMISSION.txt](LMS_SUBMISSION.txt), [CP7 checklist](CP7_REPORT.md) | Chưa xác nhận thao tác nộp hoặc thời điểm nộp |

## Số liệu được đối chiếu lại

| Bộ | Cases có điểm | Điểm eval /100 | Agent calls | Tool calls | Agent + judge tokens |
|---|---:|---:|---:|---:|---:|
| Before | 22 | 84.27 | 43 | 32 | 92,234 |
| After | 22 | 85.73 | 46 | 32 | 124,513 |
| Bonus | 10 | 88.2 | 31 | 32 | 118,949 |

H7 full eval tăng **40 → 93**; focused check CP5 là 95 và được ghi tách biệt.
Tổng tokens core tăng khoảng 35%; không kết luận cải tiến tiết kiệm chi phí.
Local Ollama không phát sinh phí API dịch vụ trong các lượt này; chưa đo điện/phần cứng.
Không cộng raw core eval 85.73 với 13.23 thành điểm bài: rubric core tối đa 85,
điểm eval chỉ là một bằng chứng. Các lượt thử ngắt/chẩn đoán không được ghép vào full eval.

Các lỗi đáng kể vẫn được công khai: core H2 regression, H1/H6/H3 thiếu tra cứu,
A6 có nguồn nhưng thiếu incident liên quan; bonus B7/B8 sai ngày/diễn giải,
B10 có URL không được tool cung cấp và kết luận trạng thái quá mức. Xem report chi tiết;
không sửa raw outputs để làm đẹp kết quả.

## Những chỗ đã chỉnh trong lần rà soát này

- Bổ sung bằng chứng H7 sau cải tiến ngay trong NOTES; phân biệt full eval 93 và focused 95.
- Gắn mốc thời gian cho 56+3 tests ở CP5 và 59+3 ở CP6/CP7 cũ.
  Kết quả mới là **61 tests chính + 22 tests bonus pass**:
  [main log](report_audit_main_tests.txt), [bonus log](report_audit_bonus_tests.txt).
- Làm rõ provenance: toàn file `agent.py` hiện tại khác CP6 vì thêm dispatcher bonus.
  Bỏ đúng block dispatcher thì core khớp byte-for-byte với [reference CP6](reference/agent_cp6.py);
  tests kiểm chứng điều này, bonus khớp manifest riêng. Không sửa code runtime/eval trong lần audit này.
- Cập nhật bàn giao đã gồm PR #2 merge `1da1845`; bằng chứng CP7 trước đây chỉ thuộc mốc core.
- Giảm các câu khẳng định quá mức về chống injection; nêu rõ giới hạn thực tế.

[Kiểm tra máy đọc được](report_audit_checks.json) và [submission checks](report_audit_submission_checks.txt)
lưu kết quả audit. Việc quét credential chỉ xét các mẫu phổ biến ở file tracked, không bảo đảm
mọi loại secret hoặc toàn bộ lịch sử Git. `local/env.sh` là script cấu hình với dummy key local,
không phải file `.env`; regex `.env` không escape dấu chấm có thể khớp nhầm đường dẫn `/env`.
