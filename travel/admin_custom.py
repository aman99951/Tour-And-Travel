from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.apps import apps


class CustomAdminMixin:
    def admin2_link(self, obj=None):
        """Generates a clickable link to Admin2 for each row."""
        url = reverse('admin2:index')
        return format_html('<a href="{}" target="_blank">Go to Admin2</a>', url)

    admin2_link.short_description = "Go to Admin2"


def register_custom_admins(app_label='travel'):
    """Dynamically unregister existing admins and re-register with CustomAdminMixin."""
    travel_models = apps.get_app_config(app_label).get_models()

    for model in travel_models:
        if model in admin.site._registry:  # Check if model is already registered
            model_admin = admin.site._registry[model]
            admin.site.unregister(model)

            # Merge existing list_display with "admin2_link"
            existing_list_display = getattr(model_admin, "list_display", ())
            new_list_display = existing_list_display + \
                ("admin2_link",) if "admin2_link" not in existing_list_display else existing_list_display

            # Create a new admin class that includes CustomAdminMixin
            new_admin_class = type(
                f'Custom{model.__name__}Admin',
                (CustomAdminMixin, model_admin.__class__),  # Correct MRO order
                {"list_display": new_list_display}  # Update list display
            )

            admin.site.register(model, new_admin_class)
