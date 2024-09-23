import os
import time
import network_harness as hn
import csv

def test_tiebreaker_protocol():
    
    net = hn.Network()
    nodes = []

    normal_node = hn.Node(1)
    nodes.append(normal_node)
    net.add_node(1, normal_node)

    rogue_node = hn.Node(2, target_func="tie")
    nodes.append(rogue_node)
    net.add_node(2, rogue_node)

    net.create_channel(1, 2)

    normal_node.start()
    time.sleep(5)
    rogue_node.start()

    normal_node_id = normal_node.thisDevice.get_id()
    rogue_node_id = rogue_node.thisDevice.get_id()

    time.sleep(10)

    normal_node.stop()
    rogue_node.stop()
    os.makedirs('output', exist_ok=True)  #creates output folder if it doesn't exist
    normal_log = f'output/device_log_{normal_node_id}.csv'
    rogue_log = f'output/device_log_{rogue_node_id}.csv'

    leader = (normal_node_id > rogue_node_id)

    with open(normal_log, newline='') as normal_logs:
        normal_reader = csv.reader(normal_logs, dialect='excel')
        with open(rogue_log, newline='') as rogue_logs:
            rogue_reader = csv.reader(rogue_logs, dialect='excel')

            normal_tiebreak_hit = False
            rogue_tiebreak_hit = False
            correct_leader_chosen = False
            correct_follower_chosen = False

            for row in normal_reader:
                if (not normal_tiebreak_hit) and (row[2] == f'HEARD OTHER LEADER: {rogue_node_id}'):
                    normal_tiebreak_hit = True
                if (normal_tiebreak_hit and leader) and (row[2] == 'REMAINED LEADER'):
                    correct_leader_chosen = True
                    break
                elif normal_tiebreak_hit and (not leader) and (row[2] == 'BECAME FOLLOWER'):
                    correct_follower_chosen = True
                    break

            for row in rogue_reader:
                if (not rogue_tiebreak_hit) and (row[2] == f'HEARD OTHER LEADER: {normal_node_id}'):
                    rogue_tiebreak_hit = True
                if rogue_tiebreak_hit and (not leader) and (row[2] == 'REMAINED LEADER'):
                    correct_leader_chosen = True
                    break
                elif (rogue_tiebreak_hit and leader) and (row[2] == 'BECAME FOLLOWER'):
                    correct_follower_chosen = True
                    break

                
                

            if normal_tiebreak_hit and rogue_tiebreak_hit and correct_follower_chosen and correct_leader_chosen: 
                print('pass basic tiebreak')
            else:
                print('failed basic tiebreak', normal_tiebreak_hit, rogue_tiebreak_hit, correct_follower_chosen, correct_leader_chosen)


def test_tiebreaker_protocol_multiple_nodes():
    net = hn.Network()
    nodes = [hn.Node(i) for i in range(1, 6)]  # Create 5 nodes
    for node in nodes:
        net.add_node(node.node_id, node)

    for i in range(len(nodes) - 1):
        net.create_channel(nodes[i].node_id, nodes[i + 1].node_id) 

    for node in nodes:
        node.start()

    time.sleep(10)

    for node in nodes:
        node.stop()

    leader_id = max(node.thisDevice.get_id() for node in nodes)  # Find the highest ID to be the leader
    for node in nodes:
        log_file = f'output/device_log_{node.thisDevice.get_id()}.csv'
        with open(log_file, newline='') as log:
            reader = csv.reader(log, dialect='excel')
            for row in reader:
                if row[2] == 'BECAME LEADER':
                    assert node.thisDevice.get_id() == leader_id
                elif row[2] == 'BECAME FOLLOWER':
                    assert node.thisDevice.get_id() != leader_id





def main():
    test_tiebreaker_protocol()
    test_tiebreaker_protocol_multiple_nodes()
if __name__ == "__main__":
    main()