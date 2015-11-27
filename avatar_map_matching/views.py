from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
import time
import json

from avatar_core.serializers import *
from hmm import *
from models import *


@api_view(['GET'])
def find_candidate_road_by_p(request):
    if 'city' in request.GET and 'lat' in request.GET and 'lng' in request.GET and 'map' in request.GET:
        # city = RoadNetwork.objects.get(id=request.GET['city'])
        map_file = open(request.GET['map'], "r")
        road_network = json.loads(map_file.readline())
        point = Point(lat=float(request.GET['lat']), lng=float(request.GET['lng']))
        p = PointSerializer(point).data
        dist = 500.0
        if 'dist' in request.GET:
            dist = float(request.GET['dist'])
        candidate_rids = []
        candidates = find_candidates_from_road(road_network, p)
        for candidate in candidates:
            if candidate["dist"] < dist:
                candidate_rids.append(candidate["rid"])
            else:
                break
        return Response(candidate_rids)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def map_matching(request):
    if 'city' in request.GET and 'id' in request.GET and 'map' in request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
        map_file = open(request.GET['map'], "r")
        road_network = json.loads(map_file.readline())
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
        trace = TraceSerializer(traj.trace).data
        hmm = HmmMapMatching()
        start = time.time()
        hmm_result = hmm.perform_map_matching(road_network, trace, candidate_rank)
        end = time.time()
        print "Map matching task takes " + str(end - start) + "seconds..."
        path = hmm.save_hmm_path_to_database(city, hmm_result)
        traj.path = path
        traj.save()
        # Save the hmm path for other use
        try:
            hmm_path_result = HmmPath.objects.get(city=city, traj=traj)
            hmm_path_result.delete()
        except ObjectDoesNotExist:
            pass
        uuid_id = str(uuid.uuid4())
        new_path = Path(id=uuid_id)
        new_path.save()
        for path_fragment in path.road.all():
            new_path.road.add(path_fragment)
        new_path.save()
        hmm_path = HmmPath(city=city, traj=traj, path=new_path)
        hmm_path.save()
        # Save the emission table for reperform map matching
        try:
            table = HmmEmissionTable.objects.get(city=city, traj=traj)
            table.delete()
        except ObjectDoesNotExist:
            pass
        candidate_rid = json.dumps(hmm_result['candidate_rid'])
        emission_prob = json.dumps(hmm_result['emission_prob'])
        emission_table = HmmEmissionTable(city=city, traj=traj, candidate=candidate_rid, table=emission_prob)
        emission_table.save()
        # Save the transition table for reperform map matching
        try:
            table = HmmTransitionTable.objects.get(city=city, traj=traj)
            table.delete()
        except ObjectDoesNotExist:
            pass
        transition_prob = json.dumps(hmm_result['transition_prob'])
        transition_table = HmmTransitionTable(city=city, traj=traj, beta=hmm_result['beta'], table=transition_prob)
        transition_table.save()
        # Save the hmm path index for other use
        try:
            index = HmmPathIndex.objects.get(city=city, traj=traj)
            index.delete()
        except ObjectDoesNotExist:
            pass
        path_index = json.dumps(hmm_result['path_index'])
        hmm_path_index = HmmPathIndex(city=city, traj=traj, index=path_index)
        hmm_path_index.save()
        return Response({
            "traj": TrajectorySerializer(traj).data,
            "dist": hmm_result['dist']
        })
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def reperform_map_matching(request):
    if 'city' in request.GET and 'id' in request.GET and 'pid' in request.GET and 'rid' in request.GET and 'uid' in request.GET and 'map' in request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
        sample = traj.trace.p.get(id=request.GET['pid'])
        road = city.roads.get(id=request.GET['rid'])
        user = Account.objects.get(id=request.GET['uid'])
        # Insert the query pair into user action history
        try:
            action_list = UserActionHistory.objects.get(user=user, traj=traj)
            try:
                action = action_list.action.get(point=sample)
                action.delete()
            except ObjectDoesNotExist:
                pass
        except ObjectDoesNotExist:
            action_list = UserActionHistory(user=user, traj=traj)
            action_list.save()
        action = Action(point=sample, road=road)
        action.save()
        action_list.action.add(action)
        action_list.save()
        # Load road network and trace to memory
        map_file = open(request.GET['map'], "r")
        road_network = json.loads(map_file.readline())
        trace = TraceSerializer(traj.trace).data
        # Convert action list to dictionary
        action_set = {}
        p_list = traj.trace.p.all().order_by("t")
        for action in action_list.action.all():
            for i in range(len(p_list)):
                if p_list[i].id == action.point.id:
                    action_set[i] = action.road.id
        if settings.DEBUG:
            print action_set
        # Construct the probability tables generated by previous map matching
        candidate_rid = json.loads(HmmEmissionTable.objects.get(city=city, traj=traj).candidate)
        emission_prob = json.loads(HmmEmissionTable.objects.get(city=city, traj=traj).table)
        transition_prob = json.loads(HmmTransitionTable.objects.get(city=city, traj=traj).table)
        beta = HmmTransitionTable.objects.get(city=city, traj=traj).beta
        hmm = HmmMapMatching()
        hmm.candidate_rid = candidate_rid
        hmm.emission_prob = emission_prob
        hmm.transition_prob = transition_prob
        hmm_result = hmm.reperform_map_matching(road_network, trace, candidate_rank, action_set, beta)
        path = hmm.save_hmm_path_to_database(city, hmm_result)
        traj.path = path
        traj.save()
        return Response(TrajectorySerializer(traj).data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_candidate_rid_by_traj(request):
    if 'city' in request.GET and 'id' in request.GET:
        try:
            city = RoadNetwork.objects.get(id=request.GET['city'])
            traj = Trajectory.objects.get(id=request.GET['id'])
            candidate_rid = json.loads(HmmEmissionTable.objects.get(city=city, traj=traj).candidate)
            return Response(candidate_rid)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_emission_table_by_traj(request):
    if 'city' in request.GET and 'id' in request.GET:
        try:
            city = RoadNetwork.objects.get(id=request.GET['city'])
            traj = Trajectory.objects.get(id=request.GET['id'])
            emission_prob = json.loads(HmmEmissionTable.objects.get(city=city, traj=traj).table)
            return Response(emission_prob)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_transition_table_by_traj(request):
    if 'city' in request.GET and 'id' in request.GET:
        try:
            city = RoadNetwork.objects.get(id=request.GET['city'])
            traj = Trajectory.objects.get(id=request.GET['id'])
            transition_prob = json.loads(HmmTransitionTable.objects.get(city=city, traj=traj).table)
            beta = HmmTransitionTable.objects.get(city=city, traj=traj).beta
            return Response({
                "beta": beta,
                "prob": transition_prob
            })
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_hmm_path_by_traj(request):
    if 'city' in request.GET and 'id' in request.GET:
        try:
            city = RoadNetwork.objects.get(id=request.GET['city'])
            traj = Trajectory.objects.get(id=request.GET['id'])
            path = HmmPath.objects.get(city=city, traj=traj).path
            return Response(PathSerializer(path).data)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_hmm_path_index_by_traj(request):
    if 'city' in request.GET and 'id' in request.GET:
        try:
            city = RoadNetwork.objects.get(id=request.GET['city'])
            traj = Trajectory.objects.get(id=request.GET['id'])
            hmm_path_index = json.loads(HmmPathIndex.objects.get(city=city, traj=traj).index)
            return Response(hmm_path_index)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_history_by_traj(request):
    if 'id' in request.GET and 'uid' in request.GET:
        try:
            traj = Trajectory.objects.get(id=request.GET['id'])
            user = Account.objects.get(id=request.GET['uid'])
            history = UserActionHistory.objects.get(user=user, traj=traj)
            action_list = []
            for action in history.action.all():
                action_list.append(action.__str__())
            return Response(action_list)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def remove_history_by_user(request):
    if 'id' in request.GET and 'uid' in request.GET:
        traj = Trajectory.objects.get(id=request.GET['id'])
        user = Account.objects.get(id=request.GET['uid'])
        history = UserActionHistory.objects.get(user=user, traj=traj)
        for action in history.action.all():
            action.delete()
        history.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
