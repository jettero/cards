#!/usr/bin/env python
# coding: utf-8


class Comparable:
    value = 0

    def __lt__(self, other):
        try:
            return self.value < other.value
        except AttributeError:
            pass
        return self.value < other

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            pass
        return self.value == other

    def __hash__(self):
        return hash(self.value)

class Indexable:
    def __len__(self):
        return len(self.cards)

    def __getitem__(self, idx):
        return self.cards[idx]
