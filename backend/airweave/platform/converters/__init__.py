"""Text converters for converting files and URLs to markdown."""

from .code_converter import CodeConverter
from .html_converter import HtmlConverter
from .mistral_converter import MistralConverter
from .simple_docx_converter import SimpleDocxConverter
from .simple_image_converter import SimpleImageConverter
from .simple_pdf_converter import SimplePdfConverter
from .simple_pptx_converter import SimplePptxConverter
from .txt_converter import TxtConverter
from .web_converter import WebConverter
from .xlsx_converter import XlsxConverter

# LLM-based converters
mistral_converter = MistralConverter()

# Simple (API-free) converters
simple_pdf_converter = SimplePdfConverter()
simple_docx_converter = SimpleDocxConverter()
simple_pptx_converter = SimplePptxConverter()
simple_image_converter = SimpleImageConverter()

# Other converters
html_converter = HtmlConverter()
xlsx_converter = XlsxConverter()  # Local openpyxl extraction (not Mistral)
txt_converter = TxtConverter()
code_converter = CodeConverter()
web_converter = WebConverter()  # URL fetching and HTML to markdown

# Aliases for backward compatibility
pdf_converter = mistral_converter  # PDF uses Mistral OCR by default
docx_converter = mistral_converter  # DOCX uses Mistral OCR by default
pptx_converter = mistral_converter  # PPTX uses Mistral OCR by default
img_converter = mistral_converter  # Images use Mistral OCR by default

__all__ = [
    "mistral_converter",
    "simple_pdf_converter",
    "simple_docx_converter",
    "simple_pptx_converter",
    "simple_image_converter",
    "pdf_converter",
    "docx_converter",
    "img_converter",
    "html_converter",
    "pptx_converter",
    "txt_converter",
    "xlsx_converter",
    "code_converter",
    "web_converter",
]
