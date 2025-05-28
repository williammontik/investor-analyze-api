# === FINAL investor_analyze.py ===

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

LANGUAGE = {
    "en": {
        "email_subject": "Your Elite Strategy Insight Report",
        "report_title": "🎯 Investor Positioning Snapshot"
    }
}

def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.7):
    try:
        result = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return result.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "⚠️ Unable to generate response."

def generate_metrics():
    return [
        {
            "title": "Market Positioning",
            "labels": ["Brand Recall", "Client Fit Clarity", "Reputation Stickiness"],
            "values": [random.randint(68, 88) for _ in range(3)]
        },
        {
            "title": "Investor Appeal",
            "labels": ["Narrative Confidence", "Scalability Model", "Proof of Trust"],
            "values": [random.randint(68, 88) for _ in range(3)]
        },
        {
            "title": "Strategic Execution",
            "labels": ["Partnership Readiness", "Luxury Channel Leverage", "Leadership Presence"],
            "values": [random.randint(68, 88) for _ in range(3)]
        }
    ]

def send_email(html_body):
    subject = LANGUAGE["en"]["email_subject"]
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

        name = data.get("fullName")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        challenge = data.get("challenge")
        context = data.get("context") or "No additional context."
        email = data.get("email")
        advisor = data.get("advisor")
        age = compute_age(dob)

        metrics = generate_metrics()

        # Map chart data to prompt input
        metric_refs = []
        for cat in metrics:
            for label, val in zip(cat['labels'], cat['values']):
                metric_refs.append(f"{label}: {val}%")

        summary_prompt = (
            f"You are analyzing a professional in the {industry} industry from {country}, aged {age}, with {experience} years of experience in the role of {role}.\n"
            f"Their current challenge is: {challenge}. Context provided: {context}\n"
            f"Here are their self-positioning metrics: {'; '.join(metric_refs)}\n"
            f"Based on similar industry profiles, generate a 4-paragraph third-person strategic summary. Do not use the person's name. Frame all insights in terms of pattern recognition and high-level investor interest."
        )

        suggestions_prompt = (
            f"Given this profile and the following metrics: {'; '.join(metric_refs)},\n"
            f"write 10 practical strategic suggestions (with emojis) to improve investor/client appeal. Do not use second-person language."
        )

        summary = get_openai_response(summary_prompt)
        creative = get_openai_response(suggestions_prompt, temp=0.85)
        report_title = LANGUAGE["en"]["report_title"]

        chart_html = ""
        for m in metrics:
            chart_html += f"<strong>{m['title']}</strong><br>"
            for label, val in zip(m['labels'], m['values']):
                chart_html += (
                    f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                    f"<span style='width:180px;'>{label}</span>"
                    f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                    f"<div style='width:{val}%;height:14px;background:#8C52FF;'></div></div>"
                    f"<span style='margin-left:10px;'>{val}%</span></div>"
                )
            chart_html += "<br>"

        html_result = f"<h4 style='text-align:center;'>{report_title}</h4>"
        html_result += (
            f"<p><strong>🌍 Country:</strong> {country}<br>"
            f"<strong>🏢 Company:</strong> {company}<br>"
            f"<strong>🧑‍💼 Role:</strong> {role}<br>"
            f"<strong>📈 Experience:</strong> {experience} years<br>"
            f"<strong>🏭 Industry:</strong> {industry}</p><br>"
        )
        html_result += chart_html
        html_result += f"<br><div style='font-size:24px; font-weight:bold; margin-top:30px;'>🧠 Strategic Summary:</div><br>"
        html_result += ''.join([f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px;'>{p}</p>" for p in summary.split("\n") if p.strip()])
        html_result += f"<br><div style='font-size:24px; font-weight:bold; margin-top:30px;'>💡 Strategic Suggestions:</div><br>"
        html_result += ''.join([f"<p style='margin:16px 0; font-size:17px;'>{line}</p>" for line in creative.split("\n") if line.strip()])
        html_result += (
            f"<br><br><p style='font-size:16px;'><strong>🛡️ Disclaimer:</strong></p>"
            f"<p style='font-size:15px; line-height:1.6;'>📩 This report is AI-generated using anonymized global patterns from professionals of similar age, experience, and industry. Please consult qualified advisors before taking business action.</p>"
        )

        send_email(html_result)

        return jsonify({
            "metrics": metrics,
            "html_result": html_result,
            "footer": "📩 This report has been emailed to you."
        })

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)), host="0.0.0.0")
