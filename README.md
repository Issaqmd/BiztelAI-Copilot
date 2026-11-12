BiztelAI Manufacturing AI Copilot

A document-based AI assistant built to help shop-floor supervisors and QC inspectors at Kaveri Precision Components Pvt. Ltd. (Hosur Plant) find information from their plant manuals and SOPs.

The application uses Retrieval-Augmented Generation (RAG) to answer questions based on the provided documents. It is designed to run on a laptop with 8 GB RAM and CPU-only hardware, and can also be accessed from a smartphone or tablet connected to the same local Wi-Fi network.



1. Key Features

- Answers based on plant documents: The Copilot uses the provided Standard Operating Procedures (SOPs) and Preventive Maintenance manuals to answer questions.
- Document revision handling: During PDF processing, the application identifies document revisions and marks older versions as superseded. For example, "QC-SOP-014 Rev 03" (15-Mar-2023) is marked as "SUPERSEDED" when the newer "Rev 04" (01-Jul-2026) is available.
- Role and safety information: Answers include information about who is authorised to perform a particular task, such as the Operator, Maintenance Technician, Shift Supervisor, Production Manager, Safety Officer, or SQE. Relevant Lockout/Tagout ("SAF-SOP-003") warnings are also highlighted.
- Handles questions not covered by the documents: When the manuals do not contain the requested information, the Copilot says so instead of making up an answer.
- Improvements based on the user journey:
  - Quick query buttons: Provides one-tap options such as Machine Alarms, LOTO Safety, QC Inspection, and Maintenance. This makes it easier for supervisors working with gloves or oily hands.
  - Expandable source details: Each source badge ("Doc ID | Revision | Page") can be expanded to show the actual text extracted from the PDF, allowing users to check the answer against the original document.



2. Technology Stack & Architecture

Component| Technology| Purpose
Backend API| FastAPI + Uvicorn| Handles API requests and serves the web interface.
PDF Extraction| PyMuPDF ("pymupdf")| Extracts text and document information from PDF pages.
Vector Search| FAISS ("faiss-cpu") + NumPy| Searches document chunks locally using vector similarity.
Embeddings & LLM| Google Gemini REST API| Uses "gemini-embedding-001" for embeddings and Gemini Flash ("gemini-3.8-flash" / "gemini-3.5-flash") to generate answers based on retrieved content.
Frontend UI| HTML5, CSS3, Vanilla JS| Provides a mobile-responsive interface without requiring additional frontend build tools.

Project Structure

BiztelAI-Copilot/
├── .env.example               # Environment variable template
├── .gitignore                 # Excludes secrets, virtual environments, and cache files
├── requirements.txt           # Python dependencies
├── README.md                  # Setup instructions and test results
├── THINKING.md                # User journey, AI critique, and final reflection
├── ingest.py                  # Extracts PDFs and builds the FAISS index
├── run.py                     # Starts the FastAPI server on 0.0.0.0:8000
├── app/
│   ├── __init__.py
│   ├── config.py              # Environment configuration and file paths
│   ├── pdf_processor.py       # PDF extraction, chunking, and revision handling
│   ├── rag_engine.py          # FAISS search and Gemini API integration
│   └── main.py                # FastAPI routes and static file hosting
├── data/
│   ├── pdfs/                  # Plant manuals and SOP documents
│   └── index/                 # FAISS index and chunk metadata
├── static/
│   └── index.html             # Mobile-responsive chatbot interface
└── tests/
    └── evaluate_questions.py  # Evaluates sample and custom questions

---

3. Local Setup & Installation

Prerequisites

- Python 3.10+ (tested on Python 3.14 on Windows)
- A Google Gemini API key from "Google AI Studio" (https://aistudio.google.com/apikey)

Step 1: Clone the Repository and Create a Virtual Environment

git clone <YOUR_GITHUB_REPO_URL>
cd BiztelAI-Copilot

python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
.\.venv\Scripts\Activate.ps1

Step 2: Install Dependencies

pip install -r requirements.txt

Step 3: Configure Environment Variables

Copy ".env.example" to ".env":

Copy-Item .env.example .env

Open ".env" and add your Gemini API key:

GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
EMBEDDING_MODEL=gemini-embedding-001
HOST=0.0.0.0
PORT=8000

Step 4: Add the Plant PDFs and Build the FAISS Index

Place the four plant PDFs ("MNT-MAN-CNC-02", "QC-SOP-014 Rev 03", "QC-SOP-014 Rev 04", and "SAF-SOP-003") inside "data/pdfs/".

Then run:

python ingest.py

Step 5: Start the Application

python run.py

- On the laptop: Open "http://localhost:8000".
- On a smartphone or tablet connected to the same Wi-Fi:
  1. Run "ipconfig" in PowerShell and find your laptop's IPv4 address (for example, "192.168.31.220").
  2. Open "http://<YOUR_LAPTOP_IP>:8000" in the phone's browser. Use "http://", not "https://".



4. Official Sample Questions (5/5 Verified)

Sample Q1: What is the recommended coolant concentration for the TX-200 CNC turning centre?

Copilot Answer: The recommended coolant concentration for the TX-200 CNC turning centre is 6–8%. The Operator should check it weekly using a refractometer ("reading x 1.0 factor"). If Alarm "AL-412" (Coolant level low) appears, the operator should top up with coolant mixed to the same 6–8% concentration.

Source Cited: "MNT-MAN-CNC-02" (Rev 02, Active), Pages 1 & 2.

Sample Q2: The machine is showing alarm AL-104. What does it mean and what should the operator do?

Copilot Answer: Alarm AL-104 indicates that the way lube oil level is low. The Operator should top up with ISO VG 68 oil to the MAX mark and then press RESET. The machine can continue operating after the reset.

Source Cited: "MNT-MAN-CNC-02" (Rev 02, Active), Page 2.

Sample Q3: Who is allowed to remove a lockout lock from a machine?

Copilot Answer:

1. Normal procedure: Each Authorised Person can remove only their own personal lock. Another person's lock must not be removed by anyone else.
2. If the lock owner is absent: The Shift Supervisor must first try to contact the owner by phone. If the owner cannot be reached, both the Production Manager and Safety Officer must jointly authorise the removal. They must physically inspect the machine, record the removal using form SF-12 Lock Removal Record, and inform the lock owner before their next shift.

Source Cited: "SAF-SOP-003" (Rev 05, Active), Pages 1 & 2.

Sample Q4: What is the outer diameter tolerance for the BH-220 bearing housing?

Copilot Answer: The machined BH-220 bearing housing has an Outer Diameter nominal dimension of 90.000 mm, with a tolerance of +/- 0.050 mm. It should be checked using a calibrated Digital caliper. This is classified as a Major characteristic.

Source Cited: "QC-SOP-014" (Rev 04, Active), Page 2.

Sample Q5: How often should spindle runout be checked, and who does it?

Copilot Answer: Spindle runout at the chuck face must be checked monthly by a Maintenance Technician. The maximum allowed runout is 0.005 mm, measured using a dial indicator. The machine must first be isolated according to "SAF-SOP-003".

Source Cited: "MNT-MAN-CNC-02" (Rev 02, Active), Page 1.

---

5. Five Additional Custom Questions

These questions were added to check how the Copilot handles document revisions, incoming QC procedures, maintenance and safety information, and questions that cannot be answered from the provided manuals.

Custom Q1: Supersession and Revision Conflict Test

Question: We received a lot of 300 pieces of bought-out components. How many random samples should the QC Inspector draw, and which form should be used to record the inspection?

Why I tested this: The older "QC-SOP-014 Rev 03" specifies five samples for all lot sizes and uses paper form "QF-07". This question checks whether the Copilot uses the newer "Rev 04" instead.

Copilot Response:

- Active instruction ("QC-SOP-014 Rev 04"): A lot of 300 pieces falls within the 91–500 range. The QC Inspector must randomly select 13 samples. Accept if there are zero minor defects; reject if there is one or more minor defects, or any critical or major defect. Results must be recorded digitally in the QMS app using form QF-07A.
- Revision warning: The Copilot identifies "QC-SOP-014 Rev 03" as "SUPERSEDED" by "Rev 04", effective 01-Jul-2026. It also identifies paper form "QF-07" as no longer in use.

Source Cited: "QC-SOP-014" (Rev 04, Active), Pages 1 & 2; supersession warning from "QC-SOP-014 Rev 03", Page 1.

Custom Q2: Incoming QC Hold and Quarantine Procedure

Question: What should the QC Inspector do if an incoming lot arrives without a Material Test Certificate (MTC), and where are rejected lots stored?

Copilot Response:

- Missing MTC: According to active procedure "QC-SOP-014 Rev 04", the supplier's Material Test Certificate (MTC) is mandatory. If it is missing, the lot must be placed on HOLD. It must not be inspected or accepted until the MTC is received.
- Rejected material: Rejected material must be given a RED tag and moved to Quarantine Cage Q1, Stores Bay 3. The cage is locked, and the key is held by the Shift QC Supervisor.
- Escalation: The Shift QC Supervisor must inform the Supplier Quality Engineer (SQE) within 4 hours of rejection so that the SQE can raise a SCAR. The older instruction about the "Red Bin area near Gate 2" in Rev 03 is no longer applicable.

Source Cited: "QC-SOP-014" (Rev 04, Active), Page 2.

Custom Q3: Maintenance and Safety Procedure Across Documents

Question: What is the step-by-step procedure and bolt torque for re-mounting the chuck or replacing a hydraulic hose on the TX-200 CNC turning centre?

Copilot Response:

- Chuck mounting bolt torque: Tighten the chuck mounting bolts in a criss-cross sequence to 110 Nm using a calibrated torque wrench.
- Replacing a hydraulic hose:
  1. Isolate the machine according to SAF-SOP-003 (Lockout/Tagout) and release the stored hydraulic pressure.
  2. Check that the panel pressure gauge reads zero before loosening any fitting.
  3. Place a drip tray under the hose and loosen the fittings slowly.
  4. Fit a new hose with the same rating and tighten the fittings.
  5. Remove the locks according to "SAF-SOP-003", start the hydraulic unit, and check that the pressure returns to 3.5–4.0 MPa (35–40 bar) with no leaks.

Source Cited: "MNT-MAN-CNC-02" (Rev 02, Active), Pages 1 & 2; "SAF-SOP-003" (Rev 05, Active), Page 1.

Custom Q4: CMM Critical Inspection Dimensions

Question: Which dimensions of the BH-220 bearing housing are classified as Critical and must be inspected on the CMM?

Copilot Response: According to Section 6 of "QC-SOP-014 Rev 04", the following three characteristics of the machined BH-220 bearing housing are classified as Critical and must be checked using a Coordinate Measuring Machine (CMM):

1. Bore diameter: "52.000 mm" ("+0.030 / -0.000 mm")
2. Mounting hole PCD: "72.00 mm" ("+/- 0.05 mm")
3. Bore concentricity to OD: "0.02 mm max."

If any sample has a critical defect, the complete lot must be rejected and returned to the supplier. Sorting is not allowed.

Source Cited: "QC-SOP-014" (Rev 04, Active), Pages 1 & 2.

Custom Q5: Unanswerable Question

Question: What is the safety torque specification for the hydraulic pump motor mounting bolts on the TX-200?

Why I tested this: The manuals provide a torque value of 110 Nm for the chuck mounting bolts, but do not specify the torque for the hydraulic pump motor mounting bolts. This question checks whether the Copilot can recognise missing information instead of using an unrelated value.

Copilot Response:

«"I cannot find this information in the provided plant manuals or procedures. The provided documentation ("MNT-MAN-CNC-02", Rev 02, Page 1) specifies the torque for the chuck mounting bolts (110 Nm using a calibrated torque wrench), but it does not contain torque specifications for the hydraulic pump motor mounting bolts."»

Source Cited: Grounded refusal ("grounded: false").