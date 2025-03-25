
#!/bin/bash

# Create export directory
export_dir="pharmacy_system_export"
mkdir -p $export_dir

# Copy all project files
cp -r pharmacy_app $export_dir/
cp -r pharmacy_management $export_dir/
cp manage.py $export_dir/
cp create_admin.py $export_dir/
cp add_test_data.py $export_dir/
cp pyproject.toml $export_dir/

# Export database structure (if using PostgreSQL)
pg_dump -s $PGDATABASE > $export_dir/database_structure.sql

# Create a zip file
zip -r pharmacy_system_export.zip $export_dir/*

echo "Export completed. Check pharmacy_system_export.zip"
