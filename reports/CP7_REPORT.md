# CP7 — Demo và kiểm tra bàn giao

**Trạng thái: bộ nộp và demo replay đã sẵn sàng về kỹ thuật.** Chưa xác nhận demo
trực tiếp với trợ giảng hoặc nộp link lên LMS; CP7 chưa được đánh dấu hoàn tất toàn bộ.

## Đã thực hiện

- [x] Kiểm tra bốn file bắt buộc `agent.py`, hai eval JSON và `NOTES.md`.
- [x] Hai bộ đủ đúng 22 case, không unscored, điểm tổng khác null và khớp case scores.
- [x] Config hai bộ giống nhau; hashes code/tools/dữ liệu khớp bản CP6.
- [x] `NOTES.md` đủ 5 mục; không sửa điểm eval hoặc code sau khi chấm.
- [x] Repo đúng tên L3A, thuộc `Phan-Trong-Hau`, public và trả HTTP 200 khi mở không đăng nhập.
- [x] Không track `.env`; quét file tracked không khớp các mẫu credential phổ biến.
  Đây không phải bảo đảm tuyệt đối cho mọi loại secret hoặc mọi commit lịch sử.
- [x] 59/59 unit tests chính pass; 3/3 tests tương thích bonus pass.
- [x] Chạy replay trace nhiều bước A8, lỗi/cải tiến H7 và regression H2 thành công.
- [x] Soạn [DEMO.md](../DEMO.md), [REPORT.md](../REPORT.md) và công cụ kiểm tra bộ nộp.
- [ ] Người học trình bày và giải thích code trực tiếp khi được yêu cầu.
- [ ] Đăng nhập LMS, nộp đúng bài Day 04, kiểm tra trạng thái xác nhận đã nộp.

Bằng chứng kiểm tra tại [cp7_submission_checks.txt](cp7_submission_checks.txt),
[cp7_tests.txt](cp7_tests.txt), [cp7_bonus_compatibility.txt](cp7_bonus_compatibility.txt).
Lệnh kiểm tra độc lập: `python3 local/check_submission.py`.

## Demo đã chạy về kỹ thuật

Các demo là replay từ kết quả model thật đã lưu, không phải lượt LLM mới.

| Nội dung | Lệnh | Log |
|---|---|---|
| Nhiều provider và nhiều bước | `python3 local/demo.py --case A8 --version after --summary-only` | [cp7_demo_multistep.txt](cp7_demo_multistep.txt) |
| Lỗi timeout và cải tiến H7 | `python3 local/demo.py --case H7 --version both` | [cp7_demo_failure.txt](cp7_demo_failure.txt) |
| Regression cần giải thích | `python3 local/demo.py --case H2 --version both --summary-only` | [cp7_demo_regression.txt](cp7_demo_regression.txt) |

A8 đọc status hai provider ở step 1, đọc chi tiết ở step 2 và final ở step 3.
H7 cho thấy lỗi baseline và giới hạn bằng chứng sau cải tiến. H2 cho thấy điểm giảm
vì thiếu tool bắt buộc. Kịch bản không che các lỗi còn lại.

## Trạng thái GitHub và phạm vi

Bài làm được phát triển trên branch `feat/local-status-agent`; PR #1 dùng để đưa
bản kiểm tra vào main cho link repo mặc định. **PR #1 đã merge** tại commit
`1a4a7ea`; đã truy cập public main không đăng nhập và kiểm tra file/hashes
khớp bản đã eval. Branch được giữ lại để xem lịch sử CP1–CP7. Bằng chứng:
[cp7_remote_verification.json](cp7_remote_verification.json).

Repo: https://github.com/Phan-Trong-Hau/K5-L3A-DAY04-PhanTrongHau-2A202603547-ReactLoopAgent
PR: https://github.com/Phan-Trong-Hau/K5-L3A-DAY04-PhanTrongHau-2A202603547-ReactLoopAgent/pull/1

Bài chính tối đa 85 điểm theo rubric; eval 85.73/100 là thước đo agent, không phải
điểm lab đã được giảng viên chấm. Tại mốc CP7 ban đầu bonus chưa chạy. Cập nhật: đã đủ 10 case, 88.2/100
→ 13.23/15 tham khảo, 61 tests chính + 22 tests bonus pass. Xem
[BONUS_REPORT.md](BONUS_REPORT.md).

## Vì sao chưa đánh dấu nộp LMS?

Đã kiểm tra khả năng thao tác: phiên này không có browser kết nối (inventory
trả apps/browsers rỗng), và tìm tích hợp VinUni LMS/Moodle không có kết quả.
Không có phiên tài khoản LMS để gửi hoặc xác minh bài nộp. Không tự nhận đã nộp.

Người học cần:

1. Mở https://aithucchien.vinuni.edu.vn và đăng nhập tài khoản cá nhân.
2. Vào đúng lớp/bài Day 04.
3. Dán link repo ở trên, lưu/nộp theo biểu mẫu thực tế.
4. Kiểm tra trạng thái xác nhận đã nộp; lưu bằng chứng trên LMS.
5. Trình bày demo và giải thích code khi giảng viên yêu cầu.

Hạn nộp phụ thuộc ca học/thông báo coach theo `SUBMISSION.md`; chưa có bằng chứng
về ca cụ thể hay thời điểm LMS nhận bài nên không khẳng định đã nộp đúng hạn.
