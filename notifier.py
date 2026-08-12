import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL


def send_price_alert(
    product_name: str,
    platform: str,
    current_price: float,
    target_price: float,
    product_url: str,
) -> bool:
    """
    Send a Gmail alert when a product hits the target price.
    Returns True on success, False on failure.
    """
    try:
        savings = max(0, target_price - current_price)
        subject = f"🎯 Target Price Hit: {product_name[:50]}"

        # Plain text fallback
        text_body = (
            f"Price Alert — {platform.upper()}\n\n"
            f"Product      : {product_name}\n"
            f"Current Price: ₹{current_price:,.0f}\n"
            f"Your Target  : ₹{target_price:,.0f}\n"
            f"You Save     : ₹{savings:,.0f}\n"
            f"Link         : {product_url}\n"
        )

        savings_row = (
            f"<tr><td>You save</td>"
            f"<td><strong style='color:#B12704;'>₹{savings:,.0f}</strong></td></tr>"
            if savings > 0 else ""
        )

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body       {{ font-family: Arial, sans-serif; background: #f0f0f0; margin: 0; padding: 20px; }}
    .card      {{ max-width: 560px; margin: auto; background: #fff;
                  border-radius: 8px; overflow: hidden;
                  box-shadow: 0 2px 8px rgba(0,0,0,.12); }}
    .header    {{ background: #ff9900; padding: 20px 24px; color: #111; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .badge     {{ display: inline-block; background: #111; color: #ff9900;
                  font-size: 11px; font-weight: bold; padding: 2px 8px;
                  border-radius: 3px; margin-bottom: 8px; letter-spacing: 1px; }}
    .body      {{ padding: 24px; }}
    .product   {{ font-size: 16px; font-weight: bold; margin-bottom: 16px; color: #111; line-height: 1.4; }}
    table      {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    td         {{ padding: 8px 0; border-bottom: 1px solid #eee; font-size: 14px; color: #333; }}
    td:last-child {{ text-align: right; }}
    .current   {{ font-size: 28px; font-weight: bold; color: #007600; }}
    .btn       {{ display: inline-block; background: #ff9900; color: #111;
                  padding: 12px 28px; border-radius: 4px; text-decoration: none;
                  font-weight: bold; font-size: 15px; }}
    .footer    {{ font-size: 11px; color: #999; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <span class="badge">{platform.upper()}</span>
      <h1>🎯 Your Target Price Has Been Hit!</h1>
    </div>
    <div class="body">
      <p class="product">{product_name}</p>
      <table>
        <tr>
          <td>Current price</td>
          <td><span class="current">₹{current_price:,.0f}</span></td>
        </tr>
        <tr>
          <td>Your target</td>
          <td>₹{target_price:,.0f}</td>
        </tr>
        {savings_row}
      </table>
      <a href="{product_url}" class="btn">Buy Now →</a>
      <p class="footer">Sent by your Price Tracker · Prices can change any time.</p>
    </div>
  </div>
</body>
</html>
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = RECIPIENT_EMAIL

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

        print(f"  ✅ Alert sent → {RECIPIENT_EMAIL}")
        return True

    except Exception as e:
        print(f"  ❌ Email failed: {e}")
        return False
