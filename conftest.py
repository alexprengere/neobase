#!/usr/bin/env python
# -*- coding: utf-8 -*-

import neobase
import pytest

@pytest.fixture
def base():
    return neobase.NeoBase()
