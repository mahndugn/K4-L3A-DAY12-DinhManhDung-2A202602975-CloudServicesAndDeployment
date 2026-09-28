# Demo CloudOps Assistant — Cloud và Docker

Ứng dụng dùng FAQ offline, không gửi câu hỏi ra nhà cung cấp AI.
Không cần tài khoản LLM. AGENT_API_KEY là khóa truy cập API của ứng dụng.

## Khởi động

1. Mở Docker Desktop, chờ engine chạy.
2. Đặt AGENT_API_KEY riêng trong .env. Giữ file này ngoài Git.
3. Chạy từ thư mục gốc repo:

```powershell
docker compose up -d --build
docker compose ps
docker compose exec redis redis-cli ping
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/ready
```

Các dấu hiệu cần quan sát: Redis phản hồi PONG, health trả service
cloudops-assistant, ready trả redis=true. Đây là kết quả mong đợi, không phải
output đã ghi nhận của bản deploy.

## Hỏi qua Swagger

Mở http://localhost:8000/docs → POST /ask → Try it out.
Nhập X-API-Key từ .env và X-User-Id=cloudops-demo, rồi thử lần lượt:

| Câu hỏi | Nội dung cần thấy |
|---|---|
| Docker image khác container thế nào? | Image là gói, container là instance |
| Docker multi-stage là gì? | builder, runtime, COPY --from |
| Health check trong Docker khác readiness thế nào? | /health, /ready và vai trò Redis |
| Rate limit dùng Redis thế nào? | Sorted Set và HTTP 429 |
| Redis giúp scale agent ra sao? | State chia sẻ giữa instance |
| giai thich them | Tiếp tục chủ đề Redis vừa hỏi |

history_length là số message trước câu hỏi hiện tại: 0, 2, 4… và tối đa 20
khi dùng ConversationStore. Một lượt tạo hai message user/assistant.
Các con số tokens và cost_usd được ước lượng để minh họa cost guard.

## Chạy smoke test tự động

Sau khi cài requirements.txt trong .venv:

```powershell
python -X utf8 scripts/demo_cloudops.py
```

Script đọc key từ .env, thử health, ready, yêu cầu xác thực, rồi hỏi các câu
demo bằng user ID mới. Script không in key; nó ghi một ít history/quota/chi phí
mô phỏng cho user demo trên service local.

## Quan sát lỗi

- Bỏ X-API-Key → 401.
- Câu hỏi rỗng hoặc chỉ khoảng trắng → 422.
- Quá RATE_LIMIT_PER_MINUTE trong 60 giây với cùng user → 429.
- Khi tổng chi phí đã vượt MONTHLY_BUDGET_USD → lượt sau bị 402.
- /ready trả 503 → kiểm tra Redis và REDIS_URL.

Xem log bằng docker compose logs --tail 50 agent. Không chia sẻ output của
docker compose config vì lệnh đó có thể hiển thị giá trị key sau nội suy.
Sau sửa code, chạy lại docker compose up -d --build.
Chạy docker compose stop để dừng mà giữ volume.

## Bằng chứng nộp bài

Điền DEPLOYMENT.md sau khi deploy thật. Chụp dashboard và các endpoint,
che API key. Tự trả lời exercises.md dựa trên quan sát, đặc biệt dung lượng
image và lỗi deploy. URL cloud, workflow deploy và ảnh chưa tự xuất hiện khi
chạy local.

## Kết quả kiểm tra local ngày 2026-09-28

Đã chạy trong workspace này:

- CP1–CP4 (bỏ test Docker) + test_cloudops.py: 106 passed, 2 deselected.
- CP2 đầy đủ, gồm build Docker thật: 16 passed (14 test cấu trúc đã nằm trong lượt trên).
- Image test: 271,067,390 bytes, runtime user appuser.
- docker compose up --wait: agent và redis đều healthy.
- Smoke test: /health, /ready, /topics trả 200; /ask không key trả 401.
- Năm câu demo có key trả lời được; history_length lần lượt 0, 2, 4, 6, 8.
- Câu “giai thich them” tiếp tục đúng chủ đề Redis ở lượt trước.

Có một cảnh báo deprecation từ Starlette TestClient/httpx, không gây fail.
Kết quả local này không thay thế minh chứng cloud CP5 hoặc ảnh chụp của bài nộp.
