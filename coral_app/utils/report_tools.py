import base64
import os
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, PageBreak, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from plotly import graph_objects as go
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
import datetime
from django.conf import settings
from django.contrib.staticfiles import finders


# 注册中文字体（需要在生成PDF前调用）
# 修改register_chinese_font函数，添加调试信息
def register_chinese_font():
    font_success = False
    try:
        pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
        print("成功加载SimSun字体")
        font_success = True
    except Exception as e:
        print(f"加载SimSun字体失败: {str(e)}")
        try:
            pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))
            print("成功加载SimHei字体")
            font_success = True
        except Exception as e:
            print(f"加载SimHei字体失败: {str(e)}")
            try:
                pdfmetrics.registerFont(TTFont('SimSun', 'fonts/simsun.ttc'))
                print("成功加载fonts/simsun.ttc")
                font_success = True
            except Exception as e:
                print(f"加载fonts/simsun.ttc失败: {str(e)}")
                try:
                    pdfmetrics.registerFont(TTFont('NotoSansCJK', 'NotoSansCJKsc-Regular.otf'))
                    print("成功加载NotoSansCJK字体")
                    font_success = True
                except Exception as e:
                    print(f"加载NotoSansCJK字体失败: {str(e)}")
    if not font_success:
        print("警告: 未能加载任何中文字体，PDF可能无法正确显示中文")
register_chinese_font()


def fig_to_base64(fig):
    """将Plotly图表转换为base64字符串"""
    # 添加engine参数，确保使用kaleido
    img_bytes = fig.to_image(format="png", engine="kaleido")
    return base64.b64encode(img_bytes).decode('utf-8')

def visual_dhw_bar(value):
    """生成热压力值的可视化条"""
    filled = min(8, int(value))
    empty = 8 - filled
    return f"{'▇' * filled}{'○' * empty} {value:.1f} DHW"


def generate_pdf_report(queryset, params):
    """生成完整的PDF报告"""
    # 准备数据
    analysis_result = params.get('analysis_result', {})
    metrics = analysis_result.get('metrics', {})
    risk_assessment = analysis_result.get('risk_assessment', {})

    # 直接使用 analysis 提供的基础数据
    date_range = metrics.get('data_range', {})
    start_date = date_range.get('start', datetime.date.today())
    end_date = date_range.get('end', datetime.date.today())
    duration_days = metrics.get('duration_days', (end_date - start_date).days or 1)
    completeness = metrics.get('completeness', min(100, int(metrics.get('data_count', 0)) / duration_days * 100))

    # 创建PDF文档
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.6 * inch,  # 上边距
        bottomMargin=0.6* inch  # 下边距
    )
    styles = getSampleStyleSheet()

    # 自定义样式
    chinese_style = ParagraphStyle(
        'ChineseStyle',
        parent=styles['Normal'],
        fontName='SimSun',
        leading=14
    )
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='SimSun',
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor('#1E3F66')
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='SimSun',
        spaceBefore=10,
        spaceAfter=10,
        textColor=colors.HexColor('#2C5E91')
    )
    risk_style = ParagraphStyle(
        'RiskStyle',
        parent=styles['BodyText'],
        backColor=colors.HexColor('#FFEEBA'),
        borderPadding=(10, 15, 10, 15),
        fontName='SimSun',
        spaceAfter=10,
        leading=16
    )

    elements = []
    # # 1. 报告标题
    logo_path = finders.find('images/logo.png')
    header_logo = Image(logo_path, width=1 * inch, height=1 * inch)
    # 创建一个表格来布局 logo 和标题
    data = [
        [header_logo, Paragraph("珊瑚礁健康评估报告", title_style), '']
    ]
    # 设置表格的列宽
    col_widths = [1 * inch, 3 * inch, 1 * inch]
    # 创建表格
    header_table = Table(data, colWidths=col_widths)
    # 设置表格样式
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # 所有内容居中
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 垂直居中
        ('LEFTPADDING', (0, 0), (0, 0), 0),  # logo 列的左内边距为 0
        ('RIGHTPADDING', (0, 0), (0, 0), 0),  # logo 列的右内边距为 0
    ]))
    # 添加表格到元素列表
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # 2. 基本信息
    meta_text = f"""
        <b>监测期间：</b>{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}<br/>
        <b>数据统计：</b>共 {duration_days} 天 | 有效数据 {metrics.get('data_count', 0)} 条 ({completeness:.0f}% 完整度)<br/>
        <b>数据质量：</b>{metrics.get('data_quality', '良好')}<br/>
        <b>报告生成：</b>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
    elements.append(Paragraph(meta_text, chinese_style))

    # 3. 风险评估
    elements.append(Paragraph("风险评估", section_style))
    risk_level = risk_assessment.get('level', '未知')
    risk_descriptions = {
        '紧急状态': '检测到立即性白化风险！需采取紧急保护措施',
        '高风险': '持续高温压力，建议启动保护预案',
        '中等风险': '存在潜在压力，建议加强监测',
        '低风险': '环境指标正常，保持常规监测'
    }
    risk_text = f"""
        <b>风险等级：</b>{analysis_result.get('risk_icons', {}).get(risk_level, '')} {risk_level}<br/>
        <b>风险描述：</b>{risk_descriptions.get(risk_level, '未知')}<br/>
        <b>风险因素：</b>{', '.join(risk_assessment.get('factors', [])) if risk_assessment.get('factors') else '无'}<br/>
        <b>行动建议：</b>{'需要立即行动' if risk_assessment.get('action_required', False) else '保持监测'}
        """
    elements.append(Paragraph(risk_text, risk_style))

    # 4. 核心指标
    elements.append(Paragraph("核心指标", section_style))
    # 温度指标表格
    temp_data = [
        ['指标', '数值', '说明'],
        ['最低温度', f"{metrics.get('min_sst', 0):.1f}°C", '监测期间最低海表温度'],
        ['最高温度', f"{metrics.get('max_sst', 0):.1f}°C", '监测期间最高海表温度'],
        ['平均温度', f"{metrics.get('avg_sst', 0):.1f}°C", '监测期间平均海表温度'],
        ['近期趋势', f"{metrics.get('recent_trend', 0):.1f}°C", '最近7天平均温度'],
        ['异常高温天数', f"{metrics.get('abnormal_days', 0)}天", '温度>30°C的天数']
    ]
    temp_table = Table(temp_data, colWidths=[1.8 * inch, 1.9 * inch, 2.8 * inch])
    temp_table.setStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ])
    elements.append(temp_table)
    elements.append(Spacer(1, 10))
    
    # 热压力指标表格
    dhw_value = metrics.get('max_dhw', 0)
    heat_data = [
        ['指标', '数值', '说明'],
        ['最大热压力值', f"{dhw_value:.1f} DHW", 'Degree Heating Week最大值'],
        ['热点天数', f"{metrics.get('hotspot_days', 0)}天", 'DHW>0的天数'],
        ['热压力水平', visual_dhw_bar(dhw_value), '热压力水平可视化']
    ]
    heat_table = Table(heat_data, colWidths=[1.8 * inch, 1.9 * inch,2.8 * inch])
    heat_table.setStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('WORDWRAP', (2, 0), (2, -1), True),
    ])
    elements.append(heat_table)

    # 5. 图表分析
    elements.append(Paragraph("趋势分析", section_style))
    df = pd.DataFrame.from_records(queryset.values(
        'date', 'sea_surface_temperature', 'degree_heating_week'
    ))
    if not df.empty:
        # 温度图表
        sst_fig = go.Figure()
        sst_fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['sea_surface_temperature'],
            name='海表温度',
            line=dict(color='#1f77b4')
        ))
        sst_fig.update_layout(
            title='海表温度趋势',
            xaxis_title='日期',
            yaxis_title='温度 (°C)'
        )
        sst_img = Image(BytesIO(base64.b64decode(fig_to_base64(sst_fig))), width=6 * inch, height=3 * inch)
        elements.append(sst_img)
        # 热压力图表
        dhw_fig = go.Figure()
        dhw_fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['degree_heating_week'],
            name='热压力指数',
            line=dict(color='#ff7f0e')
        ))
        dhw_fig.update_layout(
            title='热压力指数趋势',
            xaxis_title='日期',
            yaxis_title='DHW'
        )
        dhw_img = Image(BytesIO(base64.b64decode(fig_to_base64(dhw_fig))), width=6 * inch, height=3 * inch)
        elements.append(dhw_img)

    # 6. 建议措施
    elements.append(Paragraph("建议措施", section_style))
    for item in analysis_result.get('recommendations', []):
        elements.append(Paragraph(item, chinese_style))
        elements.append(Spacer(1, 8))
    # logo
    # 获取静态文件路径
    logo_path = finders.find('images/logo.png')
    # 添加logo到报告结尾
    try:
        footer_logo = Image(logo_path, width=2 * inch, height=2* inch)
        footer_logo.hAlign = 'RIGHT'
        elements.append(footer_logo)
    except:
        pass  # 如果logo不存在则跳过
    # 添加签名
    styles = getSampleStyleSheet()
    # 自定义签名样式：使用 SimSun 字体并加粗
    signature_style = ParagraphStyle(
        'signature',
        parent=styles['Normal'],
        fontName='SimSun',
        fontSize=12,
        alignment=2,  # 右对齐
        textColor='black',
        leading=14,  # 行间距
        fontWeight='bold'  # 加粗
    )

    signature = Paragraph('珊瑚卫士-南海珊瑚礁白化智能识别系统', signature_style)
    elements.append(signature)

    # 生成PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_excel_report(queryset, params):
    """生成Excel报告"""
    from openpyxl import Workbook
    buffer = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "珊瑚数据"

    # 写入标题行
    ws.append(['日期', '海表温度', '热压力指数'])

    # 写入数据
    for record in queryset.values('date', 'sea_surface_temperature', 'degree_heating_week'):
        ws.append([record['date'], record['sea_surface_temperature'], record['degree_heating_week']])

    wb.save(buffer)
    buffer.seek(0)
    return buffer