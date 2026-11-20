"""
Application Service: ChatbotService
Điều phối Trợ lý ảo AI Bookie (RAG - Retrieval-Augmented Generation).
Tuân thủ nghiêm ngặt Quy tắc Grounding BR08 và kịch bản tư vấn sách trong Báo cáo Thiết kế.
Tuân thủ chuẩn UML: Trả về Runtime Class ChatbotResult, không dùng DTO.
"""

from typing import Any, Dict, List, Optional

from ...infrastructure.adapters.cloudflare_llm import CloudflareLLMAdapter
from ...infrastructure.repositories.book_repository import BookRepository
from .chatbot_result import ChatbotResult
from .search_service import SearchService

SYSTEM_PROMPT_TEMPLATE = """Bạn là Bookie, trợ lý ảo AI thông minh, nhiệt huyết và là chuyên gia tư vấn văn hóa đọc của Hiệu sách Trực tuyến BookHaven.

THÔNG TIN DANH TÍNH & CÔNG NGHỆ CỦA BẠN:
- Tên: Bookie (Trợ lý ảo AI tư vấn độc quyền của Hiệu sách BookHaven).
- Nền tảng AI: Mô hình ngôn ngữ lớn Meta LLaMA 3.1 8B Instruct, vận hành serverless qua hạ tầng Cloudflare Workers AI.
- Hệ thống RAG (Retrieval-Augmented Generation): Kết hợp mô hình embedding vector đa ngữ all-MiniLM-L6-v2 (384 chiều) để tìm kiếm ngữ nghĩa theo nhu cầu và tâm trạng, cùng thuật toán dHash nhận diện bìa sách.
- Triết lý phục vụ: Thân thiện, tinh tế, am hiểu sách, tôn trọng cảm xúc độc giả và truyền cảm hứng đọc sách sâu sắc.

DỊCH VỤ & CHÍNH SÁCH ĐỘC QUYỀN CỦA BOOKHAVEN:
1. Vận chuyển hỏa tốc bằng Drone (Máy bay không người lái):
   - Áp dụng cho các đơn hàng có tổng khối lượng dưới 2.000g (2kg) trong khu vực nội thành.
   - Thời gian nhận hàng siêu tốc: Chỉ từ 30 - 45 phút.
   - Cước phí: 60.000 đ cố định. Khách hàng có thể theo dõi radar bay trực tiếp trên bản đồ.
2. Vận chuyển tiêu chuẩn: Toàn quốc từ 2 - 4 ngày, cước phí từ 25.000 đ.
3. Phương thức thanh toán:
   - VietQR tự động qua ngân hàng MBBank: Mã QR tạo tự động theo từng đơn, xác thực tức thì qua Background Worker.
   - COD: Thanh toán tiền mặt khi nhận hàng.
4. Đa dạng ấn bản: Mỗi đầu sách có thể có bản Bìa Mềm (Paperback) hoặc Bìa Cứng (Hardcover) với giá bán minh bạch.
5. Danh mục sách chính: Công nghệ Thông tin & Lập trình, Kinh tế & Tài chính, Văn học & Tiểu thuyết, Kỹ năng sống & Phát triển bản thân.

DỮ LIỆU SÁCH CÓ THẬT TRONG KHO BOOKHAVEN (GROUNDING BR08):
{context_books}

NGUYÊN TẮC PHẢN HỒI:
1. KHI NGƯỜI DÙNG HỎI VỀ BẠN (DANH TÍNH, MÔ HÌNH AI, CÔNG NGHỆ, XUẤT XỨ):
   - Giới thiệu bạn là Bookie - trợ lý ảo của BookHaven, giải thích rõ bạn chạy trên mô hình Meta LLaMA 3.1 8B kết hợp RAG và vector embeddings, sẵn sàng hỗ trợ độc giả chọn sách.
2. KHI NGƯỜI DÙNG CHÀO HỎI, CẢM ƠN HOẶC TRÒ CHUYỆN XÃ GIAO:
   - Đáp lại lịch thiệp, ấm áp, mời độc giả chia sẻ gu đọc sách hoặc chủ đề họ quan tâm.
3. KHI NGƯỜI DÙNG HỎI VỀ CHÍNH SÁCH, GIAO DRONE, THANH TOÁN VIETQR:
   - Giải đáp chính xác các thông số và quy trình theo thông tin BookHaven ở trên.
4. KHI NGƯỜI DÙNG HỎI MUA, TƯ VẤN HOẶC TÌM KIẾM SÁCH:
   - Dựa vào danh sách sách có trong kho được cung cấp ở trên.
   - Chỉ giới thiệu sách có thật trong danh sách kho, tuyệt đối không bịa đặt tên sách/giá không có trong danh sách (Grounding BR08).
   - Viết lời bình phẩm, phân tích ngắn gọn nhưng sâu sắc lý do vì sao cuốn sách đó phù hợp với câu hỏi của độc giả.
   - Nếu trong kho không có cuốn sách nào khớp, hãy lịch sự thông báo và khéo léo gợi ý các danh mục sách tương đương đang có tại BookHaven.
   - Khuyến khích người đọc bấm vào nút '+ Giỏ' ở thẻ sách bên dưới để mua nhanh.
5. VĂN PHONG:
   - Tiếng Việt tự nhiên, lịch sự, truyền cảm hứng, độ dài vừa vặn (khoảng 2-4 đoạn ngắn hoặc 3-5 câu), không dài dòng thừa thãi.
"""


class ChatbotService:
    def __init__(
        self,
        book_repo: BookRepository,
        search_service: SearchService,
        llm_adapter: Optional[CloudflareLLMAdapter] = None,
    ):
        self.book_repo = book_repo
        self.search_service = search_service
        self.llm_adapter = llm_adapter or CloudflareLLMAdapter()

    @staticmethod
    def classify_intent(message: str) -> str:
        """
        Phân loại ý định người dùng thành:
        - 'identity_tech': Hỏi về danh tính bot, mô hình AI, kiến trúc, công nghệ
        - 'greeting_chitchat': Chào hỏi, cảm ơn, khen ngợi, xã giao
        - 'policy_service': Hỏi về giao hàng drone, phí ship, thanh toán VietQR, đổi trả
        - 'book_search': Tìm kiếm, hỏi mua, xin gợi ý hoặc hỏi về sách
        """
        msg = message.lower().strip()

        book_explicit_keywords = [
            "sách", "cuốn", "tác phẩm", "tác giả", "tiểu thuyết", "truyện",
            "ấn bản", "bìa cứng", "bìa mềm", "đọc sách", "tìm sách", "mua sách",
            "gợi ý sách", "tư vấn sách", "giá bao nhiêu", "còn hàng không",
        ]
        has_book_intent = any(kw in msg for kw in book_explicit_keywords)

        tech_keywords = [
            "mô hình nào", "model nào", "llama", "llm", "ai nào", "công nghệ gì",
            "là ai", "tên gì", "giới thiệu về bạn", "bạn là gì", "ai tạo ra",
            "cloudflare", "rag", "embedding", "vector",
        ]
        if any(kw in msg for kw in tech_keywords) and not has_book_intent:
            return "identity_tech"

        greeting_keywords = [
            "xin chào", "chào bạn", "hello", "hi bookie", "chào bookie", "alo",
            "cảm ơn", "thank", "tks", "tuyệt vời", "bye", "tạm biệt",
        ]
        if any(kw in msg for kw in greeting_keywords) and not has_book_intent and len(msg.split()) <= 4:
            return "greeting_chitchat"

        policy_keywords = [
            "drone", "máy bay", "hỏa tốc", "giao hàng", "vận chuyển", "phí ship",
            "bao lâu", "vietqr", "mbbank", "ngân hàng", "thanh toán", "chuyển khoản",
            "đổi trả", "bảo hành", "hoàn tiền", "ship bao nhiêu",
        ]
        if any(kw in msg for kw in policy_keywords) and not has_book_intent:
            return "policy_service"

        return "book_search"

    def process_message(self, message: str) -> ChatbotResult:
        """
        Xử lý thông điệp người dùng qua kiến trúc RAG 2 tầng:
        1. Phân loại ý định (Intent Routing).
        2. Nếu hỏi về sách: Truy xuất kho sách thực (Retrieval qua Semantic Search) và Lọc Grounding (BR08).
        3. Tạo System Prompt đã nhúng ngữ cảnh sách thật (Augmentation).
        4. Gọi Cloudflare LLM Adapter để sinh câu trả lời tự nhiên (Generation).
        """
        clean_msg = message.strip()
        intent = self.classify_intent(clean_msg)

        if intent == "identity_tech":
            context_str = (
                "Người dùng đang hỏi về danh tính, nguồn gốc, công nghệ hoặc mô hình AI của bạn. "
                "Hãy tự tin giới thiệu bạn là Bookie, vận hành trên mô hình Meta LLaMA 3.1 8B Instruct "
                "qua Cloudflare Workers AI kết hợp kỹ thuật RAG với all-MiniLM-L6-v2. Trả lời thân thiện, "
                "thông minh, không đính kèm thẻ sách khi người dùng không hỏi mua sách."
            )
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_books=context_str)
            llm_reply = self.llm_adapter.generate_chat_response(system_prompt, clean_msg)
            return ChatbotResult(reply=llm_reply, suggested_books=[])

        elif intent == "greeting_chitchat":
            context_str = (
                "Người dùng đang chào hỏi, cảm ơn hoặc giao tiếp xã giao. "
                "Hãy chào đón nhiệt tình, phong thái nhã nhặn, giới thiệu các danh mục sách thế mạnh "
                "của BookHaven và sẵn sàng hỗ trợ độc giả chọn sách."
            )
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_books=context_str)
            llm_reply = self.llm_adapter.generate_chat_response(system_prompt, clean_msg)
            return ChatbotResult(reply=llm_reply, suggested_books=[])

        elif intent == "policy_service":
            context_str = (
                "Người dùng đang hỏi về dịch vụ hoặc chính sách của BookHaven (như giao hàng Drone hỏa tốc "
                "dưới 2kg trong 30-45 phút phí 60.000đ, giao tiêu chuẩn 2-4 ngày, quét VietQR MBBank tự động, COD). "
                "Hãy giải đáp chi tiết, chính xác các chính sách này mà không đính kèm thẻ sách ngẫu nhiên."
            )
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_books=context_str)
            llm_reply = self.llm_adapter.generate_chat_response(system_prompt, clean_msg)
            return ChatbotResult(reply=llm_reply, suggested_books=[])

        # intent == "book_search": RAG đầy đủ với Quy tắc Grounding BR08
        search_res = self.search_service.search_semantic(
            clean_msg, limit=3, min_threshold=0.35
        )

        suggested_books: List[Dict[str, Any]] = []
        context_lines: List[str] = []

        clean_lower = clean_msg.lower()
        query_words = [
            w for w in clean_lower.replace(",", " ").replace(".", " ").split() if len(w) > 2
        ]

        for item in search_res.results:
            title = item.get("title", "") if isinstance(item, dict) else getattr(item, "title", "")
            author = item.get("author_name", "") if isinstance(item, dict) else getattr(item, "author_name", "")
            desc = item.get("description", "") if isinstance(item, dict) else getattr(item, "description", "")
            sim_score = item.get("similarity_score", 0.0) if isinstance(item, dict) else getattr(item, "similarity_score", 0.0)
            book_id = item.get("book_id") if isinstance(item, dict) else getattr(item, "book_id")
            cover_image = item.get("cover_image") if isinstance(item, dict) else getattr(item, "cover_image")

            item_text = f"{title} {author} {desc}".lower()
            has_word_match = any(w in item_text for w in query_words)
            is_relevant = sim_score >= 0.40 or has_word_match

            if not is_relevant and len(search_res.results) > 0:
                first_item = search_res.results[0]
                first_id = first_item.get("book_id") if isinstance(first_item, dict) else getattr(first_item, "book_id")
                if first_id == book_id and sim_score >= 0.35:
                    is_relevant = True

            if not is_relevant:
                continue

            editions = self.book_repo.get_editions_by_book_id(book_id)
            for ed in editions:
                avail = ed.get_available_stock()
                if avail > 0:
                    suggested_books.append({
                        "book_id": str(book_id),
                        "title": title,
                        "author_name": author,
                        "unit_price": ed.unit_price,
                        "binding_type": getattr(ed, "binding_type", "Standard"),
                        "edition_id": str(ed.product_id),
                        "cover_image": cover_image,
                        "available_stock": avail,
                    })
                    context_lines.append(
                        f"- Tên: '{title}' | Tác giả: {author} | Bản: {getattr(ed, 'binding_type', 'Standard')} | "
                        f"Giá: {ed.unit_price:,} đ | Còn: {avail} cuốn | Tóm tắt: {desc[:120]}"
                    )
                    break

        if context_lines:
            context_str = "\n".join(context_lines)
        else:
            context_str = (
                "Hiện tại kho sách của BookHaven chưa có tựa sách nào khớp hoàn toàn với yêu cầu này của khách. "
                "Hãy lịch sự xin lỗi và gợi ý độc giả khám phá các danh mục sách có sẵn: Công nghệ Thông tin, "
                "Kinh tế & Tài chính, Văn học hoặc Kỹ năng sống."
            )

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_books=context_str)
        llm_reply = self.llm_adapter.generate_chat_response(system_prompt, clean_msg)
        return ChatbotResult(reply=llm_reply, suggested_books=suggested_books)
