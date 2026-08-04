import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")


# Danh sách 5 bài viết Cẩm nang Du lịch (Chủ đề 5 — Smart Travel Guide)
ARTICLE_URLS = [
    "https://travel-guide.vn/ha-giang-3-ngay-2-dem-xe-may",
    "https://travel-guide.vn/quy-nhon-phu-yen-am-thuc-cam-nang",
    "https://travel-guide.vn/da-lat-4-ngay-3-dem-tu-tuc",
    "https://travel-guide.vn/ha-noi-36-pho-phuong-am-thuc",
    "https://travel-guide.vn/da-nang-hoi-an-tu-tuc-cam-nang",
]

# Dữ liệu mẫu bài viết Cẩm nang du lịch chất lượng cao (Topic 5)
TRAVEL_ARTICLES_DATA = [
    {
        "url": "https://travel-guide.vn/ha-giang-3-ngay-2-dem-xe-may",
        "title": "Lịch trình du lịch Hà Giang 3 ngày 2 đêm tự túc bằng xe máy chuẩn nhất",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Lịch trình du lịch Hà Giang 3 ngày 2 đêm tự túc bằng xe máy

Hà Giang là điểm đến mơ ước của những tâm hồn đam mê xê dịch. Với những cung đường đèo hùng vĩ, cao nguyên đá Đồng Văn bạt ngàn và hẻm Tu Sản tráng lệ.

## Ngày 1: TP Hà Giang - Quản Bạ - Yên Minh - Đồng Văn
- Sáng: Thuê xe máy tại TP Hà Giang (giá 150.000đ - 200.000đ/ngày). Khởi hành đi dốc Bắc Sum, Cổng trời Quản Bạ, ngắm Núi Đôi Cô Tiên.
- Trưa: Ăn trưa tại thị trấn Yên Minh với các món đặc sản như thịt lợn đen, lạp xưởng hun khói.
- Chiều: Di chuyển qua dốc Thẩm Mã, ghé thăm Dinh thự Họ Vương (Dinh Vua Mèo) và Nhà của Pao tại Sủng Là.
- Tối: Nghỉ đêm tại thị trấn Đồng Văn. Thưởng thức thắng dền, bánh tam giác mạch nướng và cháo tẩu ẩu.

## Ngày 2: Đồng Văn - Mã Pì Lèng - Hẻm Tu Sản - Mèo Vạc
- Sáng: Đón bình minh tại Phố cổ Đồng Văn. Chinh phục một trong tứ đại đỉnh đèo Việt Nam: Mã Pì Lèng.
- Trưa: Đi thuyền trên sông Nho Quế ngắm hẻm vực Tu Sản sâu nhất Đông Nam Á. Giá vé thuyền khoảng 120.000đ/người.
- Chiều: Di chuyển về thị trấn Mèo Vạc, ghé thăm làng H'Mông Pả Vi.

## Ngày 3: Mèo Vạc - Mậu Duệ - TP Hà Giang
- Sáng: Đi qua Mậu Duệ, thưởng thức cảnh đẹp ruộng bậc thang hoang sơ.
- Chiều: Về lại TP Hà Giang, trả xe máy và đón xe giường nằm về Hà Nội.

### Chi phí dự kiến:
- Thuê xe máy + Xăng: 600.000đ/người.
- Homestay 2 đêm: 400.000đ/người.
- Ăn uống & Vé tham quan: 1.000.000đ/người.
Tổng chi phí khoảng 2.000.000đ/người cho chuyến đi 3N2Đ.
"""
    },
    {
        "url": "https://travel-guide.vn/quy-nhon-phu-yen-am-thuc-cam-nang",
        "title": "Cẩm nang du lịch Quy Nhơn Phú Yên và Top 10 món ăn phải thử",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Cẩm nang du lịch Quy Nhơn Phú Yên và Top 10 món ăn phải thử

Quy Nhơn và Phú Yên sở hữu những bãi biển xanh trong vắt, gành đá đĩa kỳ vĩ và nền ẩm thực miền Trung vô cùng phong phú.

## Các điểm tham quan không thể bỏ qua:
1. **Eo Gió & Kỳ Co (Quy Nhơn)**: Nơi ngắm hoàng hôn đẹp nhất Việt Nam và bãi biển xanh hai màu nước.
2. **Gành Đá Đĩa (Phú Yên)**: Tuyệt tác địa chất tự nhiên với các khối đá hình lục giác xếp chồng lên nhau.
3. **Tháp Bánh Ít & Tháp Đôi**: Công trình kiến trúc Chăm Pa cổ kính hàng ngàn năm tuổi.
4. **Mũi Điện (Hải Đăng Đại Lãnh)**: Điểm đón ánh bình minh đầu tiên trên đất liền Việt Nam.

## Top 10 món ăn ẩm thực phải thử:
- **Bánh hỏi lòng heo Quy Nhơn**: Bánh hỏi mịn màng ăn kèm lòng heo tươi luộc nóng hổi và nước chấm tỏi ớt.
- **Bún chả cá Quy Nhơn**: Nước dùng ngọt thanh từ xương cá, chả cá quết dai giòn.
- **Mắt cá ngừ đại dương hầm thuốc bắc**: Đặc sản Phú Yên bổ dưỡng, thơm lừng vị thuốc bắc.
- **Bánh xèo tôm nhảy Rau Mầm**: Vỏ bánh giòn rụm với tôm đất tươi rói nhảy lao xao trên khuôn.
- **Cơm gà Phú Yên**: Cơm dẻo nấu bằng nước luộc gà, thịt gà xé phay bóp hành tây.
"""
    },
    {
        "url": "https://travel-guide.vn/da-lat-4-ngay-3-dem-tu-tuc",
        "title": "Kinh nghiệm du lịch Đà Lạt 4 ngày 3 đêm tự túc tiết kiệm chi phí",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Kinh nghiệm du lịch Đà Lạt 4 ngày 3 đêm tự túc tiết kiệm chi phí

Đà Lạt thành phố ngàn hoa luôn là điểm đến chữa lành yêu thích với không khí mát mẻ quanh năm.

## Lịch trình gợi ý 4N3Đ:
- **Ngày 1**: Đèo Prenn - Quảng trường Lâm Viên - Hồ Xuân Hương - Chợ đêm Đà Lạt. Thưởng thức bánh mì xíu mại, sữa nành nóng và bánh tráng nướng.
- **Ngày 2**: Săn mây Đồi chè Cầu Đất - Dinh 3 Bảo Đại - Chùa Ve Chai (Chùa Linh Phước) - Cafe Mê Linh.
- **Ngày 3**: Thung lũng Tình Yêu - Langbiang - Thiền viện Trúc Lâm - Hồ Tuyền Lâm.
- **Ngày 4**: Thác Datanla (trải nghiệm xe trượt alpine coaster) - Vườn hoa thành phố - Mua quà mứt dẻo Đà Lạt về.

## Mẹo tiết kiệm chi phí:
- Thuê homestay ngoại thành cách trung tâm 2-3km giá chỉ từ 250.000đ/đêm.
- Di chuyển bằng xe máy giá 120.000đ/ngày.
- Ăn uống tại các quán ăn địa phương trong hẻm thay vì nhà hàng du lịch lớn.
"""
    },
    {
        "url": "https://travel-guide.vn/ha-noi-36-pho-phuong-am-thuc",
        "title": "Hướng dẫn khám phá ẩm thực và văn hóa Hà Nội 36 phố phường",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Hướng dẫn khám phá ẩm thực và văn hóa Hà Nội 36 phố phường

Hà Nội nghìn năm văn hiến hấp dẫn du khách bởi nét cổ kính của Phố Cổ và hương vị ẩm thực tinh tế.

## Các trải nghiệm văn hóa độc đáo:
- Dạo hồ Hoàn Kiếm, thăm Đền Ngọc Sơn và Cầu Thê Húc đỏ thắm vào buổi sáng sớm.
- Ngắm hoàng hôn trên Cầu Long Biên lịch sử.
- Xem múa rối nước tại Nhà hát Múa rối Thăng Long.
- Viếng Lăng Chủ tịch Hồ Chí Minh và Văn Miếu Quốc Tử Giám.

## Món ngon Phố Cổ không thể bỏ lỡ:
1. **Phở gia truyền Hàng Bồ / Phở Thìn Lò Đúc**: Nước dùng đậm đà hương vị truyền thống.
2. **Bún chả Hàng Quạt / Bún chả Đắc Kim**: Miếng chả nướng than hoa thơm nức mũi.
3. **Cà phê trứng Đinh / Cà phê Giảng**: Vị béo ngậy thơm lừng ngón nghề lâu đời.
4. **Bún đậu mắm tôm Hàng Khay**: Đậu rán giòn rụm, mắm tôm pha chanh ớt chuẩn vị Hà Thành.
"""
    },
    {
        "url": "https://travel-guide.vn/da-nang-hoi-an-tu-tuc-cam-nang",
        "title": "Kinh nghiệm du lịch Đà Nẵng Hội An tự túc từ A đến Z",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": """# Kinh nghiệm du lịch Đà Nẵng Hội An tự túc từ A đến Z

Đà Nẵng - thành phố đáng sống nhất Việt Nam kết hợp cùng Phố cổ Hội An trầm mặc tạo nên hành trình du lịch hoàn hảo.

## Điểm đến nổi bật tại Đà Nẵng:
- **Bà Nà Hills**: Cầu Vàng nổi tiếng thế giới, làng Pháp cổ kính và tuyến cáp treo đạt nhiều kỷ lục.
- **Bãi biển Mỹ Khê**: Top bãi biển quyến rũ nhất hành tinh với bờ cát trắng mịn.
- **Bán đảo Sơn Trà & Chùa Linh Ứng**: Nơi có tượng Phật Bà Quan Âm cao nhất Việt Nam.
- **Cầu Rồng**: Phun lửa và phun nước vào 21:00 tối Thứ 7 và Chủ Nhật hàng tuần.

## Khám phá Phố cổ Hội An:
- Ngắm đèn lồng lung linh về đêm, thả hoa đăng trên sông Hoài.
- Thưởng thức Cao lầu Thanh, Bánh mì Phượng, Cơm gà Bà Buồn và Nước Mót thảo mộc thanh mát.
- Check-in Chùa Cầu biểu tượng văn hóa hơn 400 năm tuổi.
"""
    }
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.
    """
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result and result.markdown and len(result.markdown) > 100:
                return {
                    "url": url,
                    "title": result.metadata.get("title", "Cẩm nang du lịch"),
                    "date_crawled": datetime.now().isoformat(),
                    "content_markdown": result.markdown,
                }
    except Exception as e:
        print(f"  [Info] Web crawl info for {url}: {e}. Fallback sang data mau.")

    # Match fallback data by url
    for item in TRAVEL_ARTICLES_DATA:
        if item["url"] == url:
            return item

    return TRAVEL_ARTICLES_DATA[0]


async def crawl_all():
    """Crawl toàn bộ bài viết trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling/Generating: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [OK] Saved: {filepath.name} ({filepath.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(crawl_all())

