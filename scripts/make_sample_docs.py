"""
Create the sample company documents used by the prototype.

"Nimbus Systems" is a made-up company. Making our own documents (instead of
downloading real ones) has two advantages:
  1. We know exactly what facts are inside, so we can write test questions
     with known correct answers and known correct sources.
  2. We get one of each file type the client cares about: PDF, DOCX and TXT.

Run it once:   python scripts/make_sample_docs.py
It writes the files into data/docs/. You can delete them and add your own
documents later; the rest of the code does not care what the files contain.
"""

from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).resolve().parent.parent / "data" / "docs"

# Each document is a title plus a list of (section heading, paragraphs).
# For PDFs, every section starts on a new page so citations show page numbers.

EMPLOYEE_HANDBOOK = (
    "Nimbus Systems Employee Handbook",
    [
        ("1. Working Hours", [
            "Standard working hours at Nimbus Systems are 9:00 to 17:30, Sunday to Thursday, "
            "with a one-hour lunch break. Core hours, when everyone must be available, are 10:00 to 15:00.",
            "Employees may start between 7:30 and 10:00 as long as they work 37.5 hours per week. "
            "Flexible start times must be agreed with your manager.",
        ]),
        ("2. Annual Leave", [
            "Full-time employees receive 21 days of paid annual leave per calendar year. "
            "After five years of service this increases to 25 days.",
            "Leave requests must be submitted in the HR portal at least 10 working days in advance "
            "for absences longer than three days. Up to 5 unused days may be carried over to the next "
            "year; carried-over days expire on 31 March.",
        ]),
        ("3. Sick Leave", [
            "Employees are entitled to 15 days of paid sick leave per year. "
            "If you are sick for more than two consecutive days, you must upload a medical certificate "
            "to the HR portal within 48 hours of returning to work.",
            "Notify your manager before 9:30 on the first day of absence by phone or chat.",
        ]),
        ("4. Parental Leave", [
            "Birth mothers receive 14 weeks of fully paid maternity leave. "
            "Fathers and secondary carers receive 10 working days of paid paternity leave, "
            "which must be taken within three months of the birth or adoption.",
        ]),
        ("5. Public Holidays", [
            "The company is closed on all official public holidays. The HR team publishes the "
            "holiday calendar for the coming year every December on the intranet.",
        ]),
    ],
)

REMOTE_WORK_POLICY = (
    "Nimbus Systems Remote Work Policy",
    [
        ("1. Eligibility", [
            "Employees who have completed their three-month probation period may work remotely "
            "up to two days per week, with their manager's approval.",
            "Roles that require physical presence, such as reception and facilities, are not eligible.",
        ]),
        ("2. Equipment and Internet", [
            "The company provides a laptop, headset and one external monitor for home use. "
            "Employees working remotely receive a monthly internet allowance of 150 SAR, paid with salary.",
        ]),
        ("3. Security When Working Remotely", [
            "You must connect through the company VPN when accessing internal systems from outside the office. "
            "Do not work on confidential documents in public places such as cafes, and never use public "
            "computers to access company email.",
        ]),
        ("4. Working From Abroad", [
            "Working from another country requires written approval from HR and is limited to 10 working "
            "days per year, because of tax and legal rules.",
        ]),
    ],
)

IT_GUIDE = (
    "Nimbus Systems IT Help Guide",
    [
        ("Resetting Your Password", [
            "Passwords must be at least 12 characters long and are changed every 90 days.",
            "To reset a forgotten password, go to https://reset.nimbus.example and verify your identity "
            "with the code sent to your registered mobile phone. If you are locked out after 5 failed "
            "attempts, your account unlocks automatically after 30 minutes, or you can call the IT "
            "helpdesk to unlock it immediately.",
        ]),
        ("Connecting to the VPN", [
            "Install the GlobalConnect VPN client from the Self Service app on your laptop. "
            "Sign in with your company email and approve the login request in the authenticator app.",
            "If the VPN does not connect, restart your laptop, check your internet connection, and make sure "
            "the date and time on your laptop are correct. If it still fails, open a ticket with the IT helpdesk.",
        ]),
        ("Contacting the IT Helpdesk", [
            "The IT helpdesk is open Sunday to Thursday from 8:00 to 18:00. "
            "You can reach it at extension 4357 (HELP) or by opening a ticket at https://help.nimbus.example. "
            "Urgent outside-hours issues can be reported to the on-call number 050 555 0199.",
        ]),
        ("Laptops and Equipment", [
            "Every employee receives a company laptop on their first day. Laptops are replaced every 3 years.",
            "Lost or stolen equipment must be reported to IT and security within 24 hours. "
            "Installing unapproved software on company laptops is not allowed; request new software through "
            "the Self Service app.",
        ]),
        ("Wi-Fi in the Office", [
            "Employees use the 'Nimbus-Corp' network, which signs you in automatically with your company account. "
            "Visitors use the 'Nimbus-Guest' network; reception provides a daily password.",
        ]),
    ],
)

EXPENSE_POLICY = """Nimbus Systems Travel and Expense Policy

# 1. Submitting Expenses
All business expenses must be submitted in the Finance portal within 30 days of the purchase,
with a photo or scan of the receipt attached. Expenses submitted later than 30 days will not be
reimbursed unless your department head approves an exception.

Approved expenses are paid with the next monthly salary.

# 2. Travel Booking
All flights and hotels must be booked through the company travel agent, TravelDesk.
Employees fly economy class for flights shorter than 6 hours. Business class is allowed for
flights of 6 hours or more, and for all flights taken by directors.

# 3. Daily Allowance
When travelling for work, employees receive a daily meal allowance of 200 SAR inside the country
and 350 SAR outside the country. Alcohol is never reimbursed.

# 4. Taxis and Mileage
Taxis and ride-hailing apps are reimbursed for business trips. Employees who use their own car for
business receive 1 SAR per kilometre.
"""

ONBOARDING_GUIDE = """Nimbus Systems New Employee Onboarding Guide

# Your First Day
Please arrive at 9:00 at the main reception on the ground floor and bring your national ID.
Your manager will meet you, and IT will give you your laptop and company account.

# Your First Week
During your first week you will complete the mandatory online trainings in the Learning portal:
Information Security Basics, Code of Conduct, and Health and Safety.
All three must be completed within your first 14 days.

# Probation Period
Every new employee has a probation period of three months. Your manager will hold a review
meeting with you at the end of month one and at the end of month three.

# Who to Ask
For questions about salary, contracts or leave, contact HR at hr@nimbus.example.
For laptop, password or software problems, contact the IT helpdesk.
"""

SALARY_POLICY = (
    "Nimbus Systems Compensation and Salary Policy (HR Confidential)",
    [
        ("Salary Reviews", [
            "Salaries are reviewed once per year in March, based on the annual performance rating. "
            "Increases normally range from 0% to 8% of base salary.",
        ]),
        ("Annual Bonus", [
            "Employees rated 'Exceeds Expectations' are eligible for an annual bonus of up to two months' "
            "base salary, paid in April. Employees still in probation are not eligible.",
        ]),
        ("Salary Payment", [
            "Salaries are paid on the 25th of each month. If the 25th falls on a weekend or holiday, "
            "salaries are paid on the last working day before it.",
        ]),
    ],
)


def make_pdf(path: Path, title: str, sections) -> None:
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for i, (heading, paragraphs) in enumerate(sections):
        if i > 0:
            story.append(PageBreak())  # one section per page -> clear page citations
        story.append(Paragraph(heading, styles["Heading2"]))
        for p in paragraphs:
            story.append(Paragraph(p, styles["BodyText"]))
            story.append(Spacer(1, 6))
    SimpleDocTemplate(str(path), pagesize=A4, title=title).build(story)


def make_docx(path: Path, title: str, sections) -> None:
    doc = Document()
    doc.add_heading(title, level=0)
    for heading, paragraphs in sections:
        doc.add_heading(heading, level=1)  # our DOCX loader uses these headings as sections
        for p in paragraphs:
            doc.add_paragraph(p)
    doc.save(str(path))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    make_pdf(OUT / "employee_handbook.pdf", *EMPLOYEE_HANDBOOK)
    make_pdf(OUT / "remote_work_policy.pdf", *REMOTE_WORK_POLICY)
    make_docx(OUT / "it_help_guide.docx", *IT_GUIDE)
    make_docx(OUT / "salary_policy.docx", *SALARY_POLICY)
    (OUT / "expense_policy.txt").write_text(EXPENSE_POLICY, encoding="utf-8")
    (OUT / "onboarding_guide.txt").write_text(ONBOARDING_GUIDE, encoding="utf-8")
    print(f"Sample documents written to {OUT}")


if __name__ == "__main__":
    main()
