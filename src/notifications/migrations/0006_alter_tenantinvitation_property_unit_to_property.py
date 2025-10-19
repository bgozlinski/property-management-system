# Generated to switch TenantInvitation.property_unit FK back from Unit to Property
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0002_building_unit_equipment_meter_meterreading"),
        ("notifications", "0005_alter_tenantinvitation_property_unit_to_unit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenantinvitation",
            name="property_unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="properties.property",
            ),
        ),
    ]
