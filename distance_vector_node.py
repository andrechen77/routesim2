from simulator.node import Node
import json

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        # the latest time our DV was updated
        self.latest_dv_update = -1
        # maps from destination node id to (time_cost, path_to_dest) where
        # path_to_dest represents the series of next_hops required to get to the
        # destination. thus, it never includes self.id, and is empty when this
        # node is advertising itself in its DV.
        self.distance_vector = {}

        # maps from a neighbor id to a tuple (timestamp, DV) where DV is the
        # latest DV we've received from them
        self.latest_neighbor_dvs = {}

        # maps from a neighbor id to their link cost
        self.direct_links = {}

        self.recalculate_dv()

    # Return a string
    def __str__(self):
        return f"I am node {str(self.id)}\nLink neighbors: {self.direct_links}\nMy Distance Vector: {self.distance_vector}"

    # Returns whether the DV was changed
    def recalculate_dv(self):
        # print("recalculating dv")
        # start by adding myself to new_dv
        new_dv = {self.id: (0, [])}
        # loop through neighbor's dv's to look for best paths to all dsts
        for neighbor, (_, neighbor_dv) in self.latest_neighbor_dvs.items():
            for dest, (time_cost, path) in neighbor_dv.items():
                # print(f"possible path to {dest} with through neighbor {neighbor} and path {path} with cost {time_cost}")
                cost = self.direct_links[neighbor] + time_cost
                if (dest not in new_dv or cost < new_dv[dest][0]) and self.id not in path:
                    new_dv[dest] = (cost, [neighbor] + path)
        changed = self.distance_vector != new_dv
        self.distance_vector = new_dv
        self.latest_dv_update = self.get_time()
        return changed

    def link_has_been_updated(self, neighbor, latency):
        # print(f"\ntime: {self.get_time()}, node: {self.id}, link has been updated: nei={neighbor} cost={latency}")
        # latency = -1 if delete a link
        if latency == -1 and neighbor in self.neighbors:
            # print(f"deleting neighbor {neighbor}")
            del self.direct_links[neighbor]
            del self.latest_neighbor_dvs[neighbor]
            self.neighbors.remove(neighbor)
        elif latency != -1 and neighbor not in self.neighbors:
            # print(f"adding neighbor {neighbor}"")
            self.direct_links[neighbor] = latency
            self.latest_neighbor_dvs[neighbor] = (-1, {neighbor: (latency, [neighbor])})
            # instead of depending on the neighbor to advertise their existence
            # to us we know that we already have a path to them so just assume
            # that we can use it
            self.neighbors.append(neighbor)
        elif latency != -1 and neighbor in self.neighbors:
            self.direct_links[neighbor]=latency

        # if DV changed, notify neighbors
        if self.recalculate_dv():
            # print("dv changed, notifying neighbors")
            # print(self)
            self.send_to_neighbors(self.serialize_routing_message())

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # print(f"\ntime: {self.get_time()}, node: {self.id}, processing incoming routing message:", m)
        sender_id, new_timestamp, new_dv = self.deserialize_routing_message(m)
        if sender_id not in self.neighbors:
            # our neighbor died after sending this message but before we received the message
            # print("received message from dead neighbor, discarding")
            return
        else:
            current_timestamp, _ = self.latest_neighbor_dvs[sender_id]
            if new_timestamp <= current_timestamp:
                # print("received old message, discarding")
                return

        self.latest_neighbor_dvs[sender_id] = (new_timestamp, new_dv)

        # if DV changed, notify neighbors
        if self.recalculate_dv():
            # print("dv changed, notifying neighbors")
            # print(self)
            self.send_to_neighbors(self.serialize_routing_message())

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        # print("getting next hop")
        no_path_entry = (None, [-1])
        return self.distance_vector.get(destination, no_path_entry)[1][0]

    # returns tuple (sender_id, timestamp, dv)
    def deserialize_routing_message(self, msg):
        msg = json.loads(msg)
        jsonified_dv = msg['dv']
        unjsonified_dv = {int(dst): (cost, path) for dst, [cost, path] in jsonified_dv.items()}
        return msg['sender_id'], msg['timestamp'], unjsonified_dv

    def serialize_routing_message(self):
        msg_obj = {
            'sender_id': self.id,
            'timestamp': self.get_time(),
            'dv': self.distance_vector
        }
        return json.dumps(msg_obj)
