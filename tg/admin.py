from django.contrib import admin
from .models import TelegramUser, Product, Text, Chapter, Invoice, City, Rayon, GramPrice, Req, UserBot, WithdrawInvoices


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'balance', 'is_admin']


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['welcome']


@admin.register(Req)
class ReqAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(WithdrawInvoices)
class WithdrawInvoicesAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(Rayon)
class RayonAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(GramPrice)
class GramPriceAdmin(admin.ModelAdmin):
    list_display = ['id']


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = ['id']

