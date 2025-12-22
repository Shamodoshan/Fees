"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('add-payment/', views.add_payment, name='add_payment'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('view-payments/', views.view_payments, name='view_payments'),
    path('view-expenses/', views.view_expenses, name='view_expenses'),
    path('view-confirmed/', views.view_confirmed, name='view_confirmed'),
    path('approve-payment/<int:pk>/', views.approve_payment, name='approve_payment'),
    path('decline-payment/<int:pk>/', views.decline_payment, name='decline_payment'),
    path('approve-expense/<int:pk>/', views.approve_expense, name='approve_expense'),
    path('decline-expense/<int:pk>/', views.decline_expense, name='decline_expense'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
