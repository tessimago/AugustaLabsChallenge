#!/bin/bash
set -e

echo "Restoring database from dump..."
pg_restore -U postgres -d augusta_labs_db -v /tmp/db_backup.dump
echo "Database restored successfully!"