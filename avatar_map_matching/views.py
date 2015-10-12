from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from avatar_core.serializers import *
from common import *
from hmm import *
from models import *


@api_view(['GET'])
def find_candidate_road_by_p(request):
    if 'city' in request.GET and 'lat' in request.GET and 'lng' in request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
<<<<<<< HEAD
        p = Point(lat=float(request.GET['lat']), lng=float(request.GET['lng']))
        dist = 500.0
        if 'dist' in request.GET:
            dist = float(request.GET['dist'])
        candidate_rids = []
        candidates = find_candidates_from_road(city, p)
        for candidate in candidates:
            if candidate["dist"] < dist:
                candidate_rids.append(candidate["rid"])
            else:
                break
=======
	p = Point(lat=float(request.GET['lat']), lng=float(request.GET['lng']))
	dist = 500.0
	if 'dist' in request.GET:
	    dist = float(request.GET['dist'])
	candidate_rids = []
	candidates = find_candidates_from_road(city, p)
	for candidate in candidates:
	    if candidate["dist"] < dist:
		candidate_rids.append(candidate["rid"])
	    else:
		break
>>>>>>> b562233098ac8e62c4e170769207445a853b5f6a
        return Response(candidate_rids)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def map_matching(request):
    if 'city' in request.GET and 'id' in request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
        hmm = HmmMapMatching()
        hmm_result = hmm.perform_map_matching(city, traj.trace, candidate_rank)
<<<<<<< HEAD
        path = hmm_result['path']
        traj.path = path
        traj.save()
        print hmm_result['transition_prob'][len(hmm_result['transition_prob']) - 1]
        try:
            table = HmmEmissionTable.objects.get(city=city, traj=traj)
            table.delete()
        except ObjectDoesNotExist:
            pass
        emission_2d = hmm_result['emission_prob']
        emission_1d = []
        for prob in emission_2d:
            prob_list = ','.join(map(str, prob))
            emission_1d.append(prob_list)
        emission_prob = ';'.join(emission_1d)
        emission_table = HmmEmissionTable(city=city, traj=traj, table=emission_prob)
        emission_table.save()
        try:
            table = HmmTransitionTable.objects.get(city=city, traj=traj)
            table.delete()
        except ObjectDoesNotExist:
            pass
        transition_3d = hmm_result['transition_prob']
        transition_1d = []
        for prob in transition_3d:
            transition_2d = []
            for p in prob:
                p_list = ':'.join(map(str, p))
                transition_2d.append(p_list)
            prob_list = ','.join(transition_2d)
            transition_1d.append(prob_list)
        transition_prob = ';'.join(transition_1d)
        transition_src = transition_prob + ";" + str(hmm_result['beta'])
        transition_table = HmmTransitionTable(city=city, traj=traj, table=transition_src)
        transition_table.save()
        return Response(TrajectorySerializer(traj).data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def reperform_map_matching(request):
    if 'city' in request.GET and 'id' in request.GET and 'pid' in request.GET and 'rid' in request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
        # Find the index of the query sample in the trajectory
        sample_set = traj.trace.p.all()
        p_index = 16777215
        for i in range(len(sample_set)):
            if sample_set[i].id == request.GET['pid']:
                p_index = i
        # Construct the probability tables generated by previous map matching
        emission_str = HmmEmissionTable.objects.get(city=city, traj=traj).table
        transition_str = HmmTransitionTable.objects.get(city=city, traj=traj).table
        emission_prob = []
        transition_prob = []
        for prob in emission_str.split(';'):
            emission_1d = []
            for p in prob.split(','):
                emission_1d.append(float(p))
            emission_prob.append(emission_1d)
        transition_set = transition_str.split(';')
        beta = float(transition_set[len(transition_set) - 1])
        for i in range(len(transition_set) - 1):
            transition_2d = []
            for p in transition_set[i].split(','):
                transition_1d = []
                for record in p.split(':'):
                    transition_1d.append(float(record))
                transition_2d.append(transition_1d)
            transition_prob.append(transition_2d)
        hmm = HmmMapMatching()
        hmm.emission_prob = emission_prob
        hmm.transition_prob = transition_prob
        hmm_result = hmm.reperform_map_matching(city, traj.trace, candidate_rank, p_index, request.GET['rid'], beta)
=======
>>>>>>> b562233098ac8e62c4e170769207445a853b5f6a
        path = hmm_result['path']
        traj.path = path
        traj.save()
	print hmm_result['transition_prob'][len(hmm_result['transition_prob']) - 1]
	try:
	    table = HmmEmissionTable.objects.get(city=city, traj=traj)
	    table.delete()
	except ObjectDoesNotExist:
	    pass
	emission_2d = hmm_result['emission_prob']
	emission_1d = []
	for prob in emission_2d:
	    prob_list = ','.join(map(str, prob))
	    emission_1d.append(prob_list)
	emission_prob = ';'.join(emission_1d)
	emission_table = HmmEmissionTable(city=city, traj=traj, table=emission_prob)
	emission_table.save()
	try:
	    table = HmmTransitionTable.objects.get(city=city, traj=traj)
	    table.delete()
	except ObjectDoesNotExist:
	    pass
	transition_3d = hmm_result['transition_prob']
	transition_1d = []
	for prob in transition_3d:
	    transition_2d = []
	    for p in prob:
		p_list = ':'.join(map(str, p))
		transition_2d.append(p_list)
	    prob_list = ','.join(transition_2d)
	    transition_1d.append(prob_list)
	transition_prob = ';'.join(transition_1d)
	transition_src = transition_prob + ";" + str(hmm_result['beta'])
	transition_table = HmmTransitionTable(city=city, traj=traj, table=transition_src)
	transition_table.save()
        return Response(TrajectorySerializer(traj).data)
#	return Response(transition_table.table)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def reperform_map_matching(request):
    if 'city' in request.GET and 'id' in request.GET and 'pid' in request.GET and 'rid' in  request.GET:
        city = RoadNetwork.objects.get(id=request.GET['city'])
        candidate_rank = 10
        if 'rank' in request.GET:
            candidate_rank = int(request.GET['rank'])
        traj = Trajectory.objects.get(id=request.GET['id'])
	# Find the index of the query sample in the trajectory
	sample_set = traj.trace.p.all()
	p_index = 16777215
	for i in range(len(sample_set)):
	    if sample_set[i].id == request.GET['pid']:
		p_index = i
	# Construct the probability tables generated by previous map matching
	emission_str = HmmEmissionTable.objects.get(city=city, traj=traj).table
	transition_str = HmmTransitionTable.objects.get(city=city, traj=traj).table
	emission_prob = []
	transition_prob = []
	for prob in emission_str.split(';'):
	    emission_1d = []
	    for p in prob.split(','):
		emission_1d.append(float(p))
	    emission_prob.append(emission_1d)
	transition_set = transition_str.split(';')
	beta = float(transition_set[len(transition_set) - 1])
	for i in range(len(transition_set) - 1):
	    transition_2d = []
	    for p in transition_set[i].split(','):
		transition_1d = []
		for record in p.split(':'):
		    transition_1d.append(float(record))
		transition_2d.append(transition_1d)
	    transition_prob.append(transition_2d)
	hmm = HmmMapMatching()
	hmm.emission_prob = emission_prob
	hmm.transition_prob = transition_prob
        hmm_result = hmm.reperform_map_matching(city, traj.trace, candidate_rank, p_index, request.GET['rid'], beta)
        path = hmm_result['path']
        traj.path = path
        traj.save()
	return Response(TrajectorySerializer(traj).data)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
