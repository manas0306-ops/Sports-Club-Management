"""
Seed Data Integrity & Format Validation Utility.
Authored by: Vedant Kumar (27vedantkumar) - Data & Inventory Operations
"""
import csv
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def validate_products_csv():
    path = os.path.join(DATA_DIR, "products.csv")
    print(f"Validating products dataset at: {path}")
    assert os.path.exists(path), f"File missing: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) >= 400, f"Expected 400+ rows, got {len(rows)}"
    required_cols = {"name", "category", "price", "wholesale_price", "quantity"}
    assert required_cols.issubset(set(rows[0].keys())), f"Missing headers in products.csv"

    for idx, r in enumerate(rows):
        assert r["name"].strip(), f"Row {idx}: Name is empty"
        assert r["category"].strip(), f"Row {idx}: Category is empty"
        assert float(r["price"]) > 0, f"Row {idx}: Price must be positive"
        assert float(r["wholesale_price"]) > 0, f"Row {idx}: Wholesale price must be positive"
        assert int(r["quantity"]) >= 0, f"Row {idx}: Quantity must be non-negative"

    print(f"✓ Products CSV verified: {len(rows)} valid products across categories.")

def validate_crm_users_csv():
    path = os.path.join(DATA_DIR, "crm_connected_users.csv")
    print(f"Validating CRM users dataset at: {path}")
    assert os.path.exists(path), f"File missing: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 4300, f"Expected 4,300 rows, got {len(rows)}"
    required_cols = {
        "user_id", "name", "email", "phone", "city", "state", 
        "proxy_name", "proxy_ip", "protocol", "status", 
        "last_connected", "total_connections", "data_used_mb"
    }
    assert required_cols.issubset(set(rows[0].keys())), f"Missing headers in crm_connected_users.csv"

    for idx, r in enumerate(rows):
        assert r["user_id"].startswith("USR"), f"Row {idx}: Invalid User ID format {r['user_id']}"
        assert "@" in r["email"], f"Row {idx}: Invalid email {r['email']}"
        assert r["status"] in {"Online", "Offline"}, f"Row {idx}: Invalid status {r['status']}"
        datetime.strptime(r["last_connected"], "%Y-%m-%d %H:%M:%S")

    print(f"✓ CRM Connected Users CSV verified: {len(rows)} valid users.")

def main():
    print("=" * 65)
    print("  THE CHAMPIONS CLUB - SEED DATA VERIFICATION SUITE")
    print("=" * 65)
    validate_products_csv()
    validate_crm_users_csv()
    print("=" * 65)
    print("✓ All data assets passed schema validation.\n")

if __name__ == "__main__":
    main()
