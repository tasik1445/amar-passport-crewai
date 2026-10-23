# Amar Passport — Short Submission Video Script (Bangla)

**0:00–0:20:** “আমার project-এর নাম Amar Passport AI Agent। এটি CrewAI-based multi-agent application, যেখানে ৩টি specialized agent আছে: Policy Guardian, Fee Calculator, Document Architect।”

**0:20–0:45:** “প্রত্যেক Agent-এর role, goal এবং backstory আছে। Sequential tasks-এর মাধ্যমে প্রথম Agent-এর eligibility output দ্বিতীয় Agent context হিসেবে পায়; final Agent আগের দুইটি task-এর context ব্যবহার করে।”

**0:45–1:10:** “Fee calculation Python-এর verified rule engine করে। Official published BDT fees-এ ১৫% VAT already included, তাই VAT দুইবার যোগ করা হয় না। Website scrape failure হলে cached SQLite database ব্যবহার হয়।”

**1:10–1:35:** “আমি প্রথমে ২৪ বছর বয়সী private employee-এর example চালাচ্ছি। Requested 64 pages-এর listed fee reference দেখাবে, কিন্তু official suspension notice থাকার কারণে 48-page alternative এবং warning দেখাবে।”

**1:35–1:55:** “এবার ১৫ বছর বয়সী applicant ১০-year passport চাইলে system invalid request flag করে ৫-year/৪৮-page alternative দেখাচ্ছে।”

**1:55–2:10:** “Final report English Markdown table এবং Bangla summary দেয়। `verbose=True` agent execution logs দেখায়। এটি planning assistant, official passport approval system নয়।”
