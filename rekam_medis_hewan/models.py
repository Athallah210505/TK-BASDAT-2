# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Adopsi(models.Model):
    pk = models.CompositePrimaryKey('id_adopter', 'id_hewan', 'tgl_mulai_adopsi')
    id_adopter = models.ForeignKey('Adopter', models.DO_NOTHING, db_column='id_adopter')
    id_hewan = models.ForeignKey('Hewan', models.DO_NOTHING, db_column='id_hewan')
    tgl_mulai_adopsi = models.DateField()
    status_pembayaran = models.CharField(max_length=10)
    tgl_berhenti_adopsi = models.DateField()
    kontribusi_finansial = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adopsi'


class Adopter(models.Model):
    username_adopter = models.OneToOneField('Pengunjung', models.DO_NOTHING, db_column='username_adopter', blank=True, null=True)
    id_adopter = models.UUIDField(primary_key=True)
    total_kontribusi = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adopter'


class Atraksi(models.Model):
    nama_atraksi = models.OneToOneField('Fasilitas', models.DO_NOTHING, db_column='nama_atraksi', primary_key=True)
    lokasi = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'atraksi'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Berpartisipasi(models.Model):
    pk = models.CompositePrimaryKey('nama_fasilitas', 'id_hewan')
    nama_fasilitas = models.ForeignKey('Fasilitas', models.DO_NOTHING, db_column='nama_fasilitas')
    id_hewan = models.ForeignKey('Hewan', models.DO_NOTHING, db_column='id_hewan')

    class Meta:
        managed = False
        db_table = 'berpartisipasi'


class CatatanMedis(models.Model):
    pk = models.CompositePrimaryKey('id_hewan', 'tanggal_pemeriksaan')
    id_hewan = models.ForeignKey('Hewan', models.DO_NOTHING, db_column='id_hewan')
    username_dh = models.ForeignKey('DokterHewan', models.DO_NOTHING, db_column='username_dh', blank=True, null=True)
    tanggal_pemeriksaan = models.DateField()
    diagnosis = models.CharField(max_length=100, blank=True, null=True)
    pengobatan = models.CharField(max_length=100, blank=True, null=True)
    status_kesehatan = models.CharField(max_length=50)
    catatan_tindak_lanjut = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'catatan_medis'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DokterHewan(models.Model):
    username_dh = models.OneToOneField('Pengguna', models.DO_NOTHING, db_column='username_dh', primary_key=True)
    no_str = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'dokter_hewan'


class Fasilitas(models.Model):
    nama = models.CharField(primary_key=True, max_length=50)
    jadwal = models.DateTimeField()
    kapasitas_max = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'fasilitas'


class Habitat(models.Model):
    nama = models.CharField(primary_key=True, max_length=50)
    luas_area = models.DecimalField(max_digits=65535, decimal_places=65535)
    kapasitas = models.IntegerField()
    status = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'habitat'


class Hewan(models.Model):
    id = models.UUIDField(primary_key=True)
    nama = models.CharField(max_length=100, blank=True, null=True)
    spesies = models.CharField(max_length=100)
    asal_hewan = models.CharField(max_length=100)
    tanggal_lahir = models.DateField(blank=True, null=True)
    status_kesehatan = models.CharField(max_length=50)
    nama_habitat = models.ForeignKey(Habitat, models.DO_NOTHING, db_column='nama_habitat', blank=True, null=True)
    url_foto = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'hewan'


class Individu(models.Model):
    nik = models.CharField(primary_key=True, max_length=16)
    nama = models.CharField(max_length=100)
    id_adopter = models.ForeignKey(Adopter, models.DO_NOTHING, db_column='id_adopter', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'individu'


class JadwalPemeriksaanKesehatan(models.Model):
    pk = models.CompositePrimaryKey('id_hewan', 'tgl_pemeriksaan_selanjutnya')
    id_hewan = models.ForeignKey(Hewan, models.DO_NOTHING, db_column='id_hewan')
    tgl_pemeriksaan_selanjutnya = models.DateField()
    freq_pemeriksaan_rutin = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'jadwal_pemeriksaan_kesehatan'


class JadwalPenugasan(models.Model):
    pk = models.CompositePrimaryKey('username_lh', 'tgl_penugasan')
    username_lh = models.ForeignKey('PelatihHewan', models.DO_NOTHING, db_column='username_lh')
    tgl_penugasan = models.DateTimeField()
    nama_atraksi = models.ForeignKey(Atraksi, models.DO_NOTHING, db_column='nama_atraksi', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jadwal_penugasan'


class Memberi(models.Model):
    pk = models.CompositePrimaryKey('id_hewan', 'jadwal')
    id_hewan = models.ForeignKey('Pakan', models.DO_NOTHING, db_column='id_hewan')
    jadwal = models.DateTimeField()
    username_jh = models.ForeignKey('PenjagaHewan', models.DO_NOTHING, db_column='username_jh', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'memberi'


class Organisasi(models.Model):
    npp = models.CharField(primary_key=True, max_length=8)
    nama_organisasi = models.CharField(max_length=100)
    id_adopter = models.ForeignKey(Adopter, models.DO_NOTHING, db_column='id_adopter', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organisasi'


class Pakan(models.Model):
    pk = models.CompositePrimaryKey('id_hewan', 'jadwal')
    id_hewan = models.ForeignKey(Hewan, models.DO_NOTHING, db_column='id_hewan')
    jadwal = models.DateTimeField()
    jenis = models.CharField(max_length=50)
    jumlah = models.IntegerField()
    status = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'pakan'


class PelatihHewan(models.Model):
    username_lh = models.OneToOneField('Pengguna', models.DO_NOTHING, db_column='username_lh', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'pelatih_hewan'


class Pengguna(models.Model):
    username = models.CharField(primary_key=True, max_length=50)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=50)
    nama_depan = models.CharField(max_length=50)
    nama_tengah = models.CharField(max_length=50, blank=True, null=True)
    nama_belakang = models.CharField(max_length=50)
    no_telepon = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'pengguna'


class Pengunjung(models.Model):
    username_p = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_p', primary_key=True)
    alamat = models.CharField(max_length=200)
    tgl_lahir = models.DateField()

    class Meta:
        managed = False
        db_table = 'pengunjung'


class PenjagaHewan(models.Model):
    username_jh = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_jh', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'penjaga_hewan'


class Reservasi(models.Model):
    pk = models.CompositePrimaryKey('username_p', 'nama_atraksi', 'tanggal_kunjungan')
    username_p = models.ForeignKey(Pengunjung, models.DO_NOTHING, db_column='username_p')
    nama_atraksi = models.ForeignKey(Atraksi, models.DO_NOTHING, db_column='nama_atraksi')
    tanggal_kunjungan = models.DateField()
    jumlah_tiket = models.IntegerField()
    status = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'reservasi'


class Spesialisasi(models.Model):
    pk = models.CompositePrimaryKey('username_sh', 'nama_spesialisasi')
    username_sh = models.ForeignKey(DokterHewan, models.DO_NOTHING, db_column='username_sh')
    nama_spesialisasi = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'spesialisasi'


class StafAdmin(models.Model):
    username_sa = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_sa', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'staf_admin'


class Wahana(models.Model):
    nama_wahana = models.OneToOneField(Fasilitas, models.DO_NOTHING, db_column='nama_wahana', primary_key=True)
    peraturan = models.TextField()

    class Meta:
        managed = False
        db_table = 'wahana'
