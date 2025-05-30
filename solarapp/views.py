
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm, SolarPlantForm
from django.contrib.auth.forms import AuthenticationForm
from .models import SolarPlant, UserProfile, Role
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User 
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user
from django.contrib.auth.models import AnonymousUser
from .models import SolarPlant, UserProfile, Role, UploadedFile


# Create your views here.

def home(request):
    from django.contrib.auth.models import User
    from solarapp.models import UserProfile, Role

    solar_plants = SolarPlant.objects.all()
    plant_admin_data = []
    admin_role = Role.objects.get(name="Admin solar")

    for plant in solar_plants:
        admins = UserProfile.objects.filter(
            assigned_plants=plant,
            roles=admin_role
        ).distinct()
        admin_names = [admin.user.get_full_name() or admin.user.username for admin in admins]
        has_uploaded_file = UploadedFile.objects.filter(plant=plant).exists()

        plant_admin_data.append({
            'plant': plant,
            'admin_name': ", ".join(admin_names) if admin_names else "N/A",
            'has_uploaded_file': has_uploaded_file,
        })

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name for role in profile.roles.all()]
    else:
        role_names = []

    return render(request, 'home.html', {
        'plant_admin_data': plant_admin_data, 
        'user_roles': role_names,
    })

def create_user_profile(backend, user=None, request=None, *args, **kwargs):
    if user is None:
        return
    if request and isinstance(get_user(request), User) and get_user(request).is_superuser:
        raise PermissionDenied("Please logout from your admin account before signing up with Google.")

    profile, created = UserProfile.objects.get_or_create(user=user)

    if not user.is_superuser:
        user.is_active = False
        user.save()

    if not user.profile.roles.exists():
        raise PermissionDenied("Your account has been created but is pending approval.")

def account_pending(request):
    messages.warning(request, "Your account has been created but is pending approval. Please wait for admin approval.")
    return redirect('solarapp:login')

def social_auth_error(request, *args, **kwargs):
    messages.error(request, "You must be approved by admin before using your account.")
    return redirect('solarapp:login')

def create_user_profile(backend, user, response, *args, **kwargs):
    from solarapp.models import UserProfile

    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)
    if not user.is_superuser:
        user.is_active = False
        user.save()
    if not user.profile.roles.exists():
        raise PermissionDenied("Your account has been created but is pending approval. An admin will assign roles.")

def prevent_social_linking_to_superuser(backend, user, *args, **kwargs):
    if user and user.is_superuser:
        raise PermissionDenied("Cannot link Google account to superuser.")

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            UserProfile.objects.create(user=user)  
            messages.success(request, "Your account has been created but is pending approval. An administrator will review your account and assign appropriate roles before you can log in.")
            return redirect('solarapp:login')  
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

def logout(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    list(messages.get_messages(request))  
    return redirect('social:begin', backend='google-oauth2')

"""""
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
"""""
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


    admins = UserProfile.objects.filter(assigned_plants=plant)
    admin_info = [f"{user.user.get_full_name()} [{user.user.email}]" for user in admins]


    can_edit = False
    can_delete = False

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name.lower() for role in profile.roles.all()]
        if "admin" in role_names:
            can_edit = True
            can_delete = True
        elif "admin solar" in role_names and profile.assigned_plants.filter(id=plant.id).exists():
            can_edit = True


    if request.method == 'POST':
        if 'delete' in request.POST:
            plant.delete()
            messages.success(request, "Solar plant deleted successfully.")
            return redirect('solarapp:home')
        else:
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
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

def login_request(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active and not user.is_superuser:
                messages.error(request, "Your account is awaiting approval.")
                return redirect('solarapp:login')

            if user.is_superuser or (hasattr(user, 'profile') and user.profile.roles.exists()):
                login(request, user)
                return redirect('solarapp:home')
            else:
                messages.warning(request, "Your account is pending role assignment. Please wating for admin.")
                return redirect('solarapp:login')

        else:
            try:
                fallback_user = User.objects.get(username=username)
                if not fallback_user.is_active:
                    messages.error(request, "Your account is awaiting approval. (fallback)")
                else:
                    messages.error(request, "Username or password is incorrect.")
            except User.DoesNotExist:
                messages.error(request, "Username or password is incorrect.")

            return HttpResponseRedirect(reverse('solarapp:login'))

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

    role_names = []
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name for role in profile.roles.all()]
    return render(request, 'role_manage.html', {
        'user_profiles': user_profiles,
        'roles': roles,
        'solar_plants': solar_plants,
        'user_roles': role_names,
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
    uploaded_images = plant.uploaded_files.filter(file__iendswith=('.jpg', '.jpeg', '.png'))


    can_delete = False

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name.lower() for role in profile.roles.all()]
        if "admin" in role_names:
            can_delete = True

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
        

    return render(request, 'editsolar.html', {
        'plant': plant,
        'can_delete': can_delete,
        'uploaded_images': uploaded_images,
    })


def uploadfile(request):
    user_profiles = UserProfile.objects.select_related('user').prefetch_related('roles').order_by('user__id')
    roles = Role.objects.exclude(name='Root Admin')
    solar_plants = SolarPlant.objects.all().order_by('id')
    plant_id = request.GET.get('plant_id') 
    role_names = []

    latest_uploaded_file = None
    if plant_id:
        latest_uploaded_file = UploadedFile.objects.filter(plant_id=plant_id).order_by('-uploaded_at').first()

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name for role in profile.roles.all()]

    if request.method == "POST" and request.FILES:
        uploaded_files = request.FILES.getlist('uploaded_files')
        selected_plant_id = request.POST.get('plant')
        weather = request.POST.get('weather')
        temperature = request.POST.get('temperature')
        collected_date = request.POST.get('collected_date')
        time = request.POST.get('time')

        plant = get_object_or_404(SolarPlant, id=selected_plant_id)

        for f in uploaded_files:
            UploadedFile.objects.create(
                plant=plant,
                file=f,
                weather=weather,
                temperature=temperature if temperature else None,
                collected_date=collected_date if collected_date else None,
                time=time if time else None
            )
        
        messages.success(request, f"{len(uploaded_files)} file(s) uploaded successfully.")
        return redirect(f"{reverse('solarapp:uploadzone')}?plant_id={plant.id}&date={collected_date}")


    uploaded_data = UploadedFile.objects.order_by('-uploaded_at')

    return render(request, 'uploadfile.html', {
        'user_profiles': user_profiles,
        'roles': roles,
        'solar_plants': solar_plants,
        'user_roles': role_names,
        'selected_plant_id': plant_id,  
        'uploaded_data': uploaded_data,
        'latest_uploaded_file': latest_uploaded_file,
    })


from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import UploadedFile, SolarPlant

def uploadzone(request):
    if request.method == 'POST':
        plant_id = request.GET.get('plant_id') or request.POST.get('plant_id')
        date_str = request.GET.get('date') or request.POST.get('date')
        zone = request.POST.get('zone_name')

        if not date_str:
            messages.error(request, "Date is required.")
            return redirect(request.path_info)

        try:
            collected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format. Please try again.")
            return redirect(request.path_info)

        matched = UploadedFile.objects.filter(plant_id=plant_id, collected_date=collected_date)
        updated_count = matched.update(zone=zone)

        messages.success(request, f"Zone '{zone}' saved for {updated_count} uploaded file(s).")
        return redirect('solarapp:view_uploaded', plant_id=plant_id)

 
    plant_id = request.GET.get('plant_id')
    date_str = request.GET.get('date')

    uploaded_files = []
    if plant_id and date_str:
        try:
            collected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            uploaded_files = (
                UploadedFile.objects
                .filter(plant_id=plant_id, collected_date=collected_date)
                .order_by('-uploaded_at')[:2] 
        )
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format.")

    
    return render(request, 'uploadzone.html', {
        'plant_id': plant_id,
        'date': date_str,
        'uploaded_files': uploaded_files,  
    })


def view_uploaded(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)
    uploaded_images = plant.uploaded_files.order_by('-uploaded_at')
    return render(request, 'view_uploaded.html', {
        'plant': plant,
        'uploaded_images': uploaded_images,
    })

