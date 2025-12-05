"""Simple PDF text extraction using PyPDF2 and pdfminer.six."""

import asyncio
from pathlib import Path
from typing import Dict, List

from pdfminer.high_level import extract_text as pdfminer_extract_text

from airweave.core.async_helpers import run_in_thread_pool
from airweave.core.exceptions import EntityProcessingError
from airweave.platform.converters._base import BaseTextConverter


class SimplePdfConverter(BaseTextConverter):
    """Extract text from PDFs using pdfminer.six (local, no API).

    Uses pdfminer.six for robust text extraction from PDF files.
    Falls back to PyPDF2 if pdfminer fails.
    """

    BATCH_SIZE = 10
    MAX_CONCURRENT = 20

    def __init__(self):
        """Initialize SimplePdfConverter."""
        super().__init__()
        self.logger.info("Initialized SimplePdfConverter (local extraction)")

    async def convert_batch(self, paths: List[Path]) -> Dict[Path, str]:
        """Extract text from multiple PDF files.

        Args:
            paths: List of PDF file paths

        Returns:
            Dict mapping path to extracted markdown text
        """
        self.logger.debug(f"Converting {len(paths)} PDFs with simple extraction")

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        tasks = [self._convert_single(path, semaphore) for path in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for path, result in zip(paths, results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to convert {path.name}: {result}")
                output[path] = None
            else:
                output[path] = result

        success_count = sum(1 for v in output.values() if v is not None)
        self.logger.info(
            f"Converted {success_count}/{len(paths)} PDFs successfully"
        )

        return output

    async def _convert_single(
        self, path: Path, semaphore: asyncio.Semaphore
    ) -> str:
        """Extract text from a single PDF file.

        Args:
            path: Path to PDF file
            semaphore: Concurrency control

        Returns:
            Extracted text as markdown
        """
        async with semaphore:
            try:
                # Use pdfminer.six for robust extraction
                text = await run_in_thread_pool(
                    pdfminer_extract_text, str(path)
                )

                if not text or not text.strip():
                    self.logger.warning(
                        f"No text extracted from {path.name} with pdfminer, "
                        "trying PyPDF2 fallback"
                    )
                    text = await self._extract_with_pypdf2(path)

                # Clean up text
                text = text.strip()

                if not text:
                    self.logger.warning(f"No text content in {path.name}")
                    return ""

                # Wrap in markdown code fence for consistency
                return f"```\n{text}\n```"

            except Exception as e:
                self.logger.error(
                    f"Error extracting text from {path.name}: {e}",
                    exc_info=True
                )
                raise EntityProcessingError(
                    f"Failed to extract text from PDF: {e}"
                )

    async def _extract_with_pypdf2(self, path: Path) -> str:
        """Fallback extraction using PyPDF2.

        Args:
            path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            from PyPDF2 import PdfReader

            def extract():
                reader = PdfReader(str(path))
                text_parts = []
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                return "\n\n".join(text_parts)

            return await run_in_thread_pool(extract)

        except Exception as e:
            self.logger.error(f"PyPDF2 fallback failed for {path.name}: {e}")
            return ""
