# The Champions Club

From PowerShell in the extracted project folder, run:

```powershell
python -m pip install -r requirements.txt
python seed.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Use **Member sign in → Demo credentials** to fill an account. The demo password is **password123**. The seeded bar register is open. Times in the club calendar are India Standard Time. All prices are in INR. Cash, card and UPI record tenders locally. No bank or email service is required.

## Suggested demo

1. Sign in as silver@club.com. Choose tomorrow's tennis court. A ₹600 session costs ₹300. Try the overlapping half-hour start from a separate account. Cancel the first session to release it.
2. Choose Friday at 18:00 or 19:00 to join a free eight-seat social session. Adjacent overlapping private starts are blocked.
3. Order the last Pro Carbon Racket for pickup. Sign in as shop@club.com and find the order in the fulfilment queue. Adjust stock to receive additional units.
4. As bar@club.com open a table, select a member, set quantities and send a ticket. Advance its kitchen stages and settle by payment mode. Close the shift to reconcile collections.
5. As owner@club.com open a receipt, review period totals, print an invoice, and download CSV. Archived accounts retain their history and lose access.

## Configuration

Python 3.10+; no Node build. Database defaults to club.db in the working directory. For PostgreSQL set DATABASE_URL to a postgresql:// connection string before seeding and use the same environment when starting the server. A failed PostgreSQL connection emits a warning and selects the local SQLite file. Data in these two databases remains independent.

The first run generates .club-secret. Keep this file private, or set SESSION_SECRET explicitly. Passwords use bcrypt. Each signed cookie references a revocable nonce stored as a hash with its expiry on the user record. The server checks role, active status and ownership. Local demo users are deliberately seeded with known credentials.

SQLite uses BEGIN IMMEDIATE for write operations. PostgreSQL uses a transaction-scoped advisory lock shared by all app writers. This intentionally serializes club writes for the hackathon workload. Store money in integer paise; discounts and line totals are captured at sale time. A court cancellation posts a negative receipt. Friday social sessions use the booking rows for their capacity count.

## Storage layout

The twelve ORM tables are defined in models.py. Open tabs use unpaid sales, kitchen lines use sale_items with batch and status, order fulfilment uses sale details, and staff schedules use the users.shifts JSON field. The owner revenue view counts settled sales; gross margin subtracts recorded product costs. B2B invoices record one paid service with an explicitly entered tax. Membership purchases generate printable invoices automatically.

## Verification

Run `python verify.py` for the isolated HTTP integration checks. The script creates a temporary SQLite database and leaves the demo data intact. Layout, tables, navigation, and forms have local CSS. Chart.js, Lucide, Tailwind, and the Inter font load over the internet; the finance tables also expose the chart values offline.
