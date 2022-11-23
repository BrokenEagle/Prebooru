# APP/${enums_type.upper()}_ENUMS.PY

# ## LOCAL IMPORTS
from utility.obj import AttrEnum


# ## CLASSES

# #### Rendered enums
% for name in model_enums:

class ${name}(AttrEnum):
    % for k, v in model_enums[name].items():
    ${k.replace('-', '_')} = ${v}
    % endfor

% endfor