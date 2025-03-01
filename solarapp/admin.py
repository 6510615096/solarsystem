from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Role

# Register Role model
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
    list_display = ('username', 'first_name', 'last_name', 'get_roles', 'is_staff')
    
    def get_roles(self, obj):
        try:
            return obj.profile.get_roles_display()
        except UserProfile.DoesNotExist:
            return 'No Profile'
    
    get_roles.short_description = 'Roles'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)