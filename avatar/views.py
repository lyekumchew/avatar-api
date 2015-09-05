import uuid
import csv
from datetime import datetime

from django.db import IntegrityError
from django.db.models import Max, Min
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status

from serializers import *
from map_matching.hmm import *

CSV_UPLOAD_DIR = "/var/www/html/avatar/data/"


class TrajectoryViewSet(viewsets.ModelViewSet):
    queryset = Trajectory.objects.all()
    serializer_class = TrajectorySerializer


class RoadViewSet(viewsets.ModelViewSet):
    queryset = Road.objects.all()
    serializer_class = RoadSerializer


@api_view(['GET'])
def add_traj_from_local_file(request):
    if 'src' in request.GET:
        try:
            ids = []
            traj = None
            with open(CSV_UPLOAD_DIR + request.GET["src"]) as csv_file:
                reader = csv.DictReader(csv_file)
                line_count = 0
                for row in sorted(reader, key=lambda d: (d['taxi'], d['t'])):
                    print "\rImporting Row: " + str(line_count),
                    line_count += 1
                    if traj is None or row['taxi'] != traj.taxi:
                        if traj is not None:
                            # Save previous trajectory
                            traj.save()
                        # Create new trajectory
                        uuid_id = str(uuid.uuid4())
                        trace = Trace(id=uuid_id)
                        trace.save()
                        traj = Trajectory(id=uuid_id, taxi=row['taxi'], trace=trace)
                        traj.save()
                        ids.append(uuid_id)
                    # Append current point
                    sample_id = row["id"]
                    p = Point(lat=float(row["lat"]), lng=float(row["lng"]))
                    p.save()
                    t = datetime.strptime(row["t"], "%Y-%m-%d %H:%M:%S")
                    speed = int(row["speed"])
                    angle = int(row["angle"])
                    occupy = int(row["occupy"])
                    sample = Sample(id=sample_id, p=p, t=t, speed=speed, angle=angle, occupy=occupy, src=0)
                    sample.save()
                    traj.trace.p.add(sample)
            # Save the last trajectory
            traj.save()
            return Response({"ids": ids})
        except IOError:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def create_road_network_from_local_file(request):
    intersections = []

    def find_intersection_from_set(pp):
        for ii in intersections:
            if ii.p.lat == pp.lat and ii.p.lng == pp.lng:
                return ii
        ii = Intersection(id=uuid.uuid4(), p=pp)
        ii.save()
        intersections.append(ii)
        return ii

    def close_road(rr):
        # Add intersection for last point
        ii = find_intersection_from_set(rr.p.last())
        try:
            rr.intersection.add(ii)
        except IntegrityError:
            # print "Warning: road " + road.id + " has only one intersection"
            pass
        # Calculate road length
        rr.length = int(Distance.road_length(rr))
        # Save road
        rr.save()

    if 'src' in request.GET and 'city' in request.GET:
        try:
            city = request.GET["city"]
            road_network = RoadNetwork(city=city)
            road_network.save()
            with open(CSV_UPLOAD_DIR + request.GET["src"]) as csv_file:
                reader = csv.DictReader(csv_file)
                road = None
                line_count = 0
                for row in reader:
                    print "\rImporting Row: " + str(line_count),
                    line_count += 1
                    road_id = city + "-" + row["roadid"] + "-" + row["partid"]
                    p = Point(lat=float(row["lat"]), lng=float(row["lng"]))
                    p.save()
                    if road is None or road_id != road.id:
                        # Close current road if not first road
                        if road is not None:
                            close_road(road)
                        # Create new road
                        road = Road(id=road_id)
                        road.save()
                        road_network.roads.add(road)
                        # Add intersection for first point
                        intersection = find_intersection_from_set(p)
                        road.intersection.add(intersection)
                    # Append current point
                    road.p.add(p)
            # Close last road
            close_road(road)
            # Append all intersections
            for intersection in intersections:
                road_network.intersections.add(intersection)
            # Save the road network
            road_network.save()
            return Response({
                "road_network_id": road_network.id,
                "road_network_name": road_network.city,
                "road_count": road_network.roads.count(),
                "intersection_count": len(intersections)
            })
        except IOError:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_traj_by_id(request):
    if 'id' in request.GET:
        try:
            traj = Trajectory.objects.get(id=request.GET['id'])
            traj = TrajectorySerializer(traj).data
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if "ts" in request.GET and "td" in request.GET:
            ts = datetime.strptime(request.GET["ts"], "%H:%M:%S").time()
            td = datetime.strptime(request.GET["td"], "%H:%M:%S").time()
            pruned = {
                "id": traj["id"],
                "trace": {
                    "id": traj["trace"]["id"],
                    "p": []
                },
                "path": traj["path"],
                "taxi": traj["taxi"]
            }
            # Prune points
            point_list = []
            for p in traj["trace"]["p"]:
                t = datetime.strptime(p["t"], "%Y-%m-%d %H:%M:%S").time()
                if ts <= t <= td:
                    point_list.append(p)
            # Sort by time stamp
            pruned["trace"]["p"] = sorted(point_list, key=lambda k: k['t'])
            return Response(pruned)
        else:
            return Response(traj)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def remove_traj_by_id(request):
    if 'id' in request.GET:
        traj = Trajectory.objects.get(id=request.GET['id'])
        traj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def remove_all_traj(request):
    Trajectory.objects.all().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_all_traj_id(request):
    return Response({
        "ids": Trajectory.objects.values_list('id', flat=True).order_by('id')
    })


@api_view(['GET'])
def remove_road_network(request):
    if 'city' in request.GET:
        try:
            road_network = RoadNetwork.objects.get(city=request.GET['city'])
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Delete all intersections associated with the road network
        for road in road_network.roads.all():
            road_network.roads.remove(road)
            road.delete()
        # Delete all intersections associated with the road network
        for intersection in road_network.intersections.all():
            road_network.intersections.remove(intersection)
            intersection.delete()
        road_network.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def map_matching(request):
    if 'city' in request.GET and 'id' in request.GET:
        city = request.GET['city']
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
        hmm = HmmMapMatching()
        hmm_result = hmm.perfom_map_matching(city, traj.trace, candidate_rank)
        path = hmm_result['path']
        traj.path = path
        traj.save()
        return Response(TrajectorySerializer(traj).data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def create_grid_index_by_road_network_id(request):
    if 'id' in request.GET:
        road_network = RoadNetwork.objects.get(id=request.GET["id"])
        road_network.grid_cells.clear()
        grid_count = 100
        if "grid" in request.GET:
            grid_count = int(request.GET["grid"])
        print "Finding the boundary of the road network..."
        lat_min = road_network.roads.aggregate(Min("p__lat"))["p__lat__min"]
        lat_max = road_network.roads.aggregate(Max("p__lat"))["p__lat__max"]
        lng_min = road_network.roads.aggregate(Min("p__lng"))["p__lng__min"]
        lng_max = road_network.roads.aggregate(Max("p__lng"))["p__lng__max"]
        minp = Point(lat=lat_min, lng=lng_min)
        minp.save()
        maxp = Point(lat=lat_max, lng=lng_max)
        maxp.save()
        print "Creating grid in memory..."
        grid_roads = [i[:] for i in [[] * 10] * 10]
        unit_lat = (maxp.lat - minp.lat) / grid_count
        unit_lng = (maxp.lng - minp.lng) / grid_count
        for road in road_network.roads.all():
            for p in road.p.all():
                i = int((p.lat - minp.lat) / unit_lat)
                if i > grid_count - 1:
                    i = grid_count - 1
                j = int((p.lng - minp.lng) / unit_lng)
                if j > grid_count - 1:
                    j = grid_count - 1
                if road not in grid_roads[i][j]:
                    grid_roads[i][j].append(road)
        print "Saving the results..."
        for i in range(grid_count):
            for j in range(grid_count):
                rect = Rect(lat=minp.lat + unit_lat * i, lng=minp.lng + unit_lng * j, width=unit_lng, height=unit_lat)
                rect.save()
                grid = GridCell(lat_id=i, lng_id=j, area=rect)
                grid.save()
                for road in grid_roads[i][j]:
                    grid.roads.add(road)
                grid.save()
                road_network.grid_cells.add(grid)
        print "Updating the road network..."
        road_network.pmax = maxp
        road_network.pmin = minp
        road_network.grid_lat_count = grid_count
        road_network.grid_lng_count = grid_count
        road_network.save()
        return Response({
            "grid_cell_count": grid_count
        })
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_all_road_network_id(request):
    return Response({
        "ids": RoadNetwork.objects.values_list('id', flat=True).order_by('id')
    })
