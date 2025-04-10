from django.db import models
from django.urls import reverse
from django.utils.html import format_html

class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    region = models.CharField(max_length=255, db_index=True)  # 添加索引
    #region = models.CharField(max_length=255)
    sub_region = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    lon = models.DecimalField(max_digits=8, decimal_places=5)

    def range_export_button(self, request, queryset):
        url = reverse('range_export')
        return format_html(
            '<a class="button" href="{}">范围导出</a>',
            url
        )

    class Meta:
        managed = False
        db_table = 'locations'
        indexes = [  # 复合索引
            models.Index(fields=['region', 'sub_region']),
        ]

    range_export_button.short_description = '范围导出'

class MarineData(models.Model):
    data_id = models.AutoField(primary_key=True)
    location_id = models.ForeignKey(Location, on_delete=models.CASCADE, db_column='location_id')
    # date = models.DateField()
    date = models.DateField(db_index=True)  # 添加索引
    sea_surface_temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    hotspot_value = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    degree_heating_week = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'marine_data'
        ordering = ['-date']  # 默认排序

