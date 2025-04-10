// 初始化仪表盘图表
function initCharts() {
    // 从Django模板中获取数据
    const metrics = JSON.parse('{{ metrics_json|escapejs }}');
    const params = JSON.parse('{{ current_params_json|escapejs }}');

    // 初始化SST图表
    const sstChart = echarts.init(document.getElementById('sst-chart'));
    sstChart.setOption({
        title: {
            text: '海表温度趋势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: '{b}<br/>{a0}: {c0}°C'
        },
        xAxis: {
            type: 'category',
            data: metrics.dates,
            name: '日期'
        },
        yAxis: {
            type: 'value',
            name: '温度 (°C)',
            min: function(value) {
                return Math.floor(value.min - 2);
            }
        },
        series: [{
            name: '海表温度',
            data: metrics.sst_values,
            type: 'line',
            smooth: true,
            lineStyle: {
                color: '#1f77b4',
                width: 3
            },
            itemStyle: {
                color: '#1f77b4'
            },
            markLine: {
                silent: true,
                data: [{
                    yAxis: 30,
                    name: '白化阈值',
                    lineStyle: {
                        color: 'red',
                        type: 'dashed'
                    },
                    label: {
                        position: 'end',
                        formatter: '白化阈值'
                    }
                }]
            }
        }],
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        }
    });

    // 初始化DHW图表
    const dhwChart = echarts.init(document.getElementById('dhw-chart'));
    dhwChart.setOption({
        title: {
            text: '热压力指数趋势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: '{b}<br/>{a0}: {c0}°C-周'
        },
        xAxis: {
            type: 'category',
            data: metrics.dates,
            name: '日期'
        },
        yAxis: {
            type: 'value',
            name: '热压力 (°C-周)'
        },
        series: [{
            name: '热压力指数',
            data: metrics.dhw_values,
            type: 'line',
            smooth: true,
            lineStyle: {
                color: '#ff7f0e',
                width: 3
            },
            itemStyle: {
                color: '#ff7f0e'
            },
            markArea: {
                silent: true,
                data: [[{
                    yAxis: 4,
                    itemStyle: {
                        color: 'rgba(255, 173, 177, 0.4)'
                    }
                }, {
                    yAxis: 8
                }], [{
                    yAxis: 8,
                    itemStyle: {
                        color: 'rgba(255, 0, 0, 0.4)'
                    }
                }, {
                    yAxis: 100
                }]]
            },
            markLine: {
                silent: true,
                data: [{
                    yAxis: 4,
                    name: '警戒线',
                    lineStyle: {
                        color: 'orange',
                        type: 'dashed'
                    },
                    label: {
                        position: 'end',
                        formatter: '警戒线'
                    }
                }, {
                    yAxis: 8,
                    name: '危险线',
                    lineStyle: {
                        color: 'red',
                        type: 'dashed'
                    },
                    label: {
                        position: 'end',
                        formatter: '危险线'
                    }
                }]
            }
        }],
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        }
    });

    // 窗口大小变化时重新调整图表大小
    window.addEventListener('resize', function() {
        sstChart.resize();
        dhwChart.resize();
    });
}

// 初始化报告图表
function initReportCharts() {
    // 从Django模板中获取数据
    const metrics = JSON.parse('{{ metrics_json|escapejs }}');

    // SST报告图表
    const sstReportChart = echarts.init(document.getElementById('report-sst-chart'));
    sstReportChart.setOption({
        title: {
            text: '海表温度趋势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: metrics.dates,
            name: '日期'
        },
        yAxis: {
            type: 'value',
            name: '温度 (°C)'
        },
        series: [{
            name: '海表温度',
            data: metrics.sst_values,
            type: 'line',
            smooth: true,
            lineStyle: {
                width: 3
            },
            markLine: {
                data: [{
                    yAxis: 30,
                    name: '白化阈值',
                    lineStyle: {
                        color: 'red',
                        type: 'dashed'
                    }
                }]
            }
        }]
    });

    // DHW报告图表
    const dhwReportChart = echarts.init(document.getElementById('report-dhw-chart'));
    dhwReportChart.setOption({
        title: {
            text: '热压力指数趋势',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: metrics.dates,
            name: '日期'
        },
        yAxis: {
            type: 'value',
            name: '热压力 (°C-周)'
        },
        series: [{
            name: '热压力指数',
            data: metrics.dhw_values,
            type: 'line',
            smooth: true,
            lineStyle: {
                width: 3
            },
            markLine: {
                data: [{
                    yAxis: 4,
                    name: '警戒线',
                    lineStyle: {
                        color: 'orange',
                        type: 'dashed'
                    }
                }, {
                    yAxis: 8,
                    name: '危险线',
                    lineStyle: {
                        color: 'red',
                        type: 'dashed'
                    }
                }]
            }
        }]
    });

    // 窗口大小变化时重新调整图表大小
    window.addEventListener('resize', function() {
        sstReportChart.resize();
        dhwReportChart.resize();
    });
}

// AJAX获取图表数据
function fetchChartData(params) {
    return $.ajax({
        url: '/analysis/data/',
        type: 'GET',
        data: params,
        dataType: 'json'
    });
}

// 更新图表数据
function updateCharts(data) {
    const sstChart = echarts.getInstanceByDom(document.getElementById('sst-chart'));
    const dhwChart = echarts.getInstanceByDom(document.getElementById('dhw-chart'));

    sstChart.setOption({
        xAxis: {
            data: data.dates
        },
        series: [{
            data: data.sst_values
        }]
    });

    dhwChart.setOption({
        xAxis: {
            data: data.dates
        },
        series: [{
            data: data.dhw_values
        }]
    });
}