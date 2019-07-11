from django.urls import path
from googleapi.api.view import *


urlpatterns = [
    path("UserAccessRecordList/<email>/",
         UserAccessRecordListAPIView.as_view(), name="User-Access-Record-List"),
    path("UserAccessRecord/",
         UserAccessRecordAPIView.as_view(), name="User-Access-Record"),
   
]
