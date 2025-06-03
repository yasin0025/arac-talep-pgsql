from django.urls import path
from . import views
from .views import analiz_panel, analiz_bos_saat_panel
from talep.views import uzman_panel
from .views import create_temp_admin
urlpatterns = [
    path('', views.login_view, name='login'),
    path('personel/', views.personel_panel, name='personel_panel'),
    path('talep/<int:talep_id>/', views.talep_detay, name='talep_detay'),
    path('bas_sofor/', views.bas_sofor_panel, name='bas_sofor_panel'),
    path('mudur/', views.mudur_panel, name='mudur_panel'),
    path('geri-cek/<int:talep_id>/', views.geri_cek, name='geri_cek'),
    path('iptal-et/<int:talep_id>/', views.iptal_et, name='iptal_et'),
    path('taleplerim/', views.taleplerim, name='taleplerim'),
    path('bas_sofor/onayla/<int:talep_id>/', views.bas_sofor_onayla, name='bas_sofor_onayla'),
    path('bas_sofor/reddet/<int:talep_id>/', views.bas_sofor_reddet, name='bas_sofor_reddet'),
    path('mudur/onayla/<int:talep_id>/', views.mudur_onayla, name='mudur_onayla'),
    path('mudur/reddet/<int:talep_id>/', views.mudur_reddet, name='mudur_reddet'),
    path('gorev-tamamla/<int:talep_id>/', views.gorev_tamamla, name='gorev_tamamla'),
    path('ajax/kullanici-ara/', views.kullanici_ara, name='kullanici_ara'),
    path('analiz/', views.analiz_panel, name='analiz_panel'),
    path("analiz/bos-saat/", views.analiz_bos_saat_panel, name="analiz_bos_saat"),
    path('uzman/', uzman_panel, name='uzman_panel'),
    path('uzman/onayla/<int:talep_id>/', views.uzman_onayla, name='uzman_onayla'),
    path('uzman/reddet/<int:talep_id>/', views.uzman_reddet, name='uzman_reddet'),
    path('mudur/iptal/<int:talep_id>/', views.mudur_iptal_et, name='mudur_iptal_et'),
    path('sofor-gorev-pdf/', views.sofor_gorev_pdf, name='sofor_gorev_pdf'),
    path('personel/rapor-pdf/', views.personel_rapor_pdf, name='personel_rapor_pdf'),
    path('create-admin/', views.create_admin_user),
    path('create-temp-admin/', create_temp_admin),
]
