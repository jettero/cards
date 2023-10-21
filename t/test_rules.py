#!/usr/bin/env python
# coding: utf-8

import pytest
from cards import Hand, Card, Deck
import cards.rules

RULES_FUNCTIONS = (
    cards.rules.pairs,
    cards.rules.flushes,
    cards.rules.straights,
    cards.rules.full_houses,
    cards.rules.straight_flushes,
    cards.rules.royal_flushes,
)

@pytest.mark.parametrize("cr_f", RULES_FUNCTIONS)
def test_empty_hands(cr_f):
    assert len(cr_f()) == 0

@pytest.mark.parametrize("h", [Hand(), Hand(Card()), Hand(Card(), Card(3))])
@pytest.mark.parametrize("cr_f", RULES_FUNCTIONS)
def test_undersized_hands(h,cr_f):
    assert len(cr_f(h)) == 0
