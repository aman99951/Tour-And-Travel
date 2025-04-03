from django.contrib.admin import AdminSite
from django.contrib import admin
from .models import (
    Cart, CartItem, Inquiry, Order, OrderItem, Invoice,
    Ticket, ChatRequest, ChatMessage, ProblemRequest, Agent
)

# ✅ Create Custom Admin Site


class SecondAdminSite(AdminSite):
    site_header = "Second Admin Dashboard"
    site_title = "Second Admin"
    index_title = "Welcome to the Second Admin Panel"

    # ✅ Set the correct template
    site_url = None  # Optional: Hide "View Site" link
    index_template = "admin2/index.html"  # Use the new template


# ✅ Initialize Second Admin Site
second_admin_site = SecondAdminSite(name='admin2')

# ✅ Register Models in Second Admin
second_admin_site.register(Cart)
second_admin_site.register(CartItem)
second_admin_site.register(Inquiry)
second_admin_site.register(Order)
second_admin_site.register(OrderItem)
second_admin_site.register(Invoice)
second_admin_site.register(Ticket)
second_admin_site.register(ChatRequest)
second_admin_site.register(ChatMessage)
second_admin_site.register(ProblemRequest)
second_admin_site.register(Agent)
