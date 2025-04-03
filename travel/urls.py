from .views import InquiryViewSet
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from django.urls import path
from .views import get_tour_type, TourDetailViewSet
from . import views
from rest_framework.routers import DefaultRouter

# Create a single router
router = DefaultRouter()

# Register both viewsets
router.register(r'tours', TourDetailViewSet)
router.register(r'inquiries', InquiryViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/api/tour/<int:tour_id>/type/', get_tour_type, name='tour_type'),
    path('tour-home/', views.tour_home, name='tour_home'),
    path('tour/<int:pk>/', views.view_tour, name='view_tour'),

    path("add-to-cart/<int:tour_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path('cart/remove/<int:item_id>/',
         views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:item_id>/',
         views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/',
         views.decrease_quantity, name='decrease_quantity'),

    path('checkout/', views.checkout, name='checkout'),
    path('order/confirmation/<int:order_id>/',
         views.order_confirmation, name='order_confirmation'),
    path('profile/', views.profile_view, name='profile_view'),

    path('orders/', views.order_page, name='order_page'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    #  path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/', views.invoice_page, name='invoice_page'),

    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('list/', views.ticket_list, name='ticket_list'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('ticket/<int:ticket_id>/chat/',
         views.TicketChatView.as_view(), name='ticket-chat'),
    path('chat-request/', views.user_chat_request_view, name='user_chat_request'),
    path('agent-requests/', views.agent_chat_requests_view,
         name='agent_chat_requests'),
    path('chat-session/<int:chat_request_id>/',
         views.user_chat_session_view, name='user_chat_session'),
    path('agent-chat-session/<int:chat_request_id>/',
         views.agent_chat_session_view, name='agent_chat_session'),
    path('toggle-status/', views.agent_toggle_status, name='agent_toggle_status'),

    path('submit-problem/', views.user_chat_request_view,
         name='submit_problem_description'),
    path('agent/login/', views.agent_login_view, name='agent_login'),
    path('agent/logout/', views.agent_logout_view, name='agent_logout'),
    path('api/', include(router.urls)),


    path("payment/razorpay/", views.razorpay_payment, name="razorpay_payment"),
    path('payment/paytm/', views.paytm_payment, name='paytm_payment'),

    # URL for handling Paytm payment success
    path("payment/razorpay/success/",
         views.payment_success, name="payment_success"),
    path('payment/paytm/success/', views.paytm_payment_success,
         name='paytm_payment_success'),
    path('advance-payment/', views.advance_payment, name='advance_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),

    path('phonepe/', views.phonepe_payment, name='phonepe_payment'),

    # Payment callback after the transaction
    path('callback/', views.payment_callback, name='callback'),

]
