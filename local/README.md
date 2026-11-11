# Chạy bằng Ollama local

Không cần API key dịch vụ trả phí. Dùng model `qwen3:4b-instruct` đã cài
trên máy, tạo alias có context 16384 và output tối đa 2048 tokens:

```bash
ollama create status-agent-local -f local/Modelfile
source local/env.sh
python3 run.py 'GitHub Actions có incident nào gần đây?'
python3 evals/run_evals.py --output eval_after.json
```

Ollama cần đang chạy tại `http://localhost:11434`. Nếu chưa có model gốc,
chạy `ollama pull qwen3:4b-instruct` trước. Project vẫn chỉ dùng standard library.
`openai` ở đây là tên adapter tương thích giao thức, request đi tới localhost.
`OPENAI_API_KEY=local` là giá trị giả, không phải credential.

`OPENAI_BASE_URL` chỉ override endpoint adapter OpenAI. `LOCAL_MODEL=1` bật
sampling temperature 0 và yêu cầu JSON object cho lượt không có tool schemas
(judge của repo). Không bật biến này cho ứng dụng chat thông thường không cần JSON.
`PROVIDER_TIMEOUT` là timeout mỗi HTTP request tính bằng giây, mặc định 60;
local dùng 300 vì model chạy trên phần cứng giới hạn. Số model calls vẫn bị
chặn bởi `max_steps`; đây không phải giới hạn tổng thời gian chạy.

Hai bộ eval chính dùng cùng alias, cấu hình Modelfile và 8 steps, workers=1,
snapshot nguyên bản. Không chạy nhiều workers trên GPU 4 GB để tránh tranh bộ nhớ.
Model và judge dùng chung trọng số nên điểm chỉ là tham khảo. Cấu hình local
không tính giá API; file eval chứa token usage, không chứa phép đo điện năng.

Baseline agent nằm ở commit `df52938`; muốn tái chạy baseline hãy dùng checkout
riêng, tạo alias model và source `local/env.sh` từ bản hiện tại trước khi chạy.
Không ghi đè file eval đã nộp nếu chỉ thử nghiệm; chọn `--output` khác.

## Test nhanh và đọc kết quả

```bash
# Chỉ cần tạo alias một lần, rồi chạy mỗi câu hỏi:
python3 local/try_agent.py 'GitHub Actions có sự cố gì gần đây?'

# Hoặc nhập câu hỏi khi chương trình yêu cầu:
python3 local/try_agent.py

# Lưu đầy đủ trace vào file riêng (đã được gitignore):
python3 local/try_agent.py --output reports/manual.json 'Kiểm tra Cloudflare cache purge'
```

Script hiển thị answer và danh sách tool calls; trạng thái `completed` chỉ nói loop
kết thúc bình thường, không bảo đảm câu trả lời đúng. Mỗi lần chạy là một câu hỏi
độc lập, không giữ lịch sử chat. `--mode live` gọi status API thật; mặc định snapshot
không kiểm tra tình trạng thực tế hôm nay. Mở `reports/smoke_e2.json` để xem mẫu
kết quả eval một case, hoặc đọc `reports/SMOKE_REPORT.md`.

Bản baseline hiện còn thiếu kiểm tra nguồn bằng code nên 2 tests trong
`EvidenceGateTests` chưa pass. Đây là việc của phần cải tiến tiếp theo;
không phải lỗi cài Ollama. Bộ test local endpoint chạy riêng bằng:

```bash
python3 -m unittest discover -s tests -p 'test_local_provider.py' -v
```
