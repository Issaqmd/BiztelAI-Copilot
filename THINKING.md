THINKING & PRODUCT DESIGN LOG — BiztelAI Manufacturing AI Copilot

1. Initial User Journey (First Draft — Written Before AI Critique)

Who is the User & Daily Shift Environment

The main user is a Shift Supervisor or QC Supervisor working at Kaveri Precision Components Pvt. Ltd., Hosur Plant. During a normal shift, they monitor CNC machines, check production activities, handle safety-related issues, and supervise incoming material inspections.

They usually move around the factory floor, where machines are running continuously. When a problem occurs, they may need to use a smartphone or tablet to find the correct information quickly.

Common Shop-Floor Problems

One of the common difficulties is finding the right information at the right time. For example, if a CNC machine suddenly stops and displays an alarm, the supervisor needs to understand what the alarm means and what action should be taken.

Similarly, during maintenance, they need to follow the correct safety procedures. During quality inspections, different versions of SOP documents can also create confusion about which procedure is currently valid.

Searching through paper documents or going through lengthy PDFs on a mobile screen can take too much time, especially during a busy shift.

Moments Where the Supervisor Uses the Copilot

Imagine a CNC machine displays an AL-101 alarm during a busy shift. The supervisor opens the Manufacturing AI Copilot on their phone and asks what the alarm means and what the operator should do next.

In another situation, while checking incoming materials, the supervisor can ask about the latest sampling rules or the required MTC documents.

The Copilot should provide a clear answer with simple steps and references to the original SOP, including the document name, revision number, and page number.

What Builds Trust

I would trust the Copilot if its answers were accurate, easy to understand, and supported by the actual factory documents.

It should also clearly say when information is missing or uncertain instead of guessing. This would help supervisors find information faster without spending too much time searching through multiple documents.

---

2. Skeptical AI Challenge & Critique

After writing my first user journey, I used AI to review it from the perspective of a skeptical plant manager. The following were the main points raised:

1. Physical Shop-Floor Friction (Typing with Gloves / Oily Hands)
   
   Critique: It may not be realistic to expect a supervisor to type full questions on a mobile keyboard while standing near a noisy CNC lathe. Their hands may have coolant, lube oil, or safety gloves on them.

2. The Silent Revision Trap ("QC-SOP-014 Rev 03" vs "Rev 04")
   
   Critique: Normal vector search finds text based on similarity, but it does not automatically understand which document revision is newer.
   
   Since the documents contain both "QC-SOP-014 Rev 03" (2023) and "QC-SOP-014 Rev 04" (2026), which replaces the older version, a basic RAG system could retrieve outdated sampling instructions or old paper forms ("QF-07") instead of the latest digital form ("QF-07A").

3. Role Authorization & Escalation Boundaries
   
   Critique: In a manufacturing environment, knowing what action to take is not enough. The user also needs to know who is authorised to perform it.
   
   For example, responsibilities may differ between an Operator, Maintenance Technician, Shift Supervisor, Production Manager, and Safety Officer. This is especially important when removing a LOTO lock if its owner is absent.

4. Cross-Document Safety Dependencies
   
   Critique: Some maintenance procedures, such as replacing a hydraulic hose in "MNT-MAN-CNC-02", depend on the Lockout/Tagout procedure in "SAF-SOP-003".
   
   If the system retrieves information from only one document, it may miss important safety steps, including zero-energy verification.

5. Filename Citations Alone Are Not Enough on Mobile
   
   Critique: A supervisor checking a critical tolerance or bolt torque on a phone may not trust a filename alone. They should be able to see the exact text extracted from the PDF without having to download and search through the entire document.

---

3. My Reflection on the Critique & Resulting Design Changes

The AI critique helped me notice a few problems that I had missed while writing my first user journey.

One thing I had not considered was that the system could retrieve an older SOP ("Rev 03") instead of the latest one ("Rev 04"), even when both documents contain similar information. I also had not thought much about how difficult it could be to type on a phone while wearing gloves or working in a noisy factory.

Based on this feedback, I made the following design improvements:

1. One-Tap Quick Query Chips: Added category buttons for common queries such as Machine Alarms, LOTO Safety, QC Inspection, and Maintenance. This reduces the need to type full questions on mobile devices.

2. Automated Document Revision & Supersession Tracking: Added document ID and revision number extraction during PDF processing. Older procedures such as "QC-SOP-014 Rev 03" are identified and marked as "SUPERSEDED".

3. Structured Role, Safety & Verbatim Source Display: Answers are organised to highlight authorised roles and relevant safety warnings. Users can also expand the source details to view the extracted text from the original PDF page.

---

4. Post-Build Engineering Reflection

A. Biggest Technical & Product Challenges Faced and How I Solved Them

1. The Silent Document Supersession Problem ("QC-SOP-014 Rev 03" vs "Rev 04")

Challenge:

The document folder contained both the 2023 revision ("Rev 03") and the July 2026 revision ("Rev 04") of the Incoming Material Inspection SOP "QC-SOP-014".

Normal vector similarity search can retrieve chunks from both versions. This could result in someone following an outdated procedure, such as inspecting only 5 samples instead of 13–50, using the old paper form "QF-07" instead of the digital form "QF-07A", or storing rejected parts near Gate 2 instead of using the locked Quarantine Cage Q1.

Solution:

I implemented a two-pass metadata parser in "app/pdf_processor.py".

It extracts the Document ID, Revision number, and Effective Date from each PDF. During ingestion, the application compares revision numbers for documents with matching IDs and marks older versions as "SUPERSEDED".

This status is included in the document chunks, and the Gemini system prompt instructs the model to warn the supervisor when superseded content is encountered.

2. Environment & Network Constraints on Windows + Python 3.14

Challenge:

While building the application on Windows with Python 3.14, I faced a few environment-related issues:

1. Windows Application Control blocked compiled ".pyd" DLL files inside ".venv", including "_pydantic_core".
2. Newly created Google AI Studio keys no longer worked with "gemini-2.5-flash", so I had to move to "gemini-3.8-flash" / "gemini-3.5-flash".
3. Python 3.14's "ssl.py" / "httpx" socket layer in the "google-genai" SDK experienced read timeouts on longer connections. I also initially had trouble accessing the laptop server from my phone because I used "localhost" or "https://" instead of "http://<LAN_IP>:8000".

Solution:

I addressed these issues by:

- Using PowerShell's "Unblock-File" across ".venv" to resolve the Windows policy issue.
- Checking the available Gemini API models and switching to Gemini 3.x Flash.
- Updating "app/rag_engine.py" to use direct "urllib.request" REST calls with explicit 15-second timeouts and model fallback ("gemini-3.8-flash" to "gemini-3.5-flash").
- Configuring Uvicorn to run on "0.0.0.0:8000" so the application could be accessed from a phone over local Wi-Fi using "http://192.168.31.220:8000".

---

B. What I Would Build Next (With More Time)

1. Hard Filter Toggle for Superseded Documents
   
   I would add a UI option called "Active SOPs Only" and "Include Audit Archive". By default, the system would search only active documents. Older revisions would be available when a supervisor needs to check historical changes during an audit.

2. Voice-to-Text & Regional Language Support (Tamil + English)
   
   Since the plant is in Hosur, Tamil Nadu, operators and supervisors may use a mix of Tamil and technical English. Adding browser Web Speech API voice input and bilingual Tamil/English audio explanations could make the application easier to use on the shop floor.

3. Direct PDF Page Viewer Modal
   
   I would add a feature that highlights the exact text location on the rendered PDF page when a supervisor taps a source badge.

4. Offline Local Fallback
   
   I would explore caching frequently used questions and answers in browser "localStorage" or IndexedDB. This could help users access common alarm codes ("AL-101" to "AL-412") and LOTO information in areas with poor Wi-Fi coverage.

---

C. What I Am Still Unsure About

1. Complex Multi-Page Engineering Drawings & Tables

The four PDFs used in this project contained text-based tables that PyMuPDF could extract reliably.

However, if the plant starts using scanned blueprints, CAD drawings with geometric symbols (GD&T), or multi-page wiring diagrams, normal text extraction and chunking may not preserve the original table layout or spatial information. These documents may require multimodal vision-language extraction.

2. Concurrent Shop-Floor Load vs. Free API Rate Limits

The Google AI Studio free tier works for individual supervisor queries during testing. However, if 30 supervisors across three shifts use the system at the same time during an audit, API rate limits could become an issue. Request queuing and semantic caching would need to be considered.

---

D. Questions I Would Ask the Factory Customer (Kaveri Precision Components)

1. "Why is "QC-SOP-014 Rev 03" still stored in the shared folder along with "Rev 04"? Should older revisions be completely hidden from floor operators, or should they remain available only to QC Managers during ISO audits?"

2. "Is there already a digital QMS app, as mentioned in "QC-SOP-014 Rev 04" for form "QF-07A", that we could integrate with? This could help the Copilot stay updated whenever a new SOP revision is approved."

3. "How reliable is the Wi-Fi around the TX-200 CNC shaft machining line and Quarantine Cage Q1? Also, do supervisors normally use shared rugged tablets or their personal Android phones?" 