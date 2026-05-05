# SQL Learning Plan

A progressive SQL curriculum using the procurement dataset (29 tables, 10K+ rows, graph views).

## Prerequisites

- Access to HANA Cloud instance with PROCUREMENT schema
- Basic understanding of what databases are
- Familiarity with the procurement domain (vendors, materials, purchase orders)

## Dataset Overview

| Domain | Tables | Purpose |
|--------|--------|---------|
| **Organization** | `company_code`, `purchasing_org`, `plant`, `cost_center` | Company structure |
| **Master Data** | `vendor_master`, `material_master`, `category_hierarchy` | Core entities |
| **Sourcing** | `source_list`, `contract_header`, `contract_item` | Vendor-material relationships |
| **Transactions** | `po_header`, `po_line_item`, `pr_header`, `pr_line_item` | Purchase documents |
| **Fulfillment** | `gr_header`, `gr_line_item`, `invoice_header`, `invoice_line_item` | Receipts and invoices |
| **Payments** | `payment`, `payment_invoice_link` | Financial settlements |
| **Graph Views** | `V_*` (10 views), `E_*` (14 views) | Knowledge graph representation |

---

## Module 1: SQL Foundations (Days 1-3)

### 1.1 SELECT Basics

**Concepts:** SELECT, FROM, column selection, LIMIT

```sql
-- Retrieve all columns from vendor_master
SELECT * FROM "PROCUREMENT"."vendor_master" LIMIT 10;

-- Select specific columns
SELECT "VENDOR_ID", "VENDOR_NAME", "COUNTRY" 
FROM "PROCUREMENT"."vendor_master" 
LIMIT 10;

-- Column aliases
SELECT 
    "VENDOR_ID" AS vendor_code,
    "VENDOR_NAME" AS name,
    "RISK_SCORE" AS risk
FROM "PROCUREMENT"."vendor_master"
LIMIT 5;
```

**Practice:**
1. List all materials with their descriptions
2. Show plant IDs and names
3. Display purchase order headers with PO date and total value

---

### 1.2 Filtering with WHERE

**Concepts:** WHERE, comparison operators, AND/OR, NULL handling

```sql
-- Filter by country
SELECT * FROM "PROCUREMENT"."vendor_master"
WHERE "COUNTRY" = 'JP';

-- Multiple conditions with AND
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
WHERE "COUNTRY" = 'JP' AND "STATUS" = 'ACTIVE';

-- OR conditions
SELECT * FROM "PROCUREMENT"."vendor_master"
WHERE "COUNTRY" = 'JP' OR "COUNTRY" = 'CN';

-- Numeric comparisons
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
WHERE "RISK_SCORE" >= 70;

-- NULL handling
SELECT * FROM "PROCUREMENT"."category_hierarchy"
WHERE "PARENT_CATEGORY_ID" IS NULL;  -- Top-level categories

-- NOT NULL
SELECT * FROM "PROCUREMENT"."category_hierarchy"
WHERE "PARENT_CATEGORY_ID" IS NOT NULL;  -- Child categories
```

**Practice:**
1. Find all vendors with quality score above 85
2. List materials with criticality = 'HIGH'
3. Show invoices with match_status = 'PRICE_VARIANCE'
4. Find purchase orders that are maverick (maverick_flag = 1)

---

### 1.3 Pattern Matching

**Concepts:** LIKE, wildcards (%, _), IN, BETWEEN

```sql
-- LIKE with % wildcard (any characters)
SELECT * FROM "PROCUREMENT"."material_master"
WHERE "DESCRIPTION" LIKE '%LiDAR%';

-- LIKE with _ wildcard (single character)
SELECT * FROM "PROCUREMENT"."plant"
WHERE "PLANT_ID" LIKE 'SG__';  -- SG01, SG02, etc.

-- IN for multiple values
SELECT * FROM "PROCUREMENT"."vendor_master"
WHERE "COUNTRY" IN ('JP', 'CN', 'KR', 'TW');

-- BETWEEN for ranges
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
WHERE "RISK_SCORE" BETWEEN 50 AND 70;

-- Date ranges
SELECT * FROM "PROCUREMENT"."po_header"
WHERE "PO_DATE" BETWEEN '2024-01-01' AND '2024-06-30';
```

**Practice:**
1. Find materials with 'Sensor' in description
2. List vendors from APAC countries (JP, CN, KR, TW, SG, MY, VN)
3. Show invoices with amounts between 10,000 and 50,000
4. Find categories at level 2 or 3

---

### 1.4 Sorting and Limiting

**Concepts:** ORDER BY, ASC/DESC, LIMIT, OFFSET

```sql
-- Sort ascending (default)
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
ORDER BY "RISK_SCORE";

-- Sort descending
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
ORDER BY "RISK_SCORE" DESC;

-- Multiple sort columns
SELECT "VENDOR_ID", "COUNTRY", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
ORDER BY "COUNTRY" ASC, "RISK_SCORE" DESC;

-- Top N results
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
ORDER BY "RISK_SCORE" DESC
LIMIT 10;

-- Pagination with OFFSET
SELECT "VENDOR_ID", "VENDOR_NAME"
FROM "PROCUREMENT"."vendor_master"
ORDER BY "VENDOR_ID"
LIMIT 10 OFFSET 20;  -- Skip first 20, return next 10
```

**Practice:**
1. List top 5 vendors by quality score
2. Show 10 most recent purchase orders
3. Find the 3 most expensive invoices
4. List materials sorted by category, then by description

---

## Module 2: Aggregations (Days 4-6)

### 2.1 Basic Aggregates

**Concepts:** COUNT, SUM, AVG, MIN, MAX

```sql
-- Count all vendors
SELECT COUNT(*) AS vendor_count
FROM "PROCUREMENT"."vendor_master";

-- Count with condition
SELECT COUNT(*) AS high_risk_vendors
FROM "PROCUREMENT"."vendor_master"
WHERE "RISK_SCORE" >= 70;

-- Sum of PO values
SELECT SUM("TOTAL_NET_VALUE") AS total_po_value
FROM "PROCUREMENT"."po_header";

-- Average, Min, Max
SELECT 
    AVG("RISK_SCORE") AS avg_risk,
    MIN("RISK_SCORE") AS min_risk,
    MAX("RISK_SCORE") AS max_risk
FROM "PROCUREMENT"."vendor_master";

-- Count distinct
SELECT COUNT(DISTINCT "COUNTRY") AS country_count
FROM "PROCUREMENT"."vendor_master";
```

**Practice:**
1. Count total number of purchase orders
2. Calculate total invoice amount
3. Find average lead time across all vendors
4. Count distinct categories in material_master

---

### 2.2 GROUP BY

**Concepts:** GROUP BY, aggregates with grouping

```sql
-- Vendors per country
SELECT "COUNTRY", COUNT(*) AS vendor_count
FROM "PROCUREMENT"."vendor_master"
GROUP BY "COUNTRY";

-- Total PO value by vendor
SELECT 
    "VENDOR_ID",
    COUNT(*) AS po_count,
    SUM("TOTAL_NET_VALUE") AS total_spend
FROM "PROCUREMENT"."po_header"
GROUP BY "VENDOR_ID";

-- Average risk score by country
SELECT 
    "COUNTRY",
    COUNT(*) AS vendor_count,
    AVG("RISK_SCORE") AS avg_risk,
    AVG("QUALITY_SCORE") AS avg_quality
FROM "PROCUREMENT"."vendor_master"
GROUP BY "COUNTRY"
ORDER BY avg_risk DESC;

-- Multiple grouping columns
SELECT 
    "COUNTRY",
    "VENDOR_TYPE",
    COUNT(*) AS count
FROM "PROCUREMENT"."vendor_master"
GROUP BY "COUNTRY", "VENDOR_TYPE"
ORDER BY "COUNTRY", "VENDOR_TYPE";
```

**Practice:**
1. Count materials per category
2. Total invoice amount by vendor
3. Number of PO line items per PO
4. Average unit price by material

---

### 2.3 HAVING

**Concepts:** HAVING (filtering after aggregation)

```sql
-- Countries with more than 5 vendors
SELECT "COUNTRY", COUNT(*) AS vendor_count
FROM "PROCUREMENT"."vendor_master"
GROUP BY "COUNTRY"
HAVING COUNT(*) > 5;

-- Vendors with total spend over 100,000
SELECT 
    "VENDOR_ID",
    SUM("TOTAL_NET_VALUE") AS total_spend
FROM "PROCUREMENT"."po_header"
GROUP BY "VENDOR_ID"
HAVING SUM("TOTAL_NET_VALUE") > 100000
ORDER BY total_spend DESC;

-- Categories with average material cost over 500
SELECT 
    "CATEGORY_ID",
    COUNT(*) AS material_count,
    AVG("STANDARD_COST") AS avg_cost
FROM "PROCUREMENT"."material_master"
GROUP BY "CATEGORY_ID"
HAVING AVG("STANDARD_COST") > 500;
```

**Practice:**
1. Find vendors with more than 3 purchase orders
2. List categories with more than 10 materials
3. Show plants with total PO value exceeding 500,000
4. Find invoices grouped by status where count > 20

---

## Module 3: JOINs (Days 7-10)

### 3.1 INNER JOIN

**Concepts:** Combining tables on matching keys

```sql
-- PO headers with vendor names
SELECT 
    p."PO_ID",
    p."PO_DATE",
    p."TOTAL_NET_VALUE",
    v."VENDOR_NAME",
    v."COUNTRY"
FROM "PROCUREMENT"."po_header" p
INNER JOIN "PROCUREMENT"."vendor_master" v 
    ON p."VENDOR_ID" = v."VENDOR_ID";

-- Materials with their categories
SELECT 
    m."MATERIAL_ID",
    m."DESCRIPTION",
    c."CATEGORY_NAME",
    c."LEVEL"
FROM "PROCUREMENT"."material_master" m
INNER JOIN "PROCUREMENT"."category_hierarchy" c 
    ON m."CATEGORY_ID" = c."CATEGORY_ID";

-- PO line items with material details
SELECT 
    li."PO_ID",
    li."PO_LINE_NUMBER",
    li."QUANTITY",
    li."UNIT_PRICE",
    m."DESCRIPTION" AS material_name
FROM "PROCUREMENT"."po_line_item" li
INNER JOIN "PROCUREMENT"."material_master" m 
    ON li."MATERIAL_ID" = m."MATERIAL_ID";
```

**Practice:**
1. Join invoices with vendor names
2. Join goods receipts with PO details
3. Join contract items with material descriptions
4. Join payments with vendor information

---

### 3.2 LEFT JOIN

**Concepts:** Include all rows from left table, even without matches

```sql
-- All vendors, with their PO counts (including vendors with 0 POs)
SELECT 
    v."VENDOR_ID",
    v."VENDOR_NAME",
    COUNT(p."PO_ID") AS po_count
FROM "PROCUREMENT"."vendor_master" v
LEFT JOIN "PROCUREMENT"."po_header" p 
    ON v."VENDOR_ID" = p."VENDOR_ID"
GROUP BY v."VENDOR_ID", v."VENDOR_NAME";

-- Categories with material counts (including empty categories)
SELECT 
    c."CATEGORY_ID",
    c."CATEGORY_NAME",
    COUNT(m."MATERIAL_ID") AS material_count
FROM "PROCUREMENT"."category_hierarchy" c
LEFT JOIN "PROCUREMENT"."material_master" m 
    ON c."CATEGORY_ID" = m."CATEGORY_ID"
GROUP BY c."CATEGORY_ID", c."CATEGORY_NAME";

-- Find vendors with no contracts
SELECT v."VENDOR_ID", v."VENDOR_NAME"
FROM "PROCUREMENT"."vendor_master" v
LEFT JOIN "PROCUREMENT"."contract_header" ch 
    ON v."VENDOR_ID" = ch."VENDOR_ID"
WHERE ch."CONTRACT_ID" IS NULL;
```

**Practice:**
1. List all materials, showing which have been ordered (via po_line_item)
2. Find plants with no purchase orders
3. Show all invoices with their payments (some may be unpaid)
4. List vendors with their contract counts

---

### 3.3 Multi-Table JOINs

**Concepts:** Joining 3+ tables

```sql
-- PO with vendor and plant details
SELECT 
    p."PO_ID",
    p."PO_DATE",
    v."VENDOR_NAME",
    pl."PLANT_NAME",
    p."TOTAL_NET_VALUE"
FROM "PROCUREMENT"."po_header" p
INNER JOIN "PROCUREMENT"."vendor_master" v 
    ON p."VENDOR_ID" = v."VENDOR_ID"
INNER JOIN "PROCUREMENT"."plant" pl 
    ON p."PLANT_ID" = pl."PLANT_ID";

-- Source list with vendor and material details
SELECT 
    sl."VENDOR_ID",
    v."VENDOR_NAME",
    sl."MATERIAL_ID",
    m."DESCRIPTION" AS material_name,
    sl."PLANT_ID",
    sl."PREFERRED_RANK"
FROM "PROCUREMENT"."source_list" sl
INNER JOIN "PROCUREMENT"."vendor_master" v 
    ON sl."VENDOR_ID" = v."VENDOR_ID"
INNER JOIN "PROCUREMENT"."material_master" m 
    ON sl."MATERIAL_ID" = m."MATERIAL_ID";

-- Full category path (category → parent → grandparent)
SELECT 
    c1."CATEGORY_ID",
    c1."CATEGORY_NAME" AS category,
    c2."CATEGORY_NAME" AS parent,
    c3."CATEGORY_NAME" AS grandparent
FROM "PROCUREMENT"."category_hierarchy" c1
LEFT JOIN "PROCUREMENT"."category_hierarchy" c2 
    ON c1."PARENT_CATEGORY_ID" = c2."CATEGORY_ID"
LEFT JOIN "PROCUREMENT"."category_hierarchy" c3 
    ON c2."PARENT_CATEGORY_ID" = c3."CATEGORY_ID"
WHERE c1."LEVEL" = 3;
```

**Practice:**
1. Join PO line items with PO header, vendor, and material
2. Show invoice details with vendor and related PO
3. Display contract items with vendor and material information
4. List goods receipt lines with PO, vendor, and material

---

### 3.4 Self JOINs

**Concepts:** Joining a table to itself

```sql
-- Category hierarchy (parent-child relationships)
SELECT 
    child."CATEGORY_ID" AS child_id,
    child."CATEGORY_NAME" AS child_name,
    parent."CATEGORY_ID" AS parent_id,
    parent."CATEGORY_NAME" AS parent_name
FROM "PROCUREMENT"."category_hierarchy" child
INNER JOIN "PROCUREMENT"."category_hierarchy" parent
    ON child."PARENT_CATEGORY_ID" = parent."CATEGORY_ID";

-- Find vendors in the same country
SELECT 
    v1."VENDOR_ID" AS vendor1,
    v2."VENDOR_ID" AS vendor2,
    v1."COUNTRY"
FROM "PROCUREMENT"."vendor_master" v1
INNER JOIN "PROCUREMENT"."vendor_master" v2
    ON v1."COUNTRY" = v2."COUNTRY"
    AND v1."VENDOR_ID" < v2."VENDOR_ID"  -- Avoid duplicates
LIMIT 20;
```

---

## Module 4: Subqueries (Days 11-13)

### 4.1 Scalar Subqueries

**Concepts:** Subquery returning single value

```sql
-- Vendors with above-average risk score
SELECT "VENDOR_ID", "VENDOR_NAME", "RISK_SCORE"
FROM "PROCUREMENT"."vendor_master"
WHERE "RISK_SCORE" > (
    SELECT AVG("RISK_SCORE") FROM "PROCUREMENT"."vendor_master"
);

-- POs with value above average
SELECT "PO_ID", "VENDOR_ID", "TOTAL_NET_VALUE"
FROM "PROCUREMENT"."po_header"
WHERE "TOTAL_NET_VALUE" > (
    SELECT AVG("TOTAL_NET_VALUE") FROM "PROCUREMENT"."po_header"
);
```

---

### 4.2 IN Subqueries

**Concepts:** Subquery returning a list

```sql
-- Vendors who have contracts
SELECT "VENDOR_ID", "VENDOR_NAME"
FROM "PROCUREMENT"."vendor_master"
WHERE "VENDOR_ID" IN (
    SELECT DISTINCT "VENDOR_ID" FROM "PROCUREMENT"."contract_header"
);

-- Materials that have been ordered
SELECT "MATERIAL_ID", "DESCRIPTION"
FROM "PROCUREMENT"."material_master"
WHERE "MATERIAL_ID" IN (
    SELECT DISTINCT "MATERIAL_ID" FROM "PROCUREMENT"."po_line_item"
);

-- Vendors who have NOT been paid
SELECT "VENDOR_ID", "VENDOR_NAME"
FROM "PROCUREMENT"."vendor_master"
WHERE "VENDOR_ID" NOT IN (
    SELECT DISTINCT "VENDOR_ID" FROM "PROCUREMENT"."payment"
);
```

---

### 4.3 EXISTS Subqueries

**Concepts:** Check for existence of related rows

```sql
-- Vendors with at least one high-value PO (> 50,000)
SELECT v."VENDOR_ID", v."VENDOR_NAME"
FROM "PROCUREMENT"."vendor_master" v
WHERE EXISTS (
    SELECT 1 FROM "PROCUREMENT"."po_header" p
    WHERE p."VENDOR_ID" = v."VENDOR_ID"
    AND p."TOTAL_NET_VALUE" > 50000
);

-- Materials never ordered
SELECT m."MATERIAL_ID", m."DESCRIPTION"
FROM "PROCUREMENT"."material_master" m
WHERE NOT EXISTS (
    SELECT 1 FROM "PROCUREMENT"."po_line_item" li
    WHERE li."MATERIAL_ID" = m."MATERIAL_ID"
);
```

---

### 4.4 Correlated Subqueries

**Concepts:** Subquery references outer query

```sql
-- Vendors with spend above their country's average
SELECT v."VENDOR_ID", v."VENDOR_NAME", v."COUNTRY",
    (SELECT SUM(p."TOTAL_NET_VALUE") 
     FROM "PROCUREMENT"."po_header" p 
     WHERE p."VENDOR_ID" = v."VENDOR_ID") AS vendor_spend
FROM "PROCUREMENT"."vendor_master" v
WHERE (
    SELECT SUM(p."TOTAL_NET_VALUE") 
    FROM "PROCUREMENT"."po_header" p 
    WHERE p."VENDOR_ID" = v."VENDOR_ID"
) > (
    SELECT AVG(country_spend) FROM (
        SELECT SUM(p2."TOTAL_NET_VALUE") AS country_spend
        FROM "PROCUREMENT"."po_header" p2
        INNER JOIN "PROCUREMENT"."vendor_master" v2 
            ON p2."VENDOR_ID" = v2."VENDOR_ID"
        WHERE v2."COUNTRY" = v."COUNTRY"
        GROUP BY p2."VENDOR_ID"
    )
);
```

---

## Module 5: Advanced Queries (Days 14-17)

### 5.1 CASE Expressions

**Concepts:** Conditional logic in queries

```sql
-- Categorize vendors by risk
SELECT 
    "VENDOR_ID",
    "VENDOR_NAME",
    "RISK_SCORE",
    CASE 
        WHEN "RISK_SCORE" >= 80 THEN 'Critical'
        WHEN "RISK_SCORE" >= 60 THEN 'High'
        WHEN "RISK_SCORE" >= 40 THEN 'Medium'
        ELSE 'Low'
    END AS risk_category
FROM "PROCUREMENT"."vendor_master";

-- Invoice status summary
SELECT 
    "VENDOR_ID",
    COUNT(*) AS total_invoices,
    SUM(CASE WHEN "MATCH_STATUS" = 'FULL_MATCH' THEN 1 ELSE 0 END) AS matched,
    SUM(CASE WHEN "MATCH_STATUS" != 'FULL_MATCH' THEN 1 ELSE 0 END) AS exceptions
FROM "PROCUREMENT"."invoice_header"
GROUP BY "VENDOR_ID";
```

---

### 5.2 Common Table Expressions (CTEs)

**Concepts:** WITH clause for readable complex queries

```sql
-- Vendor spend ranking using CTE
WITH vendor_spend AS (
    SELECT 
        "VENDOR_ID",
        SUM("TOTAL_NET_VALUE") AS total_spend,
        COUNT(*) AS po_count
    FROM "PROCUREMENT"."po_header"
    GROUP BY "VENDOR_ID"
)
SELECT 
    v."VENDOR_ID",
    v."VENDOR_NAME",
    vs.total_spend,
    vs.po_count
FROM "PROCUREMENT"."vendor_master" v
INNER JOIN vendor_spend vs ON v."VENDOR_ID" = vs."VENDOR_ID"
ORDER BY vs.total_spend DESC
LIMIT 10;

-- Multiple CTEs
WITH 
po_stats AS (
    SELECT "VENDOR_ID", COUNT(*) AS po_count, SUM("TOTAL_NET_VALUE") AS po_value
    FROM "PROCUREMENT"."po_header"
    GROUP BY "VENDOR_ID"
),
invoice_stats AS (
    SELECT "VENDOR_ID", COUNT(*) AS inv_count, SUM("TOTAL_NET_AMOUNT") AS inv_value
    FROM "PROCUREMENT"."invoice_header"
    GROUP BY "VENDOR_ID"
)
SELECT 
    v."VENDOR_ID",
    v."VENDOR_NAME",
    COALESCE(p.po_count, 0) AS po_count,
    COALESCE(p.po_value, 0) AS po_value,
    COALESCE(i.inv_count, 0) AS invoice_count,
    COALESCE(i.inv_value, 0) AS invoice_value
FROM "PROCUREMENT"."vendor_master" v
LEFT JOIN po_stats p ON v."VENDOR_ID" = p."VENDOR_ID"
LEFT JOIN invoice_stats i ON v."VENDOR_ID" = i."VENDOR_ID";
```

---

### 5.3 Window Functions

**Concepts:** ROW_NUMBER, RANK, running totals

```sql
-- Rank vendors by spend within each country
SELECT 
    "VENDOR_ID",
    "VENDOR_NAME",
    "COUNTRY",
    total_spend,
    RANK() OVER (PARTITION BY "COUNTRY" ORDER BY total_spend DESC) AS country_rank
FROM (
    SELECT 
        v."VENDOR_ID",
        v."VENDOR_NAME",
        v."COUNTRY",
        SUM(p."TOTAL_NET_VALUE") AS total_spend
    FROM "PROCUREMENT"."vendor_master" v
    INNER JOIN "PROCUREMENT"."po_header" p ON v."VENDOR_ID" = p."VENDOR_ID"
    GROUP BY v."VENDOR_ID", v."VENDOR_NAME", v."COUNTRY"
);

-- Running total of invoices by date
SELECT 
    "INVOICE_ID",
    "INVOICE_DATE",
    "TOTAL_NET_AMOUNT",
    SUM("TOTAL_NET_AMOUNT") OVER (ORDER BY "INVOICE_DATE") AS running_total
FROM "PROCUREMENT"."invoice_header"
ORDER BY "INVOICE_DATE";

-- Row number for pagination
SELECT * FROM (
    SELECT 
        "VENDOR_ID",
        "VENDOR_NAME",
        ROW_NUMBER() OVER (ORDER BY "VENDOR_ID") AS row_num
    FROM "PROCUREMENT"."vendor_master"
)
WHERE row_num BETWEEN 11 AND 20;
```

---

## Module 6: Graph Queries (Days 18-20)

### 6.1 Understanding Graph Views

**Concepts:** Vertex and edge views as SQL tables

```sql
-- Explore vertex view
SELECT * FROM "PROCUREMENT"."V_ALL_VERTICES" LIMIT 10;

-- Count vertices by type
SELECT "VERTEX_TYPE", COUNT(*) 
FROM "PROCUREMENT"."V_ALL_VERTICES"
GROUP BY "VERTEX_TYPE";

-- Explore edge view
SELECT * FROM "PROCUREMENT"."E_ALL_EDGES" LIMIT 10;

-- Count edges by type
SELECT "EDGE_TYPE", COUNT(*) 
FROM "PROCUREMENT"."E_ALL_EDGES"
GROUP BY "EDGE_TYPE";
```

---

### 6.2 Graph Traversal via JOINs

**Concepts:** Navigating relationships using edge views

```sql
-- Find materials supplied by a vendor (1-hop traversal)
SELECT 
    v."VERTEX_ID" AS vendor,
    v."LABEL" AS vendor_name,
    e."EDGE_TYPE",
    m."VERTEX_ID" AS material,
    m."LABEL" AS material_name
FROM "PROCUREMENT"."V_ALL_VERTICES" v
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e 
    ON v."VERTEX_ID" = e."SOURCE_VERTEX"
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" m 
    ON e."TARGET_VERTEX" = m."VERTEX_ID"
WHERE v."VERTEX_ID" = 'VND-HOKUYO'
AND e."EDGE_TYPE" = 'SUPPLIES';

-- Find all connections from a PO (multi-edge types)
SELECT 
    e."EDGE_TYPE",
    target."VERTEX_TYPE",
    target."VERTEX_ID",
    target."LABEL"
FROM "PROCUREMENT"."E_ALL_EDGES" e
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" target 
    ON e."TARGET_VERTEX" = target."VERTEX_ID"
WHERE e."SOURCE_VERTEX" = 'PO-000001';
```

---

### 6.3 Multi-Hop Traversals

**Concepts:** Following paths through the graph

```sql
-- 2-hop: PO → Vendor → Materials they supply
SELECT DISTINCT
    po."VERTEX_ID" AS po_id,
    vendor."VERTEX_ID" AS vendor_id,
    vendor."LABEL" AS vendor_name,
    material."VERTEX_ID" AS material_id,
    material."LABEL" AS material_name
FROM "PROCUREMENT"."V_ALL_VERTICES" po
-- Hop 1: PO → Vendor (ORDERED_FROM)
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e1 
    ON po."VERTEX_ID" = e1."SOURCE_VERTEX" AND e1."EDGE_TYPE" = 'ORDERED_FROM'
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" vendor 
    ON e1."TARGET_VERTEX" = vendor."VERTEX_ID"
-- Hop 2: Vendor → Materials (SUPPLIES)
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e2 
    ON vendor."VERTEX_ID" = e2."SOURCE_VERTEX" AND e2."EDGE_TYPE" = 'SUPPLIES'
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" material 
    ON e2."TARGET_VERTEX" = material."VERTEX_ID"
WHERE po."VERTEX_ID" = 'PO-000001';

-- P2P Chain: PO → GR → Invoice → Payment
SELECT 
    po."VERTEX_ID" AS po_id,
    gr."VERTEX_ID" AS gr_id,
    inv."VERTEX_ID" AS invoice_id,
    pay."VERTEX_ID" AS payment_id
FROM "PROCUREMENT"."V_ALL_VERTICES" po
-- PO ← GR (RECEIVED_FOR)
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e1 
    ON po."VERTEX_ID" = e1."TARGET_VERTEX" AND e1."EDGE_TYPE" = 'RECEIVED_FOR'
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" gr 
    ON e1."SOURCE_VERTEX" = gr."VERTEX_ID"
-- PO ← Invoice (INVOICED_FOR)
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e2 
    ON po."VERTEX_ID" = e2."TARGET_VERTEX" AND e2."EDGE_TYPE" = 'INVOICED_FOR'
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" inv 
    ON e2."SOURCE_VERTEX" = inv."VERTEX_ID"
-- Invoice ← Payment (PAYS)
INNER JOIN "PROCUREMENT"."E_ALL_EDGES" e3 
    ON inv."VERTEX_ID" = e3."TARGET_VERTEX" AND e3."EDGE_TYPE" = 'PAYS'
INNER JOIN "PROCUREMENT"."V_ALL_VERTICES" pay 
    ON e3."SOURCE_VERTEX" = pay."VERTEX_ID"
WHERE po."VERTEX_ID" = 'PO-000001';
```

---

## Module 7: Real-World Scenarios (Days 21-25)

### Scenario 1: Vendor Risk Analysis

```sql
-- High-risk vendors with significant spend
WITH vendor_spend AS (
    SELECT "VENDOR_ID", SUM("TOTAL_NET_VALUE") AS total_spend
    FROM "PROCUREMENT"."po_header"
    GROUP BY "VENDOR_ID"
)
SELECT 
    v."VENDOR_ID",
    v."VENDOR_NAME",
    v."COUNTRY",
    v."RISK_SCORE",
    v."QUALITY_SCORE",
    vs.total_spend,
    CASE 
        WHEN v."RISK_SCORE" >= 70 AND vs.total_spend > 100000 THEN 'Critical - Review Immediately'
        WHEN v."RISK_SCORE" >= 70 THEN 'High Risk - Monitor'
        WHEN vs.total_spend > 500000 THEN 'Strategic - High Volume'
        ELSE 'Standard'
    END AS vendor_classification
FROM "PROCUREMENT"."vendor_master" v
LEFT JOIN vendor_spend vs ON v."VENDOR_ID" = vs."VENDOR_ID"
WHERE v."RISK_SCORE" >= 60
ORDER BY v."RISK_SCORE" DESC, vs.total_spend DESC;
```

### Scenario 2: Invoice Matching Issues

```sql
-- Invoices with exceptions and their context
SELECT 
    i."INVOICE_ID",
    i."INVOICE_DATE",
    i."TOTAL_NET_AMOUNT",
    i."MATCH_STATUS",
    v."VENDOR_NAME",
    p."PO_ID",
    p."TOTAL_NET_VALUE" AS po_value,
    (i."TOTAL_NET_AMOUNT" - p."TOTAL_NET_VALUE") AS variance
FROM "PROCUREMENT"."invoice_header" i
INNER JOIN "PROCUREMENT"."vendor_master" v ON i."VENDOR_ID" = v."VENDOR_ID"
LEFT JOIN "PROCUREMENT"."po_header" p ON i."PO_ID" = p."PO_ID"
WHERE i."MATCH_STATUS" IN ('PRICE_VARIANCE', 'QUANTITY_VARIANCE')
ORDER BY ABS(i."TOTAL_NET_AMOUNT" - p."TOTAL_NET_VALUE") DESC;
```

### Scenario 3: Supply Chain Coverage

```sql
-- Materials with single-source risk
SELECT 
    m."MATERIAL_ID",
    m."DESCRIPTION",
    m."CRITICALITY",
    COUNT(DISTINCT sl."VENDOR_ID") AS vendor_count,
    STRING_AGG(v."VENDOR_NAME", ', ') AS vendors
FROM "PROCUREMENT"."material_master" m
LEFT JOIN "PROCUREMENT"."source_list" sl ON m."MATERIAL_ID" = sl."MATERIAL_ID"
LEFT JOIN "PROCUREMENT"."vendor_master" v ON sl."VENDOR_ID" = v."VENDOR_ID"
WHERE m."CRITICALITY" = 'HIGH'
GROUP BY m."MATERIAL_ID", m."DESCRIPTION", m."CRITICALITY"
HAVING COUNT(DISTINCT sl."VENDOR_ID") <= 1
ORDER BY m."MATERIAL_ID";
```

### Scenario 4: Spend Analysis

```sql
-- Monthly spend trend by category
SELECT 
    TO_CHAR(p."PO_DATE", 'YYYY-MM') AS month,
    c."CATEGORY_NAME",
    SUM(li."NET_VALUE") AS spend
FROM "PROCUREMENT"."po_line_item" li
INNER JOIN "PROCUREMENT"."po_header" p ON li."PO_ID" = p."PO_ID"
INNER JOIN "PROCUREMENT"."material_master" m ON li."MATERIAL_ID" = m."MATERIAL_ID"
INNER JOIN "PROCUREMENT"."category_hierarchy" c ON m."CATEGORY_ID" = c."CATEGORY_ID"
WHERE c."LEVEL" = 1  -- Top-level categories only
GROUP BY TO_CHAR(p."PO_DATE", 'YYYY-MM'), c."CATEGORY_NAME"
ORDER BY month, spend DESC;
```

---

## Learning Tips

1. **Run every query** — Don't just read, execute and observe results
2. **Modify examples** — Change filters, add columns, try different tables
3. **Check row counts** — Use COUNT(*) to understand data volumes
4. **Use LIMIT liberally** — Start with LIMIT 10 to avoid overwhelming output
5. **Read error messages** — HANA errors often indicate exact column/syntax issues
6. **Draw the joins** — Sketch table relationships before writing multi-table queries

## HANA-Specific Notes

- Column names are **case-sensitive when quoted**: `"VENDOR_ID"` ≠ `"vendor_id"`
- Use double quotes for identifiers: `"PROCUREMENT"."vendor_master"`
- `STRING_AGG` instead of `GROUP_CONCAT`
- Date formatting: `TO_CHAR(date, 'YYYY-MM-DD')`

## Next Steps

After completing this plan:
1. Practice with the `/graph/cypher` endpoint for OpenCypher queries
2. Write custom queries for new business questions
3. Explore HANA-specific features (window functions, spatial, text search)
