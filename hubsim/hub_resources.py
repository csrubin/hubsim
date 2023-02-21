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


class HubResourceBase(simpy.Resource):
    """Base class for hub resources using HubEnvironment for config and simulation monitoring"""

    def __init__(self, env: HubEnvironment, capacity: Optional[int] = None):
        super().__init__(env, capacity)
        self.env = env
        self.monitor = env.monitor
        self.config = env.config


class VerticalLift(HubResourceBase):
    """Vertical lift modeled as a hub resource with capacity equal to number of working lifts at a Hub"""

    def __init__(self, env: HubEnvironment, num_lifts: Optional[int] = None):
        if num_lifts:
            super().__init__(env, capacity=num_lifts)
        else:
            super().__init__(env, env.config.NUM_LIFTS)


class Pilot(HubResourceBase):
    """Pilots modeled as a hub resource with capacity equal to number of pilots during shift"""

    def __init__(self, env: HubEnvironment, num_pilots: Optional[int] = None):
        if num_pilots:
            super().__init__(env, capacity=num_pilots)
        else:
            super().__init__(env, env.config.NUM_LIFTS)


class SimpleBattery(HubResourceBase):
    """Batteries modeled as a simple resource with with capacity equal to number of batteries at a hub
    TODO: Require 2 batteries per drone per mission
    TODO: implement more complex battery operations processes
    """

    def __init__(self, env: HubEnvironment, num_batteries: Optional[int] = None):
        if num_batteries:
            super().__init__(env, capacity=num_batteries)
        else:
            super().__init__(env, env.config.NUM_BATTERIES)


class DeliverySpecialist(HubResourceBase):
    """Delivery Specialist modeled as a hub resource with capacity equal to number of specialists during shift"""

    def __init__(self, env: HubEnvironment, num_delivery_specialists: Optional[int] = None):
        if num_delivery_specialists:
            super().__init__(env, capacity=num_delivery_specialists)
        else:
            super().__init__(env, env.config.NUM_DELIVERY_SPECIALISTS)


class Drone(HubResourceBase):
    """Drones modeled as a hub resource with capacity equal to number of drones at a Hub"""

    def __init__(self, env: HubEnvironment, num_drones: Optional[int] = None):
        if num_drones:
            super().__init__(env, capacity=num_drones)
        else:
            super().__init__(env, env.config.NUM_DRONES)


# TODO: VOs? Other employees? employee module
class VisualObserver(HubResourceBase):
    pass
