from pathlib import Path

from app.utils.security import detect_malicious_content


def test_pdf_binary_stream_is_not_scanned_as_plain_script(tmp_path: Path) -> None:
    pdf = tmp_path / "price-action.pdf"
    pdf.write_bytes(
        b"%PDF-1.7\n1 0 obj\n<< /Length 32 >>\nstream\n"
        b"compressed-binary-exec(-sequence\nendstream\nendobj\n%%EOF"
    )

    assert detect_malicious_content(pdf) is False


def test_text_script_signature_is_still_rejected(tmp_path: Path) -> None:
    markdown = tmp_path / "unsafe.md"
    markdown.write_text("<script>document.cookie</script>", encoding="utf-8")

    assert detect_malicious_content(markdown) is True
