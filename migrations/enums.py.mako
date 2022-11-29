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

    @property
    def source(self):
        from .logical.sources import SOURCEDICT
        return SOURCEDICT[self.name]

    @property
    def domain(self):
        from .logical.sites import SITES
        return SITES[self.name]
% endif

% endfor