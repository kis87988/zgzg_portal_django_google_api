from rest_framework import serializers
from googleapi.models import *


class UserAccessRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccessRecord
        fields = "__all__"
