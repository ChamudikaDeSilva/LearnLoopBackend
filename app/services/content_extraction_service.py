import re

from pathlib import Path

import pymupdf

from app.models.material import (
    Material,
)

from app.services.storage_service import (
    StorageService,
    StoredFileNotFoundError,
)


# ============================================================
# Exceptions
# ============================================================


class ContentExtractionError(
    Exception
):
    pass


class EmptyMaterialContentError(
    ContentExtractionError
):
    pass


class UnsupportedContentTypeError(
    ContentExtractionError
):
    pass


class ContentFileNotFoundError(
    ContentExtractionError
):
    pass


# ============================================================
# Result
# ============================================================


class ExtractedContent:

    def __init__(
        self,
        text: str,
    ):
        self.text = text

        self.character_count = len(
            text
        )


# ============================================================
# Service
# ============================================================


class ContentExtractionService:

    def __init__(
        self,
    ):
        self.storage_service = (
            StorageService()
        )


    # ========================================================
    # PUBLIC ENTRY POINT
    # ========================================================

    def extract(
        self,
        material: Material,
    ) -> ExtractedContent:

        source_type = (
            material.source_type
        )


        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        if (
            source_type ==
            "text"
        ):

            return (
                self._extract_text_material(
                    material
                )
            )


        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        if (
            source_type ==
            "pdf"
        ):

            return (
                self._extract_pdf_material(
                    material
                )
            )


        # ----------------------------------------------------
        # IMAGE / CAMERA
        #
        # These will be connected to the multimodal
        # AI provider in Day 3B.
        # ----------------------------------------------------

        if (
            source_type
            in (
                "image",
                "camera",
            )
        ):

            raise (
                UnsupportedContentTypeError(
                    "Image and camera extraction "
                    "will be handled by the "
                    "multimodal AI provider."
                )
            )


        raise (
            UnsupportedContentTypeError(
                f"Unsupported material type: "
                f"{source_type}"
            )
        )


    # ========================================================
    # TEXT MATERIAL
    # ========================================================

    def _extract_text_material(
        self,
        material: Material,
    ) -> ExtractedContent:

        content = (
            material.content
            or ""
        )


        cleaned_text = (
            self._normalize_text(
                content
            )
        )


        if (
            not cleaned_text
        ):

            raise (
                EmptyMaterialContentError(
                    "The text material "
                    "does not contain content."
                )
            )


        return ExtractedContent(
            cleaned_text
        )


    # ========================================================
    # PDF MATERIAL
    # ========================================================

    def _extract_pdf_material(
        self,
        material: Material,
    ) -> ExtractedContent:

        if (
            not material.file_path
        ):

            raise (
                ContentFileNotFoundError(
                    "The material does not "
                    "have a stored file path."
                )
            )


        file_path = (
            self._resolve_file_path(
                material.file_path
            )
        )


        extracted_pages: list[str] = []


        try:

            with pymupdf.open(
                file_path
            ) as document:

                for page in document:

                    page_text = (
                        page.get_text(
                            "text",
                            sort=True,
                        )
                    )


                    page_text = (
                        self._normalize_text(
                            page_text
                        )
                    )


                    if (
                        page_text
                    ):

                        extracted_pages.append(
                            page_text
                        )


        except Exception as exc:

            raise (
                ContentExtractionError(
                    "Unable to extract "
                    "text from PDF."
                )
            ) from exc


        combined_text = (
            "\n\n".join(
                extracted_pages
            )
        )


        combined_text = (
            self._normalize_text(
                combined_text
            )
        )


        if (
            not combined_text
        ):

            raise (
                EmptyMaterialContentError(
                    "No readable text was "
                    "found in this PDF. "
                    "The PDF may contain "
                    "scanned images only."
                )
            )


        return ExtractedContent(
            combined_text
        )


    # ========================================================
    # FILE PATH
    # ========================================================

    def _resolve_file_path(
        self,
        relative_path: str,
    ) -> Path:

        try:

            return (
                self.storage_service
                .get_file_path(
                    relative_path
                )
            )


        except StoredFileNotFoundError as exc:

            raise (
                ContentFileNotFoundError(
                    "The stored material "
                    "file could not be found."
                )
            ) from exc


    # ========================================================
    # NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        if (
            not text
        ):

            return ""


        # Normalize line endings.

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )


        # Collapse repeated spaces and tabs,
        # while preserving line structure.

        lines = []


        for line in text.split(
            "\n"
        ):

            cleaned_line = re.sub(
                r"[ \t]+",
                " ",
                line,
            ).strip()


            lines.append(
                cleaned_line
            )


        text = "\n".join(
            lines
        )


        # More than two consecutive blank lines
        # are unnecessary for AI processing.

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )


        return text.strip()