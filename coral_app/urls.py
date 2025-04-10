from django.urls import path
from django.views.generic import TemplateView
from . import analysis_views
from . import views
from .views import range_export

app_name = 'coral_app'

urlpatterns = [
   # path('show/', views.show_chart, name='show'),  # 渲染模板视图
    path('range_export/', views.range_export, name='range_export'),
    # sst动态趋势折线图
    path('sst_data/', views.sst_data, name='sst_data'),#api
    path('sst_chart1/', views.show_sst_chart1, name='sst_chart1'),#渲染视图
    #筛选查看
    path('sst_data_filtered/', views.sst_data_filtered, name='sst_data_filtered'),  # 配置数据获取的路由api
    path('sst_chart2/', views.sst_chart_view, name='sst_chart_view'),  # 配置sst_chart2视图的路由
    #时许分析
    path('dhw_sst_data/',views.dhw_sst_data,name='dhw_sst_data'),
    path('dhw_sst_chart/', views.dhw_sst_chart, name='dhw_sst_chart'),
    # 分析报告相关路由
    path('dashboard/', analysis_views.analysis_dashboard, name='analysis_dashboard'),
    path('data/', analysis_views.analysis_data, name='analysis_data'),
    path('export/', analysis_views.export_report, name='export_report'),  # 确保这行存在
    #zjq主页
    path('index/', views.index, name='index'),
    path('chart1/', views.chart1, name='chart1'),
    path('information/', views.information, name='information'),
#yolov5
    path('yolo-detection/', views.yolo_detection_view, name='yolo_detection'),
    path('process-detection/', views.process_detection, name='process_detection'),

]
