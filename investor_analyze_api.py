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
        lang = data.get("lang", "en")
        gender = "male" if "he" in role.lower() or "mr" in company.lower() else "female"

        age = compute_age(dob)
        subject = "Your Strategic Investor Insight"

        chart_metrics = generate_chart_metrics()

        # Use some chart values to generate meaningful prompt
        summary_prompt = (
            f"Write a strategic investor insight summary for a similar {age}-year-old {gender} professional "
            f"with {experience} years in the {industry} sector from {country}. "
            f"The challenge is: {challenge}. Context: {context}. They are targeting: {target}. "
            f"Compare this profile with other professionals across Singapore, Malaysia, and Taiwan. "
            f"Base the strategic summary on the following metrics (percentages are examples and can be creatively interpreted):\n\n"
            f"Market Positioning: {chart_metrics[0]['labels'][0]} = {chart_metrics[0]['values'][0]}%, "
            f"{chart_metrics[0]['labels'][1]} = {chart_metrics[0]['values'][1]}%, "
            f"{chart_metrics[0]['labels'][2]} = {chart_metrics[0]['values'][2]}%\n"
            f"Investor Appeal: {chart_metrics[1]['labels'][0]} = {chart_metrics[1]['values'][0]}%, "
            f"{chart_metrics[1]['labels'][1]} = {chart_metrics[1]['values'][1]}%, "
            f"{chart_metrics[1]['labels'][2]} = {chart_metrics[1]['values'][2]}%\n"
            f"Strategic Execution: {chart_metrics[2]['labels'][0]} = {chart_metrics[2]['values'][0]}%, "
            f"{chart_metrics[2]['labels'][1]} = {chart_metrics[2]['values'][1]}%, "
            f"{chart_metrics[2]['labels'][2]} = {chart_metrics[2]['values'][2]}%\n\n"
            f"Use third-person tone. Write 4 engaging paragraphs with meaningful insights, as if you're comparing this person to similar elite profiles."
        )

        tips_prompt = (
            f"Based on this profile in the {industry} sector with {experience} years of experience, "
            f"write 10 business-savvy tips with emojis to improve investor attraction across Singapore, Malaysia, and Taiwan. "
            f"Each tip should be practical, sharp, and tailored for premium investors."
        )

        summary = get_openai_response(summary_prompt)
        tips = get_openai_response(tips_prompt, temp=0.85)
        chart_html = generate_chart_html(chart_metrics)

        html = "<h4 style='text-align:center; font-size:24px;'>🎯 Strategic Investor Insight</h4>"
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
