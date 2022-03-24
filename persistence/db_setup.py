import sqlite3

conn = sqlite3.connect("hivenotifier.db")

conn.execute(
    """
DROP TABLE IF EXISTS user;
"""
)
conn.execute(
    """
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone_number INTEGER NOT NULL,
    primary_facility_id INTEGER NOT NULL,
    most_recent_requested_date TEXT NOT NULL,
    most_recent_notification_id INTEGER NOT NULL,
    is_account_setup INTEGER NOT NULL,
    is_admin INTEGER NOT NULL
);
"""
)
conn.execute(
    """
INSERT INTO user (name, phone_number, primary_facility_id, most_recent_requested_date, most_recent_notification_id, is_account_setup, is_admin)
VALUES 
    ('Example', 12323123123, 1, '', 0, 1, 1);
"""
)

conn.execute(
    """
DROP TABLE IF EXISTS facility;
"""
)
conn.execute(
    """
CREATE TABLE facility (
    id INTEGER PRIMARY KEY,
    location TEXT NOT NULL,
    offering_guid TEXT NOT NULL
);
"""
)
conn.execute(
    """
INSERT INTO facility (location, offering_guid)
VALUES 
    ('Vancouver', '484c1a7ca09145419ef258eeb894c38f'),
    ('Surrey', 'b41f7158c38e43f5adb1ee5b003e4bd5'),
    ('North Shore', '6fa9139cc3584fc0a5662a5c36d68958'),
    ('Port Coquitlam', 'b405d11ff01346e8bce172d854720c3d');
"""
)

conn.execute(
    """
DROP TABLE IF EXISTS notification;
"""
)
conn.execute(
    """
CREATE TABLE notification (
    id INTEGER PRIMARY KEY,
    facility_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notification_date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    enabled INTEGER NOT NULL
);
"""
)


conn.commit()
conn.close()
