import streamlit as st
import pandas as pd
import pydeck as pdk
import io
import re
from pyproj import Transformer, CRS
from fpdf import FPDF
from datetime import datetime

# --- Yardımcı Fonksiyonlar ---

def to_excel(df, header_info):
    """Excel dosyası oluşturur ve biçimlendirir."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        start_row = 8 
        
        df.to_excel(writer, index=False, sheet_name='Report', startrow=start_row)
        
        workbook = writer.book
        worksheet = writer.sheets['Report']
        
        # --- Formatlar ---
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#2c3e50', 'align': 'left'})
        label_format = workbook.add_format({'bold': True, 'font_color': '#34495e', 'align': 'left'})
        text_format = workbook.add_format({'font_color': '#000000', 'align': 'left'})
        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#2980b9', 'font_color': 'white', 'border': 1})
        
        # --- Üst Bilgileri Yaz ---
        worksheet.write(0, 0, "📑 SiteWords Report", title_format)
        
        metadata = [
            ("Project:", header_info['project']),
            ("Work Order:", header_info['wo']),
            ("Client:", header_info['client']),
            ("Company:", header_info['company']),
            ("Date:", header_info['date']),
            ("Time:", header_info['time'])
        ]
        
        for i, (label, value) in enumerate(metadata):
            worksheet.write(2 + i, 0, label, label_format)
            worksheet.write(2 + i, 1, value, text_format)

        # --- Tablo Başlığını Biçimlendir ---
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(start_row, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
    return output.getvalue()

def to_csv(df):
    """CSV dosyası oluşturur."""
    return df.to_csv(index=False).encode('utf-8')

def to_html(df, header_info):
    """Stilize edilmiş HTML raporu oluşturur."""
    
    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
        
        .header-container {{ 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 15px; 
            margin-bottom: 20px; 
        }}
        
        .header-container h1 {{ 
            border: none; 
            margin: 0; 
            padding: 0; 
            color: #2c3e50;
            font-size: 28px;
        }}
        
        .meta-container {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #2980b9; }}
        .meta-row {{ display: flex; margin-bottom: 8px; align-items: center; }}
        .meta-icon {{ margin-right: 10px; font-size: 1.2em; }}
        .meta-label {{ font-weight: bold; width: 120px; color: #555; }}
        .meta-value {{ color: #000; }}
        table {{ border-collapse: collapse; width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: left; font-size: 14px; }}
        th {{ background-color: #2980b9; color: white; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e9ecef; }}
    </style>
    </head>
    <body>
    <div class="header-container">
        <h1>📑 SiteWords Report</h1>
    </div>
    
    <div class="meta-container">
        <div class="meta-row"><span class="meta-icon">🏗️</span><span class="meta-label">Project:</span><span class="meta-value">{header_info['project']}</span></div>
        <div class="meta-row"><span class="meta-icon">📋</span><span class="meta-label">Work Order:</span><span class="meta-value">{header_info['wo']}</span></div>
        <div class="meta-row"><span class="meta-icon">👤</span><span class="meta-label">Client:</span><span class="meta-value">{header_info['client']}</span></div>
        <div class="meta-row"><span class="meta-icon">🏢</span><span class="meta-label">Company:</span><span class="meta-value">{header_info['company']}</span></div>
        <div class="meta-row"><span class="meta-icon">📅</span><span class="meta-label">Date/Time:</span><span class="meta-value">{header_info['date']} | {header_info['time']}</span></div>
    </div>
    
    {df.to_html(index=False)}
    </body>
    </html>
    """
    return html.encode('utf-8')

def create_pdf(df, header_info):
    """Metin kaydırma ve dinamik düzen ile PDF raporu oluşturur."""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.set_text_color(44, 62, 80)
            self.cell(0, 10, 'SiteWords Report', 0, 1, 'L') 
            self.ln(5)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF(orientation='L', unit='mm', format='A4') 
    pdf.add_page()
    
    # --- Üst Bilgi Bölümü ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0)
    
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 25, 277, 35, 'F') 
    
    start_y = 30
    pdf.set_xy(15, start_y)
    pdf.cell(30, 8, "Project:", 0, 0, 'L')
    pdf.set_font('Arial', '', 12)
    
    safe_project = header_info['project'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 8, safe_project, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 6, "Work Order:", 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_wo = header_info['wo'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_wo, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 6, "Client:", 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_client = header_info['client'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_client, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 6, "Date/Time:", 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 6, f"{header_info['date']} | {header_info['time']}", 0, 1, 'L')
    
    pdf.ln(10)

    # --- Tablo Ayarları ---
    num_cols = len(df.columns)
    page_width = 277
    col_width = page_width / num_cols if num_cols > 0 else page_width
        
    font_size = 9
    if num_cols > 8: font_size = 7
    if num_cols > 12: font_size = 6
    
    line_height = pdf.font_size * 2
    
    # --- Tablo Başlığı ---
    pdf.set_font('Arial', 'B', font_size)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255)
    
    for col in df.columns:
        header_text = str(col).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_width, line_height, header_text[:20], border=1, align='C', fill=True)
    pdf.ln(line_height)
    
    # --- Tablo Satırları ---
    pdf.set_font('Arial', '', font_size)
    pdf.set_text_color(0)
    
    for index, row in df.iterrows():
        if pdf.get_y() > 180: 
            pdf.add_page()
            pdf.set_font('Arial', 'B', font_size)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255)
            for col in df.columns:
                header_text = str(col).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(col_width, line_height, header_text[:20], border=1, align='C', fill=True)
            pdf.ln(line_height)
            pdf.set_font('Arial', '', font_size)
            pdf.set_text_color(0)

        start_y = pdf.get_y()
        max_y = start_y
        
        for col in df.columns:
            text = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            
            x = pdf.get_x()
            y = pdf.get_y()
            
            pdf.multi_cell(col_width, line_height * 0.8, text, border=1, align='L')
            
            if pdf.get_y() > max_y:
                max_y = pdf.get_y()
                
            pdf.set_xy(x + col_width, y)
        
        pdf.set_y(max_y)

    output = pdf.output(dest='S')
    if isinstance(output, str):
        return output.encode('latin-1')
    return output

# --- Veri Ayrıştırma Fonksiyonları (İngilizce/Almanca Destekli) ---
@st.cache_data(show_spinner=False)
def convert_ne_to_latlon(df, easting_col, northing_col, source_epsg="epsg:32632"):
    try:
        source_crs = CRS(source_epsg)
        target_crs = CRS("epsg:4326")
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        valid_data = df.loc[pd.to_numeric(df[easting_col], errors='coerce').notna() & 
                            pd.to_numeric(df[northing_col], errors='coerce').notna()]
        if valid_data.empty: return pd.Series(None, index=df.index), pd.Series(None, index=df.index)
        lon, lat = transformer.transform(valid_data[easting_col].values, valid_data[northing_col].values)
        return pd.Series(lat, index=valid_data.index), pd.Series(lon, index=valid_data.index)
    except Exception: return pd.Series(None, index=df.index), pd.Series(None, index=df.index)

@st.cache_data(show_spinner=False)
def parse_task_log_sessions(file_content, region_code):
    sessions = []
    # EN/DE Mapping
    key_map = {
        "Date": "Date", "Datum": "Date", 
        "Time": "Time", "Zeit": "Time", 
        "Work Order": "Work Order", "Arbeitsauftrag": "Work Order", 
        "Project": "Project", "Projekt": "Project"
    }
    for block in re.split(r'\n\s*\n', file_content.strip()):
        lines = block.strip().split('\n')
        if not lines or not (lines[0].strip().startswith("Open WO") or lines[0].strip().startswith("Auftrag öffnen")): continue
        session_data = {}
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                prop, val = parts[1].strip(), "".join(parts[2:]).strip()
                clean_key = key_map.get(prop)
                if clean_key: session_data[clean_key] = val
        if 'Date' in session_data and 'Time' in session_data: sessions.append(session_data)
    if not sessions: return None
    df = pd.DataFrame(sessions)
    datetime_str = df['Date'] + ' ' + df['Time']
    date_format = '%m/%d/%Y %I:%M:%S %p' if region_code == "US" else '%d.%m.%Y %H:%M:%S'
    df['timestamp'] = pd.to_datetime(datetime_str, format=date_format, errors='coerce')
    if df['timestamp'].isnull().any():
        fallback = '%d.%m.%Y %H:%M:%S' if region_code == "US" else '%m/%d/%Y %I:%M:%S %p'
        df['timestamp'] = df['timestamp'].fillna(pd.to_datetime(datetime_str, format=fallback, errors='coerce'))
    return df.dropna(subset=['timestamp']).sort_values('timestamp')[['timestamp', 'Project', 'Work Order']]

@st.cache_data(show_spinner=False)
def parse_record_log(file_content, region_code):
    lines = file_content.splitlines()
    
    # EN/DE Header Row Detection
    header_index = next((i for i, line in enumerate(lines) if line.strip().startswith("Record Type") or line.strip().startswith("Datensatztyp")), -1)
    if header_index == -1: return None
    
    decimal_sep = '.' if region_code == 'US' else ','
    df = pd.read_csv(io.StringIO('\n'.join(lines[header_index:])), sep='\t', decimal=decimal_sep)
    df.columns = df.columns.str.strip()
    
    # Safely convert numeric columns for both EN/DE
    numeric_cols = ['Measured N', 'Measured E', 'Measured Elv', 'Gemess. Hochwert', 'Gemess. Rechtswert', 'Gemess. Höhe']
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
    # EN/DE Timestamp handling
    time_col_name = 'Local Time' if 'Local Time' in df.columns else 'Ortszeit'
    date_col_name = 'Date' if 'Date' in df.columns else 'Datum'
    
    if time_col_name in df.columns and date_col_name in df.columns:
        time_series = df[time_col_name].astype(str).str.replace(',', '.', regex=False)
        datetime_str = df[date_col_name].astype(str) + ' ' + time_series
        date_format = '%m/%d/%Y %H:%M:%S.%f' if region_code == "US" else '%d.%m.%Y %H:%M:%S.%f'
        fallback = '%d.%m.%Y %H:%M:%S.%f' if region_code == "US" else '%m/%d/%Y %H:%M:%S.%f'
        df['timestamp'] = pd.to_datetime(datetime_str, format=date_format, errors='coerce')
        df['timestamp'] = df['timestamp'].fillna(pd.to_datetime(datetime_str, format=fallback, errors='coerce'))
        return df.dropna(subset=['timestamp']).sort_values('timestamp')
    
    return None

def parse_latlon_value(coord_str):
    if not isinstance(coord_str, str): return None
    coord_str = coord_str.strip().replace(',', '.')
    if '°' in coord_str or "'" in coord_str or '"' in coord_str:
        match = re.search(r'(\d+)\D+(\d+)\D+([\d.]+)\D*([NSEW])', coord_str)
        if not match: return None
        deg, min, sec, direc = match.groups()
        dd = float(deg) + float(min) / 60 + float(sec) / 3600
        if direc in ['S', 'W']: dd *= -1
        return dd
    else:
        try: return float(coord_str)
        except (ValueError, TypeError): return None

# --- Streamlit UI Ayarları ---
st.set_page_config(page_title="SiteWords: Raporlama Aracı", layout="wide")

# Session State Başlatma
if 'app_mode' not in st.session_state:
    st.session_state['app_mode'] = 'Dashboard'
if 'report_data' not in st.session_state:
    st.session_state['report_data'] = None
if 'files_loaded' not in st.session_state:
    st.session_state['files_loaded'] = False

# --- UYGULAMA MODLARI ---

def show_dashboard():
    
    # Dosyalar henüz yüklenmediyse Upload ekranını göster
    if not st.session_state['files_loaded']:
        st.header('📋 SiteWords: Veri Yükleme') 
        st.divider()
        st.info('Başlamak için Bölge (Region) seçin ve TaskLog ile Record dosyalarını yükleyin.')
        
        col1, col2 = st.columns([1, 3])
        with col1:
            region_code = st.selectbox("Bölge Modu (Tarih/Ondalık)", ('EU', 'US'))
        with col2:
            uploaded_files = st.file_uploader("Log Dosyalarını Yükle", type=['txt'], accept_multiple_files=True)

        tasklog_file = next((f for f in uploaded_files if 'tasklog' in f.name.lower()), None)
        record_file = next((f for f in uploaded_files if 'record' in f.name.lower()), None)

        if tasklog_file and record_file:
            def decode_file(file):
                content = file.getvalue()
                try: return content.decode("utf-8-sig")
                except UnicodeDecodeError: return content.decode("utf-16")
            
            tasklog_string_data = decode_file(tasklog_file)
            record_string_data = decode_file(record_file)
            
            with st.spinner('Loglar ayrıştırılıyor ve birleştiriliyor...'):
                df_sessions = parse_task_log_sessions(tasklog_string_data, region_code)
                df_points = parse_record_log(record_string_data, region_code)
                
                # --- BİRLEŞTİRME MANTIĞI ---
                df = pd.DataFrame()
                if df_sessions is not None and df_points is not None:
                    df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                elif df_points is not None:
                    df = df_points
                    st.warning("TaskLog eşleşmedi. Sadece Record (Kayıt) verileri gösteriliyor.")
                else:
                    st.error("Kayıtları okuma hatası. Geçerli TaskLog ve Record dosyaları yüklediğinizden emin olun.")
                    return

            if not df.empty:
                # Koordinat İşleme (Çoklu Dil)
                lat_col = 'HA / Lat' if 'HA / Lat' in df.columns else 'Hz / Breite'
                lon_col = 'VA / Long' if 'VA / Long' in df.columns else 'V / Länge'
                
                df['lat'] = df[lat_col].apply(parse_latlon_value) if lat_col in df.columns else None
                df['lon'] = df[lon_col].apply(parse_latlon_value) if lon_col in df.columns else None
                
                missing = df['lat'].isnull()
                if missing.any():
                    e_col = 'Measured E' if 'Measured E' in df.columns else 'Gemess. Rechtswert'
                    n_col = 'Measured N' if 'Measured N' in df.columns else 'Gemess. Hochwert'
                    if e_col in df.columns and n_col in df.columns:
                        lc, lnc = convert_ne_to_latlon(df[missing], e_col, n_col)
                        df.loc[missing, 'lat'] = lc
                        df.loc[missing, 'lon'] = lnc
                
                # İşlenmiş veriyi kaydet
                st.session_state['processed_df'] = df
                st.session_state['files_loaded'] = True
                
                st.rerun()
            return

    # Dosyalar yüklendiyse Ana Dashboard ekranını göster
    if st.session_state['files_loaded']:
        head_col1, head_col2 = st.columns([4, 1])
        with head_col1:
            st.header('📋 SiteWords: Dashboard')
        with head_col2:
            st.write("") 
            if st.button("🗑️ Yüklenen Dosyaları Temizle", width='stretch'):
                st.session_state['files_loaded'] = False
                st.session_state['processed_df'] = None
                if 'dashboard_selection' in st.session_state:
                    del st.session_state['dashboard_selection']
                st.rerun()
                
        st.divider()
            
        df = st.session_state['processed_df']
        
        col_table, col_map = st.columns([1, 1])

        with col_table:
            st.subheader("🗃️ Saha Verisi Seçimi")
            st.caption("Raporlanacak satırları seçin. Hiçbir seçim yapılmazsa tüm satırlar dışa aktarılır.")
            
            df_display = df.copy().dropna(axis=1, how='all')
            
            event = st.dataframe(
                df_display, 
                key="dashboard_table", 
                width='stretch',
                height=600,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row"
            )
            
            selected_rows_indices = event.selection.rows
            st.session_state['dashboard_selection'] = selected_rows_indices
            
            if not selected_rows_indices:
                btn_text = "📄 Tüm Veriyi Raporla"
                help_text = "Satır seçilmedi. Tıklanırsa TÜM veri kullanılır."
                df_to_report = df_display
            else:
                btn_text = f"📄 Seçimi Raporla ({len(selected_rows_indices)} satır)"
                help_text = "Seçilen satırlardan rapor oluştur."
                df_to_report = df_display.iloc[selected_rows_indices]

            if st.button(btn_text, type="primary", help=help_text, width='stretch'):
                st.session_state['report_data'] = df_to_report
                st.session_state['app_mode'] = 'Report'
                st.rerun()

        with col_map:
            st.subheader("📍 Saha Haritası Görünümü")
            map_data_cols = ['lat', 'lon']
            
            # Dinamik nokta adı tespiti
            pt_col = "Point Name" if "Point Name" in df.columns else "Punktname"
            tooltip_html = "<b>Lat:</b> {lat}<br/><b>Lon:</b> {lon}"
            if pt_col in df.columns:
                map_data_cols.append(pt_col)
                tooltip_html = f"<b>Point Name:</b> {{{pt_col}}}<br/>" + tooltip_html
            
            map_data = df[map_data_cols].dropna(subset=['lat', 'lon'])

            if not map_data.empty:
                first_pt = map_data.iloc[[0]]
                view_state = pdk.ViewState(latitude=first_pt['lat'].iloc[0], longitude=first_pt['lon'].iloc[0], zoom=16, pitch=0)
                
                selected_indices = st.session_state.get('dashboard_selection', [])
                
                if selected_indices:
                    sel_idxs_pd = pd.Index(selected_indices)
                    valid_sel_idxs = sel_idxs_pd.intersection(map_data.index)
                    sel_pts = map_data.loc[valid_sel_idxs]
                    other_pts = map_data.loc[map_data.index.difference(valid_sel_idxs).difference([first_pt.index[0]])]
                else:
                    sel_pts = pd.DataFrame(columns=map_data.columns)
                    other_pts = map_data.loc[map_data.index.difference([first_pt.index[0]])]
                
                layers = [
                    pdk.Layer('ScatterplotLayer', data=other_pts, get_position='[lon, lat]', get_fill_color='[0, 100, 255]', get_radius=5, radius_units='pixels', pickable=True),
                    pdk.Layer('ScatterplotLayer', data=first_pt, get_position='[lon, lat]', get_fill_color='[255, 0, 0]', get_radius=8, radius_units='pixels', pickable=True)
                ]
                
                if not sel_pts.empty:
                    layers.append(pdk.Layer('ScatterplotLayer', data=sel_pts, get_position='[lon, lat]', get_fill_color='[0, 255, 0]', get_radius=8, radius_units='pixels'))
                
                carto_light_style = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
                st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, map_style=carto_light_style, tooltip={"html": tooltip_html}), height=600)
            else:
                st.info("Haritada gösterilecek koordinat bulunamadı.")

def show_report_generator():
    st.header("📄 Rapor Oluşturucu")
    
    if st.button("← Dashboard'a Dön"):
        st.session_state['app_mode'] = 'Dashboard'
        st.rerun()
        
    df_raw = st.session_state['report_data']
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Proje Detayları")
        def_proj = df_raw['Project'].iloc[0] if 'Project' in df_raw.columns else ""
        def_wo = df_raw['Work Order'].iloc[0] if 'Work Order' in df_raw.columns else ""
        
        r_project = st.text_input("Proje Adı", value=def_proj)
        r_wo = st.text_input("İş Emri", value=def_wo)
        r_client = st.text_input("Müşteri Adı", "Client XYZ")
        
    with c2:
        st.subheader("Rapor Metadatası")
        r_company = st.text_input("Şirket Adı", "My Surveying Co.")
        r_date = st.date_input("Rapor Tarihi", datetime.now())
        r_time = st.time_input("Rapor Saati", datetime.now())
    
    st.divider()
    
    # --- Sütun Seçimi (Çoklu Dil Destekli) ---
    all_columns = df_raw.columns.tolist()
    
    preferred_cols = [
        'Sub Type', 'Untertyp',
        'Point Name', 'Punktname',
        'Measured E', 'Gemess. Rechtswert',
        'Measured N', 'Gemess. Hochwert',
        'Measured Elv', 'Gemess. Höhe',
        'Precision H', 'Lagegenauigkeit',
        'Precision V', 'Höhengenauigkeit'
    ]
    
    selected_columns = []
    initial_selection = [c for c in preferred_cols if c in all_columns]
    
    with st.expander("⚙️ Veri Sütunlarını Seç (Aç/Kapat)", expanded=False):
        st.caption("Dışa aktarılacak raporda yer alacak sütunları seçin.")
        
        cols_grid = st.columns(5)
        
        for i, col_name in enumerate(all_columns):
            is_preferred = col_name in preferred_cols
            if cols_grid[i % 5].checkbox(col_name, value=is_preferred, key=f"chk_{i}"):
                selected_columns.append(col_name)
    
    if not selected_columns:
        st.warning("Hiçbir sütun seçilmedi. Varsayılan sütunlar aktarılacak.")
        cols_to_include = initial_selection
    else:
        cols_to_include = [c for c in all_columns if c in selected_columns]
        
    df_report = df_raw[cols_to_include]

    st.subheader(f"Rapor Önizleme ({len(df_report)} satır)")
    st.dataframe(df_report, width='stretch', hide_index=True)
    
    header_info = {
        "project": r_project, "wo": r_wo, "client": r_client,
        "company": r_company, "date": str(r_date), "time": str(r_time)
    }
    
    st.divider()
    st.subheader("Dışa Aktarma Seçenekleri")
    
    clean_project_name = re.sub(r'[^\w\-_]', '_', r_project) if r_project else "Project"
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        pdf_bytes = create_pdf(df_report, header_info)
        st.download_button(
            label="PDF İndir",
            data=pdf_bytes,
            file_name=f"Report_{clean_project_name}.pdf",
            mime="application/pdf",
            type="primary",
            width='stretch',
            key="btn_download_pdf"
        )
        
    with c2:
        excel_bytes = to_excel(df_report, header_info)
        st.download_button(
            label="Excel İndir",
            data=excel_bytes,
            file_name=f"Report_{clean_project_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
            key="btn_download_excel"
        )
        
    with c3:
        csv_bytes = to_csv(df_report)
        st.download_button(
            label="CSV İndir",
            data=csv_bytes,
            file_name=f"Report_{clean_project_name}.csv",
            mime="text/csv",
            width='stretch',
            key="btn_download_csv"
        )
        
    with c4:
        html_bytes = to_html(df_report, header_info)
        st.download_button(
            label="HTML İndir",
            data=html_bytes,
            file_name=f"Report_{clean_project_name}.html",
            mime="text/html",
            width='stretch',
            key="btn_download_html"
        )

# --- Ana Yönlendirici ---
if st.session_state['app_mode'] == 'Dashboard':
    show_dashboard()
elif st.session_state['app_mode'] == 'Report':
    show_report_generator()
