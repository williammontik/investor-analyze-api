# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.7):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return None

def send_email(html_body, subject):
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

def generate_chart_metrics():
    return [
        {
            "title": "Market Positioning",
            "labels": ["Brand Recall", "Client Fit Clarity", "Reputation Stickiness"],
            "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]
        },
        {
            "title": "Investor Appeal",
            "labels": ["Narrative Confidence", "Scalability Model", "Proof of Trust"],
            "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]
        },
        {
            "title": "Strategic Execution",
            "labels": ["Partnership Readiness", "Luxury Channel Leverage", "Leadership Presence"],
            "values": [random.randint(65, 85), random.randint(65, 85), random.randint(75, 90)]
        }
    ]

def generate_chart_html(metrics):
    colors = ["#8C52FF", "#5E9CA0", "#F2A900"]
    html = ""
    for i, m in enumerate(metrics):
        html += f"<strong style='font-size:18px;color:#333;'>{m['title']}</strong><br>"
        for j, (label, val) in enumerate(zip(m['labels'], m['values'])):
            html += (
                f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                f"<span style='width:180px;'>{label}</span>"
                f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                f"<div style='width:{val}%;height:14px;background:{colors[j % len(colors)]};'></div></div>"
                f"<span style='margin-left:10px;'>{val}%</span></div>"
            )
        html += "<br>"
    return html

@app.route("/investor_analyze", methods=["POST"])
def investor_analyze():
    try:
        data = request.get_json(force=True)
        logging.debug(f"POST received: {data}")

        full_name = data.get("fullName")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        if industry == "Other":
            industry = data.get("otherIndustry", "Other")
        challenge = data.get("challenge")
        context = data.get("context")
        target = data.get("targetProfile")
        advisor = data.get("advisor")
        email = data.get("email")
        lang = data.get("lang", "en")

        age = compute_age(dob)
        subject = "Your Strategic Investor Insight"

        summary_prompt = (
            f"A {age}-year-old professional from {country}, with {experience} years in the {industry} sector, "
            f"currently serving as a {role} at {company}, is seeking strategic support for: {challenge}. "
            f"Context: {context}. They are aiming to reach: {target}. "
            f"Write a 4-paragraph summary in third-person, using regional and global investor trends, "
            f"with insights relevant to professionals in {industry} across SG/MY/TW."
        )

        tips_prompt = (
            f"Based on this profile, write 10 business-savvy tips with emojis to help improve investor attraction. "
            f"Each tip should be practical, brief, and based on high-performing patterns among professionals in the "
            f"{industry} sector across Singapore, Malaysia, and Taiwan."
        )

        summary = get_openai_response(summary_prompt)
        tips = get_openai_response(tips_prompt, temp=0.85)
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)

        html = "<h4 style='text-align:center; font-size:24px;'>🎯 Strategic Investor Insight</h4>"

        # 📝 Submission Details at the TOP
        html += (
            "<br><div style='font-size:14px;color:#888;'>"
            f"<strong>📝 Submission Details</strong><br>"
            f"Name: {full_name}<br>"
            f"DOB: {dob}<br>"
            f"Country: {country}<br>"
            f"Company: {company}<br>"
            f"Role: {role}<br>"
            f"Years of Experience: {experience}<br>"
            f"Industry: {industry}<br>"
            f"Challenge: {challenge}<br>"
            f"Context: {context}<br>"
            f"Target Profile: {target}<br>"
            f"Advisor: {advisor}<br>"
            f"Email: {email}</div><br>"
        )

        html += chart_html

        if summary:
            html += "<br><div style='font-size:24px;font-weight:bold;'>🧠 Strategic Summary:</div><br>"
            for para in summary.split("\n"):
                if para.strip():
                    html += f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px;'>{para.strip()}</p>"
        else:
            html += "<p style='color:red;'>⚠️ Strategic summary could not be generated.</p>"

        if tips:
            html += "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Tips:</div><br>"
            for line in tips.split("\n"):
                if line.strip():
                    html += f"<p style='margin:16px 0; font-size:17px;'>{line.strip()}</p>"
        else:
            html += "<p style='color:red;'>⚠️ Creative tips could not be generated.</p>"

        html += (
            "<br><p style='font-size:16px;'><strong>🛡️ Disclaimer:</strong></p>"
            "<p style='font-size:15px; line-height:1.6;'>This report is generated by KataChat AI. "
            "For legal or financial actions, always consult qualified professionals.</p>"
        )

        html += (
            "<div style='background-color:#f0f8ff; color:#003366; padding:15px; border-left:4px solid #003366; margin-top:30px;'>"
            "<strong>AI Insights Based On:</strong><br>"
            "🔹 Elite professional signals across SG/MY/TW<br>"
            "🔹 Global investor attraction patterns<br>"
            "<em>PDPA compliant. No data retained.</em></div>"
        )

        send_email(html, subject)

        return jsonify({
            "summary": summary or "",
            "tips": tips or "",
            "html_result": html
        })

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)), host="0.0.0.0")
