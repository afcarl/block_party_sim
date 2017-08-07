#!/usr/bin/env python

import math
import cPickle as pickle
import random

#import networkx
#import pylab
import pygame


n_cages = 3
n_mice = n_cages * 5
move_only_one = False  # move at most only 1 mouse per loop
delay_ms = 100

max_occupancy = {
    'cage': n_mice + 1,
    'beam_break': 1,
    'rfid_reader': 1,
}

prob = {
    'move': {
        'cage': 0.01,
        'beam_break': 0.9,
        'rfid_reader': 0.9,
    },
    'turn': {
        'cage': 0.5,
        'beam_break': 0.1,
        'rfid_reader': 0.1,
    },
}


class Mouse(object):
    index = {}

    def __init__(self):
        self.mid = len(Mouse.index)
        self.direction = ['left', 'right'][random.randint(0, 1)]
        Mouse.index[self.mid] = self

    def __repr__(self):
        return (
            "Mouse[%s]: %s" % (self.mid, self.direction))

    @classmethod
    def by_mid(cls, mid):
        return cls.index[mid]


class Location(object):
    index = {}

    def __init__(self, ltype):
        self.lid = len(Location.index)
        self.ltype = ltype
        self.mice = {}
        Location.index[self.lid] = self

    def __repr__(self):
        return (
            "Location[%i]: %s[%i mice]" %
            (self.lid, self.ltype, len(self.mice)))

    def right(self):
        return 0 if self.lid + 1 == len(Location.index) else self.lid + 1

    def left(self):
        return self.lid - 1 if self.lid != 0 else len(Location.index) - 1

    @classmethod
    def by_lid(cls, lid):
        return cls.index[lid]

    @classmethod
    def lid_by_mid(cls, mid):
        for lid in cls.index:
            if mid in cls.index[lid].mice:
                return lid

    @property
    def occupied(self):
        return len(self.mice) >= max_occupancy[self.ltype]


# build locations
for i in xrange(n_cages):
    Location('cage')
    Location('beam_break')
    Location('rfid_reader')
    Location('beam_break')

# put mice in cages, assign random directions
for i in xrange(n_mice):
    m = Mouse()
    o = True
    while o:
        lid = random.randint(0, len(Location.index) - 1)
        l = Location.by_lid(lid)
        o = l.ltype != 'cage' or l.occupied
    Location.by_lid(lid).mice[m.mid] = m

## make graph of locations
#lg = networkx.Graph()
#for lid in Location.index:
#    if lid == len(Location.index) - 1:
#        lg.add_edge(lid, 0)
#    else:
#        lg.add_edge(lid, lid+1)
#    lg.node[lid] = Location.by_lid(lid)

## display
#networkx.draw_circular(lg)
#pylab.show()

ms = 30  # mouse 'size'
cw = int(math.ceil(math.sqrt(n_mice)) * ms)  # cage width
ch = cw  # cage height

header_h = 20

sw = cw * n_cages + 3 * ms * n_cages
sh = ch + header_h
pygame.init()

screen = pygame.display.set_mode((sw, sh))
font = pygame.font.SysFont(None, 20)

data = []
t_ms = 0
keep_looping = True
ev_to_s = lambda t_ms, ev: str(t_ms) + ",%s,%i,%i" % ev
while keep_looping:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            keep_looping = False
            continue
    # move mice
    changed = False
    mids = Mouse.index.keys()
    random.shuffle(mids)
    evs = []
    for mid in mids:
        m = Mouse.by_mid(mid)
        lid = Location.lid_by_mid(mid)
        l = Location.by_lid(lid)
        if random.random() > prob['move'][l.ltype]:  # move?
            continue
        if random.random() < prob['turn'][l.ltype]:  # turn?
            m.direction = 'left' if m.direction == 'right' else 'right'
        n = Location.by_lid(getattr(l, m.direction)())
        if not n.occupied:  # occupied?
            changed = True
            # move mouse to this location
            n.mice[mid] = m
            if l.ltype == 'beam_break':
                # report end of beam break
                evs.append(('bb', l.lid, 0))
                print(ev_to_s(t_ms, evs[-1]))
            if n.ltype == 'beam_break':
                # report beam break
                evs.append(('bb', n.lid, 1))
                print(ev_to_s(t_ms, evs[-1]))
            elif n.ltype == 'rfid_reader':
                # report rfid
                evs.append(('id', n.lid, mid))
                print(ev_to_s(t_ms, evs[-1]))
            del l.mice[mid]
        if changed and move_only_one:
            continue

    if changed:
        # report new occupancy [lid] = mids
        o = {}
        for lid in Location.index:
            o[lid] = Location.index[lid].mice.keys()
        data.append({'t': t_ms, 'o': o, 'evs': evs})

    # draw mice
    screen.fill((0, 0, 0))
    x = 0
    for lid in sorted(Location.index):
        l = Location.by_lid(lid)
        sx, sy = 0, 0
        tx = x + cw // 2 if l.ltype == 'cage' else x + ms // 2
        ty = header_h // 2
        text = font.render('%s%02i' % (l.ltype[0], lid), True, (255, 255, 255))
        tx -= text.get_width() // 2
        ty -= text.get_height() // 2
        screen.blit(text, (tx, ty))
        if l.ltype == 'cage':
            pygame.draw.line(
                screen, (255, 255, 255),
                (x, 0), (x, sh))
            pygame.draw.line(
                screen, (255, 255, 255),
                (x + cw, 0), (x + cw, sh))
        for mid in l.mice:
            m = l.mice[mid]
            c = (0, 0, 255) if m.direction == 'left' else (255, 0, 0)
            if mid == 0:
                c = (0, 255, 0)
            pygame.draw.rect(
                screen, c,
                (x + sx, header_h + sy, ms, ms))
            text = font.render('%02i' % mid, True, (255, 255, 255))
            tx = x + sx + ms // 2 - text.get_width() // 2
            ty = header_h + sy + ms // 2 - text.get_height() // 2
            screen.blit(text, (tx, ty))
            sx += ms
            if sx >= cw:
                sx = 0
                sy += ms
        if l.ltype == 'cage':
            x += cw
        else:
            x += ms

    pygame.display.update()
    pygame.time.delay(delay_ms)  # ms
    t_ms += delay_ms

# save data
with open('output.p', 'w') as f:
    pickle.dump(data, f)

with open('events.csv', 'w') as f:
    for d in data:
        for e in d['evs']:
            f.write(ev_to_s(d['t'], e) + '\n')
