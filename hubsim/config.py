"""
Configuration file used for defining default hub operations parameters and other
miscellaneous configuration details. Initially using .py file for simplicity, but may choose
a more appropriate configuration file format in the future (e.g., TOML, YAML, etc.)

TODO: Determine necessity of config file change and execute if needed
"""

from dataclasses import dataclass, field
from typing import Optional

import lea
import simpy


class Config(object):
    def __init__(self):
        self.pick_pack_timeout = lea.poisson(10)  # Idk what this should be

    # Hub operations task duration intervals
    PICK_PACK_INTERVAL_MIN = (5, 25)  # i.e. pick-packing takes between 5 and 15 min
    MISSION_INTERVAL_MIN = (5, 10)

    PREP_DRONE_INTERVAL_MIN = (1, 5)
    TAKEOFF_INTERVAL_MIN = (0.5, 2)
    LANDING_INTERVAL_MIN = (0.5, 2)
    SWAP_BATTERIES_MIN = (1, 2)
    CHARGE_BATTERIES_MIN = (15, 60)
    DISCHARGE_BATTERIES_MIN = CHARGE_BATTERIES_MIN  # Only for testing

    TIME_BETWEEN_ORDERS_INTERVAL_MIN = (1, 10)
    OPERATING_HOURS_MIN = 12 * 60  # 8am - 8pm

    # Hub resource defaults
    NUM_PILOTS = 2
    NUM_DELIVERY_SPECIALISTS = 4
    NUM_LIFTS = 1
    NUM_DRONES = 3
    NUM_BATTERIES = 10


@dataclass
class DataMonitor:
    wait_times: list[int] = field(
        default_factory=list
    )  # Times are ints in simpy (discrete steps)
    discharge_times: list[int] = field(default_factory=list)
    batteries_charged: int = 0
    orders_delivered: int = 0


class HubEnvironment(simpy.Environment):
    def __init__(self, config: Config, monitor: DataMonitor):
        super().__init__()
        self.config = config
        self.monitor = monitor


class HubResourceBase(simpy.Resource):
    def __init__(self, env: HubEnvironment, capacity: Optional[int] = None):
        super().__init__(env, capacity)
        self.env = env
        self.monitor = env.monitor
        self.config = env.config
