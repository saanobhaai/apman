from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import *
from .models import *


@login_required
def index(request):
    user_audio = SatelliteAudio.objects.filter(user=request.user)
    return render(request, 'satsound/index.html', {'user_audio': user_audio, 'is_ajax': request.is_ajax()})


@login_required
def satellite(request, norad_id):
    sat = None
    newsat = False
    try:
        if norad_id.isdigit():
            sat = Satellite.objects.get(pk=norad_id)
    except Satellite.DoesNotExist:
        newsat = True
        # see if satellite exists in our satcat cache before hitting space track
        try:
            satcat = SatCatCache.objects.get(pk=norad_id)
            sat = Satellite(
                norad_id=norad_id,
                name=satcat.name
            )
        except SatCatCache.DoesNotExist:
            st = SpaceTrackClient(identity=settings.SPACETRACK_IDENTITY, password=settings.SPACETRACK_PASSWORD)
            # https://www.space-track.org/basicspacedata/query/class/satcat/NORAD_CAT_ID/3/orderby/INTLDES asc/metadata/false
            params = {
                'norad_cat_id': norad_id,
                'metadata': False
            }
            response = st.satcat(**params)

            if len(response) == 1:
                sat = Satellite(
                    norad_id=norad_id,
                    name=response[0].get('OBJECT_NAME', '')
                )

    status = 200
    if request.method == 'POST':
        form = SatelliteAudioForm(request.POST, request.FILES)
        if form.is_valid():
            sa = SatelliteAudio()
            if newsat:
                sat.save()
            sa.satellite = sat
            sa.user = request.user
            sa.attribution = form.cleaned_data['attribution']
            sa.audio = request.FILES['audio']
            sa.type = form.cleaned_data['type']
            sa.save()

            messages.success(request,
                             '''Audio for %s successfully submitted. The audio will be available to the system once '''
                             ''' it has been reviewed by an administrator.''' % sat.name)
            return HttpResponseRedirect(reverse('index'))

        else:
            messages.error(request,
                           '''Error uploading audio for %s. If you do not see any other messages about why, please '''
                           '''contact %s for assistance.''' % (sat.name, settings.ADMINS[0][1]))
            status = 422  # signal error to UploadProgress

    else:
        form = SatelliteAudioForm()
    return render(request, 'satsound/satellite.html', {'sat': sat, 'form': form, 'norad_id': norad_id}, status=status)
