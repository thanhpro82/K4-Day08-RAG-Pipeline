import json
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.is_file() and filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting PDF: {filepath.name}")
            output_path = output_dir / f"{filepath.stem}.md"
            
            try:
                result = md.convert(str(filepath))
                content = result.text_content
                if not content or len(content) < 100:
                    raise ValueError("MarkItDown extracted empty text")
            except Exception as e:
                print(f"  [Info] MarkItDown parser info for {filepath.name}: {e}. Fallback sang pypdfium2.")
                # Fallback using pypdfium2
                import pypdfium2 as pdfium
                pdf = pdfium.PdfDocument(filepath)
                text_pages = []
                for page in pdf:
                    textpage = page.get_textpage()
                    text_pages.append(textpage.get_text_range())
                content = "\n\n".join(text_pages)

            # Ensure header format for legal document
            if not content.startswith("#"):
                clean_title = filepath.stem.replace("-", " ").title()
                content = f"# {clean_title}\n\n{content}"

            output_path.write_text(content, encoding="utf-8")
            print(f"  [OK] Saved: {output_path.name} ({len(content)} chars)")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.is_file() and filepath.suffix.lower() == ".json":
            print(f"Converting JSON: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            output_path = output_dir / f"{filepath.stem}.md"

            # Thêm metadata header
            header = f"# {data.get('title', 'Cẩm Nang Du Lịch')}\n\n"
            header += f"**Source:** {data.get('url', 'N/A')}\n"
            header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"

            content = header + data.get("content_markdown", "")
            output_path.write_text(content, encoding="utf-8")
            print(f"  [OK] Saved: {output_path.name} ({len(content)} chars)")


def convert_all():
    """Convert toàn bộ files trong data/landing/ sang data/standardized/."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n[OK] Done! Output tai:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()

