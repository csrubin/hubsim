"""
The Hub class is used to encapsulate all hub operations into a simulation environment
"""

import inspect
import random
import types
from dataclasses import dataclass
from inspect import currentframe
from typing import Any, Callable, Generator, Iterable, Optional, Union, cast, overload

import lea
import plotly.express as px
import plotly.graph_objs as go
import rich.style
import simpy
from config import Config, DataMonitor, HubEnvironment, HubResourceBase
from rich.console import Console
from rich.table import Table

# For mypy
# https://stackoverflow.com/questions/251464/how-to-get-a-function-name-as-a-string
get_caller = cast(types.FrameType, inspect.currentframe()).f_code.co_name

console = Console()

table = Table(show_header=True, header_style="bold")
table.add_column("Time")
table.add_column("Start/Stop")
table.add_column("Process")
table.add_column("Order")


# Utils
def simple_print(
    time: str,
    start_stop: str,
    process: str,
    order: str,
    style: Optional[rich.style.StyleType] = None,
) -> None:
    table.add_row(time, start_stop, process, order, style=style)


def sprint_start(time: str, process: str, order: str) -> None:
    simple_print(time, "[green]START[/green]", process, order)


def sprint_stop(time: str, process: str, order: str) -> None:
    simple_print(time, "[red]STOP[/red]", process, order)


class VerticalLift(HubResourceBase):
    def __init__(self, env: HubEnvironment, num_lifts: Optional[int] = None):
        if num_lifts:
            super().__init__(env, capacity=num_lifts)
        else:
            super().__init__(env, env.config.NUM_LIFTS)


class Pilot(HubResourceBase):
    def __init__(self, env: HubEnvironment, num_pilots: Optional[int] = None):
        if num_pilots:
            super().__init__(env, capacity=num_pilots)
        else:
            super().__init__(env, env.config.NUM_LIFTS)


class SimpleBattery(HubResourceBase):
    def __init__(self, env: HubEnvironment, num_batteries: Optional[int] = None):
        if num_batteries:
            super().__init__(env, capacity=num_batteries)
        else:
            super().__init__(env, env.config.NUM_BATTERIES)


class DeliverySpecialist(HubResourceBase):
    def __init__(
        self, env: HubEnvironment, num_delivery_specialists: Optional[int] = None
    ):
        if num_delivery_specialists:
            super().__init__(env, capacity=num_delivery_specialists)
        else:
            super().__init__(env, env.config.NUM_DELIVERY_SPECIALISTS)


class Drone(HubResourceBase):
    def __init__(self, env: HubEnvironment, num_drones: Optional[int] = None):
        if num_drones:
            super().__init__(env, capacity=num_drones)
        else:
            super().__init__(env, env.config.NUM_DRONES)


class Hub(object):
    def __init__(self, env: HubEnvironment) -> None:
        self.env = env
        self.config = env.config

        # Hub Resources
        # TODO: Resource Stores? containers?
        self.vertical_lift = VerticalLift(env)
        self.pilot = Pilot(env)
        self.delivery_specialist = DeliverySpecialist(env)
        self.drone = Drone(env)
        self.battery = SimpleBattery(env)

        # Order creation loop
        self.env.process(
            self.run_sim()
        )  # Schedule process to run simulation at instantiation of hub

    # Hub Processes
    def pick_pack(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        """
        Execute picking and packaging. Will be obsolete eventually.
        Args:
            order: Order counter for print and debug
            poisson: TODO: If True, use poisson model from config. If numerical, override config poisson model. If False,
                default to random interval from config

        Returns: Generator object for parallel pick_pack process model

        """

        sprint_start(str(self.env.now), str(get_caller), str(order))
        yield self.env.timeout(random.randint(*self.config.PICK_PACK_INTERVAL_MIN))
        sprint_stop(str(self.env.now), str(get_caller), str(order))

    def mission(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        """

        Args:
            order: Order counter for print and debug
            poisson:


        Returns: Generator object for parallel mission process model

        """
        sprint_start(str(self.env.now), str(get_caller), str(order))
        yield self.env.timeout(random.randint(*self.config.MISSION_INTERVAL_MIN))
        sprint_stop(str(self.env.now), str(get_caller), str(order))

    def prep_drone(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        yield self.env.timeout(random.randint(*self.config.PREP_DRONE_INTERVAL_MIN))

    def takeoff(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        yield self.env.timeout(random.randint(*self.config.TAKEOFF_INTERVAL_MIN))

    def landing(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        yield self.env.timeout(random.randint(*self.config.LANDING_INTERVAL_MIN))

    def swap_batteries(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        yield self.env.timeout(random.randint(*self.config.SWAP_BATTERIES_MIN))

    def charge_batteries(
        self, order: int, poisson: Union[bool, int, float] = False
    ) -> Generator[simpy.events.Timeout, Any, Any]:
        yield self.env.timeout(random.randint(*self.config.CHARGE_BATTERIES_MIN))

    def deliver_order(self, order: int) -> Generator[simpy.events.Timeout, Any, Any]:
        arrival = self.env.now
        # with self.delivery_specialist.request() as req:
        #     yield req
        #     yield self.env.process(self.pick_pack(order))
        #
        # with self.drone.request() as req:
        #     yield req
        #     yield self.env.process(self.mission(order))

        with self.delivery_specialist.request() as dsreq, self.drone.request() as dreq:
            yield self.env.all_of([dsreq, dreq])
            yield self.env.all_of(
                [
                    self.env.process(self.pick_pack(order)),
                    self.env.process(self.mission(order)),
                ]
            )

        self.env.monitor.wait_times.append(self.env.now - arrival)

    def run_sim(self):
        order = 0
        while True:  # Run until time-limit or event occurs: env.run(until=12*60)
            rand = random.randint(*self.env.config.TIME_BETWEEN_ORDERS_INTERVAL_MIN)
            yield self.env.timeout(rand)
            self.env.process(self.deliver_order(order))
            order += 1


if __name__ == "__main__":
    config = Config()
    monitor = DataMonitor()

    # Change config
    config.NUM_DRONES = 25
    config.NUM_PILOTS = 25
    config.NUM_DELIVERY_SPECIALISTS = 25
    config.PICK_PACK_INTERVAL_MIN = (1, 2)
    config.TIME_BETWEEN_ORDERS_INTERVAL_MIN = (1, 2)

    env = HubEnvironment(config, monitor)
    hub = Hub(env)
    until = 12 * 60
    hub.env.run(until=until)  # one day

    print(hub.env.monitor.wait_times)
    console.print(table)
