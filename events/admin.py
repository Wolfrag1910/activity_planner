from django.contrib import admin

from .models import RSVP, Event, Guest


class RSVPInline(admin.TabularInline):
    model = RSVP
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "starts_at", "organizer", "status"]
    list_filter = ["category", "status"]
    inlines = [RSVPInline]


admin.site.register(Guest)
