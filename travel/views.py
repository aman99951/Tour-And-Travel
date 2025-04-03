from django.http import HttpResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import base64
import hashlib
import datetime
import uuid
from .forms import *
from paytmchecksum import PaytmChecksum
import paytmchecksum
import random
from django.urls import reverse
import json
from django.conf import settings
import razorpay
from .models import Tour, TourDetail, Price, TourHotel
from .serializers import TourSerializer, TourDetailSerializer, PriceSerializer, TourHotelSerializer
from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import InquirySerializer, TourSerializer
from .models import Inquiry
from rest_framework.viewsets import ModelViewSet
from .models import City  # Import the City model if not already imported
from django.db import IntegrityError, transaction
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import Tour, TourCategory
from django.http import JsonResponse
from django.shortcuts import render, redirect
from travel.forms import UserProfileForm, UserProfileForm2, TicketReplyForm, TicketForm
from django.contrib import messages
from .models import Cart, CartItem, Price, TourPhoto, Inquiry, Order, OrderItem, UserProfile, Invoice, TicketAgent, Ticket, TicketReply, ChatMessage, ChatRequest, Agent, ProblemRequest, City
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from travel.decorators import my_login_required, agent_required
# Create your views here.


def home(request):
    return render(request, 'tour/home.html')


def signup(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Check if passwords match
            password = form.cleaned_data.get('password')
            confirm_password = form.cleaned_data.get('confirm_password')
            if password != confirm_password:
                form.add_error('confirm_password', 'Passwords do not match.')
            else:
                form.save()
                messages.success(request, "Signup successful!")
                return redirect('signin')
    else:
        form = UserProfileForm()

    return render(request, 'tour/signup.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # After login, merge carts if necessary
            merge_carts(request, user)
            messages.success(request, "Signin successful!")
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'tour/signin.html', {'error_message': 'Invalid email or password.'})
    return render(request, 'tour/signin.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def get_tour_type(request, tour_id):
    try:
        tour = Tour.objects.get(id=tour_id)
        return JsonResponse({
            'is_fixed_departure': tour.is_fixed_departure
        })
    except Tour.DoesNotExist:
        return JsonResponse({'error': 'Tour not found'}, status=404)

from django.db.models import Count, Q, F, DecimalField, Value, ExpressionWrapper
from django.db.models.functions import Least, Coalesce
def tour_home(request):
    # Retrieve categories with the count of active tours
    categories = TourCategory.objects.annotate(
        product_count=Count('tours', filter=Q(tours__active=True))
    )

    # Get selected categories and filters
    selected_categories = request.GET.getlist('category')
    selected_filter = request.GET.get('filter', '4')  # Default filter value
    filter_type = request.GET.get('filter_type', 'days')  # Default to 'days'
    number = request.GET.get('number')

    # Base queryset for active tours
    tours = Tour.objects.filter(active=True)

    # Apply category filtering
    if selected_categories:
        tours = tours.filter(category__id__in=selected_categories)

    # Apply specific filters
    if selected_filter == '1':  # Featured tours
        tours = tours.filter(feature=True)
    elif selected_filter == '2':  # New arrivals
        tours = tours.filter(new_arrival=True)
    elif selected_filter == '3':  # Clearance sale
        tours = tours.filter(clearance_sale=True)

    # Apply days or nights filter
    if filter_type == 'days' and number:
        tours = tours.filter(number_of_days=number)
    elif filter_type == 'nights' and number:
        tours = tours.filter(number_of_nights=number)

    # Annotate tours with minimum price across multiple fields while handling NULL values
    tours = tours.annotate(
        min_price=Least(
            Coalesce(ExpressionWrapper(F('prices__adult_price'), output_field=DecimalField()), Value(9999999, output_field=DecimalField())),
            Coalesce(ExpressionWrapper(F('prices__twin_sharing_price'), output_field=DecimalField()), Value(9999999, output_field=DecimalField())),
            Coalesce(ExpressionWrapper(F('prices__extra_adult_price'), output_field=DecimalField()), Value(9999999, output_field=DecimalField()))
        )
    )
    # Pagination
    paginator = Paginator(tours, 15)  # Show 15 tours per page
    page_number = request.GET.get('page')
    tours_page = paginator.get_page(page_number)

    # Pass data to the template
    return render(request, 'tour-home/tourhome.html', {
        'tours': tours_page,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_filter': selected_filter,
        'filter_type': filter_type,
        'number': number,
    })

def view_tour(request, pk):
    # Get the tour object based on the primary key
    tour = get_object_or_404(Tour, pk=pk)

    if request.method == "POST":
        # Handle the inquiry form submission
        if 'send_inquiry' in request.POST:
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            message = request.POST.get('message')

            # Ensure the user is logged in before submitting the inquiry
            if not request.user.is_authenticated:
                messages.error(
                    request, "You must be logged in to submit an inquiry.")
                return redirect('view_tour', pk=pk)

            # Create the inquiry object without the city
            try:
                Inquiry.objects.create(
                    user=request.user,
                    tour=tour,
                    from_date=from_date,
                    to_date=to_date,
                    message=message,
                )
                messages.success(
                    request, "Your inquiry has been successfully sent! We'll contact you shortly.")
            except Exception as e:
                messages.error(
                    request, f"An error occurred while sending your inquiry: {e}")

    # Render the tour detail page with the form for inquiries
    return render(request, 'tour-home/tour_detail.html', {'tour': tour})


# Get a logger instance
logger = logging.getLogger(__name__)


def merge_carts(request, user):
    """
    Merges the guest cart into the authenticated user's cart after login.
    """
    session_key = request.session.session_key
    if not session_key:
        return

    # Get the session-based cart (guest cart)
    session_cart = Cart.objects.filter(
        session_key=session_key, user=None).first()

    if session_cart:
        # Get or create the user's cart
        user_cart, created = Cart.objects.get_or_create(user=user)

        # Merge items from the session cart into the user's cart
        for item in session_cart.items.all():
            # Check if the item already exists in the user's cart
            user_cart_item = user_cart.items.filter(
                variant=item.variant).first()
            if user_cart_item:
                # If the item already exists, update the quantity
                user_cart_item.quantity += item.quantity
                user_cart_item.total_price = user_cart_item.quantity * \
                    user_cart_item.variant.price_usd
                user_cart_item.save()
            else:
                # Add new item to the user's cart
                item.cart = user_cart
                item.save()

        # Delete the session cart after merging
        session_cart.delete()


def view_cart(request):
    if request.user.is_authenticated:
        # If the user is authenticated, fetch their cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        logger.debug(f"Authenticated user cart: {cart.id}")

        # Merge session cart if it exists (only for the first time login)
        session_key = request.session.session_key
        if session_key:
            logger.debug(
                f"Session found for user {request.user.id}, merging carts.")
            merge_carts(request, request.user)
    else:
        # If the user is not authenticated, use session-based cart
        session_key = request.session.session_key
        if not session_key:
            request.session.create()  # Ensure the session key is created
            session_key = request.session.session_key
        logger.debug(f"Session key created for guest user: {session_key}")

        # Create or get a cart for the session-based user (guest user)
        cart, created = Cart.objects.get_or_create(
            session_key=session_key, user=None)

    # Fetch cart items from the cart
    cart_items = cart.items.all()

    if not cart_items:
        logger.debug("No cart items found for this cart.")
    else:
        logger.debug(f"Cart items found: {cart_items.count()} items.")

    # Fetch the tour photos for each cart item (optional, for display purposes)
    for item in cart_items:
        item.tour_photo = TourPhoto.objects.filter(tour=item.tour).first()

    # Calculate total price
    total_price = sum(
        (item.adult_price or 0) * item.quantity +
        (item.twin_sharing_price or 0) * item.quantity
        for item in cart_items
    )

    logger.debug(f"Total price calculated for cart {cart.id}: {total_price}")

    # Pass cart items and total price to the context for rendering
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'quantity_options': range(1, 11),
    }

    return render(request, 'cart/view_cart.html', context)


def add_to_cart(request, tour_id):
    if request.method == "POST":
        # Get selected tour and price
        tour = get_object_or_404(Tour, id=tour_id)
        price = get_object_or_404(Price, id=request.POST.get('price_id'))

        # Get the selected price option from the POST request
        selected_option = request.POST.get('price_option')

        # Check if the selected price option is valid and retrieve the value
        price_value = getattr(price, selected_option, None)

        if not price_value:
            # Handle invalid price option or redirect to cart
            return redirect('view_cart')

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Create or retrieve the cart for the authenticated user
            cart, created = Cart.objects.get_or_create(user=request.user)

            # Merge the session cart with user cart if the session exists
            session_key = request.session.session_key
            if session_key:
                # Merge the carts before adding a new item
                merge_carts(request, request.user)
        else:
            # For anonymous users, use session cart
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Create or retrieve the cart for the guest user using the session key
            cart, created = Cart.objects.get_or_create(
                session_key=session_key, user=None)

        # Get the quantity (default to 1 if not specified)
        quantity = int(request.POST.get('quantity', 1))

        # Add a new cart item with the selected price and quantity
        CartItem.objects.create(
            cart=cart,
            tour=tour,
            t_class=price.t_class,
            quantity=quantity,  # Set the quantity as per the user input
            adult_price=price.adult_price if selected_option == "adult_price" else None,
            twin_sharing_price=price.twin_sharing_price if selected_option == "twin_sharing_price" else None,
            extra_price=price.extra_adult_price if selected_option == "extra_adult_price" else None,
            validity_date_from=price.validity_date_from,
            validity_date_to=price.validity_date_to,
        )

        # Redirect to the cart view page after adding the item
        return redirect('view_cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)

    if item.cart.user == request.user:
        item.delete()

    return redirect('view_cart')


def increase_quantity(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('view_cart')


def decrease_quantity(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('view_cart')


@my_login_required
def order_confirmation(request, order_id):
    try:
        # Retrieve the order using the order ID
        order = Order.objects.get(id=order_id, user=request.user)
        order_items = order.items.all()  # Get all the items associated with this order
        total_price = order.total_price  # Get the total price from the order

        return render(request, 'order/order_confirmation.html', {
            'order': order,
            'order_items': order_items,
            'total_price': total_price
        })

    except Order.DoesNotExist:
        # If the order does not exist, return an error message
        return render(request, 'order/order_confirmation.html', {
            'error': "Order not found or you don't have permission to view this order."
        })


@my_login_required
def profile_view(request):
    # Get the user's profile
    try:
        profile, created = UserProfile.objects.get_or_create(
            email=request.user.email)
    except UserProfile.DoesNotExist:
        return redirect('home')  # Redirect if profile not found

    if request.method == 'POST':
        form = UserProfileForm2(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect after saving
    else:
        form = UserProfileForm2(instance=profile)

    return render(request, 'tour/profile.html', {'form': form, 'profile': profile})


@my_login_required
def order_page(request):
    # Get the orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'order/order_page.html', {'orders': orders})


@my_login_required
def order_detail(request, order_id):
    # Fetch the order object, if it exists
    order = get_object_or_404(Order, id=order_id)

    # Fetch the user profile associated with the current logged-in user
    user_profile = UserProfile.objects.get(email=request.user.email)

    # Pass the order object and user profile to the template
    return render(request, 'order/order_detail.html', {'order': order, 'user_profile': user_profile})


@my_login_required
def invoice_detail(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    return render(request, 'order/invoice_detail.html', {'invoice': invoice})


@my_login_required
def invoice_page(request):
    invoices = Invoice.objects.filter(order__user=request.user)
    return render(request, 'order/all_invoices.html', {'invoices': invoices})


@my_login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user  # Set user only if authenticated
            ticket.save()
            return redirect('ticket_list')
    else:
        form = TicketForm()
    return render(request, 'helpdesk/create_ticket.html', {'form': form})


@my_login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(
        user=request.user).prefetch_related('replies')
    return render(request, 'helpdesk/ticket_list.html', {'tickets': tickets})


@my_login_required
def ticket_detail(request, pk):
    # Get the ticket by ID
    ticket = get_object_or_404(Ticket, pk=pk)

    # Fetch all replies, ordering by creation time (oldest to newest)
    replies = ticket.replies.order_by('created_at')

    if request.method == 'POST':
        # Ensure the ticket is not closed before allowing a reply
        if ticket.status != 'Closed':
            form = TicketReplyForm(request.POST)
            if form.is_valid():
                reply = form.save(commit=False)
                reply.ticket = ticket

                # Check if the user is an agent
                try:
                    agent = TicketAgent.objects.get(user=request.user)
                    reply.agent = agent  # Assign as agent
                except TicketAgent.DoesNotExist:
                    reply.user = request.user  # Regular user reply

                reply.save()
                return redirect('ticket_detail', pk=ticket.pk)
        else:
            # If the ticket is closed, prevent reply submission
            error = 'This ticket is closed and cannot accept new messages.'
            form = TicketReplyForm()  # Reset the form
            return render(request, 'helpdesk/ticket_detail.html', {
                'ticket': ticket,
                'replies': replies,
                'form': form,
                'error': error,
            })
    else:
        form = TicketReplyForm()

    # Render the template with ticket and replies
    return render(request, 'helpdesk/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form,
    })


@method_decorator(login_required, name='dispatch')
class TicketChatView(View):
    def get(self, request, ticket_id):
        # Get the ticket
        ticket = get_object_or_404(Ticket, pk=ticket_id)

        # Fetch replies to the ticket, ordered by creation time
        replies = TicketReply.objects.filter(
            ticket=ticket).order_by('created_at')

        # Initialize the reply form
        form = TicketReplyForm()

        context = {
            'ticket': ticket,
            'replies': replies,
            'form': form,
        }
        return render(request, 'admin/ticket_chat.html', context)

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        form = TicketReplyForm(request.POST)

        if form.is_valid():
            new_reply = form.save(commit=False)
            new_reply.ticket = ticket

            # Check if the user is an agent
            try:
                agent = TicketAgent.objects.get(user=request.user)
                new_reply.agent = agent
            except TicketAgent.DoesNotExist:
                new_reply.user = request.user  # Regular user reply

            new_reply.save()
            return redirect('ticket-chat', ticket_id=ticket.id)
        else:
            # If form is invalid, return the ticket with existing replies and form errors
            replies = TicketReply.objects.filter(
                ticket=ticket).order_by('created_at')
            context = {'ticket': ticket, 'replies': replies, 'form': form}
            return render(request, 'admin/ticket_chat.html', context)


def user_chat_request_view(request):
    online_agents = Agent.objects.filter(is_online=True)

    if request.method == 'POST':
        if online_agents.exists():
            agent = online_agents.first()
            user = request.user if request.user.is_authenticated else None

            # Get guest information if the user is not authenticated
            guest_name = request.POST.get('name') if not user else None
            guest_email = request.POST.get('email') if not user else None
            guest_phone = request.POST.get('phone') if not user else None

            if agent:
                try:
                    with transaction.atomic():
                        # Create a chat request
                        chat_request = ChatRequest.objects.create(
                            user=user,
                            guest_name=guest_name,
                            guest_email=guest_email,
                            guest_phone=guest_phone,
                            agent=agent
                        )
                    return redirect('user_chat_session', chat_request_id=chat_request.id)
                except IntegrityError as e:
                    print(f"Error creating chat request: {e}")
                    messages.error(
                        request, "There was an error creating your chat request. Please try again later.")
                    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})
            else:
                messages.error(
                    request, "No available agent to handle your request.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

        else:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            problem_description = request.POST.get('problem_description')

            try:
                ProblemRequest.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    name=name,
                    email=email,
                    phone=phone,
                    problem_description=problem_description
                )
                return render(request, 'chat/thank_you.html')
            except IntegrityError as e:
                print(f"Error creating problem request: {e}")
                messages.error(
                    request, "There was an error submitting your problem. Please try again later.")
                return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})

    return render(request, 'chat/user_chat_request.html', {'online_agents': online_agents})


def agent_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate against the User model
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user is an agent
            try:
                agent = Agent.objects.get(username=username)
                # Log the agent in
                # Use the login function to set the user session
                login(request, user)
                request.session['agent_username'] = agent.username
                agent.set_online()  # Set the agent online
                # Redirect to agent chat requests
                return redirect('agent_chat_requests')
            except Agent.DoesNotExist:
                messages.error(request, "You are not authorized to log in.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin/agent_login.html')


@agent_required
def agent_logout_view(request):
    # Get the current agent from the request
    agent = Agent.objects.filter(username=request.user.username).first()

    # Check if the agent exists
    if agent:
        agent.set_offline()

    # Log out the agent
    logout(request)
    return redirect('agent_login')


@agent_required
def agent_chat_requests_view(request):
    # Get the agent associated with the logged-in session
    agent_username = request.session.get('agent_username')
    agent = get_object_or_404(Agent, username=agent_username)

    # Fetch chat requests for this agent that have not been accepted, ordered by timestamp (most recent first)
    chat_requests = ChatRequest.objects.filter(
        agent=agent, accepted=False).order_by('-timestamp')

    # Handle the acceptance of a chat request
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        chat_request = get_object_or_404(
            ChatRequest, id=request_id, agent=agent)
        chat_request.accepted = True
        chat_request.save()
        return redirect('agent_chat_session', chat_request_id=chat_request.id)

    return render(request, 'chat/agent_chat_requests.html', {'chat_requests': chat_requests})


def user_chat_session_view(request, chat_request_id):
    # Fetch the chat request object
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)

    # Handle AJAX requests for real-time message updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        messages = ChatMessage.objects.filter(
            session=chat_request).order_by('timestamp')
        return JsonResponse({
            "messages": [
                {
                    "sender": msg.sender.first_name if msg.sender else "Guest",
                    "message": msg.message,
                    "timestamp": msg.timestamp.strftime("%H:%M"),
                }
                for msg in messages
            ]
        })

    # Handle message sending when form is submitted
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            sender = request.user if request.user.is_authenticated else None
            ChatMessage.objects.create(
                session=chat_request, sender=sender, message=message_text)
            return redirect('user_chat_session', chat_request_id=chat_request.id)

    # Retrieve all messages for the chat session (for page load)
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')
    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        'user': request.user,  # Pass the user to template for identifying sender
    })


@agent_required
def agent_chat_session_view(request, chat_request_id):
    # Fetch the chat request object, ensuring it belongs to the logged-in agent
    chat_request = get_object_or_404(
        ChatRequest, id=chat_request_id, agent__username=request.user.username)

    # Handle AJAX requests for real-time message updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        messages = ChatMessage.objects.filter(
            session=chat_request).order_by('timestamp')
        return JsonResponse({
            "messages": [
                {
                    "sender": msg.sender.first_name if msg.sender else "Guest",
                    "message": msg.message,
                    "timestamp": msg.timestamp.strftime("%H:%M"),
                }
                for msg in messages
            ]
        })

    # Handle message sending when form is submitted
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Create a new chat message
            ChatMessage.objects.create(
                session=chat_request,
                sender=request.user,  # Assuming the agent is using the same User model
                message=message_text
            )
            return redirect('agent_chat_session', chat_request_id=chat_request.id)

    # Retrieve all messages for the chat session (for page load)
    messages = ChatMessage.objects.filter(
        session=chat_request).order_by('timestamp')

    return render(request, 'chat/chat_session.html', {
        'messages': messages,
        'chat_request_id': chat_request_id,
        # Pass the agent's username for display
        'agent_username': request.user.username
    })


@agent_required
def agent_toggle_status(request):
    agent = get_object_or_404(Agent, username=request.user.username)
    agent.is_online = not agent.is_online
    agent.save()
    return redirect('agent_chat_requests')


class InquiryViewSet(ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer


class TourDetailViewSet(viewsets.ModelViewSet):
    queryset = Tour.objects.all()  # Query to fetch all tours
    serializer_class = TourSerializer

# ✅ Razorpay Payment View


@my_login_required
def razorpay_payment(request):
    pending_order = request.session.get('pending_order')

    if not pending_order:
        messages.error(request, "No pending order found. Please try again.")
        # Redirect to checkout if session data is missing
        return redirect("checkout")

    razorpay_client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET)
    )

    razorpay_order = razorpay_client.order.create({
        "amount": int(pending_order["total_price"] * 100),
        "currency": "INR",
        "payment_capture": "1"
    })

    # Save order ID for verification
    request.session['razorpay_order_id'] = razorpay_order['id']

    return render(request, "payments/razorpay_payment.html", {
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })


@my_login_required
def payment_success(request):
    pending_order = request.session.get('pending_order')
    razorpay_order_id = request.session.get('razorpay_order_id')

    if not pending_order or not razorpay_order_id:
        messages.error(request, "Payment verification failed.")
        return redirect("checkout")

    # Create Order after payment success
    order = Order.objects.create(
        user=request.user,
        total_price=pending_order["total_price"],
        status="Paid"
    )

    # Create Order Items
    for item in pending_order["cart_items"]:
        OrderItem.objects.create(
            order=order,
            tour_id=item["tour_id"],
            t_class=item["t_class"],
            quantity=item["quantity"],
            adult_price=item["adult_price"],
            twin_sharing_price=item["twin_sharing_price"],
            extra_price=item["extra_price"]
        )

    # Create Invoice
    Invoice.objects.create(
        order=order,
        total_amount=pending_order["total_price"],
        status="Paid"
    )

    # Clear session
    del request.session['pending_order']
    del request.session['razorpay_order_id']

    messages.success(
        request, "Payment successful! Your order has been placed.")
    return redirect("order_confirmation")


@my_login_required
def paytm_payment(request):
    pending_order = request.session.get('pending_order')

    if not pending_order:
        messages.error(request, "No pending order found. Please try again.")
        return redirect("checkout")

    # Prepare Paytm parameters
    order_id = f"ORD{random.randint(100000, 999999)}"  # Unique Order ID
    txn_amount = pending_order["total_price"]
    user_email = request.user.email

    try:
        # Fetch the UserProfile based on email
        user_profile = UserProfile.objects.get(email=request.user.email)
        # Assuming mobile_number field is in UserProfile
        phone_number = user_profile.mobile_number
    except UserProfile.DoesNotExist:
        # If no UserProfile is found, show an error and redirect to checkout
        messages.error(
            request, "User profile not found. Please ensure your profile is complete.")
        return redirect("checkout")

    # Prepare Paytm parameters
    params = {
        'MID': settings.PAYTM_MID,
        'WEBSITE': settings.PAYTM_WEBSITE,
        'CHANNEL_ID': settings.PAYTM_CHANNEL_ID,
        'INDUSTRY_TYPE_ID': settings.PAYTM_INDUSTRY_TYPE_ID,
        'ORDER_ID': order_id,
        'CUST_ID': user_email,  # Unique customer ID
        'TXN_AMOUNT': str(txn_amount),  # Amount in string
        'EMAIL': user_email,
        'MOBILE_NO': phone_number,
        # URL for success callback
        'CALLBACK_URL': request.build_absolute_uri(reverse('paytm_payment_success'))
    }

    # Generate checksum for security
    paytm_params = params.copy()
    paytm_params['CHECKSUMHASH'] = PaytmChecksum.generate_checksum(
        paytm_params, settings.PAYTM_MERCHANT_KEY)

    # Save order ID and payment details in session
    request.session['paytm_order_id'] = order_id
    request.session['paytm_txn_amount'] = txn_amount

    return render(request, "payments/paytm_payment.html", {
        "paytm_params": paytm_params
    })


@my_login_required
def paytm_payment_success(request):
    paytm_order_id = request.session.get('paytm_order_id')
    paytm_txn_amount = request.session.get('paytm_txn_amount')

    if not paytm_order_id or not paytm_txn_amount:
        messages.error(request, "Payment verification failed.")
        return redirect("checkout")

    # Extract the Paytm response parameters
    paytm_response = request.POST.dict()
    paytm_checksum = paytm_response.pop('CHECKSUMHASH', None)

    # Verify checksum
    is_valid_checksum = paytmchecksum.verify_checksum(
        paytm_response, settings.PAYTM_MERCHANT_KEY, paytm_checksum)

    if is_valid_checksum and paytm_response.get('STATUS') == 'TXN_SUCCESS':
        # Payment was successful, create the order and invoice
        order = Order.objects.create(
            user=request.user,
            total_price=paytm_txn_amount,
            status="Paid",
            order_id=paytm_order_id
        )

        # Create Order Items
        for item in request.session['pending_order']['cart_items']:
            OrderItem.objects.create(
                order=order,
                tour_id=item["tour_id"],
                t_class=item["t_class"],
                quantity=item["quantity"],
                adult_price=item["adult_price"],
                twin_sharing_price=item["twin_sharing_price"],
                extra_price=item["extra_price"]
            )

        # Create Invoice
        Invoice.objects.create(
            order=order,
            total_amount=paytm_txn_amount,
            status="Paid"
        )

        # Clear session
        del request.session['pending_order']
        del request.session['paytm_order_id']
        del request.session['paytm_txn_amount']

        messages.success(
            request, "Payment successful! Your order has been placed.")
        return redirect("order_confirmation")

    else:
        messages.error(
            request, "Payment verification failed. Please try again.")
        return redirect("checkout")


razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))


def advance_payment(request):
    """ Handles Advance Payment with Razorpay and PhonePe """

    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(email=request.user.email)
            initial_data = {

                "mobile": user_profile.mobile_number,
                "email": user_profile.email,
            }
        except UserProfile.DoesNotExist:
            initial_data = {}
    else:
        initial_data = {}

    if request.method == "POST":
        form = AdvancePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)

            if request.user.is_authenticated:
                payment.user = request.user  # Link payment to logged-in user

            # Process Razorpay Payment
            if payment.payment_method == "razorpay":
                order_data = {
                    "amount": int(payment.amount * 100),  # Convert to paise
                    "currency": "INR",
                    "payment_capture": "1"
                }
                order = razorpay_client.order.create(order_data)
                payment.transaction_id = order["id"]
                payment.save()

                return render(request, "payments/razorpay_payment2.html", {"order": order, "payment": payment})

            # Redirect to PhonePe Payment
            elif payment.payment_method == "phonepe":
                phonepe_url = f"https://phonepe-payment-url.com?amount={payment.amount}&mobile={payment.mobile}"
                return redirect(phonepe_url)

    else:
        # Prefill form for logged-in users
        form = AdvancePaymentForm(initial=initial_data)

    return render(request, "payments/advance_payment.html", {"form": form})


def payment_success(request):
    """ Handles successful payment response """
    return JsonResponse({"status": "Payment Successful"})


@my_login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum([item.total_price() for item in cart_items])
    user_profile = UserProfile.objects.get(email=request.user.email)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        # Store order details in session (No Order is created yet)
        request.session['pending_order'] = {
            "total_price": float(total_price),  # Convert Decimal to float
            "cart_items": [
                {
                    "tour_id": item.tour.id,
                    "t_class": str(item.t_class) if isinstance(item.t_class, str) else item.t_class.id,
                    "quantity": item.quantity,
                    "adult_price": float(item.adult_price) if item.adult_price is not None else 0.0,
                    "twin_sharing_price": float(item.twin_sharing_price) if item.twin_sharing_price is not None else 0.0,
                }
                for item in cart_items
            ]
        }

        payment_redirects = {
            "razorpay": "razorpay_payment",
            "paytm": "paytm_payment",
            "cashfree": "cashfree_payment",
            "phonepe": "phonepe_payment",
        }

        if payment_method in payment_redirects:
            return redirect(reverse(payment_redirects[payment_method]))
        else:
            messages.error(request, "Invalid payment method selected.")

    return render(request, "order/checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price,
        "user_profile": user_profile
    })


logger = logging.getLogger('payment')


def generate_tran_id():
    """Generate a unique transaction ID"""
    uuid_part = str(uuid.uuid4()).split(
        '-')[0].upper()  # Get a part of the UUID
    now = datetime.datetime.now().strftime('%Y%m%d')
    return f"TRX{now}{uuid_part}"


def generate_checksum(data, salt_key, salt_index):
    """Generate checksum for the request"""
    checksum_str = data + '/pg/v1/pay' + salt_key
    checksum = hashlib.sha256(
        checksum_str.encode()).hexdigest() + '###' + salt_index
    return checksum


# Set up logger
logger = logging.getLogger(__name__)


@csrf_exempt
def phonepe_payment(request):
    """Handle payment initiation with PhonePe."""
    if request.method == "POST":
        # Retrieve the pending order details from the session
        pending_order = request.session.get('pending_order')
        if not pending_order:
            logger.error("No pending order found.")
            return HttpResponse("Error: No pending order found.", status=400)

        total_price = pending_order.get('total_price')
        if not total_price:
            logger.error("Total price is missing.")
            return HttpResponse("Error: Total price missing.", status=400)

        # Prepare the payment payload
        amount_in_paise = int(total_price * 100)  # Convert INR to paise

        callback_url = request.build_absolute_uri(
            '/callback/')  # Use direct 'callback' here
        payload = {
            "merchantId": settings.PHONEPE_MERCHANT_ID,
            "merchantTransactionId": generate_tran_id(),
            "merchantUserId": "USR1231",  # Replace with actual user ID
            "amount": amount_in_paise,
            "redirectUrl": callback_url,
            "redirectMode": "POST",
            "callbackUrl": callback_url,
            "mobileNumber": "9800278886",  # Example phone number
            "paymentInstrument": {
                "type": "PAY_PAGE",  # Ensure this is valid based on the PhonePe docs
            }
        }

        # Generate checksum
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        checksum = generate_checksum(
            data, settings.PHONEPE_MERCHANT_KEY, settings.SALT_INDEX)
        final_payload = {"request": data}

        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
        }

        # Log the request payload and headers for debugging purposes
        logger.info("Sending request to PhonePe API...")
        logger.info("Request payload: %s", json.dumps(final_payload))
        logger.info("Headers: %s", headers)

        # Send the request to PhonePe API
        try:
            response = requests.post(
                settings.PHONEPE_INITIATE_PAYMENT_URL + '/pg-sandbox/pg/v1/pay',
                headers=headers,
                json=final_payload
            )
            logger.info("Response status code: %d", response.status_code)
            logger.info("Raw response text: %s", response.text)

            # Check if the response is empty or invalid JSON
            if not response.text:
                logger.error("Empty response from PhonePe API.")
                return HttpResponse("Error: Empty response from payment gateway.", status=500)

            # Try parsing the response
            try:
                data = response.json()
                logger.info("PhonePe payment response: %s", data)

                # Check for success in the response
                if data.get('success'):
                    payment_url = data['data']['instrumentResponse']['redirectInfo']['url']
                    return redirect(payment_url)
                else:
                    logger.error("Payment creation failed: %s", data)
                    return HttpResponse("Payment creation failed. Please try again later.", status=500)

            except ValueError as e:
                logger.error("Error parsing response as JSON: %s", e)
                return HttpResponse("Error: Invalid response from payment gateway.", status=500)

        except requests.exceptions.RequestException as e:
            logger.error("Error initiating payment: %s", e)
            return HttpResponse("Error: Unable to initiate payment. Please try again later.", status=500)

    # If method is not POST, return an appropriate response.
    return HttpResponse("Invalid request method.", status=405)


@csrf_exempt
def payment_callback(request):
    """Handle the callback from PhonePe."""
    if request.method != 'POST':
        logger.error("Invalid request method: %s", request.method)
        return redirect('checkout')

    try:
        data = request.POST.dict()  # Convert QueryDict to a regular dictionary
        logger.info(data)

        if data.get('checksum') and data.get('code') == "PAYMENT_SUCCESS":
            return render(request, 'success.html')
        else:
            logger.info("Payment failed: %s", data)

    except Exception as e:
        logger.error("Error parsing callback data: %s", e)
