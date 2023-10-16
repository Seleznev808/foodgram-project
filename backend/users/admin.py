from django.contrib import admin


from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = ('username', 'first_name')
    list_filter = ('username', 'first_name')
    empty_value_display = '-пусто-'
