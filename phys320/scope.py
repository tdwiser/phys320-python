import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
import pyvisa
from typing import Literal, Optional, cast

CH_TYPE = Literal[1] | Literal[2]

_rm: Optional[pyvisa.ResourceManager] = None
_inst: Optional[pyvisa.resources.MessageBasedResource] = None

def init():
    """
        Initialize the VISA library and connect to a compatible scope, if found.
    """
    global _rm, _inst
    if _inst is not None: print("Already initialized; try reinit()"); return
    if _rm is not None: _rm.close()

    _rm = pyvisa.ResourceManager()
    for r in _rm.list_resources():
        try:
            tmp = _rm.open_resource(r)
            print(tmp)
            if not isinstance(tmp, pyvisa.resources.MessageBasedResource):
                print('Not a MessageBasedResource, skipping')
                continue
            _inst = cast(pyvisa.resources.MessageBasedResource, _rm.open_resource(r))
            print(_inst)
            idn = _inst.query("*IDN?")
            print(idn)
            if idn.startswith("TEKTRONIX,TBS 1052B-EDU"):
                print(f"Found compatible scope <{idn.strip()}> at <{_inst}>")
            else:
                _inst.close()
                _inst = None
                continue
        except Exception as e:
            print(f"({type(e)}) {e}")
            _inst = None
            continue
        break
    if _inst is None:
        print("No compatible scopes found.")

def deinit():
    """
        Deinitialize the scope and VISA library.
    """
    global _rm, _inst

    if _inst is not None:
        _inst.close()
        _inst = None
    if _rm is not None:
        _rm.close()
        _rm = None

def reinit():
    """
        Reinitialize. (Same as deinit() then init().)
    """
    deinit()
    init()

def query(*args, **kwargs):
    """Pass through a VISA query to the scope. A combination of write(message) and read()

        Parameters
        ----------
        message : str
            The message to send.
        delay : Optional[float], optional
            Delay in seconds between write and read operations. If None,
            defaults to self.query_delay.

        Returns
        -------
        str
            Answer from the device.

        """
    global _inst
    if _inst is None: raise ScopeError("No instrument initialized; try scope.init()")
    return _inst.query(*args, **kwargs)

def peek(channel: CH_TYPE = 1) -> plt.Figure:
    global _inst
    if _inst is None: raise ScopeError("No instrument initialized; try scope.init()")
    _inst.write(f"DATa:SOUrce CH{channel}")
    header = WFMP(_inst.query("WFMP?"))
    curv = _inst.query_binary_values("CURV?",'b')
    t = header.t_series()
    y = header.y_scale(curv)
    fig, ax = plt.subplots(); ax = cast(plt.Axes, ax)
    ax.plot(t,y)
    ax.set_ybound(*header.y_range())
    ax.set_title(header.wfid)
    ax.set_xlabel(header.x_unit)
    ax.set_ylabel(header.y_unit)
    return fig
    

class WFMP:
    def __init__(self, header: str):
        self.header_string = header
        data = header.split(';')
        if len(data) != 16:
            raise ScopeError("Got a non-conforming WFMP: {header}")
        try:
            self.byte_num = int(data[0])
            self.bit_num = int(data[1])
            self.encoding = data[2] # BIN or ASC
            self.binary_fmt = data[3] # RI or RP
            self.byte_order = data[4] # LSB- or MSB-first
            self.num_pts = int(data[5])
            self.wfid = data[6]
            self.pt_fmt = data[7] # ENV or Y
            self.x_incr = float(data[8])
            self.pt_offset = float(data[9])
            self.x_zero = float(data[10])
            self.x_unit = data[11].strip(" \n\'\"")
            self.y_mult = float(data[12])
            self.y_zero = float(data[13])
            self.y_offset = float(data[14])
            self.y_unit = data[15].strip(" \n\'\"")
        except Exception as e:
            raise ScopeError(e)

    def __repr__(self):
        return self.header_string
    
    def t_series(self) -> np.ndarray:
        return (np.arange(0, self.num_pts, dtype=float) - self.pt_offset)*self.x_incr + self.x_zero
    
    def y_scale(self, data: npt.ArrayLike) -> np.ndarray:
        y_raw = np.asarray(data)
        return (y_raw - self.y_offset)*self.y_mult + self.y_zero
    
    def y_range(self) -> tuple[float, float]:
        return (float(self.y_scale(-(1<<(self.bit_num-1)))), float(self.y_scale(1<<(self.bit_num-1))))

class ScopeError(Exception):
    """
    """
