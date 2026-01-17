"""
Database Query Service for Chat Context
Provides database schema information and query capabilities for AI chat.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import Dict, List, Optional, Any
import json

class DatabaseQueryService:
    """Service for querying database schema and data for chat context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get summary of database schema"""
        schema_info = {
            "tables": [],
            "table_count": 0
        }
        
        # Query to get all tables
        result = self.db.execute(text("""
            SELECT TABLE_NAME, TABLE_ROWS
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """))
        
        for row in result:
            table_name = row[0]
            table_rows = row[1] if row[1] else 0
            
            # Get columns for each table
            columns_result = self.db.execute(text(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """))
            
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == "YES",
                    "key": col[3] if col[3] else None
                })
            
            schema_info["tables"].append({
                "name": table_name,
                "row_count": table_rows,
                "columns": columns
            })
            schema_info["table_count"] += 1
        
        return schema_info
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table"""
        try:
            # Get table structure
            columns_result = self.db.execute(text(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """))
            
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == "YES",
                    "key": col[3] if col[3] else None,
                    "default": col[4],
                    "extra": col[5]
                })
            
            # Get sample data (first 5 rows)
            try:
                sample_result = self.db.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                sample_rows = []
                for row in sample_result:
                    sample_rows.append(dict(row._mapping))
            except Exception:
                sample_rows = []
            
            # Get row count
            count_result = self.db.execute(text(f"SELECT COUNT(*) as cnt FROM {table_name}"))
            row_count = count_result.fetchone()[0] if count_result else 0
            
            return {
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
                "sample_data": sample_rows[:3]  # Limit to 3 rows for context
            }
        except Exception as e:
            return None
    
    def execute_safe_query(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Execute a safe SELECT query (read-only)
        Only allows SELECT statements with LIMIT
        """
        query_upper = query.strip().upper()
        
        # Security: Only allow SELECT queries
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        # Security: Block dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        try:
            result = self.db.execute(text(query))
            rows = []
            for row in result:
                rows.append(dict(row._mapping))
            
            return {
                "success": True,
                "row_count": len(rows),
                "data": rows
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    def get_recent_data_summary(self) -> Dict[str, Any]:
        """Get summary of recent data across key tables"""
        summary = {}
        
        # Get recent SPC metrics
        try:
            spc_result = self.db.execute(text("""
                SELECT COUNT(*) as cnt, MAX(calculated_at) as latest
                FROM spc_metrics
            """))
            row = spc_result.fetchone()
            if row:
                summary["spc_metrics"] = {
                    "count": row[0] if row[0] else 0,
                    "latest": str(row[1]) if row[1] else None
                }
        except Exception:
            summary["spc_metrics"] = {"count": 0, "latest": None}
        
        # Get recent alarms
        try:
            alarm_result = self.db.execute(text("""
                SELECT COUNT(*) as cnt, COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active
                FROM alarms
            """))
            row = alarm_result.fetchone()
            if row:
                summary["alarms"] = {
                    "total": row[0] if row[0] else 0,
                    "active": row[1] if row[1] else 0
                }
        except Exception:
            summary["alarms"] = {"total": 0, "active": 0}
        
        # Get recent experiments
        try:
            exp_result = self.db.execute(text("""
                SELECT COUNT(*) as cnt
                FROM experiments
            """))
            row = exp_result.fetchone()
            if row:
                summary["experiments"] = {"count": row[0] if row[0] else 0}
        except Exception:
            summary["experiments"] = {"count": 0}
        
        return summary
