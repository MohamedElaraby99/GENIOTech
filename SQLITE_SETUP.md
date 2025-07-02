# 🗄️ SQLite Database Setup

The GENIO TECH CRM has been configured to use **SQLite** as the default database for simplified deployment.

## ✅ Changes Made

### 1. Database Configuration

- **Default database**: SQLite (`instance/crm.db`)
- **Removed dependencies**: PostgreSQL (`psycopg2-binary`) and MySQL (`pymysql`) drivers
- **Updated config**: Both development and production configs now use SQLite by default

### 2. Deployment Simplification

- **No database server required**: SQLite is file-based
- **Reduced system dependencies**: Removed PostgreSQL installation from deployment scripts
- **Easier backup**: Single database file to backup

### 3. Environment Configuration

- **Default `.env`**: Uses SQLite by default
- **Optional upgrades**: PostgreSQL/MySQL can still be used by changing `DATABASE_URL`

## 🚀 Benefits

1. **Simpler deployment**: No need to install and configure database servers
2. **Lower resource usage**: No separate database service running
3. **Easier development**: Single file database
4. **Built-in Python support**: No additional drivers needed
5. **Easy backups**: Just copy the `instance/crm.db` file

## 📁 Database Location

```
/var/www/geniotech-crm/instance/crm.db
```

## 🔄 Migration to Other Databases

If you need PostgreSQL or MySQL later, simply:

1. Install the required driver:

   ```bash
   pip install psycopg2-binary  # For PostgreSQL
   # or
   pip install pymysql          # For MySQL
   ```

2. Update your `.env` file:

   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

3. Run the migration:
   ```bash
   python wsgi.py
   ```

## 💾 Backup Recommendations

### Daily Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/www/geniotech-crm/instance/crm.db /home/backups/crm_backup_$DATE.db
find /home/backups -name "crm_backup_*.db" -mtime +7 -delete
```

### Manual Backup

```bash
cp instance/crm.db backups/crm_backup_$(date +%Y%m%d).db
```

---

**SQLite is perfect for small to medium-sized deployments with up to thousands of users. For larger scale applications, consider PostgreSQL.**
