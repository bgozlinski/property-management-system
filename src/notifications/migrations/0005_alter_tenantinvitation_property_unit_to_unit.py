# Generated manually to switch TenantInvitation.property_unit FK from Property to Unit
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0002_building_unit_equipment_meter_meterreading"),
        ("notifications", "0004_reminder_unit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenantinvitation",
            name="property_unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="properties.unit",
            ),
        ),
    ]
