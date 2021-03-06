from __future__ import unicode_literals

import logging
import math
import unicodedata
from os import path

import ephem
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from spacetrack import SpaceTrackClient
from timezonefinder import TimezoneFinder

from .validators import *

logger = logging.getLogger('commands')


def decdeg2dms(dd):
    is_positive = dd >= 0
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees
    returnstr = '%s:%s:%s'
    return returnstr % (int(degrees), int(minutes), seconds)


def satellite_upload(instance, filename):
    now = timezone.now()
    satdir = str(instance.satellite.pk)
    base, ext = path.splitext(filename)
    fn = '%s%s' % (now.strftime("%Y%m%d-%H%M%S"), ext)
    return path.join(satdir, fn)


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Satellite(BaseModel):
    norad_id = models.IntegerField(primary_key=True, verbose_name=u'NORAD catalog number')
    name = models.CharField(max_length=100)
    # https://www.space-track.org/documentation#/tle
    # blank=True in case something goes wrong getting tle from space-track on add
    tle = models.CharField(max_length=164, blank=True, verbose_name=u'two-line element')

    def update_tle(self):
        st = SpaceTrackClient(identity=settings.SPACETRACK_IDENTITY, password=settings.SPACETRACK_PASSWORD)
        tle = st.tle_latest(iter_lines=True, ordinal=1, norad_cat_id=self.pk, format='tle')
        self.tle = '\n'.join(tle)

    def update_trajectories(self):
        logger.info('update_trajectories: %s' % self.norad_id)
        if self.tle != '':
            self.satellitetrajectory_set.all().delete()

            line1 = unicodedata.normalize('NFKD', self.name).encode('ascii', 'ignore')  # not strictly necessary
            line2, line3 = self.tle.split('\n')
            s = ephem.readtle(line1, line2, line3)

            for observer in Observer.objects.all():
                # http://rhodesmill.org/pyephem/quick
                o = ephem.Observer()
                o.lat = decdeg2dms(observer.lat)
                o.lon = decdeg2dms(observer.lon)
                o.elevation = observer.elevation
                # From documentation: Rising and setting are sensitive to atmospheric refraction at the horizon, and
                # therefore to the observer's temp and pressure; set the pressure to zero to turn off refraction.
                o.pressure = 0  # (defaults to 1010mBar)
                # o.temp (defaults to 25C)
                # o.horizon: defaults to 0, but may want to set to 34 or make observer-dependent. From documentation:
                # The United States Naval Observatory, rather than computing refraction dynamically,
                # uses a constant estimate of 34' of refraction at the horizon. To determine when a body will rise
                # "high enough" above haze or obstacles, set horizon to a positive number of degrees.
                # A negative value of horizon can be used when an observer is high off of the ground.

                o.date = o.epoch = ephem.now()
                date_limit = ephem.Date(o.date + observer.trajectory_window * ephem.hour)
                traj = []
                while o.date < date_limit:
                    try:
                        np = o.next_pass(s)
                        # logger.info('%s next pass: %s' % (self.pk, np))
                        try:
                            assert np[0] < np[2] < np[4]

                            try:
                                assert traj != np

                                st = SatelliteTrajectory()
                                st.satellite = self
                                st.observer = observer
                                st.rise_time = timezone.make_aware(np[0].datetime(), timezone.utc)
                                st.rise_azimuth = math.degrees(np[1])
                                st.maxalt_time = timezone.make_aware(np[2].datetime(), timezone.utc)
                                st.maxalt_altitude = math.degrees(np[3])
                                st.set_time = timezone.make_aware(np[4].datetime(), timezone.utc)
                                st.set_azimuth = math.degrees(np[5])

                                st.save()
                                o.date = o.epoch = np[4]
                                traj = np

                            except AssertionError:  # If we get trapped in a loop, bail
                                logger.error('Repeated trajectory. Discarding %s and bailing.' % (np,))
                                o.date = o.epoch = date_limit
                                break

                        except AssertionError:
                            # uncomment next line if we want to dig into why we're getting None for events
                            # logger.error('%s Pass times out of order. Discarding %s' % (self.pk, np))
                            # If the traj times are out of order, use the latest datetime to move forward.
                            # What appears to cause this is max_alt_time and/or set_time being None,
                            # so that previous np[2] and np[4] aren't overwritten.
                            # http://rhodesmill.org/pyephem/quick.html under transit, rising, setting:
                            # "Any of the tuple values can be None if that event was not found."
                            o.date = o.epoch = max(np[0], np[2], np[4])
                            break

                    except ValueError:
                        o.date = o.epoch = date_limit
                        # TODO: handle geosynchronous satellites (no trajectories calculated)
                        break

    def save(self, *args, **kwargs):
        newsat = False
        if self._state.adding:
            newsat = True
            self.update_tle()

        super(Satellite, self).save(*args, **kwargs)

        if newsat:
            self.update_trajectories()

    def __unicode__(self):
        return '%s %s' % (self.norad_id, self.name)


class SatCatCache(BaseModel):
    norad_id = models.IntegerField(primary_key=True, verbose_name=u'NORAD catalog number')
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return '%s %s' % (self.norad_id, self.name)


class Observer(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # if we use postgres, we can use geodjango to store lat/lon as a Point
    lat = models.DecimalField(decimal_places=6, max_digits=9, verbose_name=u'latitude')
    lon = models.DecimalField(decimal_places=6, max_digits=9, verbose_name=u'longitude')
    timezone = models.CharField(max_length=100, default=settings.DEFAULT_TIMEZONE)
    elevation = models.IntegerField(default=0, verbose_name='elevation in meters')
    ip = models.CharField(max_length=40, default='127.0.0.1:54321')  # not currently used
    trajectory_window = models.PositiveSmallIntegerField(verbose_name='hours of trajectories', default=24)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        try:
            # https://github.com/MrMinimal64/timezonefinder
            tf = TimezoneFinder()
            timezone_name = tf.timezone_at(lng=self.lon, lat=self.lat)
            if timezone_name is None:
                timezone_name = tf.closest_timezone_at(lng=self.lon, lat=self.lat)
                # maybe even increase the search radius (delta_degree=x) when it is still None

            self.timezone = timezone_name

        except ValueError:
            # the coordinates were out of bounds - just use default
            pass

        super(Observer, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.user.username


class SatelliteTrajectory(BaseModel):
    satellite = models.ForeignKey(Satellite, on_delete=models.CASCADE)
    observer = models.ForeignKey(Observer, on_delete=models.CASCADE)
    rise_time = models.DateTimeField(verbose_name=u'rise time')  # UTC
    rise_azimuth = models.DecimalField(decimal_places=6, max_digits=9, verbose_name=u'rise azimuth')
    maxalt_time = models.DateTimeField(verbose_name=u'maximum altitude time')
    maxalt_altitude = models.DecimalField(decimal_places=6, max_digits=9, verbose_name=u'maximum altitude')
    set_time = models.DateTimeField(verbose_name=u'set time')
    set_azimuth = models.DecimalField(decimal_places=6, max_digits=9, verbose_name=u'set azimuth')

    _audio = None

    # def post(self):
    #     url = self.observer.ip
    #     payload = {
    #         'norad_id': self.satellite.pk,
    #         'name': self.satellite.name,
    #         'rise_time': self.rise_time,
    #         'rise_azimuth': self.rise_azimuth,
    #         'maxalt_time': self.maxalt_time,
    #         'maxalt_altitude': self.maxalt_altitude,
    #         'set_time': self.set_time,
    #         'set_azimuth': self.set_azimuth,
    #         'audiofile': 'test',
    #         'username': 'test',
    #         'attribution': 'test'
    #     }
    #     try:
    #         r = requests.post(url, json=payload, timeout=0.001)
    #     except requests.exceptions.Timeout:
    #         pass

    # def save(self, *args, **kwargs):
    #     newtraj = False
    #     if self._state.adding:
    #         newtraj = True
    #     super(SatelliteTrajectory, self).save(*args, **kwargs)
    #     if newtraj:
    #         self.post()

    def __unicode__(self):
        return '%s %s %s' % (
            self.satellite.pk, self.observer.__unicode__(), self.rise_time.strftime(settings.TRAJECTORY_TIME_FORMAT)
        )

    class Meta:
        verbose_name_plural = 'satellite trajectories'


class SatelliteAudio(BaseModel):
    TYPES = (
        (1, u'recorded transmission'),
        (2, u'interpretation'),
    )

    satellite = models.ForeignKey(Satellite, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attribution = models.CharField(max_length=100, blank=True)
    # if we decide we need to override filename with this pk:
    # http://stackoverflow.com/questions/651949/django-access-primary-key-in-models-filefieldupload-to-location
    audio = models.FileField(upload_to=satellite_upload, validators=[validate_audio_size, validate_audio_type])
    reviewed = models.BooleanField(default=False)
    type = models.PositiveSmallIntegerField(choices=TYPES)

    def __unicode__(self):
        return '%s %s' % (self.satellite.pk, self.attribution)
