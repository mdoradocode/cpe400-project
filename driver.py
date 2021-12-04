from network import Node, Link, linkNodes, Thread, crash
import logging
import string
from time import sleep
import random

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
    num_nodes = 16   # desired num of nodes
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
    links.append(linkNodes(nodes[1],nodes[5]))  # link B-F
    links.append(linkNodes(nodes[2],nodes[3]))  # link C-D
    links.append(linkNodes(nodes[3],nodes[4]))  # link D-E
    links.append(linkNodes(nodes[3],nodes[5]))  # link D-F
    links.append(linkNodes(nodes[5],nodes[6]))  # link F-G
    links.append(linkNodes(nodes[5],nodes[8]))  # link F-I
    links.append(linkNodes(nodes[6],nodes[7]))  # link G-H
    links.append(linkNodes(nodes[7],nodes[8]))  # link H-I
    links.append(linkNodes(nodes[8],nodes[9]))  # link I-J
    links.append(linkNodes(nodes[9],nodes[10]))  # link J-K
    links.append(linkNodes(nodes[10],nodes[11]))  # link K-L
    links.append(linkNodes(nodes[10],nodes[12]))  # link K-M
    links.append(linkNodes(nodes[11],nodes[12]))  # link L-M
    links.append(linkNodes(nodes[11],nodes[13]))  # link L-N
    links.append(linkNodes(nodes[11],nodes[14]))  # link L-O
    links.append(linkNodes(nodes[11],nodes[15]))  # link L-P
    links.append(linkNodes(nodes[12],nodes[13]))  # link M-N
    links.append(linkNodes(nodes[13],nodes[14]))  # link N-O
    links.append(linkNodes(nodes[14],nodes[15]))  # link O-P

    logging.info(f'Number of links={len(links)}')
    logging.info(f'Links={links}')

    '''
    Crashing of nodes/links
    crash(<Node or Link>)
    '''
    #crash(nodes[1]) # crashes Node B

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
    counter = 0
    while counter < 10:
        srcIndex = random.randint(0,num_nodes-1)#Generate a random src node
        destIndex = random.randint(0,num_nodes-1)#Generate a random destination node
        while srcIndex == destIndex:    #Check to see if the src and dest are the same and regenerate the dest if so
            destIndex = random.randint(0,num_nodes-1)
        src = nodes[srcIndex]     
        dest_id = nodes[destIndex].id  
        data = 'Test data starting at ' + nodes[srcIndex].id + " and ending at " + nodes[destIndex].id #Data with a little extra info
        print(f'Node {src.id} sending data to Node {dest_id}')
        run = Thread(target=src.dsr,args=(dest_id,data))
        run.start()
        run.join()  # waits for 'run' thread to finish
        counter += 1
        sleep(1)
        crash(nodes[random.randint(0,num_nodes-1)]) 
        for n in nodes:
            n.resetflags()  
        logging.info(f'Nodes={nodes}')
        logging.info(f'Links={links}')   

     
    
if __name__ == '__main__':
    main()