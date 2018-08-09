# -*- coding: utf-8 -*-
#
# Copyright 2018 Data61, CSIRO
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from stellar.data.stellargraph import *
from stellar.data.converter import *

import networkx as nx
import random
import numpy as np
import itertools as it
import pytest


def test_converter_categorical():
    data = [1, 5, 5, 1, 6]
    conv = CategoricalConverter()
    converted_data = conv.fit_transform(data)

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 1
    assert all(converted_data == [0, 1, 1, 0, 2])


def test_converter_categorical_mixed():
    data = [1, "a", "a", 1, "b", 2]
    conv = CategoricalConverter()
    converted_data = conv.fit_transform(data)

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 1
    assert all(converted_data == [0, 2, 2, 0, 3, 1])


def test_converter_categorical_1hot():
    data = [1, 5, 5, 1, 6]
    conv = OneHotCategoricalConverter(flatten_binary=False)
    converted_data = conv.fit_transform(data)

    expected = np.array([[1, 0, 0], [0, 1, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]])

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 3
    assert converted_data == pytest.approx(expected)

    conv = OneHotCategoricalConverter(flatten_binary=True)
    converted_data = conv.fit_transform(data)

    assert len(conv) == 3
    assert converted_data == pytest.approx(expected)


def test_converter_binary():
    data = [1, "a", None, 0, "false"]
    conv = BinaryConverter()
    converted_data = conv.fit_transform(data)

    expected = np.array([1, 1, 0, 0, 1])

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 1
    assert converted_data == pytest.approx(expected)


def test_converter_categorical_1hot_binary():
    data = [1, 5, 5, 1, 5]
    conv = OneHotCategoricalConverter(flatten_binary=False)
    converted_data = conv.fit_transform(data)

    expected = np.array([[1, 0], [0, 1], [0, 1], [1, 0], [0, 1]])

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 2
    assert np.all(converted_data == expected)

    conv = OneHotCategoricalConverter(flatten_binary=True)
    converted_data = conv.fit_transform(data)

    assert len(conv) == 1
    assert converted_data == pytest.approx([0, 1, 1, 0, 1])


def test_converter_numeric():
    data = np.array([2, 5, 5, 3, 5])
    conv = NumericConverter(normalize=False)
    converted_data = conv.fit_transform(data)

    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 1
    assert converted_data == pytest.approx(data)

    conv = NumericConverter(normalize="standard")
    converted_data = conv.fit_transform(data)
    expected = (np.array(data) - 4) / 1.26491
    assert isinstance(conv, StellarAttributeConverter)
    assert len(conv) == 1
    assert converted_data == pytest.approx(expected, rel=1e-3)


def test_attribute_spec():
    nfs = NodeAttributeSpecification()
    nfs.add_attribute_type("", "a1", NumericConverter, default_value=0, normalize=False)
    nfs.add_attribute_type("", "a2", NumericConverter, default_value=0, normalize=False)

    data = [{"a1": 1, "a2": 1}, {"a2": 1}, {"a1": 1}, {}]

    attr_list = nfs.get_attributes("")
    assert attr_list == ["a1", "a2"]

    converted_data = nfs.fit_transform("", data)
    expected = [[1, 1], [0, 1], [1, 0], [0, 0]]

    assert converted_data == pytest.approx(expected)


def test_attribute_spec_normalize_error():
    nfs = NodeAttributeSpecification()
    nfs.add_attribute_type("", "a1", NumericConverter, default_value=0)
    nfs.add_attribute_type("", "a2", NumericConverter, default_value=0)

    data = [{"a1": 1, "a2": 1}, {"a2": 1}, {"a1": 1}, {}]

    # We expect an error here as the normalization works before values have been
    # imputed with the default value, therefore the std dev will be zero.
    with pytest.raises(ValueError):
        nfs.fit_transform("", data)

    nfs = NodeAttributeSpecification()
    nfs.add_attribute_type("", "a", NumericConverter, default_value=0)

    data = [{"a": 1}, {"a": 1}, {"a": 1}, {"a": 1}]
    with pytest.raises(ValueError):
        nfs.fit_transform("", data)


def test_attribute_spec_binary_conv():
    nfs = NodeAttributeSpecification()
    nfs.add_attribute_type("", "a1", BinaryConverter)
    nfs.add_attribute_type("", "a2", BinaryConverter)

    data = [{"a1": 1, "a2": 1}, {"a2": 1}, {"a1": 1}, {}]
    converted_data = nfs.fit_transform("", data)
    expected = [[1, 1], [0, 1], [1, 0], [0, 0]]
    assert converted_data == pytest.approx(expected)


def test_attribute_spec_mixed():
    nfs = NodeAttributeSpecification()
    nfs.add_attribute_type("", "a1", OneHotCategoricalConverter)
    nfs.add_attribute_type("", "a2", NumericConverter, default_value="mean")

    data = [{"a1": 1, "a2": 0}, {"a1": "a", "a2": 1}, {"a1": 1}, {"a1": "a"}]

    converted_data = nfs.fit_transform("", data)
    expected = [[1, 0, -1], [0, 1, 1], [1, 0, 0], [0, 1, 0]]

    assert converted_data == pytest.approx(expected)
