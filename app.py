import streamlit as st
import pandas as pd
import pydeck as pdk
import io
import re
import math
from pyproj import Transformer, CRS
from fpdf import FPDF
from datetime import datetime

# --- UI Language Dictionary ---
UI_TEXT = {
    'en': {
        'upload_header': '📋 SiteWords: Data Upload',
        'upload_info': 'To begin, select your Region and upload both TaskLog and Record files.',
        'region_mode': 'Region Mode (Dates/Decimals)',
        'upload_files': 'Upload Log Files',
        'parsing_spinner': 'Parsing and joining logs...',
        'tasklog_missing': 'No TaskLog mapped. Showing Records only.',
        'parse_error': 'Error parsing records. Ensure valid TaskLog and Record files.',
        'dash_header': '📋 SiteWords: Dashboard',
        'clear_files': '🗑️ Clear Loaded Files',
        'field_data_sel': '🗃️ Field Data Selection',
        'sel_caption': 'Select rows to include in the report. If none are selected, all rows will be exported.',
        'report_all': '📄 Report All Data',
        'report_all_help': 'No rows selected. Clicking this will use ALL data.',
        'report_sel_base': '📄 Report Selection',
        'report_sel_help': 'Create report from selected rows.',
        'map_header': '📍 Site Map Overview',
        'map_caption': 'Interactive map view of the measurement points.',
        'map_pt_name': 'Point Name',
        'map_no_coord': 'No coordinates found to display on map.',
        'rep_header': '📄 Report Generator',
        'back_dash': '← Back to Dashboard',
        'proj_details': 'Project Details',
        'proj_name': 'Project Name',
        'work_order': 'Work Order',
        'client_name': 'Client Name',
        'rep_meta': 'Report Metadata',
        'company_name': 'Company Name',
        'rep_date': 'Report Date',
        'rep_time': 'Report Time',
        'col_sel_expander': '⚙️ Data Columns Selection (Click to Open/Close)',
        'col_sel_caption': 'Select columns to include in the exported report.',
        'col_warning': 'No columns selected. Export will contain default columns.',
        'rep_preview': 'Report Preview',
        'rows': 'rows',
        'export_opts': 'Export Options',
        'dl_pdf': 'Download PDF',
        'dl_excel': 'Download Excel',
        'dl_csv': 'Download CSV',
        'dl_html': 'Download HTML',
        'pdf_project': 'Project:',
        'pdf_wo': 'Work Order:',
        'pdf_client': 'Client:',
        'pdf_company': 'Company:',
        'pdf_datetime': 'Date/Time:',
        'pdf_date': 'Date:',
        'pdf_time': 'Time:',
        'pdf_page': 'Page',
        'pdf_title': 'SiteWords Report'
    },
    'de': {
        'upload_header': '📋 SiteWords: Daten-Upload',
        'upload_info': 'Wählen Sie Ihre Region und laden Sie TaskLog- und Record-Dateien hoch, um zu beginnen.',
        'region_mode': 'Region Modus',
        'upload_files': 'Log-Dateien hochladen',
        'parsing_spinner': 'Logs werden analysiert und verknüpft...',
        'tasklog_missing': 'Kein TaskLog zugeordnet. Es werden nur Records angezeigt.',
        'parse_error': 'Fehler beim Lesen der Dateien. Stellen Sie sicher, dass TaskLog und Record gültig sind.',
        'dash_header': '📋 SiteWords: Dashboard',
        'clear_files': '🗑️ Geladene Dateien löschen',
        'field_data_sel': '🗃️ Felddaten-Auswahl',
        'sel_caption': 'Wählen Sie die Zeilen für den Bericht aus. Ohne Auswahl werden alle Zeilen exportiert.',
        'report_all': '📄 Alle Daten berichten',
        'report_all_help': 'Keine Zeilen gewählt. ALLE Daten werden verwendet.',
        'report_sel_base': '📄 Auswahl berichten',
        'report_sel_help': 'Bericht aus ausgewählten Zeilen erstellen.',
        'map_header': '📍 Standortkarte Übersicht',
        'map_caption': 'Interaktive Kartenansicht der Messpunkte.',
        'map_pt_name': 'Punktname',
        'map_no_coord': 'Keine Koordinaten für die Karte gefunden.',
        'rep_header': '📄 Berichtsgenerator',
        'back_dash': '← Zurück zum Dashboard',
        'proj_details': 'Projektdetails',
        'proj_name': 'Projektname',
        'work_order': 'Arbeitsauftrag',
        'client_name': 'Kundenname',
        'rep_meta': 'Berichts-Metadaten',
        'company_name': 'Firmenname',
        'rep_date': 'Berichtsdatum',
        'rep_time': 'Berichtszeit',
        'col_sel_expander': '⚙️ Datenspalten-Auswahl (Klicken zum Öffnen/Schließen)',
        'col_sel_caption': 'Wählen Sie die Spalten für den exportierten Bericht.',
        'col_warning': 'Keine Spalten gewählt. Standardspalten werden exportiert.',
        'rep_preview': 'Berichtsvorschau',
        'rows': 'Zeilen',
        'export_opts': 'Exportoptionen',
        'dl_pdf': 'PDF herunterladen',
        'dl_excel': 'Excel herunterladen',
        'dl_csv': 'CSV herunterladen',
        'dl_html': 'HTML herunterladen',
        'pdf_project': 'Projekt:',
        'pdf_wo': 'Arbeitsauftrag:',
        'pdf_client': 'Kunde:',
        'pdf_company': 'Firma:',
        'pdf_datetime': 'Datum/Zeit:',
        'pdf_date': 'Datum:',
        'pdf_time': 'Zeit:',
        'pdf_page': 'Seite',
        'pdf_title': 'SiteWords Bericht'
    }
}

# --- Helper Functions ---

def to_excel(df, header_info, lang):
    """Generates and formats an Excel file."""
    ui = UI_TEXT[lang]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        start_row = 8 
        
        df.to_excel(writer, index=False, sheet_name='Report', startrow=start_row)
        
        workbook = writer.book
        worksheet = writer.sheets['Report']
        
        # --- Formats ---
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#2c3e50', 'align': 'left'})
        label_format = workbook.add_format({'bold': True, 'font_color': '#34495e', 'align': 'left'})
        text_format = workbook.add_format({'font_color': '#000000', 'align': 'left'})
        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#2980b9', 'font_color': 'white', 'border': 1})
        
        # --- Write Metadata ---
        worksheet.write(0, 0, f"📑 {ui['pdf_title']}", title_format)
        
        metadata = [
            (ui['pdf_project'], header_info['project']),
            (ui['pdf_wo'], header_info['wo']),
            (ui['pdf_client'], header_info['client']),
            (ui['pdf_company'], header_info['company']),
            (ui['pdf_date'], header_info['date']),
            (ui['pdf_time'], header_info['time'])
        ]
        
        for i, (label, value) in enumerate(metadata):
            worksheet.write(2 + i, 0, label, label_format)
            worksheet.write(2 + i, 1, value, text_format)

        # --- Format Table Header ---
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(start_row, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
    return output.getvalue()

def to_csv(df):
    """Generates a CSV file."""
    return df.to_csv(index=False).encode('utf-8')

def to_html(df, header_info, lang):
    """Generates a stylized HTML report."""
    ui = UI_TEXT[lang]
    
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
        <h1>📑 {ui['pdf_title']}</h1>
    </div>
    
    <div class="meta-container">
        <div class="meta-row"><span class="meta-icon">🏗️</span><span class="meta-label">{ui['pdf_project']}</span><span class="meta-value">{header_info['project']}</span></div>
        <div class="meta-row"><span class="meta-icon">📋</span><span class="meta-label">{ui['pdf_wo']}</span><span class="meta-value">{header_info['wo']}</span></div>
        <div class="meta-row"><span class="meta-icon">👤</span><span class="meta-label">{ui['pdf_client']}</span><span class="meta-value">{header_info['client']}</span></div>
        <div class="meta-row"><span class="meta-icon">🏢</span><span class="meta-label">{ui['pdf_company']}</span><span class="meta-value">{header_info['company']}</span></div>
        <div class="meta-row"><span class="meta-icon">📅</span><span class="meta-label">{ui['pdf_datetime']}</span><span class="meta-value">{header_info['date']} | {header_info['time']}</span></div>
    </div>
    
    {df.to_html(index=False)}
    </body>
    </html>
    """
    return html.encode('utf-8')

def create_pdf(df, header_info, lang):
    """Generates a PDF report with text wrapping and dynamic layouts."""
    ui = UI_TEXT[lang]
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.set_text_color(44, 62, 80)
            title_text = ui['pdf_title'].encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 10, title_text, 0, 1, 'L') 
            self.ln(5)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128)
            page_text = f"{ui['pdf_page']} {self.page_no()}"
            self.cell(0, 10, page_text, 0, 0, 'C')

    pdf = PDF(orientation='L', unit='mm', format='A4') 
    pdf.add_page()
    
    # --- Metadata Section ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0)
    
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(10, 25, 277, 35, 'F') 
    
    start_y = 30
    pdf.set_xy(15, start_y)
    
    lbl_project = ui['pdf_project'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 8, lbl_project, 0, 0, 'L')
    pdf.set_font('Arial', '', 12)
    
    safe_project = header_info['project'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 8, safe_project, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_wo = ui['pdf_wo'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_wo, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_wo = header_info['wo'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_wo, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_client = ui['pdf_client'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_client, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    safe_client = header_info['client'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(100, 6, safe_client, 0, 1, 'L')
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 10)
    lbl_dt = ui['pdf_datetime'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(30, 6, lbl_dt, 0, 0, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 6, f"{header_info['date']} | {header_info['time']}", 0, 1, 'L')
    
    pdf.ln(10)

    # --- Table Settings ---
    num_cols = len(df.columns)
    page_width = 277
    col_width = page_width / num_cols if num_cols > 0 else page_width
        
    font_size = 9
    if num_cols > 8: font_size = 7
    if num_cols > 12: font_size = 6
    
    line_height = pdf.font_size * 2
    
    # --- Table Header ---
    pdf.set_font('Arial', 'B', font_size)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255)
    
    for col in df.columns:
        header_text = str(col).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(col_width, line_height, header_text[:20], border=1, align='C', fill=True)
    pdf.ln(line_height)
    
    # --- Table Rows ---
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

# --- Data Parsing Functions (EN/DE Supported) ---
def parse_latlon_value(coord_str):
    if pd.isna(coord_str): return None
    if isinstance(coord_str, (int, float)): return float(coord_str)
    
    coord_str = str(coord_str).strip().replace(',', '.')
    
    if '°' in coord_str or "'" in coord_str or '"' in coord_str:
        match = re.search(r'(\d+)\D+(\d+)\D+([\d.]+)\D*([NSEW])?', coord_str)
        if not match: return None
        deg = float(match.group(1))
        min = float(match.group(2))
        sec = float(match.group(3))
        direc = match.group(4)
        dd = deg + min / 60 + sec / 3600
        if direc in ['S', 'W']: dd *= -1
        return dd
    else:
        try: 
            return float(coord_str)
        except (ValueError, TypeError): 
            return None

@st.cache_data(show_spinner=False)
def process_coordinates(df):
    """
    Advanced coordinate processor. 
    It auto-detects if Trimble exported coordinates in DD.MMSSssss format 
    by validating against UTM derived coordinates.
    """
    lat_col = 'HA / Lat' if 'HA / Lat' in df.columns else 'Hz / Breite'
    lon_col = 'VA / Long' if 'VA / Long' in df.columns else 'V / Länge'
    e_col = 'Measured E' if 'Measured E' in df.columns else 'Gemess. Rechtswert'
    n_col = 'Measured N' if 'Measured N' in df.columns else 'Gemess. Hochwert'
    
    df['__lat_raw'] = df[lat_col].apply(parse_latlon_value) if lat_col in df.columns else None
    df['__lon_raw'] = df[lon_col].apply(parse_latlon_value) if lon_col in df.columns else None
    df['__e'] = df[e_col] if e_col in df.columns else None
    df['__n'] = df[n_col] if n_col in df.columns else None

    def decode_dms(val):
        if pd.isna(val): return val
        sign = -1 if val < 0 else 1
        val = abs(val)
        d = int(val)
        m = int((val - d) * 100)
        s = (val - d - m / 100) * 10000
        return sign * (d + m / 60 + s / 3600)

    use_dms = False
    valid_mask = df['__lat_raw'].notna() & df['__lon_raw'].notna() & df['__e'].notna() & df['__n'].notna()
    if valid_mask.any():
        idx = valid_mask.idxmax()
        raw_lat = df.loc[idx, '__lat_raw']
        raw_lon = df.loc[idx, '__lon_raw']
        e_val = df.loc[idx, '__e']
        n_val = df.loc[idx, '__n']
        
        zone = 32
        if e_val > 31000000 and e_val < 34000000:
            zone = int(e_val / 1000000)
            e_val = e_val % 10000000
        elif raw_lon > 0:
            zone = int(raw_lon / 6) + 31
            
        epsg_code = f"epsg:{32600 + zone}" if raw_lat >= 0 else f"epsg:{32700 + zone}"
        
        try:
            transformer = Transformer.from_crs(epsg_code, "epsg:4326", always_xy=True)
            utm_lon, utm_lat = transformer.transform(e_val, n_val)
            
            lat_dms = decode_dms(raw_lat)
            lon_dms = decode_dms(raw_lon)
            
            dist_dd = (raw_lat - utm_lat)**2 + (raw_lon - utm_lon)**2
            dist_dms = (lat_dms - utm_lat)**2 + (lon_dms - utm_lon)**2
            
            # Trimble Quirks: If interpreting as DD.MMSSssss places the point much closer to the true UTM location
            if dist_dms < dist_dd and dist_dms < 0.001:
                use_dms = True
        except:
            pass

    if use_dms:
        df['lat'] = df['__lat_raw'].apply(decode_dms)
        df['lon'] = df['__lon_raw'].apply(decode_dms)
    else:
        df['lat'] = df['__lat_raw']
        df['lon'] = df['__lon_raw']

    missing = df['lat'].isnull() | df['lon'].isnull()
    if missing.any() and df['__e'].notna().any():
        for idx, row in df[missing].iterrows():
            if pd.notna(row['__e']) and pd.notna(row['__n']):
                e_val = row['__e']
                n_val = row['__n']
                
                zone = 32
                if e_val > 31000000 and e_val < 34000000:
                    zone = int(e_val / 1000000)
                    e_val = e_val % 10000000
                elif pd.notna(row['__lon_raw']) and row['__lon_raw'] > 0:
                    zone = int(row['__lon_raw'] / 6) + 31
                    
                epsg_code = f"epsg:{32600 + zone}"
                try:
                    transformer = Transformer.from_crs(epsg_code, "epsg:4326", always_xy=True)
                    lon_val, lat_val = transformer.transform(e_val, n_val)
                    df.at[idx, 'lat'] = lat_val
                    df.at[idx, 'lon'] = lon_val
                except:
                    pass
                    
    df = df.drop(columns=['__e', '__n', '__lat_raw', '__lon_raw'])
    return df

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

# --- Streamlit UI Setup ---
st.set_page_config(page_title="SiteWords", layout="wide")

# Initialize Session State
if 'app_mode' not in st.session_state:
    st.session_state['app_mode'] = 'Dashboard'
if 'report_data' not in st.session_state:
    st.session_state['report_data'] = None
if 'files_loaded' not in st.session_state:
    st.session_state['files_loaded'] = False
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'en'
if 'raw_tasklog' not in st.session_state:
    st.session_state['raw_tasklog'] = None
if 'raw_record' not in st.session_state:
    st.session_state['raw_record'] = None
if 'region_code' not in st.session_state:
    st.session_state['region_code'] = 'EU'

# --- APP MODES ---

def show_dashboard():
    lang = st.session_state['lang']
    ui = UI_TEXT[lang]
    
    # Show Upload screen if files not loaded yet
    if not st.session_state['files_loaded']:
        st.header(ui['upload_header']) 
        st.divider()
        st.info(ui['upload_info'])
        
        col1, col2 = st.columns([1, 3])
        with col1:
            region_code = st.selectbox(ui['region_mode'], ('EU', 'US'), index=0 if st.session_state['region_code'] == 'EU' else 1)
        with col2:
            uploaded_files = st.file_uploader(ui['upload_files'], type=['txt'], accept_multiple_files=True)

        tasklog_file = next((f for f in uploaded_files if 'tasklog' in f.name.lower()), None)
        record_file = next((f for f in uploaded_files if 'record' in f.name.lower()), None)

        if tasklog_file and record_file:
            def decode_file(file):
                content = file.getvalue()
                try: return content.decode("utf-8-sig")
                except UnicodeDecodeError: return content.decode("utf-16")
            
            tasklog_string_data = decode_file(tasklog_file)
            record_string_data = decode_file(record_file)
            
            st.session_state['raw_tasklog'] = tasklog_string_data
            st.session_state['raw_record'] = record_string_data
            st.session_state['region_code'] = region_code
            
            with st.spinner(ui['parsing_spinner']):
                df_sessions = parse_task_log_sessions(tasklog_string_data, region_code)
                df_points = parse_record_log(record_string_data, region_code)
                
                # --- MERGING LOGIC ---
                df = pd.DataFrame()
                if df_sessions is not None and df_points is not None:
                    # Both dataframes need to be sorted by timestamp for merge_asof
                    df_points = df_points.sort_values('timestamp')
                    df_sessions = df_sessions.sort_values('timestamp')
                    df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                elif df_points is not None:
                    df = df_points
                    st.warning(ui['tasklog_missing'])
                else:
                    st.error(ui['parse_error'])
                    return

            if not df.empty:
                # Determine UI Language based on Column Headers
                if 'Gemess. Rechtswert' in df.columns or 'Datensatztyp' in df.columns:
                    st.session_state['lang'] = 'de'
                else:
                    st.session_state['lang'] = 'en'
                    
                # Advanced Coordinate Processing
                df = process_coordinates(df)
                
                # Save processed data
                st.session_state['processed_df'] = df
                st.session_state['files_loaded'] = True
                
                st.rerun()
            return

    # Show Main Dashboard if files loaded
    if st.session_state['files_loaded']:
        lang = st.session_state['lang']
        ui = UI_TEXT[lang]
        
        head_col1, head_col2, head_col3 = st.columns([6, 2, 2])
        with head_col1:
            st.header(ui['dash_header'])
        with head_col2:
            # Region toggle in active dashboard
            new_region = st.selectbox(ui['region_mode'], ('EU', 'US'), index=0 if st.session_state['region_code'] == 'EU' else 1, label_visibility="collapsed")
            if new_region != st.session_state['region_code']:
                st.session_state['region_code'] = new_region
                with st.spinner(ui['parsing_spinner']):
                    df_sessions = parse_task_log_sessions(st.session_state['raw_tasklog'], new_region)
                    df_points = parse_record_log(st.session_state['raw_record'], new_region)
                    
                    df = pd.DataFrame()
                    if df_sessions is not None and df_points is not None:
                        df_points = df_points.sort_values('timestamp')
                        df_sessions = df_sessions.sort_values('timestamp')
                        df = pd.merge_asof(df_points, df_sessions, on='timestamp', direction='backward')
                    elif df_points is not None:
                        df = df_points
                    
                    if not df.empty:
                        # Advanced Coordinate Processing
                        df = process_coordinates(df)
                                
                        st.session_state['processed_df'] = df
                        st.session_state['dashboard_selection'] = []
                st.rerun()

        with head_col3:
            if st.button(ui['clear_files'], width='stretch'):
                st.session_state['files_loaded'] = False
                st.session_state['processed_df'] = None
                st.session_state['raw_tasklog'] = None
                st.session_state['raw_record'] = None
                if 'dashboard_selection' in st.session_state:
                    del st.session_state['dashboard_selection']
                st.rerun()
                
        st.divider()
            
        df = st.session_state['processed_df']
        
        col_table, col_map = st.columns([1, 1])

        with col_table:
            st.subheader(ui['field_data_sel'])
            st.caption(ui['sel_caption'])
            
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
                btn_text = ui['report_all']
                help_text = ui['report_all_help']
                df_to_report = df_display
            else:
                btn_text = f"{ui['report_sel_base']} ({len(selected_rows_indices)} {ui['rows']})"
                help_text = ui['report_sel_help']
                df_to_report = df_display.iloc[selected_rows_indices]

            if st.button(btn_text, type="primary", help=help_text, width='stretch'):
                st.session_state['report_data'] = df_to_report
                st.session_state['app_mode'] = 'Report'
                st.rerun()

        with col_map:
            st.subheader(ui['map_header'])
            st.caption(ui['map_caption'])
            
            map_data_cols = ['lat', 'lon']
            
            # Dynamic point name detection
            pt_col = "Point Name" if "Point Name" in df.columns else "Punktname"
            tooltip_html = "<b>Lat:</b> {lat}<br/><b>Lon:</b> {lon}"
            if pt_col in df.columns:
                map_data_cols.append(pt_col)
                tooltip_html = f"<b>{ui['map_pt_name']}:</b> {{{pt_col}}}<br/>" + tooltip_html
            
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
                st.info(ui['map_no_coord'])

def show_report_generator():
    lang = st.session_state['lang']
    ui = UI_TEXT[lang]
    
    st.header(ui['rep_header'])
    
    if st.button(ui['back_dash']):
        st.session_state['app_mode'] = 'Dashboard'
        st.rerun()
        
    df_raw = st.session_state['report_data']
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(ui['proj_details'])
        def_proj = df_raw['Project'].iloc[0] if 'Project' in df_raw.columns else ""
        def_wo = df_raw['Work Order'].iloc[0] if 'Work Order' in df_raw.columns else ""
        
        r_project = st.text_input(ui['proj_name'], value=def_proj)
        r_wo = st.text_input(ui['work_order'], value=def_wo)
        r_client = st.text_input(ui['client_name'], "Client XYZ")
        
    with c2:
        st.subheader(ui['rep_meta'])
        r_company = st.text_input(ui['company_name'], "My Surveying Co.")
        r_date = st.date_input(ui['rep_date'], datetime.now())
        r_time = st.time_input(ui['rep_time'], datetime.now())
    
    st.divider()
    
    # --- Column Selection (Multi-Language Supported) ---
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
    
    with st.expander(ui['col_sel_expander'], expanded=False):
        st.caption(ui['col_sel_caption'])
        
        cols_grid = st.columns(5)
        
        for i, col_name in enumerate(all_columns):
            is_preferred = col_name in preferred_cols
            if cols_grid[i % 5].checkbox(col_name, value=is_preferred, key=f"chk_{i}"):
                selected_columns.append(col_name)
    
    if not selected_columns:
        st.warning(ui['col_warning'])
        cols_to_include = initial_selection
    else:
        cols_to_include = [c for c in all_columns if c in selected_columns]
        
    df_report = df_raw[cols_to_include]

    st.subheader(f"{ui['rep_preview']} ({len(df_report)} {ui['rows']})")
    st.dataframe(df_report, width='stretch', hide_index=True)
    
    header_info = {
        "project": r_project, "wo": r_wo, "client": r_client,
        "company": r_company, "date": str(r_date), "time": str(r_time)
    }
    
    st.divider()
    st.subheader(ui['export_opts'])
    
    clean_project_name = re.sub(r'[^\w\-_]', '_', r_project) if r_project else "Project"
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        pdf_bytes = create_pdf(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_pdf'],
            data=pdf_bytes,
            file_name=f"Report_{clean_project_name}.pdf",
            mime="application/pdf",
            type="primary",
            width='stretch',
            key="btn_download_pdf"
        )
        
    with c2:
        excel_bytes = to_excel(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_excel'],
            data=excel_bytes,
            file_name=f"Report_{clean_project_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width='stretch',
            key="btn_download_excel"
        )
        
    with c3:
        csv_bytes = to_csv(df_report)
        st.download_button(
            label=ui['dl_csv'],
            data=csv_bytes,
            file_name=f"Report_{clean_project_name}.csv",
            mime="text/csv",
            width='stretch',
            key="btn_download_csv"
        )
        
    with c4:
        html_bytes = to_html(df_report, header_info, lang)
        st.download_button(
            label=ui['dl_html'],
            data=html_bytes,
            file_name=f"Report_{clean_project_name}.html",
            mime="text/html",
            width='stretch',
            key="btn_download_html"
        )

# --- APP MODES ---
if st.session_state['app_mode'] == 'Dashboard':
    show_dashboard()
elif st.session_state['app_mode'] == 'Report':
    show_report_generator()
