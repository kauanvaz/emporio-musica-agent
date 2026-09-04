import streamlit as st

from src.agent import interact_with_agent


st.set_page_config(page_title="Empório da Música", page_icon="🎸")

st.title("🎸 Empório da Música")
st.caption("Pergunte sobre produtos, pedidos e políticas da loja.")

# Mantém o histórico da conversa na UI
if "messages" not in st.session_state:
    st.session_state.messages = []

# Renderiza o histórico acumulado
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua mensagem..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Chama o agente passando o histórico acumulado
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                answer = interact_with_agent(prompt, history=st.session_state.messages[:-1])
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as exc:
                st.error(f"Ocorreu um erro: {exc}")
