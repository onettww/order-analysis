from PyInstaller.utils.hooks import collect_all_data_files, copy_metadata

datas = copy_metadata('streamlit')

# 收集Streamlit的静态文件
static_files = collect_all_data_files('streamlit')
datas += static_files
