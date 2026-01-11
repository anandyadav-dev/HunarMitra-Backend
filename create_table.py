from django.db import connection

sql = """
CREATE TABLE IF NOT EXISTS analytics_event_aggregates_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT '',
    count INT NOT NULL DEFAULT 0,
    unique_users INT NOT NULL DEFAULT 0,
    unique_anonymous INT NOT NULL DEFAULT 0,
    meta JSON NOT NULL,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    UNIQUE KEY unique_date_type_source (date, event_type, source),
    INDEX agg_date_type_idx (date, event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

with connection.cursor() as cursor:
    cursor.execute(sql)
    print("✅ Table created successfully!")
