# Bonus — 5 providers, bounded retries và pagination

Agent dùng schemas/system prompt của tools bonus. Phần mở rộng nằm tại
`bonus/agent.py`; `agent.py` chỉ dispatch vào đó khi có nhiều status tools riêng.
Luồng bài chính được giữ nguyên; bản đúng đã eval CP6 lưu ở
`reports/reference/agent_cp6.py` và được kiểm tra hash bằng tests.
Không sửa tools/snapshot/cases/grading của đề.

## Chạy bằng model local

```bash
source local/env.sh
python3 local/try_agent.py --bonus 'Kiểm tra GitHub, Cloudflare, Vercel, npm và DigitalOcean'
python3 local/try_agent.py --bonus --output reports/manual_bonus.json 'Đọc timeline Vercel incident sps6n39gm4sg'
```

Mặc định bonus 16 model steps, bài chính vẫn 6. Snapshot không đại diện status
thực tế hôm nay. `--mode live` gọi public APIs thật và có thể gặp rate limit.

## Các cơ chế được triển khai

- **Registry:** 5 status tools riêng và `get_incident_details`, dùng nguyên schemas.
- **Retry:** tối đa 3 lỗi liên tiếp cho mỗi tool/provider. Đọc Retry-After dạng số
  giây hoặc HTTP-date; chờ tối đa 5 giây, nếu cần lâu hơn thì dừng retry và báo thiếu
  dữ liệu. 429 giả lập có delay=0. Không coi 429 là outage.
- **Budget:** tool hết retry bị loại khỏi schemas khi là status tool; lời gọi model
  cố yêu cầu lại bị từ chối, ghi `tool_blocked` và trả observation đúng call ID.
  Trace phân biệt gọi tool thật (`tool`) với yêu cầu bị chặn (`tool_blocked`).
- **Fallback recovery:** nếu model đã thấy lỗi nhưng cố kết thúc khi còn budget,
  agent lên lịch retry bằng message/call ID riêng và event `scheduled_retry`. Không
  giả vờ đây là lời gọi do LLM sinh ra; vẫn tính đúng model calls và tool executions.
- **Arguments:** trả `INVALID_ARGUMENTS` để model sửa theo schema. Fallback bỏ key
  không hỗ trợ, sửa integer theo bounds trong schema; không đoán/thay provider hoặc ID.
  Lỗi rate limit và lỗi định dạng dùng chung budget lỗi liên tiếp, không reset chỉ vì đổi loại lỗi.
- **Pagination:** câu hỏi yêu cầu timeline/thông báo cũ phải đọc đủ các update;
  track coverage offset/total_updates, nhắc trang thiếu khi final quá sớm. Không
  hard-code ID incident hoặc nội dung đáp án. Page limit ưu tiên 3 theo schema.
- **Trạng thái xuyên trang:** giữ status incident tại snapshot và timestamp update mới nhất
  qua các trang. Offset lớn chứa update cũ hơn, không coi trang đọc cuối là trạng thái mới.
  Context không sao chép body/error prose thành system instructions.
- **Context:** bỏ chỉ trường `distractors` được tools đánh dấu, lưu số lượng trong
  `context_omitted` và event `context_compacted`; giữ status/incident/update/URL thật.
  Trace là observation sau xử lý, không lưu lại nguyên danh sách nhiễu.
- **Sources:** final phải có các URL incident đã đọc thành công; sửa trong cùng budget.
  Status-only sources được hướng dẫn trong prompt, chưa có semantic validator cho mọi claim.
- **Boundaries:** registry chỉ hỗ trợ 5 providers, không bịa Linear/Slack hoặc theo
  chỉ dẫn giả nằm trong tool output. Một số hành vi vẫn phụ thuộc model/judge.

## Tests và eval

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s bonus -p 'test_*.py' -v

# Full eval bonus có checkpoint, không sửa run_case/grading:
python3 local/run_checkpoint_evals.py --bonus
# Chỉ dùng khi lượt đang dở, cùng code/model/config/ngày UTC:
python3 local/run_checkpoint_evals.py --bonus --resume

# Lệnh gốc của đề cũng dùng cùng bonus engine:
python3 evals/run_evals.py --bonus --output eval_results_bonus_retry.json
```

Không ghi đè `eval_bonus.json` khi chỉ chạy thử; chọn output/checkpoint riêng.
Chỉ quy đổi điểm /15 khi đủ 10 case được chấm. Xem `reports/BONUS_REPORT.md`
sau khi full eval hoàn tất; không cộng điểm eval bài chính trực tiếp vào điểm bonus.

## Giới hạn

Pagination đầy đủ chỉ được yêu cầu khi câu hỏi nói rõ timeline/thông báo cũ; query
scope khác vẫn phụ thuộc model chọn trang phù hợp. Update body có thể bị cắt ngay
trong tool, đọc đủ trang không khôi phục phần body đó. Source presence không chứng
minh mọi claim đúng. Retry và revision có thể làm hết max_steps, khi đó trả max_steps.
Model/judge dùng chung trọng số; điểm là ước lượng cần đọc cùng trace.
