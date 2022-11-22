# APP/MODELS/ATTR_ENUMS.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

# #### Column enums

class SiteDescriptor(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class ApiDataType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class ArchiveType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class PostType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class SubscriptionStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class SubscriptionElementStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class SubscriptionElementKeep(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class UploadStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class UploadElementStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


# #### Polymorphic enums

class PoolElementType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class SiteDataType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)


class TagType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)
