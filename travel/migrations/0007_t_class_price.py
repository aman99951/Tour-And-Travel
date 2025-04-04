# Generated by Django 5.1.4 on 2024-12-11 16:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0006_currency_tourcategory_tourtype_tourtypeoption_tour'),
    ]

    operations = [
        migrations.CreateModel(
            name='T_class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the t=class', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('adult_price', models.DecimalField(decimal_places=2, help_text='Price for adults.', max_digits=10)),
                ('twin_sharing_price', models.DecimalField(decimal_places=2, help_text='Price for twin sharing.', max_digits=10)),
                ('extra_adult_price', models.DecimalField(decimal_places=2, help_text='Price for extra adults.', max_digits=10)),
                ('infant_price', models.DecimalField(decimal_places=2, help_text='Price for infants.', max_digits=10)),
                ('child_price', models.DecimalField(decimal_places=2, help_text='Price for children.', max_digits=10)),
                ('no_of_pax', models.PositiveIntegerField(help_text='Number of passengers.')),
                ('validity_date_from', models.DateField(help_text='Validity start date.')),
                ('validity_date_to', models.DateField(help_text='Validity end date.')),
                ('active', models.BooleanField(default=True, help_text='Is the price active?')),
                ('tour', models.ForeignKey(help_text='Related tour.', on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='travel.tour')),
                ('t_class', models.ForeignKey(help_text=' name of the t-class', on_delete=django.db.models.deletion.CASCADE, related_name='tours', to='travel.t_class')),
            ],
        ),
    ]
