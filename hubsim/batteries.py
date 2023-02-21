"""
Contains all classes related to battery resources
Todo: More
"""

import inspect
import random
from dataclasses import dataclass
from typing import Any, Callable, Generator, Iterable, Optional, overload

import lea
import plotly.express as px
import plotly.graph_objs as go
import simpy
from config import Config, DataMonitor
from hub_resources import HubEnvironment, HubResourceBase


class Battery(HubResourceBase):
    """
    Battery modeled as a simpy resource with capacity of 1. Two charged batteries required per mission.

    TODO: Threshold for "charged" ? or leave as binary?
    TODO: self.loggers?

    """

    def __init__(
        self, env: HubEnvironment, _id: int
    ):  # TODO: does it need an id attribute? Replace idx args in processes?
        super().__init__(env, capacity=1)
        self.charged = bool(random.randint(0, 1))  # Randomly spawn batteries that are charged and discharged
        self.stowed = True
        self._id = _id

    # Battery Processes
    def charge(self) -> Generator[simpy.Timeout, Any, Any]:
        """
        Charge battery. Assumes binary state (charged, not charged).
        Args:
            idx: Index/counter used for print statements and debugging

        Returns: Generator object for charging battery for a period of time
        """

        # Fail immediately here to indicate attempt to charge already charged batteries -- indicates other logic issue
        # Only charge previously discharged batteries
        assert (
            not self.charged
        ), f"Attempt to charge already charged battery: #{self._id} | charged: {self.charged}, stowed: {self.stowed}"

        self.stowed = False  # Not stowed if charging
        yield self.env.timeout(
            random.randint(*self.config.CHARGE_BATTERIES_MIN)
        )  # Charge for random time in defined interval
        self.charged = True  # When finished charging, set charge state to true

        # Stow battery after charging completes
        self.env.process(self.stow(self._id))
        self.monitor.batteries_charged += 1
        print(f"Battery Charged: {self._id}")

    def discharge(self, idx: int = 0) -> Generator[simpy.Timeout, Any, Any]:
        """
        Discharge battery. Assumes binary state (charged, not charged).
        Args:
            idx: Index/counter used for print statements and debugging

        Returns: Generator object for discharging battery for a period of time

        """
        # Only start missions at 100%, fail immediately if we get here
        assert self.charged, f"Attempt to discharge not charged battery: #{idx}"

        self.stowed = False  # Discharging has begun, battery is no longer stored
        yield self.env.timeout(random.randint(*self.config.DISCHARGE_BATTERIES_MIN))
        self.charged = False  # Discharging has occurred, battery is no longer charged

    def stow(self, idx: int = 0) -> Generator[simpy.Timeout, Any, Any]:
        """
        Store battery. Assumes this takes 0 time. Kept as generator for consistency with other processes
        TODO: is this needed? Is stowing a battery process or a battery_store process? or both?
        Args:
            idx: Index/counter used for print statements and debugging

        Returns: Generator object for storing battery
        """
        assert not self.stowed  # Fail if attempt to store a battery that is already stored
        yield self.env.timeout(0)  # Storage happens immediately TODO: should this take time?
        self.stowed = True


class BatteryCharger(HubResourceBase):
    """"""

    def __init__(self, env, capacity: int = 4):
        super().__init__(env, capacity=capacity)

    def charge(self, battery: Battery):
        yield self.env.process(battery.charge())


class BatteryStore(simpy.FilterStore):
    """
    Battery storage modeled as a simpy store that holds Battery objects. FilterStore subclassed to enable
    filtering requests based on battery states
    """

    def __init__(
        self,
        env: HubEnvironment,
        storage_capacity: int = 20,  # TODO: convert to config object paradigm
        charge_capacity: int = 2,
        num_batteries: int = 10,
    ):
        """

        Args:
            env: Obligatory environment reference
            storage_capacity: Total amount of batteries that can be stowed
            charge_capacity: Total amount of chargers
            num_batteries: Total number of batteries that can be processed
        """
        super().__init__(env, capacity=storage_capacity)
        self.env = env
        self.items = [Battery(env, i) for i in range(num_batteries)]
        self.chargers = BatteryCharger(self.env, capacity=charge_capacity)

        # Creation loop, for testing # TODO: remove
        self.env.process(self.run_sim())

    # https://stackoverflow.com/questions/2024566/how-to-access-outer-class-from-an-inner-class
    # def create_charger(self) -> simpy.Resource:
    #     """Factory method to create chargers and access BatteryStore from Charger class"""
    #     return BatteryCharger(self)

    # Maybe shouldnt overload, necessary at all?
    # def get(self):
    #     for _ in range(2):
    #         yield super().get(lambda battery: battery.charged is True)

    def run_chargers(self, idx: int, battery: Battery):
        with self.chargers.request() as req:
            yield req
            yield self.env.any_of(self.chargers.charge(battery))

    def run_sim(self):
        while True:
            # Spawn discharge process between every 1 and 5 min
            rand = random.randint(1, 5)
            yield self.env.timeout(rand)
            for idx, b in enumerate(self.items):
                if b.charged is True:
                    self.env.process(b.discharge(idx))
                    print(f"Start discharging Battery {idx} at {self.env.now}")

                if b.charged is False and b.stowed is True:
                    yield self.env.process(self.run_chargers(idx, b))
                    print(f"Start charging Battery {idx} at {self.env.now}")


if __name__ == "__main__":
    config = Config()
    monitor = DataMonitor()

    env = HubEnvironment(config, monitor)
    batt_str = BatteryStore(env)
    until = 12 * 60
    batt_str.env.run(until=until)  # one day
    print(monitor.batteries_charged)
