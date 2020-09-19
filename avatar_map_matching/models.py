from avatar_core.models import *
from avatar_user.models import *


class HmmEmissionTable(models.Model):
    city = models.ForeignKey(RoadNetwork, on_delete=models.CASCADE)
    traj = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    candidate = models.TextField(max_length=65535, null=True)
    table = models.TextField(max_length=65535, null=True)

    def __str__(self):
        return str(self.table)

    class Meta:
        unique_together = ("city", "traj")


class HmmTransitionTable(models.Model):
    city = models.ForeignKey(RoadNetwork, on_delete=models.CASCADE)
    traj = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    beta = models.FloatField(null=True)
    table = models.TextField(max_length=65535, null=True)

    def __str__(self):
        return str(self.table)

    class Meta:
        unique_together = ("city", "traj")


class HmmPath(models.Model):
    city = models.ForeignKey(RoadNetwork, on_delete=models.CASCADE)
    traj = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    path = models.ForeignKey(Path, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.path.id)

    class Meta:
        unique_together = ("city", "traj")


class HmmPathIndex(models.Model):
    city = models.ForeignKey(RoadNetwork, on_delete=models.CASCADE)
    traj = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    index = models.TextField(max_length=65535, null=True)

    def __str__(self):
        return str(self.index)

    class Meta:
        unique_together = ("city", "traj")


class Action(models.Model):
    point = models.ForeignKey(Sample, on_delete=models.CASCADE)
    road = models.ForeignKey(Road, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.point.id) + ":" + str(self.road.id)


class UserActionHistory(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    traj = models.ForeignKey(Trajectory, on_delete=models.CASCADE)
    action = models.ManyToManyField(Action)

    def __str__(self):
        return str(self.user.id) + "," + str(self.traj.id)

    class Meta:
        unique_together = ("user", "traj")
