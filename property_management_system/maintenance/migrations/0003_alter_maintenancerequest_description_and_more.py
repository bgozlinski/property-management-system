# Generated by Django 5.2.3 on 2025-06-29 09:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("maintenance", "0002_initial"),
        ("properties", "0001_initial"),
        ("users", "0003_landlord_tenant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="maintenancerequest",
            name="description",
            field=models.TextField(
                help_text="Describe the maintenance you want to perform."
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="property",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="maintenance_requests",
                to="properties.property",
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="status",
            field=models.IntegerField(
                choices=[
                    (1, "Pending"),
                    (2, "In Progress"),
                    (3, "Completed"),
                    (4, "Cancelled"),
                ],
                default=1,
                help_text="Current status of the maintenance request.",
            ),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="maintenance_requests",
                to="users.tenant",
            ),
        ),
    ]
