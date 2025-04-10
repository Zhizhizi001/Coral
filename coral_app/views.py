from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Avg, Max
from django.views.decorators.http import require_GET
from openpyxl import Workbook
from .models import Location, MarineData
from django.views.decorators.csrf import csrf_exempt
import cv2
import os
import torch
import numpy as np
import base64
import warnings
import sys
from pathlib import Path

# 全局变量用于存储加载的模型
loaded_models = {}


def check_requirements():
    """检查并安装必要的依赖"""
    try:
        import pkg_resources

        # 定义必需的包
        requirements = [
            'gitpython>=3.1.30',
            'requests>=2.32.2',
            'ultralytics'
        ]

        # 检查并安装缺失的包
        for requirement in requirements:
            try:
                pkg_resources.require(requirement)
            except pkg_resources.DistributionNotFound:
                print(f"Installing {requirement}...")
                os.system(f'pip install {requirement}')

    except Exception as e:
        print(f"Warning: Failed to check/install requirements: {e}")


def load_model(model_path):
    """
    根据模型文件名判断加载v5还是v8模型，使用缓存避免重复加载
    """
    try:
        # 如果模型已经加载过，直接返回缓存的模型
        if model_path in loaded_models:
            return loaded_models[model_path]

        # 抑制所有警告
        warnings.filterwarnings('ignore')

        model_name = model_path.lower()
        if 'v8' in model_name:
            from ultralytics import YOLO
            model = YOLO(model_path)
        else:
            # 设置环境变量以抑制某些警告
            os.environ['CUDA_VISIBLE_DEVICES'] = ''  # 强制使用CPU
            os.environ['TORCH_CUDA_ARCH_LIST'] = 'None'  # 禁用CUDA架构检查

            # 配置torch设置
            torch.backends.cudnn.enabled = False
            torch.backends.cuda.matmul.allow_tf32 = False

            # 加载模型
            model = torch.hub.load('ultralytics/yolov5',
                                   'custom',
                                   path=model_path,
                                   force_reload=False,  # 避免重复下载
                                   verbose=False)  # 减少输出信息

            # 禁用自动混合精度
            model.amp = False

            # 设置为评估模式
            model.eval()

        # 缓存加载的模型
        loaded_models[model_path] = model
        return model

    except Exception as e:
        raise Exception(f"模型加载失败: {str(e)}")


@csrf_exempt  # 仅用于测试，生产环境不建议使用
def process_detection(request):
    if request.method == 'POST':
        try:
            # 检查依赖项（仅在首次运行时）
            if not hasattr(process_detection, '_requirements_checked'):
                check_requirements()
                process_detection._requirements_checked = True

            # 获取上传的文件和参数
            uploaded_file = request.FILES['file']
            conf_thres = float(request.POST.get('conf_thres', 0.33))
            iou_thres = float(request.POST.get('iou_thres', 0.26))
            selected_model = request.POST.get('model', 'best.pt')

            # 构建模型完整路径
            model_path = os.path.join('./pt', selected_model)

            # 将上传的文件转换为OpenCV格式
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # 使用缓存机制加载模型
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = load_model(model_path)

            # 执行检测
            if 'v8' in selected_model.lower():
                results = model(img, conf=conf_thres, iou=iou_thres)[0]
                detection_results = []
                for box in results.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    name = results.names[class_id]
                    detection_results.append({
                        'xmin': float(x1),
                        'ymin': float(y1),
                        'xmax': float(x2),
                        'ymax': float(y2),
                        'confidence': confidence,
                        'name': name
                    })
            else:
                with torch.no_grad():
                    results = model(img)
                detection_results = results.pandas().xyxy[0].to_dict('records')

            # 在图像上绘制检测框
            for det in detection_results:
                x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                label = f"{det['name']} {det['confidence']:.2f}"

                color = (0, 255, 0) if det['name'] == 'Healthy' else (0, 0, 255)

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, color, 2)

            # 将处理后的图像转换为base64格式
            _, buffer = cv2.imencode('.jpg', img)
            processed_image_data = base64.b64encode(buffer).decode('utf-8')

            return JsonResponse({
                'status': 'success',
                'results': detection_results,
                'image': f"data:image/jpeg;base64,{processed_image_data}"
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=400)


def yolo_detection_view(request):
    # 获取可用的模型列表
    pt_list = [f for f in os.listdir('./pt') if f.endswith('.pt')]
    return render(request, 'coral_app/yolo_detection.html', {
        'pt_list': pt_list
    })


def index(request):
    """
    渲染系统首页
    """
    return render(request, 'coral_app/index.html')

def chart1(request):
    """
    渲染图表1页面，显示所有SST记录
    """
    records = MarineData.objects.all().values('location_id', 'date', 'sea_surface_temperature')
    return render(request, 'coral_app/chart1.html', context={'marine_data': records})

def range_export(request):
    """
    根据筛选条件导出数据到Excel
    """
    table = request.GET.get('table', 'locations')
    locations = []
    marine_data = []
    filter_applied = False

    if table == 'locations':
        locations = Location.objects.all()
        min_lat = request.GET.get('min_lat', '0')
        max_lat = request.GET.get('max_lat', '90')
        min_lon = request.GET.get('min_lon', '0')
        max_lon = request.GET.get('max_lon', '180')

        try:
            min_lat = float(min_lat)
            max_lat = float(max_lat)
            min_lon = float(min_lon)
            max_lon = float(max_lon)
        except ValueError:
            pass

        if (min_lat != 0 or max_lat != 90 or
                min_lon != 0 or max_lon != 180):
            locations = locations.filter(
                lat__gte=min_lat,
                lat__lte=max_lat,
                lon__gte=min_lon,
                lon__lte=max_lon
            )
            filter_applied = True

        paginator = Paginator(locations, 50)
        page_number = request.GET.get('page', 1)
        locations = paginator.get_page(page_number)

    elif table == 'marine_data':
        marine_data = MarineData.objects.all()
        min_lat = request.GET.get('min_lat', '0')
        max_lat = request.GET.get('max_lat', '90')
        min_lon = request.GET.get('min_lon', '0')
        max_lon = request.GET.get('max_lon', '180')
        min_sst = request.GET.get('min_sst', '0')
        max_sst = request.GET.get('max_sst', '100')

        try:
            min_lat = float(min_lat)
            max_lat = float(max_lat)
            min_lon = float(min_lon)
            max_lon = float(max_lon)
            min_sst = float(min_sst)
            max_sst = float(max_sst)
        except ValueError:
            pass

        if (min_lat != 0 or max_lat != 90 or
                min_lon != 0 or max_lon != 180 or
                min_sst != 0 or max_sst != 100):
            marine_data = marine_data.filter(
                location_id__lat__gte=min_lat,
                location_id__lat__lte=max_lat,
                location_id__lon__gte=min_lon,
                location_id__lon__lte=max_lon,
                sea_surface_temperature__gte=min_sst,
                sea_surface_temperature__lte=max_sst
            )
            filter_applied = True

        paginator = Paginator(marine_data, 50)
        page_number = request.GET.get('page', 1)
        marine_data = paginator.get_page(page_number)

    context = {
        'table': table,
        'locations': locations,
        'marine_data': marine_data,
        'filter_applied': filter_applied,
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon,
        'min_sst': min_sst,
        'max_sst': max_sst,
    }

    if 'export' in request.GET:
        return export_to_excel(locations if table == 'locations' else marine_data, table)

    return render(request, 'coral_app/range_export.html', context)

def export_to_excel(queryset, table):
    """
    导出数据到Excel
    """
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{table}.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = table

    if table == 'locations':
        ws.append(['Location ID', 'Region', 'Sub-Region', 'Latitude', 'Longitude'])
        for obj in queryset:
            ws.append([obj.location_id, obj.region, obj.sub_region, obj.lat, obj.lon])

    elif table == 'marine_data':
        ws.append(['Data ID', 'Location ID', 'Date', 'Sea Surface Temperature', 'Hotspot Value', 'Degree Heating Week'])
        for obj in queryset:
            ws.append([obj.data_id, obj.location_id.location_id, obj.date, obj.sea_surface_temperature, obj.hotspot_value, obj.degree_heating_week])

    wb.save(response)
    return response
############################################################################################################

def sst_data(request):
    try:
        locations = Location.objects.all()
        location_names = {loc.location_id: f"{loc.region} - {loc.sub_region}" for loc in locations}

        records = MarineData.objects.values('location_id', 'date').annotate(avg_sst=Avg('sea_surface_temperature')).order_by('date')
        dataset_raw = []

        for record in records:
            dataset_raw.append({
                "Date": record['date'].strftime('%Y-%m-%d'),
                "Year": record['date'].year,  # 添加 Year 字段
                "Location": location_names.get(record['location_id'], 'Unknown'),
                "sst": float(record['avg_sst']) if record['avg_sst'] else None
            })

        return JsonResponse(dataset_raw, safe=False)
    except Exception as e:
        print("发生错误:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

def show_sst_chart1(request):
    return render(request, 'coral_app/sst_chart1.html')
###########################################################################################################

def sst_data_filtered(request):
    filter_location = request.GET.get('filter_location', '')
    filter_year = request.GET.get('filter_year', '')

    records = MarineData.objects.all()

    if filter_location:
        records = records.filter(location_id__region=filter_location)

    if filter_year and filter_year.isdigit():
        records = records.filter(date__year=int(filter_year))

    if not records.exists():
        return JsonResponse({'current_sst': [], 'max_sst': []})

    # 按月份聚合数据
    current_sst = records.values('date__month').annotate(sst=Avg('sea_surface_temperature')).order_by('date__month')
    monthly_data = {entry['date__month']: entry['sst'] for entry in current_sst}

    # 填充12个月的数据，缺失则为 None
    current_sst_list = [monthly_data.get(month, None) for month in range(1, 13)]
    data = {
        'current_sst': current_sst_list
    }

    return JsonResponse(data)


def sst_chart_view(request):
    """
    渲染SST图表页面，并传递地点数据
    """
    locations = Location.objects.all()
    return render(request, 'coral_app/sst_chart2.html', {'locations': locations})
############################################################################################################
@require_GET
def dhw_sst_data(request):
    """获取DHW与SST关系数据"""
    try:
        # 1. 参数解析
        location_id = request.GET.get('location_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # 2. 基础查询集
        queryset = MarineData.objects.select_related('location_id').all()

        # 3. 应用过滤器
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        if start_date and end_date:
            queryset = queryset.filter(date__gte=start_date, date__lte=end_date)

        # 4. 数据格式处理
        data = queryset.values(
            'date',
            'sea_surface_temperature',
            'degree_heating_week',
            'location_id__region',
            'location_id__sub_region'
        ).order_by('date')

        # 5. 构建响应数据
        result = [{
            "date": item["date"].strftime("%Y-%m-%d"),
            "sst": float(item["sea_surface_temperature"]) if item["sea_surface_temperature"] is not None else 0,  # 确保 sst 为 0 而不是 None
            "dhw": float(item["degree_heating_week"]) if item["degree_heating_week"] is not None else 0,  # 确保 dhw 为 0 而不是 None
            "location": f"{item['location_id__region']} - {item['location_id__sub_region']}"
        } for item in data]

        # 返回数组格式的JSON数据
        return JsonResponse(result, safe=False)

    except Exception as e:
        # 返回错误信息
        return JsonResponse({"error": str(e)}, status=500)

def dhw_sst_chart(request):
    """渲染DHW与SST图表页面"""
    locations = Location.objects.all()
    return render(request, 'coral_app/dhw_sst_chart.html', {'locations': locations})

##############################################################################################################
def information(request):
    """
    渲染信息浏览页面
    """
    return render(request, 'coral_app/information.html')



