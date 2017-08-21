from rest_framework import serializers
from oqatt_core.models import User

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['contact', 'uid']