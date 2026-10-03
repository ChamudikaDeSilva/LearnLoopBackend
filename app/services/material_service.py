from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.user import User

from app.repositories.material_repository import (
    MaterialRepository,
)

from app.repositories.subject_repository import (
    SubjectRepository,
)

from app.schemas.material import (
    ImageMaterialTitleUpdateRequest,
    TextMaterialCreateRequest,
    TextMaterialUpdateRequest,
)

from app.services.storage_service import (
    StorageService,
    StoredFileNotFoundError,
)


# =========================================================
# Exceptions
# =========================================================

class MaterialNotFoundError(Exception):
    pass


class SubjectNotFoundError(Exception):
    pass


class UnsupportedMaterialEditError(Exception):
    pass


class UnsupportedMaterialFileError(Exception):
    pass


class MaterialFileNotFoundError(Exception):
    pass


# =========================================================
# Material Service
# =========================================================

class MaterialService:

    def __init__(
        self,
        db: Session,
    ):

        self.material_repository = (
            MaterialRepository(
                db
            )
        )

        self.subject_repository = (
            SubjectRepository(
                db
            )
        )

        self.storage_service = (
            StorageService()
        )


    # =====================================================
    # SUBJECT OWNERSHIP
    # =====================================================

    def ensure_subject_exists(
        self,
        subject_id: int,
        current_user: User,
    ) -> None:

        subject = (
            self.subject_repository
            .get_by_id_and_user(
                subject_id,
                current_user.id,
            )
        )

        if subject is None:
            raise SubjectNotFoundError()


    # =====================================================
    # GET MATERIALS
    # =====================================================

    def get_materials(
        self,
        subject_id: int,
        current_user: User,
    ) -> list[Material]:

        self.ensure_subject_exists(
            subject_id,
            current_user,
        )

        return (
            self.material_repository
            .get_all_by_subject_and_user(
                subject_id,
                current_user.id,
            )
        )


    # =====================================================
    # GET ONE MATERIAL
    # =====================================================

    def get_material(
        self,
        material_id: int,
        current_user: User,
    ) -> Material:

        material = (
            self.material_repository
            .get_by_id_and_user(
                material_id,
                current_user.id,
            )
        )

        if material is None:
            raise MaterialNotFoundError()

        return material


    # =====================================================
    # GET MATERIAL FILE
    # =====================================================

    def get_material_file(
        self,
        material_id: int,
        current_user: User,
    ) -> tuple[
        Material,
        Path,
    ]:

        material = (
            self.get_material(
                material_id,
                current_user,
            )
        )

        if (
            material.source_type
            not in (
                "pdf",
                "image",
                "camera",
            )
        ):
            raise UnsupportedMaterialFileError()

        if not material.file_path:
            raise MaterialFileNotFoundError()

        try:

            file_path = (
                self.storage_service
                .get_file_path(
                    material.file_path
                )
            )

        except StoredFileNotFoundError:

            raise MaterialFileNotFoundError()

        return (
            material,
            file_path,
        )


    # =====================================================
    # CREATE TEXT
    # =====================================================

    def create_text_material(
        self,
        subject_id: int,
        request: TextMaterialCreateRequest,
        current_user: User,
    ) -> Material:

        self.ensure_subject_exists(
            subject_id,
            current_user,
        )

        title = (
            request.title
            .strip()
        )

        content = (
            request.content
            .strip()
        )

        return (
            self.material_repository
            .create_text(
                user_id=current_user.id,
                subject_id=subject_id,
                title=title,
                content=content,
            )
        )


    # =====================================================
    # CREATE PDF
    # =====================================================

    async def create_pdf_material(
        self,
        subject_id: int,
        title: str,
        file: UploadFile,
        current_user: User,
    ) -> Material:

        self.ensure_subject_exists(
            subject_id,
            current_user,
        )

        clean_title = (
            title.strip()
        )

        if not clean_title:
            raise ValueError(
                "Material title is required."
            )

        relative_path: str | None = None

        try:

            (
                relative_path,
                file_size,
                original_file_name,
            ) = (
                await self.storage_service
                .save_pdf(
                    file=file,
                    user_id=current_user.id,
                    subject_id=subject_id,
                )
            )

            material = (
                self.material_repository
                .create_pdf(
                    user_id=current_user.id,
                    subject_id=subject_id,
                    title=clean_title,
                    file_name=original_file_name,
                    file_path=relative_path,
                    file_size=file_size,
                )
            )

            return material

        except Exception:

            if relative_path:

                self.storage_service.delete_file(
                    relative_path
                )

            raise


    # =====================================================
    # CREATE IMAGE
    # =====================================================

    async def create_image_material(
        self,
        subject_id: int,
        title: str,
        file: UploadFile,
        current_user: User,
    ) -> Material:

        self.ensure_subject_exists(
            subject_id,
            current_user,
        )

        clean_title = (
            title.strip()
        )

        if not clean_title:
            raise ValueError(
                "Material title is required."
            )

        relative_path: str | None = None

        try:

            (
                relative_path,
                file_size,
                original_file_name,
                mime_type,
            ) = (
                await self.storage_service
                .save_image(
                    file=file,
                    user_id=current_user.id,
                    subject_id=subject_id,
                )
            )

            material = (
                self.material_repository
                .create_image(
                    user_id=current_user.id,
                    subject_id=subject_id,
                    title=clean_title,
                    file_name=original_file_name,
                    file_path=relative_path,
                    mime_type=mime_type,
                    file_size=file_size,
                )
            )

            return material

        except Exception:

            if relative_path:

                self.storage_service.delete_file(
                    relative_path
                )

            raise


    # =====================================================
    # UPDATE TEXT
    # =====================================================

    def update_text_material(
        self,
        material_id: int,
        request: TextMaterialUpdateRequest,
        current_user: User,
    ) -> Material:

        material = (
            self.get_material(
                material_id,
                current_user,
            )
        )

        if (
            material.source_type !=
            "text"
        ):
            raise UnsupportedMaterialEditError()

        title = (
            request.title
            .strip()
        )

        content = (
            request.content
            .strip()
        )

        return (
            self.material_repository
            .update_text(
                material=material,
                title=title,
                content=content,
            )
        )


    # =====================================================
    # UPDATE IMAGE TITLE
    # =====================================================

    def update_image_title(
        self,
        material_id: int,
        request: ImageMaterialTitleUpdateRequest,
        current_user: User,
    ) -> Material:

        material = (
            self.get_material(
                material_id,
                current_user,
            )
        )

        if (
            material.source_type !=
            "image"
        ):
            raise UnsupportedMaterialEditError()

        clean_title = (
            request.title
            .strip()
        )

        if not clean_title:
            raise ValueError(
                "Material title is required."
            )

        return (
            self.material_repository
            .update_title(
                material=material,
                title=clean_title,
            )
        )


    # =====================================================
    # DELETE
    # =====================================================

    def delete_material(
        self,
        material_id: int,
        current_user: User,
    ) -> None:

        material = (
            self.get_material(
                material_id,
                current_user,
            )
        )

        file_path = (
            material.file_path
        )

        self.material_repository.delete(
            material
        )

        if file_path:

            self.storage_service.delete_file(
                file_path
            )