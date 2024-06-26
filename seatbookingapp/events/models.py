from django.db import models



#used sqlite itself we can change it to mysql but for now using sqlite


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    totalSeats = models.IntegerField()
    seatingChart = models.JSONField()  # This will store the seating chart as JSON

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seatsBooked = models.JSONField()  # This will store an array of seat identifiers
    isVIP = models.BooleanField(default=False)

class Waitlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
