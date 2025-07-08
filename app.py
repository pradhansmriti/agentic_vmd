import streamlit as st
import requests
import os

import streamlit as st
import requests
import os

st.set_page_config(page_title="OpenRouter GPT-4o Chat")

st.title("🧠 LLM Chat with OpenRouter")
st.markdown("Enter a prompt and get a response from `gpt-4o` via OpenRouter API.")

# Input prompt
prompt = st.text_area("📝 Prompt", placeholder="e.g. How do I check if an object is an instance of a class in Python?")

if st.button("Submit"):
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Querying OpenRouter..."):

            headers = {
                "Authorization": f"Bearer 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",
                "HTTP-Referer": "http://localhost",
                "X-Title": "streamlit-openrouter-ui",
                "Content-Type": "application/json"
            }

            data = {
                "model": "gpt-4o",  # You can also use "mistralai/mistral-7b-instruct"
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                st.success("✅ Response:")
                st.markdown(reply)
            else:
                st.error(f"Error {response.status_code}: {response.text}")
