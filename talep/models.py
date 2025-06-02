from django.db import models
from django.contrib.auth.models import User

# Kullanıcı Profili
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=[
        ('personel', 'Personel'),
        ('bas_sofor', 'Baş Şoför'),
        ('mudur', 'Müdür'),
        ('uzman', 'Uzman / Şube Müdürü')
    ])
    adsoyad = models.CharField(max_length=100, blank=True)  # 🔴 BURAYI EKLEDİK

    def __str__(self):
        return f"{self.user.username} - {self.rol}"

# Araç Bilgileri
class Arac(models.Model):
    plaka = models.CharField(max_length=20, unique=True)
    kapasite = models.IntegerField(null=True, blank=True)  # Admin formdan gizlenebilir ama modelde kalır
    marka_model = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.plaka} - {self.marka_model}"

# Şoför Modeli
class Sofor(models.Model):
    ad_soyad = models.CharField(max_length=100)
    telefon = models.CharField(max_length=20)

    def __str__(self):
        return self.ad_soyad

# Talep Modeli
class AracTalep(models.Model):
    BASKANLIK_SECENEKLERI = [
        ('SHB', 'Sağlık Hizmetleri Başkanlığı'),
        ('DHB', 'Destek Hizmetleri Başkanlığı'),
        ('HSB', 'Halk Sağlığı Başkanlığı'),
        ('KHB', 'Kamu Hastaneleri Başkanlığı'),
        ('MB', 'Müdürlük Bünyesi'),
    ]

    talep_eden = models.ForeignKey(User, on_delete=models.CASCADE)
    baskanlik = models.CharField(max_length=50, choices=BASKANLIK_SECENEKLERI)
    birim = models.CharField(max_length=100)
    gorev_aciklamasi = models.TextField()
    kisi_sayisi = models.PositiveIntegerField()
    gidilecek_ilce = models.CharField(max_length=100, default="Belirtilmedi")
    gidis_tarihi = models.DateField()
    gidis_saati = models.TimeField()
    talep_tarihi = models.DateTimeField(auto_now_add=True)
    talep_eden_adsoyad = models.CharField(max_length=100, blank=True, null=True)

    uzman_onaylayan = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uzman_onayladigi_talepler'
    )
    uzman_onay_durumu = models.CharField(
        max_length=20,
        choices=[
            ('bekliyor', 'Bekliyor'),
            ('onaylandi', 'Onaylandı'),
            ('reddedildi', 'Reddedildi')
        ],
        default='bekliyor'
    )
    uzman_red_aciklama = models.TextField(null=True, blank=True)
    uzman_onay_tarihi = models.DateTimeField(null=True, blank=True)  # 🔴 EKLENDİ

    def __str__(self):
        return f"{self.talep_eden.username} - {self.gidis_tarihi} - {self.gorev_aciklamasi}"

# Ek Kişi Modeli
class EkKisiBilgisi(models.Model):
    talep = models.ForeignKey(AracTalep, on_delete=models.CASCADE, related_name='ek_kisiler')
    ad_soyad = models.CharField(max_length=100)
    unvan = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.ad_soyad

# ✅ Talep Onay Modeli – Görev tamamlanınca varış saati buraya eklendi
class TalepOnay(models.Model):
    talep = models.OneToOneField(AracTalep, on_delete=models.CASCADE, related_name='talep_onay')
    durum = models.CharField(
        max_length=20,
        choices=[
            ('bekliyor', 'Bekliyor'),
            ('onaylandi', 'Onaylandı'),
            ('reddedildi', 'Reddedildi'),
            ('tamamlandi', 'Tamamlandı'),
            ('iptal', 'İptal Edildi')
        ]
    )
    aciklama = models.TextField(blank=True, null=True)
    iptal_aciklama = models.TextField(blank=True, null=True)
    onay_tarihi = models.DateTimeField(auto_now_add=True)
    arac = models.ForeignKey(Arac, on_delete=models.SET_NULL, null=True, blank=True)
    sofor = models.ForeignKey(Sofor, on_delete=models.SET_NULL, null=True, blank=True)
    varis_saati = models.TimeField(null=True, blank=True)
    atama_tarihi = models.DateTimeField(null=True, blank=True)  # 🔴 EKLENDİ
    yonetici_onay_tarihi = models.DateTimeField(null=True, blank=True)  # 🔴 EKLENDİ

    def __str__(self):
        return f"TalepOnay: {self.talep}"
from django.db import models
from django.contrib.auth.models import User

class Gorev(models.Model):
    tarih = models.DateField()
    personel = models.ForeignKey(User, on_delete=models.CASCADE)
    arac = models.CharField(max_length=50)
    sofor = models.CharField(max_length=50)
    gorev_aciklamasi = models.TextField()
    ek_kisiler = models.ManyToManyField('UserProfile', blank=True)

    def __str__(self):
        return f"{self.tarih} - {self.personel}"
