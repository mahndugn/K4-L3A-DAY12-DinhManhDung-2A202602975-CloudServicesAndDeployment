# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay từng dòng giữ chỗ bên dưới bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Đinh Mạnh Dũng  Mã học viên: 2A202602975

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Khi deploy lên Railway, container của tôi được tạo và Uvicorn bắt đầu chạy,
> nhưng tiến trình dừng ngay với `ValidationError: agent_api_key - Field
> required`. Nhờ fail fast, tôi biết service Railway chưa có `AGENT_API_KEY`
> trước khi nhận traffic. Nếu dùng mặc định `"changeme"`, deployment có thể
> vẫn xanh nhưng bất kỳ ai đoán được khóa mặc định đều gọi được `/ask`, và lỗi
> cấu hình chỉ bị phát hiện sau khi service đã bị truy cập trái phép.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Một dòng log tôi thu được sau khi gọi `/ask` là:
> `{"event":"ask_completed","level":"info","timestamp":"2026-09-28T09:38:26.439682+00:00","user_id":"sv-exercises","tokens_in":7,"tokens_out":69,"cost_usd":4.245e-05}`.
> Từ dòng này tôi có thể (1) lọc hoặc đếm số request theo `user_id`, thời gian
> và mức log để điều tra sự cố; (2) tổng hợp token và `cost_usd` thành dashboard
> hoặc cảnh báo ngân sách. Chuỗi `print("đã trả lời xong")` không có các trường
> ổn định để hệ thống log truy vấn hay tính toán.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | khoảng 1.1 GB |
| Multi-stage | 271 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Bản đầu dùng `python:3.11` đầy đủ nên mang theo Debian và nhiều công cụ
> build/phát triển; nó còn `COPY . .` trước khi cài package. Bản cuối dùng
> `python:3.11-slim`, cài dependency ở builder và chỉ chép `/install`, `app/`,
> `utils/` sang runtime. Phần chênh lệch chủ yếu là công cụ biên dịch, header,
> cache và các thành phần hệ điều hành không cần lúc chạy. Image multi-stage
> thực tế của tôi được Docker báo là 271 MB.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Khi chỉ sửa `app/main.py`, các layer base image, `WORKDIR`, `COPY
> requirements.txt` và `RUN pip install` vẫn dùng cache; Docker chỉ chạy lại
> `COPY app`, các layer sau nó như tạo user, metadata health check và CMD. Nếu
> đặt `COPY . .` trước `RUN pip install`, mọi thay đổi source làm layer COPY đổi,
> kéo theo việc cài lại toàn bộ dependency dù `requirements.txt` không đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Nếu endpoint Python có lỗ hổng thực thi lệnh, kẻ tấn công trước hết chạy lệnh
> với UID của tiến trình trong container. Khi tiến trình là root, kết hợp thêm
> cấu hình nguy hiểm như capability dư thừa, mount thư mục host hoặc Docker
> socket, họ có thể sửa file được mount hay tìm cách thoát container để chiếm
> quyền cao trên host. `USER appuser` cắt chuỗi ở bước thực thi lệnh: mã bị khai
> thác chỉ có UID 10001 và không được tự ý sửa file hệ thống. Biện pháp này giảm
> tác động chứ không thay thế việc bỏ capability và tránh mount nhạy cảm.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Có thể gửi tối đa 20 request trong hai giây quanh ranh giới phút: gửi 10
> request ở giây 59 của phút trước, rồi gửi tiếp 10 request ở giây 00 của phút
> sau. Bộ đếm theo phút đã reset nên cho phép cả hai đợt. Sliding window nhìn lại
> đúng 60 giây nên đợt đầu vẫn còn trong cửa sổ và sẽ chặn đợt thứ hai.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit giới hạn tốc độ ngắn hạn, ở đây là số request trong 60 giây; cost
> guard giới hạn tổng chi phí tích lũy theo tháng. Một người gọi đều 1 request
> mỗi phút sẽ luôn qua rate limit nhưng cuối tháng có thể hết ngân sách và bị
> cost guard chặn. Ngược lại, người còn nguyên ngân sách nhưng gửi 11 request
> gần như đồng thời sẽ bị rate limit chặn request thứ 11, dù cost guard vẫn cho
> phép về mặt chi phí.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu dùng một endpoint kiểm tra Redis cho cả liveness và readiness, Redis mất
> kết nối sẽ làm cả ba container báo lỗi. Load balancer loại cả ba khỏi traffic,
> rồi liveness probe cho rằng tiến trình chết và lần lượt restart chúng. Redis
> vẫn lỗi nên container mới lại fail probe, tạo vòng lặp restart trong 30 giây;
> các request đang xử lý còn có thể bị gián đoạn. Tách riêng giúp `/health` vẫn
> 200 vì tiến trình còn sống, còn `/ready` trả 503 để chỉ tạm ngừng nhận traffic.
> Khi Redis phục hồi, readiness tự về 200 mà không cần restart ứng dụng.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Với cùng `X-User-Id`, tôi gọi bốn lần và quan sát `history_length` lần lượt là
> `0, 2, 4, 6`; mỗi lượt thêm một message người dùng và một message trả lời vào
> Redis. Khi nhiều replica dùng chung Redis, replica nào nhận request cũng đọc
> cùng lịch sử nên dãy vẫn tăng thống nhất. Nếu dùng dict Python, mỗi container
> có một bản riêng; qua load balancer tôi sẽ thấy số liệu nhảy như `0, 0, 2, 0`
> hoặc tăng theo từng nhánh, và lịch sử mất khi container restart.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Lỗi thật của tôi trên Railway là
> `ValidationError: agent_api_key - Field required [input_value={'port':'8080'}]`,
> sau đó `Application startup failed. Exiting.` và service restart liên tục. Log
> cho thấy Railway đã truyền `PORT=8080` và Uvicorn đã chạy, nên nguyên nhân
> không nằm ở Dockerfile mà là thiếu biến bắt buộc. Tôi thêm `AGENT_API_KEY`
> trong Variables của service ứng dụng và deploy lại. Sau đó `/health` trả 200;
> `/ready` ban đầu trả 503 nên tôi tiếp tục gắn `REDIS_URL` bằng reference
> `${{Redis.REDIS_URL}}`. Sau lần deploy tiếp theo, `/ready` trả
> `{"status":"ready","redis":true}` và POST `/ask` có API key trả 200.
