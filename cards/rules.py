#!/usr/bin/env python
# coding: utf-8

from functools import lru_cache
from itertools import combinations
from inspect import isgenerator

memoize = lru_cache(maxsize=10)

HAND_LEN = 5
SUITS = 4
RANKS = 13
WRAP_FINAL_RANK = True # if 2=2 and K=13, Aces can be 1 or 14 in a straight when wrapping is turned on

class Score:
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

    @classmethod
    def name(cls, sv):
        sc = score_class(sv)
        for item in dir(cls):
            if 'A' <= item[0] <= 'Z': # I'm honestly surprised this works
                try:
                    if sc == getattr(cls,item):
                        return item.lower().replace('_', ' ')
                except ValueError:
                    pass
        return f'Nothing(value={sv})'

@memoize
def join_score(hc, hp1, hp2, hp3):
    return hc*1_00_00_00 + hp1*1_00_00 + hp2*1_00 + hp3#*1

@memoize
def score_class(v):
    if v < 1_00_00_00:
        return int(v)
    return int( v / 1_00_00_00 )

# All the hand detectors should return best first so nuts can assume res[0] is the best one

@memoize
def _flatten(*cards, key=None):
    def _inner(*cards):
        for item in cards:
            if isinstance(item, (list,tuple)) or isgenerator(item):
                yield from item
            elif hasattr(item, "cards"):
                yield from item.cards
            else:
                yield item
    if callable(key):
        return list(sorted(_inner(*cards), key=key))
    if key == '-':
        return list(reversed(sorted(_inner(*cards))))
    return list(sorted(_inner(*cards)))

@memoize
def _consec(*cards, wrap_final_rank=WRAP_FINAL_RANK):
    cards = _flatten(*cards)
    for i,j in zip(range(0,len(cards)-1), range(1,len(cards))):
        if cards[i].rvalue +1 != cards[j].rvalue:
            if (wrap_final_rank and cards[j] is cards[-1]
                and cards[j].rank == cards[j].ranks[-1]
                and cards[0].rank == cards[0].ranks[0]):
                    return True
            return False
    return True

@memoize
def flushes(*cards, hand_len=HAND_LEN):
    if len(cards) < hand_len:
        return list()
    count = dict()
    for item in _flatten(*cards, key='-'):
        if item.suit not in count:
            count[item.suit] = [item]
        else:
            count[item.suit].append(item)
    return list( sorted(c) for v in count.values() for c in combinations(v, hand_len) )

@memoize
def _straight_sort(*cards, wrap_final_rank=WRAP_FINAL_RANK):
    s = tuple(sorted(cards))
    if wrap_final_rank:
        if s[0].rank == s[0].ranks[0] and s[-1].rank == s[-1].ranks[-1]:
            return (s[-1], *s[0:-1])
    return s

@memoize
def straights(*cards, hand_len=HAND_LEN, wrap_final_rank=WRAP_FINAL_RANK):
    # XXX: can an A be low in a straight? am I making this up? and if it's low
    # in the straight, is it a 5 high straight? pretty sure that's right
    return list(sorted([ _straight_sort(*C, wrap_final_rank=wrap_final_rank)
        for C in combinations(_flatten(*cards), hand_len)
            if _consec(*C, wrap_final_rank=wrap_final_rank) ], key=lambda x: -x[-1].value))

@memoize
def pairs(*cards, min_c=2, max_c=SUITS):
    if len(cards) < min_c:
        return {}
    d = { c.rvalue:tuple(sorted(x for x in cards if x.rank == c.rank)) for c in cards }
    ret = dict()
    for _,c in reversed(sorted(d.items())):
        if (N := len(c)) >= min_c and N <=max_c:
            if N in ret:
                ret[N].append(c)
            else:
                ret[N] = [c]
    return { x:list(sorted(y, key=lambda x: -x[-1].value)) for x,y in ret.items() }

@memoize
def full_houses(*cards, lsz=3, ssz=2):
    p = pairs(*cards, min_c=ssz, max_c=lsz)
    return list(sorted((a+b for a in p.get(lsz, []) for b in p.get(ssz, [])), key=lambda x: 100*x[0].rvalue + x[-1].rvalue))

@memoize
def straight_flushes(*cards, hand_len=HAND_LEN, wrap_final_rank=WRAP_FINAL_RANK):
    g = (_straight_sort(*f, wrap_final_rank=wrap_final_rank) for f in flushes(*cards, hand_len=hand_len)
            if straights(*f, hand_len=hand_len, wrap_final_rank=wrap_final_rank))
    return list(sorted(g, key=lambda x: -x[-1].value ))

@memoize
def royal_flushes(*cards, hand_len=HAND_LEN, wrap_final_rank=WRAP_FINAL_RANK):
    g = ( x for x in straight_flushes(*cards, hand_len=hand_len, wrap_final_rank=wrap_final_rank)
            if x[-1].rank == x[-1].ranks[-1] )
    return list(sorted(g, key=lambda x: -x[-1].value ))

@memoize
def nuts(*cards, hand_len=HAND_LEN, wrap_final_rank=WRAP_FINAL_RANK, min_c=2, max_c=SUITS):
    cards = _flatten(*cards, key='-')

    if len(cards) < 1:
        return 0,list()

    def _reup_hand(pick):
        ret = list(pick)
        for item in cards:
            if len(ret) >= hand_len:
                return ret
            if item not in ret:
                ret.append(item)
        return ret

    if res := royal_flushes(*cards, hand_len=hand_len, wrap_final_rank=wrap_final_rank):
        res = res[0]
        score = join_score(Score.ROYAL_FLUSH, res[-1].value, 0, 0)
        return score, res

    if res := straight_flushes(*cards, hand_len=hand_len, wrap_final_rank=wrap_final_rank):
        res = res[0]
        score = join_score(Score.STRAIGHT_FLUSH, res[-1].value, 0, 0)
        return score, res

    p = pairs(*cards, min_c=min_c, max_c=max_c)
    if p and 4 in p:
        res = p[4][0]
        score = join_score(Score.FOUR_KIND, res[-1].value, 0, 0)
        return score, _reup_hand(res)

    if res := full_houses(*cards, lsz=3, ssz=2):
        res = res[0]
        score = join_score(Score.FULL_HOUSE, res[2].value, res[4].value, 0) # AAA22 or 222AA
        return score, _reup_hand(res)

    if res := flushes(*cards, hand_len=hand_len):
        res = res[0]
        score = join_score(Score.FLUSH, res[-1].value, 0, 0)
        return score, res

    if res := straights(*cards, hand_len=hand_len, wrap_final_rank=wrap_final_rank):
        res = res[0]
        score = join_score(Score.STRAIGHT, res[-1].value, 0, 0)
        return score, res

    if p and 3 in p:
        res = _reup_hand(p[3][0])
        score = join_score(Score.THREE_KIND, res[2].value, res[3].value, 0)
        return score, _reup_hand(res)

    if p and 2 in p and len(p[2])>1:
        res = _reup_hand(p[2][0] + p[2][1])
        score = join_score(Score.TWO_PAIR, res[1].value, res[3].value, res[4].value)
        return score, _reup_hand(res)

    if p and 2 in p:
        res = _reup_hand(p[2][0])
        score = join_score(Score.ONE_PAIR, res[1].value, res[2].value, 0)
        return score, _reup_hand(res)

    return cards[0].value, cards[:hand_len]
