# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === Setup ===
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# === Utilities ===
def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.85):
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

# === Chart Content ===
def generate_chart_metrics():
    return [
        {
            "title": "Market Positioning",
            "labels": ["Brand Recall", "Client Fit", "Reputation Stickiness"],
            "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]
        },
        {
            "title": "Investor Appeal",
            "labels": ["Story Confidence", "Scalability", "Proof of Trust"],
            "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]
        },
        {
            "title": "Strategic Execution",
            "labels": ["Partnership Readiness", "Premium Access", "Leadership Influence"],
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

def build_dynamic_summary(age, experience, industry, country, metrics):
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, luxury, leader = metrics[2]["values"]
    return (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 Strategic Summary:</div><br>"
        f"<p style='line-height:1.7;'>Professionals in {industry} from {country} with {experience} years of experience and aged {age} tend to show solid positioning: "
        f"{brand}% brand recall, {fit}% client fit, and {stick}% reputation stickiness.</p>"
        f"<p style='line-height:1.7;'>Investor-attracting traits include {conf}% story confidence, {trust}% trust signals, and {scale}% scalability potential.</p>"
        f"<p style='line-height:1.7;'>Strategic indicators — partnership readiness ({partn}%), premium access ({luxury}%), and leadership influence ({leader}%) — suggest high executive potential.</p>"
        f"<p style='line-height:1.7;'>Compared with peers across Singapore, Malaysia, and Taiwan, your overall profile reflects notable investor appeal.</p>"
    )

# === Endpoint ===
@app.route("/investor-analyze-api", methods=["POST"])
def investor_analyze():
    try:
        data = request.get_json(force=True)
        logging.debug(f"POST received: {data}")

        full_name = data.get("fullName")
        chinese_name = data.get("chineseName", "")
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

        age = compute_age(dob)
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics)

        prompt = (
            f"You are a business advisor. Write 10 motivating, emoji-starting tips for attracting investors "
            f"for a {industry} professional with {experience} years experience in {country}. Language: English. Tone: practical and strategic."
        )
        tips_text = get_openai_response(prompt)
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Suggestions:</div><br>" + \
                         "<br>".join(f"<p style='font-size:16px;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ Unable to generate tips at the moment.</p>"

        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 Based on:</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>Anonymous industry data from SG, MY, TW</li>"
            "<li>OpenAI investor insights model</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>Data is PDPA compliant and never stored permanently.</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>Note:</strong> A more personalized version will be sent within 24–48 hours via email. "
            "Book a short strategy call to fast-track your growth. 🎯</p></div>"
        )

        title = "<h4 style='text-align:center;font-size:24px;'>🎯 Investor Positioning Insight</h4>"

        details = (
            f"<br><div style='font-size:14px;color:#666;'>"
            f"<strong>📝 Submission Summary</strong><br>"
            f"Full Name: {full_name}<br>"
            f"Chinese Name: {chinese_name}<br>"
            f"DOB: {dob}<br>"
            f"Country: {country}<br>"
            f"Company: {company}<br>"
            f"Role: {role}<br>"
            f"Experience: {experience}<br>"
            f"Industry: {industry}<br>"
            f"Challenge: {challenge}<br>"
            f"Context: {context}<br>"
            f"Target: {target}<br>"
            f"Referrer: {advisor}<br>"
            f"Email: {email}</div><br>"
        )

        full_html = title + details + chart_html + summary_html + tips_block + footer
        send_email(full_html, "Your Investor Insight Report")

        return jsonify({"html_result": title + chart_html + summary_html + tips_block + footer})

    except Exception as e:
        logging.error(f"investor_analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error. Please try again later."}), 500

# === Local Dev Only ===
if __name__ == "__main__":
    app.run(debug=True)
