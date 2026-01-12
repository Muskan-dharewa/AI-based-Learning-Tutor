import os
import streamlit as st
from openai import OpenAI
import re

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

client = OpenAI(api_key=API_KEY)

FORMAT_RULES = """
STRICT RULES:
- ALL equations MUST be written using LaTeX
- ALWAYS wrap equations using \\[ and \\]
- NEVER use [ ] or < >
- Do NOT write equations inline
- Put each equation on its own line
"""

st.set_page_config(page_title="AI Learning Tutor", layout="centered")
st.title("📘 AI Learning Adaptive Tutor -Making Learning easier")
st.write("Personalized explanations, quizzes, and practice questions.")


defaults = {
    "generated": False,
    "content": {},
    "mcq_submitted": {},
    "mcq_correct": {},
    "score": 0,
    "last_topic": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


difficulty = st.selectbox(
    "🎯 Select difficulty:",
    ["Beginner", "Intermediate", "Advanced"]
)

topic = st.text_input("📚 Enter the topic you want to learn:")


if topic and topic != st.session_state.last_topic:
    st.session_state.generated = False
    st.session_state.mcq_submitted = {}
    st.session_state.mcq_correct = {}
    st.session_state.score = 0

def fix_latex(text):
    return text.replace("[", "\\[").replace("]", "\\]")


def parse_mcqs(text):
    questions = re.split(r"\n(?=Q\d+\.)", text)
    parsed = []

    for q in questions:
        lines = [l.strip() for l in q.split("\n") if l.strip()]
        if len(lines) < 6:
            continue

        question = lines[0]
        options = lines[1:5]
        answer = lines[5].split(":")[-1].strip()

        parsed.append((question, options, answer))

    return parsed


if topic and st.button("🚀 Generate Learning Content"):
    with st.spinner("AI is preparing your learning material..."):

        explanation = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
Explain the topic "{topic}" clearly.

Difficulty: {difficulty}

- Use headings
- Use bullet points

{FORMAT_RULES}
"""
            }]
        ).choices[0].message.content

        mcq_text = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
Create EXACTLY 15 MCQs on "{topic}".
Difficulty: {difficulty}

STRICT RULES:
- Do NOT add introduction text
- Do NOT add headings
- Start directly with Q1.
- Follow ONLY this format:

Q1. Question text
A. option
B. option
C. option
D. option
Answer: A
"""
            }]
        ).choices[0].message.content

        practice = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Create 10 practice questions on {topic}. Difficulty: {difficulty}"
            }]
        ).choices[0].message.content

        solutions = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
Provide detailed solutions for the practice questions on "{topic}".

{FORMAT_RULES}
"""
            }]
        ).choices[0].message.content

        st.session_state.content = {
            "explanation": explanation,
            "mcq_text": mcq_text,
            "practice": practice,
            "solutions": solutions
        }

        st.session_state.last_topic = topic
        st.session_state.generated = True


if st.session_state.generated:

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📘 Explanation", "📝 MCQs (15)", "✏️ Practice", "✅ Solutions"]
    )

    with tab1:
        st.markdown(fix_latex(st.session_state.content["explanation"]), unsafe_allow_html=True)

    with tab2:
        st.subheader("📝 Practice MCQs")
        st.info(f"🎯 Score: {st.session_state.score} / 15")

        mcqs = parse_mcqs(st.session_state.content["mcq_text"])

        for i, (q, opts, ans) in enumerate(mcqs):

            st.markdown(f"### {q}")

            choice = st.radio(
                "Choose one:",
                opts,
                key=f"mcq_{i}"
            )

            if st.button("Submit", key=f"submit_{i}"):
                st.session_state.mcq_submitted[i] = True

                if choice.split(".")[0] == ans:
                    if not st.session_state.mcq_correct.get(i, False):
                        st.session_state.score += 1
                    st.session_state.mcq_correct[i] = True
                    st.balloons()
                else:
                    st.session_state.mcq_correct[i] = False

            if st.session_state.mcq_submitted.get(i):
                if st.session_state.mcq_correct.get(i):
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Correct answer: {ans}")

            st.divider()

    with tab3:
        st.markdown(st.session_state.content["practice"], unsafe_allow_html=True)

    with tab4:
        st.markdown(fix_latex(st.session_state.content["solutions"]), unsafe_allow_html=True)

    if st.button("🔄 Learn a New Topic"):
        st.session_state.clear()
        st.rerun()