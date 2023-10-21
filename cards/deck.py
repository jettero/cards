#!/usr/bin/env python
# coding: utf-8

"""
Poker Generics

Texas Holdem is the very first aim of the lib, but Card and Deck are meant to
be generics for everything from Poker through Tarot and all the way to
Roguelike RPG game decks (eventually).
"""

import itertools
import inspect
import random
from .overloads import Comparable, Indexable
import cards.rules

CLUB = "♣"
DIAMOND = "♦"
HEART = "♥"
SPADE = "♠"


class Card(Comparable):
    """
    Until we support a few types of decks, the generic Card is most certainly a
    Poker card.  Specifically, your wiki search should be "standard 52-card
    deck of French-suited playing cards." Though, we also assign values based
    loosely on Poker rules.
    """

    suits = "♣♦♥♠"
    ranks = "23456789TJQKA"
    color_map = {"♣": "38;5;242", "♦": "31", "♥": "31", "♠": "38;5;242"}

    suit_values = {"♣": 0.1, "♦": 0.2, "♥": 0.3, "♠": 0.4}
    rank_values = {x: y for x, y in zip("23456789TJQKA", range(2, 25))}

    xlate = {x: y for x, y in zip("CDHS", suits)}

    def __init__(self, rank='2', suit=HEART):
        if isinstance(rank, int):
            rank = str(rank)
        if len(rank) == 2:
            rank,suit = rank
        if rank not in self.ranks:
            raise ValueError(f'rank={rank} not in ranks={self.ranks}')

        suit = suit.upper().replace(" ", "")

        if suit not in self.suits and suit in self.xlate:
            suit = self.xlate[suit]

        self.rank = rank
        self.suit = suit
        self.rvalue = self.rank_values[rank]
        self.svalue = self.suit_values[suit]
        self.value = self.rvalue + self.svalue

    def __repr__(self):
        return f"C({str(self)})"

    def __str__(self):
        t = f"{self.rank}{self.suit}"
        if self.suit in self.color_map:
            return f"\x1b[{self.color_map[self.suit]}m{t}\x1b[m"
        return t


class Deck(Indexable):
    """
    Until we support a few types of decks, the generic Deck is most certainly a Poker deck.
    """

    def __init__(self, ccls=Card):
        self.suits = ccls.suits
        self.ranks = ccls.ranks

        # for s for r gives us the typical all-clubs, all-diamonds, ... ordering of a new deck
        # for r for s gives all 2s, all 3s, all 4s...
        self._cards = tuple(Card(r, s) for r, s in [(r, s) for s in self.suits for r in self.ranks])

    @property
    def cards(self):
        try:
            return self._current
        except AttributeError:
            pass
        self._current = list(self._cards)
        return self._current

    def shuffle(self):
        self._current = list(self._cards)
        random.shuffle(self._current)
        return self

    def __repr__(self):
        return f"D({str(self)})"

    def __str__(self):
        return " ".join([str(x) for x in self.cards])

    def deal(self, n=1):
        return tuple(self.cards.pop() for _ in range(n))

    def pop(self, card):
        if not isinstance(card, Card):
            raise TypeError(f'{card!r} is not a Card')
        try:
            return self.cards.pop( self.cards.index(card) )
        except ValueError:
            pass
        raise Exception(f'{card!r} not in deck')

    def push(self, card):
        if not isinstance(card, Card):
            raise TypeError(f'{card!r} is not a Card')
        if card in self.cards:
            raise ValueError(f'{card!r} is already in deck')
        self.cards.append(card)

    def __getitem__(self, idx):
        return self.cards[idx]


class Hand(Comparable, Indexable):
    """
    Until we support a few types of hands, the generic Hand is a 5-card Poker hand -- with optional shared cards.
    """

    def __init__(self, *cards):
        self._my_cards = list()

        # The idea is that updating the shared hand updates all the hands that
        # share it... so shared cards should be hands. Does this even make
        # sense outside of poker?
        self._shared_hands = list()

        self.add(*cards)

    @property
    def value(self):
        return cards.rules.nuts(*self.cards)[0]

    @property
    def vclass(self):
        return cards.rules.score_class(self.value)

    @property
    def vname(self):
        return Score.name(self.value)

    def nuts(self):
        return Hand(*(cards.rules.nuts(*self.cards)[1]))

    @classmethod
    def mkhand(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"expecting string of card vals (e.g. 2D3C4H), received: {v!r}")

        v = v.upper().replace(" ", "")

        if len(v) % 2 != 0:
            raise ValueError(f"expecting string of card vals (e.g. 2D3C4H), received: {v!r}")
        return cls(Card(v[i], v[i + 1]) for i in range(0, len(v), 2))

    @classmethod
    def copy(cls, v):
        return cls(*self._my_cards, *self._shared_hands)

    def add(self, *things):
        for x in things:
            if isinstance(x, Card):
                self._my_cards.append(x)
            elif isinstance(x, Hand):
                self._shared_hands.append(x)
            elif isinstance(x, (list, tuple)):
                self.add(*x)
            elif inspect.isgenerator(x):
                for y in x:
                    self.add(y)
            elif isinstance(x, str) and len(x) == 2:
                self.add(Card(*x))
            else:
                raise ValueError(f"ERROR: argument {x!r} isn't of type Card, Hand, list, or tuple")

    @property
    def my_cards(self):
        return self._my_cards

    @property
    def shared_cards(self):
        ret = list()
        for item in self._shared_hands:
            ret.extend(item.cards)
        return ret

    @property
    def cards(self):
        return self.my_cards + self.shared_cards

    def __repr__(self):
        return f"H({str(self)})"

    def __str__(self):
        my_cards = " ".join(str(x) for x in self.my_cards)
        if sc := self.shared_cards:
            shared_cards = " ".join(str(x) for x in sc)
            return f"{my_cards} [{shared_cards}]"
        return my_cards
