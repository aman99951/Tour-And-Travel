# Generated by Django 5.1.4 on 2024-12-24 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0030_cart_session_key_alter_cart_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
