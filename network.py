from threading import Thread, Lock, Event, main_thread

class Node:
    ids = []
    RTT = 3     # num of seconds till timeout
    def __init__(self, id: str):
        if id in Node.ids:
            raise ValueError(f'id {id} already in use')
        Node.ids.append(id)

        self.id = id    # str
        self.routes = []    # lists of node ids (str)
        self.neighbors = []     # Nodes
        self.RREQ = False
        self.RREP = False
        self.lock = Lock()
        self.timeout = Event()

    def __str__(self):
        return self.id

    def dsr(self, dest: str, data = 'default data'):
        # if self has route to dest, transmit data
        for r in self.routes:   # currently explores only first valid route (should explore every possible route)
            if dest in r:
                self.__transmit(r, data)
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
        self.__forward('RREQ', route, dest=dest)

        # wait for RREP or timeout
        timer = Thread(target=self.__timer,name=f'{self.id}.timer')
        timer.start()
        while (not self.RREP) and (not self.timeout.is_set()):
            pass

        # if self received RREP, forward DATA
        if self.RREP:
            for r in self.routes:
                if dest in r:
                    self.__forward('DATA', r, data=data)
                    return
        # else, timeout
        else:
            print(f'{self.id} timeout')

    def __forward(self, msg: str, route: list, dest = '', data = 'default data'):
        
        #print(f'{self.id} {msg} {route} {dest}')

        # RREQ: send RREQ to each neighbor
        if msg == 'RREQ':
            for n in self.neighbors:
                t = Thread(target=n.__rreq, args=(route,dest), name=f'{n.id}.RREQ')
                t.start()
            return
        # RREP: send RREP to prev node in route
        if msg == 'RREP':
            prevnode = route[route.index(self.id) - 1]
            for n in self.neighbors:
                if n.id == prevnode:
                    t = Thread(target=n.__rrep,args=(route,),name=f'{n.id}.RREP')
                    t.start()
                    return
        # DATA: send DATA to next node in route
        if msg == 'DATA':
            nextnode = route[route.index(self.id) + 1]
            for n in self.neighbors:
                if n.id == nextnode:
                    t = Thread(target=n.__transmit,args=(route,data))
                    t.start()
                    return
        if msg == 'ERR':
            return
        else:
            print(f'Node {self.id}.forward(): Invalid msg')
    
    def __rreq(self, route: list, dest: str):

        #print(f'__rreq {self.id} {route} {dest}')

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
            self.__forward('RREQ', route, dest=dest)
    
    def __rrep(self, route: list):
        
        #print(f'__rrep {self.id} {route}')
        
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
        self.__forward('RREP', route)

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
        # if self is dest, transmit success
        if self.id == route[len(route) - 1]:
            print(f'{self.id} (DATA): {data}')
        # else, forward data to next node in route
        else:
            self.__forward('DATA', route, data=data)

    def __timer(self):
        timeremaining = Node.RTT
        i = 0.1 # seconds
        # while there is time remaining, check if self received RREP then stop timer
        # otherwise, wait for i sec then decrement time remaining by i
        while timeremaining > 0:
            if self.RREP:
                return
            self.timeout.wait(i)
            timeremaining -= i
        # trigger timeout
        self.timeout.set()
            

def linkNodes(u: Node, v: Node):
    if v not in u.neighbors and u not in v.neighbors:
        u.neighbors.append(v)
        v.neighbors.append(u)
    else:
        print('already linked')


x = Node('x')
y = Node('y')
linkNodes(x,y)
z = Node('z')
linkNodes(y,z)
run = Thread(target=x.dsr,args=('z','data goes here'))
run.start()
run.join()
#print(x.routes)
#print(y.routes)
#print(z.routes)

###print(f'Routes: {y.routes}')
'''
print(threading.enumerate())
mainthread = threading.main_thread()
for t in threading.enumerate():
    if t is not mainthread:
        print(t.getName())
'''
