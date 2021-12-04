from network import Node, Link, linkNodes, Thread, crash
import logging
import string
from time import sleep

logging.basicConfig(level=logging.DEBUG,filename='driver.log',format='%(asctime)s : %(levelname)s : %(message)s')


def main():
    logging.info('INITIALIZATION =============================================')
    '''
    class Node and class Link settings
    '''
    Node.RTT = 3
    Node.recover_time = .1
    Node.auto_recover = True

    Link.recover_time = .1
    Link.auto_recover = True

    logging.info(f'<class Node> RTT={Node.RTT} s, recover_time={Node.recover_time} s, auto_recover={Node.auto_recover}')
    logging.info(f'<class Link> recover_time={Link.recover_time} s, auto_recover={Link.auto_recover}')

    '''
    Creation of nodes
    '''
    num_nodes = 4   # desired num of nodes
    nodes = []      # list containing all nodes
    names = list(string.ascii_uppercase) # all nodes alphabetically named
    for name in names:
        if names.index(name) >= num_nodes:
            break
        nodes.append(Node(name))
    
    logging.info(f'Number of nodes={num_nodes}')
    logging.info(f'Nodes={nodes}')

    '''
    Linking of nodes
    '''
    links = []
    links.append(linkNodes(nodes[0],nodes[1]))  # link A-B
    links.append(linkNodes(nodes[1],nodes[2]))  # link B-C
    links.append(linkNodes(nodes[0],nodes[3]))  # link A-D
    links.append(linkNodes(nodes[2],nodes[3]))  # link C-D

    logging.info(f'Number of links={len(links)}')
    logging.info(f'Links={links}')

    '''
    Crashing of nodes/links
    crash(<Node or Link>)
    '''
    crash(nodes[1]) # crashes Node B

    '''
    Recovery of nodes/links (default set to autorecovery)
    recover(<Node or Link>)
    '''

    '''
    DSR test run
    '''
    logging.info('TEST START =================================================')
    logging.info(f'Nodes={nodes}')
    logging.info(f'Links={links}')
    src = nodes[0]      # src is Node A
    dest_id = nodes[2].id  # dest is Node C
    data = 'data goes here'
    print(f'Node {src.id} sending data to Node {dest_id}')
    run = Thread(target=src.dsr,args=(dest_id,data))
    run.start()
    run.join()  # waits for 'run' thread to finish
    sleep(1)    
    for n in nodes:
        n.resetflags()
    logging.info(f'Nodes={nodes}')
    logging.info(f'Links={links}')    
    src = nodes[1]      # src is node B
    dest_id = nodes[3].id  # dest is Node D
    data = 'data goes here'
    print(f'Node {src.id} sending data to Node {dest_id}')
    run1 = Thread(target=src.dsr,args=(dest_id,data))
    run1.start()
    run1.join()  # waits for 'run' thread to finish
    
if __name__ == '__main__':
    main()