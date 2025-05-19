from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from solarapp import views

app_name = "solarapp"

urlpatterns = [
    path("", views.login_request, name="login"),
    path("register/", views.register, name="register"),
    path("home/", views.home , name="home"),
    path("profile/", views.profile_view, name="profile"),
    path("logout/", views.logout, name="logout"),
    path("addnewsolar/", views.addnewsolar, name="addnewsolar"),
    path("detail/", views.detail, name="detail"),
    path("detail/<int:plant_id>/", views.detail, name="detail"),
    path("detail_perf/", views.detail_perf, name="detail_perf"),
    path("detail_perf/<int:plant_id>/", views.detail_perf, name="detail_perf"),
    path("role_manage/", views.role_manage, name="role_manage"),
    path("role_manage/update_role/<int:profile_id>/", views.update_user_role, name="update_user_role"),
    path("role_manage/update_plant/<int:profile_id>/", views.update_user_plant, name="update_user_plant"),
    path("myteamadmin/", views.myteamadmin, name="myteamadmin"),
    path("myteamadmin/<int:plant_id>/", views.myteamadmin, name="myteamadmin"),
    path("editsolar/", views.editsolar, name="editsolar"),
    path("editsolar/<int:plant_id>/", views.editsolar, name="editsolar"),
    path("uploadfile/", views.uploadfile, name="uploadfile"),
    path("uploadzone/", views.uploadzone, name="uploadzone"),
    path("account-pending/", views.account_pending, name="account_pending"),
    path("auth-error/", views.social_auth_error, name="auth_error"),
    path('plant/<int:plant_id>/view_uploaded/', views.view_uploaded, name='view_uploaded'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
