import re, string
import requests
import urllib
from django.shortcuts import render
from .forms import SentenceForm
import redis
import json

# dont remove the word 'Bearer' from the Authorization token, only update the token
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer BQCaEIN0EnsdlON0oQTNHoSq2RzaEDFTuKZLomQUEcklknBm_866AfQPZ_klLdgF_LlqIcl76G28E6Fb0oYLxILgT6a7qt4o0iIcjOAJCTEgFr0VCAi-sflYJbVKwHEWGCkrIcnBhqvDS9rZI0RGtUZMVdwmqPvwXSaZYstVBhpG60J26aVw',
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "example"
    }
}

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def splitSentence(text):
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    txt = regex.sub('', text)
    split = txt.split()
    spl = list(chunks(split, 3))
    arr = []

    for i,val in enumerate(spl):
        join = " ".join(val)
        if len(val)%3==0:
            arr.append(join)
        if len(val)%3==1 and len(arr)>1:
            arr[i-1] = arr[i-1] +" "+''.join(val)
        if len(val)%3==2:
            arr.append(join)
    return arr


def index(request):
    arr_tracks = []
    r_cache = redis.StrictRedis(host='localhost', port=6379, db=0)  # using redis as cache
    if request.POST.get('input_sentence'):


        form = SentenceForm(request.POST)
        input = request.POST['input_sentence']
        sentence = splitSentence(input.lower())

        if len(sentence) == 0:
            error = 'Sentence too short.'
            context = {'form':form, 'error':error}
            return render(request, 'playlist/playlist.html',context)

        for i in sentence:
            print (r_cache.get(i))



            if r_cache.exists(i):  # it already exists in cache
                continue

            track = urllib.parse.quote(i)

            url = 'https://api.spotify.com/v1/search?q={}&type=track&limit=1'
            r = requests.get(url.format(track), headers=headers).json()

            if 'error' in r:
                error = r['error']['message']
                context = {'form':form, 'error':error}
                return render(request, 'playlist/playlist.html',context)

            if r['tracks']['total']==0:
                no_images = True
                context = { 'form':form, 'no_images':no_images}
                return render(request, 'playlist/playlist.html',context)

            track_details = {
                'artist': r['tracks']['items'][0]['artists'][0]['name'],
                'track': r['tracks']['items'][0]['name'],
                'album': r['tracks']['items'][0]['album']['name'],
                'link': r['tracks']['items'][0]['external_urls']['spotify'],
                'image': r['tracks']['items'][0]['album']['images'][2]['url'],
            }


            json_tracks = json.dumps(track_details)
            r_cache.set(str(i), json_tracks,ex=604800) # expire key in 1 week


    # for i in r_cache.keys():   #for deleting
    #     r_cache.delete(i)

    form = SentenceForm()

    for i in r_cache.keys():  # get from cache
        arr_tracks.append(json.loads(r_cache.get(i).decode('utf-8')))

    context = {'arr_tracks':arr_tracks, 'form':form}

    return render(request, 'playlist/playlist.html',context)
