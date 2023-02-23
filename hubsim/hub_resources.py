"""
Helper classes for clearly defining hub resources
TODO: rename file?
"""
from typing import Optional

import simpy
from config import Config, DataMonitor


class HubEnvironment(simpy.Environment):
    """Subclass of simpy.Environment for adding configuration and monitoring utilities"""

    def __init__(self, config: Config, monitor: DataMonitor):
        super().__init__()
        self.config = config
        self.monitor = monitor

    # TODO figure out caching
    # @st.cache_data
    # def run(
    #     self, until: Optional[Union[SimTime, Event]] = None
    # ) -> Optional[Any]:
    #     return super().run(until)


class HubResource(simpy.Resource):
    """Base class for hub resources using HubEnvironment for config and simulation monitoring"""

    def __init__(self, env: HubEnvironment, capacity: Optional[int]):
        super().__init__(env, capacity=capacity)
        self.env = env
        self.monitor = env.monitor
        self.config = env.config


class HubStore(simpy.FilterStore):
    def __init__(self, env: HubEnvironment, capacity: Optional[int]):
        super().__init__(env, capacity=capacity)
        self.env = env
        self.monitor = env.monitor
        self.config = env.config


class VerticalLift(HubResource):
    """Vertical lift modeled as a hub resource with capacity equal to number of working lifts at a Hub"""

    def __init__(self, env: HubEnvironment):
        super().__init__(env, env.config.NUM_LIFTS)


class SimpleBattery(HubResource):
    """Batteries modeled as a simple resource with with capacity equal to number of batteries at a hub
    TODO: Require 2 batteries per drone per mission
    TODO: implement more complex battery operations processes
    """

    def __init__(self, env: HubEnvironment):
        super().__init__(env, env.config.NUM_BATTERIES)


class Drone(HubResource):
    """Drones modeled as a hub resource with capacity equal to number of drones at a Hub"""

    def __init__(self, env: HubEnvironment):
        super().__init__(env, env.config.NUM_DRONES)
