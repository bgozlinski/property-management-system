from rest_framework import serializers
from .models import Reminder
from properties.models import Property
from properties.serializers import PropertySerializer


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for the Reminder model"""
    property_details = PropertySerializer(source='property', read_only=True)

    class Meta:
        model = Reminder
        fields = ['id', 'title', 'description', 'due_date', 'property', 'property_details']
        read_only_fields = ['id']

    def validate_due_date(self, value):
        """Validate that due_date is not in the past"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value