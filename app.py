import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine, text
from supabase import create_client, Client

# Configuración de página
st.set_page_config(page_title="Cotizador Polyuprotec", page_icon="🏗️", layout="wide")

# Conexión a Base de Datos y Supabase desde Secrets
@st.cache_resource
def init_connections():
    db_url = st.secrets["DATABASE_URL"]
    engine = create_engine(db_url)
    
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
    
    return engine, supabase

engine, supabase_client = init_connections()

# Funciones de base de datos para Equipos
def cargar_datos_equipos():
    try:
        query = "SELECT * FROM cotizaciones_equipos ORDER BY fecha DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cotizaciones_equipos (
                    id SERIAL PRIMARY KEY,
                    fecha DATE,
                    proveedor TEXT,
                    contacto TEXT,
                    equipo TEXT,
                    capacidad TEXT,
                    tarifa TEXT,
                    origen TEXT,
                    destino TEXT,
                    alquiler NUMERIC,
                    flete NUMERIC,
                    pdf TEXT,
                    observaciones TEXT
                );
            """))
        return pd.DataFrame()

def insertar_cotizacion(fecha, proveedor, contacto, equipo, capacidad, tarifa, origen, destino, alquiler, flete, pdf, observaciones):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO cotizaciones_equipos (fecha, proveedor, contacto, equipo, capacidad, tarifa, origen, destino, alquiler, flete, pdf, observaciones)
            VALUES (:fecha, :proveedor, :contacto, :equipo, :capacidad, :tarifa, :origen, :destino, :alquiler, :flete, :pdf, :observaciones)
        """), {
            "fecha": fecha,
            "proveedor": proveedor,
            "contacto": contacto,
            "equipo": equipo,
            "capacidad": capacidad,
            "tarifa": tarifa,
            "origen": origen,
            "destino": destino,
            "alquiler": alquiler,
            "flete": flete,
            "pdf": pdf,
            "observaciones": observaciones
        })

# Funciones para Servicios
def cargar_datos_servicios():
    try:
        query = "SELECT * FROM cotizaciones_servicios ORDER BY fecha DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cotizaciones_servicios (
                    id SERIAL PRIMARY KEY,
                    fecha DATE,
                    proveedor TEXT,
                    contacto TEXT,
                    tipo_servicio TEXT,
                    alcance TEXT,
                    ubicacion TEXT,
                    costo_total NUMERIC,
                    pdf TEXT,
                    observaciones TEXT
                );
            """))
        return pd.DataFrame()

def insertar_servicio(fecha, proveedor, contacto, tipo_servicio, alcance, ubicacion, costo_total, pdf, observaciones):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO cotizaciones_servicios (fecha, proveedor, contacto, tipo_servicio, alcance, ubicacion, costo_total, pdf, observaciones)
            VALUES (:fecha, :proveedor, :contacto, :tipo_servicio, :alcance, :ubicacion, :costo_total, :pdf, :observaciones)
        """), {
            "fecha": fecha,
            "proveedor": proveedor,
            "contacto": contacto,
            "tipo_servicio": tipo_servicio,
            "alcance": alcance,
            "ubicacion": ubicacion,
            "costo_total": costo_total,
            "pdf": pdf,
            "observaciones": observaciones
        })

# Título principal
st.title("🏗️ Sistema de Cotizaciones - Polyuprotec S.A.")

# Pestañas principales
tab1, tab2 = st.tabs(["🚜 Equipos y Fletes", "🛠️ Módulo de Servicios"])

with tab1:
    st.header("Gestión de Cotizaciones de Equipos")
    
    with st.expander("➕ Registrar Nueva Cotización de Equipo", expanded=False):
        with st.form("form_registro_equipo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: fecha_cot = st.date_input("Fecha", date.today())
            with col2: prov = st.text_input("Proveedor *")
            with col3: contacto = st.text_input("Contacto")
            
            opciones_equipos = ["Camión Grúa", "Excavadora", "Retroexcavadora", "Mini cargador", "Bulldozer", "Vibrocompactador", "Carrotanque", "Otro"]
            opciones_tarifas = ["Por Día", "Por Hora", "Mes", "Viaje", "Global"]
            
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
            
            submitted = st.form_submit_button("💾 Guardar Cotización", use_container_width=True)
            if submitted:
                if prov and orig and dest:
                    nombre_pdf = ""
                    if archivo_pdf:
                        timestamp_unico = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        nombre_pdf = f"{timestamp_unico}_{prov}_{equipo}.pdf".replace(" ", "_")
                        try:
                            supabase_client.storage.from_("documentos").upload(
                                path=nombre_pdf,
                                file=archivo_pdf.getvalue(),
                                file_options={"content-type": "application/pdf"}
                            )
                        except Exception as e:
                            st.error(f"⚠️ Error al subir el PDF a Supabase: {e}")
                            nombre_pdf = ""
                            
                    insertar_cotizacion(fecha_cot, prov, contacto, equipo, esp_final, tarifa, orig, dest, alquiler, flete, nombre_pdf, obs)
                    st.success("¡Agregado exitosamente!")
                    st.rerun()
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    # Mostrar registros existentes
    df_eq = cargar_datos_equipos()
    if not df_eq.empty:
        st.subheader("📋 Cotizaciones de Equipos Registradas")
        st.dataframe(df_eq, use_container_width=True)

with tab2:
    st.header("Gestión de Cotizaciones de Servicios")
    
    with st.expander("➕ Registrar Nuevo Servicio", expanded=False):
        with st.form("form_registro_servicio", clear_on_submit=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1: f_serv = st.date_input("Fecha", date.today(), key="f_s")
            with col_s2: prov_serv = st.text_input("Proveedor / Contratista *", key="p_s")
            with col_s3: cont_serv = st.text_input("Contacto", key="c_s")
            
            tipo_s = st.text_input("Tipo de Servicio")
            alcance = st.text_area("Alcance Técnico")
            ubica = st.text_input("Ubicación *")
            costo_tot = st.number_input("Costo Total", min_value=0, step=50000, key="ct_s")
            
            pdf_serv = st.file_uploader("PDF", type=["pdf"], key="pdf_s")
            obs_serv = st.text_area("Observaciones", key="obs_s")

            submitted_serv = st.form_submit_button("💾 Guardar Servicio", use_container_width=True)
            if submitted_serv:
                if prov_serv and ubica:
                    nombre_pdf_s = ""
                    if pdf_serv:
                        timestamp_unico_s = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        nombre_pdf_s = f"{timestamp_unico_s}_{prov_serv}_{tipo_s}.pdf".replace(" ", "_")
                        try:
                            supabase_client.storage.from_("documentos").upload(
                                path=nombre_pdf_s,
                                file=pdf_serv.getvalue(),
                                file_options={"content-type": "application/pdf"}
                            )
                        except Exception as e:
                            st.error(f"⚠️ Error al subir el PDF de servicio: {e}")
                            nombre_pdf_s = ""
                            
                    insertar_servicio(f_serv, prov_serv, cont_serv, tipo_s, alcance, ubica, costo_tot, nombre_pdf_s, obs_serv)
                    st.success("¡Servicio registrado con éxito!")
                    st.rerun()
                else:
                    st.error("Completa los campos obligatorios (*).")

    # Mostrar servicios existentes
    df_serv = cargar_datos_servicios()
    if not df_serv.empty:
        st.subheader("📋 Servicios Registrados")
        st.dataframe(df_serv, use_container_width=True)
