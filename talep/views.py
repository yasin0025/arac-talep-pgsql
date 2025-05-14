from django.db.models import Q
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import AracTalep, TalepOnay, Arac, Sofor
from .models import UserProfile, EkKisiBilgisi, AracTalep, TalepOnay, Arac, Sofor
from .forms import BaskanlikForm
from django.views.decorators.http import require_POST
from datetime import date
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime, date
from django.utils.timezone import make_aware
from django.core.paginator import Paginator
from datetime import datetime, date, time, timedelta
from django.http import JsonResponse

@require_POST
@login_required
def bas_sofor_reddet(request, talep_id):
    if request.user.userprofile.rol != 'bas_sofor':
        return HttpResponse("Yetkiniz yok.", status=403)

    talep = get_object_or_404(AracTalep, id=talep_id)
    try:
        onay = talep.talep_onay
    except TalepOnay.DoesNotExist:
        return HttpResponse("Onay kaydı bulunamadı.", status=404)

    aciklama = request.POST.get('aciklama', '').strip()
    if not aciklama:
        messages.error(request, "Red açıklaması boş bırakılamaz.")
        return redirect('bas_sofor_panel')

    onay.durum = 'reddedildi'
    onay.aciklama = aciklama
    onay.save()

    messages.success(request, "Talep reddedildi.")
    return redirect('bas_sofor_panel')

@login_required
def personel_panel(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    ad_soyad = user_profile.adsoyad

    saat_baslangic = time(8, 0)
    saat_bitis = time(17, 0)
    adim = timedelta(minutes=15)
    saat_araligi = []

    current = datetime.combine(datetime.today(), saat_baslangic)
    end = datetime.combine(datetime.today(), saat_bitis)
    while current <= end:
        saat_araligi.append(current.time().strftime("%H:%M"))
        current += adim

    if request.method == 'POST':
        baskanlik_form = BaskanlikForm(request.POST)
        if baskanlik_form.is_valid():
            talep_eden_adsoyad = ad_soyad
            baskanlik = baskanlik_form.cleaned_data['baskanlik']
            birim = request.POST.get('birim')
            gidilecek_ilce = request.POST.get('gidilecek_ilce')
            gorev_aciklamasi = request.POST.get('gorev_aciklamasi')
            kisi_sayisi = int(request.POST.get('kisi_sayisi'))
            gidis_tarihi = request.POST.get('gidis_tarihi')
            gidis_saati_str = request.POST.get('gidis_saati')
            gidis_saati = datetime.strptime(gidis_saati_str, "%H:%M").time()

            talep = AracTalep.objects.create(
                talep_eden=request.user,
                talep_eden_adsoyad=talep_eden_adsoyad,
                baskanlik=baskanlik,
                birim=birim,
                gidilecek_ilce=gidilecek_ilce,
                gorev_aciklamasi=gorev_aciklamasi,
                kisi_sayisi=kisi_sayisi,
                gidis_tarihi=gidis_tarihi,
                gidis_saati=gidis_saati,
            )

            TalepOnay.objects.create(talep=talep, durum='ilk')

            ek_ad_list = request.POST.getlist('ek_ad[]')
            ek_unvan_list = request.POST.getlist('ek_unvan[]')

            for ad, unvan in zip(ek_ad_list, ek_unvan_list):
                if ad.strip():
                    matched_profile = UserProfile.objects.filter(adsoyad=ad.strip()).select_related("user").first()
                    EkKisiBilgisi.objects.create(
                        talep=talep,
                        ad_soyad=ad.strip(),
                        unvan=unvan.strip(),
                        user=matched_profile.user if matched_profile else None
                    )

            return redirect('personel_panel')
    else:
        baskanlik_form = BaskanlikForm()

    today = timezone.now().date()
    tum_talepler = AracTalep.objects.filter(
    Q(talep_eden=request.user) |
    Q(ek_kisiler__user=request.user)
).prefetch_related('talep_onay').distinct().order_by('-talep_tarihi')

    paginator = Paginator(tum_talepler, 8)
    sayfa_numarasi = request.GET.get('sayfa')
    talepler = paginator.get_page(sayfa_numarasi)

    return render(request, 'talep/personel_panel.html', {
        'ad_soyad': ad_soyad,
        'talepler': talepler,
        'baskanlik_form': baskanlik_form,
        'saat_araligi': saat_araligi,
        'today': today,
        'kisi_sayilari': range(1, 16),
        'paginator': paginator,
    })




@login_required
def talep_detay(request, talep_id):
    try:
        talep = AracTalep.objects.get(id=talep_id)
    except AracTalep.DoesNotExist:
        raise Http404("Talep bulunamadı.")

    # Eğer giriş yapan kişi talep eden değilse ve ek kişi değilse, erişimi engelle
    if request.user != talep.talep_eden:
        ek_kisi_var_mi = talep.ek_kisiler.filter(user=request.user).exists()
        if not ek_kisi_var_mi:
            raise Http404("Bu talep size ait değil.")

    onay = getattr(talep, 'talep_onay', None)
    today = timezone.now().date()

    return render(request, 'talep/talep_detay.html', {
        'talep': talep,
        'onay': onay,
        'today': today
    })


@login_required
def geri_cek(request, talep_id):
    talep = get_object_or_404(AracTalep, id=talep_id, talep_eden=request.user)
    if not hasattr(talep, 'talep_onay'):
        talep.delete()
    return redirect('personel_panel')

@login_required
def iptal_et(request, talep_id):
    talep = get_object_or_404(AracTalep, id=talep_id, talep_eden=request.user)
    if hasattr(talep, 'talep_onay'):
        onay = talep.talep_onay
        if onay.durum == 'onaylandi' and talep.gidis_tarihi > timezone.now().date():
            onay.durum = 'reddedildi'
            onay.aciklama = 'Talep sahibi tarafından iptal edildi.'
            onay.save()
    return redirect('personel_panel')

@login_required
def taleplerim(request):
    talepler = AracTalep.objects.filter(talep_eden=request.user).order_by('-talep_tarihi')
    return render(request, 'talep/taleplerim.html', {'talepler': talepler})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            try:
                profile = user.userprofile
            except UserProfile.DoesNotExist:
                messages.error(request, "Kullanıcı rolü tanımlı değil.")
                return redirect('login')

            if profile.rol == 'personel':
                return redirect('personel_panel')
            elif profile.rol == 'bas_sofor':
                return redirect('bas_sofor_panel')
            elif profile.rol == 'mudur':
                return redirect('mudur_panel')
        else:
            messages.error(request, "Geçersiz kullanıcı adı veya parola.")
    return render(request, 'talep/login.html')

from datetime import datetime

from django.core.paginator import Paginator

@login_required
def bas_sofor_panel(request):
    from datetime import datetime, timedelta, time
    from django.utils.timezone import make_aware

    today = timezone.now().date()
    now = timezone.localtime().time()
    now_dt = datetime.combine(date.today(), now)

    # 🔁 Önceki güne ait ama tamamlanmamış görevleri otomatik tamamla
    otomatik_tamamlanacaklar = TalepOnay.objects.filter(
        talep__gidis_tarihi__lt=today,
        durum='onaylandi'
    )
    for onay in otomatik_tamamlanacaklar:
        onay.durum = 'tamamlandi'
        onay.save()

    talepler_bekleyen = AracTalep.objects.select_related('talep_eden')\
        .filter(talep_onay__durum='ilk').order_by('-talep_tarihi')

    talepler_mudur = AracTalep.objects.select_related('talep_eden')\
        .filter(talep_onay__durum='bekliyor').order_by('-talep_tarihi')

    # 🔽 Geçmiş görevler - sayfalama
    gecmis_queryset = AracTalep.objects.select_related('talep_eden', 'talep_onay', 'talep_onay__arac', 'talep_onay__sofor')\
        .prefetch_related('ek_kisiler')\
        .filter(talep_onay__durum='tamamlandi')\
        .order_by('-gidis_tarihi', '-gidis_saati')

    paginator = Paginator(gecmis_queryset, 8)
    sayfa = request.GET.get('sofor_sayfa')
    talepler_gecmis = paginator.get_page(sayfa)

    # 🔽 Tarih seçimi güvenli hale getirildi
    secilen_tarih_str = request.GET.get('tarih')
    try:
        secilen_tarih = datetime.strptime(secilen_tarih_str, "%Y-%m-%d").date() if secilen_tarih_str else today
    except (ValueError, TypeError):
        secilen_tarih = today

    secilen_gorevler = AracTalep.objects.select_related(
        'talep_eden', 'talep_onay', 'talep_onay__arac', 'talep_onay__sofor'
    ).filter(gidis_tarihi=secilen_tarih, talep_onay__durum='onaylandi')

    bugun_secildi = (secilen_tarih == today)

    # 🔄 Seçilen tarihe göre görevde olmayan araç ve şoförleri bul
    atanan_araclar = TalepOnay.objects.filter(
        talep__gidis_tarihi=secilen_tarih,
        durum='onaylandi'
    ).values_list('arac_id', flat=True)
    musait_araclar = Arac.objects.exclude(id__in=atanan_araclar)

    atanan_soforler = TalepOnay.objects.filter(
        talep__gidis_tarihi=secilen_tarih,
        durum='onaylandi'
    ).values_list('sofor_id', flat=True)
    musait_soforler = Sofor.objects.exclude(id__in=atanan_soforler)

    # 🔽 Her görev için özel varış saati listesi (sadece gidis_saati sonrasını göster)
    varis_saatleri_dict = {}
    for talep in secilen_gorevler:
        gidis_saati = talep.gidis_saati
        saat_listesi = []
        start = time(8, 0)
        end = time(18, 0)
        current = datetime.combine(date.today(), start)
        while current.time() <= end:
            if current.time() > gidis_saati:
                saat_listesi.append(current.time().strftime("%H:%M"))
            current += timedelta(minutes=15)
        varis_saatleri_dict[talep.id] = saat_listesi

    return render(request, 'talep/bas_sofor_panel.html', {
        'talepler_bekleyen': talepler_bekleyen,
        'talepler_mudur': talepler_mudur,
        'talepler_gecmis': talepler_gecmis,
        'secilen_gorevler': secilen_gorevler,
        'musait_araclar': musait_araclar,
        'musait_soforler': musait_soforler,
        'bugun_secildi': bugun_secildi,
        'today': today,
        'now': now_dt.time(),
        'secilen_tarih': secilen_tarih,
        'varis_saatleri_dict': varis_saatleri_dict,
    })


@login_required
def bas_sofor_onayla(request, talep_id):
    talep = get_object_or_404(
        AracTalep.objects.select_related('talep_eden'),
        id=talep_id
    )

    if request.method == 'POST':
        arac_id = request.POST.get('arac')
        sofor_id = request.POST.get('sofor')

        arac = get_object_or_404(Arac, id=arac_id)
        sofor = get_object_or_404(Sofor, id=sofor_id)

        onay = talep.talep_onay
        onay.arac = arac
        onay.sofor = sofor
        onay.durum = 'bekliyor'
        onay.onay_tarihi = timezone.now()
        onay.save()

        return redirect('bas_sofor_panel')

    # 15 dakikalık varış saatleri listesi
    varis_saatleri = []
    start = time(8, 0)
    end = time(18, 0)
    current = datetime.combine(date.today(), start)
    while current.time() <= end:
        varis_saatleri.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=15)

    araclar = uygun_araclari_getir(talep.gidis_tarihi)
    soforler = uygun_soforleri_getir(talep.gidis_tarihi)
    ek_kisiler = talep.ek_kisiler.all()

    return render(request, 'talep/bas_sofor_onayla.html', {
        'talep': talep,
        'araclar': araclar,
        'soforler': soforler,
        'ek_kisiler': ek_kisiler,
        'varis_saatleri': varis_saatleri,
    })




def uygun_araclari_getir(tarih):
    atanan_araclar = TalepOnay.objects.filter(
        talep__gidis_tarihi=tarih,
        durum__in=['bekliyor', 'onaylandi'],
        arac__isnull=False
    ).values_list('arac_id', flat=True)
    return Arac.objects.exclude(id__in=atanan_araclar)

def uygun_soforleri_getir(tarih):
    atanan_soforler = TalepOnay.objects.filter(
        talep__gidis_tarihi=tarih,
        durum__in=['bekliyor', 'onaylandi'],
        sofor__isnull=False
    ).values_list('sofor_id', flat=True)
    return Sofor.objects.exclude(id__in=atanan_soforler)


from django.core.paginator import Paginator

@login_required
def mudur_panel(request):
    if request.user.userprofile.rol != 'mudur':
        return HttpResponse("Yetkiniz yok.", status=403)

    today = timezone.now().date()

    # Tarih seçimi
    secilen_tarih_str = request.GET.get('tarih')
    try:
        secilen_tarih = datetime.strptime(secilen_tarih_str, "%Y-%m-%d").date() if secilen_tarih_str else today
    except (ValueError, TypeError):
        secilen_tarih = today

    # Bekleyen talepler
    talepler_mudur = AracTalep.objects.select_related('talep_eden')\
        .filter(talep_onay__durum='bekliyor').order_by('-talep_tarihi')

    # Geçmiş görevler - sayfalama
    gecmis_queryset = AracTalep.objects.select_related(
        'talep_eden', 'talep_onay', 'talep_onay__arac', 'talep_onay__sofor'
    ).prefetch_related('ek_kisiler').filter(
        talep_onay__durum='tamamlandi'
    ).order_by('-gidis_tarihi', '-gidis_saati')

    paginator = Paginator(gecmis_queryset, 8)
    sayfa = request.GET.get('mudur_sayfa')
    talepler_gecmis = paginator.get_page(sayfa)

    # Görevler
    bugunku_gorevler = TalepOnay.objects.select_related('talep', 'talep__talep_eden', 'arac', 'sofor') \
        .filter(durum='onaylandi', talep__gidis_tarihi=secilen_tarih)

    atanan_araclar = bugunku_gorevler.values_list('arac_id', flat=True)
    musait_araclar = Arac.objects.exclude(id__in=atanan_araclar)

    atanan_soforler = bugunku_gorevler.values_list('sofor_id', flat=True)
    musait_soforler = Sofor.objects.exclude(id__in=atanan_soforler)

    return render(request, 'talep/mudur_panel.html', {
        'talepler_mudur': talepler_mudur,
        'talepler_gecmis': talepler_gecmis,
        'bugunku_gorevler': bugunku_gorevler,
        'musait_araclar': musait_araclar,
        'musait_soforler': musait_soforler,
        'today': today,
        'secilen_tarih': secilen_tarih,
    })



@require_POST
@login_required
def mudur_reddet(request, talep_id):
    if request.user.userprofile.rol != 'mudur':
        return HttpResponse("Yetkiniz yok.", status=403)

    talep = get_object_or_404(AracTalep, id=talep_id)
    onay = talep.talep_onay

    aciklama = request.POST.get('aciklama', '').strip()
    if not aciklama:
        messages.error(request, "Red açıklaması boş bırakılamaz.")
        return redirect('mudur_panel')

    onay.durum = 'reddedildi'
    onay.aciklama = aciklama
    onay.save()

    messages.success(request, "Talep reddedildi.")
    return redirect('mudur_panel')

@login_required
def gorev_tamamla(request, talep_id):
    if request.method == "POST":
        talep = get_object_or_404(AracTalep, id=talep_id)
        talep_onay = get_object_or_404(TalepOnay, talep=talep)

        now = timezone.localtime()  # offset-aware
        gidis_datetime = make_aware(datetime.combine(talep.gidis_tarihi, talep.gidis_saati))

        if gidis_datetime <= now:
            talep_onay.durum = 'tamamlandi'

            varis_saati_str = request.POST.get("varis_saati")
            if varis_saati_str:
                try:
                    talep_onay.varis_saati = datetime.strptime(varis_saati_str, "%H:%M").time()
                except ValueError:
                    pass  # Saat verisi hatalıysa kaydetme

            talep_onay.save()

    return HttpResponseRedirect(reverse('bas_sofor_panel') + '#durumtakvim')


@login_required
def geri_cek(request, talep_id):
    talep = get_object_or_404(AracTalep, id=talep_id, talep_eden=request.user)
    try:
        onay = talep.talep_onay
        if onay.durum == 'ilk':
            onay.delete()
            talep.delete()
    except TalepOnay.DoesNotExist:
        talep.delete()

    return redirect('personel_panel')
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import get_object_or_404

@require_POST
@login_required
def mudur_onayla(request, talep_id):
    if request.user.userprofile.rol != 'mudur':
        return HttpResponse("Yetkiniz yok.", status=403)

    talep = get_object_or_404(AracTalep, id=talep_id)
    onay = talep.talep_onay
    onay.durum = 'onaylandi'
    onay.save()

    messages.success(request, "Talep onaylandı.")
    return redirect('mudur_panel')
from datetime import time

def filtreli_varis_saatleri(gidis_saati):
    return [
        time(saat, dakika).strftime("%H:%M")
        for saat in range(8, 18)
        for dakika in (0, 15, 30, 45)
        if time(saat, dakika) > gidis_saati
    ]

@require_GET
@login_required
def kullanici_ara(request):
    q = request.GET.get("q", "")
    if len(q) < 2:
        return JsonResponse([], safe=False)

    matches = UserProfile.objects.filter(adsoyad__icontains=q).values_list("adsoyad", flat=True)[:10]
    return JsonResponse(list(matches), safe=False)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta, time
from django.db.models import Count
from django.db.models.functions import Cast
from django.db.models import DateField
from collections import OrderedDict
import json
from talep.models import AracTalep

@login_required
def analiz_panel(request):
    if request.user.userprofile.rol != 'mudur':
        return HttpResponse("Yetkiniz yok.", status=403)

    bugun = timezone.now().date()
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')

    if not baslangic or not bitis:
        bitis = bugun
        baslangic = bitis - timedelta(days=30)

    try:
        baslangic = datetime.strptime(str(baslangic), "%Y-%m-%d").date()
        bitis = datetime.strptime(str(bitis), "%Y-%m-%d").date()
    except:
        return HttpResponse("Geçersiz tarih")

    talepler = AracTalep.objects.filter(
        gidis_tarihi__range=(baslangic, bitis),
        talep_onay__durum__in=['onaylandi', 'tamamlandi']
    ).select_related('talep_onay', 'talep_onay__arac')

    toplam_gorev = talepler.count()

    # Geçerli günleri say
    gecerli_gunler = [baslangic + timedelta(days=i) for i in range((bitis - baslangic).days + 1) if (baslangic + timedelta(days=i)).weekday() < 5]
    resmi_tatil_gunleri = ["01-01", "23-04", "01-05", "19-05", "15-07", "30-08", "29-10"]
    gecerli_gunler = [g for g in gecerli_gunler if g.strftime("%d-%m") not in resmi_tatil_gunleri]

    gun_sayisi = len(gecerli_gunler)
    ortalama_gorev = toplam_gorev / gun_sayisi if gun_sayisi > 0 else 0

    arac_gorev_sayisi = talepler.values('talep_onay__arac__plaka')\
        .annotate(sayi=Count('id')).order_by('-sayi')

    ilce_gorev = talepler.values('gidilecek_ilce')\
        .annotate(sayi=Count('id')).order_by('-sayi')

    baskanlik_kullanim = talepler.values('baskanlik')\
        .annotate(sayi=Count('id')).order_by('-sayi')

    gunluk_gorevler = talepler.annotate(
        gun=Cast('gidis_tarihi', output_field=DateField())
    ).values('gun').annotate(sayi=Count('id')).order_by('gun')

    context = {
        'baslangic': baslangic,
        'bitis': bitis,
        'toplam_gorev': toplam_gorev,
        'ortalama_gorev': round(ortalama_gorev, 2),
        'arac_labels': json.dumps([i['talep_onay__arac__plaka'] for i in arac_gorev_sayisi]),
        'arac_data': json.dumps([i['sayi'] for i in arac_gorev_sayisi]),
        'ilce_labels': json.dumps([i['gidilecek_ilce'] for i in ilce_gorev]),
        'ilce_data': json.dumps([i['sayi'] for i in ilce_gorev]),
        'baskanlik_labels': json.dumps([i['baskanlik'] for i in baskanlik_kullanim]),
        'baskanlik_data': json.dumps([i['sayi'] for i in baskanlik_kullanim]),
        'gunluk_labels_json': json.dumps([i['gun'].strftime('%Y-%m-%d') for i in gunluk_gorevler]),
        'gunluk_data_json': json.dumps([i['sayi'] for i in gunluk_gorevler]),
    }

    return render(request, 'talep/analiz.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta, time
from collections import defaultdict, OrderedDict
from .models import AracTalep, Arac

from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.shortcuts import render
from .models import AracTalep, Arac

@login_required
def analiz_bos_saat_panel(request):
    if request.user.userprofile.rol != 'mudur':
        return HttpResponse("Yetkiniz yok.", status=403)

    bugun = timezone.now().date()
    baslangic_raw = request.GET.get("baslangic")
    bitis_raw = request.GET.get("bitis")

    if not baslangic_raw or not bitis_raw:
        bitis = bugun
        baslangic = bitis - timedelta(days=7)
    else:
        try:
            baslangic = datetime.strptime(baslangic_raw, "%Y-%m-%d").date()
            bitis = datetime.strptime(bitis_raw, "%Y-%m-%d").date()
        except:
            return HttpResponse("Geçersiz tarih")

    gun_sayisi = (bitis - baslangic).days + 1
    toplam_arac_sayisi = Arac.objects.count()

    if toplam_arac_sayisi == 0:
        return HttpResponse("Araç kaydı bulunamadı.")

    saat_dilimleri = OrderedDict({
        "08:00 - 09:00": 0,
        "09:00 - 10:00": 0,
        "10:00 - 11:00": 0,
        "11:00 - 12:00": 0,
        "12:00 - 13:00": 0,
        "13:00 - 14:00": 0,
        "14:00 - 15:00": 0,
        "15:00 - 16:00": 0,
        "16:00 - 17:00": 0,
    })

    toplam_bos_araclar = OrderedDict((k, 0) for k in saat_dilimleri)

    tum_araclar = Arac.objects.all()

    for tarih in (baslangic + timedelta(n) for n in range(gun_sayisi)):
        talepler = AracTalep.objects.filter(
            gidis_tarihi=tarih,
            talep_onay__durum__in=['onaylandi', 'tamamlandi']
        ).select_related("talep_onay")

        doluluk = defaultdict(list)
        for talep in talepler:
            arac = talep.talep_onay.arac
            bas = talep.gidis_saati
            bit = getattr(talep, 'tahmini_varis_saati', None) or time(17, 0)
            doluluk[arac.id].append((bas, bit))

        for start_str in toplam_bos_araclar.keys():
            s, e = start_str.split(" - ")
            start = datetime.strptime(s, "%H:%M").time()
            end = datetime.strptime(e, "%H:%M").time()

            bos_arac_sayisi = 0
            for arac in tum_araclar:
                kullanildi_mi = False
                for aralik in doluluk.get(arac.id, []):
                    if aralik[0] <= end and aralik[1] >= start:
                        kullanildi_mi = True
                        break
                if not kullanildi_mi:
                    bos_arac_sayisi += 1

            toplam_bos_araclar[start_str] += bos_arac_sayisi

    # Şimdi oranları % olarak hesapla
    ortalama_oranlar = OrderedDict()
    for saat_araligi, toplam_bos_sayi in toplam_bos_araclar.items():
        ortalama_bos = toplam_bos_sayi / gun_sayisi
        oran = (ortalama_bos / toplam_arac_sayisi) * 100
        ortalama_oranlar[saat_araligi] = round(oran, 2)

    context = {
        "saat_labels": list(ortalama_oranlar.keys()),
        "saat_values": list(ortalama_oranlar.values()),
        "baslangic": baslangic,
        "bitis": bitis,
    }

    return render(request, "talep/analiz_bos_saat.html", context)





