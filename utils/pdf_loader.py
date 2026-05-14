from pypdf import PdfReader


def extract_text_from_pdf(pdf_file):
    text = ""

    pdf_reader = PdfReader(pdf_file)

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text

    return text