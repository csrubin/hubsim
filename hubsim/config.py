"""
Configuration file used for defining default hub operations parameters and other
miscellaneous configuration details. Initially using .py file for simplicity, but may choose
a more appropriate configuration file format in the future (e.g., TOML, YAML, etc.)

TODO: Determine necessity of config file change and execute if needed
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

import lea


class Config:
    """Configuration object for passing different options to simulation environment"""

    def __init__(self):
        # TODO Idk what this should be -- maybe define lea.pmf based of histogram bins built from legit hub data?
        # self.pick_pack_timeout = lea.poisson(10)
        pass

    # Hub operations task duration intervals
    PICK_PACK_INTERVAL = (5, 25)  # i.e. pick-packing takes between 5 and 15 min
    FLIGHT_INTERVAL = (5, 10)
    PREP_DRONE_INTERVAL = (1, 5)
    CHARGE_BATTERIES_INTERVAL = (30, 60)
    DISCHARGE_BATTERIES_INTERVAL = CHARGE_BATTERIES_INTERVAL  # Only for testing
    BATTERY_QUEUE_INTERVAL = (5, 10)  # Time for batteries to be monitored and moved to appropriate queue
    ORDER_CREATION_INTERVAL = (10, 45)
    OPERATING_HOURS_DURATION = 12.0 * 60.0  # 8am - 8pm

    # Hub resource defaults
    NUM_PILOTS = 2
    NUM_DELIVERY_SPECIALISTS = 1
    NUM_DRONES = 3
    NUM_CHARGERS = 4  # Total of 4 batteries can charge at once
    NUM_BATTERIES = 10
    BATTERY_STORE_CAPACITY = 15  # Larger capacity than num batteries

    # Not used yet
    NUM_LIFTS = 1

    RANDOM = False


@dataclass
class OrderStatus(IntEnum):
    """
    Object to hold status of a particular order
    TODO: Align with HubOps? I'm sure they have statuses of some sort
    """

    CREATED = 0
    STARTED = 1
    PREP_QUEUE = 2
    PREP = 3  # Pickpacking, drone prep, resource requests
    FLIGHT_QUEUE = 4
    FLIGHT = 5
    COMPLETED = 6


@dataclass
class Order:
    """
    Dataclass to hold information about individual orders. Useful for monitoring data about orders as
    processes occur, and for analyzing aggregate data at the end of simulation runs. Note: All time-based
    datapoints are integers because in DES, time is only a relative, discrete unit.

    For our purposes, time is measured in minutes.
    """

    _id: int  # Mangle attribute name so as not to shadow builtin id object

    creation_time: Optional[int] = None
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    total_duration: Optional[int] = None

    pickpack_start_time: Optional[int] = None
    pickpack_duration: Optional[int] = None
    pickpack_queue_duration: Optional[int] = None

    prep_start_time: Optional[int] = None
    prep_duration: Optional[int] = None
    prep_queue_duration: Optional[int] = None

    flight_start_time: Optional[int] = None
    flight_duration: Optional[int] = None
    flight_queue_duration: Optional[int] = None

    status: OrderStatus = OrderStatus.CREATED


@dataclass
class DataMonitor:
    """
    Dataclass to hold information about the simulation as a whole. Often these will be populated
    by doing calculations on attributes from other dataclasses (like orders)
    """

    wait_times: list[int] = field(default_factory=list)
    discharge_times: list[int] = field(default_factory=list)
    batteries_charged: int = 0
    batteries_discharged: int = 0
    orders_delivered: int = 0
    delivery_times: list[int] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)


@dataclass
class Color:
    pass
