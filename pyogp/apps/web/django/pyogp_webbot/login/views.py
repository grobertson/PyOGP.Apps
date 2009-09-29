# Create your views here.
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse


#from pyogp.lib.client.agent import Agent
#from pyogp.lib.client.settings import Settings

def index(request):
    return login(request, kwargs)

def login(request, firstname = None, lastname = None, error_message = None):
    #return HttpResponse('goddamn svn ci sucks ass')
    return render_to_response('login.html', {'firstname':firstname, 'lastname':lastname, 'error_message':error_message})

def login_request(request, firstname = None, lastname = None, password = None, error_message = None):

    if request.POST:
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        password = request.POST['password']

    try:

        #settings = Settings()
        raise Exception

    except Exception, e:

        error_message = 'login error message!'

        return HttpResponse('would like to show the login form again, with any error message that\'s appropriate')
        #return HttpResponseRedirect(reverse('pyogp_webbot.login.views.login', kwargs={'firstname':firstname, 'lastname':lastname, 'error_message':error_message}))
    