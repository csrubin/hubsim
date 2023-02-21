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
import simpy


class Config(object):
    def __init__(self):
        # TODO Idk what this should be -- maybe defind lea.pmf based of histogram bins built from legit hub data?
        self.pick_pack_timeout = lea.poisson(10)

    # Hub operations task duration intervals
    PICK_PACK_INTERVAL_MIN = (5, 25)  # i.e. pick-packing takes between 5 and 15 min
    FLIGHT_INTERVAL_MIN = (5, 10)
    PREP_DRONE_INTERVAL_MIN = (1, 5)
    CHARGE_BATTERIES_MIN = (15, 60)
    DISCHARGE_BATTERIES_MIN = CHARGE_BATTERIES_MIN  # Only for testing

    ORDER_INTERVAL_MIN = (10, 45)
    OPERATING_HOURS_MIN = 12.0 * 60.0  # 8am - 8pm

    # Hub resource defaults
    NUM_PILOTS = 2
    NUM_DELIVERY_SPECIALISTS = 1
    NUM_DRONES = 3

    # Not used yet
    NUM_LIFTS = 1
    NUM_BATTERIES = 10

    RANDOM = False


class OrderStatus(IntEnum):
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
    Times are ints bc simpy time is discrete ints
    """

    id: int

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
    wait_times: list[int] = field(default_factory=list)  # Times are ints in simpy (discrete steps)
    discharge_times: list[int] = field(default_factory=list)
    batteries_charged: int = 0
    orders_delivered: int = 0
    delivery_times: list[int] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)


@dataclass
class Color:
    pass


class HubEnvironment(simpy.Environment):
    def __init__(self, config: Config, monitor: DataMonitor):
        super().__init__()
        self.config = config
        self.monitor = monitor

    # @st.cache_data
    # def run(
    #     self, until: Optional[Union[SimTime, Event]] = None
    # ) -> Optional[Any]:
    #     return super().run(until)


class HubResourceBase(simpy.Resource):
    def __init__(self, env: HubEnvironment, capacity: Optional[int] = None):
        super().__init__(env, capacity)
        self.env = env
        self.monitor = env.monitor
        self.config = env.config
