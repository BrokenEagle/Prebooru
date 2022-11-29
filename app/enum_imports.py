# ## PACKAGE IMPORTS
from config import USE_ENUMS

# ## COLLATION IMPORTS

if USE_ENUMS:
    from .logical.enums import SiteDescriptorEnum as site_descriptor
    from .logical.enums import ApiDataTypeEnum as api_data_type
    from .logical.enums import ArchiveTypeEnum as archive_type
    from .logical.enums import PostTypeEnum as post_type
    from .logical.enums import SubscriptionStatusEnum as subscription_status
    from .logical.enums import SubscriptionElementStatusEnum as subscription_element_status
    from .logical.enums import SubscriptionElementKeepEnum as subscription_element_keep
    from .logical.enums import UploadStatusEnum as upload_status
    from .logical.enums import UploadElementStatusEnum as upload_element_status
    from .logical.enums import PoolElementTypeEnum as pool_element_type
    from .logical.enums import SiteDataTypeEnum as site_data_type
    from .logical.enums import TagTypeEnum as tag_type
else:
    from .models.model_enums import ApiDataType as api_data_type
    from .models.model_enums import ArchiveType as archive_type
    from .models.model_enums import PostType as post_type
    from .models.model_enums import SubscriptionStatus as subscription_status
    from .models.model_enums import SubscriptionElementStatus as subscription_element_status
    from .models.model_enums import SubscriptionElementKeep as subscription_element_keep
    from .models.model_enums import UploadStatus as upload_status
    from .models.model_enums import UploadElementStatus as upload_element_status
    from .models.model_enums import PoolElementType as pool_element_type
    from .models.model_enums import SiteDataType as site_data_type
    from .models.model_enums import TagType as tag_type
    from .models.model_enums import SiteDescriptor as site_descriptor

NONCE = None
