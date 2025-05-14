from django.contrib import admin
from .models import Arac, AracTalep, TalepOnay, EkKisiBilgisi, UserProfile, Sofor

@admin.register(Arac)
class AracAdmin(admin.ModelAdmin):
    list_display = ('plaka', 'marka_model')  # kapasite görünmüyor
    fields = ('plaka', 'marka_model')        # kapasite formda da yok


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'adsoyad', 'rol']
    search_fields = ('ad_soyad', 'user__username')

@admin.register(Sofor)
class SoforAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'telefon')
    search_fields = ('ad_soyad', 'telefon')

admin.site.register(AracTalep)

