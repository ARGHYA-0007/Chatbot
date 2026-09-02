
import streamlit as st
import requests

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Intro Extractor",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Intro Extractor")
st.write("Enter your text and let the FastAPI backend process it.")

# -----------------------------
# FastAPI URL
# -----------------------------
FASTAPI_URL = "http://127.0.0.1:8000"

# -----------------------------
# Input
# -----------------------------
user_input = st.text_area(
    "Enter your text:",
    placeholder="Write something here..."
)

# -----------------------------
# Predict Button
# -----------------------------
if st.button("Extract", type="primary"):

    if not user_input.strip():
        st.warning("Please enter some text.")
        st.stop()

    try:
        with st.spinner("Processing..."):

            response = requests.post(
                f"{FASTAPI_URL}/predicting",
                params={
                    "input_x": user_input
                },
                timeout=120
            )

        # -----------------------------
        # Handle Response
        # -----------------------------
        if response.status_code == 200:

            result = response.json()

            st.success("Successfully processed!")

            st.subheader("Result")

            # Display the complete response
            st.json(result)

        else:
            st.error(
                f"FastAPI returned an error "
                f"({response.status_code})"
            )

            st.code(response.text)

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to FastAPI. "
            "Make sure your FastAPI server is running."
        )

    except requests.exceptions.Timeout:
        st.error("The request took too long. Please try again.")

    except Exception as e:
        st.error(f"Unexpected error: {e}")


# -----------------------------
# Backend Health Check
# -----------------------------
st.divider()

if st.button("Check Backend"):

    try:
        response = requests.get(
            f"{FASTAPI_URL}/health",
            timeout=10
        )

        if response.status_code == 200:
            st.success("✅ FastAPI backend is running!")
            st.json(response.json())
        else:
            st.error(
                f"Backend returned status code "
                f"{response.status_code}"
            )

    except requests.exceptions.ConnectionError:
        st.error("❌ FastAPI backend is not reachable.")
