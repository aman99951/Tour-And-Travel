# Generated by Django 5.1.4 on 2024-12-12 11:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0016_tourcity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the country.', max_length=100, unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='tourcity',
            name='country_name',
        ),
        migrations.AddField(
            model_name='tourcity',
            name='country',
            field=models.ForeignKey(default=1, help_text='Country of the city.', on_delete=django.db.models.deletion.CASCADE, related_name='tour_cities', to='travel.country'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the state.', max_length=100)),
                ('country', models.ForeignKey(help_text='Related country.', on_delete=django.db.models.deletion.CASCADE, related_name='states', to='travel.country')),
            ],
            options={
                'unique_together': {('name', 'country')},
            },
        ),
        migrations.AlterField(
            model_name='tourcity',
            name='state',
            field=models.ForeignKey(help_text='State of the city.', on_delete=django.db.models.deletion.CASCADE, related_name='tour_cities', to='travel.state'),
        ),
    ]
