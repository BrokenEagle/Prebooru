# APP/LOGICAL/ENUMS/${enums_type.upper()}.PY

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum

# ## LOCAL IMPORTS
from .. import sites


# ## CLASSES

# #### Rendered enums
% for name in model_enums:

% if name != 'SiteDescriptorEnum':
class ${name}(AttrEnum):
    % for k, v in model_enums[name].items():
    ${k.replace('-', '_')} = ${v}
    % endfor
% else:
class ${name}(AttrEnum):
    % for k, v in model_enums[name].items():
    ${k.replace('-', '_')} = ${v}
    % endfor

    # ## Instance properties

    source = sites.source
    domain = sites.domain

    # ## Class properties

    get_site_from_domain = sites.get_site_from_domain
    get_site_from_url = sites.get_site_from_url
    get_site_from_id = sites.get_site_from_id
% endif

% endfor