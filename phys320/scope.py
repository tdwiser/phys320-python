from time import sleep
import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
import pandas as pd
import pyvisa
import pyvisa.constants
import pyvisa.events

import enum

# for type hinting:
from typing import Any, Optional, Literal, Iterable, Self, cast
from matplotlib.figure import Figure as mplFigure
from matplotlib.axes import Axes as mplAxes

class MeasurementType(enum.StrEnum):
    CYCLE_RMS = "CRMs"
    CURSOR_RMS = "CURSORRms"
    FALL_TIME = "FALL"
    FREQUENCY = "FREQuency"
    MAXIMUM = "MAXImum"
    MEAN = "MEAN"
    MINIMUM = "MINImum"
    NONE = "NONe"
    NEG_PULSE_WIDTH = "NWIdth"
    PULSE_DUTY = "PDUty"
    PERIOD = "PERIod"
    PHASE = "PHAse"
    PEAK_TO_PEAK = "PK2pk"
    POS_PULSE_WIDTH = "PWIdth"
    RISE_TIME = "RISe"
    DELAY_RR = "DELAYRR"
    DELAY_RF = "DELAYRF"
    DELAY_FR = "DELAYFR"
    DELAY_FF = "DELAYFF"
    AMPLITUDE = "AMplitude"
    CYCLE_MEAN = "CMEAN"
    HIGH_REF = "HIGH"
    LOW_REF = "LOW"
    NEG_DUTY = "NDUty"
    POS_OVERSHOOT = "POVERshoot"
    NEG_OVERSHOOT = "NOVERshoot"
    CURSOR_MEAN = "CURSORMean"
    BURST_WIDTH = "BURSTWIDth"
    AREA = "AREA"
    CYCLE_AREA = "CAREA"
    POS_PULSE_COUNT = "PPULSECount"
    NEG_PULSE_COUNT = "NPULSECount"
    RISING_EDGE_COUNT = "REDGECount"
    FALLING_EDGE_COUNT = "FEDGECount"
MT = MeasurementType

class Channel(enum.StrEnum):
    CH1 = "CH1"
    CH2 = "CH2"
    MATH = "MATH"
CH1 = Channel.CH1
CH2 = Channel.CH2
MATH = Channel.MATH
ChannelLike = Channel | Literal[1,2,'1','2','ch1','ch2','CH1','CH2','math','MATH'] # convertible to Channel

class Measurement:
    _last: Optional[Self] = None

    def __init__(self, type: MeasurementType, source: ChannelLike, source2: Optional[ChannelLike] = None):
        self.type = type
        self.source = ch(source)
        self.source2 = ch(source2) if source2 else None
    
    def __repr__(self) -> str:
        return f"{self.type.name} ({self.type.value}) on {self.source}" \
                + (f", {self.source2}" if self.source2 else "")
    
    def __str__(self) -> str:
        return f"{self.type.name}_{self.source}" + (f"_{self.source2}" if self.source2 else "")

    def value(self, *, force_setup = False) -> float:
        global _inst
        cls = type(self)
        if force_setup:
            cls._last = None
        if _inst is None: raise ScopeError.uninitialized()
        if event_pending():
            _inst.write("*CLS")
        if (not cls._last) or (cls._last.type != self.type):
            _inst.write(f"MEASU:IMM:TYP {self.type}")
        if (not cls._last) or (cls._last.source != self.source):
            _inst.write(f"MEASU:IMM:SOU {self.source}")
        if (not cls._last) or (cls._last.source2 != self.source2):
            if self.source2:
                _inst.write(f"MEASU:IMM:SOURCE2 {self.source2}")
        cls._last = self
        if event_pending():
            cls._last = None
            raise ScopeError.bad_setup(self)
        return float(query("MEASU:IMM:VAL?"))


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
        return
    _initialization_commands()

def _initialization_commands():
    global _inst #, _wrapped_handler
    if _inst is None: return
    _inst.write("DESE 255") # enable all device-level events
    _inst.write("*ESE 255") # enable triggering on all events

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

def query(message: str, delay: Optional[float] = None, warn_on_events: bool = True) -> str:
    """Pass through a VISA query to the scope. A combination of write(message) and read().

    By default, raise a ScopeWarning if events are generated by the query.

        Parameters
        ----------
        message : str
            The message to send.
        delay : Optional[float], optional
            Delay in seconds between write and read operations. If None,
            defaults to self.query_delay.
        warn_on_events: bool = True
            Whether to raise a ScopeWarning if events are generated by this query.

        Returns
        -------
        str
            Answer from the device.

        """
    global _inst
    if _inst is None: raise ScopeError.uninitialized()
    if warn_on_events and event_pending():
        _inst.write("*CLS")
    result = _inst.query(message, delay)
    if warn_on_events and event_pending():
        raise ScopeWarning("Event generated by last query, access with scope.event_queue()")
    return result

def event_pending() -> bool:
    global _inst
    if _inst is None: raise ScopeError.uninitialized()
    return bool(_inst.stb & (1 << 5)) # check for bit 5 (ESB) of STatus Byte register

def event_queue() -> str:
    global _inst
    if _inst is None: raise ScopeError.uninitialized()
    query("*ESR?", warn_on_events = False)
    return query("ALLEV?", warn_on_events = False)

def curve(channelA: ChannelLike, channelB: Optional[ChannelLike] = None) -> pd.DataFrame:
    global _inst
    if _inst is None: raise ScopeError.uninitialized()
    if channelB:
        channels = [ch(channelA), ch(channelB)]
    else:
        channels = [ch(channelA)]
    y = []
    for channel in channels:
        _inst.write(f"DATa:SOUrce {channel}")
        header = WFMP(_inst.query("WFMP?"))    
        curv = _inst.query_binary_values("CURV?",'b')
        y.append(header.y_scale(curv))
    t = header.t_series()
    data = {"t": t, ch(channelA): y[0]}
    if(channelB): data[ch(channelB)] = y[1]
    df = pd.DataFrame(data)
    return df

def peek(channel: ChannelLike = Channel.CH1, ax: Optional[mplAxes] = None) -> (mplFigure | None):
    """Helper function to get a quick plot of a channel e.g.~scope.peek(2) to see CH2.
    
    Parameters
    ----------
    channel: ChannelLike = CH1
        Which channel to peek. 1, 2, "MATH", etc. are allowed.
    ax: Optional[Axes] = None
        Plot the channel data on pre-existing matplotlib axes, if you want.
        If None, a new figure and axes will be created.

    Returns
    -------
    Figure | None
        If a new figure is created (`ax` is None) then it is returned.
    """
    global _inst
    if _inst is None: raise ScopeError.uninitialized()
    channel = ch(channel)
    _inst.write(f"DATa:SOUrce {channel}")
    header = WFMP(_inst.query("WFMP?"))
    curv = _inst.query_binary_values("CURV?",'b')
    t = header.t_series()
    y = header.y_scale(curv)
    if not ax:
        fig, ax = plt.subplots(); ax = cast(mplAxes, ax)
    else:
        fig = None
    ax.plot(t,y)
    ax.set_ybound(*header.y_range())
    ax.set_title(header.wfid)
    ax.set_xlabel(header.x_unit)
    ax.set_ylabel(header.y_unit)
    return fig

def repeat_measurements(measurements: Iterable[Measurement], append_to: Optional[list] = None, delay_seconds: Optional[float] = None):
    results = append_to or []
    try:
        while True:
            if delay_seconds is None:
                s = input("Enter to take data point, q to quit")
                if(s == 'q'):
                    break
            else:
                sleep(delay_seconds)
            try:
                results.append([m.value() for m in measurements])
            except ScopeWarning as e:
                print(e)
            except ScopeError as e:
                print(e)
                input("any key to continue")
    except KeyboardInterrupt:
        pass
    finally:
        return results


def measure(type: MeasurementType, source: Channel = Channel.CH1, source2: Optional[Channel] = None) -> float:
    global _inst
    
    if _inst is None: raise ScopeError.uninitialized()
    _inst.write(f"MEASU:IMM:TYP {type}")
    _inst.write(f"MEASU:IMM:SOU {source}")
    if source2: _inst.write(f"MEASU:IMM:SOURCE2 {source2}")
    return float(query("MEASU:IMM:VAL?"))

class WFMP: # WaveForM Preamble interpreter utility class
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
            self.wfid = data[6].strip(" \n\'\"")
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
        match self.binary_fmt:
            case "RI": # raw signed integer
                bmax = 1 << (self.bit_num - 1)
                ymax = float(self.y_scale(bmax))
                ymin = float(self.y_scale(-bmax))
            case "RP": # raw unsigned integer
                bmax = 1 << self.bit_num
                ymax = float(self.y_scale(bmax))
                ymin = float(self.y_scale(0))
            case _:
                raise ScopeError(f"unknown binary format '{self.binary_fmt}' in preamble")
        return (ymin, ymax)

def ch(num: ChannelLike) -> Channel:
    """
        Return the proper channel specification for sending to the scope in commands.
        Converts literal 1 or '1' to 'CH1', etc.

        Parameters
        ----------
        num: ChannelLike
            Channel number to normalize.

        Returns
        -------
        Channel
            The normalized channel string.
    """
    match num:
        case num if num in Channel:
            num = cast(Channel, num)
            return num
        case 1 | '1' | 'ch1':
            return Channel.CH1
        case 2 | '2' | 'ch2':
            return Channel.CH2
        case num if str(num).upper() == "MATH":
            return Channel.MATH
    raise ScopeError.bad_channel(num)

class ScopeError(Exception):
    """
    """
    @classmethod
    def uninitialized(cls) -> Self:
        return cls("No instrument initialized; try scope.init()")
    
    @classmethod
    def bad_channel(cls, bad: ChannelLike) -> Self:
        return cls(f"Invalid channel {bad}. Valid channels are [{" ".join(list(Channel))}]")

    @classmethod
    def bad_setup(cls, bad: Measurement) -> Self:
        return cls(f"Failed to setup measurement {bad}")

class ScopeWarning(Warning):
    """
    """