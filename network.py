from threading import Thread, Lock, Event
import logging
import time

class Node:
    ids = []
    RTT = 3     # num of seconds till timeout
    recover_time = 1 # num of seconds to recover
    auto_recover = True
    error_count = 0
    num_hops = 0
    result = -1 # initial = -1, fail = 0, success = 1
    def __init__(self, id: str):
        if id in Node.ids:
            raise ValueError(f'id {id} already in use')
        Node.ids.append(id)

        self.id = id    # str
        self.routes = []    # lists of node ids (str)
        self.neighbors = []     # Nodes
        self.links = []     # links to neighbors
        self.RREQ = False
        self.RREP = False
        self.RERR = False
        self.ACK = False
        self.alive = True
        self.lock = Lock()
        self.timeout = Event()

    def __str__(self):
        status = str()
        if self.alive:
            status = 'live'
        else:
            status = 'dead'
        return f'{self.id}:{status}'

    def __repr__(self):
        return str(self)

    def dsr(self, dest: str, data = 'default data'):
        # reset hop counter
        Node.num_hops = 0
        # if self has route to dest, transmit data
        hasroute = False
        for r in self.routes:
            if dest in r:
                hasroute = True
                retry = 0
                while retry < 2:
                    self.__forward('DATA', r.copy(), data=data)

                    # wait for DACK, RERR, or timeout
                    timer = Thread(target=self.__timer,args=('ACK',),name=f'{self.id}.DACK_timer')
                    timer.start()
                    while (not self.ACK) and (not self.RERR) and (not self.timeout.is_set()):
                        pass

                    # if self received ACK from dest, forward complimentary ACK
                    if self.ACK:
                        self.__forward('SACK', r.copy())
                        return

                    # if self received RERR, reset RERR flag and try again if another route available
                    elif self.RERR:
                        self.lock.acquire()
                        try:
                            self.RERR = False
                        finally:
                            self.lock.release()

                    # else, try once more
                    else:
                        retry += 1
        # if found route but all failed, no other routes available
        if hasroute:
            print(f'Node {self.id} unable to forward data to Node {dest}')
            # prompt user to continue trying to RREQ. default is yes
            x = input(f'Continue trying? [Y/N]\n')
            #if x == 'Y':
                #time.sleep(.1)
            if x == 'N':
                Node.result = 0
                return

        # else, begin RREQ
        # set RREQ flag
        self.lock.acquire()
        try:
            self.RREQ = True
        finally:
            self.lock.release()
        # forward RREQ to neighbors
        route = [self.id]
        self.__forward('RREQ', route.copy(), dest=dest)

        # wait for RREP or timeout
        timer = Thread(target=self.__timer,args=('RREP',),name=f'{self.id}.RREP_timer')
        timer.start()
        while (not self.RREP) and (not self.timeout.is_set()):
            pass

        # if self received RREP, forward DATA
        if self.RREP:
            for r in self.routes:
                if dest in r:
                    retry = 0
                    while retry < 2:
                        self.__forward('DATA', r.copy(), data=data)

                        # wait for DACK, RERR, or timeout
                        timer = Thread(target=self.__timer,args=('ACK',),name=f'{self.id}.DACK_timer')
                        timer.start()
                        while (not self.ACK) and (not self.RERR) and (not self.timeout.is_set()):
                            pass

                        # if self received ACK from dest, forward complimentary ACK
                        if self.ACK:
                            self.__forward('SACK', r.copy())
                            return

                        # if self received RERR, reset RERR flag and try again if another route available
                        elif self.RERR:
                            self.lock.acquire()
                            try:
                                self.RERR = False
                            finally:
                                self.lock.release()

                        # else, try once more
                        else:
                            retry += 1
            # no other routes available
            print(f'Node {self.id} unable to forward data to Node {dest}')

        # else, timeout
        else:
            print(f'Node {self.id} timed out. Unable to find route to Node {dest}')
        
        # prompt user to continue trying. default is yes
        x = input(f'Continue trying? [Y/N]\n')
        if x == 'N':
            Node.result = 0
            return
        else:
        
            self.resetflags()
            self.dsr(dest,data)

    def resetflags(self):
        self.RREQ = False
        self.RREP = False
        self.RERR = False
        self.ACK = False

    def __forward(self, msg: str, route: list, dest = '', data = 'default data'):
        
        logging.debug(f'{self.id} {msg} {route} {dest}')

        # RREQ: send RREQ to each neighbor
        if msg == 'RREQ':
            for n in self.neighbors:
                for link in self.links:
                    # only if link to neighbor and neighbor are alive, forward RREQ
                    if link == Link(self,n) and link.alive and n.alive:
                        t = Thread(target=n.__rreq, args=(route.copy(),dest), name=f'{n.id}.RREQ')
                        t.start()
            return
        # RREP: send RREP to prev node in route
        if msg == 'RREP':
            prevnode = route[route.index(self.id) - 1]
            for n in self.neighbors:
                if n.id == prevnode:
                    for link in self.links:
                        # only if link to n and n are alive, forward RREP
                        if link == Link(self,n) and link.alive and n.alive:
                            t = Thread(target=n.__rrep,args=(route.copy(),),name=f'{n.id}.RREP')
                            t.start()
                            return
        # RERR: send RERR to prev node in route
        if msg == 'RERR':
            # increment hop counter
            Node.num_hops += 1
            prevnode = route[route.index(self.id) - 1]
            for n in self.neighbors:
                if n.id == prevnode:
                    for link in self.links:
                        # only if link to n and n are alive, forward RERR
                        if link == Link(self,n) and link.alive and n.alive:
                            t = Thread(target=n.__rerr, args=(route.copy(),data),name=f'{n.id}.RRER')
                            t.start()
                            return
        # DATA: send DATA to next node in route
        if msg == 'DATA':
            # increment hop counter
            Node.num_hops += 1
            nextnode = route[route.index(self.id) + 1]
            for n in self.neighbors:
                if n.id == nextnode:
                    for link in self.links:
                        if link == Link(self,n):
                            # forward DATA to n only if link to n and n is alive
                            if link.alive and n.alive:
                                t = Thread(target=n.__transmit,args=(route.copy(),data))
                                t.start()
                            # if link to n is dead, forward RERR and dead link back to src
                            elif not link.alive:
                                self.error_count += 1
                                self.__rerr(route,[self.id,n.id])
                            # else, n is dead, forward RERR and dead node back to src
                            else:
                                self.error_count += 1
                                self.__rerr(route,[n.id])
                            return
        # DACK: send DACK to prev node in route
        if msg == 'DACK':
            # increment hop counter
            Node.num_hops += 1
            prevnode = route[route.index(self.id) - 1]
            for n in self.neighbors:
                if n.id == prevnode:
                    for link in self.links:
                        # only if link to n and n are alive, forward DACK
                        if link == Link(self,n) and link.alive and n.alive:
                            t = Thread(target=n.__dack, args=(route.copy(),),name=f'{n.id}.DACK')
                            t.start()
                            return
        # SACK: send SACK to next node in route
        if msg == 'SACK':
            # increment hop counter
            Node.num_hops += 1
            nextnode = route[route.index(self.id) + 1]
            for n in self.neighbors:
                if n.id == nextnode:
                    for link in self.links:
                        # only if link to n and n are alive, forward SACK
                        if link == Link(self,n) and link.alive and n.alive:
                            t = Thread(target=n.__sack, args=(route.copy(),),name=f'{n.id}.SACK')
                            t.start()
                            return
        else:
            logging.critical(f'Node {self.id}.forward(): Invalid msg: {msg}')
    
    def __rreq(self, route: list, dest: str):
        # cache route
        self.__cache(route)
        # if self already forwarded RREQ, terminate
        if self.RREQ:
            return
        # else, set RREQ flag
        self.lock.acquire()
        try:
            self.RREQ = True
        finally:
            self.lock.release()
        # append self to route
        route.append(self.id)
        # if self is dest, begin RREP
        if self.id == dest:
            self.__rrep(route)
        # else, forward RREQ
        else:
            self.__forward('RREQ', route.copy(), dest=dest)
    
    def __rrep(self, route: list):
        # cache route
        self.__cache(route)
        # if self already received RREP, terminate
        if self.RREP:
            return
        # if self is src, trigger src RREP flag and terminate
        if self.id == route[0]:
            self.lock.acquire()
            try:
                self.RREP = True
            finally:
                self.lock.release()
            return
        # else, forward RREP
        self.__forward('RREP', route.copy())

    def __cache(self, route: list):
        # make route copy to work with
        rcopy = route.copy()
        # if self not in route, must append self to route, reverse route
        # and add all subroutes starting from self
        if self.id not in rcopy:
            rcopy.append(self.id)
            rcopy.reverse()
            for i in range(2,len(rcopy) + 1):
                subroute = rcopy[:i]
                self.lock.acquire()
                try:
                    if subroute not in self.routes:
                        self.routes.append(subroute)
                finally:
                    self.lock.release()
        # else, self in route. only need to add subroutes
        # starting from self to end of current route
        else:
            i = rcopy.index(self.id)
            for j in range(i + 2, len(rcopy) + 1):
                subroute = rcopy[i:j]
                self.lock.acquire()
                try:
                    if subroute not in self.routes:
                        self.routes.append(subroute)
                finally:
                    self.lock.release()
        
        #print(f'__cache {self.id} {self.routes}')

    def __transmit(self, route: list, data):
        # if self is dest, transmit success, forward ACK to src
        if self.id == route[len(route) - 1]:
            self.__forward('DACK',route.copy())
            # wait for SACK or timeout before dislaying data
            timer = Thread(target=self.__timer,args=('ACK',),name=f'{self.id}.SACK_timer')
            timer.start()
            while (not self.ACK) and (not self.timeout.is_set()):
                pass
            Node.result = 1
            logging.info(f'{self.id} received data: {data}')
            logging.info(f'Total hops: {Node.num_hops}')
            print(f'Node {self.id} received data: {data}')
            print(f'Total hops: {Node.num_hops}')
        # else, forward data to next node in route
        else:
            self.__forward('DATA', route.copy(), data=data)

    def __rerr(self, route: list, delroute: list):
        # delete all routes with dead link/node
        self.__delete(delroute)
        # if self is src, trigger src RERR flag and terminate
        if self.id == route[0]:
            self.lock.acquire()
            try:
                self.RERR = True
            finally:
                self.lock.release()
            return
        # else, forward RERR backwards on route
        else:
            self.__forward('RERR', route.copy(), data = delroute)
    
    def __delete(self, delroute: list):
        # if delroute is a node, remove all routes with that node
        if len(delroute) == 1:
            for route in self.routes:
                if delroute[0] in route:
                    self.lock.acquire()
                    try:
                        self.routes.remove(route)
                    finally:
                        self.lock.release()
        # else, delroute is a link, remove all routes with link in forward and reverse
        else:
            x, y = delroute
            for route in self.routes:
                if x in route and y in route:
                    if (route.index(x) + 1 == route.index(y)) or (route.index(x) - 1 == route.index(y)):
                        self.lock.acquire()
                        try:
                            self.routes.remove(route)
                        finally:
                            self.lock.release()

    def __dack(self, route: list):
        # if self is src, set ACK flag for src
        if self.id == route[0]:
            self.lock.acquire()
            try:
                self.ACK = True
            finally:
                self.lock.release()
        # else, forward DACK
        else:
            self.__forward('DACK', route.copy())
    
    def __sack(self, route: list):
        # if self is dest, set ACK flag for src
        if self.id == route[len(route) - 1]:
            self.lock.acquire()
            try:
                self.ACK = True
            finally:
                self.lock.release()
        # else, forward SACK
        else:
            self.__forward('SACK', route.copy())

    def __timer(self, msg: str):
        timeremaining = Node.RTT
        i = 0.1 # seconds
        # while there is time remaining, check if self received RREP/ACK then stop timer
        # otherwise, wait for i sec then decrement time remaining by i
        while timeremaining > 0:
            if (msg == 'RREP' and self.RREP) or (msg == 'ACK' and (self.ACK or self.RERR)):
                return
            self.timeout.wait(i)
            timeremaining -= i
        # trigger timeout
        self.timeout.set()

class Link:
    auto_recover = True
    recover_time = 1 # num of seconds to recover
    def __init__(self, u: Node, v: Node):
        if u == v:
            raise ValueError('attempt to link node to self')
        self.node1 = u.id
        self.node2 = v.id
        self.alive = True
        self.lock = Lock()
    
    def __eq__(self, other):
        if isinstance(other,Link):
            return (self.node1 == other.node1 and self.node2 == other.node2) or (self.node1 == other.node2 and self.node2 == other.node1)
        else:
            raise TypeError('expecting Link')
    
    def __str__(self):
        status = str()
        if self.alive:
            status = 'live'
        else:
            status = 'dead'
        return f'{self.node1}-{self.node2}:{status}'

    def __repr__(self):
        return str(self)

def linkNodes(u: Node, v: Node) -> Link:
    if u == v:
        raise ValueError('Attempt to link node to self')
    if v not in u.neighbors and u not in v.neighbors:
        u.neighbors.append(v)
        v.neighbors.append(u)
        link = Link(u,v)
        u.links.append(link)
        v.links.append(link)
        return link
    else:
        logging.warning(f'Nodes {u} and {v} already linked')

def crash(u):
    if (isinstance(u, Node) or isinstance(u, Link)):
        if u.alive:
            u.lock.acquire()
            try:
                u.alive = False
            finally:
                u.lock.release()
            if u.auto_recover:
                t = Thread(target=recover,args=(u,))
                t.start()
        else:
            print(f'Node {u} already crashed')
    else:
        raise TypeError('Expecting Node or Link')

def recover(u):
    if (isinstance(u, Node) or isinstance(u, Link)):
        if not u.alive:
            timer = Event()
            timer.wait(u.recover_time)
            u.lock.acquire()
            try:
                u.alive = True
            finally:
                u.lock.release()
        else:
            print(f'Node {u} already live')
    else:
        raise TypeError('Expecting Node or Link')