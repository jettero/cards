#!/usr/bin/env python
# coding: utf-8

from cards import Hand, Deck
import cards.rules

def test_basics():
    d = Deck().shuffle()
    r = Hand(d.deal(5))  # should work with or without *()
    h = Hand(*(d.deal(2)), r)  # so try both

    assert len(r.cards) == 5
    assert len(h.cards) == 7
    assert len(r.my_cards) == 5
    assert len(h.my_cards) == 2
    assert len(r.shared_cards) == 0
    assert len(h.shared_cards) == 5
