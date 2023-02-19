"""

"""
import random

import plotly.express as px
import simpy

from config import Config, DataMonitor, HubEnvironment
from hub import Hub


def main():
    pass


if __name__ == "__main__":
    # main(2)
    # print(wait_times)
    # fig = px.histogram(wait_times)
    # fig.show()

    # for i in range(1,20):
    #     wait_times = []
    #     main(i, wait_times)
    #     print(wait_times)

    # env = simpy.Environment()
    # hub = Hub(env)
    #
    # until = 12 * 60
    # # hub.env.run(until=until)  # one day
    # while hub.env.peek() < until:
    #     hub.env.step()
    # print(hub.env._queue[0])

    # pp = lea.poisson(10) # poisson = discrete gaussian
    # l = pp.random(10000)
    # lea.pmf()
    # fig = px.histogram(l)
    # fig.show()

    config = Config()
    monitor = DataMonitor()
    env = HubEnvironment(config, monitor)
    hub = Hub(env)

    until = 12 * 60
    hub.env.run(until=until)  # one day
    print(hub.env.monitor.wait_times)


# while hub.env.peek() < until:
#     hub.env.step()
# print(hub.env._queue[0])
