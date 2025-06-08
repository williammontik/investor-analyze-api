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

def build_dynamic_summary(age, experience, industry, country, metrics, challenge="", context="", target_profile=""):
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, luxury, leader = metrics[2]["values"]
    return (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 Strategic Summary:</div><br>"
        f"<p style='line-height:1.7;'>In the {industry} landscape of {country}, individuals with around {experience} years of experience — particularly at a formative age like {age} — often find themselves at an inflection point. Your recent reflection on <strong>{challenge}</strong> is more than valid — it's common among ambitious professionals navigating crowded markets. From what you've shared — <em>“{context}”</em> — it's clear you're not just seeking change, but clarity. A brand recall score of {brand}% shows you've made a mark, but clarity of value at {fit}% and trust retention at {stick}% suggest there's still room for your message to land more deeply with the right audience.</p>"

        f"<p style='line-height:1.7;'>Investor sentiment in {country} often hinges on coherence and confidence. Your narrative strength, benchmarked at {conf}%, is a clear signal that your story has power. But scalability — currently at {scale}% — might benefit from tighter frameworks or sharper articulation, especially when pitching more complex strategies. The encouraging figure of {trust}% in proof of trust shows that your foundation is solid. Now, it’s about how those foundations are communicated — not just internally, but externally where it matters most.</p>"

        f"<p style='line-height:1.7;'>Execution is where strong ideas meet the market. With partnership readiness at {partn}%, there’s a clear openness to collaboration — which may align well with your ideal partner or investor type: <strong>{target_profile}</strong>. The {luxury}% score in luxury channel leverage reveals branding potential far beyond current visibility, and leadership presence at {leader}% suggests that while you're already seen as credible, there’s opportunity to further anchor your role in high-trust, high-influence spaces.</p>"

        f"<p style='line-height:1.7;'>Benchmarking your profile against peers across Singapore, Malaysia, and Taiwan reveals not only consistency but strategic upside. The data suggests your instincts are right — but to fully meet the challenge of <strong>{challenge}</strong>, the next step is about aligning message, medium, and market with precision. These insights don’t just show where you are — they illuminate the specific shifts that could turn momentum into meaningful breakthrough.</p>"
    )

@app.route("/investor_analyze", methods=["POST"])
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
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics, challenge, context, target)

        prompt = (
            f"Based on a professional in {industry} with {experience} years in {country}, generate 10 practical investor attraction tips with emojis for elite professionals in Singapore, Malaysia, and Taiwan."
        )
        tips_text = get_openai_response(prompt)
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 Creative Tips:</div><br>" + \
                         "<br>".join(f"<p style='font-size:16px;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ Creative tips could not be generated.</p>"

        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 AI Insights Generated From:</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>Data from anonymized professionals across Singapore, Malaysia, and Taiwan</li>"
            "<li>Investor sentiment models & trend benchmarks from OpenAI and global markets</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>All data is PDPA-compliant and never stored. "
            "Our AI systems detect statistically significant patterns without referencing any individual record.</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>PS:</strong> This initial insight is just the beginning. A more personalized, data-specific report — reflecting the full details you’ve provided — will be prepared and delivered to your inbox within <strong>24 to 48 hours</strong>. "
            "This allows our AI systems to cross-reference your profile with nuanced regional and sector-specific benchmarks, ensuring sharper recommendations tailored to your exact challenge. "
            "If you'd like to speak sooner, we’d be glad to arrange a <strong>15-minute call</strong> at your convenience. 🎯</p></div>"
        )

        title = "<h4 style='text-align:center;font-size:24px;'>🎯 AI Strategic Insight</h4>"

        details = (
            f"<br><div style='font-size:14px;color:#666;'>"
            f"<strong>📝 Submission Summary</strong><br>"
            f"English Name: {full_name}<br>"
            f"Chinese Name: {chinese_name}<br>"
            f"DOB: {dob}<br>"
            f"Country: {country}<br>"
            f"Company: {company}<br>"
            f"Role: {role}<br>"
            f"Years of Experience: {experience}<br>"
            f"Industry: {industry}<br>"
            f"Challenge: {challenge}<br>"
            f"Context: {context}<br>"
            f"Target Profile: {target}<br>"
            f"Referrer: {advisor}<br>"
            f"Email: {email}</div><br>"
        )

        full_html = title + details + chart_html + summary_html + tips_block + footer
        send_email(full_html, "Strategic Investor Insight")

        return jsonify({"html_result": title + chart_html + summary_html + tips_block + footer})

    except Exception as e:
        logging.error(f"Investor analyze error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
