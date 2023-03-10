from django.shortcuts import render, redirect
from django.http import HttpResponse
from accounts.utils import detect_user, send_verification_email

from vendor.forms import vendorForm
from vendor.models import Vendor
from .froms import UserForm
from .models import User, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator



# restrict vendor and allow customer
def check_role_customer(user):
    if user.role==2:
        return True
    else:
        raise PermissionDenied

# restrict customer and allow vendor
def check_role_vendor(user):
    if user.role==1:
        return True
    else:
        raise PermissionDenied

def registerUser(request):

    if request.method == 'POST':
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
            user = User.objects.create_user(
                first_name, last_name, username, email, password)
            user.role = User.CUSTOMER
            user.save()
            # send verification email
            mail_subject = "Please activate your account"
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request,user,mail_subject,email_template)
            messages.success(request, "Your account has been created successfully")
            return redirect('registerUser')
        else:
            print(form.errors)
    else:
        form = UserForm()
    context = {
        'form': form
    }
    return render(request, 'accounts/registerUser.html', context=context)


def registerVendor(request):

    if request.method == 'POST':
        # create user and store data
        form = UserForm(request.POST)
        v_form = vendorForm(request.POST, request.FILES)

        if form.is_valid() and v_form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(
                first_name, last_name, username, email, password)
            user.role = User.VENDOR
            user.save()

            vendor = v_form.save(commit=False)
            vendor.user = user
            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()
            # send verification email
            mail_subject = "Please activate your account"
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request,user,mail_subject,email_template)
            messages.success(
                request, 'your account has been registered successfully, please wait for approval..')
            return redirect('registerVendor')
        else:
            print("invalid form")

    else:
        form = UserForm()
        v_form = vendorForm()

    context = {
        'form': form,
        'v_form': v_form
    }
    return render(request, 'accounts/registerVendor.html', context=context)


def activate(request,uidb64,token):
    # activate user by setting is_active status as True
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account is activated")
        return redirect('myaccount')
    
    else:
        messages.error(request, "Invalid Link")
        return redirect('myaccount')


def login(request):
    
    if request.user.is_authenticated:
        messages.warning(request, "you are already logged in")
        return redirect('myaccount')
    else:    
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')

            user = auth.authenticate(email=email, password=password)

            if user is not None:
                auth.login(request, user)
                messages.success(request, "You are Logged In")
                return redirect('myaccount')
            else:
                messages.error(request, "Invalid login credentials")
                return redirect('login')
        return render(request, 'accounts/login.html')
            
                

def logout(request):
    auth.logout(request)
    messages.info(request, "Logged Out")
    return redirect('login')

@login_required(login_url='login')
def myaccount(request):
    user = request.user
    redirecturl = detect_user(user)
    return redirect(redirecturl)

@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request, 'accounts/custDashboard.html')

@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')


def forgot_password(request):
    
    if request.method=='POST':
        email = request.POST['email']
        
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)
            
            # send reset passward email
            mail_subject = "Reset your password"
            email_template = 'accounts/emails/reset_password_email.html'
            send_verification_email(request,user,mail_subject,email_template)
            messages.success(request, "Password reset link has been sent to your email address")
            return redirect('login')
        else:
            messages.error(request, "Account does not exists")
            return redirect('forgot_password')
        
    return render(request, 'accounts/forgot_password.html')


def reset_password_validate(request,uidb64,token):
    # validate user by decoding token and primary key
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.info(request,'Please reset you password')
        return redirect('reset_password')
    else:
        messages.error(request, "Link Expired")
        return redirect('myaccount') 

def reset_password(request):
    
    if request.method=='POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password==confirm_password:
            pk = request.session.get('uid')
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request,'Password reset successfull')
            return redirect('login')
        else:
            messages.error(request,'Password do not match')
            return redirect('reset_password')
        
    return render(request, 'accounts/reset_password.html')
