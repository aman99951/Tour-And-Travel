from .admin_custom import register_custom_admins
from .forms import TourDetailAdminForm
from django import forms
from django.templatetags.static import static
from django.http import JsonResponse
from django.contrib import admin
from .models import UserProfile, Tour, City, TourCategory, TourType, TourTypeOption, Currency, Price, T_class, TourDetail, CustomField, TourPhoto, TourCity, State, Country, TourDate, TourHotel, Tourvisa, Cart, CartItem, Inquiry, Order, OrderItem, Invoice, Ticket, TicketAgent, TicketReply, Agent, ChatMessage, ChatRequest, ProblemRequest


register_custom_admins()


class TourPhotoInline(admin.TabularInline):
    model = TourPhoto
    extra = 1  # Allows adding multiple photos dynamically


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'mobile_number', 'title',
                    'city', 'country', 'company_city', 'company_country', 'agree_terms', 'over_18')
    search_fields = ('email', 'first_name', 'last_name',
                     'mobile_number', 'title')
    list_filter = ('title', 'country', 'company_country',
                   'agree_terms', 'over_18')
    ordering = ('-id',)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(TourCategory)
admin.site.register(TourType)
admin.site.register(Currency)
admin.site.register(City)


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'short_description', 'tour_type', 'type', 'category', 'number_of_nights', 'number_of_days',
        'currency', 'departure_city', 'feature', 'new_arrival', 'clearance_sale', 'active'
    )
    list_filter = ('tour_type', 'type', 'category', 'feature',
                   'new_arrival', 'clearance_sale', 'active')
    search_fields = ('code', 'short_description', 'departure_city')
    inlines = [TourPhotoInline]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/json/',
                 self.admin_site.admin_view(self.tour_json), name='tour_json'),
        ]
        return custom_urls + urls

    def tour_json(self, request, pk):
        from django.shortcuts import get_object_or_404
        tour = get_object_or_404(Tour, pk=pk)
        print("Tour Data:", tour)
        data = {
            'id': tour.id,
            'type': {
                'is_fixed_departure': tour.type.is_fixed_departure,
                'is_tour_package': tour.type.is_tour_package,
            },
        }
        return JsonResponse(data)


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = (
        'tour', 't_class', 'adult_price', 'twin_sharing_price', 'extra_adult_price',
        'infant_price', 'child_price', 'no_of_pax', 'validity_date_from', 'validity_date_to', 'active'
    )
    list_filter = ('tour', 't_class', 'active')
    search_fields = ('tour__code', 't_class')


admin.site.register(T_class)


class CustomFieldInline(admin.TabularInline):
    model = CustomField
    extra = 1  # Allows adding new rows dynamically in the admin


@admin.register(TourPhoto)
class TourPhotoAdmin(admin.ModelAdmin):
    list_display = ('tour', 'image')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country__name')
    list_filter = ('country',)


@admin.register(TourCity)
class TourCityAdmin(admin.ModelAdmin):
    list_display = ('tour', 'country', 'state', 'num_of_days', 'num_of_nights')
    search_fields = ('tour__name', 'country__name', 'state__name')
    list_filter = ('country',)


@admin.register(TourTypeOption)
class TourTypeOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',
                    'is_fixed_departure', 'is_tour_package')
    search_fields = ('name',)
    list_filter = ('is_fixed_departure', 'is_tour_package')


@admin.register(Tourvisa)
class TourVisaAdmin(admin.ModelAdmin):
    list_display = ('tour', 'name_of_country')


@admin.register(TourHotel)
class TourHotelAdmin(admin.ModelAdmin):
    list_display = ('tour', 'destination', 'hotel_name')
    search_fields = ('tour__code', 'destination', 'hotel_name')


class TourDateAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        """
        Dynamically adjust which fields are shown based on the tour's type.
        """
        if obj and obj.tour:  # If we are editing an existing TourDate object
            tour_type_option = obj.tour.type  # Get the selected TourTypeOption

            # If the tour has a fixed departure, only show the 'fixed_departure_date' field
            if tour_type_option.is_fixed_departure:
                return ['tour', 'fixed_departure_date']

            # If it's a tour package, show from_date and to_date
            elif tour_type_option.is_tour_package:
                return ['tour', 'from_date', 'to_date']

        # Default field order for new TourDate instance
        return super().get_fields(request, obj)

    def get_fieldsets(self, request, obj=None):
        """
        Dynamically adjust which fields are grouped together based on the tour's type.
        """
        if obj and obj.tour:  # If we are editing an existing TourDate object
            tour_type_option = obj.tour.type  # Get the selected TourTypeOption

            # If the tour is a fixed departure, only show fixed_departure_date in its own group
            if tour_type_option.is_fixed_departure:
                return [(None, {'fields': ['tour', 'fixed_departure_date']})]

            # If it's a tour package, show from_date and to_date in their own group
            elif tour_type_option.is_tour_package:
                return [(None, {'fields': ['tour', 'from_date', 'to_date']})]

        # Default fieldset
        return super().get_fieldsets(request, obj)

    class Media:
        # Include JavaScript to handle dynamic field visibility
        js = ('admin/js/tourdate_admin.js',)  # Path to your custom JS file


# Register the admin
admin.site.register(TourDate, TourDateAdmin)

# Define custom AdminSite class


class TourDetailAdmin(admin.ModelAdmin):
    list_display = ('tour',)
    search_fields = ('tour__code',)
    inlines = [CustomFieldInline]  # Add your inline models here if any

    class Media:
        css = {
            # Ensure this path matches your actual static file path
            'all': (static('admin/css/admin_custom.css'),)
        }

# ✅ CustomField Inline


class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ["label", "value"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assign custom ID for CKEditor
        self.fields["value"].widget.attrs["id"] = "id_value"


class CustomFieldInline(admin.TabularInline):
    model = CustomField
    extra = 0
    form = CustomFieldForm


class TourDetailAdmin(admin.ModelAdmin):
    form = TourDetailAdminForm
    inlines = [CustomFieldInline]

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields["itinerary"].widget.attrs["id"] = "id_itinerary"
        context["adminform"].form.fields["includes"].widget.attrs["id"] = "id_includes"
        context["adminform"].form.fields["excludes"].widget.attrs["id"] = "id_excludes"
        context["adminform"].form.fields["cancellation_policy"].widget.attrs["id"] = "id_cancellation_policy"
        context["adminform"].form.fields["notes"].widget.attrs["id"] = "id_notes"
        return super().render_change_form(request, context, *args, **kwargs)


admin.site.register(TourDetail, TourDetailAdmin)
