from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.material import Material


class MaterialRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    # =====================================================
    # GET ALL
    # =====================================================

    def get_all_by_subject_and_user(
        self,
        subject_id: int,
        user_id: int,
    ) -> list[Material]:

        statement = (
            select(Material)
            .where(
                Material.subject_id == subject_id,
                Material.user_id == user_id,
            )
            .order_by(
                Material.created_at.desc()
            )
        )

        return list(
            self.db
            .scalars(statement)
            .all()
        )


    # =====================================================
    # GET ONE
    # =====================================================

    def get_by_id_and_user(
        self,
        material_id: int,
        user_id: int,
    ) -> Material | None:

        statement = (
            select(Material)
            .where(
                Material.id == material_id,
                Material.user_id == user_id,
            )
        )

        return (
            self.db
            .scalars(statement)
            .first()
        )


    # =====================================================
    # CREATE TEXT
    # =====================================================

    def create_text(
        self,
        user_id: int,
        subject_id: int,
        title: str,
        content: str,
    ) -> Material:

        material = Material(
            user_id=user_id,
            subject_id=subject_id,
            title=title,
            source_type="text",
            content=content,
        )

        self.db.add(
            material
        )

        self.db.commit()

        self.db.refresh(
            material
        )

        return material


    # =====================================================
    # CREATE PDF
    # =====================================================

    def create_pdf(
        self,
        user_id: int,
        subject_id: int,
        title: str,
        file_name: str,
        file_path: str,
        file_size: int,
    ) -> Material:

        material = Material(
            user_id=user_id,
            subject_id=subject_id,
            title=title,
            source_type="pdf",
            content=None,
            file_name=file_name,
            file_path=file_path,
            mime_type="application/pdf",
            file_size=file_size,
        )

        self.db.add(
            material
        )

        self.db.commit()

        self.db.refresh(
            material
        )

        return material


    # =====================================================
    # CREATE IMAGE
    # =====================================================

    def create_image(
        self,
        user_id: int,
        subject_id: int,
        title: str,
        file_name: str,
        file_path: str,
        mime_type: str,
        file_size: int,
    ) -> Material:

        material = Material(
            user_id=user_id,
            subject_id=subject_id,
            title=title,
            source_type="image",
            content=None,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            file_size=file_size,
        )

        self.db.add(
            material
        )

        self.db.commit()

        self.db.refresh(
            material
        )

        return material


    # =====================================================
    # UPDATE TEXT
    # =====================================================

    def update_text(
        self,
        material: Material,
        title: str,
        content: str,
    ) -> Material:

        material.title = title
        material.content = content

        self.db.commit()

        self.db.refresh(
            material
        )

        return material


    # =====================================================
    # UPDATE IMAGE TITLE
    # =====================================================

    def update_title(
        self,
        material: Material,
        title: str,
    ) -> Material:

        material.title = title

        self.db.commit()

        self.db.refresh(
            material
        )

        return material


    # =====================================================
    # DELETE
    # =====================================================

    def delete(
        self,
        material: Material,
    ) -> None:

        self.db.delete(
            material
        )

        self.db.commit()