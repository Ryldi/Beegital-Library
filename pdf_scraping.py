from pdfminer.high_level import extract_text
from io import BytesIO

class PDF_scraper:
  def text_scraper(file_object):
    file_object = BytesIO(file_object)

    text = extract_text(file_object)
    return text