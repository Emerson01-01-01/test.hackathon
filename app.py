
import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import date

# -----------------------------------------
# CONFIGURACION GENERAL
# -----------------------------------------
st.set_page_config(
    page_title="Asistente de Víveres",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Asistente Inteligente de Víveres")
st.caption(
    "Prototipo para organizar anotaciones de una tienda "
    "y convertirlas en un archivo Excel."
)

# -----------------------------------------
# ALMACENAMIENTO TEMPORAL
# -----------------------------------------
if "registros" not in st.session_state:
    st.session_state.registros = []

if "chat" not in st.session_state:
    st.session_state.chat = [
        {
            "role": "assistant",
            "content": (
                "¡Hola! Soy tu asistente de tienda. 📒\n\n"
                "Puedes subir una foto de tu cuaderno, "
                "registrar las ventas, compras o gastos "
                "y descargar tus datos en Excel.\n\n"
                "Importante: por ahora necesito que "
                "transcribas los apuntes de la fotografía."
            )
        }
    ]

# -----------------------------------------
# BARRA LATERAL
# -----------------------------------------
st.sidebar.header("📋 Menú")

seccion = st.sidebar.radio(
    "¿Qué deseas hacer?",
    [
        "Inicio y chatbot",
        "Registrar movimientos",
        "Consultar registros",
        "Descargar Excel"
    ]
)

st.sidebar.info(
    "Versión de demostración. Los datos se guardan "
    "temporalmente mientras la sesión está activa."
)

# -----------------------------------------
# INICIO Y CHATBOT
# -----------------------------------------
if seccion == "Inicio y chatbot":

    st.subheader("💬 Conversa con tu asistente")

    for mensaje in st.session_state.chat:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    pregunta = st.chat_input(
        "Ejemplo: ¿Cómo registro las ventas de hoy?"
    )

    if pregunta:
        st.session_state.chat.append(
            {"role": "user", "content": pregunta}
        )

        texto = pregunta.lower()

        if any(p in texto for p in [
            "excel", "descargar", "archivo"
        ]):
            respuesta = (
                "Para obtener tu Excel, entra en "
                "**Descargar Excel** en el menú lateral. "
                "Podrás revisar tus movimientos y descargar "
                "el archivo."
            )

        elif any(p in texto for p in [
            "foto", "fotografía", "imagen", "cuaderno"
        ]):
            respuesta = (
                "¡Perfecto! Entra en **Registrar movimientos** "
                "y sube la foto de tu cuaderno. En esta versión "
                "puedes visualizarla, pero debes transcribir "
                "los datos manualmente."
            )

        elif any(p in texto for p in [
            "venta", "compra", "gasto", "inventario",
            "registrar", "producto"
        ]):
            respuesta = (
                "Entra en **Registrar movimientos**. "
                "Selecciona el tipo de movimiento, la fecha, "
                "el producto, la cantidad y el precio unitario. "
                "Revisa los datos antes de guardarlos."
            )

        elif any(p in texto for p in [
            "total", "ganancia", "resumen"
        ]):
            if st.session_state.registros:
                df_chat = pd.DataFrame(
                    st.session_state.registros
                )
                respuesta = (
                    f"Tienes {len(df_chat)} movimientos "
                    "registrados. Puedes revisar los importes "
                    "en **Consultar registros** y descargar "
                    "el resumen en Excel."
                )
            else:
                respuesta = (
                    "Todavía no tienes movimientos registrados. "
                    "Agrega algunos para consultar tu información."
                )

        else:
            respuesta = (
                "Puedo ayudarte a registrar ventas, compras "
                "y gastos, revisar tus anotaciones y preparar "
                "un Excel. Prueba preguntándome cómo registrar "
                "una venta o cómo descargar el archivo."
            )

        st.session_state.chat.append(
            {"role": "assistant", "content": respuesta}
        )

        st.rerun()

    st.divider()
    st.subheader("📸 Fotografía del cuaderno")

    foto = st.file_uploader(
        "Sube una foto de tus anotaciones",
        type=["jpg", "jpeg", "png"],
        key="foto_inicio"
    )

    if foto is not None:
        try:
            imagen = Image.open(foto)
            st.image(
                imagen,
                caption="Fotografía cargada para revisar",
                width=500
            )
            st.success(
                "Foto cargada. Transcribe los apuntes "
                "en la sección Registrar movimientos."
            )
        except Exception:
            st.error("No se pudo abrir la imagen.")

# -----------------------------------------
# REGISTRAR MOVIMIENTOS
# -----------------------------------------
elif seccion == "Registrar movimientos":

    st.subheader("📒 Registrar datos del cuaderno")

    st.write(
        "Sube la fotografía y transcribe cada apunte. "
        "Podrás revisar la información antes de descargarla."
    )

    foto = st.file_uploader(
        "Fotografía del cuaderno (opcional)",
        type=["jpg", "jpeg", "png"],
        key="foto_registro"
    )

    if foto is not None:
        try:
            imagen = Image.open(foto)
            st.image(
                imagen,
                caption="Apunte original para comparar",
                width=500
            )
        except Exception:
            st.error("No se pudo abrir la imagen.")

    with st.form("formulario_registro"):

        fecha_mov = st.date_input(
            "Fecha del movimiento",
            value=date.today()
        )

        tipo = st.selectbox(
            "Tipo de movimiento",
            ["Venta", "Compra", "Gasto"]
        )

        producto = st.text_input(
            "Producto o concepto",
            placeholder="Ej.: Arroz, azúcar o pago de luz"
        )

        cantidad = st.number_input(
            "Cantidad",
            min_value=0.01,
            value=1.0,
            step=1.0
        )

        precio = st.number_input(
            "Precio unitario o importe por unidad ($)",
            min_value=0.0,
            value=0.0,
            step=0.10,
            format="%.2f"
        )

        notas = st.text_input(
            "Observaciones (opcional)",
            placeholder="Ej.: anotación del cuaderno"
        )

        guardar = st.form_submit_button(
            "➕ Guardar movimiento",
            use_container_width=True
        )

        if guardar:
            if not producto.strip():
                st.error("Escribe el nombre del producto o concepto.")

            elif precio <= 0:
                st.error("El precio debe ser mayor que cero.")

            else:
                importe = round(cantidad * precio, 2)

                nuevo = {
                    "Fecha": fecha_mov.isoformat(),
                    "Tipo": tipo,
                    "Producto": producto.strip(),
                    "Cantidad": cantidad,
                    "Precio unitario ($)": precio,
                    "Total ($)": importe,
                    "Observaciones": notas.strip()
                }

                st.session_state.registros.append(nuevo)

                st.session_state.chat.append({
                    "role": "assistant",
                    "content": (
                        f"✅ Movimiento guardado: {producto}, "
                        f"tipo {tipo}, total ${importe:.2f}. "
                        "Puedes seguir registrando datos."
                    )
                })

                st.success("¡Movimiento guardado correctamente!")

# -----------------------------------------
# CONSULTAR REGISTROS
# -----------------------------------------
elif seccion == "Consultar registros":

    st.subheader("📊 Registros de la tienda")

    if st.session_state.registros:

        df = pd.DataFrame(st.session_state.registros)

        st.metric(
            "Movimientos registrados",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Si necesitas corregir un dato, elimina el registro "
            "incorrecto desde la opción siguiente y vuelve a "
            "registrarlo."
        )

        opciones = list(range(len(df)))

        seleccionado = st.selectbox(
            "Selecciona el número de registro que deseas eliminar",
            opciones,
            format_func=lambda i: (
                f"{i + 1}. {df.iloc[i]['Producto']} - "
                f"{df.iloc[i]['Tipo']}"
            )
        )

        if st.button("🗑️ Eliminar registro seleccionado"):
            st.session_state.registros.pop(seleccionado)
            st.rerun()

    else:
        st.info("Todavía no hay registros. Agrega el primero.")

# -----------------------------------------
# DESCARGAR EXCEL
# -----------------------------------------
elif seccion == "Descargar Excel":

    st.subheader("📥 Descargar reporte de la tienda")

    if st.session_state.registros:

        df = pd.DataFrame(st.session_state.registros)

        # Resumen por tipo de movimiento
        resumen = (
            df.groupby("Tipo", as_index=False)["Total ($)"]
            .sum()
        )

        # Crear Excel en memoria sin guardar datos en el disco
        salida = BytesIO()

        with pd.ExcelWriter(
            salida,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Movimientos",
                index=False
            )

            resumen.to_excel(
                writer,
                sheet_name="Resumen",
                index=False
            )

        st.write(
            "El archivo incluirá dos hojas: "
            "**Movimientos** y **Resumen**."
        )

        st.dataframe(
            resumen,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="⬇️ Descargar Excel (.xlsx)",
            data=salida.getvalue(),
            file_name=f"reporte_viveres_{date.today().isoformat()}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )

    else:
        st.warning(
            "No hay datos para exportar. Registra al menos "
            "un movimiento primero."
        )

st.divider()
st.caption(
    "Prototipo académico de gestión de víveres. "
    "Los datos son de prueba y no constituyen una "
    "contabilidad oficial."
)
