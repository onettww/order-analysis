#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单完工率分析系统
Order Completion Rate Analysis System

功能：
1. 完工率分析 - 分析计划待完工与实际完工数据（支持区域筛选）
2. 签到校验 - 检查上门签到时间是否在预约时间范围内
3. 历史记录 - 查看历史分析记录，支持手动修改标题

作者：MiniMax Agent
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
from io import BytesIO

# ============================================================================
# 页面配置 - 设置中文字体和页面属性
# ============================================================================
st.set_page_config(
    page_title="订单完工率分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': None,
        'Report a bug': None,
        'About': "订单完工率分析系统 v1.0"
    }
)

# 设置中文字体
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    .stApp {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    /* 侧边栏中文化 */
    [data-testid="stSidebar"] {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    /* 表格中文化 */
    .stDataFrame {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    /* 按钮样式 */
    .stButton > button {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    /* 提示信息样式 */
    .stSuccess, .stError, .stWarning, .stInfo {
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 自定义CSS样式
# ============================================================================
st.markdown("""
<style>
    /* 标题样式 */
    .main-title {
        font-size: 28px;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 20px;
    }
    
    .section-title {
        font-size: 22px;
        font-weight: bold;
        color: #333;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    
    /* 卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .metric-card.green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .metric-card.orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .metric-card.blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* 提示框样式 */
    .info-box {
        background: #E3F2FD;
        border-left: 4px solid #2196F3;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .warning-box {
        background: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .success-box {
        background: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    /* 筛选框样式 */
    .filter-box {
        background: #FAFAFA;
        border: 1px solid #E0E0E0;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    
    /* 历史记录样式 */
    .history-item {
        background: #F5F5F5;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
    }
    
    .history-item-no-title {
        background: #ECEFF1;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #9E9E9E;
    }
    
    /* 复制文字框样式 */
    .copy-text-box {
        background: #F5F5F5;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-size: 14px;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 数据存储路径
# ============================================================================
DATA_DIR = os.path.expanduser("~/order_analysis_data")
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# ============================================================================
# 初始化会话状态
# ============================================================================
def init_session_state():
    """初始化会话状态"""
    if 'history' not in st.session_state:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                st.session_state.history = json.load(f)
        else:
            st.session_state.history = []
    
    if 'plan_df' not in st.session_state:
        st.session_state.plan_df = None
    
    if 'actual_df' not in st.session_state:
        st.session_state.actual_df = None
    
    # 初始化筛选状态
    if 'selected_provinces' not in st.session_state:
        st.session_state.selected_provinces = []
    
    if 'selected_cities' not in st.session_state:
        st.session_state.selected_cities = []
    
    if 'filter_applied' not in st.session_state:
        st.session_state.filter_applied = False

def save_history():
    """保存历史记录到文件"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=2)

# ============================================================================
# 数据处理函数
# ============================================================================
def validate_and_process_data(plan_df, actual_df):
    """
    验证和处理数据
    - 重命名列名
    - 删除不需要的列
    """
    errors = []
    
    # 处理计划待完工数据
    if plan_df is not None:
        # 重命名列（兼容不同的列名）
        rename_map = {
            '来单时间': '工单创建时间',
            '省': '省份',      # 省 → 省份
            '市': '城市'       # 市 → 城市
        }
        plan_df = plan_df.rename(columns=rename_map)
        
        # 删除不需要的列
        cols_to_drop = ['预约完工时间']
        existing_cols_to_drop = [col for col in cols_to_drop if col in plan_df.columns]
        if existing_cols_to_drop:
            plan_df = plan_df.drop(columns=existing_cols_to_drop)
        
        # 清理城市名称（去掉末尾的"市"字，避免显示为"深圳市市"）
        if '城市' in plan_df.columns:
            plan_df.loc[:, '城市'] = plan_df['城市'].str.replace('市$', '', regex=True)
    
    # 处理实际完工数据
    if actual_df is not None:
        # 重命名列（兼容不同的列名）
        rename_map = {
            '省': '省份',      # 省 → 省份
            '市': '城市'       # 市 → 城市
        }
        actual_df = actual_df.rename(columns=rename_map)
        
        # 清理城市名称（去掉末尾的"市"字）
        if '城市' in actual_df.columns:
            actual_df.loc[:, '城市'] = actual_df['城市'].str.replace('市$', '', regex=True)
        
        # 确保必要的列存在
        required_cols = ['工单号', '省份', '城市', '完工时间']
        missing_cols = [col for col in required_cols if col not in actual_df.columns]
        if missing_cols:
            errors.append(f"实际完工表格缺少必要列：{', '.join(missing_cols)}")
        
        # 新增的列（用于签到校验）
        optional_cols = ['预约开始时间', '预约结束时间', '上门签到时间', '工人姓名', '旧机信息']
        missing_optional = [col for col in optional_cols if col not in actual_df.columns]
        if missing_optional:
            # 这些是可选的，签到校验功能会检查
            pass
    
    return plan_df, actual_df, errors

def analyze_data_by_region(plan_df, actual_df, selected_provinces=None, selected_cities=None):
    """
    按区域分析数据
    
    参数：
    - plan_df: 计划待完工数据
    - actual_df: 实际完工数据
    - selected_provinces: 选中的省份列表
    - selected_cities: 选中的城市列表
    
    返回：
    - 统计概览数据和区域详情表格
    """
    if plan_df is None or actual_df is None:
        return None
    
    # 初始化筛选条件
    if selected_provinces is None:
        selected_provinces = []
    if selected_cities is None:
        selected_cities = []
    
    # 筛选数据
    filtered_plan = plan_df.copy()
    filtered_actual = actual_df.copy()
    
    # 省份筛选
    if selected_provinces and len(selected_provinces) > 0:
        filtered_plan = filtered_plan[filtered_plan['省份'].isin(selected_provinces)]
        filtered_actual = filtered_actual[filtered_actual['省份'].isin(selected_provinces)]
    
    # 城市筛选
    if selected_cities and len(selected_cities) > 0:
        filtered_plan = filtered_plan[filtered_plan['城市'].isin(selected_cities)]
        filtered_actual = filtered_actual[filtered_actual['城市'].isin(selected_cities)]
    
    # 获取工单号集合
    plan_ids = set(filtered_plan['工单号'].dropna()) if '工单号' in filtered_plan.columns else set()
    actual_ids = set(filtered_actual['工单号'].dropna()) if '工单号' in filtered_actual.columns else set()
    
    # 计算各类订单数量
    total_plan = len(plan_ids)  # 计划待完工总数
    total_actual = len(actual_ids)  # 实际完工总数
    on_time_ids = plan_ids.intersection(actual_ids)  # 预约内完工（同时存在于两个表格）
    modified_ids = actual_ids.difference(plan_ids)  # 改单回收（只在实际完工中存在）
    
    # 计算完工率：新的公式（预约内完工+改单完工）/计划待完工×100%
    on_time_count = len(on_time_ids)
    modified_count = len(modified_ids)
    today_completed = on_time_count + modified_count  # 今日完工 = 预约内完工 + 改单回收
    completion_rate = (today_completed / total_plan * 100) if total_plan > 0 else 0
    
    # 按区域统计详细数据
    region_stats = analyze_region_details(filtered_plan, filtered_actual)
    
    return {
        'total_plan': total_plan,
        'total_actual': total_actual,
        'on_time': on_time_count,
        'modified': modified_count,
        'today_completed': today_completed,
        'completion_rate': completion_rate,
        'region_stats': region_stats
    }

def analyze_region_details(plan_df, actual_df):
    """
    按城市统计详细数据
    
    计算逻辑：
    - 计划待完工：该城市在计划表格中的工单数
    - 预约内完工：该城市在计划+实际表格中工单号一致的订单数
    - 改单回收：该城市在实际表格中，但工单号与计划表格不一致的订单数
    - 完工率：（预约内完工+改单回收）/ 计划待完工 × 100%
    """
    if plan_df is None or actual_df is None:
        return pd.DataFrame()
    
    # 确保有省份和城市列
    if '省份' not in plan_df.columns or '城市' not in plan_df.columns:
        return pd.DataFrame()
    
    # 获取所有城市
    all_cities = set(plan_df['城市'].dropna().unique())
    if '城市' in actual_df.columns:
        all_cities.update(actual_df['城市'].dropna().unique())
    
    # 初始化结果列表
    results = []
    
    for city in all_cities:
        # 该城市的计划数据
        city_plan = plan_df[plan_df['城市'] == city]
        city_plan_ids = set(city_plan['工单号'].dropna())
        plan_count = len(city_plan_ids)
        
        # 该城市的实际数据
        city_actual = actual_df[actual_df['城市'] == city]
        city_actual_ids = set(city_actual['工单号'].dropna())
        
        # 预约内完工：工单号一致
        on_time_count = len(city_plan_ids.intersection(city_actual_ids))
        
        # 改单回收：工单号不一致
        modified_count = len(city_actual_ids.difference(city_plan_ids))
        
        # 计算完工率：（预约内完工+改单回收）/ 计划待完工 × 100%
        today_completed = on_time_count + modified_count
        completion_rate = (today_completed / plan_count * 100) if plan_count > 0 else 0
        
        # 获取省份
        province = city_plan['省份'].iloc[0] if len(city_plan) > 0 else \
                   (city_actual['省份'].iloc[0] if len(city_actual) > 0 else '')
        
        results.append({
            '省份': province,
            '城市': city,
            '计划待完工': plan_count,
            '预约内完工': on_time_count,
            '改单回收': modified_count,
            '完工率': f"{completion_rate:.2f}%"
        })
    
    # 创建DataFrame并按计划待完工数量降序排序
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('计划待完工', ascending=False)
    
    return df

def analyze_checkin(actual_df):
    """
    分析签到时间是否在预约时间范围内
    """
    if actual_df is None:
        return None
    
    # 检查必要的列是否存在
    required_cols = ['预约开始时间', '预约结束时间', '上门签到时间']
    missing_cols = [col for col in required_cols if col not in actual_df.columns]
    if missing_cols:
        return {
            'available': False,
            'missing_cols': missing_cols,
            'message': f"数据中缺少签到校验所需的列：{', '.join(missing_cols)}"
        }
    
    # 复制数据进行处理
    df = actual_df.copy()
    
    # 转换时间列为datetime格式
    time_cols = ['预约开始时间', '预约结束时间', '上门签到时间']
    for col in time_cols:
        if col in df.columns:
            df.loc[:, col] = pd.to_datetime(df[col], errors='coerce')
    
    # 过滤掉上门签到时间为空的记录
    valid_df = df[df['上门签到时间'].notna()].copy()
    
    if len(valid_df) == 0:
        return {
            'available': True,
            'valid_count': 0,
            'invalid_count': 0,
            'excluded_count': len(df) - len(valid_df),
            'compliance_rate': 0,
            'details': pd.DataFrame(),
            'message': '所有记录的上门签到时间均为空，无法进行校验'
        }
    
    # 判断签到时间是否在预约时间范围内
    valid_df['签到状态'] = valid_df.apply(
        lambda row: '有效' if pd.notna(row['预约开始时间']) and pd.notna(row['预约结束时间']) 
        and row['预约开始时间'] <= row['上门签到时间'] <= row['预约结束时间'] 
        else '无效', axis=1
    )
    
    # 统计
    valid_count = len(valid_df[valid_df['签到状态'] == '有效'])
    invalid_count = len(valid_df[valid_df['签到状态'] == '无效'])
    excluded_count = len(df) - len(valid_df)
    compliance_rate = (valid_count / len(valid_df) * 100) if len(valid_df) > 0 else 0
    
    return {
        'available': True,
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'excluded_count': excluded_count,
        'compliance_rate': compliance_rate,
        'details': valid_df,
        'message': None
    }

# ============================================================================
# 页面组件
# ============================================================================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 10px 0;'>
            <span style='font-size: 24px;'>📊</span>
            <h2 style='margin: 10px 0; color: #1E88E5;'>订单完工率分析系统</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 导航")
        st.markdown("**选择页面**")
        
        # 页面选择
        page = st.radio(
            "选择页面",
            options=["数据导入", "完工率分析", "签到校验", "历史记录"],
            index=1,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 使用说明
        st.markdown("""
        <div style='background: #E3F2FD; padding: 15px; border-radius: 8px;'>
            <strong style='color: #1976D2;'>使用说明：</strong>
            <ol style='margin: 10px 0; padding-left: 20px;'>
                <li>先在「数据导入」上传XLSX文件</li>
                <li>在「完工率分析」查看分析结果</li>
                <li>在「签到校验」查看签到时间校验</li>
                <li>「历史记录」查看历史数据</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        return page

def render_data_import_page():
    """渲染数据导入页面"""
    st.markdown("""
    <div class='main-title'>
        📁 数据导入
    </div>
    """, unsafe_allow_html=True)
    
    # 提示信息
    st.markdown("""
    <div class='info-box'>
        <strong>📋 上传说明：</strong><br>
        请上传两个XLSX格式的文件。系统会自动进行数据分析和统计。
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: #F5F5F5; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h4 style='color: #333; margin-bottom: 15px;'>📋 计划待完工表格</h4>
            <p style='color: #666; font-size: 14px;'>
            <strong>必需列名：</strong><br>
            • 工单号<br>
            • 省<br>
            • 市<br>
            • 工单创建时间（原"来单时间"）<br>
            <br>
            <strong>注意：</strong>"预约完工时间"列将被自动删除
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        plan_file = st.file_uploader(
            "上传计划待完工表格 (XLSX)",
            type=['xlsx'],
            key='plan_file'
        )
        
        if plan_file:
            try:
                df = pd.read_excel(plan_file)
                st.session_state.plan_df = df
                # 重置筛选状态
                st.session_state.selected_provinces = []
                st.session_state.selected_cities = []
                st.session_state.filter_applied = False
                st.markdown(f"""
                <div class='success-box'>
                    ✅ 成功加载 {len(df)} 条计划待完工记录
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class='warning-box'>
                    ⚠️ 读取文件失败：{str(e)}
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #F5F5F5; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h4 style='color: #333; margin-bottom: 15px;'>✅ 实际完工表格</h4>
            <p style='color: #666; font-size: 14px;'>
            <strong>必需列名：</strong><br>
            • 工单号<br>
            • 省<br>
            • 市<br>
            • 完工时间<br>
            <br>
            <strong>签到校验新增列：</strong><br>
            • 预约开始时间<br>
            • 预约结束时间<br>
            • 上门签到时间<br>
            • 工人姓名<br>
            • 旧机信息
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        actual_file = st.file_uploader(
            "上传实际完工表格 (XLSX)",
            type=['xlsx'],
            key='actual_file'
        )
        
        if actual_file:
            try:
                df = pd.read_excel(actual_file)
                st.session_state.actual_df = df
                # 重置筛选状态
                st.session_state.selected_provinces = []
                st.session_state.selected_cities = []
                st.session_state.filter_applied = False
                st.markdown(f"""
                <div class='success-box'>
                    ✅ 成功加载 {len(df)} 条实际完工记录
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class='warning-box'>
                    ⚠️ 读取文件失败：{str(e)}
                </div>
                """, unsafe_allow_html=True)
    
    # 分析按钮
    if st.button("🚀 开始分析", type="primary", use_container_width=True):
        if st.session_state.plan_df is not None and st.session_state.actual_df is not None:
            # 验证和处理数据
            plan_df, actual_df, errors = validate_and_process_data(
                st.session_state.plan_df.copy(),
                st.session_state.actual_df.copy()
            )
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # 保存原始数据用于后续分析
                st.session_state.plan_df = plan_df
                st.session_state.actual_df = actual_df
                
                # 设置默认筛选（选中第一个省份）
                if '省份' in plan_df.columns:
                    provinces = plan_df['省份'].dropna().unique()
                    if len(provinces) > 0:
                        st.session_state.selected_provinces = [provinces[0]]
                
                st.session_state.selected_cities = []
                st.session_state.filter_applied = True
                
                # 分析数据
                result = analyze_data_by_region(
                    plan_df, actual_df,
                    st.session_state.selected_provinces,
                    st.session_state.selected_cities
                )
                st.session_state.analysis_result = result
                
                # 保存到历史记录
                save_to_history(result)
                
                st.success("✅ 分析完成！请切换到「完工率分析」或「签到校验」查看结果。")
        else:
            st.warning("⚠️ 请先上传两个数据文件")

def render_completion_analysis_page():
    """渲染完工率分析页面"""
    st.markdown("""
    <div class='main-title'>
        📊 完工率分析
    </div>
    """, unsafe_allow_html=True)
    
    if 'analysis_result' not in st.session_state or st.session_state.analysis_result is None:
        st.markdown("""
        <div class='warning-box'>
            ⚠️ 暂无分析数据。请先在「数据导入」页面上传数据并进行分析。
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 获取数据
    plan_df = st.session_state.plan_df
    actual_df = st.session_state.actual_df
    
    if plan_df is None or actual_df is None:
        return
    
    # 清理城市名称（确保一致）
    if '城市' in plan_df.columns:
        plan_df.loc[:, '城市'] = plan_df['城市'].str.replace('市$', '', regex=True)
    if '城市' in actual_df.columns:
        actual_df.loc[:, '城市'] = actual_df['城市'].str.replace('市$', '', regex=True)
    
    # 获取省份和城市列表
    provinces = list(plan_df['省份'].dropna().unique()) if '省份' in plan_df.columns else []
    all_cities = list(plan_df['城市'].dropna().unique()) if '城市' in plan_df.columns else []
    
    # ============================================================================
    # 区域筛选
    # ============================================================================
    st.markdown("""
    <div class='filter-box'>
        <h4 style='margin-bottom: 15px;'>🔍 区域筛选</h4>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # 省份多选框
        if provinces:
            default_index = 0 if not st.session_state.selected_provinces else \
                           provinces.index(st.session_state.selected_provinces[0]) if st.session_state.selected_provinces and st.session_state.selected_provinces[0] in provinces else 0
            selected_provinces = st.multiselect(
                "选择省份",
                options=provinces,
                default=[provinces[default_index]] if provinces else [],
                key='province_multiselect'
            )
        else:
            selected_provinces = []
            st.info("暂无省份数据")
    
    with col2:
        # 城市多选框
        # 如果选中了省份，只显示选中省份下的城市
        if selected_provinces and len(selected_provinces) > 0:
            cities_in_provinces = plan_df[plan_df['省份'].isin(selected_provinces)]['城市'].dropna().unique()
            available_cities = list(cities_in_provinces)
        else:
            # 不选省份时，显示全部城市
            available_cities = all_cities
        
        if available_cities:
            # 如果之前有选中的城市，且在可用城市列表中，则保持选中
            default_cities = [c for c in st.session_state.selected_cities if c in available_cities] if st.session_state.selected_cities else available_cities[:1] if available_cities else []
            selected_cities = st.multiselect(
                "选择城市",
                options=available_cities,
                default=default_cities,
                key='city_multiselect'
            )
        else:
            selected_cities = []
            st.info("暂无城市数据")
    
    with col3:
        # 筛选按钮
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("筛选", type="primary", use_container_width=True):
            # 更新筛选状态
            st.session_state.selected_provinces = selected_provinces
            st.session_state.selected_cities = selected_cities
            st.session_state.filter_applied = True
            
            # 重新分析数据
            result = analyze_data_by_region(plan_df, actual_df, selected_provinces, selected_cities)
            st.session_state.analysis_result = result
            
            st.success("✅ 筛选完成！")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================================
    # 统计概览（筛选后数据）
    # ============================================================================
    result = st.session_state.analysis_result
    
    st.markdown("### 📈 统计概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 36px;'>{result['total_plan']}</h3>
            <p style='margin: 5px 0;'>今日待完工</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card green'>
            <h3 style='margin: 0; font-size: 36px;'>{result['on_time']}</h3>
            <p style='margin: 5px 0;'>预约订单内完工</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card orange'>
            <h3 style='margin: 0; font-size: 36px;'>{result['modified']}</h3>
            <p style='margin: 5px 0;'>非预约内订单完工</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='metric-card blue'>
            <h3 style='margin: 0; font-size: 36px;'>{result['completion_rate']:.2f}%</h3>
            <p style='margin: 5px 0;'>完工率</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================================================
    # 可复制的文字说明
    # ============================================================================
    st.markdown("### 📋 统计说明")
    
    # 生成可复制的文字
    copy_text = f"今日待完工{result['total_plan']}单，今日完工{result['today_completed']}单，完工率{result['completion_rate']:.2f}%。其中预约订单内完工{result['on_time']}单，非预约内订单完工{result['modified']}单。"
    
    col_copy, col_button = st.columns([5, 1])
    
    with col_copy:
        st.markdown(f"""
        <div class='copy-text-box'>
            {copy_text}
        </div>
        """, unsafe_allow_html=True)
    
    with col_button:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("复制", type="secondary", use_container_width=True):
            st.code(copy_text, language=None)
            st.toast("已复制到剪贴板！", icon="✅")
    
    # ============================================================================
    # 区域详情数据
    # ============================================================================
    st.markdown("### 🗺️ 区域详情数据")
    
    region_stats = result['region_stats']
    
    if not region_stats.empty:
        # 显示表格
        st.dataframe(
            region_stats,
            use_container_width=True,
            hide_index=True
        )
        
        # 导出功能
        col_export, _ = st.columns([1, 3])
        with col_export:
            if st.button("📥 导出区域统计", use_container_width=True):
                # 导出到Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    region_stats.to_excel(writer, index=False, sheet_name='区域详情')
                
                st.download_button(
                    label="⬇️ 下载Excel文件",
                    data=output.getvalue(),
                    file_name=f"区域详情_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("暂无区域详情数据")

def render_checkin_validation_page():
    """渲染签到校验页面"""
    st.markdown("""
    <div class='main-title'>
        ✅ 签到校验
    </div>
    """, unsafe_allow_html=True)
    
    if 'actual_df' not in st.session_state or st.session_state.actual_df is None:
        st.markdown("""
        <div class='warning-box'>
            ⚠️ 暂无数据。请先在「数据导入」页面上传实际完工数据。
        </div>
        """, unsafe_allow_html=True)
        return
    
    actual_df = st.session_state.actual_df
    
    # 检查是否有签到数据
    required_cols = ['预约开始时间', '预约结束时间', '上门签到时间']
    missing_cols = [col for col in required_cols if col not in actual_df.columns]
    
    if missing_cols:
        st.markdown(f"""
        <div class='warning-box'>
            ⚠️ 数据中缺少签到校验所需的列：{', '.join(missing_cols)}<br>
            请确保实际完工表格包含以下列：预约开始时间、预约结束时间、上门签到时间
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 筛选条件
    col1, col2 = st.columns(2)
    
    with col1:
        # 时间筛选
        time_mode = st.radio(
            "时间模式",
            options=["日", "月"],
            horizontal=True,
            index=0
        )
        
        if time_mode == "日":
            selected_date = st.date_input(
                "选择日期",
                value=date.today(),
                max_value=date.today()
            )
        else:
            # 月份选择使用selectbox代替
            current_year = date.today().year
            current_month = date.today().month
            month_options = [(year, month) for year in range(current_year - 1, current_year + 1) for month in range(1, 13)]
            month_labels = [f"{year}-{month:02d}" for year, month in month_options]
            selected_month_tuple = st.selectbox(
                "选择月份",
                options=month_options,
                format_func=lambda x: f"{x[0]}-{x[1]:02d}",
                index=len(month_options) - 1
            )
    
    with col2:
        # 区域筛选
        if '省份' in actual_df.columns:
            provinces = ['全部'] + list(actual_df['省份'].dropna().unique())
            selected_provinces = st.multiselect(
                "选择省份",
                options=provinces,
                default=['全部']
            )
        else:
            selected_provinces = ['全部']
        
        if '城市' in actual_df.columns:
            cities = ['全部'] + list(actual_df['城市'].dropna().unique())
            selected_cities = st.multiselect(
                "选择城市",
                options=cities,
                default=['全部']
            )
        else:
            selected_cities = ['全部']
    
    # 筛选数据
    filtered_df = actual_df.copy()
    
    # 时间筛选
    if time_mode == "日" and selected_date:
        filtered_df.loc[:, '完工日期'] = pd.to_datetime(filtered_df['完工时间'], errors='coerce').dt.date
        filtered_df = filtered_df[filtered_df['完工日期'] == selected_date]
    elif time_mode == "月" and selected_month_tuple:
        selected_year, selected_month = selected_month_tuple
        filtered_df.loc[:, '完工年月'] = pd.to_datetime(filtered_df['完工时间'], errors='coerce')
        filtered_df = filtered_df[
            (filtered_df['完工年月'].dt.year == selected_year) & 
            (filtered_df['完工年月'].dt.month == selected_month)
        ]
    
    # 区域筛选
    if selected_provinces and '全部' not in selected_provinces:
        filtered_df = filtered_df[filtered_df['省份'].isin(selected_provinces)]
    
    if selected_cities and '全部' not in selected_cities:
        filtered_df = filtered_df[filtered_df['城市'].isin(selected_cities)]
    
    # 分析签到数据
    analysis = analyze_checkin(filtered_df)
    
    if analysis is None or not analysis.get('available', False):
        st.info("暂无签到数据可供分析")
        return
    
    # 显示统计结果
    st.markdown("### 📊 校验统计")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = analysis['valid_count'] + analysis['invalid_count']
        st.markdown(f"""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 24px;'>{total_orders}</h3>
            <p style='margin: 5px 0;'>总订单数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card green'>
            <h3 style='margin: 0; font-size: 24px;'>{analysis['valid_count']}</h3>
            <p style='margin: 5px 0;'>签到有效</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card orange'>
            <h3 style='margin: 0; font-size: 24px;'>{analysis['invalid_count']}</h3>
            <p style='margin: 5px 0;'>签到无效</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='metric-card blue'>
            <h3 style='margin: 0; font-size: 24px;'>{analysis['compliance_rate']:.2f}%</h3>
            <p style='margin: 5px 0;'>合格率</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 显示无效签到记录
    if analysis['invalid_count'] > 0:
        st.markdown("### ❌ 签到不在预约时间内订单详细")
        
        invalid_df = analysis['details'][analysis['details']['签到状态'] == '无效'].copy()
        
        # 准备显示的列
        display_cols = ['省份', '城市', '工单号', '工人姓名', '旧机信息', '完工时间', '预约开始时间', '预约结束时间', '上门签到时间']
        available_cols = [col for col in display_cols if col in invalid_df.columns]
        
        if available_cols:
            display_df = invalid_df[available_cols].copy()
            
            # 格式化时间列
            time_cols = ['完工时间', '预约开始时间', '预约结束时间', '上门签到时间']
            for col in time_cols:
                if col in display_df.columns:
                    # 检查是否是datetime类型
                    if pd.api.types.is_datetime64_any_dtype(display_df[col]):
                        display_df.loc[:, col] = display_df[col].dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        # 如果不是datetime类型，尝试转换
                        try:
                            temp_dates = pd.to_datetime(display_df[col], errors='coerce')
                            display_df.loc[:, col] = temp_dates.dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            # 转换失败，保留原值
                            pass
            
            # 合并省市作为区域
            if '省份' in display_df.columns and '城市' in display_df.columns:
                display_df.loc[:, '区域'] = display_df['省份'] + ' - ' + display_df['城市']
                # 调整列顺序
                cols = ['区域'] + [col for col in display_df.columns if col not in ['区域', '省份', '城市']]
                display_df = display_df[cols]
            
            # 显示表格
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 导出功能
            if st.button("📥 导出无效记录", use_container_width=True):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    display_df.to_excel(writer, index=False, sheet_name='无效签到记录')
                
                st.download_button(
                    label="⬇️ 下载Excel文件",
                    data=output.getvalue(),
                    file_name=f"无效签到记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.markdown("""
        <div class='success-box'>
            ✅ 所有订单的签到时间都在预约时间范围内！
        </div>
        """, unsafe_allow_html=True)

def render_history_page():
    """渲染历史记录页面"""
    st.markdown("""
    <div class='main-title'>
        📁 历史记录
    </div>
    """, unsafe_allow_html=True)
    
    # 时间筛选
    col1, col2 = st.columns(2)
    with col1:
        history_time_mode = st.radio(
            "时间筛选模式",
            options=["日", "月"],
            horizontal=True,
            index=0
        )
    
    with col2:
        if history_time_mode == "日":
            history_selected_date = st.date_input(
                "选择日期",
                value=date.today(),
                max_value=date.today(),
                key="history_date"
            )
        else:
            # 月份选择使用selectbox代替
            current_year = date.today().year
            current_month = date.today().month
            month_options = [(year, month) for year in range(current_year - 1, current_year + 1) for month in range(1, 13)]
            month_labels = [f"{year}-{month:02d}" for year, month in month_options]
            selected_month_tuple = st.selectbox(
                "选择月份",
                options=month_options,
                format_func=lambda x: f"{x[0]}-{x[1]:02d}",
                index=len(month_options) - 1,
                key="history_month"
            )
    
    # 获取过滤后的历史记录
    filtered_history = st.session_state.history.copy()
    
    # 时间筛选
    if history_time_mode == "日" and history_selected_date:
        filtered_history = [
            h for h in filtered_history 
            if 'analysis_date' in h and h['analysis_date'] == history_selected_date.strftime('%Y-%m-%d')
        ]
    elif history_time_mode == "月" and selected_month_tuple:
        selected_year, selected_month = selected_month_tuple
        month_str = f"{selected_year}-{selected_month:02d}"
        filtered_history = [
            h for h in filtered_history 
            if 'analysis_date' in h and h['analysis_date'].startswith(month_str)
        ]
    
    # 排序：未设置标题的在前，然后按日期降序
    filtered_history_sorted = sorted(
        filtered_history,
        key=lambda x: (x.get('custom_title') is None, x.get('analysis_date', '')),
        reverse=True
    )
    
    # 显示记录数量
    st.markdown(f"**共{len(filtered_history_sorted)}条记录**")
    
    if not filtered_history_sorted:
        st.markdown("""
        <div class='info-box'>
            📭 暂无历史记录
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 显示历史记录
    for idx, record in enumerate(filtered_history_sorted):
        with st.expander(expanded=False, label=f"记录: {record.get('custom_title', record.get('analysis_date', '未命名'))}"):
            # 生成标题
            if record.get('custom_title'):
                title = record['custom_title']
            else:
                # 使用完工日期作为标题（只显示年月日）
                analysis_date = record.get('analysis_date', '')
                if analysis_date:
                    title = f"完工日期: {analysis_date}"
                else:
                    title = "未设置标题"
            
            # 统计信息
            stats = record.get('stats', {})
            
            # 构建详情文本
            detail_text = f"""
            **统计信息：**
            - 计划待完工：{stats.get('total_plan', 0)}
            - 完工：{stats.get('total_actual', 0)}
            - 完工率：{stats.get('completion_rate', 0):.2f}%
            
            **分析时间：** {record.get('created_at', '')}
            """
            
            st.markdown(detail_text)
            
            # 编辑按钮
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("编辑标题", key=f"edit_{idx}"):
                    # 显示编辑表单
                    new_title = st.text_input(
                        "修改标题",
                        value=record.get('custom_title', ''),
                        key=f"title_input_{idx}"
                    )
                    
                    if st.button("保存", key=f"save_{idx}"):
                        # 更新标题
                        record['custom_title'] = new_title
                        save_history()
                        st.success("标题已更新！")
                        st.rerun()
            
            with col_delete:
                if st.button("删除记录", key=f"delete_{idx}"):
                    st.session_state.history.remove(record)
                    save_history()
                    st.success("记录已删除！")
                    st.rerun()

def save_to_history(result):
    """保存分析结果到历史记录"""
    if result is None:
        return
    
    # 创建历史记录
    history_item = {
        'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'analysis_date': date.today().strftime('%Y-%m-%d'),
        'custom_title': None,  # 用户可以手动设置标题
        'stats': {
            'total_plan': result['total_plan'],
            'total_actual': result['total_actual'],
            'on_time': result['on_time'],
            'modified': result['modified'],
            'completion_rate': result['completion_rate']
        }
    }
    
    # 添加到历史记录列表开头
    st.session_state.history.insert(0, history_item)
    
    # 保存到文件
    save_history()

# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    # 初始化会话状态
    init_session_state()
    
    # 渲染侧边栏并获取当前页面
    current_page = render_sidebar()
    
    # 根据当前页面渲染相应内容
    if current_page == "数据导入":
        render_data_import_page()
    elif current_page == "完工率分析":
        render_completion_analysis_page()
    elif current_page == "签到校验":
        render_checkin_validation_page()
    elif current_page == "历史记录":
        render_history_page()

if __name__ == "__main__":
    main()
