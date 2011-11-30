#!/usr/bin/env python
import sys
import traceback
import random
import time
from collections import defaultdict
from math import sqrt
import numpy as np

MY_ANT = 0
ANTS = 0
DEAD = -1
LAND = -2
FOOD = -3
WATER = -4
UNSEEN = -5

AIM = {'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}
RIGHT = {'n': 'e',
         'e': 's',
         's': 'w',
         'w': 'n'}
LEFT = {'n': 'w',
        'e': 'n',
        's': 'e',
        'w': 's'}
BEHIND = {'n': 's',
          's': 'n',
          'e': 'w',
          'w': 'e'}

def debug(*msgs):
    text = ' '.join(str(m) for m in msgs) + '\n'
    sys.stderr.write(text)
    sys.stderr.flush()


class Ants():
    def __init__(self):
        self.cols = None
        self.rows = None
        self.map = None
        self.hill_list = {}
        self.ant_list = {}
        self.dead_list = defaultdict(list)
        self.food_list = []
        self.visible_food_list = []
        self.turntime = 0
        self.loadtime = 0
        self.turn_start_time = None
        self.visible = None
        self.viewradius2 = 0
        self.attackradius2 = 0
        self.spawnradius2 = 0
        self.turns = 0
        self.turn = -1

    def setup(self, data):
        """Parse initial input and setup starting game state"""
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                key = tokens[0]
                if key == 'cols':
                    self.cols = int(tokens[1])
                elif key == 'rows':
                    self.rows = int(tokens[1])
                elif key == 'player_seed':
                    random.seed(int(tokens[1]))
                elif key == 'turntime':
                    self.turntime = int(tokens[1])
                elif key == 'loadtime':
                    self.loadtime = int(tokens[1])
                elif key == 'viewradius2':
                    self.viewradius2 = int(tokens[1])
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])
                elif key == 'turns':
                    self.turns = int(tokens[1])
        self.map = np.ndarray((self.rows, self.cols), dtype=np.int8)
        self.map.fill(UNSEEN)
        self.visible = np.zeros((self.rows, self.cols), dtype = np.bool)
        self._vision_setup()

    def update(self, data):
        """Parse engine input and update the game state"""
        # start timer
        self.turn_start_time = time.clock()
        
        # clear hill, ant and food data
        self.hill_list = {}
        for row, col in self.ant_list.keys():
            self.map[row,col] = LAND
        self.ant_list = {}
        for row, col in self.dead_list.keys():
            self.map[row,col] = LAND
        self.dead_list = defaultdict(list)
        self.visible_food_list = []
        visible_hill_list = {}
        
        # update map and create new ant and food lists
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                if len(tokens) == 2:
                    if tokens[0] == 'turn':
                        self.turn = int(tokens[1])
                elif len(tokens) >= 3:
                    row = int(tokens[1])
                    col = int(tokens[2])
                    if tokens[0] == 'w':
                        self.map[row,col] = WATER
                    elif tokens[0] == 'f':
                        self.map[row,col] = FOOD
                        self.visible_food_list.append((row, col))
                    else:
                        owner = int(tokens[3])
                        if tokens[0] == 'a':
                            self.map[row,col] = owner
                            self.ant_list[(row, col)] = owner
                        elif tokens[0] == 'd':
                            # food could spawn on a spot where an ant just died
                            # don't overwrite the space unless it is land
                            #if self.map[row][col] == LAND:
                            #    self.map[row][col] = DEAD
                            # but always add to the dead list
                            self.dead_list[(row, col)].append(owner)
                        elif tokens[0] == 'h':
                            owner = int(tokens[3])
                            visible_hill_list[(row, col)] = owner
        self._update_visible()

        # Update food
        new_food = []
        for pos in self.food_list:
            if self.visible[pos]:
                self.map[pos] = LAND
            else:
                # Assume still there
                new_food.append(pos)
        for pos in self.visible_food_list:
            self.map[pos] = FOOD
        self.food_list = new_food + self.visible_food_list

        # Update hills
        for pos, owner in self.hill_list.items():
            if self.visible[pos] and pos not in visible_hill_list:
                del self.hill_list[pos]
        self.hill_list.update(visible_hill_list)

    def time_remaining(self):
        return self.turntime - int(1000 * (time.clock() - self.turn_start_time))
    
    def issue_order(self, ant_loc, dir_or_dest = None):
        """Issue an order by either (ant_loc, dir) or (ant_loc, dest) pair"""
        if dir_or_dest is None:
            # Compatibility with old pack
            ant_loc, dir_or_dest = ant_loc
        if isinstance(dir_or_dest, str):
            direction = dir_or_dest
        elif len(dir_or_dest) == 2:
            direction = self.direction(ant_loc, dir_or_dest)[0]
        else:
            raise ValueError("Invalid order " + str((ant_loc, dir_or_dest)))
        sys.stdout.write('o %s %s %s\n' % (ant_loc[0], ant_loc[1], direction))
        sys.stdout.flush()
        
    def finish_turn(self):
        """Finish the turn by writing the go line"""
        sys.stdout.write('go\n')
        sys.stdout.flush()
    
    def my_hills(self):
        return [loc for loc, owner in self.hill_list.items()
                    if owner == MY_ANT]

    def enemy_hills(self):
        return [(loc, owner) for loc, owner in self.hill_list.items()
                    if owner != MY_ANT]
        
    def my_ants(self):
        """return a list of all my ants"""
        return [(row, col) for (row, col), owner in self.ant_list.items()
                    if owner == MY_ANT]

    def enemy_ants(self):
        """return a list of all visible enemy ants"""
        return [((row, col), owner)
                    for (row, col), owner in self.ant_list.items()
                    if owner != MY_ANT]

    def food(self):
        """Return a list of all known food locations (visible or not)"""
        return self.food_list[:]

    def passable(self, loc):
        """True if seen and not water"""
        row, col = loc
        return self.map[row,col] not in (WATER, UNSEEN)
    
    def unoccupied(self, loc):
        """True if no ants are at the location"""
        row, col = loc
        return self.map[row,col] in (LAND, DEAD)

    def neighbours(self, pos):
        """Returns the four neighbours of a position"""
        return [((pos[0]-1)%self.rows, pos[1]),
                (pos[0], (pos[1]+1)%self.cols),
                ((pos[0]+1)%self.rows, pos[1]),
                (pos[0], (pos[1]-1)%self.cols)]

    def neighbours_and_dirs(self, pos):
        """Returns four position, direction pairs"""
        return ((((pos[0]-1)%self.rows, pos[1]), 'n'),
                ((pos[0], (pos[1]+1)%self.cols), 'e'),
                (((pos[0]+1)%self.rows, pos[1]), 's'),
                ((pos[0], (pos[1]-1)%self.cols), 'w'))

    def destination(self, loc, direction):
        """Calculate a new location given the direction and wrap correctly"""
        row, col = loc
        d_row, d_col = AIM[direction]
        return (row + d_row) % self.rows, (col + d_col) % self.cols

    def distance(self, loc1, loc2):
        """Calculate the closest distance between two locations"""
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row + d_col

    def direction(self, loc1, loc2):
        """Return a list of the 1 or 2 fastest (closest) directions to reach a location"""
        row1, col1 = loc1
        row2, col2 = loc2
        height2 = self.rows//2
        width2 = self.cols//2
        d = []
        if row1 < row2:
            if row2 - row1 >= height2:
                d.append('n')
            if row2 - row1 <= height2:
                d.append('s')
        if row2 < row1:
            if row1 - row2 >= height2:
                d.append('s')
            if row1 - row2 <= height2:
                d.append('n')
        if col1 < col2:
            if col2 - col1 >= width2:
                d.append('w')
            if col2 - col1 <= width2:
                d.append('e')
        if col2 < col1:
            if col1 - col2 >= width2:
                d.append('e')
            if col1 - col2 <= width2:
                d.append('w')
        return d

    def _vision_setup(self):
        # Precalculate a circular mask used in _update_visible
        viewradius = int(sqrt(self.viewradius2))
        diameter = viewradius * 2 + 1
        self.vision_disc = np.zeros((diameter, diameter), dtype = np.bool)
        for y, x in np.ndindex(*self.vision_disc.shape):
            if (viewradius - y)**2 + (viewradius - x)**2 <= self.viewradius2:
                self.vision_disc[y, x] = True

    def _update_visible(self):
        self.visible.fill(False)
        viewradius = int(sqrt(self.viewradius2))
        diameter = viewradius * 2 + 1

        for a_row, a_col in self.my_ants():
            top = (a_row - viewradius) % self.rows
            left = (a_col - viewradius) % self.cols
            # Height/width of the top and left parts of vision disc (which might actually
            # be draw at the bottom or right of the map) -- rest of vision disc wraps over.
            toph = min(diameter, self.rows - top)
            leftw = min(diameter, self.cols - left)
            if toph == diameter and leftw == diameter:
                self.visible[top:top+toph, left:left+leftw] |= self.vision_disc
            else:
                bottomh = diameter - toph
                rightw = diameter - leftw

                self.visible[top:top+toph, left:left+leftw] |= self.vision_disc[:toph, :leftw]
                self.visible[:bottomh, left:left+leftw] |= self.vision_disc[toph:, :leftw]
                self.visible[top:top+toph, :rightw] |= self.vision_disc[:toph, leftw:]
                self.visible[:bottomh, :rightw] |= self.vision_disc[toph:, leftw:]
            
        # Any non-land UNSEEN tiles have already been changed to whatever in update()
        self.map[(self.map == UNSEEN) & self.visible] = LAND
    
    def render_text_map(self):
        """Return a pretty text representation of the map"""

        icons = 'abcdefghijABCDEFGHIJ0123456789   #*,!'
        lookup = np.ndarray(len(icons), '|S1', buffer = icons)
        result = lookup[self.map]

        # Visible land gets . rest gets ,
        result[self.visible & (self.map == LAND)] = '.'

        for pos, owner in self.hill_list.iteritems():
            if self.map[pos] >= ANTS:
                # hill already destroyed if owner not the same as ant owner
                result[pos] = lookup[self.map[pos] + 10]
            else:
                result[pos] = lookup[owner + 20]

        tmp = ''
        for row in result:
            tmp += '# ' + row.view(('S', row.shape[0]))[0] + '\n'
        return tmp

    # static methods are not tied to a class and don't have self passed in
    # this is a python decorator
    @staticmethod
    def run(bot):
        """Parse input, update game state and call the bot classes do_turn method"""
        ants = Ants()
        map_data = ''
        while True:
            try:
                current_line = sys.stdin.readline().rstrip('\r\n') # string new line char
                if current_line.lower() == 'ready':
                    ants.setup(map_data)
                    bot.do_setup(ants)
                    ants.finish_turn()
                    map_data = ''
                elif current_line.lower() == 'go':
                    ants.update(map_data)
                    # call the do_turn method of the class passed in
                    bot.do_turn(ants)
                    ants.finish_turn()
                    map_data = ''
                else:
                    map_data += current_line + '\n'
            except EOFError:
                break
            except KeyboardInterrupt:
                raise
            except:
                # don't raise error or return so that bot attempts to stay alive
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
