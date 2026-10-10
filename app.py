import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
import datetime

# PAGE CONFIG

st.set_page_config(page_title="Microplastic Detector", layout="wide")

# UI WIDTH CONTROL
st.markdown(
    """
    <style>
        .main {
            max-width: 1200px;
            margin: auto;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Microplastic Detection System")
st.write(
    "Upload an image to classify microplastic type, see probabilities, "
    "and download a detailed PDF report."
)


# LOAD MODEL

MODEL_PATH = r"C:\Users\syam\OneDrive\Desktop\microplastic\Project folder\runs\classify\train11\weights\best.pt"
model = YOLO(MODEL_PATH)


# BALANCED UI LAYOUT

left_col, right_col = st.columns([1.1, 1.9])

with left_col:
    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png"]
    )


# PROCESS IMAGE (LOGIC UNCHANGED)

if uploaded_file is not None:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)

    with left_col:
        st.image(img, caption="Uploaded Image", width=320)

    with st.spinner("Detecting microplastic type..."):
        results = model.predict(img_np)

    result = results[0]

    if result.probs is None:
        st.error("No probabilities returned by the model.")
        st.stop()

    probs = result.probs.data.cpu().numpy()
    class_names = result.names
    prob_dict = {class_names[i]: float(probs[i]) for i in range(len(probs))}

    # SAME LOGIC 
    none_prob = prob_dict.get("none", 1.0)
    other_probs = [prob for cls, prob in prob_dict.items() if cls != "none"]

    if none_prob >= 0.4:
        detection_status = "Microplastic Not Detected"
    else:
        if any(prob >= 0.5 for prob in other_probs):
            detection_status = "Microplastic Detected"
        else:
            detection_status = "Microplastic Not Detected"

    # DISPLAY RESULTS

    with right_col:
        st.subheader(" Detection Result")
        if "Not Detected" in detection_status:
            st.markdown(
                f"<h3 style='color:red'>{detection_status}</h3>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<h3 style='color:green'>{detection_status}</h3>",
                unsafe_allow_html=True
            )

        st.subheader(" Class Probabilities")
        for cls, prob in prob_dict.items():
            bar_color = "green" if prob < 0.4 else "red"
            st.markdown(
                f"{cls}: `{prob:.4f}` | "
                f"<span style='color:{bar_color}'>■</span>",
                unsafe_allow_html=True
            )

        st.subheader(" Download Detection Report (With Image)")

        if st.button("Generate Report"):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"microplastic_report_{timestamp}.pdf"
            c = canvas.Canvas(report_path, pagesize=letter)

            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, 750, "Microplastic Detection Report")

            c.setFont("Helvetica", 10)
            c.drawString(50, 735, f"Generated on: {datetime.datetime.now()}")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 710, f"Detection Result: {detection_status}")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 660, "Class Probabilities:")
            c.setFont("Helvetica", 10)

            y = 640
            for cls, prob in prob_dict.items():
                c.drawString(60, y, f"{cls}: {prob:.4f}")
                y -= 15

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y - 20, "Input Image:")

            img_reader = ImageReader(img)
            pdf_img_width = 300
            pdf_img_height = int(img.height * (300 / img.width))

            c.drawImage(
                img_reader,
                50,
                y - 20 - pdf_img_height,
                width=pdf_img_width,
                height=pdf_img_height
            )

            c.showPage()
            c.save()

            with open(report_path, "rb") as pdf_file:
                st.download_button(
                    "⬇ Download Report PDF",
                    pdf_file,
                    report_path,
                    "application/pdf"
                )

            try:
                os.remove(report_path)
            except:
                pass
