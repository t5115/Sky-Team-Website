"""
URL configuration for mysite project.

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
from django.urls import path , include
from django.shortcuts import render 

def home_view(request):
    return render(request, "index.html")  

def create_view(request):
    return render(request,"pages/signup.html")

def forgot_password(request):
    return render(request, "pages/reset_account.html")

urlpatterns = [
    path("admin/" , admin.site.urls),

    # Authentication URLs
    path("accounts/" , include("accounts.urls")),  

    # home route
    path("" , home_view , name="home"),
    
    #Create account
    path("create_account/",create_view,name="create-account"),

    #Forgot Password
    path("forgot_password",forgot_password,name="forgot-password"),



]