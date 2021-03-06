import json

from avatar.common import *
from avatar_core.serializers import *

ROAD_NETWORK = dict()
HMM_RESULT = dict()
USER_HISTORY = dict()


def get_road_network_by_id(road_network_id):
    if road_network_id not in ROAD_NETWORK:
        ROAD_NETWORK[road_network_id] = create_road_network_dict(road_network_id)
    return ROAD_NETWORK[road_network_id]


def create_road_network_dict(road_network_id):
    log("Creating cache for road network " + road_network_id + "...")
    start = datetime.now()
    road_network = RoadNetwork.objects.get(id=road_network_id)
    road_network_data = RoadNetworkSerializer(road_network).data
    # Re-construct the road network into dictionary
    road_network_dict = dict()
    # Save all roads associated with the road network
    road_network_dict["roads"] = dict()
    for road in road_network_data["roads"]:
        road_network_dict["roads"][road["id"]] = road
    # Save all intersections associated with the road network
    road_network_dict["intersections"] = dict()
    for intersection in road_network_data["intersections"]:
        road_network_dict["intersections"][intersection["id"]] = intersection
    # Save all grid cells associated with the road network
    road_network_dict["grid_cells"] = dict()
    for grid_cell in road_network_data["grid_cells"]:
        if str(grid_cell["lat_id"]) not in road_network_dict["grid_cells"]:
            road_network_dict["grid_cells"][str(grid_cell["lat_id"])] = dict()
        road_network_dict["grid_cells"][str(grid_cell["lat_id"])][str(grid_cell["lng_id"])] = grid_cell
    # Save other information associated with the road network
    road_network_dict["city"] = road_network_data["city"]
    road_network_dict["grid_lat_count"] = road_network_data["grid_lat_count"]
    road_network_dict["grid_lng_count"] = road_network_data["grid_lng_count"]
    road_network_dict["pmin"] = road_network_data["pmin"]
    road_network_dict["pmax"] = road_network_data["pmax"]
    road_network_dict["graph"] = json.loads(road_network_data["graph"])
    if road_network_data["shortest_path_index"] is not None:
        road_network_dict["shortest_path_index"] = json.loads(road_network_data["shortest_path_index"])
    else:
        road_network_dict["shortest_path_index"] = None
    end = datetime.now()
    log("Saving road network to memory takes " + str((end - start).total_seconds()) + " seconds.")
    return road_network_dict


def get_traj_by_id(traj_id):
    traj = Trajectory.objects.get(id=traj_id)
    traj = TrajectorySerializer(traj).data
    if traj_id in HMM_RESULT:
        traj["path"] = HMM_RESULT[traj_id]
        for fragment in traj["path"]["road"]:
            road = Road.objects.get(id=fragment["road"]["id"])
            road_data = RoadSerializer(road).data
            fragment["road"] = road_data
    return traj
