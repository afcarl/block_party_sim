#!/usr/bin/env python

import numpy


efn = 'events.csv'
ofn = 'output.p'

evs = numpy.loadtxt(
    efn, delimiter=',', dtype=[
        ('t', 'i4'), ('c', 'S2'), ('l', 'i1'), ('v', 'i1')])

max_l = max(evs['l'])
inc_l = lambda l: l + 1 if l != max_l else 0
dec_l = lambda l: l - 1 if l != 0 else max_l

# heuristic 1: straight movement through tube by 1 mouse
# for 'right' movements: bb @ l - 1, id @ l, bb @ l + 1
# for 'left' movements: bb @ l + 1, id @ l, bb @ l + 1
moves = []
id_ev_inds = numpy.where(evs['c'] == 'id')[0]
for i in id_ev_inds:
    id_ev = evs[i]
    assert id_ev['c'] == 'id'
    ll = dec_l(id_ev['l'])
    rl = inc_l(id_ev['l'])
    # find last bb at l - 1 or l + 1
    last_bb = None
    for e in evs[:i][::-1]:
        if e['l'] in (ll, rl) and e['c'] == 'bb' and e['v'] == 0:
            last_bb = e
    # find next bb at l - 1 or l + 1
    next_bb = None
    for e in evs[i+1:]:
        if e['l'] in (ll, rl) and e['c'] == 'bb' and e['v'] == 0:
            next_bb = e
    if last_bb is None or next_bb is None:
        print("Failed to find nearest beam breaks %i: %s" % (i, id_ev))
        continue
    if (next_bb['l'] == ll and last_bb['l'] == rl):
        direction = 'right'
        nl = inc_l(rl)
        ol = dec_l(ll)
    elif (next_bb['l'] == rl and last_bb['l'] == ll):
        direction = 'left'
        nl = dec_l(ll)
        ol = inc_l(rl)
    else:
        print("Failed to determine direction %i: %s" % (i, id_ev))
        print("\t%s" % (last_bb, ))
        print("\t%s" % (next_bb, ))
        continue
    # at id_ev['t'] mouse id_ev['v'] moved direction
    print(
        "at %i mouse %i moved %s into %i from %i" %
        (id_ev['t'], id_ev['v'], direction, nl, ol))
    moves.append((id_ev['t'], id_ev['v'], id_ev['l'], direction, nl, ol))
