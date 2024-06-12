import numpy as np
import pyvisa
from typing import Optional

_rm: Optional[pyvisa.ResourceManager] = None
_inst: Optional[pyvisa.Resource] = None

def init():
    global _rm, _inst
    if _inst is not None: print("Already initialized; try reinit()"); return
    
    _rm = pyvisa.ResourceManager("@py")
    for r in _rm.list_resources():
        try:
            _inst = _rm.open_resource(r)
        except:
            continue
        break
    print(_inst)

def deinit():
    global _rm, _inst

    if _inst is not None:
        _inst.close()
        _inst = None
    if _rm is not None:
        _rm.close()
        _rm = None

def reinit():
    deinit()
    init()

