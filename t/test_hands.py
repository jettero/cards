#!/usr/bin/env python
# coding: utf-8

import itertools
import pytest
from cards import Hand, Card, Deck
from cards.rules import Score, score_class


def generate_pairs_of_length(N=2):
    # this produces a randomly generated N-pair hand for each card in the
    # deck. So, exactly 52 hands that are one-pair hands.
    d = Deck()
    for c0 in list(d.shuffle().cards):
        h = Hand(d.pop(c0))
        for _ in range(N - 1):
            for c in d.cards:
                if c.rank == c0.rank:
                    h.add(d.pop(c))
                    break
        for c in d.cards:
            if len(h) >= 5:
                break
            if c.rank in (x.rank for x in h[N - 2 :]):
                continue
            h.add(d.pop(c))

        yield h
        for c in h.cards:
            d.push(c)


@pytest.mark.parametrize("h", generate_pairs_of_length(2))
def test_one_pair(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.ONE_PAIR


@pytest.mark.parametrize("h", generate_pairs_of_length(3))
def test_three_of_a_kind(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.THREE_KIND


@pytest.mark.parametrize("h", generate_pairs_of_length(4))
def test_four_of_a_kind(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.FOUR_KIND


def generate_two_pair():
    d = Deck().shuffle()
    for c0, c1 in itertools.combinations(d.cards, 2):
        if c0.rank == c1.rank:
            continue
        h = Hand(d.pop(c0), d.pop(c1))
        for x in (c0, c1):
            for c in d.cards:
                if c.rank == x.rank:
                    h.add(d.pop(c))
                    break
        for c in d.cards:
            if len(h) >= 5:
                break
            if c.rank != c0.rank and c.rank != c1.rank:
                h.add(d.pop(c))

        yield h
        for c in h.cards:
            d.push(c)


@pytest.mark.parametrize("h", generate_two_pair())
def test_two_pair(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.TWO_PAIR


def generate_full_house():
    d = Deck().shuffle()
    for c0, c1 in itertools.combinations(d.cards, 2):
        if c0.rank == c1.rank:
            continue
        h = Hand(d.pop(c0), d.pop(c1))
        for n, x in enumerate((c0, c1), start=1):
            for _ in range(n):
                for c in d.cards:
                    if c.rank == x.rank:
                        h.add(d.pop(c))
                        break

        yield h
        for c in h.cards:
            d.push(c)


@pytest.mark.parametrize("h", generate_full_house())
def test_full_house(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.FULL_HOUSE


def generate_straight_flush(straight=True, flush=True):
    max_start = Card.rank_values["T"] if straight else 10_000
    a_ok = Card.rank_values["A"]
    d = Deck()
    for c0 in list(d.shuffle().cards):
        if max_start < c0.rvalue < a_ok:
            continue
        h = Hand(d.pop(c0))
        while len(h) < 5:
            lv = h[-1].rvalue + 1
            for c in d.cards:
                if c0.suit == c.suit:
                    if not flush and len(h) == 1:
                        continue
                elif flush:
                    continue

                if lv == c.rvalue or (c0.rank == "A" and len(h) == 1 and c.rank == "2"):
                    if not straight and len(h) == 1:
                        continue
                elif straight:
                    continue

                h.add(d.pop(c))
                break

        yield h
        for c in h.cards:
            d.push(c)


@pytest.mark.parametrize("h", generate_straight_flush(flush=False))
def test_straight(h):
    assert len(h.nuts()) == len(h)
    assert score_class(h.value) == Score.STRAIGHT


def test_generators():
    assert len(list(generate_pairs_of_length(2))) == 52
    assert len(list(generate_pairs_of_length(3))) == 52
    assert len(list(generate_pairs_of_length(4))) == 52
    # Why 52? We pick each card once, the pair/tripple/quad and then fill the
    # hands with spam.

    assert len(list(generate_two_pair())) == 1326-78
    assert len(list(generate_full_house())) == 1248
    # Why 1248? C(52,2) is 1326 combinations, but we're only using the ones
    # where the two chosen cards are different. Turns out, there's 78
    # combinations where the two cards are the same.

    assert len(list(generate_straight_flush(straight=False, flush=True))) == 52
    # same as above, we pick a card and then spam fill with matching suit

    assert len(list(generate_straight_flush(straight=True, flush=False))) == len("A23456789T")*4
    assert len(list(generate_straight_flush(straight=True, flush=True))) == 40
    # Why 40? We generate the straights by picking a card and then choosing
    # cards that are strictly in order (minus the A low thing). That means we
    # can't start with any card higher than a T ... len(A23456789T)=10 * 4-suits => 40
