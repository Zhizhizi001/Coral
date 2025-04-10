from django.contrib import admin
from .models import Location, MarineData
from openpyxl import Workbook
from django.http import HttpResponse

class ExportExcelMixin(object):
    def export_as_excel(self, request, queryset):
        #将查询集（queryset）导出为 Excel 文件
        meta = self.model._meta
        field_names = [field.name for field in meta.fields][1:]
        field_verbose_names = [field.verbose_name for field in meta.fields][1:]
        # 创建 Excel 文件
        response = HttpResponse(content_type='application/msexcel')
        filename = self.model._meta.verbose_name

        response['Content-Disposition'] = f'attachment; filename={filename.encode("utf-8").decode("ISO-8859-1")}.xlsx'
        wb = Workbook()
        ws = wb.active
        ws.append(field_verbose_names)
        # 填充数据
        for obj in queryset:
            data = []
            for field in field_names:
                if hasattr(obj, f'get_{field}_display'):
                    value = getattr(obj, f'get_{field}_display')()
                else:
                    value = getattr(obj, field)
                data.append(f'{value}')
            ws.append(data)
        # 返回 Excel 文件
        wb.save(response)
        return response
    export_as_excel.short_description = '导出Excel'
    export_as_excel.type = 'success'

class LocationAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ('location_id', 'region', 'sub_region', 'lat', 'lon')
    list_per_page = 50  # 分页：每页10条
    list_max_show_all = 200  # default    '''最大条目'''
    search_fields = ('region', 'sub_region') # 搜索框 ^, =, @, None=icontains
    # date_hierarchy = 'create_date'  #按日期分组
    empty_value_display = 'NA'  # 默认空值
    '''过滤选项'''
    list_filter = ('region', 'sub_region')
    actions = ['export_as_excel']
    # search_fields = ('region', 'sub_region')


class MarineDataAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ('data_id', 'location_id', 'date', 'sea_surface_temperature', 'hotspot_value', 'degree_heating_week')
    list_per_page = 50
    list_max_show_all = 200  # default    '''最大条目'''
    search_fields = ('location_id__region', 'date')
    #search_fields = ['title']  # 搜索框 ^, =, @, None=icontains
    empty_value_display = 'NA'  # 默认空值
    '''过滤选项'''
    list_filter = ('date', 'sea_surface_temperature', 'hotspot_value', 'degree_heating_week')
    actions = ['export_as_excel']

# Register your models here.
admin.site.register(Location, LocationAdmin)
admin.site.register(MarineData, MarineDataAdmin)


