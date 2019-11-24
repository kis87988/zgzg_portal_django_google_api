import os
from pathlib import Path
import httplib2

from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_list_or_404, get_object_or_404
import logging

from googleapi.models import *
from googleapi.api.serializers import *
from datetime import datetime

from google.oauth2 import id_token, service_account
from google.auth.transport import requests
from apiclient import discovery

logger = logging.getLogger(__name__)


class UserAccessRecordListAPIView(APIView):
    def get(self, request, email):
        userAccessRecord = get_list_or_404(UserAccessRecord, email=email)
        serializer = UserAccessRecordSerializer(userAccessRecord, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAccessRecordAPIView(APIView):
    scopes = ["https://www.googleapis.com/auth/drive",
              "https://www.googleapis.com/auth/drive.file",
              "https://www.googleapis.com/auth/spreadsheets"]
    secretFile = os.path.join(os.getcwd(), "env", os.getenv(
        "DJANGO_GOOGLE_SERVICES_ACCOUNT_FILENAME"))
    credentials = service_account.Credentials.from_service_account_file(
        secretFile, scopes=scopes)
    service = discovery.build("sheets", "v4", credentials=credentials)
    spreadsheetID = os.getenv("DJANGO_GOOGLE_SPREADSHEET_ID")
    spreatsheetName = "UserInfoForPortal"
    spreatSheetColumnNumber = {
        "EmailAddress": {"colnumNumber": 2, "updateable": False},
        "ChineseName": {"colnumNumber": 8, "updateable": False},
        "FirstName": {"colnumNumber": 9, "updateable": False},
        "LastName": {"colnumNumber": 10, "updateable": False},
        "NickName": {"colnumNumber": 11, "updateable": False},
        "WechatID": {"colnumNumber": 13, "updateable": False},
        "TShirtSize": {"colnumNumber": 14, "updateable": False},
        "DietaryRestriction": {"colnumNumber": 15, "updateable": False},
        "ReimbursementMethod": {"colnumNumber": 16, "updateable": True},
        "ReimbursementAccountType": {"colnumNumber": 17, "updateable": True},
        "ReimbursementAccountEmail": {"colnumNumber": 18, "updateable": True},
        "ReimbursementAccountPhoneNumber": {"colnumNumber": 19, "updateable": True},
        "PhoneNumber": {"colnumNumber": 23, "updateable": True},
        "Zgid": {"colnumNumber": 32, "updateable": False},
        "ZgidEmail": {"colnumNumber": 33, "updateable": False},
        "PromoCode2020": {"colnumNumber": 34, "updateable": False}
    }

    def _checkVaildToken(self, request):
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(
            request.data["id_token"], req, os.getenv('DJANGO_GOOGLE_CLIEND_ID'))
        if id_info["iss"] != "accounts.google.com" or id_info["email"] != request.data["email"]:
            return False
        return True

    def _getGoogleSheetRowNumberFromEmail(self, request):
        ranges = [
            f"{self.spreatsheetName}!B:B",
            f"{self.spreatsheetName}!AG:AG"
        ]
        serviceRequest = self.service.spreadsheets().values().batchGet(
            spreadsheetId=self.spreadsheetID, ranges=ranges, majorDimension='COLUMNS')
        try:
            response = serviceRequest.execute()
        except Exception as e:
            logger.error(e)
            return -1
        userEmail: str = request.data["email"]
        rowList: list
        if userEmail.endswith("@zgzg.io"):
            rowList = response["valueRanges"][1]["values"][0]
        else:
            rowList = response["valueRanges"][0]["values"][0]
            map(str.lower, rowList)
        return rowList.index(userEmail)+1 if userEmail in rowList else -1

    def _updateGoogleSheet(self, request):
        ret = {"returnCode": -1}
        rowNumber = self._getGoogleSheetRowNumberFromEmail(request)
        if rowNumber < 1:
            return ret
        range_ = f"{self.spreatsheetName}!A{rowNumber}:ZZ{rowNumber}"
        valueInputOption = "RAW"
        values = []
        serviceRequest = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetID, range=range_)
        try:
            response = serviceRequest.execute()
        except Exception as e:
            logger.error(e)
            return ret
        responseValues = response["values"][0]
        try:
            for key in self.spreatSheetColumnNumber:
                if self.spreatSheetColumnNumber[key]["updateable"]:
                    responseValues[self.spreatSheetColumnNumber[key]
                                   ["colnumNumber"]-1] = str(request.data["data"][key])
        except Exception as e:
            print(e, self.spreatSheetColumnNumber[key]
                  ["colnumNumber"]-1, len(responseValues))
        serviceRequest = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheetID, 
            range=f"{self.spreatsheetName}!A{rowNumber}:ZZ{rowNumber}",
            valueInputOption=valueInputOption,
            body={
                "values": [responseValues]
            })

        try:
            response = serviceRequest.execute()
        except Exception as e:
            logger.error(e)
            return False
        return True

    def _getGoogleSheetData(self, request):
        ret = {"returnCode": -1}
        rowNumber = self._getGoogleSheetRowNumberFromEmail(request)
        if rowNumber < 1:
            return ret
        range_ = f"{self.spreatsheetName}!A{rowNumber}:ZZ{rowNumber}"
        serviceRequest = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetID, range=range_)
        try:
            response = serviceRequest.execute()
        except Exception as e:
            logger.error(e)
            return ret
        responseValues = response["values"][0]
        PersonEmail = responseValues[self.spreatSheetColumnNumber["EmailAddress"]["colnumNumber"]-1]
        ZgidEmail = responseValues[self.spreatSheetColumnNumber["ZgidEmail"]["colnumNumber"]-1]
        if PersonEmail == request.data["email"] or ZgidEmail == request.data["email"]:
            ret["returnCode"] = 1
            for key in self.spreatSheetColumnNumber:
                ret[key] = responseValues[self.spreatSheetColumnNumber[key]
                                          ["colnumNumber"]-1]
        return ret

    def get(self, request):
        userAccessRecord = UserAccessRecord.objects.all()
        serializer = UserAccessRecordSerializer(userAccessRecord, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request.data["record_time"] = datetime.now()
        request.data["action"] = "View"

        serializers = UserAccessRecordSerializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            if self._checkVaildToken(request):
                ret = self._getGoogleSheetData(request)
                status_ = status.HTTP_201_CREATED if ret["returnCode"] == 1 else status.HTTP_404_NOT_FOUND
                return Response(ret, status=status_)
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        request.data["record_time"] = datetime.now()
        tokenVaild = self._checkVaildToken(request)
        request.data["action"] = "Unauthorized to update profile"

        if tokenVaild:
            request.data["action"] = "Update profile: "
            ret = self._getGoogleSheetData(request)
            for key in ret:
                if ret[key] != request.data["data"][key]:
                    request.data["action"] += f"{key} from {ret[key]} to {request.data['data'][key]},"
            self._updateGoogleSheet(request)

        serializers = UserAccessRecordSerializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            if tokenVaild:
                ret = self._getGoogleSheetData(request)
                status_ = status.HTTP_201_CREATED if ret["returnCode"] == 1 else status.HTTP_404_NOT_FOUND
                return Response(ret, status=status_)
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
