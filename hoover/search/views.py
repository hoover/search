import json
from urllib.parse import quote
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf import settings
from ..contrib import installed
from . import es
from .models import Collection

if installed.ratelimit:
    from ..contrib.ratelimit.decorators import limit_user
else:
    limit_user = lambda func: func


class JsonResponse(HttpResponse):

    def __init__(self, data):
        return super(JsonResponse, self).__init__(
            json.dumps(data),
            content_type='application/json',
        )


def can_search(user, collections_arg):
    rv = list(Collection.objects_for_user(user))
    if collections_arg is not None:
        collections = set(collections_arg)
        rv = [col for col in rv if col.name in collections]
    return rv


def ping(request):
    Collection.objects.count()
    return HttpResponse('ok\n')


def home(request):
    collections_arg = request.GET.get('collections')
    if collections_arg is not None:
        collections_arg = collections_arg.split()
    return render(request, 'home.html', {
        'collections': Collection.objects_for_user(request.user),
        'selected': set(can_search(request.user, collections_arg)),
    })


@csrf_exempt
def collections(request):
    return JsonResponse([
        {'name': col.name, 'title': col.title}
        for col in Collection.objects_for_user(request.user)
    ])


@csrf_exempt
@limit_user
def search(request):
    body = json.loads(request.body.decode('utf-8'))
    collections = can_search(request.user, body.get('collections'))
    res, counts = es.search(
        from_=body.get('from'),
        size=body.get('size'),
        query=body['query'],
        fields=body.get('fields'),
        highlight=body.get('highlight'),
        collections=[c.name for c in collections],
    )

    from .es import _index_id
    def col_name(id):
        return Collection.objects.get(id=id).name

    for item in res['hits']['hits']:
        name = col_name(_index_id(item['_index']))
        url = 'doc/{}/{}'.format(name, item['_id'])
        item['_collection'] = name
        item['_url'] = request.build_absolute_uri(url)
    res['count_by_index'] = {
        col_name(i): counts[i]
        for i in counts
    }
    return JsonResponse(res)


@limit_user
def doc(request, collection_name, id):
    collection = get_object_or_404(
        Collection.objects_for_user(request.user),
        name=collection_name,
    )
    return collection.get_loader().get(id).view(request)


def whoami(request):
    return JsonResponse({
        'username': request.user.username,
        'admin': request.user.is_superuser,
        'urls': {
            'login': reverse('login'),
            'admin': reverse('admin:index'),
            'password_change': reverse('password_change'),
            'logout': reverse('logout') + '?next=' + reverse('home'),
        },
    })
