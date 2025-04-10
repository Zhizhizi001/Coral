from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from .models import MarineData, Location
from .utils import analysis_tools, chart_tools, report_tools
from datetime import datetime, date
from django.contrib.auth.decorators import login_required

CACHE_TIMEOUT = 3600


def get_risk_level_class(level):
    return {
        '紧急状态': 'danger',
        '高风险': 'warning',
        '中等风险': 'info',
        '低风险': 'success'
    }.get(level, 'secondary')


def safe_date_parse(date_str, default):
    if not date_str:
        return default
    try:
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return default
    except Exception:
        return default


def get_base_data():
    cache_key = 'dashboard_base_data'
    data = cache.get(cache_key)
    if not data:
        try:
            data = {
                'min_date': MarineData.objects.earliest('date').date,
                'max_date': MarineData.objects.latest('date').date,
                'regions': list(Location.objects.values('region', 'sub_region').distinct())
            }
            cache.set(cache_key, data, CACHE_TIMEOUT)
        except MarineData.DoesNotExist:
            data = {
                'min_date': date(2000, 1, 1),
                'max_date': date.today(),
                'regions': []
            }
    return data


def analysis_dashboard(request):
    try:
        base_data = get_base_data()

        # 处理请求参数
        region_param = request.GET.get('region', 'all')
        start_date = safe_date_parse(request.GET.get('start_date'), base_data['min_date'])
        end_date = safe_date_parse(request.GET.get('end_date'), base_data['max_date'])

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # 构建查询集
        queryset = MarineData.objects.select_related('location_id').filter(
            date__range=(start_date, end_date)
        )

        # 区域筛选
        if region_param != 'all':
            if '-' in region_param:
                region, sub_region = region_param.split('-', 1)
                queryset = queryset.filter(
                    location_id__region=region,
                    location_id__sub_region=sub_region
                )
            else:
                queryset = queryset.filter(location_id__region=region_param)

        # 生成分析结果
        analysis_result = analysis_tools.analyze_coral_health(queryset) if queryset.exists() else None
        # 生成分析结果后存入缓存
        if analysis_result:
            cache_key = f"analysis_result_{request.GET.urlencode()}"
            cache.set(cache_key, analysis_result, 3000)  # 缓存50分钟
        # 安全获取指标
        metrics = analysis_result.get('metrics', {}) if analysis_result else {}

        context = {
            'sst_chart': chart_tools.generate_sst_trend(queryset),
            'dhw_chart': chart_tools.generate_dhw_heatmap(queryset),
            'metrics': {
                'min_sst': metrics.get('min_sst', 0),
                'max_sst': metrics.get('max_sst', 0),
                'avg_sst': metrics.get('avg_sst', 0),
                'hotspot_days': metrics.get('hotspot_days', 0),
                'max_dhw': metrics.get('max_dhw', 0)
            },
            'current_params': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'region': region_param
            },
            'date_range': {
                'min': base_data['min_date'].strftime('%Y-%m-%d'),
                'max': base_data['max_date'].strftime('%Y-%m-%d')
            },
            'regions': base_data['regions'],
            'health_analysis': analysis_result,
            'risk_level_class': get_risk_level_class(
                analysis_result.get('risk_assessment', {}).get('level', '未知') if analysis_result else '未知'
            )
        }
        return render(request, 'coral_app/analysis/dashboard.html', context)
    except Exception as e:
        return HttpResponse(f"服务器错误: {str(e)}", status=500)


# 保持analysis_data和export_report函数不变
def analysis_data(request):
    """AJAX数据接口"""
    try:
        # 参数处理
        start_date = safe_date_parse(request.GET.get('start_date'), date(2000, 1, 1))
        end_date = safe_date_parse(request.GET.get('end_date'), date.today())

        # 构建查询集
        queryset = MarineData.objects.filter(
            location_id__region=request.GET.get('region', 'all'),
            date__range=(start_date, end_date)
        )

        return JsonResponse({
            'sst_chart': chart_tools.generate_sst_trend(queryset),
            'dhw_chart': chart_tools.generate_dhw_heatmap(queryset)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def export_report(request):
    """导出分析报告"""
    try:
        # 获取基础数据
        base_data = get_base_data()
        
        # 获取查询参数，使用默认值
        start_date = request.GET.get('start_date', base_data['min_date'].strftime('%Y-%m-%d'))
        end_date = request.GET.get('end_date', base_data['max_date'].strftime('%Y-%m-%d'))
        region_param = request.GET.get('region', 'all')
        
        # 构建查询集
        queryset = MarineData.objects.select_related('location_id').all()
        
        # 应用日期过滤
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(date__range=[start_date_obj, end_date_obj])
        except ValueError:
            start_date_obj = base_data['min_date']
            end_date_obj = base_data['max_date']
        
        # 应用区域过滤
        if region_param != 'all':
            if '-' in region_param:
                region, sub_region = region_param.split('-', 1)
                queryset = queryset.filter(
                    location_id__region=region,
                    location_id__sub_region=sub_region
                )
            else:
                queryset = queryset.filter(location_id__region=region_param)
            
        # 获取分析结果
        cache_key = f"analysis_result_{request.GET.urlencode()}"
        analysis_result = cache.get(cache_key)
        
        if not analysis_result:
            # 生成新的分析结果
            analysis_result = analysis_tools.analyze_coral_health(queryset)
            if analysis_result:
                cache.set(cache_key, analysis_result, 3000)  # 缓存50分钟
        
        # 准备报告参数
        params = {
            'analysis_result': analysis_result
        }
        
        # 生成PDF报告
        pdf_buffer = report_tools.generate_pdf_report(queryset, params)
        
        # 准备响应
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="coral_health_report.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'导出失败: {str(e)}'}, status=500)
