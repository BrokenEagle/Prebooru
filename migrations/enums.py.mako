# APP/LOGICAL/ENUMS/${enums_type.upper()}.PY

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum

# ## LOCAL IMPORTS
from .. import sites


# ## CLASSES

# #### Rendered enums
% for name in model_enums:

class ${name}(AttrEnum):
    % for k, v in model_enums[name].items():
    ${k.replace('-', '_')} = ${v}
    % endfor

% endfor