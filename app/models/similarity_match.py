# APP/MODELS/SIMILARITY_MATCH.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class SimilarityMatch(JsonModel):
    # ## Public

    # #### Columns
    forward_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False, primary_key=True)
    reverse_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False, primary_key=True)
    score = DB.Column(DB.Float, nullable=False)

    # #### Relationships
    # post <- Post (MtO)

    # #### Instance properties

    @property
    def id(self):
        return f"{self.forward_id}-{self.reverse_id}"

    @property
    def shortlink(self):
        return f"similarity match #{self.id}"

    # #### Class methods

    @classmethod
    def find(cls, forward_id, reverse_id):
        return cls.query.filter_by(forward_id=forward_id, reverse_id=reverse_id).first()

    # ## Private

    # #### Class variables

    __table_args__ = {
        'sqlite_with_rowid': False,
    }