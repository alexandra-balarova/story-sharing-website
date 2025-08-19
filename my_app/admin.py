from django.contrib import admin
from my_app.models import Story, Chapter, Genre, Comment, Warning, Fandom, Profile, Reason, Report, Tag

admin.site.register(Profile)
admin.site.register(Genre)
admin.site.register(Warning)
admin.site.register(Fandom)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Reason)


class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 1

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'public')
    list_filter = ('public', 'genres', 'warnings')
    search_fields = ('title', 'author__username', 'synopsis')
    filter_horizontal = ('genres', 'warnings', 'fandoms')
    inlines = [ChapterInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'reporter', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reporter__username', 'text')
    actions = ['mark_as_resolved', 'mark_as_rejected']

    @admin.action(description="Mark selected reports as Resolved")
    def mark_as_resolved(self, request, queryset):
        for report in queryset:
            if report.status != 'Resolved':
                report.status = 'Resolved'
                report.save()

    @admin.action(description="Mark selected reports as Rejected")
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='Rejected')

admin.site.register(Report, ReportAdmin)

