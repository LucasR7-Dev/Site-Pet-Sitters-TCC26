"""
URL configuration for backendpetmee project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.urls import path
from . import views


urlpatterns = [
    #rota raiz (http://127.0.0.1:8000/)
    path('', views.cadastro_user, name='inicio'),

    #rotas especificas
    path('registro/', views.cadastro_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('home/', views.home, name='home'),
    path('pets/novo/', views.cadastrar_pet, name='cadastrar_pet'),
    path('pets/<int:pet_id>/', views.detalhes_pet, name='detalhes_pet'),
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    path('perfil/<uuid:user_id>/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/<uuid:user_id>/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<uuid:user_id>/avaliacoes/', views.criar_avaliacao, name='criar_avaliacao'),
]
