from django.shortcuts import render, redirect
from django.http import HttpResponse
from .froms import UserForm
from .models import User
from django.contrib import messages

# Create your views here.

def registerUser(request):
    
    if request.method=='POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # create user using form
            # password = form.cleaned_data['password']
            # user = form.save(commit=False)
            # user.set_password(password)
            # user.role = User.CUSTOMER
            # user.save()
            
            # create user using create_user method in models.py
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name,last_name,username,email,password)
            user.role = User.CUSTOMER
            user.save()
            messages.success(request, "Your account has been created successfully")
            return redirect('registerUser')
        else:
            print(form.errors)
    else:    
        form = UserForm()
    context = {
        'form':form
    }    
    return render(request, 'accounts/registerUser.html', context=context)
