from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import User, Event, Booking, Waitlist
import json

@csrf_exempt
def book_seats(request, eventId):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = get_object_or_404(User, id=data['userId'])
        event = get_object_or_404(Event, id=eventId)
        requested_seats = data['seatsRequested']
        is_vip = data.get('isVIP', False)
        
        available_seats = []
        booked_seats = json.loads(event.seatingChart)
        
        # Check and mark seats as booked
        for seat in requested_seats:
            for booked_seat in booked_seats:
                if (booked_seat['row'] == seat['row'] and 
                    booked_seat['column'] == seat['column'] and 
                    not booked_seat['is_booked']):
                    available_seats.append(seat)
                    booked_seat['is_booked'] = True
                    booked_seat['user_id'] = user.id
                    break
        
        if len(available_seats) == len(requested_seats):
            # All requested seats are available
            Booking.objects.create(user=user, event=event, seatsBooked=available_seats, isVIP=is_vip)
            event.seatingChart = json.dumps(booked_seats)
            event.save()
            return JsonResponse({'message': 'Booking successful', 'allocatedSeats': available_seats})
        else:
            if is_vip:
                # Handle VIP priority booking
                reallocated_seats = []
                for seat in requested_seats:
                    for booked_seat in booked_seats:
                        if (booked_seat['row'] == seat['row'] and 
                            booked_seat['column'] == seat['column']):
                            if booked_seat['user_id']:
                                # Move existing user to waitlist
                                existing_booking = get_object_or_404(Booking, user_id=booked_seat['user_id'], event=event)
                                Waitlist.objects.create(user=existing_booking.user, event=event)
                                existing_booking.delete()
                                # Send dummy email notification
                                print(f"Sent email to {existing_booking.user.email}")
                            reallocated_seats.append(seat)
                            booked_seat['is_booked'] = True
                            booked_seat['user_id'] = user.id
                            break
                if len(reallocated_seats) == len(requested_seats):
                    Booking.objects.create(user=user, event=event, seatsBooked=reallocated_seats, isVIP=is_vip)
                    event.seatingChart = json.dumps(booked_seats)
                    event.save()
                    return JsonResponse({'message': 'Booking successful with VIP reallocation', 'allocatedSeats': reallocated_seats})
            
            # Add to waitlist if seats are not available
            Waitlist.objects.create(user=user, event=event, timestamp=timezone.now())
            return JsonResponse({'message': 'Seats not available. Added to waitlist.'}, status=400)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def cancel_booking(request, bookingId):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=bookingId)
        event = booking.event
        booked_seats = json.loads(event.seatingChart)

        # Mark seats as available
        for seat in booking.seatsBooked:
            for booked_seat in booked_seats:
                if booked_seat['row'] == seat['row'] and booked_seat['column'] == seat['column']:
                    booked_seat['is_booked'] = False
                    booked_seat['user_id'] = None
                    break
        
        booking.delete()

        # Check waitlist and confirm seats for the first user in the waitlist
        waitlist = Waitlist.objects.filter(event=event).order_by('timestamp').first()
        if waitlist:
            waitlist_user = waitlist.user
            Waitlist.objects.filter(user=waitlist_user, event=event).delete()
            Booking.objects.create(user=waitlist_user, event=event, seatsBooked=booking.seatsBooked, isVIP=False)
            for seat in booking.seatsBooked:
                for booked_seat in booked_seats:
                    if booked_seat['row'] == seat['row'] and booked_seat['column'] == seat['column']:
                        booked_seat['is_booked'] = True
                        booked_seat['user_id'] = waitlist_user.id
                        break
            print(f"Sent email to {waitlist_user.email}")

        event.seatingChart = json.dumps(booked_seats)
        event.save()

        return JsonResponse({'message': 'Booking cancelled and seats reallocated'})

    return JsonResponse({'message': 'Invalid request method.'}, status=405)
