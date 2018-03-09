"""oqatt_core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from oqatt_core import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/user/test$', views.TestApi.as_view()),
    url(r'^api/user/create$', views.CreateUser.as_view()),
    url(r'^api/user/sync_contacts$', views.SyncUserContacts.as_view()),
    url(r'^api/user/(?P<me_id>.+)/poll/publish$', views.PublishPoll.as_view()),
    url(r'^api/user/(?P<me_id>.+)/poll/publish/open$', views.PublishGroupPoll.as_view()),
    url(r'^api/user/(?P<me_id>.+)/poll/vote$', views.Vote.as_view()),
    url(r'^api/user/(?P<me_id>.+)/token/balance$', views.GetTokenBalance.as_view()),
    url(r'^api/user/(?P<me_id>.+)/update/profile/fcm_id$', views.UpdateFCMId.as_view())

]