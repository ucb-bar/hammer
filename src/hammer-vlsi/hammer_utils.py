#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  utils.py
#  Misc utils/functions for hammer_vlsi.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

import copy
from functools import reduce
import inspect
from typing import List, Any, Set, Dict, Tuple, TypeVar, Callable, Iterable, Optional

__all__ = ['deepdict', 'deeplist', 'add_lists', 'add_dicts', 'reverse_dict', 'in_place_unique', 'topological_sort',
           'reduce_named', 'get_or_else', 'optional_map', 'check_function_type']


def deepdict(x: dict) -> dict:
    """
    Deep copy a dictionary. This is needed because dict() by itself only makes a shallow copy.
    See https://stackoverflow.com/questions/5105517/deep-copy-of-a-dict-in-python
    Convenience function.

    :param x: Dictionary to copy
    :return: Deep copy of the dictionary provided by copy.deepcopy().
    """
    return copy.deepcopy(x)


def deeplist(x: list) -> list:
    """
    Deep copy a list. This is needed because list() by itself only makes a shallow copy.
    See https://stackoverflow.com/questions/5105517/deep-copy-of-a-dict-in-python
    Convenience function.

    :param x: List to copy
    :return: Deep copy of the list provided by copy.deepcopy().
    """
    return copy.deepcopy(x)


_T = TypeVar('_T')


def add_lists(a: List[_T], b: List[_T]) -> List[_T]:
    """Helper method: join two lists together while type checking."""
    assert isinstance(a, List)
    assert isinstance(b, List)
    return a + b


def add_dicts(a: dict, b: dict) -> dict:
    """Helper method: join two dicts together while type checking.
    The second dictionary will override any entries in the first."""
    assert isinstance(a, dict)
    assert isinstance(b, dict)

    # Deepdicts are necessary since Python dictionaries are mutable, and dict() does a shallow copy.
    # Here, don't modify the original 'a'.
    newdict = deepdict(a)
    # When we updated newdict with b, e.g. if b['a'] was a (mutable) list with id 123, then newdict['a'] would point to
    # the same list as in id(newdict['a']) == 123.
    # Therefore, we need to deepdict b (or the result equivalently).
    newdict.update(deepdict(b))
    return newdict


def reverse_dict(x: dict) -> dict:
    """
    Reverse a dictionary (keys become values and vice-versa). Only works if the dictionary is isomorphic (no duplicate
    values), or some pairs will be lost.

    :param x: Dictionary to reverse
    :return: Reversed dictionary
    """
    return {value: key for key, value in x.items()}


def in_place_unique(items: List[Any]) -> None:
    """
    "Fast" in-place uniquification of a list.

    :param items: List to be uniquified.
    """
    seen = set()  # type: Set[Any]
    i = 0
    # We will be all done when i == len(items)
    while i < len(items):
        item = items[i]
        if item in seen:
            # Delete and keep index pointer the same.
            del items[i]
            continue
        else:
            seen.add(item)
            i += 1


def topological_sort(graph: Dict[str, Tuple[List[str], List[str]]], starting_nodes: List[str]) -> List[str]:
    """
    Perform a topological sort on the graph and return a valid ordering.

    :param graph: dict that represents key as the node and value as a tuple of (outgoing edges, incoming edges).
    :param starting_nodes: List of starting nodes to use.
    :return: A valid topological ordering of the graph.
    """

    # Make a copy of the graph since we'll be modifying it.
    working_graph = deepdict(graph)  # type: Dict[str, Tuple[List[str], List[str]]]

    queue = []  # type: List[str]
    output = []  # type: List[str]

    # Add starting nodes to the queue.
    queue.extend(starting_nodes)

    while len(queue) > 0:
        # Get front-most node in the queue.
        node = queue.pop(0)

        # It should have no incoming edges.
        assert len(working_graph[node][1]) == 0

        # Add it to the output.
        output.append(node)

        # Examine all targets of outgoing edges of this node.
        for target_node in working_graph[node][0]:
            # Remove the corresponding incoming edge there.
            working_graph[target_node][1].remove(node)

            # If the target node now has no incoming nodes, we can add it to the queue.
            if len(working_graph[target_node][1]) == 0:
                queue.append(target_node)

    return output


def reduce_named(function: Callable, sequence: Iterable, initial: Any = None) -> Any:
    """
    Version of functools.reduce with named arguments.
    See https://mail.python.org/pipermail/python-ideas/2014-October/029803.html
    """
    if initial is None:
        return reduce(function, sequence)
    else:
        return reduce(function, sequence, initial)


def get_or_else(optional: Optional[_T], default: _T) -> _T:
    """
    Get the value from the given Optional value or the default.
    :param optional: Optional value from which to extract a value.
    :param default: Default value if the given Optional is None.
    :return: Value from the Optional or the default.
    """
    if optional is None:
        return default
    else:
        return optional


_U = TypeVar('_U')


def optional_map(optional: Optional[_T], func: Callable[[_T], _U]) -> Optional[_U]:
    """
    If 'optional' is not None, then apply the given function to it. Otherwise, return None.
    :param optional: Optional value to map.
    :param func: Function to apply to optional value.
    :return: 'func' applied to optional, or None if 'optional' is None.
    """
    if optional is None:
        return None
    else:
        return func(optional)


def check_function_type(function: Callable, args: List[type], return_type: type) -> None:
    """
    Check that the given function obeys its function type signature.
    Raises TypeError if the function is of the incorrect type.
    :param function: Function to typecheck
    :param args: List of arguments to the function
    :param return_type: Return type
    """

    def msg(cause: str) -> str:
        if cause != "":
            cause_full = ": " + cause
        else:
            cause_full = cause
        return "Function {function} has an incorrect signature{cause_full}".format(function=str(function),
                                                                                   cause_full=cause_full)

    inspected = inspect.getfullargspec(function)
    annotations = inspected.annotations
    inspected_args = inspected.args
    if len(inspected_args) != len(args):
        raise TypeError(msg(
            "Too many arguments - got {got}, expected {expected}".format(got=len(inspected_args), expected=len(args))))
    else:
        for i, (inspected_var_name, expected) in list(enumerate(zip(inspected_args, args))):
            inspected = annotations[inspected_var_name]
            if inspected != expected:
                inspected_name = str(inspected.__name__)  # type: ignore
                expected_name = str(expected.__name__)  # type: ignore
                raise TypeError(msg(
                    "For argument {i}, got {got}, expected {expected}".format(i=i, got=inspected_name,
                                                                              expected=expected_name)))
    inspected_return = annotations['return']
    if inspected_return != return_type:
        inspected_return_name = str(inspected_return.__name__)  # type: ignore
        return_type_name = str(return_type.__name__)  # type: ignore
        raise TypeError(msg("Got return type {got}, expected {expected}".format(got=inspected_return_name,
                                                                                expected=return_type_name)))
