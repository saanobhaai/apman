from django.conf.urls import url
from rest_framework import routers

from .resources import *
from .views import *

router = routers.DefaultRouter()
router.register(r'satellitetrajectories', FlatSatelliteTrajectoryViewset, 'satellitetrajectories')
router.register(r'satelliteinfo', SatCatViewSet, 'satelliteinfo')
router.register(r'satelliteaudio', SatelliteAudioViewset, 'satelliteaudio')

api_urls = [
               # non-viewset views
           ] + router.urls

satsound_urls = [
    url(r'^$', index, name='index'),
    url(r'^sat/(?P<norad_id>[\w\-]+)/$', sataudio, name='satellite'),
]
