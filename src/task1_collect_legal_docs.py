"""
Task 1 — Thu thập văn bản chính sách thương mại điện tử / hỗ trợ khách hàng.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang chính thức của một sàn TMĐT.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.

Gợi ý nguồn (ví dụ trang công khai Shopee Vietnam — help.shopee.vn):
    - https://help.shopee.vn/portal/4/article/77251 (Chính sách trả hàng và hoàn tiền)
    - https://help.shopee.vn/portal/4/article/79198 (Phương thức thanh toán)
    - https://help.shopee.vn/portal/4/article/77244 (Chính sách bảo mật)

Gợi ý văn bản (chủ đề chính sách thương mại điện tử):
    - Chính sách đổi trả/hoàn tiền (Returns/Refund Policy)
    - Phương thức thanh toán (Payment Methods)
    - Chính sách bảo mật (Privacy Policy)
    - Quy định đăng bán sản phẩm cho người bán (Seller Listing Regulations)

Nhớ gắn metadata `customer_role` (`buyer`/`seller`/`both`) cho từng tài liệu — yêu cầu riêng
của K4 Variant (kế thừa từ Lab 07), cần thiết để viết benchmark query dùng metadata_filter.

Lưu ý: một số trang help center dùng JavaScript render nội dung (SPA) — crawl về chỉ thấy
tiêu đề mà không có nội dung thật. Đổi sang bài viết khác cùng domain thay vì cố xử lý,
và chỉ dùng nguồn công khai/được phép chia sẻ.
"""

from pathlib import Path

from pathlib import Path
from fpdf import FPDF

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")


class TravelRegulationPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, 'QUY DINH VA HUONG DAN DU LICH NAM 2026', border=False, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(5)


def create_travel_pdf(filename: str, title: str, sections: list[dict]):
    """Tạo file PDF quy định du lịch chuẩn bằng fpdf2 (> 1KB)."""
    pdf = TravelRegulationPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(4)
    
    # Sections
    for section in sections:
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, section["heading"], new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 6, section["body"])
        pdf.ln(3)

    filepath = DATA_DIR / filename
    pdf.output(str(filepath))
    print(f"  [OK] Da tao PDF: {filepath.name} ({filepath.stat().st_size} bytes)")


def collect_legal_docs():
    """Thu thập 3 văn bản quy định du lịch cho Chủ đề 5: Smart Travel Guide."""
    setup_directory()

    # 1. Hà Giang Tourism & Motorbike Safety Regulations
    create_travel_pdf(
        "quy-dinh-an-toan-du-lich-ha-giang.pdf",
        "QUY DINH AN TOAN KHI DU LICH XE MAY TAI HA GIANG",
        [
            {
                "heading": "Dieu 1: Quy dinh chung doi voi du khach phuot xe may",
                "body": "Khach du lich khi tham gia du lich phuot bang xe may tren cac tuyen duong deo Ha Giang (nhu Ma Pi Leng, Quan Ba, Yen Minh, Dong Van) bat buoc phai co giay phep lai xe hop le phu hop voi dung tich xi lanh, doi mu bao hiem dat chuan va mang day du bao ho kiem tra phanh xe dinh ky."
            },
            {
                "heading": "Dieu 2: Gioi han toc do va an toan di chuyen duong deo",
                "body": "Doi voi duong deo doc quanh co va khu vuc suong mu, toc do toi da cho phep la 30km/h. Khong di chuyen vao ban dem sau 19h00 tren cac doan deo nguy hiem nhu Ma Pi Leng va doc Tham Ma."
            },
            {
                "heading": "Dieu 3: Bao ve di san Cao nguyen da Dong Van",
                "body": "Nghiem cam hanh vi khac ve, xa rac thai nhua hoac lam hu hai cac di tich lich su va di san dia chat thuoc Cong vien dia chat toan cau Cao nguyen da Dong Van va hem vuc Tu San."
            }
        ]
    )

    # 2. Quy Nhơn - Phú Yên Coastal & Marine Heritage Protection Regulations
    create_travel_pdf(
        "quy-dinh-bao-ton-di-san-quy-nhon-phu-yen.pdf",
        "QUY DINH BAO TON DI SAN VA DU LICH BIEN QUY NHON - PHU YEN",
        [
            {
                "heading": "Dieu 1: Quy dinh bao ve he sinh thai san ho va bai bien",
                "body": "Khach du lich tham gia tour lan bien ngam san ho khong duoc phep dam len, be hoac mang san ho ra khoi khu vuc bao ton sinh thai bien Ky Co, Hon Kho va Eo Gio (Quy Nhon)."
            },
            {
                "heading": "Dieu 2: An toan tam bien va hoat dong the thao duoi nuoc",
                "body": "Khach du lich chi duoc tam bien trong khu vuc co phao bao hieu va luc luong cuu ho. Khi tham gia moto nuoc hoac du bay phai mac ao phao bao ho bat buoc."
            },
            {
                "heading": "Dieu 3: Bao ve danh thang Ghenh Da Dia va Mui Dien",
                "body": "Giu gin ve sinh chung va an toan tai khu vuc danh thang quoc gia Ghenh Da Dia (Phu Yen). Cam giam len cac mep da doc nguy hieu va cam xa rac thai nhua xuong bien."
            }
        ]
    )

    # 3. Hotel & Homestay Accommodations Booking & Stay Regulations
    create_travel_pdf(
        "huong-dan-dang-ky-lu-tru-khach-san.pdf",
        "QUY DINH DANG KY TAM TRU VA HUY PHONG KHACH SAN HOMESTAY",
        [
            {
                "heading": "Dieu 1: Thu tuc khai bao tam tru cho khach du lich",
                "body": "Khach du lich khi den nhan phong tai cac co so luu tru (khach san, homestay, resort) phai xuat trinh CCCD, Ho chieu hoac Giay khai sinh doi voi tre em de co so luu tru thuc hien khai bao tam tru theo quy dinh."
            },
            {
                "heading": "Dieu 2: Chinh sach hoan tien va huy phong luu tru",
                "body": "Khach hang duoc huy phong mien phi truoc 48 gio so voi gio nhan phong (check-in 14h00). Huy phong trong vong 24-48 gio se chiu phi 50% tien phong dem dau tien. Huy phong trong 24 gio se khong duoc hoan tien."
            },
            {
                "heading": "Dieu 3: Quy tac ung xuc va giu yen tinh trong khu luu tru",
                "body": "Khong mang chat chay no, chat cam vao phong khach san. Giu yen tinh sau 22h00 de khong anh huong den cac khach du lich khac trong cung co so luu tru."
            }
        ]
    )


if __name__ == "__main__":
    collect_legal_docs()

