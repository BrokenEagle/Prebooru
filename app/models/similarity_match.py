# APP/MODELS/SIMILARITY_MATCH.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, integer_column, real_column


# ## CLASSES

class SimilarityMatch(JsonModel):
    # ## Columns
    forward_id = integer_column(foreign_key='post.id', primary_key=True)
    reverse_id = integer_column(foreign_key='post.id', primary_key=True, index=True)
    score = real_column(nullable=False)

    # ## Relationships
    # forward_post <- Post (OtO)
    # reverse_post <- Post (OtO)

    # ## Instance properties

    @property
    def id(self):
        return f"{self.forward_id}-{self.reverse_id}"

    @property
    def shortlink(self):
        return f"similarity match #{self.id}"

    # ## Class methods

    @classmethod
    def find(cls, forward_id, reverse_id):
        return cls.query.filter_by(forward_id=forward_id, reverse_id=reverse_id).one_or_none()

    # ## Private

    __table_args__ = (
        DB.CheckConstraint(
            "forward_id < reverse_id",
            name="id_order"),
        {'sqlite_with_rowid': False},
    )
