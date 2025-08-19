from rest_framework import serializers
from my_app.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'read']
        read_only_fields = ['id', 'message', 'created_at']

