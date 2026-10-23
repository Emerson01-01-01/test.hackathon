import streamlit as st
import pandas as pd
import base64
import json
import io
from openai import OpenAI

# ---------- Page Configuration ----------
st.set_page_config(page_title="Image to Excel", layout="centered")
st.title("📸 Image to Excel (Hackathon Demo)")
st.write("Upload a photo containing table data, and AI will automatically extract it and generate an Excel file.")

# ---------- Sidebar Configuration ----------
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key", type="password", value="YOUR_OPENAI_API_KEY")
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
    st.caption("If the API call fails, the application will return simulated data to ensure the demo runs smoothly.")

# ---------- File Upload ----------
uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display the original image
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    if st.button("🚀 Start Extraction", type="primary"):
        with st.spinner("AI is analyzing the image..."):
            try:
                # ---------- Try Calling the Real API ----------
                if not api_key or api_key == "YOUR_OPENAI_API_KEY":
                    raise ValueError("No API Key provided")

                client = OpenAI(api_key=api_key)

                # Encode the image as base64
                image_bytes = uploaded_file.getvalue()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")

                # Build the Prompt: Force return of JSON array
                prompt = """
                You are a data extraction assistant. Analyze the image and extract all table data.
                Return ONLY a JSON array, where each object represents a row.
                Keys must be simple English field names (e.g., item, quantity, price).
                Do not wrap the JSON in markdown code blocks. Output pure JSON only.
                """

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )

                raw_content = response.choices[0].message.content
                parsed = json.loads(raw_content)

                # Handle various possible JSON structures
                if isinstance(parsed, list):
                    data_list = parsed
                elif isinstance(parsed, dict):
                    # Find the first list value in the dictionary
                    data_list = next((v for v in parsed.values() if isinstance(v, list)), [parsed])
                else:
                    data_list = [parsed]

            except Exception as e:
                # ---------- Fallback: Simulated Data ----------
                st.warning(f"API call failed ({str(e)[:60]}...), using simulated data for the demo.")
                data_list = [
                    {"item": "Wireless Mouse", "quantity": 3, "price": 29.99},
                    {"item": "USB-C Cable", "quantity": 5, "price": 12.50},
                    {"item": "Laptop Stand", "quantity": 2, "price": 45.00},
                    {"item": "Mechanical Keyboard", "quantity": 1, "price": 89.99},
                ]

            # ---------- Display Results and Generate Excel ----------
            if data_list:
                df = pd.DataFrame(data_list)
                st.success("✅ Extraction Complete!")
                st.subheader("Preview Data")
                st.dataframe(df, use_container_width=True)

                # Generate Excel in memory
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, sheet_name="Extracted Data", index=False)
                buffer.seek(0)

                # Download Button
                st.download_button(
                    label="📥 Download Excel",
                    data=buffer,
                    file_name="extracted_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No valid data was extracted. Please try another image.")

else:
    st.info("👆 Please upload an image to start.")