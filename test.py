from network import Node, linkNodes, Thread

x = Node('x')
y = Node('y')
linkNodes(x,y)
z = Node('z')
linkNodes(y,z)
run = Thread(target=x.dsr,args=('z','data goes here'))
run.start()
run.join()