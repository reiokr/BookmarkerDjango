# Generated by Django 4.0.4 on 2022-08-21 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_remove_customuser_email_verified'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
