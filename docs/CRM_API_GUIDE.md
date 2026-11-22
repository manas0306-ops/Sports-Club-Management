# CRM Leads Pipeline & Telemetry API Specification

**Author & Module Lead:** Ujjwal Prakash (`ujjwalprakash07`)  
**Component:** Backend APIs, CRM Lead Lifecycle & Telemetry Services  
**Service Layer:** [services.py](file:///c:/Users/Maanas/OneDrive/Desktop/ChampionsClub/services.py) · [main.py](file:///c:/Users/Maanas/OneDrive/Desktop/ChampionsClub/main.py)  

---

## 1. Overview
The Champions Club Prospective Lead Pipeline manages prospective membership inquiries, trial bookings, and real-time proxy connection telemetry across 4,300+ connected users.

All endpoints are protected by Role-Based Access Control (**RBAC**) and restricted to `desk` and `owner` accounts.

---

## 2. API Endpoints

### 2.1 GET `/api/crm/stats`
Returns aggregated real-time telemetry metrics across the entire leads pipeline.

- **Access:** Desk Staff, Club Owner (`403 Forbidden` for members)
- **Response Format (JSON):**
```json
{
  "total_inquiries": 4305,
  "online_now": 77,
  "connected_last_6h": 77,
  "total_bandwidth_gb": 3198.28,
  "top_cities": [
    ["Bengaluru", 434],
    ["Mumbai", 392],
    ["Delhi", 366],
    ["Hyderabad", 250],
    ["Pune", 232]
  ],
  "protocols": {
    "HTTPS": 2580,
    "SOCKS5": 1150,
    "HTTP": 575
  },
  "pipeline_stages": {
    "New": 1280,
    "Contacted": 1420,
    "Quote Sent": 985,
    "Converted": 620
  }
}
```

---

### 2.2 GET `/api/crm/leads`
Queries and filters leads with precision matching and chronological connection ordering.

- **Query Parameters:**
  - `query` *(string)*: Precision search term. Matches User ID (`USR00001`, `00001`, `1`), name, email, phone, city, or proxy IP.
  - `scope` *(string)*: `6h` (default: leads connected in last 6 hours) or `all` (all-time historical database).
  - `status` *(string)*: Filter by `Online` or `Offline`.
  - `limit` *(int, default: 50)*: Number of records to return.
  - `offset` *(int, default: 0)*: Pagination offset.

- **Response Format (JSON):**
```json
{
  "total": 77,
  "offset": 0,
  "limit": 50,
  "leads": [
    {
      "id": 3598,
      "user_code": "USR03593",
      "name": "Ujjwal Kapoor",
      "email": "ujjwal.kapoor@gmail.com",
      "phone": "+91 9876543210",
      "city": "Phagwara",
      "state": "Punjab",
      "proxy_name": "proxy-atq-01",
      "proxy_ip": "10.33.1.220",
      "protocol": "HTTPS",
      "status": "Online",
      "stage": "Contacted",
      "data_used_mb": "293.3",
      "total_connections": 33,
      "lead_score": 85,
      "last_connected": "2026-11-22 09:36:48",
      "time_since": "25m ago"
    }
  ]
}
```

---

### 2.3 POST `/api/lead_stage`
Advances a lead monotonically through the pipeline lifecycle stages.

- **Payload:**
```json
{
  "id": 1,
  "stage": "Contacted"
}
```
- **Lifecycle Transition Rules:**
  $$\text{New} \longrightarrow \text{Contacted} \longrightarrow \text{Quote Sent} \longrightarrow \text{Converted}$$
- **Validation:** Attempting to skip stages or demote an advanced lead returns `422 Unprocessable Entity`.

---

## 3. Lead Scoring Algorithm
The lead score ($S \in [10, 100]$) is computed by `compute_lead_score(lead)`:

$$S = \min\Big(100, 10 + 40 \cdot \mathbb{I}_{\text{Online}} + \min(30, 2 \cdot C) + \min\Big(20, \Big\lfloor \frac{M}{100} \Big\rfloor\Big) + 25 \cdot \mathbb{I}_{\text{Trial}}\Big)$$

Where:
- $\mathbb{I}_{\text{Online}} = 1$ if `status == "Online"`, else $0$
- $C$: `total_connections`
- $M$: `data_used_mb`
- $\mathbb{I}_{\text{Trial}} = 1$ if complimentary court trial was requested
