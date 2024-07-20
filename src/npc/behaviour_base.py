from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Callable


@dataclass
class Context(ABC):
    pass


ContextType = TypeVar("ContextType", bound=Context)


class Node(ABC):
    """
    Base class for all nodes on the behaviour tree.
    """
    @abstractmethod
    def run(self, context: ContextType | None):
        pass


class Composite(Node, ABC):
    children: list[Node]

    def __init__(self, children: list[Node] = None):
        """
        Base class for all composite nodes.
        :param children: List of nodes to compose
        """
        self.children = children or []


class Sequence(Composite):
    """
    Returns false on first child failure, true if all children succeed.
    """
    def run(self, context: ContextType | None):
        for child in self.children:
            if not child.run(context):
                return False
        return True


class Selector(Composite):
    """
    Returns true on first child success, false if all children fail.
    """
    def run(self, context: ContextType | None):
        for child in self.children:
            if child.run(context):
                return True
        return False


def weighted_shuffle(children: list[tuple[int, Node]]) -> list[Node]:
    """
    Shuffles a list of nodes based on their weights.
    References:
    https://softwareengineering.stackexchange.com/a/344274
    https://utopia.duth.gr/%7Epefraimi/research/data/2007EncOfAlg.pdf
    """
    # Calculate the shuffle order based on weights
    shuffle_order = sorted(
        range(len(children)),
        key=lambda i: random.random() ** (1.0 / children[i][0])
    )
    # Return the nodes in the new shuffled order
    return [children[i][1] for i in shuffle_order]


class RandomComposite(Node, ABC):
    children: list[tuple[int, Node]]

    def __init__(self, children: list[tuple[int, Node]] = None):
        """
        Base class for all random composite nodes.
        :param children: List of tuples containing weight and child
        """
        self.children = children or []


class RandomSelector(RandomComposite):
    """
    Returns true on first child success, false if all children fail.
    Children are shuffled prior to execution based on their weights.
    """
    def run(self, context: ContextType | None):
        for child in weighted_shuffle(self.children):
            if child.run(context):
                return True
        return False


class Decorator(Node, ABC):
    child: Node

    def __init__(self, child: Node):
        """
        Base class for all decorator nodes.
        :param child: Node to decorate
        """
        self.child = child


class Inverter(Decorator):
    """
    Inverts its child return value.
    """
    def run(self, context: ContextType | None):
        return not self.child.run(context)


class Leaf(Node, ABC):
    """
    Base class for all leaf nodes.
    """
    pass


class Condition(Leaf):
    condition_func: Callable[[ContextType], bool]

    def __init__(self, condition_func: Callable[[ContextType], bool]):
        """
        Runs the given condition function.
        :param condition_func: Callable[[ContextType], bool]
        """
        self.condition_func = condition_func

    def run(self, context: ContextType | None):
        return self.condition_func(context)


class Action(Leaf):
    action_func: Callable[[ContextType], bool]

    def __init__(self, action_func: Callable[[ContextType], bool]):
        """
        Runs the given action function.
        :param action_func: Callable[[ContextType], bool]
        """
        self.action_func = action_func

    def run(self, context: ContextType | None):
        return self.action_func(context)
