from events.views import book_seats,cancel_booking
from django.urls import path


urlpatterns = [
    path('book/<int:eventId>/', book_seats, name='book_seats'),
    path('cancel/<int:bookingId>/', cancel_booking, name='cancel_booking'),
]