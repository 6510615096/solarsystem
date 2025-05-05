from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created but is pending approval. An administrator will review your account and assign appropriate roles before you can log in.")
            return redirect('solarapp:login')  
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

def home(request):      
    return render(request, "home.html")

def addnewsolar(request):
    return render(request, 'addnewsolar.html')

def myteamadmin(request):
    return render(request, 'myteamadmin.html')

def uploadfile(request):
    return render(request, 'uploadfile.html')

"""
def detail(request):
    my_list = [1, 2]
    
    context = {
        'my_list': my_list,
    }
    return render(request, 'detail.html', context)
"""
def rolemanagement(request):
    return render(request, 'rolemanagement.html')

def detail(request):
    # Dummy data
    zone_a_performance = [100, 100, 20, 50, 100, 20, 50, 100, 45, 100, 50, 100, 100, 20, 30, 40]
    zone_b_performance = [100, 50, 20, 100, 100, 50, 20, 100, 100, 40, 100, 50, 30, 20, 30, 40]

    return render(request, 'detail.html', {
        'zone_a_performance': zone_a_performance,
        'zone_b_performance': zone_b_performance,
    })


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    """
                    if not hasattr(user, 'profile') or not user.profile.role:
                        messages.warning(request, "Waiting for account approval by admin")
                        return redirect('solarapp:login')
                    """
                    return redirect('solarapp:home')
                else:
                    messages.error(request, "Your account is awaiting approval. Please contact an administrator.")
            else:
                messages.error(request, "Username or password is incorrect")
    else:
        form = AuthenticationForm()
    return render(request, 'index.html', {'form': form})

def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        return redirect('solarapp:home')  # กลับไปหน้า Home หลังบันทึก
    return render(request, 'profile.html', {'user': user})

def addnewsolar(request):
    return render(request, 'addnewsolar.html')

