from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Role
from .models import UploadedFile

# Register Role model

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'plant', 'uploaded_at', 'collected_date', 'weather', 'temperature')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin): 
    list_display = ('name', 'description')
    search_fields = ('name',)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'
    filter_horizontal = ('roles',) 

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'get_roles', 'is_active', 'is_staff')
    list_filter = ('is_active',)
    actions = ['activate_users']
    
    def get_roles(self, obj):
        try:
            return  obj.profile.get_roles_display()
        except UserProfile.DoesNotExist:
            return 'No Profile'
    
    get_roles.short_description = 'Roles'
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} users.")
    activate_users.short_description = "Activate selected users"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)