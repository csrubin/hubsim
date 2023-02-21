"""
The Hub class is used to encapsulate all hub operations into a simulation environment
"""

import random
from typing import Any, Generator

from config import Config, DataMonitor, Order, OrderStatus
from hub_resources import DeliverySpecialist, Drone, Pilot, SimpleBattery, VerticalLift
from simpy import Environment, Timeout


class HubEnvironment(Environment):
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


class Hub(object):
    """A DroneUp Hub environment for simulating processes and operations that occur at delivery hubs"""

    def __init__(self, env: HubEnvironment) -> None:
        self.env = env
        self.config = env.config
        self.monitor = env.monitor

        # Hub Resources
        # TODO: Resource Stores? containers?
        self.vertical_lift = VerticalLift(env)
        self.pilot = Pilot(env)
        self.delivery_specialist = DeliverySpecialist(env)
        self.drone = Drone(env)
        self.battery = SimpleBattery(env)

        # Order creation loop
        self.env.process(self.create_orders())  # Schedule process to run simulation at instantiation of hub

        if self.config.RANDOM is False:
            random.seed(42)

    # Hub Processes
    def pick_pack(self, order: Order) -> Generator[Timeout, Any, Any]:
        """
        Execute picking and packaging. Will be obsolete eventually when WM takes over this portion of our workflow.

        Args:
            order: Order object for monitoring entity flow as created by create_orders()

        Returns: Generator object for parallel pick_pack process model

        """
        order.pickpack_start_time = self.env.now
        order.status = OrderStatus.PREP  # TODO: Bug??? new status?
        yield self.env.timeout(random.randint(*self.config.PICK_PACK_INTERVAL_MIN))
        order.pickpack_duration = self.env.now - order.pickpack_start_time

    def flight(self, order: Order) -> Generator[Timeout, Any, Any]:
        """
        Execute flight plan. Assumes all conditions for flight have been met.
        Args:
            order: Order object for monitoring entity flow as created by create_orders()

        Returns: Generator object for parallel flight process model

        """
        order.flight_start_time = self.env.now
        order.status = OrderStatus.FLIGHT
        yield self.env.timeout(random.randint(*self.config.FLIGHT_INTERVAL_MIN))
        order.flight_duration = self.env.now - order.flight_start_time

    def prep_drone(self, order: Order) -> Generator[Timeout, Any, Any]:
        """
        Execute drone preparation activities. Can be used as an abstraction for all processes related to hardware
        preparation (therefore not pickpacking).
        TODO: Currently unused
        Args:
            order: Order object for monitoring entity flow as created by create_orders()

        Returns: Generator object for parallel drone preparation process model

        """
        order.prep_start_time = self.env.now
        order.status = OrderStatus.PREP
        yield self.env.timeout(random.randint(*self.config.PREP_DRONE_INTERVAL_MIN))
        order.prep_duration = self.env.now - order.prep_start_time

    def deliver_order(self, order: Order) -> Generator[Timeout, Any, Any]:
        """
        Execute delivery process given that an order has been created. This is the main process of interest, and
        has a defined start and end.
        TODO: figure out parallelism here--will have to rework order status/queueing time handline
        Args:
            order: Order object for monitoring entity flow as created by create_orders()

        Returns: Generator for handling top-level process flow
        """

        order.start_time = self.env.now
        order.status = OrderStatus.STARTED

        # Request delivery specialist, suspend function until available
        with self.delivery_specialist.request() as req:  # TODO: create pool of employee resources
            pickpack_req_time = self.env.now
            order.status = OrderStatus.PREP_QUEUE
            yield req
            order.pickpack_queue_duration = self.env.now - pickpack_req_time

            # Pickpack order
            yield self.env.process(self.pick_pack(order))

        # Request drone, pilot, and battery, suspend function until ALL are available
        with self.drone.request() as drone_req, self.pilot.request() as pilot_req, self.battery.request() as batt_req:
            prep_req_time = self.env.now
            order.status = OrderStatus.FLIGHT_QUEUE
            yield self.env.all_of([drone_req, pilot_req, batt_req])
            order.flight_queue_duration = self.env.now - prep_req_time

            # Fly order
            yield self.env.process(self.flight(order))

        # with self.delivery_specialist.request() as dsreq, self.drone.request() as dreq:
        #     yield self.env.all_of([dsreq, dreq])
        #     yield self.env.all_of(
        #         [
        #             self.env.process(self.pick_pack(order)),
        #             self.env.process(self.mission(order)),
        #         ]
        #     )

        # End of delivery monitoring
        order.completion_time = self.env.now
        order.status = OrderStatus.COMPLETED
        order.total_duration = order.completion_time - order.creation_time

        self.env.monitor.wait_times.append(order.total_duration)
        self.env.monitor.delivery_times.append(order.completion_time)
        self.env.monitor.orders_delivered += 1

    def create_orders(self) -> Generator[Timeout, Any, Any]:
        """
        Infinite creation-loop for introducing orders into the system.
        TODO: add option to set specific # of deliveries

        Returns: Generator for waiting time between order creation
        """

        order_id = 0
        while True:  # Run until time-limit or event occurs: env.run(until=12*60)
            # Wait some time between orders
            yield self.env.timeout(*self.env.config.ORDER_INTERVAL_MIN)

            # Create new order object, save object and relevant info
            order = Order(order_id)
            order.creation_time = self.env.now
            order.status = OrderStatus.CREATED
            self.monitor.orders.append(order)

            # Queue order for delivery
            self.env.process(self.deliver_order(order))
            order_id += 1


if __name__ == "__main__":
    raise RuntimeError("Do not run hub.py as a script.")
