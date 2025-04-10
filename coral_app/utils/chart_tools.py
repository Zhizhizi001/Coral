
# chart_tools.py
import plotly.graph_objects as go
from plotly.offline import plot
import pandas as pd
from django.db.models import Min, Max
from datetime import date as dt_date, timedelta
import base64
from io import BytesIO


def generate_sst_trend(queryset):
    """生成海表温度趋势图（修复空数据问题）"""
    # 获取安全日期范围
    try:
        if queryset.exists():
            date_info = queryset.aggregate(
                min_date=Min('date'),
                max_date=Max('date')
            )
            min_date = date_info['min_date']
            max_date = date_info['max_date']
        else:
            min_date = dt_date.today() - timedelta(days=30)
            max_date = dt_date.today()
    except Exception as e:
        print(f"日期获取错误: {str(e)}")
        min_date = dt_date.today() - timedelta(days=30)
        max_date = dt_date.today()

    fig = go.Figure()

    if queryset.exists():
        try:
            df = pd.DataFrame.from_records(
                queryset.values('date', 'sea_surface_temperature')
            )
            if not df.empty and 'sea_surface_temperature' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['sea_surface_temperature'],
                    line=dict(color='#1f77b4'),
                    name='海表温度'
                ))
                fig.add_hline(y=30, line_dash="dot", line_color="red")
        except Exception as e:
            print(f"SST图表生成错误: {str(e)}")

    # 空数据提示
    if len(fig.data) == 0:
        fig.add_annotation(
            text="无可用数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        # 必须添加空轨迹以确保生成有效div
        fig.add_trace(go.Scatter(x=[], y=[]))

    # 统一布局配置
    fig.update_layout(
        title={'text': '海表温度变化趋势', 'x': 0.5},
        xaxis={'title': '日期', 'range': [min_date, max_date]},
        yaxis={'title': '温度 (°C)'},
        template='plotly_white'
    )
    return plot(fig, output_type='div', include_plotlyjs=True)  # 改为True确保包含JS


def generate_dhw_heatmap(queryset):
    """生成热压力分布图（增强稳定性）"""
    fig = go.Figure()
    df = pd.DataFrame()

    if queryset.exists():
        try:
            df = pd.DataFrame.from_records(
                queryset.values(
                    'location_id__lat',
                    'location_id__lon',
                    'degree_heating_week'
                )
            )
            if not df.empty and 'degree_heating_week' in df.columns:
                fig.add_trace(go.Densitymapbox(
                    lat=df['location_id__lat'],
                    lon=df['location_id__lon'],
                    z=df['degree_heating_week'],
                    radius=15,
                    colorscale='Hot',
                    colorbar={'title': 'DHW'},
                    hoverinfo='z'
                ))
        except Exception as e:
            print(f"生成DHW图表时出错: {str(e)}")

    # 空数据提示
    if len(fig.data) == 0:
        fig.add_annotation(
            text="无可用数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )

    # 地图配置
    center_lat = df['location_id__lat'].mean() if not df.empty else 0
    center_lon = df['location_id__lon'].mean() if not df.empty else 0

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox={
            'center': {'lat': center_lat, 'lon': center_lon},
            'zoom': 3 if not df.empty else 1
        },
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500
    )
    return plot(fig, output_type='div', include_plotlyjs=False)


def fig_to_base64(fig):
    """图表转Base64（用于PDF导出）"""
    buf = BytesIO()
    fig.write_image(buf, format='png', engine="kaleido")
    return base64.b64encode(buf.getvalue()).decode('utf-8')