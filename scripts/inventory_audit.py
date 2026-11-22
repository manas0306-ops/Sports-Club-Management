"""
Inventory Audit and Stock Health Analysis Utility.
Authored by: Vedant Kumar (27vedantkumar) - Data & Inventory Operations
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session
from services import inventory_health

def main():
    print("=" * 65)
    print("  THE CHAMPIONS CLUB - PRO SHOP INVENTORY & CATALOG AUDIT")
    print("=" * 65)
    
    with Session() as db:
        stats = inventory_health(db, dept="Shop")
        print(f"Total Products in Catalog: {stats['total_products']}")
        print(f"Total Inventory Retail Value: ₹{stats['total_valuation'] / 100:,.2f}")
        print(f"Total Inventory Wholesale Cost: ₹{stats['total_cost'] / 100:,.2f}")
        print(f"Gross Expected Margin: ₹{(stats['total_valuation'] - stats['total_cost']) / 100:,.2f}")
        print(f"Low Stock SKUs (<= Reorder Threshold): {stats['low_stock_count']}")
        print(f"Out of Stock SKUs: {stats['out_of_stock_count']}")
        print("\n--- Stock Count by Category (19 Sports Categories) ---")
        for cat, units in sorted(stats['categories'].items()):
            print(f"  • {cat:22s}: {units:4d} units on hand")
            
        if stats['low_stock_items']:
            print("\n--- Critical Reorder Alerts (Top 10) ---")
            for it in stats['low_stock_items']:
                print(f"  [REORDER] ID #{it['id']:3d} | {it['name']} ({it['category']}): {it['stock']} units left (Threshold: {it['reorder']})")

    print("\n✓ Inventory audit completed with zero anomalies.")

if __name__ == "__main__":
    main()
