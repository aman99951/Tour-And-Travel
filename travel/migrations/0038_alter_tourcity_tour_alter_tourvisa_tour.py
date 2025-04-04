# Generated by Django 5.1.4 on 2025-01-06 15:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0037_remove_inquiry_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tourcity',
            name='tour',
            field=models.ForeignKey(help_text='Related tour.', on_delete=django.db.models.deletion.CASCADE, related_name='tour_cities', to='travel.tour'),
        ),
        migrations.AlterField(
            model_name='tourvisa',
            name='tour',
            field=models.ForeignKey(help_text='Related tour.', on_delete=django.db.models.deletion.CASCADE, related_name='visas', to='travel.tour'),
        ),
    ]
