from django.db import models


class Point(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()

    def __str__(self):
        return "(" + str(self.lat) + "," + str(self.lng) + ")"


class SampleMeta(models.Model):
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return str(self.key) + ": " + str(self.value)


class Sample(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    p = models.ForeignKey(Point)
    t = models.DateTimeField()
    speed = models.IntegerField(null=True)
    angle = models.IntegerField(null=True)
    occupy = models.IntegerField(null=True)
    meta = models.ManyToManyField(SampleMeta)
    src = models.IntegerField(null=True)

    def __str__(self):
        return self.id


class Intersection(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    p = models.ForeignKey(Point, null=True)

    def __str__(self):
        return self.id


class Road(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255, null=True)
    type = models.IntegerField(null=True)
    length = models.IntegerField(null=True)
    speed = models.IntegerField(null=True)
    p = models.ManyToManyField(Point)
    intersection = models.ManyToManyField(Intersection)

    def __str__(self):
        return self.id

    def point_location(self, p):
        all_p = list(self.p.all())
        for i in range(len(all_p) - 1):
            p1 = all_p[i]
            p2 = all_p[i + 1]
            if min(p1.lat, p2.lat) <= p.lat <= max(p1.lat, p2.lat) or min(p1.lng, p2.lng) <= p.lng <= max(p1.lng, p2.lng):
                return i
        return None


class Trace(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    p = models.ManyToManyField(Sample)

    def __str__(self):
        return self.id


class PathFragment(models.Model):
    road = models.ForeignKey(Road)
    p = models.TextField(max_length=65535, null=True)

    def __str__(self):
        return str(self.road)


class Path(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    road = models.ManyToManyField(PathFragment)

    def __str__(self):
        return self.id


class Trajectory(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    taxi = models.CharField(max_length=255)
    trace = models.ForeignKey(Trace, null=True)
    path = models.ForeignKey(Path, null=True)

    def __str__(self):
        return self.id


class Rect(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()

    def __str__(self):
        return "(" + str(self.lat) + "," + str(self.lng) + "," + str(self.height) + "," + str(self.width) + ")"

    def contains_road(self, road):
        for p in list(road.p.all()):
            if self.contains_road_point(p):
                return True
        return False

    def contains_road_point(self, p):
        if self.lng <= p.lng < self.lng + self.width and self.lat <= p.lat < self.lat + self.height:
            return True
        else:
            return False


class GridCell(models.Model):
    # Actual ID of the grid cell (lat count, lng count)
    lat_id = models.IntegerField()
    lng_id = models.IntegerField()
    # Bounding box of the girid cell
    area = models.ForeignKey(Rect)
    roads = models.ManyToManyField(Road)
    intersections = models.ManyToManyField(Intersection)

    def __str__(self):
        return "(" + str(self.lat_id) + "," + str(self.lng_id) + ")"


class RoadNetwork(models.Model):
    city = models.CharField(max_length=32, unique=True)
    roads = models.ManyToManyField(Road)
    intersections = models.ManyToManyField(Intersection)
    grid_cells = models.ManyToManyField(GridCell)
    grid_lat_count = models.IntegerField(null=True)
    grid_lng_count = models.IntegerField(null=True)
    pmin = models.ForeignKey(Point, related_name="pmin", null=True)
    pmax = models.ForeignKey(Point, related_name="pmax", null=True)
    graph = models.CharField(max_length=10485760, null=True)

    def __str__(self):
        return self.city
