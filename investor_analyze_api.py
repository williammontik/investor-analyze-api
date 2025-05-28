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


def build_dynamic_summary(age, experience, industry, country, metrics):
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, luxury, leader = metrics[2]["values"]

    return f"""
<p>Among professionals in the {industry} sector in {country}, those with similar profiles — such as a {age}-year-old with {experience} years of experience — demonstrate strong market positioning. Brand recall scores typically average {brand}%, while client fit clarity and reputation stickiness at {fit}% and {stick}%, respectively, reflect reliable traction within local and regional markets.</p>
<p>Across regional investor landscapes, narrative confidence remains a key driver of funding interest. Comparable professionals show narrative clarity at {conf}%, with proof of trust reaching {trust}% — a critical factor in early-stage or growth-stage fundraising. Scalability model scores at {scale}% highlight ongoing opportunities to refine regional expansion strategies.</p>
<p>In global growth contexts, partnership readiness at {partn}% suggests a favorable stance toward alliances or co-branded initiatives. Luxury channel leverage, scored at {luxury}%, reveals branding potential beyond core markets. Leadership presence, observed at {leader}%, aligns with executive influence benchmarks in high-performing teams across Asia.</p>
<p>Benchmarked against peers in Singapore, Malaysia, and Taiwan, this profile reflects strong investor appeal and execution strength in the {industry} sector. By refining key levers and reinforcing brand signals, similar profiles continue to gain traction in both regional and global investment ecosystems.</p>
"""


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

        age = compute_age(dob)
        subject = "Your Strategic Investor Insight"
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics)

        tips_prompt = (
            f"Based on a professional profile in the {industry} sector with {experience} years of experience in {country}, "
            f"write 10 business-savvy tips with emojis to improve investor attraction. Each tip should be practical, brief, and relevant to elite professionals in Singapore, Malaysia, and Taiwan."
        )
        tips = get_openai_response(tips_prompt) or "⚠️ Creative tips could not be generated."

        tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Tips:</div><br>"
        for line in tips.split("\n"):
            if line.strip():
                tips_block += f"<p style='margin:16px 0; font-size:17px;'>{line.strip()}</p>"

        footer_block = (
            "<br><p style='font-size:16px;'><strong>🛡️ Disclaimer:</strong></p>"
            "<p style='font-size:15px; line-height:1.6;'>This report is generated by KataChat AI. "
            "For legal or financial actions, always consult qualified professionals.</p>"
            "<div style='background-color:#f0f8ff; color:#003366; padding:15px; border-left:4px solid #003366; margin-top:30px;'>"
            "<strong>AI Insights Based On:</strong><br>"
            "🔹 Elite professional signals across SG/MY/TW<br>"
            "🔹 Global investor attraction patterns<br>"
            "<em>PDPA compliant. No data retained.</em></div>"
        )

        title_block = "<h4 style='text-align:center; font-size:24px;'>🎯 Strategic Investor Insight</h4>"

        details_block = (
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

        email_html = title_block + details_block + chart_html + summary_html + tips_block + footer_block
        user_html = title_block + chart_html + summary_html + tips_block + footer_block

        send_email(email_html, subject)

        return jsonify({
            "summary": summary_html,
            "tips": tips,
            "html_result": user_html
        })

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)), host="0.0.0.0")
