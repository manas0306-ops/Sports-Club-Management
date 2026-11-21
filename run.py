"""
The Champions Club - Application Runner
Usage:
    python run.py
"""
import uvicorn
import os

if __name__ == "__main__":
    # Ensure database is seeded if not present
    if not os.path.exists("champions_club.db"):
        from seed_data import seed_database
        seed_database()

    print("\n=======================================================")
    print("🏆 The Champions Club - Sports Management System")
    print("   Digital Backbone for Tennis, Cricket, Shop & Bar")
    print("   Web Portal:        http://127.0.0.1:8000")
    print("   Member Hub:        http://127.0.0.1:8000/members")
    print("   Court Schedule:    http://127.0.0.1:8000/courts")
    print("   Pro Gear Shop:     http://127.0.0.1:8000/shop")
    print("   Bar & Café POS:    http://127.0.0.1:8000/bar")
    print("   Kitchen KOT Board: http://127.0.0.1:8000/kitchen")
    print("   CRM & Leads:       http://127.0.0.1:8000/crm")
    print("   Owner Dashboard:   http://127.0.0.1:8000/owner")
    print("   API Documentation: http://127.0.0.1:8000/api/v1/docs")
    print("=======================================================\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app"])
