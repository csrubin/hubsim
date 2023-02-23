"""
Contains all classes related to battery resources
TODO: More
"""

import random
from collections import deque
from enum import IntEnum
from typing import Any, Generator, Optional

from config import Config, DataMonitor
from hub_resources import HubEnvironment, HubResource, HubStore
from simpy import Timeout


class BatteryStatus(IntEnum):
    """Process or place battery could be. Use Normal bool for charged/discharged"""

    CHARGING_QUEUE = 0
    CHARGING_ACTIVE = 1
    CHARGING_INACTIVE = 2
    DEPLOYMENT_QUEUE = 3
    DEPLOYED = 4
    # TODO Maybe add in maintenance state?


# TODO: how to create state map to exclude conditions that could never be true?
# Ex: Charged and in charge queue? Charged+DeployedQueue, Charged+Deployed
# Write state_transition() function to move from one to the other and set attrs appropriately


class Battery(HubResource):
    """
    Battery modeled as a simpy resource with capacity of 1.
    TODO Two charged batteries required per mission.
    TODO: self.loggers?
    """

    def __init__(self, env: HubEnvironment, _id: int):
        super().__init__(env, capacity=1)
        self._id = _id
        self.charged: bool = bool(random.randint(0, 1))  # Randomly spawn batteries that are charged and discharged

        # Set status as in a queue based on whether battery is charged. Assume only queues are
        # populated at the beginning of all simulations
        if self.charged is True:
            self.status = BatteryStatus.DEPLOYMENT_QUEUE
        else:
            self.status = BatteryStatus.CHARGING_QUEUE

    def __repr__(self):
        return f"B{self._id}"  # Easier to print(batt) instead of print(batt._id)

    # Battery Processes
    def charge(self) -> Generator[Timeout, Any, Any]:
        """
        Charge battery. Assumes binary state (charged, not charged).

        Returns: Generator object for charging battery for a period of time
        """

        # Fail immediately here to indicate attempt to charge already charged batteries -- indicates other logic issue
        # Only charge previously discharged batteries
        assert self.charged is False, f"ERROR: Attempt to charge BATTERY {self._id}, already charged."

        # Charge for random time in defined interval
        self.status = BatteryStatus.CHARGING_ACTIVE
        yield self.env.timeout(random.randint(*self.config.CHARGE_BATTERIES_INTERVAL))

        # Finished charging, not yet moved to deployment queue
        self.charged = True
        self.status = BatteryStatus.CHARGING_INACTIVE

        # Queue battery after charging completes
        yield self.env.process(self._queue())

    def discharge(self) -> Generator[Timeout, Any, Any]:
        """
        Discharge battery. Assumes binary state (charged, not charged).

        Returns: Generator object for discharging battery for a period of time
        """
        # Only start missions at 100%, fail immediately if we get here
        assert self.charged is True, f"ERROR: Attempt to discharge BATTERY {self._id}, already discharged."

        # Discharge for random time in defined interval
        self.status = BatteryStatus.DEPLOYED
        yield self.env.timeout(random.randint(*self.config.DISCHARGE_BATTERIES_INTERVAL))

        # Discharging has occurred, battery is no longer charged
        self.charged = False

        # Queue battery after discharging completes
        yield self.env.process(self._queue())

    def _queue(self) -> Generator[Timeout, Any, Any]:
        """
        Move battery status to appropriate queue after charge/discharge processes
        TODO: is this a Battery process or a BatteryStore process?

        Returns: Generator object for placing battery in correct queue
        """
        # Fail if attempt to store a battery that is already in a queue
        assert self.status.value not in [
            BatteryStatus.DEPLOYMENT_QUEUE.value,
            BatteryStatus.CHARGING_QUEUE.value,
        ], f"ERROR: Attempt to queue BATTERY {self._id}, already queued."

        # TODO: Should I be introducing Events/Conditions here instead of Timeouts?
        # Should this take time? I dont think within battery,
        # but a person (resource) moving it from one place to another should
        yield self.env.timeout(0)

        if self.charged is True:
            self.status = BatteryStatus.DEPLOYMENT_QUEUE
            # TODO: make available in BatteryStore.items  OR OR OR filter for batteries that are in deployment queue when requesting

        elif self.charged is False:
            self.status = BatteryStatus.CHARGING_QUEUE


class BatteryStore(HubStore):
    """
    Battery storage modeled as a simpy store that holds Battery objects. FilterStore subclassed to enable
    filtering requests based on battery states
    """

    def __init__(self, env: HubEnvironment):
        super().__init__(env, capacity=env.config.BATTERY_STORE_CAPACITY)

        # Populate store with batteries
        self.batteries = [Battery(env, i) for i in range(self.config.NUM_BATTERIES)]

        # TODO: deques/queues might be unnecessary
        self.charge_queue = list(filter(lambda batt: not batt.charged, self.batteries))
        self.deploy_queue = list(filter(lambda batt: batt.charged, self.batteries))
        self.charge_process_queue = deque([])

        # List of AVAILABLE items (for requesting), put charged batteries into available queue
        self.items = self.deploy_queue  # Link lists to alias "items" TODO: potential bug with reassignment

        self.chargers = HubResource(self.env, capacity=self.config.NUM_CHARGERS)

        """
        Construct: Let simpy functionality
        deal with requesting/releasing, just add functionality to BatteryStore to
        take batteries out of the loop and put them in a charging queue that's all running in the
        same environment so time is  shared.

        # TODO NEXT Look into yielding simpy Events (more subclassing?)
        # Condition events are interesting ... lambdas filtering to returning true
        """

        # TODO Handle assumption that battery charging is happening "perfectly" (fixed?)
        # AKA all events happen as SOON as they are able (which is not often the case with humans)

        # TODO monitor queue of uncharged batteries and operate accordingly
        self.env.process(self.run_battery_store())

    # https://stackoverflow.com/questions/2024566/how-to-access-outer-class-from-an-inner-class
    # def create_charger(self) -> simpy.Resource:
    #     """Factory method to create chargers and access BatteryStore from Charger class"""
    #     return BatteryCharger(self)

    def _charge_battery(self, battery: Battery) -> Generator[Timeout, Any, Any]:
        """
        Charge battery using resource slot in battery charger
        Args:
            battery: Battery object to be charged

        Returns: Generator object for processing battery charging

        """
        with battery.request() as req:
            yield req
            yield self.env.process(battery.charge())
            self.monitor.batteries_charged += 1

    def _discharge_battery(self, battery: Battery) -> Generator[Timeout, Any, Any]:
        """
        Discharge battery using resource slot in battery charger
        Args:
            battery: Battery object to be charged

        Returns: Generator object for processing battery charging

        """
        with battery.request() as req:
            yield req
            yield self.env.process(battery.discharge())
            self.monitor.batteries_discharged += 1

    def _run_chargers(self, battery: Battery) -> Generator[Timeout, Any, Any]:
        with self.chargers.request() as req:
            yield req
            yield self.env.process(self._charge_battery(battery))
            self.charge_queue.remove(battery)

    def _run_deployment(self, battery: Battery) -> Generator[Timeout, Any, Any]:
        yield self.env.process(self._discharge_battery(battery))
        self.deploy_queue.remove(battery)

    def run_battery_store(self):
        """TODO: Does this get yielded to by hub or running its own while loop?"""

        while True:
            # Spawn battery store checking process
            rand = random.randint(15, 20)
            yield self.env.timeout(rand)

            # Collect processes to do simultaneously
            for battery in self.batteries:

                # Don't queue batteries for any processes if they're already being used (.count attr from simpy)
                if battery.count > 0:
                    continue

                # Move batteries to appropriate queue based on their status
                if (
                    battery.status == BatteryStatus.DEPLOYMENT_QUEUE
                    and battery not in self.deploy_queue
                    and battery.charged is True
                ):
                    self.deploy_queue.append(battery)
                elif (
                    battery.status == BatteryStatus.CHARGING_QUEUE
                    and battery not in self.charge_queue
                    and battery.charged is not True
                ):
                    self.charge_queue.append(battery)

                # Append appropriate process based on queue
                # if battery in self.deploy_queue:
                # self.charge_process_queue.append(self.env.process((self._run_deployment(battery)))) # Testing only

                if battery in self.charge_queue:
                    self.charge_process_queue.append(self.env.process((self._run_chargers(battery))))

            # Kick off collected processes
            yield self.env.all_of(self.charge_process_queue)


if __name__ == "__main__":
    from hub import Hub, HubEnvironment

    random.seed(42)

    config = Config()
    monitor = DataMonitor()

    hours = 12
    hubenv = HubEnvironment(config, monitor)
    hub = Hub(hubenv)
    until = hours * 60
    # hub.env.run(until)

    try:
        while hubenv.peek() < until:
            now = hubenv.now
            hubenv.step()
            if hubenv.now != now:
                pass
    except Exception as e:
        print(f"EXITING SIMULATION | {e}")
    finally:
        print(f"Batteries Charged: {hub.monitor.batteries_charged}")
