#!/bin/bash

# Script to fix Django template syntax errors in all templates

cd /home/emarat/Downloads/org-management-main/templates/core

echo "Fixing template syntax errors..."

# List of templates that have the formatting issue
for file in dashboard.html customer_list.html customer_form.html inventory_list.html inventory_form.html expense_form.html payment_list.html payment_form.html reports.html confirm_delete.html; do
    if [ -f "$file" ]; then
        echo "Fixing $file..."
        
        # Use sed to fix the template tags on first line
        # Replace pattern: {% extends 'base.html' %} {% block ... with proper line breaks
        sed -i '1s/{% extends '\''base\.html'\'' %} {% block/{% extends '\''base.html'\'' %}\n\n{% block/g' "$file"
        
        # Fix any {%endblock %} that might be split across lines
        sed -i ':a;N;$!ba;s/{%\nendblock %}/{% endblock %}/g' "$file"
        
        # Fix any {% block content %} that might be on same line as endblock
        sed -i 's/{% endblock %} {% block content %}/{% endblock %}\n\n{% block content %}/g' "$file"
    fi
done

echo "Done!"
