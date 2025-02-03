import uuid

from django.db import models


class TelegramUser(models.Model):
    user_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    is_super_admin = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_exchanger = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    balance = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')


    def __str__(self):
        return self.username if self.username else f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        return str(uuid.uuid4().hex[:10]).upper()


class City(models.Model):
    city_name = models.CharField(max_length=255)

    def __str__(self):
        return self.city_name


class Rayon(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    rayon_name = models.CharField(max_length=255)

    def __str__(self):
        return self.rayon_name


class Chapter(models.Model):
    chapter_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    photo = models.CharField(max_length=2555, null=True, blank=True)

    def __str__(self):
        return self.chapter_name


class GramPrice(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    gram = models.FloatField()
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.chapter} {self.gram} {self.price}"


class Product(models.Model):
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    rayon = models.ForeignKey(Rayon, on_delete=models.SET_NULL, null=True, blank=True)
    bought_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    gram = models.ForeignKey(GramPrice, on_delete=models.SET_NULL, null=True, blank=True)
    date_add = models.DateTimeField(auto_now_add=True)
    date_bought = models.DateTimeField(null=True, blank=True)
    address = models.TextField()
    reserved = models.BooleanField(default=False)


class Req(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    req_name = models.TextField()
    req = models.TextField()
    active = models.BooleanField(default=False)


class Invoice(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True, blank=True)
    req = models.CharField(max_length=2555)
    reserved_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    kzt_amount = models.PositiveIntegerField()
    crypto_amount = models.FloatField(null=True, blank=True)
    active = models.BooleanField(default=True)
    complete = models.BooleanField(default=False)
    unique_pod = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    withdrawed_to_shop = models.BooleanField(default=False)
    txid_withdrawed_to_shop = models.CharField(max_length=2555, null=True, blank=True)


class Text(models.Model):
    welcome = models.TextField()
    photo = models.TextField(null=True, blank=True)

class MainBot(models.Model):
    bot_token = models.CharField(max_length=255, null=True, blank=True)
    bot_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    pid = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Bot for {self.user.username} ({self.bot_name})"


class UserBot(models.Model):
    bot_token = models.CharField(max_length=255, null=True, blank=True)
    bot_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    pid = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)

class PromoCode(models.Model):
    code = models.CharField(max_length=5, unique=True, blank=True, null=True)
    amount = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        return str(uuid.uuid4().hex[:5]).upper()


class ShopConfiguration(models.Model):
    ref_percent = models.FloatField(default=2)
    name_of_shop = models.CharField(max_length=255, null=True, blank=True)
    USDT_TRC20 = models.CharField(max_length=2555, null=True, blank=True)


class Report(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Conversation(models.Model):
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class WithdrawInvoices(models.Model):
    invoices_to_withdraw = models.ManyToManyField(Invoice)
    complete = models.BooleanField(default=False)