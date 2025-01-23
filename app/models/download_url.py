# APP/MODELS/DOWNLOAD_URL.PY

# ## LOCAL IMPORTS
from .base import JsonModel, integer_column, text_column


# ## CLASSES

class DownloadUrl(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    url = text_column(nullable=False)
    download_id = integer_column(foreign_key='download.id', nullable=False, index=True)

    # ## Relations
    # (MtO) download [Download]
