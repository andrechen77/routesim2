from simulator.node import Node
import logging
import json

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.logging.debug("new node %d" % self.id)
        self.link_states = {} # dictionary from unordered pairs of link ids (frozensets) to (seq_num, latency) pairs
        self.adj_list = {} # dictionary from a node id to sets of neighbor ids
        self.routing_table = {}

    def __str__(self):
        return f"A Link State Node: {str(self.id)}\nLink neighbors: {self.neighbors}\nLink state dict: {str(self.link_states)}\n"

    # updates the link in my own routing table only, returns a (old_seq_num, (seq_num,
    # latency)) tuple. seq_num of None means that the update is directly observed
    def update_link(self, link, latency, seq_num=None):
        old_seq_num, latency = self.link_states.get(link, (0, -1))
        print("updating link:", link, latency, seq_num, old_seq_num)
        if seq_num is None or seq_num > old_seq_num:
            # maintain link states
            self.link_states[link] = old_seq_num + 1, latency

            # maintain adjacency list of network
            if latency == -1:
                src, dst = link
                self.adj_list.get(src, set()).discard(dst)
                self.adj_list.get(dst, set()).discard(src)
            else:
                self.adj_list.get(src, set()).add(dst)
                self.adj_list.get(dst, set()).add(src)

            self.run_djikstra()
        return old_seq_num, self.link_states[link]

    def run_djikstra(self):
        # TODO rerun dijkstra's algorithm to find the shortest path from me to
        # every other node
        # First, let's define a function to find the node with the smallest distance
        # that has not been visited yet
        def min_distance(distances, visited):
            # Initialize minimum distance for next node
            min_val = float('inf')
            min_node = -1
            # Loop through all nodes to find minimum distance
            for i in range(len(distances)):
                if distances[i] < min_val and i not in visited:
                    min_val = distances[i]
                    min_node = i
            return min_node

        # Initialize distance and visited "arrays"
        infinity = float('inf')
        distances = {v:infinity for v in self.adj_list.keys()}
        visited = set()
        # Set distance at starting node to 0 and add to visited list
        distances[self.id] = 0
        visited.add(self.id)
        # Loop through all nodes to find shortest path to each node
        for v in self.adj_list.keys():
            # Find minimum distance node that has not been visited yet
            current_node = min_distance(distances, visited)
            # Add current_node to list of visited nodes
            visited.add(current_node)
            # Loop through all neighboring nodes of current_node
            for neighbor in self.adj_list[v]:
                # Calculate the distance from start_node to neighbor,
                # passing through current_node
                latency = self.link_states[frozenset(neighbor, current_node)][1]
                new_distance = distances[current_node] + latency
                # Update the distance if it is less than previous recorded value
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    if v == self.id:
                        self.routing_table[neighbor] = neighbor
                    else:
                        self.routing_table[neighbor] = self.routing_table[v]

        # Return the list of the shortest distances to all nodes
        self.distances = distances

    def serialize_routing_message(self, link):
        # routing message: link source, link destination, sequence number, latency
        seq_num, latency = self.link_states[link]
        src, dst = link
        msg_obj = {
            "sender_id": self.id,
            "src": src,
            "dst": dst,
            "seq_num": seq_num,
            "latency": latency
        }
        return json.dumps(msg_obj)

    def deserialize_routing_message(self, msg):
        msg = json.loads(msg)
        return msg["sender_id"], frozenset([msg["src"], msg["dst"]]), msg["seq_num"], msg["latency"]

    def link_has_been_updated(self, neighbor, latency):
        self.logging.debug('link update, neighbor %d, latency %d, time %d' % (neighbor, latency, self.get_time()))

        my_link = frozenset([self.id, neighbor])

        # update link_states dict
        self.update_link(my_link, latency)

        if latency == -1 and neighbor in self.neighbors:
            # delete a link
            self.neighbors.remove(neighbor)
        elif latency != -1 and neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            # for new neighbors, send information about every link in link_states dict
            for link in self.link_states:
                self.send_to_neighbor(neighbor, self.serialize_routing_message(link))

        # propogate received link info to all neighbors
        self.send_to_neighbors(self.serialize_routing_message(my_link))

    def process_incoming_routing_message(self, m):
        self.logging.debug("receive a message at Time %d. " % self.get_time() + m)

        sender_id, msg_link, seq_num, latency = self.deserialize_routing_message(m)
        old_seq_num, _ = self.update_link(msg_link, latency, seq_num)

        if seq_num > old_seq_num:
            # message is new
            # propagate to all neighbors
            self.send_to_neighbors(self.serialize_routing_message(msg_link))
        elif seq_num < old_seq_num:
            # message is old, send new link info to sender
            self.send_to_neighbor(sender_id, self.serialize_routing_message(msg_link))

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return self.routing_table.get(destination, -1)
