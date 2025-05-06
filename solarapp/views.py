from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm, SolarPlantForm
from django.contrib.auth.forms import AuthenticationForm
from .models import SolarPlant, UserProfile, Role
from django.views.decorators.csrf import csrf_exempt

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
    solar_plants = SolarPlant.objects.all()

    plant_admin_map = {}
    for plant in solar_plants:
        admins = UserProfile.objects.filter(assigned_plants=plant)
        admin_names = [admin.user.get_full_name() or admin.user.username for admin in admins]
        plant.admin_name = ", ".join(admin_names) if admin_names else "N/A"

    return render(request, 'home.html', {
        'solar_plants': solar_plants,
    })

"""
def detail(request):
    my_list = [1, 2]
    
    context = {
        'my_list': my_list,
    }
    return render(request, 'detail.html', context)
"""


def detail(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)

    # ดึงผู้ดูแลที่เกี่ยวข้อง
    admins = UserProfile.objects.filter(assigned_plants=plant)
    admin_info = [f"{user.user.get_full_name()} [{user.user.email}]" for user in admins]

    if request.method == 'POST':
        if 'delete' in request.POST:
            plant.delete()
            messages.success(request, "Solar plant deleted successfully.")
            return redirect('solarapp:home')
        else:
            # อัปเดตค่าที่สามารถแก้ไขได้
            plant.name = request.POST.get('name', plant.name)
            plant.weather = request.POST.get('weather', plant.weather)
            plant.temperature = request.POST.get('temperature', plant.temperature)
            plant.address = request.POST.get('address', plant.address)

            collected_at = request.POST.get('collected_at')
            submitted_at = request.POST.get('submitted_at')

            if collected_at:
                parsed_collected = parse_datetime(collected_at)
                if parsed_collected:
                    plant.collected_at = parsed_collected

            if submitted_at:
                parsed_submitted = parse_datetime(submitted_at)
                if parsed_submitted:
                    plant.submitted_at = parsed_submitted

            plant.save()
            messages.success(request, "Solar plant updated successfully.")
            return redirect('solarapp:detail', plant_id=plant.id)

    # ใช้ข้อมูล mock สำหรับ performance (หรือดึงจาก model ได้ถ้ามี)
    zone_a_performance = [100, 100, 20, 50, 100, 20, 50, 100, 45, 100, 50, 100, 100, 20, 30, 40]
    zone_b_performance = [100, 50, 20, 100, 100, 50, 20, 100, 100, 40, 100, 50, 30, 20, 30, 40]

    return render(request, 'detail.html', {
        'plant': plant,
        'admin_info': "\n".join(admin_info),
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
    if request.method == 'POST':
        form = SolarPlantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('solarapp:home')
    else:
        form = SolarPlantForm()

    return render(request, 'addnewsolar.html', {'form': form})

def detail_perf(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)

    return render(request, 'detail_perf.html', {
        'plant': plant,
    })

def role_manage(request):
    user_profiles = UserProfile.objects.select_related('user').prefetch_related('roles').order_by('user__id')
    roles = Role.objects.exclude(name='Root Admin')
    solar_plants = SolarPlant.objects.all().order_by('id')
    return render(request, 'role_manage.html', {
        'user_profiles': user_profiles,
        'roles': roles,
        'solar_plants': solar_plants,
    })

def update_user_role(request, profile_id):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=profile_id)
        role_ids = request.POST.getlist('role_ids[]')
        profile.roles.set(role_ids)
        profile.save()
    return redirect('solarapp:role_manage')

def update_user_plant(request, profile_id):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=profile_id)
        plant_ids = request.POST.getlist('plant_ids[]')
        profile.assigned_plants.set(plant_ids)
        profile.save()
    return redirect('solarapp:role_manage')

def myteamadmin(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)
    team_profiles = UserProfile.objects.filter(assigned_plants=plant).select_related('user').prefetch_related('roles')
    current_user_profile = None
    if request.user.is_authenticated:
        current_user_profile = getattr(request.user, 'profile', None)

    sorted_profiles = sorted(team_profiles, key=lambda p: 0 if p == current_user_profile else 1)

    return render(request, 'myteamadmin.html', {
        'plant': plant,
        'team_profiles': sorted_profiles
    })

def editsolar(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)

    if request.method == 'POST':
        if 'delete' in request.POST:
            plant.delete()
            messages.success(request, "Solar plant has been deleted.")
            return redirect('solarapp:home')

        plant.name = request.POST.get('plant-name')
        plant.properties = request.POST.get('plant-properties')
        plant.address = request.POST.get('address')
        plant.save()
        messages.success(request, "Solar plant has been updated.")
        return redirect('solarapp:home')

    return render(request, 'editsolar.html', {
        'plant': plant
    })

def uploadfile(request):
    return render(request, 'uploadfile.html')

def uploadzone(request):
    return render(request, 'uploadzone.html')