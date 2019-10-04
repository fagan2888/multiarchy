"""Author: Brandon Trabucco, Copyright 2019, MIT License"""


import numpy as np
import tensorflow as tf


def nested_apply(
    function,
    *structures
):
    # apply a function to a nested structure of objects
    if (isinstance(structures[0], np.ndarray) or
            isinstance(structures[0], tf.Tensor) or not (
            isinstance(structures[0], list) or
            isinstance(structures[0], tuple) or
            isinstance(structures[0], set) or
            isinstance(structures[0], dict))):
        return function(*structures)

    elif isinstance(structures[0], list):
        return [
            nested_apply(
                function,
                *x,) for x in zip(*structures)]

    elif isinstance(structures[0], tuple):
        return tuple(
            nested_apply(
                function,
                *x,) for x in zip(*structures))

    elif isinstance(structures[0], set):
        return {
            nested_apply(
                function,
                *x,) for x in zip(*structures)}

    elif isinstance(structures[0], dict):
        keys_list = structures[0].keys()
        values_list = [[y[key] for key in keys_list] for y in structures]
        return {
            key: nested_apply(
                function,
                *values) for key, values in zip(keys_list, zip(*values_list))}


def discounted_sum(
    terms,
    discount_factor
):
    # compute discounted sum of rewards across terms using discount_factor
    weights = tf.tile([[discount_factor]], [1, tf.shape(terms)[1]])
    weights = tf.math.cumprod(weights, axis=1, exclusive=True)
    return tf.math.cumsum(
        terms * weights, axis=1, reverse=True) / weights


def flatten(
        structures
):
    # flatten a nested structure of tensors to a list
    if (isinstance(structures, np.ndarray) or
            isinstance(structures, tf.Tensor) or not (
            isinstance(structures, list) or
            isinstance(structures, tuple) or
            isinstance(structures, set) or
            isinstance(structures, dict))):
        return [structures]

    elif (isinstance(structures, list) or isinstance(structures, tuple) or
          isinstance(structures, set)):
        output = []
        for s in structures:
            output.extend(flatten(s))
        return output

    elif isinstance(structures, dict):
        output = []
        for s in structures.values():
            output.extend(flatten(s))
        return output
