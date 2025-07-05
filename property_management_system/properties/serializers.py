from rest_framework import serializers
from .models import Property
from users.models import Landlord


class LandlordSerializer(serializers.ModelSerializer):
    """Serializer for the Landlord model (used for nested representation)"""

    class Meta:
        model = Landlord
        fields = ['id', 'name', 'contact_info']
        read_only_fields = fields  # Make all fields read-only when nested


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for the Property model"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    landlord_details = LandlordSerializer(source='landlord', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'address', 'city', 'postal_code', 'area_m2',
            'current_rent', 'additional_costs', 'status', 'status_display',
            'landlord', 'landlord_details'
        ]
        read_only_fields = ['id']

    def validate_area_m2(self, value):
        """Validate that area is positive"""
        if value <= 0:
            raise serializers.ValidationError("Area must be a positive number")
        return value

    def validate_current_rent(self, value):
        """Validate that rent is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Rent cannot be negative")
        return value

    def validate_additional_costs(self, value):
        """Validate that additional costs are non-negative"""
        if value < 0:
            raise serializers.ValidationError("Additional costs cannot be negative")
        return value