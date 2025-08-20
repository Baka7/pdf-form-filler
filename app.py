import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Form Filler Chatbot", layout="centered")

st.title("📄 PDF Form Filler Chatbot with Photo & Resume Upload")
st.write(
    "Upload a fillable PDF form, answer the chatbot's questions, upload your photo and resume, and download your filled form."
)

# ==== Upload PDF Form ====
uploaded_file = st.file_uploader("Upload your interactive PDF", type=["pdf"])

# Extra uploads
photo_upload = st.file_uploader("Upload your Photo", type=["png", "jpg", "jpeg"])
resume_upload = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # Extract fields
    field_list = []
    for page in doc:
        widgets = page.widgets()
        if widgets:
            for w in widgets:
                choices = []
                if w.field_type_string in ["ComboBox", "ListBox"]:
                    try:
                        choices = list(w.choice_values)
                    except Exception:
                        pass

                field_list.append(
                    {
                        "name": w.field_name,
                        "value": w.field_value,
                        "type": w.field_type_string,
                        "required": w.field_flags & 2 != 0,
                        "choices": choices,
                        "on_state_value": getattr(w, "on_state_value", None),
                    }
                )

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    st.subheader("💬 Fill the Form Fields Below")

    # Render UI per field type
    for i, field in enumerate(field_list):
        label = f"**{field['name']}**"
        if field["required"]:
            label += " (Required)"

        default_val = st.session_state.answers.get(field["name"], field["value"])

        # Construct a unique key for each input element
        unique_key = f"{field['type']}_{field['name']}_{i}"

        if field["type"] == "CheckBox":
            on_val = field.get("on_state_value") or "Yes"
            checked = default_val == on_val
            checked_new = st.checkbox(label, value=checked, key=unique_key)
            st.session_state.answers[field["name"]] = on_val if checked_new else "Off"

        elif field["type"] in ["ComboBox", "ListBox"]:
            options = field["choices"] if field["choices"] else [""]
            default_index = options.index(default_val) if default_val in options else 0
            selected = st.selectbox(label, options, index=default_index, key=unique_key)
            st.session_state.answers[field["name"]] = selected

        else:
            val = st.text_input(label, value=default_val or "", key=unique_key)
            st.session_state.answers[field["name"]] = val

    # ==== Fill and download button ====
    if st.button("✅ Fill PDF and Download"):
        # Fill form fields
        for page in doc:
            widgets = page.widgets()
            if widgets:
                for w in widgets:
                    if w.field_name in st.session_state.answers:
                        w.field_value = st.session_state.answers[w.field_name]
                        w.update()

        # Insert photo (if uploaded)
        if photo_upload:
            img_bytes = photo_upload.read()
            # Change these coordinates to match your photo box (x0, y0, x1, y1)
            rect = fitz.Rect(250, 100, 650, 250)
            page0 = doc[0]  # Insert on first page
            page0.insert_image(rect, stream=img_bytes)

        # ==== Resume attachment ====
        if resume_upload:
            resume_bytes = resume_upload.read()  # get file bytes from uploaded resume
            resume_filename = resume_upload.name or "resume.pdf"

            # Embed the uploaded resume in the PDF
            doc.embfile_add(resume_filename, resume_bytes)

            # Coordinates for the attachment icon on the first page
            rect = fitz.Rect(50, 650, 100, 700)  # adjust to where you want the icon

            # Add a clickable attachment icon linked to the embedded file
            page0 = doc[0]  # first page
            page0.add_file_annot(rect, resume_bytes, filename=resume_filename)

        # Save PDF to BytesIO
        output_pdf_bytes = io.BytesIO()
        doc.save(output_pdf_bytes)
        output_pdf_bytes.seek(0)

        st.download_button(
            label="⬇️ Download Filled PDF",
            data=output_pdf_bytes,
            file_name="filled_form.pdf",
            mime="application/pdf",
        )
