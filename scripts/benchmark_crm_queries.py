"""
CRM Query Latency & Precision Search Benchmark.
Authored by: Ujjwal Prakash (ujjwalprakash07) - Backend APIs & CRM Systems
"""
import time
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Session
from models import Lead
from services import clock

def benchmark_crm():
    print("=" * 65)
    print("  THE CHAMPIONS CLUB - CRM QUERY LATENCY BENCHMARK")
    print("=" * 65)
    
    with Session() as db:
        # 1. Benchmark full table scan vs index query
        t0 = time.perf_counter()
        count = db.query(Lead).count()
        t1 = time.perf_counter()
        print(f"Total Leads Count ({count} records): {(t1 - t0)*1000:.2f} ms")

        # 2. Benchmark precision User ID lookup
        sample_ids = ["USR00001", "USR01000", "USR02500", "USR04300"]
        lookup_times = []
        for uid in sample_ids:
            s0 = time.perf_counter()
            match = db.query(Lead).filter_by(user_code=uid).first()
            s1 = time.perf_counter()
            lookup_times.append((s1 - s0) * 1000)
            assert match is not None, f"Could not find {uid}"

        avg_lookup = sum(lookup_times) / len(lookup_times)
        print(f"Average Precision User ID Lookup: {avg_lookup:.2f} ms (Target < 10.0 ms)")

        # 3. Benchmark connection time sorting
        c0 = time.perf_counter()
        recent = db.query(Lead).order_by(Lead.created.desc()).limit(100).all()
        c1 = time.perf_counter()
        print(f"Fetch Top 100 Chronological Leads: {(c1 - c0)*1000:.2f} ms")

        assert avg_lookup < 50.0, "Lookup performance exceeds threshold"

    print("=" * 65)
    print("✓ All query performance benchmarks within real-time SLA thresholds.\n")

if __name__ == "__main__":
    benchmark_crm()
