from .models import MarineData
from django.db.models import Max


def calculate_climatic_baseline(location):
    """
    计算气候基准值（该地点的历史海表温度最大值）

    参数:
        location: Location 实例，表示具体的地点

    返回值:
        气候基准值（历史海表温度的最大值）
    """
    # 获取该地点的所有海表温度记录，计算最大值
    max_sst = MarineData.objects.filter(location_id=location).aggregate(Max('sea_surface_temperature'))
    # 如果有记录，返回最大值，否则返回0
    return max_sst['sea_surface_temperature__max'] if max_sst['sea_surface_temperature__max'] is not None else 0


def calculate_heat_stress_index(current_temperature, climatic_baseline):
    """
    计算热应力指数（当前海温与气候基准值的差值）

    参数:
        current_temperature: 当前观测到的海温（单位：摄氏度）
        climatic_baseline: 该地点的气候基准值（单位：摄氏度）

    返回值:
        热应力指数（单位：摄氏度）
    """
    # 当前温度与气候基准值的差值即为热应力指数
    return current_temperature - climatic_baseline


def detect_bleaching_event(heat_stress_index, critical_threshold=1.0, warning_threshold=0.5):
    """
    根据热应力指数判断是否发生珊瑚白化事件

    参数:
        heat_stress_index: 热应力指数（单位：摄氏度）
        critical_threshold: 临界阈值（单位：摄氏度），超过该阈值时认为发生严重白化，默认值为1.0
        warning_threshold: 警报阈值（单位：摄氏度），超过该阈值时认为可能发生白化，默认值为0.5

    返回值:
        白化事件状态：
            - 'Bleaching Warning: Critical Level'（严重白化）
            - 'Bleaching Warning: Possible'（可能发生白化）
            - 'No Bleaching Event Detected'（没有白化事件）
    """
    # 如果热应力指数超过临界阈值，则认为是严重白化事件
    if heat_stress_index >= critical_threshold:
        return "Bleaching Warning: Critical Level"
    # 如果热应力指数超过警报阈值，则认为可能发生白化事件
    elif heat_stress_index >= warning_threshold:
        return "Bleaching Warning: Possible"
    # 否则没有白化事件
    else:
        return "No Bleaching Event Detected"