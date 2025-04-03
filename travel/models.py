import pycountry
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django_ckeditor_5.fields import CKEditor5Field
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    # Email, Password, Confirm Password, Mobile Number
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    confirm_password = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)

    # Mailing Address fields
    title_choices = [('Mr', 'Mr'), ('Mrs', 'Mrs')]
    title = models.CharField(
        max_length=10, choices=title_choices, default='MR')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    # Billing Address fields
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    country_of_passport = models.CharField(max_length=100)
    landline_number = models.CharField(max_length=15)

    # Company Address fields
    company_address = models.TextField(blank=True, null=True)
    company_city = models.CharField(max_length=100, blank=True, null=True)
    company_state = models.CharField(max_length=100, blank=True, null=True)
    company_postal_code = models.CharField(
        max_length=10, blank=True, null=True)
    company_country = models.CharField(max_length=100, blank=True, null=True)

    # Terms and Conditions
    agree_terms = models.BooleanField(default=False)
    over_18 = models.BooleanField(default=False)

    def __str__(self):
        return self.email

# Signal to create or update User when UserProfile is saved


@receiver(post_save, sender=UserProfile)
def create_or_update_user(sender, instance, created, **kwargs):
    if created:
        # Create a corresponding User instance
        user = User.objects.create_user(
            username=instance.email,
            email=instance.email,
            password=instance.password
        )
        user.first_name = instance.first_name
        user.last_name = instance.last_name
        user.save()
    else:
        # Update the existing User instance if the UserProfile is updated
        try:
            user = User.objects.get(username=instance.email)
            user.first_name = instance.first_name
            user.last_name = instance.last_name
            user.email = instance.email
            user.set_password(instance.password)  # Update password if changed
            user.save()
        except User.DoesNotExist:
            pass


class TourType(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            help_text="Name of the tour type (e.g., India, International).")

    def __str__(self):
        return self.name


class TourCategory(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            help_text="Name of the tour category.")

    def __str__(self):
        return self.name


class Currency(models.Model):
    name = models.CharField(
        max_length=100, help_text="Name of the currency (e.g., US Dollar, Indian Rupee).")

    def __str__(self):
        return self.name


class TourTypeOption(models.Model):
    name = models.CharField(
        max_length=150, unique=True, help_text="Type of the tour option (e.g., Fixed Departure or Tour Package)."
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of the tour type option."
    )
    is_fixed_departure = models.BooleanField(
        default=False, help_text="Indicates if this option is a Fixed Departure tour."
    )
    is_tour_package = models.BooleanField(
        default=False, help_text="Indicates if this option is a Tour Package."
    )

    def __str__(self):
        return self.name


class Tour(models.Model):
    code = models.CharField(max_length=50, unique=True,
                            default=uuid.uuid4, help_text="Unique code for the tour.")
    tour_type = models.ForeignKey(
        TourType, on_delete=models.CASCADE, related_name="tours", help_text="Type of the tour.")
    short_description = models.CharField(
        max_length=255, help_text="Short title or description of the tour.")
    type = models.ForeignKey(TourTypeOption, on_delete=models.CASCADE,
                             related_name="tours", help_text="Tour type option.")
    long_description = models.TextField(
        help_text="Detailed description of the tour.")
    category = models.ForeignKey(TourCategory, on_delete=models.CASCADE,
                                 related_name="tours", help_text="Category of the tour.")
    number_of_nights = models.PositiveIntegerField(
        help_text="Number of nights for the tour.")
    number_of_days = models.PositiveIntegerField(
        help_text="Number of days for the tour.")
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE,
                                 related_name="tours", help_text="Currency for pricing.")
    departure_city = models.CharField(
        max_length=100, help_text="City of departure.")
    feature = models.BooleanField(
        default=False, help_text="Mark as a featured tour.")
    new_arrival = models.BooleanField(
        default=False, help_text="Mark as a new arrival.")
    clearance_sale = models.BooleanField(
        default=False, help_text="Mark as a clearance sale.")
    active = models.BooleanField(default=True, help_text="Is the tour active?")

    def __str__(self):
        return f" {self.short_description} - {self.type}"


class TourDate(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="dates", help_text="Related tour."
    )
    fixed_departure_date = models.DateField(
        blank=True, null=True, help_text="Date for Fixed Departures."
    )
    from_date = models.DateField(
        blank=True, null=True, help_text="Start date for Tour Packages."
    )
    to_date = models.DateField(
        blank=True, null=True, help_text="End date for Tour Packages."
    )

    def clean(self):
        """
        Enforce rules:
        - Fixed Departure: only `fixed_departure_date` should be set.
        - Tour Package: only `from_date` and `to_date` should be set.
        """
        if self.fixed_departure_date and (self.from_date or self.to_date):
            raise ValidationError(
                "Fixed Departure tours should only have a 'fixed_departure_date', not 'from_date' or 'to_date'."
            )
        if not self.fixed_departure_date and not (self.from_date and self.to_date):
            raise ValidationError(
                "Tour Packages should have both 'from_date' and 'to_date'."
            )

    def __str__(self):
        if self.fixed_departure_date:
            return f"{self.tour.code} - Fixed Departure: {self.fixed_departure_date}"
        return f"{self.tour.code} - Tour Package: {self.from_date} to {self.to_date}"


class T_class(models.Model):
    name = models.CharField(
        max_length=100, help_text="Name of the t=class")

    def __str__(self):
        return self.name


class Price(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE,
                             related_name="prices", help_text="Related tour.")
    t_class = models.ForeignKey(T_class, on_delete=models.CASCADE,
                                related_name="tours", help_text=" name of the t-class")
    adult_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price for adults.")
    twin_sharing_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price for twin sharing.")
    extra_adult_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price for extra adults.")
    infant_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price for infants.")
    child_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price for children.")
    no_of_pax = models.PositiveIntegerField(help_text="Number of passengers.")
    validity_date_from = models.DateField(help_text="Validity start date.")
    validity_date_to = models.DateField(help_text="Validity end date.")
    active = models.BooleanField(
        default=True, help_text="Is the price active?")

    def get_minimum_price(self):
        return min(self.adult_price, self.twin_sharing_price, self.extra_adult_price)

    def __str__(self):
        return f"{self.t_class} - {self.tour.code}"


class TourDetail(models.Model):
    tour = models.OneToOneField(
        Tour, on_delete=models.CASCADE, related_name="details", help_text="Related tour."
    )
    itinerary = models.TextField(null=True, blank=True)  # Changed to TextField
    includes = models.TextField(null=True, blank=True)  # Changed to TextField
    excludes = models.TextField(null=True, blank=True)  # Changed to TextField
    cancellation_policy = models.TextField(
        null=True, blank=True)  # Changed to TextField
    notes = models.TextField(null=True, blank=True)  # Changed to TextField

    def __str__(self):
        return f"Tour Detail {self.id}"


class CustomField(models.Model):
    tour_detail = models.ForeignKey(
        TourDetail, on_delete=models.CASCADE, related_name="custom_fields")
    label = models.CharField(max_length=255)
    value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.label}: {self.value}"


class TourPhoto(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="photos", help_text="Related tour for the photo.")
    image = models.ImageField(upload_to="tour_photos/",
                              help_text="Upload tour photo.")

    def __str__(self):
        return f"Photo for {self.tour.code}"


def get_country_choices():
    """Fetch country names as choices for the dropdown."""
    return [(country.name, country.name) for country in pycountry.countries]


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, choices=get_country_choices(),
                            help_text="Name of the country.")

    def __str__(self):
        return self.name


def get_state_choices():
    """Fetch state names as choices (filtered later based on the country)."""
    return [(subdiv.name, subdiv.name) for subdiv in pycountry.subdivisions]


class State(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="states", help_text="Related country.")
    name = models.CharField(
        max_length=100, help_text="Name of the state.", choices=get_state_choices(),)

    class Meta:
        # Ensures state names are unique within a country
        unique_together = ('name', 'country')

    def __str__(self):
        return f"{self.name}, {self.country}"


class City(models.Model):
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="city", help_text="Related country.")
    name = models.CharField(
        max_length=100, help_text="Name of the state.")

    class Meta:
        # Ensures state names are unique within a country
        unique_together = ('name', 'state')

    def __str__(self):
        return f"{self.name} - {self.state}"


class TourCity(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="cities", help_text="Related tour.")
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="tour_cities", help_text="Country of the city.")
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="tour_cities", help_text="State of the city.")
    num_of_days = models.PositiveIntegerField(
        help_text="Number of days spent in the city.")
    num_of_nights = models.PositiveIntegerField(
        help_text="Number of nights spent in the city.")

    def __str__(self):
        return f"{self.state} ({self.num_of_days} Days, {self.num_of_nights} Nights)"


class Tourvisa(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="Visa", help_text="Related tour.")
    name_of_country = models.CharField(
        max_length=100, help_text="Name of the Visa Country.")

    def __str__(self):
        return f"{self.tour.code} visa of {self.name_of_country} "


class TourHotel(models.Model):
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="tour_hotels", help_text="Related tour."
    )
    t_class = models.ForeignKey(
        T_class, on_delete=models.CASCADE, related_name="t_class_hotel", help_text="T-class"
    )
    destination = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="Hotel_destination", help_text="T-class"
    )
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="Hotel_city", help_text="T-class"
    )
    hotel_name = models.CharField(
        max_length=255, help_text="Name of the hotel.")

    def __str__(self):
        return f"Hotel: {self.hotel_name} in {self.destination} for {self.tour.code}"


class Cart(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart ({self.user or self.session_key})"

    def total_price(self):
        """Calculate the total price of all items in the cart."""
        total = sum(item.total_price() for item in self.items.all())
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items"
    )
    tour = models.ForeignKey(
        'Tour', on_delete=models.CASCADE, related_name="cart_items"
    )
    t_class = models.ForeignKey(
        'T_class', on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    adult_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    twin_sharing_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    extra_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    validity_date_from = models.DateField()
    validity_date_to = models.DateField()

    def total_price(self):
        """Calculate the total price for this cart item based on the selected price."""
        if self.adult_price:
            return self.adult_price * self.quantity
        elif self.twin_sharing_price:
            return self.twin_sharing_price * self.quantity
        elif self.extra_price:
            return self.extra_price * self.quantity
        return 0.00


class Inquiry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Inquiry by {self.user} for {self.tour}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=STATUS_CHOICES,
                              default='Pending', max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the related invoice status if the order is marked as paid
        if self.status == 'Paid' and hasattr(self, 'invoice'):
            self.invoice.mark_as_paid()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items")
    tour = models.ForeignKey('Tour', on_delete=models.CASCADE)
    t_class = models.ForeignKey('T_class', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    adult_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    twin_sharing_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    extra_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    def total_price(self):
        """Calculate the total price for this order item based on the selected price."""
        if self.adult_price:
            return self.adult_price * self.quantity
        elif self.twin_sharing_price:
            return self.twin_sharing_price * self.quantity
        elif self.extra_price:
            return self.extra_price * self.quantity
        return 0.00

    def __str__(self):
        return f"{self.tour.short_description} in {self.t_class.name} for {self.order.user.username}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="invoice")
    invoice_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=STATUS_CHOICES,
                              default='Pending', max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Invoice {self.id} for Order {self.order.id}"

    def mark_as_paid(self):
        """Mark the invoice as paid."""
        self.status = 'Paid'
        self.save()

    def save(self, *args, **kwargs):
        # Calculate the total amount based on the sum of all order items
        total_amount = sum(item.total_price()
                           for item in self.order.items.all())
        self.total_amount = total_amount
        super().save(*args, **kwargs)


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=255)
    deparment = models.CharField(max_length=20, default='')
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='New')
    attachments = models.FileField(
        upload_to='tickets/attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

# Model to track agent availability


class TicketAgent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_agent = models.BooleanField(default=True)  # Ensure this is an agent

    def __str__(self):
        return f"Agent: {self.user.username}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name='replies', on_delete=models.CASCADE)
    agent = models.ForeignKey(TicketAgent, null=True, blank=True,
                              on_delete=models.SET_NULL)  # Use TicketAgent for agents
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.ticket.subject}"


class Agent(models.Model):
    username = models.CharField(
        max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)  # Store hashed password
    name = models.CharField(max_length=20, null=True, blank=True)
    phone = models.IntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_online(self):
        self.is_online = True
        self.save()

    def set_offline(self):
        self.is_online = False
        self.save()

    def save(self, *args, **kwargs):
        # If an Agent is being created or updated, create or update the corresponding User
        if self.username and self.password:
            # Check if a User already exists for this Agent
            user, created = User.objects.get_or_create(username=self.username)

            # If the user was just created, set the password and other details
            if created:
                # Hashes the password and sets it
                user.set_password(self.password)
            else:
                # Update the password if it has changed
                if not check_password(self.password, user.password):
                    user.set_password(self.password)

            # Update other user fields
            user.first_name = self.name or ''  # Optional: set first name
            user.save()

        super().save(*args, **kwargs)  # Call the parent class save method

    def __str__(self):
        return self.username


class ChatRequest(models.Model):
    user = models.ForeignKey(
        User, related_name='chat_requests', on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(
        Agent, related_name='chat_requests', on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=20, null=True, blank=True)
    guest_phone = models.IntegerField(null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Chat request from {self.user} to agent {self.agent}"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatRequest, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.message[:50]} to {self.sender}"


class ProblemRequest(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, default=1, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    problem_description = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Problem Request from {self.name} ({self.email})"


class AdvancePayment(models.Model):
    PAYMENT_METHODS = [
        ('razorpay', 'Razorpay'),
        ('phonepe', 'PhonePe'),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, default=1, null=True, blank=True)

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.amount} - {self.payment_status}"
