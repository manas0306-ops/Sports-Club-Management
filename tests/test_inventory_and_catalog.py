"""
Catalog and Inventory Unit Tests.
Authored by: Vedant Kumar (27vedantkumar) - Data & Inventory Operations
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session
from models import Product
from services import inventory_health

def test_inventory_and_catalog():
    print("--- Testing Sports Gear Catalog & Stock Integrity ---")
    with Session() as db:
        prods = db.query(Product).filter_by(department="Shop").all()
        assert len(prods) >= 400, f"Expected at least 400 products, found {len(prods)}"
        
        categories = set(p.category for p in prods)
        expected_categories = {
            'Cricket', 'Tennis', 'Padel', 'Badminton', 'Football', 
            'Basketball', 'Volleyball', 'Table Tennis', 'Squash', 'Hockey', 
            'Swimming', 'Athletics', 'Gym & Fitness', 'Boxing & MMA', 
            'Cycling', 'Yoga & Recovery', 'Apparel & Kits', 'Footwear', 'Accessories'
        }
        for ec in expected_categories:
            assert ec in categories, f"Missing expected category: {ec}"
        print(f"✓ All {len(categories)} sports categories verified in catalog.")

        # Price and stock sanity checks
        for p in prods:
            assert p.price > 0, f"Product {p.id} has invalid price: {p.price}"
            assert p.cost > 0, f"Product {p.id} has invalid cost: {p.cost}"
            assert p.stock_on_hand >= 0, f"Product {p.id} has negative stock: {p.stock_on_hand}"
        print("✓ All product prices, wholesale costs, and stock levels are valid.")

        health = inventory_health(db, dept="Shop")
        assert health["total_products"] == len(prods)
        assert health["total_valuation"] > health["total_cost"]
        assert health["out_of_stock_count"] == 0
        print(f"✓ Inventory health check passed: ₹{health['total_valuation']/100:,.2f} valuation.")

    print("PASS: Catalog and Inventory unit tests passed successfully.\n")

if __name__ == "__main__":
    test_inventory_and_catalog()
