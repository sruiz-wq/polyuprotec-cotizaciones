import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import date, datetime
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS Y NUBE (SUPABASE)
# ==========================================
# Conexión al Storage (Para los PDFs)
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase_client: Client = create_client(supabase_url, supabase_key)

def get_connection():
    # Conexión a PostgreSQL (Para los datos de las tablas)
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            proveedor TEXT,
            contacto TEXT,
            equipo TEXT,
            especificacion TEXT,
            tipo_tarifa TEXT,
            origen TEXT,
            destino TEXT,
            costo_alquiler REAL,
            costo_flete REAL,
            archivo_pdf TEXT,
            observaciones TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS servicios (
            id SERIAL PRIMARY KEY,
            fecha DATE,
            proveedor TEXT,
            contacto TEXT,
            tipo_servicio TEXT,
            alcance TEXT,
            ubicacion TEXT,
            costo_total REAL,
            archivo_pdf TEXT,
            observaciones TEXT
        )
    ''')
    conn.commit()
    c.close()
    conn.close()

# --- FUNCIONES EQUIPOS ---
def insertar_cotizacion(fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, pdf_nombre, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO cotizaciones (fecha, proveedor, contacto, equipo, especificacion, tipo_tarifa, origen, destino, costo_alquiler, costo_flete, archivo_pdf, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, pdf_nombre, obs))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def actualizar_cotizacion(id_cot, fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE cotizaciones 
        SET fecha=%s, proveedor=%s, contacto=%s, equipo=%s, especificacion=%s, tipo_tarifa=%s, origen=%s, destino=%s, costo_alquiler=%s, costo_flete=%s, observaciones=%s
        WHERE id=%s
    ''', (fecha, prov, contacto, equipo, esp, tarifa, origen, destino, alquiler, flete, obs, id_cot))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def eliminar_cotizacion(id_cot):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM cotizaciones WHERE id=%s', (id_cot,))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=300)
def cargar_datos():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM cotizaciones', conn)
    conn.close()
    return df

# --- FUNCIONES SERVICIOS ---
def insertar_servicio(fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, pdf_nombre, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO servicios (fecha, proveedor, contacto, tipo_servicio, alcance, ubicacion, costo_total, archivo_pdf, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, pdf_nombre, obs))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def actualizar_servicio(id_serv, fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, obs):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE servicios 
        SET fecha=%s, proveedor=%s, contacto=%s, tipo_servicio=%s, alcance=%s, ubicacion=%s, costo_total=%s, observaciones=%s
        WHERE id=%s
    ''', (fecha, prov, contacto, tipo_serv, alcance, ubicacion, costo, obs, id_serv))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

def eliminar_servicio(id_serv):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM servicios WHERE id=%s', (id_serv,))
    conn.commit()
    c.close()
    conn.close()
    st.cache_data.clear()

@st.cache_data(ttl=300)
def cargar_servicios():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM servicios', conn)
    conn.close()
    return df

def formato_pesos(valor):
    return f"$ {valor:,.0f}".replace(",", ".")

init_db()

# --- ÍCONOS DINÁMICOS ---
iconos_equipos = {
    "Todos": "🌍", "Camión Grúa": "🚛", "Grúa Telescópica": "🏗️", 
    "Montacarga": "🚜", "Telehandler": "🚜", "Manlift": "🦒", "Brazos Articulados": "🦾", 
    "Tijeras": "✂️", "Andamios": "🪜", "Contenedor": "📦", 
    "Baños Portátiles": "🚻", "Otro": "🛠️"
}

# ==========================================
# 2. INTERFAZ DE USUARIO (UI)
# ==========================================
st.set_page_config(page_title="Directorio Polyuprotec", page_icon="logo.png", layout="wide", initial_sidebar_state="expanded")

# Mostrar logo en la barra lateral
try:
    st.sidebar.image("logo.png", use_container_width=True)
except Exception:
    pass

st.sidebar.markdown("---")
st.sidebar.header("📌 Menú Principal")
menu_principal = st.sidebar.radio("Selecciona el Módulo:", ["🚜 Equipos y Fletes", "🛠️ Módulo de Servicios"])

# ==========================================
# MÓDULO 1: EQUIPOS Y FLETES
# ==========================================
if menu_principal == "🚜 Equipos y Fletes":
    st.title("🚜 Panel de Cotizaciones: Equipos y Fletes")
    df = cargar_datos()

    opciones_equipos = ["Camión Grúa", "Grúa Telescópica", "Montacarga", "Telehandler", "Manlift", "Brazos Articulados", "Tijeras", "Andamios", "Contenedor", "Baños Portátiles", "Otro"]
    opciones_tarifas = ["Por Día", "Por Mes", "Global (Todo el proyecto)"]

    with st.expander("➕ Registrar Nueva Cotización de Equipo", expanded=False):
        with st.form("form_registro_equipo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: fecha_cot = st.date_input("Fecha", date.today())
            with col2: prov = st.text_input("Proveedor *")
            with col3: contacto = st.text_input("Contacto")
            
            col_eq1, col_eq2, col_eq3 = st.columns(3)
            with col_eq1: equipo = st.selectbox("Equipo", opciones_equipos)
            with col_eq2:
                esp_val = st.number_input("Capacidad / Altura (Ton o Mts)", min_value=0.0, step=1.0)
                esp_final = f"{esp_val} Unidades"
            with col_eq3: tarifa = st.selectbox("Tarifa", opciones_tarifas)

            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            with col_l1: orig = st.text_input("Origen *")
            with col_l2: dest = st.text_input("Destino *")
            with col_l3: alquiler = st.number_input("Alquiler", min_value=0, step=50000)
            with col_l4: flete = st.number_input("Flete", min_value=0, step=50000)
                
            archivo_pdf = st.file_uploader("PDF", type=["pdf"])
            obs = st.text_area("Observaciones")
            
            if st.form_submit_button("💾 Guardar Cotización", use_container_width=True):
                if prov and orig and dest:
                    nombre_pdf = ""
                    if archivo_pdf:
                        try:
                            import unicodedata
                            pdf_bytes = archivo_pdf.getvalue()
                            timestamp_unico = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            
                            def limpiar_texto(texto):
                                nfkd = unicodedata.normalize('NFKD', texto)
                                sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
                                return "".join(c for c in sin_tildes if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")

                            prov_clean = limpiar_texto(prov)
                            equipo_clean = limpiar_texto(equipo)
                            nombre_pdf = f"{timestamp_unico}_{prov_clean}_{equipo_clean}.pdf"
                            
                            supabase_client.storage.from_("documentos").upload(
                                path=nombre_pdf,
                                file=pdf_bytes,
                                file_options={"content-type": "application/pdf", "upsert": "true"}
                            )
                        except Exception as e:
                            st.error(f"⚠️ Error al subir el PDF a Supabase Storage: {e}")
                            nombre_pdf = ""
                            
                    insertar_cotizacion(fecha_cot, prov, contacto, equipo, esp_final, tarifa, orig, dest, alquiler, flete, nombre_pdf, obs)
                    st.success("¡Agregado exitosamente a la nube!")
                    st.rerun()
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    if not df.empty:
        with st.expander("✏️ Editar o 🗑️ Eliminar un Registro de Equipo", expanded=False):
            opciones_registro = df['id'].astype(str) + " - " + df['proveedor'] + " (" + df['equipo'] + ")"
            seleccion = st.selectbox("Selecciona la cotización a modificar:", opciones_registro)
            if seleccion:
                id_sel = int(seleccion.split(" - ")[0])
                reg = df[df['id'] == id_sel].iloc[0]
                try: f_act = datetime.strptime(str(reg['fecha']), "%Y-%m-%d").date()
                except: f_act = date.today()

                tab1, tab2 = st.tabs(["✏️ Editar Cotización", "🗑️ Eliminar Cotización"])
                with tab1:
                    with st.form("form_edit_eq"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            nf = st.date_input("Fecha", f_act)
                            np = st.text_input("Proveedor", reg['proveedor'])
                            nc = st.text_input("Contacto", reg['contacto'] if pd.notna(reg['contacto']) else "")
                        with c2:
                            idx_eq = opciones_equipos.index(reg['equipo']) if reg['equipo'] in opciones_equipos else 0
                            neq = st.selectbox("Equipo", opciones_equipos, index=idx_eq)
                            nesp = st.text_input("Especificación", reg['especificacion'])
                            nori = st.text_input("Origen", reg['origen'])
                        with c3:
                            idx_tar = opciones_tarifas.index(reg['tipo_tarifa']) if reg['tipo_tarifa'] in opciones_tarifas else 0
                            ntar = st.selectbox("Tarifa", opciones_tarifas, index=idx_tar)
                            ndes = st.text_input("Destino", reg['destino'])
                            nalq = st.number_input("Alquiler", min_value=0, value=int(reg['costo_alquiler']), step=50000)
                            nfle = st.number_input("Flete", min_value=0, value=int(reg['costo_flete']), step=50000)
                        nobs = st.text_area("Observaciones", reg['observaciones'] if pd.notna(reg['observaciones']) else "")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            actualizar_cotizacion(id_sel, nf, np, nc, neq, nesp, ntar, nori, ndes, nalq, nfle, nobs)
                            st.success("¡Registro actualizado con éxito!")
                            st.rerun()
                with tab2:
                    st.warning(f"⚠️ Vas a eliminar el registro de **{reg['proveedor']}**.")
                    if st.button("Sí, Eliminar Definitivamente", type="primary"):
                        eliminar_cotizacion(id_sel)
                        st.success("Registro eliminado.")
                        st.rerun()

    st.markdown("---")
    if not df.empty:
        df['costo_total'] = df['costo_alquiler'] + df['costo_flete']
        with st.container(border=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1: eq_s = st.selectbox("🔍 Selecciona el Equipo:", ['Todos'] + list(df['equipo'].unique()))
            with col_f2: orig_s = st.selectbox("🔍 Selecciona el Origen:", ['Todas'] + list(df['origen'].unique()))
        
        df_f = df.copy()
        if eq_s != 'Todos': df_f = df_f[df_f['equipo'] == eq_s]
        if orig_s != 'Todas': df_f = df_f[df_f['origen'] == orig_s]
        
        if not df_f.empty:
            df_f = df_f.sort_values('costo_alquiler', ascending=True)
            mejor_opcion = df_f.iloc[0]
            icono = iconos_equipos.get(eq_s, "⚙️")
            st.markdown(f"## {icono} Análisis para: {eq_s}")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Cotizaciones", len(df_f))
            c2.metric("Opciones", df_f['equipo'].nunique())
            c3.metric("🏆 Mejor Proveedor", mejor_opcion['proveedor'])
            c4.metric("⚙️ Especificación", mejor_opcion['especificacion'])
            c5.metric("💰 Alquiler Mínimo", formato_pesos(mejor_opcion['costo_alquiler']))

            st.markdown("### 📋 Base de Datos Detallada")
            df_disp = df_f.copy()
            df_disp['archivo_pdf'] = df_disp['archivo_pdf'].apply(lambda x: "📄 Adjunto" if pd.notna(x) and str(x).strip() != "" and str(x).strip() != "None" else "Sin PDF")
            for col in ['costo_alquiler', 'costo_flete', 'costo_total']: df_disp[col] = df_disp[col].apply(formato_pesos)
            
            st.dataframe(
                df_disp[['id', 'fecha', 'proveedor', 'equipo', 'especificacion', 'tipo_tarifa', 'origen', 'destino', 'costo_alquiler', 'costo_flete', 'costo_total', 'archivo_pdf', 'observaciones']], 
                use_container_width=True, hide_index=True
            )
            
# --- VISOR PROFESIONAL SEGURO ---
            with st.expander("📂 Visualizar PDF en la Página"):
                df_con_pdf = df_f[df_f['archivo_pdf'].notna() & (df_f['archivo_pdf'] != "") & (df_f['archivo_pdf'].astype(str) != "None")]
                if not df_con_pdf.empty:
                    opciones_pdf = df_con_pdf['id'].astype(str) + " - " + df_con_pdf['proveedor'] + " (" + df_con_pdf['equipo'] + ")"
                    sel_pdf = st.selectbox("Selecciona la cotización para ver el documento:", opciones_pdf)
                    if sel_pdf:
                        id_p = int(sel_pdf.split(" - ")[0])
                        nombre_real_pdf = df_con_pdf[df_con_pdf['id'] == id_p]['archivo_pdf'].values[0]
                        
                        try:
                            # Obtener URL pública directa desde Supabase Storage
                            res_url = supabase_client.storage.from_("documentos").get_public_url(nombre_real_pdf)
                            url_publica = res_url.get('publicUrl', res_url) if isinstance(res_url, dict) else res_url
                            
                            # Descargar bytes para el botón de descarga nativo
                            pdf_bytes = supabase_client.storage.from_("documentos").download(nombre_real_pdf)
                            
                            st.markdown("---")
                            st.subheader("📄 Gestión del Documento Adjunto")
                            st.info(f"📁 Archivo vinculado: **{nombre_real_pdf}**")
                            
                            # Botones de acción limpia en Streamlit
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                st.link_button("🔍 Ver documento en pantalla completa", url_publica, use_container_width=True)
                            with col_b2:
                                st.download_button(
                                    label="📥 Descargar Archivo PDF",
                                    data=pdf_bytes,
                                    file_name=nombre_real_pdf,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            st.markdown("---")
                        except Exception as e:
                            st.error(f"⚠️ Error al procesar el archivo adjunto: {e}")
                else:
                    st.info("No hay PDFs adjuntos para este filtro.")
                    
# ==========================================
# MÓDULO 2: SERVICIOS
# ==========================================
elif menu_principal == "🛠️ Módulo de Servicios":
    st.title("🛠 Panel de Cotizaciones: Servicios Generales")
    df_serv = cargar_servicios()
    tipos_servicios = ["Montaje Estructural", "Suministro de Materiales", "Pintura y Recubrimientos", "Servicio de Rolado", "Mantenimiento", "Otro"]

    with st.expander("➕ Registrar Nueva Cotización de Servicio", expanded=False):
        with st.form("form_registro_servicio", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: f_serv = st.date_input("Fecha", date.today())
            with col2: prov_serv = st.text_input("Proveedor *")
            with col3: cont_serv = st.text_input("Contacto")

            c_s1, c_s2, c_s3 = st.columns(3)
            with c_s1: tipo_s = st.selectbox("Tipo de Servicio", tipos_servicios)
            with c_s2: ubica = st.text_input("Ubicación / Proyecto *")
            with c_s3: costo_tot = st.number_input("Costo Total (COP)", min_value=0, step=100000)
            
            alcance = st.text_area("Alcance Técnico")
            pdf_serv = st.file_uploader("PDF", type=["pdf"])
            obs_serv = st.text_area("Observaciones")

            if st.form_submit_button("💾 Guardar Servicio", use_container_width=True):
                if prov_serv and ubica:
                    nombre_pdf_s = ""
                    if pdf_serv:
                        try:
                            import unicodedata
                            pdf_bytes_s = pdf_serv.getvalue()
                            timestamp_unico_s = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            
                            def limpiar_texto(texto):
                                nfkd = unicodedata.normalize('NFKD', texto)
                                sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
                                return "".join(c for c in sin_tildes if c.isalnum() or c in (' ', '_')).strip().replace(" ", "_")

                            prov_s_clean = limpiar_texto(prov_serv)
                            tipo_s_clean = limpiar_texto(tipo_s)
                            nombre_pdf_s = f"{timestamp_unico_s}_{prov_s_clean}_{tipo_s_clean}.pdf"
                            
                            supabase_client.storage.from_("documentos").upload(
                                path=nombre_pdf_s,
                                file=pdf_bytes_s,
                                file_options={"content-type": "application/pdf", "upsert": "true"}
                            )
                        except Exception as e:
                            st.error(f"⚠️ Error al subir el PDF de servicio: {e}")
                            nombre_pdf_s = ""
                            
                    insertar_servicio(f_serv, prov_serv, cont_serv, tipo_s, alcance, ubica, costo_tot, nombre_pdf_s, obs_serv)
                    st.success("¡Servicio registrado con éxito en la nube!")
                    st.rerun()
                else:
                    st.error("Completa los campos obligatorios (*).")

    if not df_serv.empty:
        with st.expander("✏️ Editar o 🗑️ Eliminar un Registro de Servicio", expanded=False):
            opciones_del_s = df_serv['id'].astype(str) + " - " + df_serv['proveedor'] + " (" + df_serv['tipo_servicio'] + ")"
            sel_eliminar = st.selectbox("Selecciona el servicio a modificar:", opciones_del_s)
            
            if sel_eliminar:
                id_s_sel = int(sel_eliminar.split(" - ")[0])
                reg_s = df_serv[df_serv['id'] == id_s_sel].iloc[0]
                try: f_act_s = datetime.strptime(str(reg_s['fecha']), "%Y-%m-%d").date()
                except: f_act_s = date.today()

                tab_s1, tab_s2 = st.tabs(["✏️ Editar", "🗑️ Eliminar"])
                with tab_s1:
                    with st.form("form_edit_serv"):
                        col_s1, col_s2, col_s3 = st.columns(3)
                        with col_s1:
                            nf_s = st.date_input("Fecha", f_act_s)
                            np_s = st.text_input("Proveedor", reg_s['proveedor'])
                            nc_s = st.text_input("Contacto", reg_s['contacto'] if pd.notna(reg_s['contacto']) else "")
                        with col_s2:
                            idx_ts = tipos_servicios.index(reg_s['tipo_servicio']) if reg_s['tipo_servicio'] in tipos_servicios else 0
                            nt_s = st.selectbox("Tipo de Servicio", tipos_servicios, index=idx_ts)
                            nub_s = st.text_input("Ubicación", reg_s['ubicacion'])
                            ncos_s = st.number_input("Costo Total", min_value=0, value=int(reg_s['costo_total']), step=100000)
                        with col_s3:
                            nalc_s = st.text_area("Alcance Técnico", reg_s['alcance'] if pd.notna(reg_s['alcance']) else "")
                            nobs_s = st.text_area("Observaciones", reg_s['observaciones'] if pd.notna(reg_s['observaciones']) else "")
                        
                        if st.form_submit_button("Actualizar Registro"):
                            actualizar_servicio(id_s_sel, nf_s, np_s, nc_s, nt_s, nalc_s, nub_s, ncos_s, nobs_s)
                            st.success("¡Servicio actualizado!")
                            st.rerun()
                with tab_s2:
                    st.warning(f"⚠️ Vas a eliminar a **{reg_s['proveedor']}**.")
                    if st.button("Sí, Eliminar Definitivamente", type="primary"):
                        eliminar_servicio(id_s_sel)
                        st.success("Registro eliminado.")
                        st.rerun()

    st.markdown("---")
    if not df_serv.empty:
        with st.container(border=True):
            tipo_sel = st.selectbox("🔍 Filtra por Tipo de Servicio:", ['Todos'] + list(df_serv['tipo_servicio'].unique()))
        
        df_serv_f = df_serv.copy()
        if tipo_sel != 'Todos': df_serv_f = df_serv_f[df_serv_f['tipo_servicio'] == tipo_sel]
        
        if not df_serv_f.empty:
            df_serv_f = df_serv_f.sort_values('costo_total', ascending=True)
            mejor_serv = df_serv_f.iloc[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cotizaciones", len(df_serv_f))
            c2.metric("Opciones", df_serv_f['tipo_servicio'].nunique())
            c3.metric("🏆 Mejor Proveedor", mejor_serv['proveedor'])
            c4.metric("💰 Costo Mínimo", formato_pesos(mejor_serv['costo_total']))

            st.markdown("### 📋 Base de Datos Detallada")
            df_s_disp = df_serv_f.copy()
            df_s_disp['archivo_pdf'] = df_s_disp['archivo_pdf'].apply(lambda x: "📄 Adjunto" if pd.notna(x) and str(x).strip() != "" and str(x).strip() != "None" else "Sin PDF")
            df_s_disp['costo_total'] = df_s_disp['costo_total'].apply(formato_pesos)
            
            st.dataframe(df_s_disp[['id', 'fecha', 'proveedor', 'tipo_servicio', 'alcance', 'ubicacion', 'costo_total', 'archivo_pdf', 'observaciones']], use_container_width=True, hide_index=True)
            
            # --- VISOR PARA SERVICIOS DESDE SUPABASE ---
            with st.expander("📂 Visualizar PDF en la Página"):
                df_serv_con_pdf = df_serv_f[df_serv_f['archivo_pdf'].notna() & (df_serv_f['archivo_pdf'] != "") & (df_serv_f['archivo_pdf'].astype(str) != "None")]
                if not df_serv_con_pdf.empty:
                    opciones_pdf_s = df_serv_con_pdf['id'].astype(str) + " - " + df_serv_con_pdf['proveedor'] + " (" + df_serv_con_pdf['tipo_servicio'] + ")"
                    sel_pdf_s = st.selectbox("Selecciona el servicio para ver el documento:", opciones_pdf_s)
                    if sel_pdf_s:
                        id_ps = int(sel_pdf_s.split(" - ")[0])
                        nombre_real_pdf_s = df_serv_f[df_serv_f['id'] == id_ps]['archivo_pdf'].values[0]
                        url_publica_s = supabase_client.storage.from_("documentos").get_public_url(nombre_real_pdf_s)
                        
                        st.markdown("---")
                        st.markdown(f'<iframe src="{url_publica_s}" width="100%" height="600px" type="application/pdf"></iframe>', unsafe_allow_html=True)
                        st.markdown("---")
                        st.link_button("📥 Descargar o abrir en pestaña completa", url_publica_s)
                else:
                    st.info("No hay PDFs adjuntos para este filtro.")
