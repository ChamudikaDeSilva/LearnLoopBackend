from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


# =========================================================
# Storage Configuration
# =========================================================

UPLOAD_ROOT = Path("uploads")


MAX_PDF_SIZE = (
    20 * 1024 * 1024
)


MAX_IMAGE_SIZE = (
    10 * 1024 * 1024
)


CHUNK_SIZE = (
    1024 * 1024
)


# =========================================================
# Exceptions
# =========================================================

class InvalidPdfError(
    Exception
):
    pass


class InvalidImageError(
    Exception
):
    pass


class FileTooLargeError(
    Exception
):
    pass


class StoredFileNotFoundError(
    Exception
):
    pass


# =========================================================
# Storage Service
# =========================================================

class StorageService:

    # =====================================================
    # SAVE PDF
    # =====================================================

    async def save_pdf(
        self,
        file: UploadFile,
        user_id: int,
        subject_id: int,
    ) -> tuple[
        str,
        int,
        str,
    ]:

        original_file_name = (
            Path(
                file.filename
                or "document.pdf"
            ).name
        )


        target_path: (
            Path | None
        ) = None


        try:

            # =============================================
            # Extension
            # =============================================

            if not (
                original_file_name
                .lower()
                .endswith(".pdf")
            ):
                raise InvalidPdfError(
                    "Only PDF files are allowed."
                )


            # =============================================
            # Signature
            # =============================================

            header = await file.read(
                5
            )


            if header != b"%PDF-":
                raise InvalidPdfError(
                    "The uploaded file is not "
                    "a valid PDF document."
                )


            await file.seek(
                0
            )


            # =============================================
            # Folder
            # =============================================

            target_directory = (
                UPLOAD_ROOT
                / "users"
                / str(user_id)
                / "subjects"
                / str(subject_id)
            )


            target_directory.mkdir(
                parents=True,
                exist_ok=True,
            )


            # =============================================
            # Filename
            # =============================================

            stored_file_name = (
                f"{uuid4().hex}.pdf"
            )


            target_path = (
                target_directory
                / stored_file_name
            )


            file_size = 0


            # =============================================
            # Write
            # =============================================

            with target_path.open(
                "wb"
            ) as output_file:

                while True:

                    chunk = (
                        await file.read(
                            CHUNK_SIZE
                        )
                    )


                    if not chunk:
                        break


                    file_size += len(
                        chunk
                    )


                    if (
                        file_size
                        > MAX_PDF_SIZE
                    ):
                        raise FileTooLargeError(
                            "PDF files must not "
                            "exceed 20 MB."
                        )


                    output_file.write(
                        chunk
                    )


            relative_path = (
                target_path
                .relative_to(
                    UPLOAD_ROOT
                )
                .as_posix()
            )


            return (
                relative_path,
                file_size,
                original_file_name,
            )


        except Exception:

            if (
                target_path
                is not None
            ):
                target_path.unlink(
                    missing_ok=True
                )


            raise


        finally:

            await file.close()


    # =====================================================
    # SAVE IMAGE
    # =====================================================

    async def save_image(
        self,
        file: UploadFile,
        user_id: int,
        subject_id: int,
    ) -> tuple[
        str,
        int,
        str,
        str,
    ]:

        original_file_name = (
            Path(
                file.filename
                or "image.jpg"
            ).name
        )


        content_type = (
            file.content_type
            or ""
        ).lower()


        allowed_mime_types = {
            "image/jpeg":
                ".jpg",

            "image/jpg":
                ".jpg",

            "image/png":
                ".png",

            "image/webp":
                ".webp",
        }


        extension = (
            allowed_mime_types
            .get(
                content_type
            )
        )


        if not extension:
            raise InvalidImageError(
                "Only JPEG, PNG and WEBP "
                "images are allowed."
            )


        target_path: (
            Path | None
        ) = None


        try:

            # =============================================
            # Basic binary signature validation
            # =============================================

            header = await file.read(
                12
            )


            valid_image = False


            # JPEG
            if (
                header.startswith(
                    b"\xFF\xD8\xFF"
                )
            ):
                valid_image = True


            # PNG
            elif (
                header.startswith(
                    b"\x89PNG\r\n\x1a\n"
                )
            ):
                valid_image = True


            # WEBP
            elif (
                len(header) >= 12
                and
                header[0:4] == b"RIFF"
                and
                header[8:12] == b"WEBP"
            ):
                valid_image = True


            if not valid_image:
                raise InvalidImageError(
                    "The uploaded file is not "
                    "a valid image."
                )


            await file.seek(
                0
            )


            # =============================================
            # Folder
            # =============================================

            target_directory = (
                UPLOAD_ROOT
                / "users"
                / str(user_id)
                / "subjects"
                / str(subject_id)
            )


            target_directory.mkdir(
                parents=True,
                exist_ok=True,
            )


            # =============================================
            # Filename
            # =============================================

            stored_file_name = (
                f"{uuid4().hex}{extension}"
            )


            target_path = (
                target_directory
                / stored_file_name
            )


            file_size = 0


            # =============================================
            # Write
            # =============================================

            with target_path.open(
                "wb"
            ) as output_file:

                while True:

                    chunk = (
                        await file.read(
                            CHUNK_SIZE
                        )
                    )


                    if not chunk:
                        break


                    file_size += len(
                        chunk
                    )


                    if (
                        file_size
                        > MAX_IMAGE_SIZE
                    ):
                        raise FileTooLargeError(
                            "Image files must not "
                            "exceed 10 MB."
                        )


                    output_file.write(
                        chunk
                    )


            relative_path = (
                target_path
                .relative_to(
                    UPLOAD_ROOT
                )
                .as_posix()
            )


            return (
                relative_path,
                file_size,
                original_file_name,
                content_type,
            )


        except Exception:

            if (
                target_path
                is not None
            ):
                target_path.unlink(
                    missing_ok=True
                )


            raise


        finally:

            await file.close()


    # =====================================================
    # GET FILE PATH
    # =====================================================

    def get_file_path(
        self,
        relative_path: str,
    ) -> Path:

        if not relative_path:
            raise StoredFileNotFoundError(
                "Stored file path is missing."
            )


        upload_root = (
            UPLOAD_ROOT.resolve()
        )


        target_path = (
            UPLOAD_ROOT
            / relative_path
        ).resolve()


        try:

            target_path.relative_to(
                upload_root
            )


        except ValueError:

            raise StoredFileNotFoundError(
                "Invalid stored file path."
            )


        if (
            not target_path.exists()
            or
            not target_path.is_file()
        ):
            raise StoredFileNotFoundError(
                "Stored file was not found."
            )


        return target_path


    # =====================================================
    # DELETE FILE
    # =====================================================

    def delete_file(
        self,
        relative_path: str,
    ) -> None:

        if not relative_path:
            return


        upload_root = (
            UPLOAD_ROOT.resolve()
        )


        target_path = (
            UPLOAD_ROOT
            / relative_path
        ).resolve()


        try:

            target_path.relative_to(
                upload_root
            )


        except ValueError:

            return


        target_path.unlink(
            missing_ok=True
        )