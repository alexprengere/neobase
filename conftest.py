#!/usr/bin/env python
# -*- coding: utf-8 -*-

import neobase
import pytest


@pytest.fixture
def base():
    return neobase.NeoBase()


@pytest.fixture
def past_base():
    return neobase.NeoBase(date='2012-01-01')
