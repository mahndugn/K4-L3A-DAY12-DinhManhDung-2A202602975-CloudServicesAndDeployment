"""Curated offline FAQ. Specific topics precede generic ones; no external LLM."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    phrases: tuple[str, ...]
    question: str
    answer: str


TOPICS = (
    Topic("multi_stage", "Docker multi-stage", ("multi stage", "multistage", "nhieu stage"),
          "Docker multi-stage là gì?",
          "Multi-stage dùng nhiều FROM trong Dockerfile. Stage builder cài dependency; "
          "runtime chỉ COPY --from=builder những thành phần cần chạy. Build tools có thể "
          "được loại khỏi image cuối. Mức giảm dung lượng phụ thuộc nội dung từng stage; "
          "multi-stage không tự tạo non-root user, cần khai báo USER riêng."),
    Topic("probes", "Health và readiness", ("readiness", "liveness", "health", "healthcheck", "ready", "probe"),
          "Readiness probe khác health check thế nào?",
          "Health check là tên chung cho kiểm tra sức khỏe. Trong CloudOps Assistant, "
          "/health là liveness: không gọi Redis; /ready là readiness: PING Redis và trả "
          "503 nếu Redis lỗi. Khi được cấu hình, orchestrator có thể restart container "
          "sau khi liveness thất bại đủ ngưỡng, còn readiness loại instance khỏi traffic. "
          "Docker Compose đơn thuần chỉ đánh dấu unhealthy, không tự restart vì trạng thái đó."),
    Topic("rate_limit", "Rate limit", ("rate limit", "rate limiting", "429", "sliding window", "gioi han request"),
          "Rate limit dùng Redis để làm gì?",
          "Rate limit giới hạn số request mỗi user trong 60 giây gần nhất. Redis Sorted Set "
          "lưu timestamp: xóa request cũ, đếm, kiểm tra rồi thêm member duy nhất và TTL. "
          "Vượt quota trả 429 kèm Retry-After trước khi gọi mock LLM. Bản lab dùng nhiều "
          "lệnh Redis riêng; production cần thao tác atomic như Lua để tránh vượt quota khi chạy đồng thời."),
    Topic("budget", "Ngân sách mô phỏng", ("cost guard", "cost", "budget", "chi phi", "ngan sach", "402"),
          "Cost guard khác rate limit thế nào?",
          "Rate limit đếm request, cost guard đếm chi phí theo user và tháng UTC. "
          "Key cost:<user>:<YYYY-MM> lưu tổng; vượt ngân sách thì trả 402. Lab kiểm tra "
          "chi phí đã ghi nhận trước lượt gọi rồi cộng chi phí sau đó, nên không bảo đảm "
          "trần tuyệt đối cho lượt đang chạy. Tokens và USD là số mô phỏng, không có hóa đơn LLM."),
    Topic("auth", "Xác thực API", ("api key", "authentication", "xac thuc", "401", "compare digest"),
          "API key bảo vệ CloudOps Assistant như thế nào?",
          "POST /ask yêu cầu X-API-Key khớp AGENT_API_KEY và so sánh constant-time bằng "
          "secrets.compare_digest. Thiếu hoặc sai khóa trả 401. Khóa nằm trong .env local "
          "hoặc secret store khi deploy. X-User-Id là nhãn demo do client cung cấp, không "
          "phải danh tính đã xác thực; production cần gắn user với credential riêng."),
    Topic("shutdown", "Graceful shutdown", ("shutdown", "sigterm", "sigint", "tat an toan"),
          "Graceful shutdown khi deploy Docker hoạt động ra sao?",
          "SIGTERM yêu cầu server ngừng nhận việc mới, hoàn tất request đang chạy rồi thoát. "
          "Lifecycle bật cờ shutting_down và chuyển tín hiệu cho handler cũ của Uvicorn. "
          "CMD dùng exec để Uvicorn nhận tín hiệu trực tiếp; quá thời gian chờ, runtime có "
          "thể SIGKILL. Kiểm tra thực tế bằng log khi dừng container."),
    Topic("cache", "Docker build cache", ("build cache", "layer cache", "cache", "pip install", "requirements"),
          "Vì sao copy requirements trước source code?",
          "COPY requirements.txt rồi RUN pip install trước khi COPY app và utils giúp "
          "tái sử dụng layer dependency khi chỉ đổi code. Nếu COPY toàn bộ source trước "
          "pip install, thay đổi code có thể làm bước cài thư viện chạy lại."),
    Topic("network", "Mạng container", ("localhost", "network", "mang container", "6379", "connection refused"),
          "Vì sao Docker không kết nối Redis qua localhost?",
          "localhost trong container là chính container đó. Agent trong Compose dùng "
          "redis://redis:6379/0 với redis là tên service; Python chạy trên Windows dùng "
          "redis://localhost:6379/0 qua cổng publish. Kiểm tra docker compose ps và "
          "docker compose exec redis redis-cli ping để xác nhận Redis phản hồi PONG."),
    Topic("compose", "Docker Compose", ("compose",),
          "Docker Compose chạy CloudOps Assistant thế nào?",
          "Compose khai báo agent và redis trong cùng mạng. docker compose up -d --build "
          "build agent rồi khởi động stack; agent đợi Redis healthy. Dùng docker compose ps "
          "để xem trạng thái và docker compose logs agent để xem log. Không scale nhiều "
          "agent với cùng host port 8000:8000; cần bỏ cổng cố định và đặt load balancer phía trước."),
    Topic("volume", "Redis persistence và volume", ("volume", "persistence", "appendonly", "aof", "luu ben vung"),
          "Redis volume dùng để làm gì?",
          "Compose bật Redis AOF và gắn volume redis-data vào /data để dữ liệu tồn tại "
          "qua việc tạo lại container. History vẫn có TTL 7 ngày và giữ tối đa 20 message. "
          "Volume không phải backup; docker compose down -v xóa volume và dữ liệu của stack."),
    Topic("config", "Environment và secrets", ("12 factor", "environment", "env", "secret", "cau hinh"),
          "Vì sao cấu hình phải nằm trong biến môi trường?",
          "Cùng code/image dùng ở local và cloud, nhưng PORT, REDIS_URL và AGENT_API_KEY "
          "khác nhau. Settings đọc environment hoặc .env; thiếu API key phải fail fast. "
          "Không commit .env hoặc nhúng key vào Dockerfile. .dockerignore ngăn secret "
          "đi vào build context; .gitignore ngăn Git theo dõi file mới."),
    Topic("logging", "Structured logging", ("logging", "log", "json", "nhat ky"),
          "Log JSON giúp vận hành CloudOps Assistant thế nào?",
          "Mỗi log là một JSON trên stdout có event, level và timestamp UTC. ask_completed "
          "thêm user_id, tokens_in, tokens_out và cost_usd mô phỏng để lọc và đếm sự kiện. "
          "Xem bằng docker compose logs agent. Không ghi API key hoặc toàn bộ câu hỏi vào log."),
    Topic("redis", "Redis và stateless scaling", ("redis", "stateless", "scale", "scaling", "history", "lich su"),
          "Redis giúp scale agent ra sao?",
          "Redis lưu history, quota và chi phí ngoài RAM của agent. Các instance dùng "
          "cùng Redis và user_id sẽ đọc cùng state. History dùng List, giữ 20 message "
          "gần nhất với TTL 7 ngày. fake:// chỉ là RAM để thử local, không chia sẻ giữa "
          "container và không dùng cho demo scale hoặc cloud."),
    Topic("deployment", "Cloud deployment", ("deploy", "deployment", "railway", "render", "port"),
          "Deploy CloudOps Assistant lên cloud cần gì?",
          "Build image, bind 0.0.0.0 và đọc PORT do nền tảng cấp. Thiết lập AGENT_API_KEY "
          "và REDIS_URL tới Redis thật, rồi kiểm tra HTTPS /health, /ready và /ask. "
          "Ghi URL và output thật vào DEPLOYMENT.md. Không dùng localhost làm Redis URL "
          "giữa các dịch vụ cloud riêng biệt."),
    Topic("docker", "Docker, image và container", ("docker", "image", "container", "dockerfile"),
          "Docker image khác container thế nào?",
          "Docker image là gói filesystem và cấu hình để chạy ứng dụng; container là "
          "instance đang chạy từ image. Dockerfile mô tả cách build image CloudOps "
          "Assistant gồm Python, dependency và source. Redis chạy trong container riêng, "
          "hai service giao tiếp qua mạng Compose."),
    Topic("cloud", "Cloud cơ bản", ("cloud", "dien toan dam may", "devops"),
          "Cloud là gì?",
          "Cloud cung cấp tài nguyên tính toán, lưu trữ và mạng qua dịch vụ từ xa. "
          "Trong lab này, bạn triển khai container CloudOps Assistant và Redis lên nền "
          "tảng cloud để người khác gọi qua HTTPS. Docker đóng gói ứng dụng; nền tảng "
          "cloud cung cấp nơi chạy, mạng và quản lý vòng đời service."),
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def match_topic(question: str) -> Topic | None:
    text = f" {normalize(question)} "
    matches = [topic for topic in TOPICS
               if any(f" {phrase} " in text for phrase in topic.phrases)]
    # Comparing budget with rate limiting should explain both mechanisms.
    if any(topic.id == "budget" for topic in matches):
        return next(topic for topic in matches if topic.id == "budget")
    return matches[0] if matches else None


def topic_catalog() -> list[dict]:
    return [{"id": topic.id, "title": topic.title, "example_question": topic.question}
            for topic in TOPICS]


def answer_question(question: str, history: list[dict]) -> str:
    topic = match_topic(question)
    if topic is None and normalize(question) in {
        "giai thich them", "noi ro hon", "cho vi du", "vi du", "explain more", "tell me more",
    }:
        for turn in reversed(history):
            if turn.get("role") == "user":
                topic = match_topic(turn.get("content", ""))
                if topic:
                    return f"Về {topic.title}: {topic.answer}"
        return "Bạn muốn giải thích thêm chủ đề nào? Ví dụ: Docker multi-stage hoặc Redis scaling."
    if topic:
        return topic.answer
    return (
        "CloudOps Assistant là FAQ offline về Cloud và Docker. Mình chưa có câu trả lời "
        "phù hợp trong bộ kiến thức hiện tại. Bạn có thể hỏi: Docker image khác container "
        "thế nào, readiness khác liveness ra sao, hoặc Redis giúp scale agent ra sao?"
    )
