from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
from django.db.models import Q


# Create your views here.

@login_required
def home(request):
    search = request.GET.get('plant_name', '').strip()
    status = request.GET.get('status', '').strip()
    sort = request.GET.get('sort', '').strip()

    queryset = SolarPlant.objects.all()

    # ✅ ค้นหา (search) ทั้ง id และ name
    if search:
        if search.isdigit():
            queryset = queryset.filter(id=int(search))
        else:
            queryset = queryset.filter(name__icontains=search)

    # ✅ กรองตามสถานะ
    if status:
        queryset = queryset.filter(status__iexact=status)

    # เตรียมข้อมูลแสดงผลแบบมี admin และไฟล์
    plant_admin_data = []
    admin_role = Role.objects.get(name="Admin solar")

    for plant in queryset:
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

    # ✅ เรียงลำดับตาม id
    if sort == "id_asc":
        plant_admin_data.sort(key=lambda x: x['plant'].id)
    elif sort == "id_desc":
        plant_admin_data.sort(key=lambda x: x['plant'].id, reverse=True)

    # ✅ ส่ง role ของ user ไปให้ template ด้วย
    role_names = []
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        role_names = [role.name for role in profile.roles.all()]

    return render(request, 'home.html', {
        'plant_admin_data': plant_admin_data,
        'user_roles': role_names,
    })




def create_user_profile(backend, user, response, *args, **kwargs):
    from solarapp.models import UserProfile
    
    # Check if this is a new user profile creation
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user)
        # For new users, always set as inactive unless they're superuser
        if not user.is_superuser:
            user.is_active = False
            user.save()
            raise PermissionDenied("Your account has been created and is pending admin approval.")
    
    # For existing users, check if they have roles
    if not user.profile.roles.exists():
        if not user.is_active:  # If account exists but not active
            raise PermissionDenied("Your account is pending admin approval.")
        else:  # If account exists and is active, but no roles
            raise PermissionDenied("Please contact an administrator to assign roles to your account.")

def account_pending(request):
    messages.warning(request, "Your account has been created but is pending approval. Please wait for admin approval.")
    return redirect('solarapp:login')

def social_auth_error(request, *args, **kwargs):
    messages.error(request, "You must be approved by admin before using your account.")
    return redirect('solarapp:login')

def prevent_social_linking_to_superuser(backend, user, *args, **kwargs):
    if user and user.is_superuser:
        raise PermissionDenied("Cannot link Google account to superuser.")

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create user but don't log them in
            user = form.save(commit=False)
            user.is_active = False  # Set as inactive by default
            user.save()

            # Create user profile
            UserProfile.objects.create(user=user)

            messages.success(request, "Your account has been created but is pending approval. An admin will assign roles before you can login.")
            return redirect('solarapp:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    # Clear all messages
    list(messages.get_messages(request))
    return redirect('solarapp:login')

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
@login_required
def detail(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)

    admins = UserProfile.objects.filter(assigned_plants=plant)
    admin_info = [f"{user.user.get_full_name()} [{user.user.email}]" for user in admins]

 
    strategy = get_role_strategy(request.user)
    can_edit = strategy.can_edit(request.user, plant)
    can_delete = strategy.can_delete(request.user, plant)

    if request.method == 'POST':
        if 'delete' in request.POST and can_delete:
            plant.delete()
            messages.success(request, "Solar plant deleted successfully.")
            return redirect('solarapp:home')
        elif can_edit:
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
        else:
            messages.error(request, "You don't have permission to update this plant.")

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



@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        return redirect('solarapp:home')  # กลับไปหน้า Home หลังบันทึก
    return render(request, 'profile.html', {'user': user})


@login_required
def addnewsolar(request):
    if request.method == 'POST':
        form = SolarPlantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('solarapp:home')
    else:
        form = SolarPlantForm()

    return render(request, 'addnewsolar.html', {'form': form})

@login_required
def detail_perf(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)

    return render(request, 'detail_perf.html', {
        'plant': plant,
    })

@login_required
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

@login_required
def update_user_role(request, profile_id):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=profile_id)
        role_ids = request.POST.getlist('role_ids[]')
        profile.roles.set(role_ids)
        profile.save()
    return redirect('solarapp:role_manage')

@login_required
def update_user_plant(request, profile_id):
    if request.method == 'POST':
        profile = get_object_or_404(UserProfile, id=profile_id)
        plant_ids = request.POST.getlist('plant_ids[]')
        profile.assigned_plants.set(plant_ids)
        profile.save()
    return redirect('solarapp:role_manage')

@login_required
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

@login_required
def editsolar(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)
    uploaded_images = plant.uploaded_files.filter(file__iendswith=('.jpg', '.jpeg', '.png'))


    can_delete = False

    if request.user.is_authenticated:
        strategy = get_role_strategy(request.user)
        can_delete = strategy.can_delete(request.user, plant)


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


@login_required
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

@login_required
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


@login_required
def view_uploaded(request, plant_id):
    plant = get_object_or_404(SolarPlant, id=plant_id)
    uploaded_images = plant.uploaded_files.order_by('-uploaded_at')
    return render(request, 'view_uploaded.html', {
        'plant': plant,
        'uploaded_images': uploaded_images,
    })


class RoleStrategy:
    def can_edit(self, user, plant):
        return False

    def can_delete(self, user, plant):
        return False


class AdminStrategy(RoleStrategy):
    def can_edit(self, user, plant):
        return True

    def can_delete(self, user, plant):
        return True


class AdminSolarStrategy(RoleStrategy):
    def can_edit(self, user, plant):
        return plant in user.profile.assigned_plants.all()

    def can_delete(self, user, plant):
        return False


def get_role_strategy(user):
    if not user.is_authenticated:
        return RoleStrategy()

    role_names = [role.name.lower() for role in user.profile.roles.all()]

    if "admin" in role_names:
        return AdminStrategy()
    elif "admin solar" in role_names:
        return AdminSolarStrategy()

    return RoleStrategy()

def get_user_by_email_if_exists(backend, details, user=None, *args, **kwargs):
    if user:
        return None
    
    email = details.get('email')
    if email:
        try:
            existing_user = User.objects.get(email=email)
            if existing_user:
                return {'user': existing_user, 'is_new': False}
        except User.DoesNotExist:
            pass
    return None

