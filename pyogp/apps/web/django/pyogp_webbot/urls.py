from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^pyogp_webbot/', include('pyogp_webbot.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^$', 'pyogp_webbot.login.views.index'),
    (r'^pyogp_webbot/$', 'pyogp_webbot.login.views.index'),
    (r'^pyogp_webbot/login/$', 'pyogp_webbot.login.views.login'),
    (r'^pyogp_webbot/login/login_request/$', 'pyogp_webbot.login.views.login_request'),
)
