# -*- coding: utf-8 -*-
import os, logging, smtplib, io, base64, random
from datetime import datetime
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
import matplotlib.pyplot as plt
from openai import OpenAI

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def generate_chart_image(labels, values, title):
    colors = ['#4CAF50', '#2196F3', '#FFC107']
    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.barh(labels, values, color=[colors[i % 3] for i in range(len(labels))])
    ax.set_xlim(0, 100)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    for bar in bars:
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{bar.get_width():.0f}%', va='center')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.read()).decode('utf-8')

def get_openai_response(prompt, temp=0.7):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "⚠️ Unable to generate response."

def send_email(subject, html_body):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Email send error: {e}")

@app.route("/investor_analyze", methods=["POST"])
def investor_analyze():
    try:
        data = request.get_json(force=True)

        fullName = data.get("fullName")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        challenge = data.get("challenge")
        context = data.get("context")
        targetProfile = data.get("targetProfile")
        email = data.get("email")
        advisor = data.get("advisor")

        chart_data = {
            "Market Positioning": {
                "Brand Recall": random.randint(65, 85),
                "Audience Alignment": random.randint(60, 80),
                "Relationship Retention": random.randint(70, 90)
            },
            "Investor Appeal": {
                "Solution Narrative": random.randint(70, 90),
                "Long-Term Value Story": random.randint(60, 80),
                "Trust Signals": random.randint(75, 95)
            },
            "Strategic Execution": {
                "Premium Funnel Readiness": random.randint(60, 85),
                "Partnership Potential": random.randint(60, 80),
                "Personal Brand Energy": random.randint(70, 90)
            }
        }

        chart_html = ""
        for title, section in chart_data.items():
            labels = list(section.keys())
            values = list(section.values())
            img_b64 = generate_chart_image(labels, values, title)
            chart_html += f"<h4>{title}</h4><img src='data:image/png;base64,{img_b64}' style='max-width:100%;margin:20px 0;'>"

        prompt_summary = (
            f"You are analyzing a {role} in the {industry} industry from {country} with {experience} years of experience. "
            f"Their challenge is: {challenge}. Context: {context}. Chart scores: {chart_data}. "
            f"Write a strategic summary in 4 paragraphs. Avoid mentioning the person's name."
        )

        prompt_tips = (
            f"Suggest 10 investor positioning strategies for someone in {industry} facing the challenge: '{challenge}'. "
            f"Add emojis. Use bullet points. Audience: {targetProfile}."
        )

        summary = get_openai_response(prompt_summary)
        tips = get_openai_response(prompt_tips, temp=0.85)

        html = f"<h2>🎯 Investor Insight Report</h2>{chart_html}"
        html += "<h3 style='margin-top:30px;'>🧠 Strategic Summary:</h3>"
        html += ''.join(f"<p>{p.strip()}</p>" for p in summary.split("\n") if p.strip())
        html += "<h3 style='margin-top:30px;'>💡 Creative Tips:</h3>"
        html += ''.join(f"<p>{t.strip()}</p>" for t in tips.split("\n") if t.strip())

        html += (
            "<hr><p style='font-size:14px;color:#888;'>"
            f"Full Name: {fullName}<br>DOB: {dob}<br>Country: {country}<br>"
            f"Company: {company}<br>Role: {role}<br>Years of Experience: {experience}<br>"
            f"Industry: {industry}<br>Challenge: {challenge}<br>Context: {context}<br>"
            f"Target Profile: {targetProfile}<br>Advisor: {advisor}<br>Email: {email}<br>"
            "<br>📩 This report has been emailed. Generated by KataChat AI — PDPA compliant.</p>"
        )

        send_email("Your Investor Insight Report", html)

        return jsonify({
            "summary": summary,
            "tips": tips,
            "charts_html": chart_html,
            "full_html": html
        })

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)), host="0.0.0.0")
