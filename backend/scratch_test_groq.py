import asyncio
from app.ai.nodes.log_complaint import log_complaint_node
from app.ai.nodes.document_extraction import document_extract_node
from app.ai.nodes.edit_complaint import edit_complaint_node

async def main():
    print("--- TESTING LOG COMPLAINT ---")
    log_state = {
        "messages": [{"role": "user", "content": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. Batch AMX240602, 12 capsules, manufacturing March 2026, expiry February 2028."}]
    }
    log_res = await log_complaint_node(log_state)
    print("LOG RESULT:", log_res)

    print("\n--- TESTING DOCUMENT EXTRACTION ---")
    doc_state = {
        "document_text": "Zeno health reported discolored capsules in Crocine tablet 500 mg. Batch CRX240602, 20 tablets, manufacturing March 2026, expiry February 2027.",
        "document_metadata": {"file_name": "Zeno health reported discolored cap.txt"}
    }
    doc_res = await document_extract_node(doc_state)
    print("DOC RESULT:", doc_res)

    print("\n--- TESTING EDIT COMPLAINT ---")
    edit_state = {
        "current_complaint": log_res["current_complaint"],
        "messages": [{"role": "user", "content": "Change batch to BMX240602 and quantity to 48 capsules"}]
    }
    edit_res = await edit_complaint_node(edit_state)
    print("EDIT RESULT:", edit_res)

if __name__ == "__main__":
    asyncio.run(main())
