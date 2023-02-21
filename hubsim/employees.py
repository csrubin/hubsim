"""
Contains all classes related to employees
Type of Worker, different permissions or possible tasks. Important as input to simulation

Todo: More
"""

import inspect
import random
from dataclasses import dataclass
from typing import Any, Callable, Generator, Iterable, overload

import lea
import plotly.express as px
import plotly.graph_objs as go
import simpy
from config import *

# TODO: Define resourcepool class? Defines resources with overlapping capabilities


class HubEmployee:
    pass


class RemotePilotInCommand(HubEmployee):
    pass


class SafetyPilot(HubEmployee):
    pass


class VisualObserver(HubEmployee):
    pass
