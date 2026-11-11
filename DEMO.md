# Demo và tự kiểm tra bài chính

Các lệnh replay dưới đây đọc **trace thật đã lưu** từ eval trước/sau. Chúng không
gọi model, không cần API key/Ollama và không tạo điểm mới. Demo trực tiếp trước
trợ giảng và phần giải thích code vẫn do người học trình bày.

## Kịch bản 3–5 phút

1. Giới thiệu bài: agent tự viết bằng Python standard library, model local Qwen3 4B,
   hai tools GitHub/Cloudflare; không dùng framework agent.
2. Trình bày trace nhiều bước A8:

   ```bash
   python3 local/demo.py --case A8 --version after --summary-only
   ```

   Step 1: hai status calls. Step 2: đọc chi tiết hai incident. Step 3: final.
   Nêu vì sao phải giữ assistant message, trả đúng `tool_call_id` và xử lý đủ
   mọi call trước request model tiếp theo. Muốn đọc toàn bộ evidence: thêm `--full-trace`.
3. Trình bày lỗi đã chọn H7 và cải tiến:

   ```bash
   python3 local/demo.py --case H7 --version both
   ```

   Baseline: timeout nhưng kết luận operational (40 điểm). Sau: nêu chưa xác minh
   được Cloudflare, vẫn dẫn nguồn GitHub (93 điểm). Giải thích `status_unverified`
   dùng schema labels, không đưa nội dung lỗi bên ngoài thành system instructions.
4. Cho thấy giới hạn thật và regression:

   ```bash
   python3 local/demo.py --case H2 --version both --summary-only
   python3 local/demo.py --case A6 --version after --summary-only
   ```

   H2: 100 → 50 vì bỏ `get_incident_details`. A6: source gate sửa URL nhưng vẫn
   không đọc incident liên quan. URL có mặt không bảo đảm factuality/completeness.
5. Chốt kết quả: 84.27 → 85.73; 43 → 46 model calls; token tăng 35%.
   Không kết luận cải thiện toàn diện. Judge từng phạt nguồn cho thơ H4 và bỏ sót
   lỗi ở A5/A6; đối chiếu trace thay vì chỉ nhìn điểm.

## Chạy agent mới bằng model local

Ollama cần đang chạy và có model gốc:

```bash
ollama create status-agent-local -f local/Modelfile
python3 local/try_agent.py 'GitHub Actions có sự cố gì gần đây?'
```

Lệnh này có gọi model, có thể mất vài phút; mặc định dùng snapshot. Dùng
`--output reports/manual_demo.json` để lưu một lần thử riêng. Không ghi đè hai file eval.
`--mode live` gọi status API hiện tại, khác dữ liệu snapshot dùng để chấm.

## Tự kiểm tra trước khi nộp

```bash
python3 local/check_submission.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s bonus -p 'test_*.py' -v
```

Kết quả đã kiểm tra: 59 tests chính và 3 tests tương thích bonus pass.
3 tests bonus này không phải bộ eval bonus 10 case; chưa có điểm bonus.

## Những câu cần giải thích được

- **CP1/CP2/CP3 khác nhau:** công cụ chạy riêng → model điều phối tools → xử lý lỗi/budget/trace.
- **Một step là gì:** một lần gọi model, không phải một tool call.
- **Vì sao `completed` vẫn sai:** chỉ là điều kiện dừng bình thường, không kiểm chứng nội dung.
- **Tool error khác provider error:** trả observation cho model khi tool lỗi;
  lỗi gọi LLM làm kết thúc run vì không có response tiếp theo.
- **Source gate làm gì:** lấy URL incident thành công, kiểm tra final, yêu cầu sửa
  trong budget. Hết budget trả `max_steps`; không ép nguồn khi chưa đọc incident thành công.
- **Giới hạn dữ liệu:** tìm chuỗi trong 50 incident, tối đa 5 matches, updates có thể rút gọn;
  snapshot không phải status hôm nay.
- **Vì sao không sửa tiếp code ở CP7:** để code nộp đúng bản đã chạy `eval_after.json`.
