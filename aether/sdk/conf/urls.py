# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.conf import settings
from django.contrib import admin
from django.urls import include, path


def generate_urlpatterns(token=False, app=[]):
    '''
    Generates the most common url patterns in the apps based on settings.
    '''

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # APP specific
    urlpatterns = app or []

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # HEALTH checks
    urlpatterns += _get_health_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # KEYCLOAK GATEWAY endpoints
    if settings.GATEWAY_ENABLED:
        urlpatterns = [
            # this is reachable using internal network
            path(route='', view=include(urlpatterns)),
            # this is reachable using the gateway server
            path(route=f'<slug:realm>/{settings.GATEWAY_SERVICE_ID}/',
                 view=include(urlpatterns)),
        ]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TOKEN endpoints
    urlpatterns += _get_token_urls(token)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # AUTHORIZATION endpoints
    urlpatterns += _get_auth_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ADMIN endpoints
    urlpatterns += _get_admin_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # DEBUG toolbar
    urlpatterns += _get_debug_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # nesting app urls
    app_url = settings.APP_URL[1:]  # remove leading slash
    if app_url:
        # Prepend url endpoints with "{APP_URL}/"
        # if APP_URL = "/eha-app" then `<my-server>/eha-app/<endpoint-url>`
        # if APP_URL = "/"        then `<my-server>/<endpoint-url>`
        urlpatterns = [
            path(route=f'{app_url}/', view=include(urlpatterns)),
        ]

    return urlpatterns


def _get_health_urls():
    from aether.sdk.health import views

    health_urls = [
        path(route='health', view=views.health, name='health'),
        path(route='check-db', view=views.check_db, name='check-db'),
        path(route='check-app', view=views.check_app, name='check-app'),
    ]

    if settings.EXTERNAL_APPS:
        from aether.sdk.auth.apptoken.decorators import app_token_required

        health_urls += [
            # checks if the external app is reachable
            path(route='check-app/<slug:name>',
                 view=views.check_external,
                 name='check-external'),

            # to check if the user tokens are valid
            path(route='check-tokens',
                 view=app_token_required(views.health),
                 name='check-tokens'),
        ]

    return health_urls


def _get_token_urls(token):
    token_urls = []

    if token:
        from aether.sdk.auth.views import auth_token

        # generates users token
        token_urls += [
            path(route=settings.TOKEN_URL, view=auth_token, name='token'),
        ]
        if settings.GATEWAY_ENABLED:
            token_urls += [
                path(route=f'{settings.GATEWAY_PUBLIC_PATH}/{settings.TOKEN_URL}',
                     view=auth_token,
                     name='public-token'),
            ]

    if settings.EXTERNAL_APPS:
        from aether.sdk.auth.apptoken.views import user_app_token_view

        token_urls += [
            # shows the current user app tokens
            path(route=settings.CHECK_TOKEN_URL,
                 view=user_app_token_view,
                 name='check-user-tokens'),
        ]

    return token_urls


def _get_auth_urls():
    if settings.CAS_SERVER_URL:
        from django_cas_ng import views

        login_view = views.LoginView.as_view()
        logout_view = views.LogoutView.as_view()

    else:
        from django.contrib.auth.views import LoginView, LogoutView

        if not settings.KEYCLOAK_SERVER_URL:
            logout_view = LogoutView.as_view(template_name=settings.LOGGED_OUT_TEMPLATE)
            login_view = LoginView.as_view(template_name=settings.LOGIN_TEMPLATE)

        else:
            from aether.sdk.auth.keycloak.views import KeycloakLogoutView

            logout_view = KeycloakLogoutView.as_view(template_name=settings.LOGGED_OUT_TEMPLATE)

            if not settings.KEYCLOAK_BEHIND_SCENES:
                from aether.sdk.auth.keycloak.forms import RealmForm
                from aether.sdk.auth.keycloak.views import KeycloakLoginView

                login_view = KeycloakLoginView.as_view(
                    template_name=settings.KEYCLOAK_TEMPLATE,
                    authentication_form=RealmForm,
                )
            else:
                from aether.sdk.auth.keycloak.forms import RealmAuthenticationForm

                login_view = LoginView.as_view(
                    template_name=settings.KEYCLOAK_BEHIND_TEMPLATE,
                    authentication_form=RealmAuthenticationForm,
                )

    auth_urls = [
        path(route='login', view=login_view, name='login'),
        path(route='logout', view=logout_view, name='logout'),
    ]

    extra_auth_urls = [
        path(route='logout', view=logout_view, name='logout'),
    ]

    ns = 'rest_framework'
    return [
        path(route='', view=include(extra_auth_urls)),
        path(route=f'{settings.AUTH_URL}/', view=include((auth_urls, ns), namespace=ns)),
    ]


def _get_admin_urls():
    admin_urls = [
        # monitoring
        path(route='~prometheus/', view=include('django_prometheus.urls')),
        # uWSGI monitoring
        path(route='~uwsgi/', view=include('django_uwsgi.urls')),
        # django admin section
        path(route='', view=admin.site.urls),
    ]

    if settings.PROFILING_ENABLED:
        admin_urls += [
            path(route='~silk/', view=include('silk.urls', namespace='silk')),
        ]

    return [
        path(route=f'{settings.ADMIN_URL}/', view=include(admin_urls)),
    ]


def _get_debug_urls():
    if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        return [
            path(route=f'{settings.DEBUG_TOOLBAR_URL}/', view=include(debug_toolbar.urls)),
        ]
    return []
