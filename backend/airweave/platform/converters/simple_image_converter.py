"""Simple image handling - extracts metadata only (no OCR)."""

import asyncio
from pathlib import Path
from typing import Dict, List

from PIL import Image

from airweave.core.exceptions import EntityProcessingError
from airweave.platform.sync.async_helpers import run_in_thread_pool
from airweave.platform.converters._base import BaseTextConverter


class SimpleImageConverter(BaseTextConverter):
    """Extract metadata from images using Pillow (no OCR, no API).

    Note: Does not perform OCR. Only extracts image metadata.
    For OCR, use Mistral or external OCR service.
    """

    BATCH_SIZE = 20
    MAX_CONCURRENT = 30

    def __init__(self):
        """Initialize SimpleImageConverter."""
        super().__init__()
        self.logger.info(
            "Initialized SimpleImageConverter (metadata only, no OCR)"
        )

    async def convert_batch(self, paths: List[Path]) -> Dict[Path, str]:
        """Extract metadata from multiple images.

        Args:
            paths: List of image file paths

        Returns:
            Dict mapping path to metadata text
        """
        self.logger.debug(f"Processing {len(paths)} images")

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        tasks = [self._convert_single(path, semaphore) for path in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for path, result in zip(paths, results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to process {path.name}: {result}")
                output[path] = None
            else:
                output[path] = result

        success_count = sum(1 for v in output.values() if v is not None)
        self.logger.info(
            f"Processed {success_count}/{len(paths)} images successfully"
        )

        return output

    async def _convert_single(
        self, path: Path, semaphore: asyncio.Semaphore
    ) -> str:
        """Extract metadata from a single image.

        Args:
            path: Path to image file
            semaphore: Concurrency control

        Returns:
            Image metadata as text
        """
        async with semaphore:
            try:
                def extract_metadata():
                    with Image.open(str(path)) as img:
                        metadata = [
                            f"**Image:** {path.name}",
                            f"**Format:** {img.format}",
                            f"**Size:** {img.size[0]}x{img.size[1]} pixels",
                            f"**Mode:** {img.mode}",
                        ]

                        # Extract EXIF data if available
                        exif = img.getexif()
                        if exif:
                            metadata.append("\n**EXIF Data:**")
                            for tag_id, value in exif.items():
                                try:
                                    from PIL.ExifTags import TAGS
                                    tag_name = TAGS.get(tag_id, tag_id)
                                    metadata.append(f"- {tag_name}: {value}")
                                except:
                                    pass

                        return "\n".join(metadata)

                text = await run_in_thread_pool(extract_metadata)
                return text

            except Exception as e:
                self.logger.error(
                    f"Error extracting metadata from {path.name}: {e}",
                    exc_info=True
                )
                raise EntityProcessingError(
                    f"Failed to extract image metadata: {e}"
                )
