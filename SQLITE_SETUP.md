# 🗄️ SQLite Database Setup

The GENIO TECH CRM has been configured to use **SQLite** as the database for simplified deployment.

## ✅ Changes Made

### 1. Database Configuration

- **Database**: SQLite (`instance/crm.db`)
- **Removed dependencies**: PostgreSQL and MySQL drivers completely removed
- **Updated config**: Both development and production configs use SQLite only

### 2. Deployment Simplification

- **No database server required**: SQLite is file-based
- **Reduced system dependencies**: No database server installation needed
- **Easier backup**: Single database file to backup

### 3. Environment Configuration

- **Default `.env`**: Uses SQLite only
- **No alternatives**: System designed specifically for SQLite

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

**SQLite is perfect for small to medium-sized deployments with thousands of users and provides excellent performance for most CRM applications.**
