from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'websnoop.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'websnoop.webforms.showFinderForm'),
    url(r'^snoop/getpages/$', 'webscrape.views.getPages'),
    url(r'^snoop/$', 'webscrape.views.getInputs'),
    url(r'^snoop/getinput/$', 'webscrape.views.getInputs'),
)
