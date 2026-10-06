from sqlalchemy.orm import (
    Session,
)

from app.models.material_summary import (
    MaterialSummary,
)


class MaterialSummaryRepository:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        db: Session,
    ):

        self.db = (
            db
        )


    # ========================================================
    # GET BY MATERIAL
    # ========================================================

    def get_by_material_id(
        self,
        material_id: int,
    ) -> MaterialSummary | None:

        return (
            self.db
            .query(
                MaterialSummary
            )
            .filter(
                MaterialSummary.material_id
                ==
                material_id
            )
            .first()
        )


    # ========================================================
    # UPSERT
    #
    # Creates the first summary.
    #
    # Generate Again updates the same row.
    # ========================================================

    def upsert(
        self,
        *,
        material_id: int,
        provider: str,
        source_type: str,
        extracted_character_count: int,
        summary: str,
        key_points: list[str],
        study_tips: list[str],
    ) -> MaterialSummary:

        existing = (
            self.get_by_material_id(
                material_id
            )
        )


        try:

            # =================================================
            # CREATE
            # =================================================

            if existing is None:

                existing = (
                    MaterialSummary(
                        material_id=
                            material_id,

                        provider=
                            provider,

                        source_type=
                            source_type,

                        extracted_character_count=
                            extracted_character_count,

                        summary=
                            summary,

                        key_points=
                            key_points,

                        study_tips=
                            study_tips,
                    )
                )


                self.db.add(
                    existing
                )


            # =================================================
            # UPDATE
            # =================================================

            else:

                existing.provider = (
                    provider
                )


                existing.source_type = (
                    source_type
                )


                existing.extracted_character_count = (
                    extracted_character_count
                )


                existing.summary = (
                    summary
                )


                existing.key_points = (
                    key_points
                )


                existing.study_tips = (
                    study_tips
                )


            # =================================================
            # SAVE
            # =================================================

            self.db.commit()


            self.db.refresh(
                existing
            )


            return existing


        except Exception:

            self.db.rollback()

            raise