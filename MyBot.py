from numpy.core.arrayprint import set_printoptions
from ants import *
import logging

logging.basicConfig()
log = logging.getLogger('MyBot')
log.setLevel(logging.DEBUG)

goals = ['food', 'explore', 'enemy_hill']

goal_weights = {
    'food': .05,
    'explore': .04,
    'enemy_hill': .1
}

goal_diffusions = {
    'food': 10,
    'explore': 10,
    'enemy_hill': 10
}

map_vals = {
    'food': -3,
    'explore': -5
}

MAX = 999999

class MyBot:
    def __init__(self):
        self.map = None
        self._ants = None
        self._newmap = None
        self._watermap = None
        self._enemyants = None
        self._myants = None
        self._basecollab = None
        self._targets = {}
        self._goalmaps = {}
        self.sought = defaultdict(int)
        self.enemy_hills = []
        set_printoptions(threshold='nan')

    def do_setup(self, ants):
        for goal in goals:
            self._goalmaps[goal] = np.zeros((ants.rows, ants.cols), float)

        self.ants = ants
        
        self._watermap = np.ones((ants.rows, ants.cols), int)
        self._myants = np.empty((ants.rows, ants.cols), bool)
        self._enemyants = np.empty((ants.rows, ants.cols), bool)

        goal_diffusions['food'] = int(max(ants.rows, ants.cols) * .3)
        goal_diffusions['explore'] = int(max(ants.rows, ants.cols) * .8)
        goal_diffusions['enemy_hill'] = int(max(ants.rows, ants.cols) * .8)

        self._basecollab = np.ones((self.ants.rows, self.ants.cols))

    @staticmethod
    def fear_of(arr):
        t = np.ones(arr.shape, float)
        t[arr] = .8
        #log.debug(t)
        return t

    @staticmethod
    def love_of(arr):
        t = np.ones(arr.shape, arr.dtype)
        t[arr] = 1.2
        return t

    #noinspection PyArgumentEqualDefault
    @staticmethod
    def fastroll(array, shift, axis):
        prefix = [slice(None)] * axis
        shift %= array.shape[axis]
        ret = np.empty_like(array)
        ret[prefix + [slice(shift, None)]] = array[prefix + [slice(None, -shift)]]
        ret[prefix + [slice(0, shift)]] = array[prefix + [slice(-shift, None)]]
        return ret

    def diffuse(self, goal):
        gm = self._goalmaps[goal]
        d = goal_weights[goal]
        l = self._basecollab.copy()
        if goal == 'food':
            l *= MyBot.fear_of(self._myants)
            #log.debug(l)
        gm += d * MyBot.fastroll(gm, shift=1, axis=1) * self._watermap * l
        gm += d * MyBot.fastroll(gm, shift=-1, axis=1) * self._watermap * l
        gm += d * MyBot.fastroll(gm, shift=1, axis=0) * self._watermap * l
        gm += d * MyBot.fastroll(gm, shift=-1, axis=0) * self._watermap * l
        self._goalmaps[goal] = gm

    def dump_diffuse_map(self, goal):
        gm = self._goalmaps[goal]
        for r in range(self._ants.rows):
            cells = []
            for c in range(self._ants.cols):
                val = gm[r, c]
                o = ''
                if self._ants.map[r, c] == WATER:
                    o = '~'
                elif (r, c) in self._ants.my_ants():
                    o = '@'
                elif val > 1000 * MAX:
                    o = '%'
                elif val > .1 * MAX:
                    o = ':'
                elif val > 0:
                    o = '.'
                elif not val:
                    o = ' '
                cells.append(o)
            log.debug(''.join(cells))

    def move_to_goal(self, (r, c), goal):
        neighbors = self._ants.neighbours((r, c))
        gm = self._goalmaps[goal]
        food_vals = [(gm[nr, nc], nr, nc) for nr, nc in neighbors]
        food_vals.sort()
        food_vals.reverse()
        for v in food_vals:
            dest, food_val = (v[1], v[2]), v[0]
            self.sought[goal] += 1
#            log.debug('Ant (seeking %s) (%s, %s) -> (%s) %s %s' %
#                      (goal, r, c, food_val, dest[0], dest[1]))
            if dest not in self._targets:
                self._ants.issue_order((r, c), dest)
                self._targets[dest] = (r, c)
                break
            self._targets[(r, c)] = (r, c)

    def do_turn(self, ants):
        start_time = ants.time_remaining()
        log.debug('Time remaining: %s', start_time)
        self._ants = ants
        self._targets = {}
        self._enemyants *= False
        self._myants *= False
        decisions = {}
        to_diffuse = ['food', 'explore']

        for goal in ['food', 'explore']:
            self._goalmaps[goal] *= 0

        t = ants.map == -4
        self._watermap[t] = 0

        for ant in ants.ant_list:
            if ant in ants.my_ants():
                self._myants[ant] = True
            else:
                self._enemyants[ant] = True
        log.debug('Time left after making collab maps: %s', ants.time_remaining())

        for eh in self._ants.enemy_hills():
            if eh not in self.enemy_hills:
                self.enemy_hills.append(eh)
                self._goalmaps['enemy_hill'] *= 0
                if 'enemy_hill' not in to_diffuse:
                    to_diffuse.append('enemy_hill')
            self._goalmaps['enemy_hill'][eh[0]] = MAX
        log.debug('Time left after mapping hills: %s', ants.time_remaining())


        for goal in ['food', 'explore']:
            t = ants.map == map_vals[goal]
            self._goalmaps[goal][t] = MAX/2
        log.debug('Time left after marking goals: %s', ants.time_remaining())

        
        for goal in to_diffuse:
            for i in range(goal_diffusions[goal]):
                self.diffuse(goal=goal)
        log.debug('Time left after diffusing: %s', ants.time_remaining())

        for r, c in ants.my_ants():
            if self._goalmaps['food'][r, c] > 0:
                target_goal = 'food'
            elif self._goalmaps['enemy_hill'][r, c] > 0:
                target_goal = 'enemy_hill'
            elif self._goalmaps['explore'][r, c] > 0:
                target_goal = 'explore'
            else:
                target_goal = None
                
            if target_goal:
                self.move_to_goal((r, c), goal=target_goal)
            else:
                dest = random.choice(ants.neighbours((r, c)))
                if dest not in self._targets:
                    self._targets[dest] = (r, c)
                    self._ants.issue_order((r, c), dest)
                log.debug('Ant (seeking %s) (%s, %s) ->  %s %s' %
                      ('nothing', r, c, dest[0], dest[1]))
                self.sought['nothing'] += 1
        log.debug('Time left after moving ants: %s', ants.time_remaining())

        #self.dump_diffuse_map('enemy_hill')
        log.debug(self.sought)
        log.debug('my ants: %s enemy hills: %s', len(ants.my_ants()), self.enemy_hills)
        log.debug('Turn took %sms.', start_time - ants.time_remaining())


if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    try:
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
