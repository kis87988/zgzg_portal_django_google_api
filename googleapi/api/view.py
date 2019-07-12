import os
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_list_or_404, get_object_or_404

from googleapi.models import *
from googleapi.api.serializers import *
from datetime import datetime

from google.oauth2 import id_token
from google.auth.transport import requests
class UserAccessRecordListAPIView(APIView):
    def get(self,request,email):
        userAccessRecord = get_list_or_404(UserAccessRecord, email=email)
        serializer = UserAccessRecordSerializer(userAccessRecord, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserAccessRecordAPIView(APIView):
    def _checkVaildToken(self,request):
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(
            request.data["id_token"], req, os.getenv('GOOGLE_CLIEND_ID'))
        if id_info["iss"] != "accounts.google.com" or id_info["email"] != request.data["email"]:
            return False
        return True
    def _updateGoogleSheet(self,request):
        return True
    def _getGoogleSheetData(self,request):
        return True
    def get(self, request):
        userAccessRecord = UserAccessRecord.objects.all()
        serializer = UserAccessRecordSerializer(userAccessRecord, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self, request):
        request.data["record_time"] = datetime.now()
        if "SheetData" in request.data:
            request.data["action"] = "update profile"
        serializers = UserAccessRecordSerializer(data = request.data)
        if serializers.is_valid():
            serializers.save()
            if self._checkVaildToken(request):
                if "SheetData" in request.data:
                    self._updateGoogleSheet(request)
                self._getGoogleSheetData(request)
                return Response({"test": "this is test data"}, status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializers.errors,status=status.HTTP_400_BAD_REQUEST)
