# Báo cáo tiến độ theo checkpoint

Quy trình: hoàn thiện một CP → ghi bằng chứng → commit và push → báo người học
và dừng trước CP tiếp theo. Chỉ đánh dấu hoàn tất khi đã kiểm tra tiêu chí của CP.

| CP | Nội dung | Trạng thái |
|---|---|---|
| CP1 | Setup và khám phá tools | Hoàn tất kỹ thuật |
| CP2 | Agent loop | Có code nền, chưa chốt riêng CP |
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

Kết luận: **CP1 hoàn tất về setup và kiểm tra tools**. Chưa chốt CP2 trong lượt này.
