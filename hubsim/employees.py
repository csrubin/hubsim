"""
Contains all classes related to employees
Type of Worker, different permissions or possible tasks. Important as input to simulation

TODO: More
"""

from typing import Optional

from hub_resources import HubEnvironment, HubResource, HubStore

# TODO: Define resourcepool (Maybe use simpy.Stores) class? Defines resources with overlapping capabilities


class Pilot(HubResource):
    """Pilots modeled as a hub resource with capacity equal to number of pilots during shift"""

    def __init__(self, env: HubEnvironment, num_pilots: Optional[int] = None):
        if num_pilots:
            super().__init__(env, capacity=num_pilots)
        else:
            super().__init__(env, env.config.NUM_LIFTS)


class DeliverySpecialist(HubResource):
    """Delivery Specialist modeled as a hub resource with capacity equal to number of specialists during shift"""

    def __init__(self, env: HubEnvironment, num_delivery_specialists: Optional[int] = None):
        if num_delivery_specialists:
            super().__init__(env, capacity=num_delivery_specialists)
        else:
            super().__init__(env, env.config.NUM_DELIVERY_SPECIALISTS)


# TODO: VOs? Other employees? employee module
class VisualObserver(HubResource):
    pass


class HubEmployee(HubResource):
    pass


class RemotePilotInCommand(HubEmployee):
    pass


class SafetyPilot(HubEmployee):
    pass


class EmployeeStore(HubStore):
    pass
