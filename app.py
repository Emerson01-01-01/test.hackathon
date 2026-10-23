import streamlit as st
import pandas as pd
import base64
import json
import io
from openai import OpenAI

# ---------- Configuración de la págiana ----------
st.set_page_config(page_title="Imagen a Excel", layout="centered")
st.title("📸 Imagen a Excel (Demo para Hackathon)")
st.write("Sube una foto que contenga datos de una tabla y la IA extraerá la información automáticamente para generar un archivo Excel.")

# ---------- Configuración en la barra lateral ----------
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Clave API de OpenAI", type="password", value="TU_CLAVE_OPENAI")
    modelo = st.selectbox("Modelo", ["gpt-4o-mini", "gpt-4o"], index=0)
    st.caption("Si la llamada a la API falla, la aplicación devolverá datos simulados para que la demo funcione sin problemas.")

# ---------- Subida de archivo ----------
archivo_subido = st.file_uploader("Elige una imagen", type=["png", "jpg", "jpeg"])

if archivo_subido is not None:
    # Mostrar la imagen original
    st.image(archivo_subido, caption="Imagen subida", use_container_width=True)

    if st.button("🚀 Iniciar extracción", type="primary"):
        with st.spinner("La IA está analizando la imagen..."):
            try:
                # ---------- Intentar llamar a la API real ----------
                if not api_key or api_key == "TU_CLAVE_OPENAI":
                    raise ValueError("No se proporcionó la clave API")

                cliente = OpenAI(api_key=api_key)

                # Codificar la imagen en base64
                bytes_imagen = archivo_subido.getvalue()
                imagen_base64 = base64.b64encode(bytes_imagen).decode("utf-8")

                # Construir el prompt: forzar la devolución de un arreglo JSON
                prompt = """
                Eres un asistente de extracción de datos. Analiza la imagen y extrae todos los datos de la tabla.
                Devuelve ÚNICAMENTE un arreglo JSON, donde cada objeto representa una fila.
                Las claves deben ser nombres de campo simples en español (por ejemplo: producto, cantidad, precio).
                No envuelvas el JSON en bloques de código markdown. Devuelve solo el JSON puro.
                """

                respuesta = cliente.chat.completions.create(
                    model=modelo,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{imagen_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )

                contenido_crudo = respuesta.choices[0].message.content
                datos_parseados = json.loads(contenido_crudo)

                # Manejar las distintas estructuras JSON posibles
                if isinstance(datos_parseados, list):
                    lista_datos = datos_parseados
                elif isinstance(datos_parseados, dict):
                    # Buscar el primer valor que sea una lista dentro del diccionario
                    lista_datos = next(
                        (v for v in datos_parseados.values() if isinstance(v, list)),
                        [datos_parseados]
                    )
                else:
                    lista_datos = [datos_parseados]

            except Exception as e:
                # ---------- Respaldo: datos simulados ----------
                st.warning(f"La llamada a la API falló ({str(e)[:60]}...). Se usarán datos simulados para la demo.")
                lista_datos = [
                    {"producto": "Ratón inalámbrico", "cantidad": 3, "precio": 29.99},
                    {"producto": "Cable USB-C", "cantidad": 5, "precio": 12.50},
                    {"producto": "Soporte para portátil", "cantidad": 2, "precio": 45.00},
                    {"producto": "Teclado mecánico", "cantidad": 1, "precio": 89.99},
                ]

            # ---------- Mostrar resultados y generar Excel ----------
            if lista_datos:
                df = pd.DataFrame(lista_datos)
                st.success("✅ ¡Extracción completada!")
                st.subheader("Vista previa de los datos")
                st.dataframe(df, use_container_width=True)

                # Generar el Excel en memoria
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
                    df.to_excel(escritor, sheet_name="Datos Extraídos", index=False)
                buffer.seek(0)

                # Botón de descarga
                st.download_button(
                    label="📥 Descargar Excel",
                    data=buffer,
                    file_name="datos_extraidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No se pudo extraer ningún dato válido. Por favor, prueba con otra imagen.")

else:
    st.info("👆 Por favor, sube una imagen para comenzar.")
