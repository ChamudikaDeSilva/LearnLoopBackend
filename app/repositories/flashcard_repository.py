from sqlalchemy.orm import (
    Session,
)

from app.models.flashcard import (
    Flashcard,
)

from app.models.flashcard_set import (
    FlashcardSet,
)

from app.schemas.flashcard import (
    FlashcardContent,
)


class FlashcardRepository:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        db: Session,
    ):

        self.db = db


    # ========================================================
    # GET SET BY MATERIAL
    # ========================================================

    def get_set_by_material_id(
        self,
        material_id: int,
    ) -> FlashcardSet | None:

        return (
            self.db
            .query(
                FlashcardSet
            )
            .filter(
                FlashcardSet.material_id
                ==
                material_id
            )
            .first()
        )


    # ========================================================
    # GET CARDS
    # ========================================================

    def get_cards_by_set_id(
        self,
        flashcard_set_id: int,
    ) -> list[Flashcard]:

        return (
            self.db
            .query(
                Flashcard
            )
            .filter(
                Flashcard.flashcard_set_id
                ==
                flashcard_set_id
            )
            .order_by(
                Flashcard.position.asc()
            )
            .all()
        )


    # ========================================================
    # GET COMPLETE MATERIAL DECK
    # ========================================================

    def get_by_material_id(
        self,
        material_id: int,
    ) -> tuple[
        FlashcardSet,
        list[Flashcard],
    ] | None:

        flashcard_set = (
            self.get_set_by_material_id(
                material_id
            )
        )


        if flashcard_set is None:

            return None


        cards = (
            self.get_cards_by_set_id(
                flashcard_set.id
            )
        )


        return (
            flashcard_set,
            cards,
        )


    # ========================================================
    # REPLACE / UPSERT FLASHCARD DECK
    #
    # Entire operation is transactional.
    #
    # If something fails:
    # rollback restores previous cards.
    # ========================================================

    def replace(
        self,
        *,
        material_id: int,
        provider: str,
        cards: list[
            FlashcardContent
        ],
    ) -> tuple[
        FlashcardSet,
        list[Flashcard],
    ]:

        try:

            flashcard_set = (
                self.get_set_by_material_id(
                    material_id
                )
            )


            # =================================================
            # CREATE SET FIRST TIME
            # =================================================

            if flashcard_set is None:

                flashcard_set = (
                    FlashcardSet(
                        material_id=
                            material_id,

                        provider=
                            provider,
                    )
                )


                self.db.add(
                    flashcard_set
                )


                # We need the generated ID
                # before inserting child cards.
                self.db.flush()


            # =================================================
            # EXISTING SET
            # =================================================

            else:

                flashcard_set.provider = (
                    provider
                )


                # Remove previous generated cards.
                (
                    self.db
                    .query(
                        Flashcard
                    )
                    .filter(
                        Flashcard.flashcard_set_id
                        ==
                        flashcard_set.id
                    )
                    .delete(
                        synchronize_session=False
                    )
                )


                self.db.flush()


            # =================================================
            # INSERT NEW CARDS
            # =================================================

            for (
                index,
                card,
            ) in enumerate(
                cards,
                start=1,
            ):

                new_card = (
                    Flashcard(
                        flashcard_set_id=
                            flashcard_set.id,

                        position=
                            index,

                        front=
                            card.front.strip(),

                        back=
                            card.back.strip(),
                    )
                )


                self.db.add(
                    new_card
                )


            # =================================================
            # COMMIT WHOLE DECK
            # =================================================

            self.db.commit()


            self.db.refresh(
                flashcard_set
            )


            saved_cards = (
                self.get_cards_by_set_id(
                    flashcard_set.id
                )
            )


            return (
                flashcard_set,
                saved_cards,
            )


        except Exception:

            self.db.rollback()

            raise