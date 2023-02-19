"""sample model execution"""
from simpy import Environment
import random

# import examples.resources_loop.resource_loop_example_model as model_module
# from ..resources_loop import resource_loop_example_model as model_module

"""model template for generated model files"""
from casymda.blocks import (
    Delay,
    Entity,
    NamedResource,
    ResourceRelease,
    ResourceSeizeQueue,
    RoundRobinGateway,
    SeizeProcessRelease,
    Sink,
    Source,
)


class Model:
    """generated model"""

    def __init__(self, env):

        self.env = env
        self.finish_count = 0

        #!resources+components

        self.resource_1 = NamedResource(
            self.env, "resource_1", xy=(525, 43), capacity=3, ways={}
        )

        self.source = Source(
            self.env,
            "source",
            xy=(25, 169),
            inter_arrival_time=5,
            max_entities=6,
            ways={"wait_for_resource": [(43, 169), (125, 169)]},
        )

        self.sink = Sink(self.env, "sink", xy=(1035, 169), ways={})

        self.proc_1 = Delay(
            self.env,
            "proc_1",
            xy=(525, 169),
            process_time=5,
            block_capacity=1,
            ways={"gateway_2": [(575, 169), (730, 169)]},
        )

        self.wait_for_resource = ResourceSeizeQueue(
            self.env,
            "wait_for_resource",
            resource=self.resource_1,
            xy=(175, 169),
            ways={"gateway_1": [(225, 169), (280, 169)]},
        )

        self.release_resource = ResourceRelease(
            self.env,
            "release_resource",
            resource=self.resource_1,
            xy=(895, 169),
            ways={"sink": [(945, 169), (1017, 169)]},
        )

        self.proc_2 = Delay(
            self.env,
            "proc_2",
            xy=(525, 363),
            process_time=5,
            block_capacity=1,
            ways={"gateway_1": [(475, 363), (305, 363), (305, 194)]},
        )

        self.gateway_2 = RoundRobinGateway(
            self.env,
            "gateway_2",
            xy=(755, 169),
            ways={
                "release_resource": [(780, 169), (845, 169)],
                "proc_2": [(755, 194), (755, 363), (575, 363)],
            },
        )

        self.gateway_1 = RoundRobinGateway(
            self.env,
            "gateway_1",
            xy=(305, 169),
            ways={"proc_1": [(330, 169), (475, 169)]},
        )

        #!model

        self.model_components = {
            "source": self.source,
            "sink": self.sink,
            "proc_1": self.proc_1,
            "wait_for_resource": self.wait_for_resource,
            "release_resource": self.release_resource,
            "proc_2": self.proc_2,
            "gateway_2": self.gateway_2,
            "gateway_1": self.gateway_1,
        }

        self.model_graph_names = {
            "source": ["wait_for_resource"],
            "sink": [],
            "proc_1": ["gateway_2"],
            "wait_for_resource": ["gateway_1"],
            "release_resource": ["sink"],
            "proc_2": ["gateway_1"],
            "gateway_2": ["release_resource", "proc_2"],
            "gateway_1": ["proc_1"],
        }
        # translate model_graph_names into corresponding objects
        self.model_graph = {
            self.model_components[name]: [
                self.model_components[nameSucc]
                for nameSucc in self.model_graph_names[name]
            ]
            for name in self.model_graph_names
        }

        for component in self.model_graph:
            component.successors = self.model_graph[component]



def simple_run(interval):
    """run model"""

    env = Environment()
    model = Model(env)
    model.source.max_entities = 200

    low, high = interval

    # model.env.run()
    until = 50
    while env.peek() < until:
        model.env.step()
        model.source.inter_arrival_time = random.randint(low, high)
        # print(model.source.inter_arrival_time)

    if not model.source.overall_count_in > model.proc_1.overall_count_in:

        print(f"MaxEnt: {model.source.max_entities}\n"
              f"Source: {model.source.overall_count_in}\n"
              f"Proc1: {model.proc_1.overall_count_in}\n"
              f"Proc2: {model.proc_2.overall_count_in}\n"
              f"Sink: {model.sink.overall_count_in}\n"
              f"Source > Proc1: {model.source.overall_count_in > model.proc_1.overall_count_in}\n"
              f"Interval: {low, high}\n")



if __name__ == "__main__":

    for i in range(10):
        low = random.randint(1, 10)
        high = random.randint(10, 30)
        simple_run((low, high))
