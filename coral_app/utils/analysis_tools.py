import datetime
from django.db.models import Avg, Max, Min, F
from datetime import timedelta


def analyze_coral_health(queryset):
    """
    珊瑚健康智能分析（终极增强版）
    功能特点：
    1. 完整的风险等级评估体系
    2. 增强的可视化报告输出
    3. 智能建议生成系统
    4. 数据质量自动检测
    """
    # 基础数据检查
    if not queryset.exists():
        return {
            'status': 'error',
            'message': '没有可分析的数据'
        }

    # 核心指标计算
    metrics = {
        'data_count': queryset.count(),
        'avg_sst': queryset.aggregate(Avg('sea_surface_temperature'))['sea_surface_temperature__avg'] or 0,
        'max_sst': queryset.aggregate(Max('sea_surface_temperature'))['sea_surface_temperature__max'] or 0,
        'min_sst': queryset.aggregate(Min('sea_surface_temperature'))['sea_surface_temperature__min'] or 0,
        'max_dhw': queryset.aggregate(Max('degree_heating_week'))['degree_heating_week__max'] or 0,
        'hotspot_days': queryset.filter(degree_heating_week__gt=0).count(),
        'abnormal_days': queryset.filter(sea_surface_temperature__gt=30).count(),
        'missing_data': queryset.filter(sea_surface_temperature__isnull=True).count(),
        'data_range': {
            'start': queryset.earliest('date').date,
            'end': queryset.latest('date').date
        }
    }

    # 计算近期趋势（避免除零错误）
    recent_avg = queryset.filter(date__gte=F('date') - timedelta(days=7)) \
        .aggregate(Avg('sea_surface_temperature'))['sea_surface_temperature__avg']
    metrics['recent_trend'] = recent_avg if recent_avg is not None else metrics['avg_sst']

    # 数据质量分析
    quality_issues = []
    if metrics['max_sst'] > 35:
        quality_issues.append('极端高温数据')
    if metrics['min_sst'] < 10:
        quality_issues.append('异常低温数据')
    if metrics['missing_data'] > 0:
        quality_issues.append(f"{metrics['missing_data']}条缺失记录")
    metrics['data_quality'] = '良好' if not quality_issues else '，'.join(quality_issues)

    # 风险评估
    risk_factors = {
        'extreme_heat': metrics['max_sst'] > 32,
        'prolonged_heat': metrics['avg_sst'] > 30 and metrics['hotspot_days'] > 7,
        'acute_stress': metrics['max_dhw'] > 8,
        'chronic_stress': metrics['max_dhw'] > 4 and metrics['hotspot_days'] > 15
    }

    # 风险等级判定
    if risk_factors['extreme_heat'] or risk_factors['acute_stress']:
        risk_level = '紧急状态'
        action_required = True
    elif risk_factors['prolonged_heat'] or risk_factors['chronic_stress']:
        risk_level = '高风险'
        action_required = True
    elif metrics['max_dhw'] > 2:
        risk_level = '中等风险'
        action_required = False
    else:
        risk_level = '低风险'
        action_required = False

    # 报告模板配置
    risk_icons = {
        '紧急状态': '🔴',
        '高风险': '🟠',
        '中等风险': '🟡',
        '低风险': '🟢'
    }
    risk_descriptions = {
        '紧急状态': '检测到立即性白化风险！需采取紧急保护措施',
        '高风险': '持续高温压力，建议启动保护预案',
        '中等风险': '存在潜在压力，建议加强监测',
        '低风险': '环境指标正常，保持常规监测'
    }
    action_plans = {
        '紧急状态': [
            "• 立即启动白化应急响应预案",
            "• 部署实时监测浮标网络",
            "• 限制人类活动区域"
        ],
        '高风险': [
            "• 每日水下巡检",
            "• 部署遮阳设施",
            "• 准备珊瑚修复物资"
        ],
        '中等风险': [
            "• 每周2次水质检测",
            "• 记录珊瑚颜色变化",
            "• 备份生态样本"
        ],
        '低风险': [
            "• 维持常规监测",
            "• 每月生态影像记录",
            "• 设备维护检查"
        ]
    }

    # 报告生成
    duration_days = (metrics['data_range']['end'] - metrics['data_range']['start']).days or 1
    completeness = min(100, int(metrics['data_count'] / duration_days * 100))

    report = f"""
🌊 珊瑚礁健康评估报告 {'⭐' * 3}
────────────────────────────────
📅 监测期间：{metrics['data_range']['start'].strftime('%Y-%m-%d')} 至 {metrics['data_range']['end'].strftime('%Y-%m-%d')}
📊 数据统计：共 {duration_days} 天 | 有效数据 {metrics['data_count']} 条 ({completeness}% 完整度)

📌 核心指标
• 温度范围：{metrics['min_sst']:.1f}~{metrics['max_sst']:.1f}°C
• 平均温度：{metrics['avg_sst']:.1f}°C ({'↑' if metrics['recent_trend'] > metrics['avg_sst'] else '↓'} 近期趋势)
• 热压力值：{'▇' * int(metrics['max_dhw'])}{'○' * (8 - int(metrics['max_dhw']))} {metrics['max_dhw']:.1f} DHW

🚨 风险评估：{risk_icons.get(risk_level)} {risk_level}
{risk_descriptions.get(risk_level, '')}

🛠️ 推荐措施：
{chr(10).join(action_plans.get(risk_level, ['• 保持常规监测']))}

📝 数据质量：{'✅ 优良' if metrics['data_quality'] == '良好' else '⚠️ ' + metrics['data_quality']}
⏰ 报告生成：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
────────────────────────────────
    """

    return {
        'status': 'success',
        'metrics': {
            **metrics,
            'duration_days': duration_days,  # 新增字段
            'completeness': completeness  # 新增字段
        },
        # 'metrics': metrics,
        'risk_assessment': {
            'level': risk_level,
            'factors': [k for k, v in risk_factors.items() if v],
            'action_required': action_required
        },
        'recommendations': action_plans.get(risk_level, []),  # 新增建议列表
        'risk_icons': risk_icons,  # 新增图标字典
        'report': report.strip(),
        'data_quality': metrics['data_quality']
    }